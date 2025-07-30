# coco_evo.py - CoCoEvo-style evolutionary loop
# ==================================================
# This module plugs into the existing SuiteManager / Evaluator stack and provides a
# two-population co-evolution of **programs** (Prolog encodings) and **tests**
# (logical queries).  It assumes that Stage-1 vocabulary alignment from
# `evolve.run_vocab_alignment` is available and re-uses it to make sure any brand-new
# individuals that the engine spawns are vocabulary-clean *before* they
# participate in logic-level evolution.
#
# ───────────────────────────────────────────────────────────────────────────────
# Public API
# ───────────────────────────────────────────────────────────────────────────────
#   from suite_manager import SuiteManager
#   from coco_evo import CoCoEvoEngine
#
#   sm = SuiteManager()                 # with *vocab-clean* initial pop
#   ... (seed sm via your existing flow) ...
#   engine = CoCoEvoEngine(sm, contract_text)
#   engine.run()                        # in-place evolution - populations live in sm
#
# ───────────────────────────────────────────────────────────────────────────────
# The engine will:
#   1. Keep confidence/discrimination metrics updated for *logic* fitness.
#   2. Maintain Pareto fronts for tests (confidence & discrimination).
#   3. Spawn new programs/tests via LLM crossover & mutation.
#   4. **Immediately** pipe any spawn that fails vocab alignment back through the
#      Stage-1 repair loop (run_vocab_alignment), isolating repairs to only the
#      newcomers.  Once repaired, they re-enter the evolutionary population.
#
#
# ───────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import math
import random
import logging
from typing import List, Dict, Tuple, Optional

from suite_manager import SuiteManager, CandidateSolution, TestCase
from evolve import run_vocab_alignment                 # Stage-1 repair
from utils import generate_content                     # → calls the LLM
from prompts import (
    PROGRAM_CROSSOVER_PROMPT,
    PROGRAM_MUTATION_PROMPT,
    TEST_MUTATION_PROMPT,
    TEST_GENERATION_PROMPT,
    PROLOG_GENERATION_PROMPT
)

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper metrics (confidence & discrimination) - logic-based
# ---------------------------------------------------------------------------

def calculate_test_conf(test_idx: int,
                        code_population: List[Dict],
                        matrix: List[List[int]],
                        solutions: List[CandidateSolution]) -> float:
    passed = 0.0
    total = 0.0
    for c in code_population:
        try:
            p_idx = solutions.index(c["solution"])
        except ValueError:
            continue
        fitness = c["logic_fitness"]
        if matrix[p_idx][test_idx]:
            passed += fitness
        total += fitness
    return 0.0 if total == 0.0 else passed / total



def calculate_test_disc(test_idx: int,
                        code_population: List[Dict],
                        matrix: List[List[int]],
                        solutions: List[CandidateSolution]) -> float:
    passed = 0
    for c in code_population:
        try:
            p_idx = solutions.index(c["solution"])
        except ValueError:
            continue
        if matrix[p_idx][test_idx]:
            passed += 1
    total = len(code_population)
    p = 0.0 if total == 0 else passed / total
    if p in (0.0, 1.0):
        return 0.0
    return -(p * math.log2(p) + (1 - p) * math.log2(1 - p))

# ---------------------------------------------------------------------------
# Pareto utilities for multi-objective test selection
# ---------------------------------------------------------------------------

def dominates(a: Dict, b: Dict, metrics: List[str]) -> bool:
    """Return ``True`` iff *a* dominates *b* on all metrics (≥) and > on ≥1."""
    better_or_equal = all(a[m] >= b[m] for m in metrics)
    strictly_better = any(a[m] > b[m] for m in metrics)
    return better_or_equal and strictly_better


def build_pareto_front(pop: List[Dict], metrics: List[str]) -> List[List[Dict]]:
    """Layered Pareto fronts (non-dominated sorting)."""
    remaining = pop[:]
    fronts: List[List[Dict]] = []
    while remaining:
        front = [p for p in remaining
                 if not any(dominates(q, p, metrics) for q in remaining if q is not p)]
        fronts.append(front)
        remaining = [p for p in remaining if p not in front]
    return fronts


