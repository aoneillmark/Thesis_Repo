# evolve.py
import os
import random
from collections import deque, defaultdict

from suite_manager import SuiteManager
from utils import generate_content
from prompts import PROLOG_GENERATION_PROMPT, TEST_REPAIR_PROMPT

# ────────────────────────────────────────────────────────────────────────────
# Configurable thresholds (spec-driven)
# ────────────────────────────────────────────────────────────────────────────
# GOOD_THRESHOLD = 0.8   # ≥ 4/5 passes
# BAD_THRESHOLD  = 0.0   # 0/5 passes

# ────────────────────────────────────────────────────────────────────────────
# Helper metrics
# ────────────────────────────────────────────────────────────────────────────

def compute_pass_rates(pass_matrix):
    """
    Given a 0/1 *pass* matrix return per-program and per-test pass-rates.
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


def select_refactor_target(
    prog_rates,
    test_rates,
    iteration,
    repair_attempts,
    last_fixed_iter,
    *,
    max_repair_tries=2,   # give up after N failed repairs
    cooldown_iters=1      # skip an item for N iterations after we touch it
):
    """
    Pick the next program/test to refactor.

    An item is *ineligible* if:
      • we've already tried to repair it `max_repair_tries` times, or
      • it was last repaired ≤ `cooldown_iters` iterations ago.

    Returns (target_kind, idx) where target_kind ∈ {"program", "test"}.
    """

    candidates = []

    # ---------- gather eligible programs ----------
    for i, rate in enumerate(prog_rates):
        key = ("program", i)
        # exhausted?
        if repair_attempts[key] >= max_repair_tries:
            continue
        # still cooling-down?
        if key in last_fixed_iter and iteration - last_fixed_iter[key] <= cooldown_iters:
            continue
        candidates.append(("program", i, rate))

    # ---------- gather eligible tests -------------
    for j, rate in enumerate(test_rates):
        key = ("test", j)
        if repair_attempts[key] >= max_repair_tries:
            continue
        if key in last_fixed_iter and iteration - last_fixed_iter[key] <= cooldown_iters:
            continue
        candidates.append(("test", j, rate))

    # ---------- if everything is blocked ----------
    if not candidates:
        # fall back to original catastrophe alternation
        target = _catastrophe[0]
        _catastrophe.rotate(-1)
        idx = random.randrange(len(prog_rates if target == "program" else test_rates))
        return target, idx

    # ---------- normal case: choose worst pass-rate ----------
    target, idx, _ = min(candidates, key=lambda t: t[2])  # lower rate = worse
    return target, idx


# ────────────────────────────────────────────────────────────────────────────
# Seeding helper
# ────────────────────────────────────────────────────────────────────────────

# def _seed_manager(sm, contract_text, n_solutions, n_tests):
#     """Populate a blank SuiteManager with tests + candidate programs."""
#     sm.test_cases = sm.generate_test_cases(n_tests, contract_text)

#     prompt_fns = [
#         lambda ct, p=PROLOG_GENERATION_PROMPT: p.format(contract_text=ct)
#         for _ in range(n_solutions)
#     ]
#     sm.generate_solutions(n_solutions, contract_text, prompt_fns)
#     sm.evaluate_fitness(scope="seeds")


# ────────────────────────────────────────────────────────────────────────────
# Repair helpers
# ────────────────────────────────────────────────────────────────────────────

def repair_program(suite_manager, p_idx, failing_tests):
    sol = suite_manager.solutions[p_idx]
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
    if updated:
        sol.original_program = updated.strip()


def repair_test(suite_manager, t_idx, failing_progs):
    tc = suite_manager.test_cases[t_idx]
    prog_snips = "\n\n".join(p.original_program for p in failing_progs)
    prompt = TEST_REPAIR_PROMPT.format(
        prog_snips=prog_snips,
        failing_query=tc.original_fact,
    )
    updated = generate_content(prompt)
    if updated:
        tc.original_fact = updated.strip()


# ────────────────────────────────────────────────────────────────────────────
# New helpers & driver for post-Stage-1 processing
# ────────────────────────────────────────────────────────────────────────────

# def _collect_clean_sets(suite_manager):
#     """
#     Return (clean_solutions, covered_tests) where
#     clean_solutions  = [sol  | sol.vocab_fitness == 1.0]
#     covered_tests    = set of TestCase objs that at least one clean solution passes
#                        vocab-wise.
#     """
#     if not suite_manager.evaluator.vocab_matrix:
#         raise RuntimeError("evaluate_fitness() must be run first")

    

#     clean_sol_ids = [
#         i for i, row in enumerate(suite_manager.evaluator.vocab_matrix)
#         if all(row)  # every test passed vocab-wise
#     ]

#     clean_solutions = [suite_manager.solutions[i] for i in clean_sol_ids]

