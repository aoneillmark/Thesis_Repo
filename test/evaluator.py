# evaluator.py
import os
import math
from prolog_compiler import consult, extract_goal

class Evaluator:
    def __init__(self, log_dir):
        self.log_dir = log_dir
        self.logic_matrix = []
        self.vocab_matrix = []
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
        test_log = os.path.join(self.log_dir, "test_cases.pl")
        with open(test_log, "w", encoding="utf-8") as f:
            for tc in test_cases:
                f.write((tc.canonical_fact or "❌ Invalid test case") + "\n")

    def evaluate(self, solutions, test_cases):
        print("\n--- 🏆 Starting Evaluation ---")
        self.save_solutions(solutions)
        self.save_test_cases(test_cases)

        logic_matrix = []
        vocab_matrix = []

        for sol in solutions:
            logic_row = []
            vocab_row = []
            logic_passes = 0
            vocab_errors = 0

            for tc in test_cases:
                result, _ = self._run_single_test(sol.canonical_program, tc.canonical_fact)

                # logic matrix: 1 if logic passed, else 0
                if result == "logic_pass":
                    logic_passes += 1
                    logic_row.append(1)
                else:
                    logic_row.append(0)

                # vocab matrix: 1 if vocab error, else 0
                if result == "vocab_error":
                    vocab_errors += 1
                    vocab_row.append(1)
                else:
                    vocab_row.append(0)

            sol.logic_fitness = logic_passes / len(test_cases) if test_cases else 0
            sol.vocab_fitness = 1 - (vocab_errors / len(test_cases)) if test_cases else 0

            logic_matrix.append(logic_row)
            vocab_matrix.append(vocab_row)

            print(f"  🔍 Solution {sol.id} logic_fitness: {sol.logic_fitness:.2f} "
                  f"({logic_passes}/{len(test_cases)})")
            print(f"  📝 Solution {sol.id} vocab_fitness: {sol.vocab_fitness:.2f} "
                  f"({vocab_errors}/{len(test_cases)})")

        # Compute per-test confidence & discrimination only for logic
        logic_fitnesses = [sol.logic_fitness for sol in solutions]
        self._compute_confidence(test_cases, logic_matrix, logic_fitnesses, "logic_confidence")
        self._compute_discrimination(test_cases, logic_matrix, "logic_discrimination")

        # Expose the raw matrices if you need them downstream
        self.logic_matrix = logic_matrix
        self.vocab_matrix = vocab_matrix

    def _compute_confidence(self, test_cases, matrix, fitness_vector, attr_name):
        total = len(matrix)
        total_weight = sum(fitness_vector)
        for j, tc in enumerate(test_cases):
            if total_weight == 0:
                conf = 0.0
            else:
                passed_w = sum(matrix[i][j] * fitness_vector[i] for i in range(total))
                conf = passed_w / total_weight
            setattr(tc, attr_name, conf)
            print(f"  🧪 Test {tc.id} {attr_name}: {conf:.2f}")

    def _compute_discrimination(self, test_cases, matrix, attr_name):
        total = len(matrix)
        for j, tc in enumerate(test_cases):
            pass_count = sum(matrix[i][j] for i in range(total))
            p = pass_count / total if total else 0.0
            if p in (0.0, 1.0):
                disc = 0.0
            else:
                disc = -(p * math.log2(p) + (1 - p) * math.log2(1 - p))
            setattr(tc, attr_name, disc)
            print(f"  🧪 Test {tc.id} {attr_name}: {disc:.2f}")

    def _run_single_test(self, program, fact):
        if not program or not fact:
            return "invalid_input", "Missing program or test fact"
        goal = extract_goal(fact)
        if not goal:
            return "invalid_input", "Malformed test case"
        passed, reason = consult(program, goal)
        if not passed:
            if self._is_vocab_error(reason):
                return "vocab_error", reason
            return "logic_fail", reason
        return "logic_pass", None

    def _is_vocab_error(self, reason):
        checks = [
            "Unknown procedure",
            "ERROR: ",
            "Singleton variables",
            "Undefined procedure"
        ]
        return any(msg in reason for msg in checks)