def pareto_selection(test_population: List[Dict],
                     select_size: int,
                     metrics: List[str],
                     mode: str = "auto",
                     filter_algo: str = "") -> List[Dict]:
    """Heuristic from the CoCoEvo paper for picking a Pareto-optimal subset."""
    fronts = build_pareto_front(test_population, metrics)
    selected: List[Dict] = fronts[0]
    for i in range(1, len(fronts)):
        if len(selected) >= select_size:
            break
        f = fronts[i]
        if len(selected) + len(f) <= select_size:
            selected += f
        else:
            if mode == "strict":
                f_sorted = sorted(f, key=lambda x: x["fitness"], reverse=True)
                selected += f_sorted[: select_size - len(selected)]
            elif mode == "auto":
                selected += random.sample(f, select_size - len(selected))
            else:
                raise ValueError("pareto_selection: unknown mode")
    if filter_algo == "avg":
        avg_fit = sum(t["fitness"] for t in test_population) / max(1, len(test_population))
        selected = [s for s in selected if s["fitness"] >= avg_fit]
    return selected

# ---------------------------------------------------------------------------
# Core Engine
# ---------------------------------------------------------------------------

class CoCoEvoEngine:
    """Co-evolution driver maintaining vocabulary-clean invariants."""

    # ---------------------------------------------------------------------
    # Construction
    # ---------------------------------------------------------------------
    def __init__(self,
                 suite_manager: SuiteManager,
                 contract_text: str,
                 max_generations: int = 50,
                 pop_cap_programs: int = 30,
                 pop_cap_tests: int = 30,
                 max_reseed_attempts: int = 5,
                 rng_seed: Optional[int] = None):
        self.sm = suite_manager
        self.contract_text = contract_text
        self.max_generations = max_generations
        self.pop_cap_programs = pop_cap_programs
        self.pop_cap_tests = pop_cap_tests
        self.max_reseed_attempts = max_reseed_attempts
        self.rng = random.Random(rng_seed)

        # Caches - re-computed each generation
        self.logic_matrix: List[List[int]] = []   # rows = programs, cols = tests
        self.code_population: List[Dict] = []     # {'idx', 'logic_fitness'}
        self.test_population: List[Dict] = []     # {'idx', conf, disc, fitness}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    # 1) Vocab alignment -------------------------------------------------
    def _ensure_vocab_alignment(self,
                                new_prog_idxs: List[int] | None = None,
                                new_test_idxs: List[int] | None = None) -> None:
        """Run Stage-1 repair on newly spawned individuals **only**."""
        return run_vocab_alignment(self.sm, max_iters=self.max_reseed_attempts)

    # 1-b) Emergency reseed ---------------------------------------------
    def _reseed_populations(self):
        """Hard-reset both populations when vocab repair cannot recover fitness."""
        logger.warning("Reseeding ALL programs & tests - vocab repair exhausted with 0/N fitness.")

        # Drop existing individuals
        self.sm.solutions.clear()
        self.sm.test_cases.clear()

        # Fresh seed via existing spawning helpers - ensures Stage-1 alignment
        # for _ in range(self.pop_cap_programs):
        #     self._spawn_program()
        # for _ in range(self.pop_cap_tests):
        #     self._spawn_test()
        
        super_secret_prompt = "\n\nAdditionally, here are the test cases you will be tested on; make sure to match the predicate signature and arity. {test_cases}"

        sol_prompts = [
            (lambda ct, p=PROLOG_GENERATION_PROMPT, secret=super_secret_prompt: 
            p.format(contract_text=ct) + secret.format(
                test_cases="\n".join(tc.original_fact for tc in self.sm.test_cases)))
            for _ in range(self.pop_cap_programs)
        ]

        self.sm.generate_solutions(
            num_solutions=self.pop_cap_programs,
            contract_text=self.contract_text,
            prompt_fns=sol_prompts
        )
        
        self.sm.generate_solutions(
            num_solutions=self.pop_cap_programs,
            contract_text=self.contract_text,
        )

        # One final vocab alignment pass for the brand-new population
        self._ensure_vocab_alignment()
    
    # ---------------------------------------------------------------------------
    # Cosine Scheduler
    # ---------------------------------------------------------------------------
    def cosine_scheduler(self, step: int, total_steps: int,
                        max_p: float = 0.9, min_p: float = 0.1) -> float:
        """
        Cosine-annealed probability between `max_p` (at step 0)
        and `min_p`  (at step total_steps).
        """
        cos_val = (1 - math.cos(math.pi * step / total_steps)) / 2   # 1→0
        return min_p + (max_p - min_p) * cos_val
    # ---------------------------------------------------------------------------

    # --------------------------------------------------------------
    # (A) Helper: locate current best program after each evaluation
    # --------------------------------------------------------------
    def _best_program(self) -> Tuple[int, CandidateSolution]:
        best = max(self.code_population, key=lambda x: x["logic_fitness"])
        return self.sm.solutions.index(best["solution"]), best["solution"]


    # --------------------------------------------------------------
    # (B) Helper: run Pbest on all tests and build feedback object
    # --------------------------------------------------------------
    def _program_feedback(self, p_idx: int) -> Dict:
        status = self.logic_matrix[p_idx]              # 1 = pass, 0 = fail
        failing = [self.sm.test_cases[j].original_fact
                for j, ok in enumerate(status) if not ok]
        passing  = [self.sm.test_cases[j].original_fact
                for j, ok in enumerate(status) if ok]
        return {"failing": failing, "passing": passing}


    # --------------------------------------------------------------
    # (C) Spawn tests *with feedback*
    # --------------------------------------------------------------
    def _spawn_test_feedback(self, feedback: Dict) -> Optional[int]:
        prompt = TEST_GENERATION_PROMPT.format(
            contract_text=self.contract_text,
            program=self._best_program()[1].original_program,
            failing="\n".join(feedback["failing"][:5]),  # show up to 5
            passing="\n".join(feedback["passing"][:5]),
        )
        raw = generate_content(prompt)
        if not raw or not raw.strip():
            return None
        tc = TestCase(raw.strip())
        self.sm.test_cases.append(tc)
        return len(self.sm.test_cases) - 1

    # 2) Evaluation & metric computation --------------------------------
    def _evaluate_logic(self, *, scope: str):
        """Populate ``logic_matrix`` then derive program & test metrics."""
        self.sm.evaluate_fitness(scope=scope)
        self.logic_matrix = self.sm.evaluator.logic_matrix or []

        # Filter out solutions whose program failed to compile / is empty
        valid_pairs = [(i, s) for i, s in enumerate(self.sm.solutions)
                       if (s.original_program and s.original_program.strip())]
        if len(valid_pairs) < len(self.sm.solutions):
            self.sm.solutions = [s for _, s in valid_pairs]
            self.logic_matrix = [self.logic_matrix[i] for i, _ in valid_pairs]

        # Program logic fitness = proportion of tests passed
        self.code_population = []
        # for idx, row in enumerate(self.logic_matrix):
        #     passed = sum(row)
        #     total = len(row) if row else 1
        #     logic_fitness = passed / total
        #     self.code_population.append({
        #         "idx": idx,
        #         "logic_fitness": logic_fitness,
        #     })
        for new_idx, (old_idx, _) in enumerate(valid_pairs):
            row = self.logic_matrix[new_idx]
            passed = sum(row)
            total = len(row) if row else 1
            logic_fitness = passed / total
            self.code_population.append({
                "solution": self.sm.solutions[new_idx],
                "logic_fitness": logic_fitness,
            })



        # Test metrics
        self.test_population = []
        for j in range(len(self.sm.test_cases)):
            conf = calculate_test_conf(j, self.code_population, self.logic_matrix, self.sm.solutions)
            disc = calculate_test_disc(j, self.code_population, self.logic_matrix, self.sm.solutions)
            fitness = 0.5 * conf + 0.5 * disc
            self.test_population.append({
                "idx": j,
                "conf": conf,
                "disc": disc,
                "fitness": fitness,
            })

    # 3) Selection helpers -----------------------------------------------
    def _tournament_select(self, k: int = 2) -> CandidateSolution:
        contenders = self.rng.sample(self.code_population, k)
        winner = max(contenders, key=lambda x: x["logic_fitness"])
        return winner["solution"]

    
    def _random_select(self) -> CandidateSolution:
        """Select a random solution from the population."""
        if not self.sm.solutions:
            return None
        return self.rng.choice(self.sm.solutions)

    # 4) LLM-driven genetic operators ------------------------------------
    def _crossover_programs(self, p1: CandidateSolution, p2: CandidateSolution) -> str:
        prompt = PROGRAM_CROSSOVER_PROMPT.format(
            parent_a=p1.original_program,
            parent_b=p2.original_program,
            contract_text=self.contract_text,
        )
        result = generate_content(prompt)
        if not result:
            print("Crossover failed - empty result from LLM.")
        return result or ""

    def _mutate_program(self, prog: CandidateSolution) -> str:
        prompt = PROGRAM_MUTATION_PROMPT.format(
            program=prog.original_program,
            contract_text=self.contract_text,
        )
        result = generate_content(prompt)
        if not result:
            print("Mutation failed - empty result from LLM.")
        return result or ""

    def _spawn_program(self, use_crossover: bool = True, pa: Optional[CandidateSolution] = None, pb: Optional[CandidateSolution] = None) -> Tuple[Optional[int], Optional[CandidateSolution]]:
        """Create a child program; return ``(idx, sol)`` or ``(None, None)``."""
        if use_crossover and len(self.sm.solutions) >= 2:
            raw = self._crossover_programs(pa, pb)
        else:
            raw = self._mutate_program(pa)
        if not raw.strip():
            print("LLM returned empty program - spawn aborted.")
            return None, None
        
        child = CandidateSolution(self.contract_text, program_text=raw)
        if not child.original_program or not child.original_program.strip():
            print("❌ Spawned program is empty or invalid.")
            return None, None

        self.sm.solutions.append(child)
        return len(self.sm.solutions) - 1, child

    # --------------------------  TESTS  ----------------------------------
    def _mutate_test(self, tc: TestCase) -> str:
        prompt = TEST_MUTATION_PROMPT.format(
            test=tc.original_fact,
            contract_text=self.contract_text,
        )
        result = generate_content(prompt)
        if not result:
            print("Test mutation failed - empty result from LLM.")
        return result or ""

    # def _spawn_test(self) -> Tuple[Optional[int], Optional[TestCase]]:
    #     """Spawn a *predicate-shape-preserving* test case.

    #     The new strategy is:
    #     • **Prefer mutation** of an existing test (prob = `mutation_rate`).
    #     • If generating from scratch, pass *up to 5 exemplar tests* to the LLM and
    #       *explicitly* instruct it to keep *exactly the same* predicate signatures &
    #       arity.  This prevents the engine from introducing facts that the logic
    #       vocabulary cannot recognise.
    #     """
    #     use_mutation = self.sm.test_cases and (self.rng.random() < self.mutation_rate)

    #     if use_mutation:
    #         parent = self.rng.choice(self.sm.test_cases)
    #         raw = self._mutate_test(parent)
    #     else:
    #         exemplars = "\n".join(t.original_fact for t in self.sm.test_cases[:5]) if self.sm.test_cases else ""
    #         guidance = (
    #             """
    #             You are generating a *new* logical query (test case) to challenge the 
    #             current Prolog encoding of the insurance contract.  The test *must* 
    #             use **exactly the same predicate names and number of arguments** as 
    #             those shown below.  Think of a novel *scenario* or edge-case that the 
    #             contract might cover, but keep the *shape* identical.  
    #             Return a test in a similar format as the exemplars, matching the signature (arity and arguments).
    #             """ # This is an example of the format you should use, but make sure to use the predicate signatures provided in the exemplar tests later: \n % Args: Name, Age, Activity \n test("Scenario description", is_claim_covered("John", 67, "skydiving")).
    #         )
    #         prompt = (
    #             f"{TEST_GENERATION_PROMPT.format(contract_text=self.contract_text)}\n\n{guidance}\n\n"  # base task description
    #             f"# Exemplar tests (keep shape)\n{exemplars}\n\n# → New test:"
    #         )
    #         raw = generate_content(prompt)
    #         if not raw:
    #             print("Test generation failed - empty result from LLM.")
    #     if not raw or not raw.strip():
    #         return None, None

    #     tc = TestCase(raw.strip())
    #     self.sm.test_cases.append(tc)
    #     return len(self.sm.test_cases) - 1, tc

    # 5) Population culling ----------------------------------------------
    # --------------------------------------------------------------
    #  (helpers) population culling
    # --------------------------------------------------------------
    def _trim_programs(self) -> None:
        self.code_population.sort(key=lambda x: x["logic_fitness"], reverse=True)
        keep_solutions = {d["solution"] for d in self.code_population[:self.pop_cap_programs]}
        self.sm.solutions = [s for s in self.sm.solutions if s in keep_solutions]


    
    def _trim_tests(self) -> None:
        """Pareto-filter the test suite by (confidence, discrimination)."""
        selected = pareto_selection(
            self.test_population,
            self.pop_cap_tests,
            metrics=["conf", "disc"],
        )
        keep = {d["idx"] for d in selected}
        self.sm.test_cases = [t for j, t in enumerate(self.sm.test_cases) if j in keep]

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self) -> None:
        """Execute co-evolution for ``max_generations`` generations."""
        flag = False
        while not flag and self.max_reseed_attempts > 0:
            if self._ensure_vocab_alignment():   # Defensive repair for initial pop
                flag = True
            elif self.max_reseed_attempts > 0:
                logger.warning("Initial population failed vocab alignment - reseeding.")
                self.max_reseed_attempts -= 1
                self._reseed_populations()
            else:
                logger.error("Exhausted vocab repair attempts - cannot proceed.")
                raise RuntimeError("Vocab alignment failed after multiple attempts.")

        self._evaluate_logic(scope="initial")

        for gen in range(1, self.max_generations + 1):
            print(f"\n═══════ CoCoEvo | Generation {gen}/{self.max_generations} ═══════")

            # --- Calculate crossover rate for this generation ---
            x = self.cosine_scheduler(gen-1, self.max_generations)  # 0-indexed
            self.crossover_rate = x                            # update for this gen

            num_children = self.pop_cap_programs               # size in Algorithm 1
            num_cross = int(num_children * self.crossover_rate)
            num_mut   = num_children - num_cross
            # ----------------------------------------------------


            # Evaluate & compute metrics (PRE-spawn)
            # pre = f"evo_gen_{gen:04d}/pre"
            # self._evaluate_logic(scope=pre)

            # # --- Emergency reseed check --------------------------------
            # if self.code_population and all(p["logic_fitness"] == 0.0 for p in self.code_population):
            #     self._reseed_populations()
            #     # Re-evaluate after reseed and skip normal spawn/cull for this gen
            #     self._evaluate_logic(scope=f"evo_gen_{gen:04d}/reseed")
            #     continue

            # ---------------- Spawn ----------------
            # -------- (Mutate and Crossover) -------
            # new_prog_idxs: List[int] = []
            # new_test_idxs: List[int] = []
            # for _ in range(max(1, self.pop_cap_programs // 10)):
            #     idx, _ = self._spawn_program()
            #     if idx is not None:
            #         new_prog_idxs.append(idx)
            # for _ in range(max(1, self.pop_cap_tests // 10)):
            #     idx, _ = self._spawn_test()
            #     if idx is not None:
            #         new_test_idxs.append(idx)


            # Spawn new programs
            new_prog_idxs: List[int] = []
            new_test_idxs: List[int] = []
            for _ in range(num_cross):
                # NEED TO SELECT TWO PARENTS FOR CROSSOVER
                # USE _tournament_select() TO PICK TWO PROGRAMS
                pa, pb = self._tournament_select(), self._tournament_select() # NOTE: Should have a checker to ensure pa != pb
                idx, _ = self._spawn_program(use_crossover=True, pa=pa, pb=pb)
                if idx is not None:
                    new_prog_idxs.append(idx)
            for _ in range(num_mut):
                pa = self._random_select()
                idx, _ = self._spawn_program(use_crossover=False, pa=pa)
                if idx is not None:
                    new_prog_idxs.append(idx)
            
            # NOTE: not sure yet if to have vocab alignment inside evolution loop
            #       or just rely on Stage-1 repair before the run.
            # # Ensure vocabulary alignment for new programs 
            # if new_prog_idxs:
            #     print(f"• Ensuring vocab alignment for {len(new_prog_idxs)} new programs …")
            #     if not self._ensure_vocab_alignment(new_prog_idxs):
            #         print("❌ Vocab alignment failed for new programs - reseeding.")
            #         self._reseed_populations()
            #         continue # this generation is skipped


            # Evaluate new programs (P') on T
            # Each p' in P' gets fitness based on T (conf_P') (not test confidence)
            # P = greedy(P ∪ P', conf_P,P') # I believe conf_P,P' is the logic_fitness of sets P (old programs) and P' (new programs)
            #   Meaning we evaluate the new programs on the existing tests
            #   and select the best-performing programs from both the old and new populations.
            if new_prog_idxs:
                print(f"• Evaluating {len(new_prog_idxs)} new programs on existing tests …")
                self._evaluate_logic(scope=f"evo_gen_{gen:04d}/spawned_programs")
            else:
                print("• No new programs spawned this generation.")
            # Cull programs based on logic fitness
            self._trim_programs()  # This will keep the top-k programs by logic_fitness


            # Spawn new tests
            # 1. Get champion and its feedback
            best_idx, best_prog = self._best_program()
            feedback = self._program_feedback(best_idx)
            # 2. Spawn test-offspring that specifically target Pbest
            num_new_tests = max(1, self.pop_cap_tests // 10) 
            for _ in range(num_new_tests):
                idx = self._spawn_test_feedback(feedback)
                if idx is not None:
                    new_test_idxs.append(idx)
            
            # NOTE: not sure yet if to have vocab alignment inside evolution loop
            #       or just rely on Stage-1 repair before the run.
            # # Ensure vocabulary alignment for new tests
            # if new_test_idxs:
            #     print(f"• Ensuring vocab alignment for {len(new_test_idxs)} new tests …")
            #     if not self._ensure_vocab_alignment(new_test_idxs):
            #         print("❌ Vocab alignment failed for new tests - reseeding.")
            #         self._reseed_populations()
            #         continue  # this generation is skipped

            # NOTE: legacy code for vocab repair - not used in the current flow
            # # Vocabulary repair for newcomers
            # if new_prog_idxs or new_test_idxs:
            #     print(f"• Vocab repair for {len(new_prog_idxs)} programs / {len(new_test_idxs)} tests …")
            #     if (self._ensure_vocab_alignment(new_prog_idxs, new_test_idxs)):
            #         print("  ✅ Vocab alignment successful.")
            #     else:
            #         print("  ❌ Vocab alignment failed.")
            #         # Emergency reseed if vocab repair fails?
            #         self._reseed_populations()
            #         continue  # this generation is skipped

            # After new test generation;
            post = f"evo_gen_{gen:04d}/post"
            # T = T ∪ T' 
            # Evaluate P on T ∪ T' (i.e. re-evaluate all programs on all tests)
            # Calculate conf_T, discrimination disc_T
            # T = Pareto_selection(T, pop_cap_tests, metrics=['conf', 'disc'])
            print("• Evaluating all programs on all tests (including new ones) …")
            self._evaluate_logic(scope=post)
            # Cull tests based on Pareto selection
            self._trim_tests()  # This will keep the top-k tests by (conf, disc)

        print("✅ CoCoEvo run completed.")

