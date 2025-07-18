# evaluator.py
import os
import math
from prolog_compiler import consult, extract_goal
import re

class Evaluator:
    def __init__(self, log_dir):
        self.log_dir = log_dir
        self.logic_matrix = []
        self.vocab_matrix = []
        self.SIG_RE = re.compile(r'([a-z]\w*)\s*\(([^:-]*)')     # crude but fast
        os.makedirs(self.log_dir, exist_ok=True)

    # def save_solutions(self, solutions):
    #     for sol in solutions:
    #         sol.canonical_program = sol.original_program
    #         fname = os.path.join(self.log_dir, f"solution_{sol.id}.pl")
    #         with open(fname, "w", encoding="utf-8") as f:
    #             f.write(sol.canonical_program or "❌ No canonical program available.")


    # def save_test_cases(self, test_cases):
    #     for tc in test_cases:
    #         tc.canonical_fact = tc.original_fact
    #     test_log = os.path.join(self.log_dir, "test_cases.pl")
    #     with open(test_log, "w", encoding="utf-8") as f:
    #         for tc in test_cases:
    #             f.write((tc.canonical_fact or "❌ Invalid test case") + "\n")

    # def signature_set(self, code: str) -> set[tuple[str, int]]:
    #     """Return {(name, arity), …} for every *head* in a Prolog program."""
    #     return {
    #         (name, len([a for a in args.split(',') if a.strip()]))
    #         for name, args in self.SIG_RE.findall(code)
    #     }

    # def has_arity_mismatch(self, program: str, goal: str) -> bool:
    #     sigs = self.signature_set(program)
    #     match = self.SIG_RE.match(goal)
    #     if not match:
    #         return True  # Treat it as a mismatch if the format is unrecognized
    #     g_name, g_args = match.groups()
    #     return (g_name, len([a for a in g_args.split(',') if a.strip()])) not in sigs

    def save_solutions(self, solutions, iteration=None):
        iter_dir = os.path.join(self.log_dir, f"iter_{iteration:02d}") if iteration else self.log_dir
        os.makedirs(iter_dir, exist_ok=True)
        for sol in solutions:
            sol.canonical_program = sol.original_program
            fname = os.path.join(iter_dir, f"solution_{sol.id}.pl")
            with open(fname, "w", encoding="utf-8") as f:
                f.write(sol.canonical_program or "❌ No canonical program available.")

    def save_test_cases(self, test_cases, iteration=None):
        iter_dir = os.path.join(self.log_dir, f"iter_{iteration:02d}") if iteration else self.log_dir
        os.makedirs(iter_dir, exist_ok=True)
        for tc in test_cases:
            tc.canonical_fact = tc.original_fact
        test_log = os.path.join(iter_dir, "test_cases.pl")
        with open(test_log, "w", encoding="utf-8") as f:
            for tc in test_cases:
                f.write((tc.canonical_fact or "❌ Invalid test case") + "\n")

    def evaluate(self, solutions, test_cases, iteration=None):
        print("\n--- 🏆 Starting Evaluation ---")
        self.save_solutions(solutions, iteration)
        self.save_test_cases(test_cases, iteration)

        logic_matrix = []
        vocab_matrix = []

        # Evaluate each solution against each test
        for sol in solutions:
            logic_row = []
            vocab_row = []
            logic_passes = 0
            vocab_errors = 0

            for tc in test_cases:
                result, reason = self._run_single_test(sol.canonical_program, tc.canonical_fact)
                # print(reason)

                # logic matrix: 1 if logic passed, else 0
                if result == "logic_pass":
                    logic_passes += 1
                    logic_row.append(1)
                else:
                    # print(f"        ↳ reason: {reason}")      # NEW LINE
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
                  f"({len(test_cases)-vocab_errors}/{len(test_cases)})")

        # Compute per-test metrics
        logic_fitnesses = [sol.logic_fitness for sol in solutions]
        self._compute_confidence(test_cases, logic_matrix, logic_fitnesses, "logic_confidence")
        self._compute_discrimination(test_cases, logic_matrix, "logic_discrimination")

        # Print test-level fitness for logic and vocab
        num_sols = len(solutions)
        for j, tc in enumerate(test_cases):
            # logic pass count
            pass_count = sum(logic_matrix[i][j] for i in range(num_sols))
            logic_rate = pass_count / num_sols if num_sols else 0
            # vocab error count
            error_count = sum(vocab_matrix[i][j] for i in range(num_sols))
            vocab_rate = 1 - (error_count / num_sols) if num_sols else 0
            print(f"  🧪 Test {tc.id} logic_fitness: {logic_rate:.2f} ({pass_count}/{num_sols})")
            print(f"  📝 Test {tc.id} vocab_fitness: {vocab_rate:.2f} "
                  f"({num_sols-error_count}/{num_sols})")

        # Expose raw matrices and updated test attributes downstream
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
        # if self.has_arity_mismatch(program, goal):
        #     return "vocab_error", "Predicate name / arity mismatch"


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
            "Undefined procedure",
            "Timeout"
        ]
        return any(msg in reason for msg in checks)
