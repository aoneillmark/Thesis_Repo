# coco_evo.py – CoCoEvo-style evolutionary loop
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
#   engine.run()                        # in-place evolution – populations live in sm
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
from evolve import run_vocab_alignment                 # Stage‑1 repair
from utils import generate_content                     # → calls the LLM
from prompts import (
    PROGRAM_CROSSOVER_PROMPT,
    PROGRAM_MUTATION_PROMPT,
    TEST_MUTATION_PROMPT,
    TEST_GENERATION_PROMPT,
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
# Helper metrics (confidence & discrimination) – logic‑based
# ---------------------------------------------------------------------------

def calculate_test_conf(test_idx: int,
                        code_population: List[Dict],
                        matrix: List[List[int]]) -> float:
    """Weighted confidence of *test* ``test_idx`` using program *logic_fitness*.

    The weight of each program is its ``logic_fitness``; tests passed by
    stronger programs contribute more to the confidence score.
    """
    passed = 0.0
    total = 0.0
    for c in code_population:
        p_idx = int(c["idx"])
        fitness = c["logic_fitness"]
        if matrix[p_idx][test_idx]:
            passed += fitness
        total += fitness
    return 0.0 if total == 0.0 else passed / total


def calculate_test_disc(test_idx: int,
                        code_population: List[Dict],
                        matrix: List[List[int]]) -> float:
    """Binary entropy over pass/fail distribution – higher ⇒ more discriminative."""
    passed = sum(1 for c in code_population if matrix[int(c["idx"])][test_idx])
    total = len(code_population)
    p = 0.0 if total == 0 else passed / total
    if p in (0.0, 1.0):
        return 0.0
    return -(p * math.log2(p) + (1 - p) * math.log2(1 - p))

# ---------------------------------------------------------------------------
# Pareto utilities for multi‑objective test selection
# ---------------------------------------------------------------------------

def dominates(a: Dict, b: Dict, metrics: List[str]) -> bool:
    """Return ``True`` iff *a* dominates *b* on all metrics (≥) and > on ≥1."""
    better_or_equal = all(a[m] >= b[m] for m in metrics)
    strictly_better = any(a[m] > b[m] for m in metrics)
    return better_or_equal and strictly_better


def build_pareto_front(pop: List[Dict], metrics: List[str]) -> List[List[Dict]]:
    """Layered Pareto fronts (non‑dominated sorting)."""
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
    """Heuristic from the CoCoEvo paper for picking a Pareto‑optimal subset."""
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
                 crossover_rate: float = 0.6,
                 mutation_rate: float = 0.3,
                 vocab_repair_iters: int = 5,
                 rng_seed: Optional[int] = None):
        self.sm = suite_manager
        self.contract_text = contract_text
        self.max_generations = max_generations
        self.pop_cap_programs = pop_cap_programs
        self.pop_cap_tests = pop_cap_tests
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.vocab_repair_iters = vocab_repair_iters
        self.rng = random.Random(rng_seed)

        # Caches – re‑computed each generation
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
        """Run Stage‑1 repair on newly spawned individuals **only**."""
        if not new_prog_idxs and not new_test_idxs:
            return  # nothing to repair
        return run_vocab_alignment(self.sm, max_iters=self.vocab_repair_iters)

    # 1-b) Emergency reseed ---------------------------------------------
    def _reseed_populations(self):
        """Hard-reset both populations when vocab repair cannot recover fitness."""
        logger.warning("Reseeding ALL programs & tests - vocab repair exhausted with 0/N fitness.")

        # Drop existing individuals
        self.sm.solutions.clear()
        self.sm.test_cases.clear()

        # Fresh seed via existing spawning helpers – ensures Stage-1 alignment
        # for _ in range(self.pop_cap_programs):
        #     self._spawn_program()
        # for _ in range(self.pop_cap_tests):
        #     self._spawn_test()
        self.sm.generate_solutions(
            num_solutions=self.pop_cap_programs,
            contract_text=self.contract_text,
        )
        self.sm.test_cases = self.sm.generate_test_cases(
            num_cases=self.pop_cap_tests,
            contract_text=self.contract_text,
        )

        # One final vocab alignment pass for the brand-new population
        self._ensure_vocab_alignment()

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
        for idx, row in enumerate(self.logic_matrix):
            passed = sum(row)
            total = len(row) if row else 1
            logic_fitness = passed / total
            self.code_population.append({
                "idx": idx,
                "logic_fitness": logic_fitness,
            })

        # Test metrics
        self.test_population = []
        for j in range(len(self.sm.test_cases)):
            conf = calculate_test_conf(j, self.code_population, self.logic_matrix)
            disc = calculate_test_disc(j, self.code_population, self.logic_matrix)
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
        winner_idx = max(contenders, key=lambda x: x["logic_fitness"])["idx"]
        return self.sm.solutions[winner_idx]

    # 4) LLM‑driven genetic operators ------------------------------------
    def _crossover_programs(self, p1: CandidateSolution, p2: CandidateSolution) -> str:
        prompt = PROGRAM_CROSSOVER_PROMPT.format(
            parent_a=p1.original_program,
            parent_b=p2.original_program,
            contract_text=self.contract_text,
        )
        result = generate_content(prompt)
        if not result:
            logger.error("Crossover failed – empty result from LLM.")
        return result or ""

    def _mutate_program(self, prog: CandidateSolution) -> str:
        prompt = PROGRAM_MUTATION_PROMPT.format(
            program=prog.original_program,
            contract_text=self.contract_text,
        )
        result = generate_content(prompt)
        if not result:
            logger.error("Mutation failed – empty result from LLM.")
        return result or ""

    def _spawn_program(self) -> Tuple[Optional[int], Optional[CandidateSolution]]:
        """Create a child program; return ``(idx, sol)`` or ``(None, None)``."""
        if self.rng.random() < self.crossover_rate and len(self.sm.solutions) >= 2:
            pa, pb = self._tournament_select(), self._tournament_select()
            raw = self._crossover_programs(pa, pb)
        else:
            parent = self._tournament_select()
            raw = self._mutate_program(parent)
        if not raw.strip():
            logger.error("LLM returned empty program – spawn aborted.")
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
            logger.error("Test mutation failed – empty result from LLM.")
        return result or ""

    def _spawn_test(self) -> Tuple[Optional[int], Optional[TestCase]]:
        """Spawn a *predicate‑shape‑preserving* test case.

        The new strategy is:
        • **Prefer mutation** of an existing test (prob = `mutation_rate`).
        • If generating from scratch, pass *up to 5 exemplar tests* to the LLM and
          *explicitly* instruct it to keep *exactly the same* predicate signatures &
          arity.  This prevents the engine from introducing facts that the logic
          vocabulary cannot recognise.
        """
        use_mutation = self.sm.test_cases and (self.rng.random() < self.mutation_rate)

        if use_mutation:
            parent = self.rng.choice(self.sm.test_cases)
            raw = self._mutate_test(parent)
        else:
            exemplars = "\n".join(t.original_fact for t in self.sm.test_cases[:5]) if self.sm.test_cases else ""
            guidance = (
                """
                You are generating a *new* logical query (test case) to challenge the 
                current Prolog encoding of the insurance contract.  The test *must* 
                use **exactly the same predicate names and number of arguments** as 
                those shown below.  Think of a novel *scenario* or edge-case that the 
                contract might cover, but keep the *shape* identical.  
                Return a test in a similar format as the exemplars, matching the signature (arity and arguments).
                """ # This is an example of the format you should use, but make sure to use the predicate signatures provided in the exemplar tests later: \n % Args: Name, Age, Activity \n test("Scenario description", is_claim_covered("John", 67, "skydiving")).
            )
            prompt = (
                f"{TEST_GENERATION_PROMPT}\n\n{guidance}\n\n"  # base task description
                f"# Exemplar tests (keep shape)\n{exemplars}\n\n# → New test:"
            )
            raw = generate_content(prompt)
            if not raw:
                logger.error("Test generation failed – empty result from LLM.")
        if not raw or not raw.strip():
            return None, None

        tc = TestCase(raw.strip())
        self.sm.test_cases.append(tc)
        return len(self.sm.test_cases) - 1, tc

    # 5) Population culling ----------------------------------------------
    def _trim_populations(self):
        # ---- Programs ----
        self.code_population.sort(key=lambda x: x["logic_fitness"], reverse=True)
        survivors_prog_idxs = {d["idx"] for d in self.code_population[: self.pop_cap_programs]}
        self.sm.solutions = [s for i, s in enumerate(self.sm.solutions) if i in survivors_prog_idxs]

        # ---- Tests ----
        selected_tests = pareto_selection(
            self.test_population,
            self.pop_cap_tests,
            metrics=["conf", "disc"],
        )
        survivor_test_idxs = {d["idx"] for d in selected_tests}
        self.sm.test_cases = [t for j, t in enumerate(self.sm.test_cases) if j in survivor_test_idxs]

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self):
        """Execute co‑evolution for ``max_generations`` generations."""
        self._ensure_vocab_alignment()   # Defensive repair for initial pop

        for gen in range(1, self.max_generations + 1):
            print(f"\n═══════ CoCoEvo | Generation {gen}/{self.max_generations} ═══════")

            # Evaluate & compute metrics
            pre = f"evo_gen_{gen:04d}/pre"
            self._evaluate_logic(scope=pre)

            # ---------------- Spawn ----------------
            new_prog_idxs: List[int] = []
            new_test_idxs: List[int] = []
            for _ in range(max(1, self.pop_cap_programs // 10)):
                idx, _ = self._spawn_program()
                if idx is not None:
                    new_prog_idxs.append(idx)
            for _ in range(max(1, self.pop_cap_tests // 10)):
                idx, _ = self._spawn_test()
                if idx is not None:
                    new_test_idxs.append(idx)

            # Vocabulary repair for newcomers
            if new_prog_idxs or new_test_idxs:
                print(f"• Vocab repair for {len(new_prog_idxs)} programs / {len(new_test_idxs)} tests …")
                self._ensure_vocab_alignment(new_prog_idxs, new_test_idxs)

            # Re‑evaluate after repairs & cull
            post = f"evo_gen_{gen:04d}/post"
            self._evaluate_logic(scope=post)
            self._trim_populations()

        print("✅ CoCoEvo run completed.")