#     passed_test_idxs = {
#         j
#         for i in clean_sol_ids
#         for j, ok in enumerate(suite_manager.evaluator.vocab_matrix[i])
#         if ok
#     }
#     covered_tests = [suite_manager.test_cases[j] for j in sorted(passed_test_idxs)]
#     return clean_solutions, covered_tests


# ────────────────────────────────────────────────────────────────────────────
# Debug helper (can be removed later)
# ────────────────────────────────────────────────────────────────────────────

# def evolution_dummy(solutions, tests, m, n):
#     """
#     Temporary stand‑in that activates only when we have enough material.
#     Returns **True** when activated so the caller can break its loop.
#     """
#     if len(solutions) < m or len(tests) < n:
#         return False  # keep searching / generating

#     print("\n🚀  evolution_dummy ACTIVATED")
#     print("   Solutions:", [s.id for s in solutions[:m]])
#     print("   Tests    :", [t.id for t in tests[:n]])
#     return True


# ────────────────────────────────────────────────────────────────────────────
# Outer evolutionary driver
# ────────────────────────────────────────────────────────────────────────────

# def evolve_until_dummy(
#     contract_text,
#     *,
#     target_m=3,
#     target_n=5,
#     max_vocab_iters=5,
#     reseed_batch=3,
#     max_rounds=10,
#     GOOD_THRESHOLD=0.8,
#     BAD_THRESHOLD=0.0,
# ):
#     """
#     High‑level loop:
#       • spawn / extend a SuiteManager
#       • run vocab alignment
#       • harvest clean sets
#       • reseed until evolution_dummy() fires or we hit max_rounds
#     """
#     round_no = 0
#     suite_manager = SuiteManager()

#     # ── initial seed ────────────────────────────────────────────────────
#     _seed_manager(suite_manager, contract_text, target_m, target_n)

#     while round_no < max_rounds:
#         round_no += 1
#         print(f"\n================  OUTER ROUND {round_no}  ================\n")

#         # ── Stage‑1 alignment ───────────────────────────────────────────
#         aligned = run_vocab_alignment(
#             suite_manager,
#             round_tag = f"vocab_round_{round_no:02d}",
#             GOOD_THRESHOLD = GOOD_THRESHOLD,
#             BAD_THRESHOLD  = BAD_THRESHOLD,
#             max_iters      = max_vocab_iters,
#         )

#         # ────────────────────────────────────────────────────────────
#         # Alignment failed → salvage what we can, or restart from scratch
#         # ────────────────────────────────────────────────────────────
#         if not aligned:
#             clean_solutions, covered_tests = _collect_clean_sets(suite_manager)

#             # Nothing worth keeping?  Start totally fresh and continue.
#             if not clean_solutions:
#                 print("⚠️  Alignment failed – nothing clean; hard reset\n")
#                 suite_manager = SuiteManager()
#                 _seed_manager(suite_manager, contract_text, target_m, target_n)
#                 continue

#             print(
#                 f"⚠️  Alignment failed – salvaging {len(clean_solutions)} clean solutions "
#                 f"and {len(covered_tests)} tests"
#             )

#             # Start a *fresh* manager but keep the good stuff
#             suite_manager = SuiteManager()
#             suite_manager.solutions.extend(clean_solutions)
#             suite_manager.test_cases.extend(covered_tests)

#             # reseed only what’s missing
#             missing_sols = max(0, target_m - len(clean_solutions))
#             missing_tests = max(0, target_n - len(covered_tests))

#             if missing_tests:
#                 new_tests = suite_manager.generate_test_cases(
#                     max(missing_tests, reseed_batch),
#                     contract_text,
#                     existing_tests=suite_manager.test_cases,  # prevent dupes
#                 )
#                 suite_manager.test_cases.extend(new_tests)

#             if missing_sols:
#                 prompt_fns = [
#                     lambda ct, p=PROLOG_GENERATION_PROMPT: p.format(contract_text=ct)
#                     for _ in range(max(missing_sols, reseed_batch))
#                 ]
#                 suite_manager.generate_solutions(
#                     max(missing_sols, reseed_batch),
#                     contract_text,
#                     prompt_fns,
#                 )

#             continue  # go to next outer round

#         # ── Alignment succeeded: harvest clean sets ─────────────────────
#         clean_solutions, covered_tests = _collect_clean_sets(suite_manager)

#         # ⬇️  prune: keep only tests that are *currently* covered ---------
#         suite_manager.test_cases = covered_tests

#         print(
#             f"📈  Clean solutions so far: {len(clean_solutions)}  |  "
#             f"Covered tests: {len(covered_tests)}"
#         )

#         # ── Try to activate the dummy (placeholder for Stage‑2) ─────────
#         if evolution_dummy(clean_solutions, covered_tests, target_m, target_n):
#             print("✅  Done.")
#             return

