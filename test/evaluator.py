import os
import math
import re
from pathlib import Path
from prolog_compiler import consult, extract_goal
from logging_utils import LogManager


class Evaluator:
    """
    • logic_matrix  : 1 = query succeeds
    • vocab_matrix  : 1 = query *compiles* (no undefined predicate / arity / timeout)
                      regardless of whether it logically succeeds
    """
    SIG_RE = re.compile(r'([a-z]\w*)\s*\(([^:-]*)')

    def __init__(self, log_manager: LogManager):
        self.logm = log_manager
        self.logic_matrix: list[list[int]] = []
        self.vocab_matrix: list[list[int]] = []

    # ───────────────────────── file helpers ──────────────────────────
    def _dump_programs(self, solutions, folder: Path):
        folder.mkdir(parents=True, exist_ok=True)
        for sol in solutions:
            (folder / f"{sol.id}.pl").write_text(sol.original_program or "", encoding="utf-8")

    def _dump_tests(self, test_cases, file_path: Path):
        file_path.write_text("\n".join(tc.original_fact for tc in test_cases), encoding="utf-8")

    # ───────────────────────── evaluation ────────────────────────────
    def evaluate(self, solutions, test_cases, scope: str):
        """
        `scope` is a relative path fragment (e.g. "vocab_round_02/iter_03")
        used only for logging output.
        """
        # ensure canonical_* fields exist --------------------------------
        # for sol in solutions:
        #     sol.canonical_program = getattr(sol, "canonical_program",
        #                                     sol.original_program)
        # for tc in test_cases:
        #     tc.canonical_fact = getattr(tc, "canonical_fact",
        #                                 tc.original_fact)
        for sol in solutions:
            if sol.canonical_program is None:
                sol.canonical_program = sol.original_program
        for tc in test_cases:
            if tc.canonical_fact is None:
                tc.canonical_fact = tc.original_fact

        workdir = self.logm.path(scope)
        print(f"\n--- 🏆 Eval @ {workdir.relative_to(self.logm.run_dir)} ---")

        # persist artefacts ----------------------------------------------
        self._dump_programs(solutions, workdir / "solutions")
        self._dump_tests(test_cases, workdir / "tests.pl")

        self.logic_matrix, self.vocab_matrix = [], []
        self.errors_matrix = []

        # ───────────────── solution-level loop ──────────────────────────
        for sol in solutions:
            logic_row, vocab_row = [], []
            logic_passes, vocab_passes = 0, 0
            error_row = []

            for tc in test_cases:
                result, reason = self._run_single_test(
                    sol.canonical_program, tc.canonical_fact
                )

                # ---------- logic matrix (1 = pass) ----------
                if result == "logic_pass":
                    logic_passes += 1
                    logic_row.append(1)
                else:
                    logic_row.append(0)

                # ---------- vocab matrix (1 = pass) ----------
                if (result != "vocab_error" and
                        result != "other_error"):
                    vocab_passes += 1
                    vocab_row.append(1)
                else:
                    vocab_row.append(0)

                # ---------- unexpected outcome ---------------
                if result not in ("logic_pass", "logic_error", "vocab_error"):
                    print(f"        ⚠️  Unclassified outcome [{result}] - {reason}")
                
                # ---------- error row ------------------------
                error_row.append(reason or "")

            total = len(test_cases) or 1
            sol.logic_fitness = logic_passes / total
            sol.vocab_fitness = vocab_passes / total

            self.logic_matrix.append(logic_row)
            self.vocab_matrix.append(vocab_row)
            self.errors_matrix.append(error_row)

            print(f"  🔍 Solution {sol.id} logic_fitness: "
                  f"{sol.logic_fitness:.2f} ({logic_passes}/{total})")
            print(f"  📝 Solution {sol.id} vocab_fitness: "
                  f"{sol.vocab_fitness:.2f} ({vocab_passes}/{total})")

            # CSV for later inspection
            self.logm.write_row(
                f"{scope}/metrics.csv",
                dict(scope=scope,
                     sol_id=sol.id,
                     logic=sol.logic_fitness,
                     vocab=sol.vocab_fitness)
            )

        # ───────────────── test-level summaries ─────────────────────────
        num_sols = len(solutions) or 1
        for j, tc in enumerate(test_cases):
            logic_pass_count = sum(self.logic_matrix[i][j] for i in range(num_sols))
            vocab_pass_count = sum(self.vocab_matrix[i][j] for i in range(num_sols))

            print(f"  🧪 Test {tc.id} logic_fitness: "
                  f"{logic_pass_count/num_sols:.2f} ({logic_pass_count}/{num_sols})")
            print(f"  📝 Test {tc.id} vocab_fitness: "
                  f"{vocab_pass_count/num_sols:.2f} ({vocab_pass_count}/{num_sols})")

        # confidence / discrimination still based on *logic* only
        logic_fitnesses = [s.logic_fitness for s in solutions]
        self._compute_confidence(test_cases, self.logic_matrix,
                                 logic_fitnesses, "logic_confidence")
        self._compute_discrimination(test_cases, self.logic_matrix,
                                     "logic_discrimination")

    # ───────────────────────── stats helpers ───────────────────────────
    def _compute_confidence(self, test_cases, matrix, fitness_vector, attr_name):
        total_weight = sum(fitness_vector)
        for j, tc in enumerate(test_cases):
            if total_weight == 0:
                conf = 0.0
            else:
                passed_w = sum(matrix[i][j] * fitness_vector[i]
                               for i in range(len(matrix)))
                conf = passed_w / total_weight
            setattr(tc, attr_name, conf)
            print(f"  🧪 Test {tc.id} {attr_name}: {conf:.2f}")

    def _compute_discrimination(self, test_cases, matrix, attr_name):
        total = len(matrix)
        for j, tc in enumerate(test_cases):
            p = sum(matrix[i][j] for i in range(total)) / total if total else 0.0
            disc = 0.0 if p in (0.0, 1.0) else -(p*math.log2(p) + (1-p)*math.log2(1-p))
            setattr(tc, attr_name, disc)
            print(f"  🧪 Test {tc.id} {attr_name}: {disc:.2f}")

    # ───────────────────────── single call to Prolog ───────────────────
    def _run_single_test(self, program: str, fact: str):
        if not program or not fact:
            return "other_error", "Missing program or test fact"

        goal = extract_goal(fact)
        if not goal:
            return "other_error", "Malformed test case"

        passed, reason = consult(program, goal)
        # print(reason or "No reason provided")


        if not passed:
            if self._is_vocab_error(reason):
                return "vocab_error", reason
            if self._is_logic_error(reason):
                return "logic_error", reason
            if not self._is_logic_error(reason) and not self._is_vocab_error(reason):
                return "other_error", reason
        return "logic_pass", None

    @staticmethod
    def _is_vocab_error(reason: str | None) -> bool:
        if not reason:
            return False
        return any(substr in reason for substr in (
            "Unknown procedure", "Undefined procedure", "ERROR:", "Syntax error",
        ))

    @staticmethod
    def _is_logic_error(reason: str | None) -> bool:
        if not reason:
            return False
        return any(substr in reason for substr in (
            "Goal failed"
        ))
