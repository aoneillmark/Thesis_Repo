# evolve.py
import os
import random
from collections import deque

from test import EvolutionarySystem, generate_content
from prompts import PROLOG_GENERATION_PROMPT

# ────────────────────────────────────────────────────────────────────────────
# Configurable thresholds (spec-driven)
# ────────────────────────────────────────────────────────────────────────────
GOOD_THRESHOLD = 0.8   # ≥ 4/5 passes
BAD_THRESHOLD  = 0.0   # 0/5 passes

# ────────────────────────────────────────────────────────────────────────────
# Helper metrics
# ────────────────────────────────────────────────────────────────────────────
def compute_pass_rates(pass_matrix):
    """
    Convert a 0/1 vocabulary-pass matrix into per-row (program) and per-column
    (test) pass-rates.
    """
    if not pass_matrix:
        return [], []

    n_prog = len(pass_matrix)
    n_test = len(pass_matrix[0])

    prog_rates = [sum(row) / n_test for row in pass_matrix]
    test_rates = [
        sum(pass_matrix[i][j] for i in range(n_prog)) / n_prog
        for j in range(n_test)
    ]
    return prog_rates, test_rates


# cyclic deque = spec’s “alternate program / test” during catastrophe
_catastrophe = deque(["program", "test"])

def select_refactor_target(prog_rates, test_rates):
    """
    Implements Section 4 of the Vocabulary-Alignment Feedback Loop.
    """
    if all(r == 0 for r in prog_rates) and all(r == 0 for r in test_rates):
        target = _catastrophe[0]
        _catastrophe.rotate(-1)
        idx = random.randrange(len(prog_rates if target == "program" else test_rates))
        return target, idx

    min_prog = min(prog_rates)
    min_test = min(test_rates)

    if min_prog < min_test:
        return "program", prog_rates.index(min_prog)
    if min_test < min_prog:
        return "test", test_rates.index(min_test)

    # tie ⇒ test first
    return "test", test_rates.index(min_test)


# ────────────────────────────────────────────────────────────────────────────
# Repair helpers
# ────────────────────────────────────────────────────────────────────────────
def repair_program(system, p_idx, failing_tests):
    sol = system.solutions[p_idx]
    failing_snips = "\n".join(t.original_fact for t in failing_tests)
    prompt = f"""
    You are fixing ONE Prolog program so that its predicate names & arities
    match the tests shown below (keep the underlying logic).

    ----- PROGRAM -----
    {sol.original_program}

    ----- FAILING TESTS -----
    {failing_snips}

    Produce ONLY the corrected program.
    """
    updated = generate_content(prompt)
    # print(updated)
    if updated:
        sol.original_program = updated.strip()

def repair_test(system, t_idx, failing_progs):
    tc = system.test_cases[t_idx]
    prog_snips = "\n\n".join(p.original_program for p in failing_progs)
    other_tests = "\n".join(t.original_fact for t in system.test_cases if t != tc)
    prompt = f"""
    You are fixing ONE Prolog query so that its predicate names & arities
    match all programs shown below (keep query intent).

    ----- TEST -----
    {tc.original_fact}

    ----- FAILING PROGRAMS -----
    {prog_snips}

    Produce ONLY the corrected test fact.
    """
    updated = generate_content(prompt)
    # print(updated)
    if updated:
        tc.original_fact = updated.strip()


# ────────────────────────────────────────────────────────────────────────────
# Stage-1: vocabulary alignment loop
# ────────────────────────────────────────────────────────────────────────────
def run_vocab_alignment(system, max_iters=5):
    """
    Continually evaluate and repair until all programs & tests reach the
    GOOD_THRESHOLD pass-rate or we hit max_iters.
    """
    for it in range(1, max_iters + 1):
        print(f"\n🔄  Vocabulary alignment | Iteration {it}")
        system.evaluate_fitness(iteration=it)            # populates vocab_matrix (errors)

        # convert 1=edgecase(error) → pass=0/1
        error_matrix = system.evaluator.vocab_matrix
        pass_matrix  = [[1 - cell for cell in row] for row in error_matrix]

        prog_rates, test_rates = compute_pass_rates(pass_matrix)

        # stop?
        if all(r >= GOOD_THRESHOLD for r in prog_rates) \
           and all(r >= GOOD_THRESHOLD for r in test_rates):
            print("✅ Vocabulary aligned.")
            return True

        target, idx = select_refactor_target(prog_rates, test_rates)
        if target == "program":
            failing_tests = [
                system.test_cases[j] for j, ok in enumerate(pass_matrix[idx])
                if ok == 0
            ]
            print(f"🔧 Repairing program {idx} (ID: {system.solutions[idx].id})")
            repair_program(system, idx, failing_tests)
        else:
            failing_progs = [
                system.solutions[i] for i, row in enumerate(pass_matrix)
                if row[idx] == 0
            ]
            print(f"🔧 Repairing test {idx} (ID: {system.test_cases[idx].id})")
            repair_test(system, idx, failing_progs)

    print("❌ Failed to converge within max_iters.")
    return False


# ────────────────────────────────────────────────────────────────────────────
# Stage-2: logic refinement (placeholder)
# ────────────────────────────────────────────────────────────────────────────
def run_logic_refinement(system):
    print("\n🚀 Entering Stage-2 logic checks")
    system.evaluate_fitness()  # full metrics now

    ranked = sorted(system.solutions,
                    key=lambda s: s.logic_fitness,
                    reverse=True)
    print("\n🏅 Top solutions:")
    for sol in ranked[:3]:
        print(f"• {sol.id} | logic={sol.logic_fitness:.2f} | "
              f"vocab={sol.vocab_fitness:.2f}")


# ────────────────────────────────────────────────────────────────────────────
# Orchestration
# ────────────────────────────────────────────────────────────────────────────
def evolve_with_feedback(contract_text,
                         n_programs=5,
                         n_tests=5,
                         max_vocab_iters=5):
    """
    High-level driver:
      1 seed populations → 2 Stage-1 alignment → 3 Stage-2 refinement
    """
    system = EvolutionarySystem()

    # Seed tests & programs
    system.test_cases = system.generate_test_cases(n_tests, contract_text)
    # default_prompts = [(lambda ct: ct) for _ in range(n_programs)] 
    default_prompts = [
        lambda ct, p=PROLOG_GENERATION_PROMPT: p.format(contract_text=ct)
        for _ in range(n_programs)
    ]
    system.generate_solutions(n_programs, contract_text, default_prompts)

    # Stage-1
    if not run_vocab_alignment(system, max_iters=max_vocab_iters):
        return

    # Stage-2
    run_logic_refinement(system)


# ────────────────────────────────────────────────────────────────────────────
# CLI entry-point
# ────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    CONTRACT = "insurance_contract.txt"
    if not os.path.isfile(CONTRACT):
        print(f"✘ Cannot find {CONTRACT}")
        exit(1)

    with open(CONTRACT, "r", encoding="utf-8") as fh:
        contract_text = fh.read()

    evolve_with_feedback(contract_text, max_vocab_iters=10)
