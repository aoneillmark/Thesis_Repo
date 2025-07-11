# evaluator.py

import os
import uuid
import re
from prolog_compiler import consult, extract_goal


class Evaluator:
    def __init__(self, log_dir):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)

    def save_solutions(self, solutions):
        for sol in solutions:
            sol.canonical_program = sol.original_program
            fname = os.path.join(self.log_dir, f"solution_{sol.id}.pl")
            with open(fname, "w", encoding="utf-8") as f:
                f.write(sol.canonical_program or "❌ No canonical program available.")

    def save_test_cases(self, test_cases):
        for tc in test_cases:
            tc.canonical_fact = tc.original_fact
        test_log_path = os.path.join(self.log_dir, "test_cases.pl")
        with open(test_log_path, "w", encoding="utf-8") as f:
            for tc in test_cases:
                f.write((tc.canonical_fact or "❌ Invalid test case") + "\n")

    def evaluate(self, solutions, test_cases):
        print("\n--- 🏆 Starting Evaluation ---")
        self.save_solutions(solutions)
        self.save_test_cases(test_cases)

        for sol in solutions:
            passed_count = 0
            vocab_error_count = 0
            for tc in test_cases:
                result, reason = self._run_single_test(sol.canonical_program, tc.canonical_fact)

                if result == "logic_pass":
                    passed_count += 1
                elif result == "vocab_error":
                    vocab_error_count += 1

            sol.logic_fitness = passed_count / len(test_cases) if test_cases else 0
            sol.vocab_fitness = 1 - (vocab_error_count / len(test_cases)) if test_cases else 1

            print(f"  🔍 Solution {sol.id} logic_fitness: {sol.logic_fitness:.2f} ({passed_count}/{len(test_cases)})")
            print(f"  🧠 Solution {sol.id} vocab_fitness: {sol.vocab_fitness:.2f} ({vocab_error_count} vocab errors)")

    def _run_single_test(self, canonical_program, canonical_test_fact):
        if not canonical_program or not canonical_test_fact:
            return "invalid_input", "Missing program or test fact"

        goal = extract_goal(canonical_test_fact)
        if not goal:
            return "invalid_input", "Malformed test case"

        passed, reason = consult(canonical_program, goal)

        if not passed:
            if self._is_vocab_error(reason):
                return "vocab_error", reason
            return "logic_fail", reason

        return "logic_pass", None

    def _is_vocab_error(self, reason):
        # Detect Prolog arity or unknown predicate/variable errors
        arity_errors = [
            "Unknown procedure",
            "ERROR: ",  # General Prolog errors
            "Singleton variables",
            "Undefined procedure"
        ]
        return any(err_msg in reason for err_msg in arity_errors)