#         # ── Otherwise reseed missing material and loop again ────────────
#         missing_sols = max(0, target_m - len(clean_solutions))
#         missing_tests = max(0, target_n - len(covered_tests))

#         if missing_tests:
#             new_tests = suite_manager.generate_test_cases(
#                 max(missing_tests, reseed_batch),
#                 contract_text,
#             )
#             suite_manager.test_cases.extend(new_tests)

#         if missing_sols:
#             prompt_fns = [
#                 lambda ct, p=PROLOG_GENERATION_PROMPT: p.format(contract_text=ct)
#                 for _ in range(max(missing_sols, reseed_batch))
#             ]
#             suite_manager.generate_solutions(
#                 max(missing_sols, reseed_batch),
#                 contract_text,
#                 prompt_fns,
#             )

#     print("❌  evolve_until_dummy: gave up after max_rounds without satisfying quotas.")


# ────────────────────────────────────────────────────────────────────────────
# Stage‑1: vocabulary alignment loop
# ────────────────────────────────────────────────────────────────────────────

def run_vocab_alignment(
    suite_manager,
    *,
    round_tag: str = "vocab_round_00",   # NEW – eg. "vocab_round_03"
    GOOD_THRESHOLD=0.8,
    BAD_THRESHOLD=0.0,
    max_iters=5,
):

    """
    Continually evaluate and repair until all programs & tests reach the
    GOOD_THRESHOLD pass‑rate or we hit max_iters.
    """
    repair_attempts = defaultdict(int)  # key = ("program"|"test", idx)
    last_fixed_iter = {}

    for it in range(1, max_iters + 1):
        print(f"\n🔄  Vocabulary alignment | Iteration {it}")
        scope = f"{round_tag}/iter_{it:02d}"
        suite_manager.evaluate_fitness(scope=scope)

        # error_matrix = suite_manager.evaluator.vocab_matrix
        # pass_matrix = [[1 - cell for cell in row] for row in error_matrix]

        prog_rates, test_rates = compute_pass_rates(suite_manager.evaluator.vocab_matrix)
        if not prog_rates or not test_rates:
            return False  # nothing evaluated

        # Success condition
        if all(r >= GOOD_THRESHOLD for r in prog_rates) and all(
            r >= GOOD_THRESHOLD for r in test_rates
        ):
            print("✅ Vocabulary aligned.")
            return True

        target, idx = select_refactor_target(
            prog_rates,
            test_rates,
            it,
            repair_attempts,
            last_fixed_iter,
        )

        if target == "program":
            failing_tests = [
                suite_manager.test_cases[j]
                for j, ok in enumerate(suite_manager.evaluator.vocab_matrix[idx])
                if ok == 0
            ]
            print(
                f"🔧 Repairing program {idx} (ID: {suite_manager.solutions[idx].id})"
            )
            repair_program(suite_manager, idx, failing_tests)
        else:
            failing_progs = [
                suite_manager.solutions[i]
                for i, row in enumerate(suite_manager.evaluator.vocab_matrix)
                if row[idx] == 0
            ]
            print(
                f"🔧 Repairing test {idx} (ID: {suite_manager.test_cases[idx].id})"
            )
            repair_test(suite_manager, idx, failing_progs)

        key = (target, idx)
        repair_attempts[key] += 1
        last_fixed_iter[key] = it

    print("❌ Failed to converge within max_iters.")
    return False


# ────────────────────────────────────────────────────────────────────────────
# Stage‑2: logic refinement (placeholder)
# ────────────────────────────────────────────────────────────────────────────

def run_logic_refinement(suite_manager):
    print("\n🚀 Entering Stage‑2 logic checks")
    suite_manager.evaluate_fitness()  # full metrics now

    ranked = sorted(
        suite_manager.solutions, key=lambda s: s.logic_fitness, reverse=True
    )

    print("\n🏅 Top solutions:")
    for sol in ranked[:3]:
        print(
            f"• {sol.id} | logic={sol.logic_fitness:.2f} | vocab="
            f"{sol.vocab_fitness:.2f}"
        )


# ────────────────────────────────────────────────────────────────────────────
# CLI entry‑point
# ────────────────────────────────────────────────────────────────────────────

# if __name__ == "__main__":
#     with open("insurance_contract.txt", encoding="utf-8") as fh:
#         contract_text = fh.read()

#     # e.g. want 4 vocab‑clean programs and 6 vocab‑clean tests
#     evolve_until_dummy(
#         contract_text,
#         target_m=4,
#         target_n=6,
#         max_vocab_iters=10,
#         reseed_batch=3,
#         max_rounds=10,
#         GOOD_THRESHOLD=0.8,
#         BAD_THRESHOLD=0.0,
#     )
