"""evaluator_z3.py – Z3-based evaluator for the co-evolution system
────────────────────────────────────────────────────────────────────
Classifier rules adjusted per conversation:
    • *vocab_error*  → programme fails to **compile/parse/execute** (syntax, NameError,
      time‑out, etc.).
    • *logic_error*  → programme runs but returns the **wrong option label** (or no
      model / "unsat"), i.e. it simply answers incorrectly.
    • *logic_pass*   → programme runs and returns the gold label.

Everything else is tagged *other_error*.
"""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import List, Tuple

from logging_utils import LogManager
from sat_problem_solver import LSAT_Z3_Program  # adjust import path if needed

# ────────────────────────── error patterns ──────────────────────────
# These strings flag *vocab* problems (parse / compile / runtime crash).
_VOCAB_ERR_PATTERNS = (
    "NameError",
    "AttributeError",
    "SyntaxError",
    "undeclared",
    "unknown",
)

# Any *runtime* message containing these tokens is still considered a
# *logic* error: the programme ran but produced no satisfying model.
_LOGIC_ERR_PATTERNS = (
    "unsat",
    "UNSAT",
)


class Evaluator:
    """Compute fitness matrices for Z3 candidates & test cases."""

    def __init__(self, log_manager: LogManager):
        self.logm = log_manager
        self.logic_matrix: List[List[int]] = []
        self.vocab_matrix: List[List[int]] = []
        self.errors_matrix: List[List[str]] = []

    # ─────────────────────── helpers: persist artefacts ──────────────
    def _dump_combined(self, solutions, test_cases, folder: Path):
        folder.mkdir(parents=True, exist_ok=True)
        for sol in solutions:
            for tc in test_cases:
                combo = tc.options_block + "\n\n" + sol.canonical_program
                (folder / f"{sol.id}__{tc.id}.z3.py").write_text(combo, encoding="utf-8")

    # ─────────────────────── main entry point ───────────────────────
    def evaluate(self, solutions, test_cases, scope: str):
        workdir = self.logm.path(scope)
        print(f"\n--- 🏆 Z3-Eval @ {workdir.relative_to(self.logm.run_dir)} ---")

        # Persist combined artefacts for debugging
        self._dump_combined(solutions, test_cases, workdir / "combined_programs")

        self.logic_matrix, self.vocab_matrix, self.errors_matrix = [], [], []

        for sol in solutions:
            sol.syntax_errors.clear()
        for tc in test_cases:
            tc.syntax_errors.clear()
    
        for sol in solutions:
            logic_row, vocab_row, error_row = [], [], []
            logic_passes = vocab_passes = 0

            for tc in test_cases:
                result, reason = self._run_single_test(sol, tc)
                # print(f"  🧪 Test {tc.id} result: {result} ({reason})")

                # Update rows / counters ------------------------------------------------
                if result == "logic_pass":
                    logic_passes += 1
                    vocab_passes += 1
                    logic_row.append(1)
                    vocab_row.append(1)
                elif result == "logic_error":
                    vocab_passes += 1  # compiled + executed OK
                    logic_row.append(0)
                    vocab_row.append(1)
                elif result == "vocab_error":
                    sol.syntax_errors.append(reason or "(unknown)")
                    tc.syntax_errors.append(reason or "(unknown)")
                    logic_row.append(0)
                    vocab_row.append(0)
                else:  # other_error
                    sol.syntax_errors.append(reason or "(unknown)")
                    tc.syntax_errors.append(reason or "(unknown)")
                    logic_row.append(0)
                    vocab_row.append(0)

                # error_row.append(reason or "")

            total = len(test_cases) or 1
            sol.logic_fitness = logic_passes / total
            sol.vocab_fitness = vocab_passes / total

            self.logic_matrix.append(logic_row)
            self.vocab_matrix.append(vocab_row)
            # self.errors_matrix.append(error_row)

            print(
                f"  🔍 Solution {sol.id} logic_fitness: {sol.logic_fitness:.2f} ({logic_passes}/{total})"
            )
            print(
                f"  📝 Solution {sol.id} vocab_fitness: {sol.vocab_fitness:.2f} ({vocab_passes}/{total})"
            )

            self.logm.write_row(
                f"{scope}/metrics.csv",
                dict(scope=scope, sol_id=sol.id, logic=sol.logic_fitness, vocab=sol.vocab_fitness),
            )

        # ───────── per-test summaries ─────────────────────────────────
        num_sols = len(solutions) or 1
        for j, tc in enumerate(test_cases):
            logic_pass_count = sum(self.logic_matrix[i][j] for i in range(num_sols))
            vocab_pass_count = sum(self.vocab_matrix[i][j] for i in range(num_sols))

            tc.logic_fitness = logic_pass_count / num_sols
            tc.vocab_fitness = vocab_pass_count / num_sols

            print(
                f"  🧪 Test {tc.id} logic_fitness: {tc.logic_fitness:.2f} ({logic_pass_count}/{num_sols})"
            )
            print(
                f"  📝 Test {tc.id} vocab_fitness: {tc.vocab_fitness:.2f} ({vocab_pass_count}/{num_sols})"
            )

        # Higher-level statistics
        logic_scores = [s.logic_fitness for s in solutions]
        self._compute_confidence(test_cases, self.logic_matrix, logic_scores, "logic_confidence")
        self._compute_discrimination(test_cases, self.logic_matrix, "logic_discrimination")

    # ───────────────────── auxiliary stats ───────────────────────────
    def _compute_confidence(self, test_cases, matrix, weights, attr):
        total_w = sum(weights)
        for j, tc in enumerate(test_cases):
            conf = 0.0 if total_w == 0 else sum(matrix[i][j] * weights[i] for i in range(len(matrix))) / total_w
            setattr(tc, attr, conf)
            print(f"  🧪 Test {tc.id} {attr}: {conf:.2f}")

    def _compute_discrimination(self, test_cases, matrix, attr):
        n = len(matrix)
        for j, tc in enumerate(test_cases):
            p = sum(matrix[i][j] for i in range(n)) / n if n else 0.0
            disc = 0.0 if p in (0.0, 1.0) else -(p * math.log2(p) + (1 - p) * math.log2(1 - p))
            setattr(tc, attr, disc)
            print(f"  🧪 Test {tc.id} {attr}: {disc:.2f}")

    # ───────────────────── single run helper ─────────────────────────
    def _run_single_test(self, sol, tc) -> Tuple[str, str | None]:
        """Return (code, reason) where code ∈ {logic_pass, logic_error, vocab_error, other_error}"""

        logic_program = tc.options_block + "\n\n" + sol.canonical_program

        try:
            z3_prog = LSAT_Z3_Program(logic_program, "AR-LSAT")
        except Exception as exc:
            return "vocab_error", f"ParseException: {exc}"

        if not getattr(z3_prog, "flag", True) or z3_prog.standard_code is None:
            # Try to get the actual error message from the LSAT_Z3_Program instance
            error_msg = getattr(z3_prog, 'error_message', None)
            if error_msg:
                return "vocab_error", f"ParseError: {error_msg}"
            return "vocab_error", "ParseError (flag=false). Are you sure # Options, # Declarations, and # Constraints are correct and in the code?"
    
        output, err = z3_prog.execute_program()

        if output is None:
            if self._is_vocab_error(err):
                return "vocab_error", err
            if self._is_logic_error(err):
                return "logic_error", err
            return "other_error", err

        # Map raw Z3 result to option label
        try:
            predicted = z3_prog.answer_mapping(output)
        except Exception as exc:
            return "other_error", f"MappingError: {exc}"

        gold = getattr(tc, "correct_label", None)
        if gold is None:
            # Unlabelled test – compilation counts only as vocab pass
            return "logic_error", "Missing gold label"

        if predicted == gold:
            return "logic_pass", None
        else:
            return "logic_error", f"Predicted {predicted}, expected {gold}"

    # ───────────────────── pattern helpers ───────────────────────────
    @staticmethod
    def _is_vocab_error(msg: str | None) -> bool:
        if not msg:
            return False
        return any(pat.lower() in msg.lower() for pat in _VOCAB_ERR_PATTERNS)

    @staticmethod
    def _is_logic_error(msg: str | None) -> bool:
        if not msg:
            return False
        return any(pat.lower() in msg.lower() for pat in _LOGIC_ERR_PATTERNS)
