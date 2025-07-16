import math
# import os
# import datetime
# timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
# log_dir = f"logs/run_{timestamp}"
# os.makedirs(log_dir, exist_ok=True)

def calculate_test_conf(test_idx, code_population, matrix):
    passed = 0.0
    total = 0.0
    for c in code_population:
        code_idx = int(c['idx'])
        fitness = c['fitness']
        if matrix[code_idx][test_idx]:
            passed += fitness
        total += fitness
    return 0.0 if total == 0.0 else passed / total

def calculate_test_disc(test_idx, code_population, matrix):
    passed = 0.0
    total = 0.0
    for c in code_population:
        code_idx = int(c['idx'])
        if matrix[code_idx][test_idx]:
            passed += 1
        total += 1
    p = 0.0 if total == 0.0 else passed / total
    if p == 0.0 or p == 1.0:
        return 0.0
    return -(p * math.log2(p) + (1 - p) * math.log2(1 - p))

# def save_solutions(solutions, iteration=None):
#     iter_dir = os.path.join(log_dir, f"iter_{iteration:02d}") if iteration else log_dir
#     os.makedirs(iter_dir, exist_ok=True)
#     for sol in solutions:
#         sol.canonical_program = sol.original_program
#         fname = os.path.join(iter_dir, f"solution_{sol.id}.pl")
#         with open(fname, "w", encoding="utf-8") as f:
#             f.write(sol.canonical_program or "❌ No canonical program available.")

# def save_test_cases(test_cases, iteration=None):
#     iter_dir = os.path.join(log_dir, f"iter_{iteration:02d}") if iteration else log_dir
#     os.makedirs(iter_dir, exist_ok=True)
#     for tc in test_cases:
#         tc.canonical_fact = tc.original_fact
#     test_log = os.path.join(iter_dir, "test_cases.pl")
#     with open(test_log, "w", encoding="utf-8") as f:
#         for tc in test_cases:
#             f.write((tc.canonical_fact or "❌ Invalid test case") + "\n")