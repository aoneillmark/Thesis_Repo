"""evaluator_fol.py – FOL-based evaluator for the co-evolution system
────────────────────────────────────────────────────────────────────
Classifier rules:
    • *vocab_error*  → program fails to parse/execute (e.g., syntax error)
    • *logic_error*  → program runs but returns incorrect label
    • *logic_pass*   → program returns the correct label

Fallback is *other_error*.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from logging_utils import LogManager
from fol_solver.prover9_solver import FOL_Prover9_Program  # ✅ New solver

# _VOCAB_ERR_PATTERNS = ("syntax", "parse", "undeclared", "NameError", "unknown")
# _LOGIC_ERR_PATTERNS = ("false", "unsat", "fail")


class Evaluator:
    """Compute fitness matrices for FOL candidates & test cases."""

    def __init__(self, log_manager: LogManager):
        self.logm = log_manager
        self.logic_matrix: List[List[int]] = []
        self.vocab_matrix: List[List[int]] = []
        self.errors_matrix: List[List[str]] = []

    def _dump_combined(self, solutions, test_cases, folder: Path):
        folder.mkdir(parents=True, exist_ok=True)
        for sol in solutions:
            for tc in test_cases:
                combo = "# Question:" + "\n" + tc.questions + "\n\n" + "# Predicates:" + "\n" + sol.predicates + "\n\n" + "# Premises:" + "\n" + sol.premises + "\n\n" + "# Conclusion:" + "\n" + tc.conclusions
                (folder / f"{sol.id}__{tc.id}.fol.txt").write_text(combo, encoding="utf-8")

    def evaluate(self, solutions, test_cases, scope: str):
        workdir = self.logm.path(scope)
        print(f"\n--- 🏆 FOL-Eval @ {workdir.relative_to(self.logm.run_dir)} ---")

        self._dump_combined(solutions, test_cases, workdir / "combined_programs")
        self.logic_matrix, self.vocab_matrix, self.errors_matrix = [], [], []

        for sol in solutions:
            logic_row, vocab_row = [], []
            logic_passes = vocab_passes = 0

            for tc in test_cases:
                result, reason = self._run_single_test(sol, tc)
                sol.syntax_errors.clear()
                tc.syntax_errors.clear()

                if result == "logic_pass":
                    logic_passes += 1
                    vocab_passes += 1
                    logic_row.append(1)
                    vocab_row.append(1)
                elif result == "logic_error":
                    vocab_passes += 1
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

            total = len(test_cases) or 1
            sol.logic_fitness = logic_passes / total
            sol.vocab_fitness = vocab_passes / total

            self.logic_matrix.append(logic_row)
            self.vocab_matrix.append(vocab_row)

            print(f"  🔍 Solution {sol.id} logic_fitness: {sol.logic_fitness:.2f} ({logic_passes}/{total})")
            print(f"  📝 Solution {sol.id} vocab_fitness: {sol.vocab_fitness:.2f} ({vocab_passes}/{total})")

            self.logm.write_row(
                f"{scope}/metrics.csv",
                dict(scope=scope, sol_id=sol.id, logic=sol.logic_fitness, vocab=sol.vocab_fitness),
            )

        num_sols = len(solutions) or 1
        for j, tc in enumerate(test_cases):
            logic_pass_count = sum(self.logic_matrix[i][j] for i in range(num_sols))
            vocab_pass_count = sum(self.vocab_matrix[i][j] for i in range(num_sols))

            tc.logic_fitness = logic_pass_count / num_sols
            tc.vocab_fitness = vocab_pass_count / num_sols

            print(f"  🧪 Test {tc.id} logic_fitness: {tc.logic_fitness:.2f} ({logic_pass_count}/{num_sols})")
            print(f"  📝 Test {tc.id} vocab_fitness: {tc.vocab_fitness:.2f} ({vocab_pass_count}/{num_sols})")

        logic_scores = [s.logic_fitness for s in solutions]
        self._compute_confidence(test_cases, self.logic_matrix, logic_scores, "logic_confidence")
        self._compute_discrimination(test_cases, self.logic_matrix, "logic_discrimination")

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

    def _run_single_test(self, sol, tc) -> Tuple[str, str | None]:
        """Return (code, reason) where code ∈ {logic_pass, logic_error, vocab_error, other_error}"""

        # fol_program_text =  sol.canonical_program + "\n\n" + tc.canonical_block
        # fol_program_text = tc.questions + "\n\n" + sol.canonical_program + "\n\n" + tc.conclusions
        fol_program_text = "# Question:" + "\n" + tc.questions + "\n\n" + "# Predicates:" + "\n" + sol.predicates + "\n\n" + "# Premises:" + "\n" + sol.premises + "\n\n" + "# Conclusion:" + "\n" + tc.conclusions
        # Make sure it's utf-8 encoded
        try:
            fol_program_text = fol_program_text.encode("utf-8").decode("utf-8")
        except UnicodeDecodeError as exc:
            print("❌ UnicodeDecodeError:", exc)
            return -1

        try:
            fol_prog = FOL_Prover9_Program(fol_program_text)
        except Exception as exc:
            return "vocab_error", f"InitException: {exc}"
        
        # Check if fol_prog.flag is type Exception
        if isinstance(fol_prog.flag, Exception):
            print("FIX THIS MAN!!! I'M IN _run_single_test. Should have a better error handling here.")
            return "vocab_error", fol_prog.syntax_error or "Unknown syntax error"

        try:
            result = fol_prog.execute_program()
        except Exception as exc:
            return "other_error", f"ExecutionError: {exc}"

        if result is None:
            err_msg = fol_prog.syntax_error if hasattr(fol_prog, "syntax_error") else "(unknown error)"
            return "vocab_error", err_msg

        predicted = str(result[0]).lower()
        gold = getattr(tc, "correct_label", None)

        if gold is None:
            return "logic_error", "Missing gold label"
        
        print(f"  🧪 Test {tc.id} predicted: {predicted}, gold: {gold}")

        if predicted == gold:
            return "logic_pass", None
        else:
            return "logic_error", f"Predicted {predicted}, expected {gold}"

    # @staticmethod
    # def _is_vocab_error(msg: str | None) -> bool:
    #     if not msg:
    #         return False
    #     return any(pat.lower() in msg.lower() for pat in _VOCAB_ERR_PATTERNS)

    # @staticmethod
    # def _is_logic_error(msg: str | None) -> bool:
    #     if not msg:
    #         return False
    #     return any(pat.lower() in msg.lower() for pat in _LOGIC_ERR_PATTERNS)
