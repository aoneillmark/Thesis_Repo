#!/usr/bin/env python3
"""batch_run.py – iterate CoCoEvo across the full benchmark.

Usage
-----
$ python batch_run.py                 # 3‑generation evolutionary run per policy
$ python batch_run.py --oneshot       # zero‑shot (gen=0) baseline per policy
$ python batch_run.py -g 5            # custom generations
$ python batch_run.py -p 4            # simple parallelism (4 worker processes)

The script discovers every `*.txt` under `benchmark_policy/`, runs the
pipeline from `main_coco_run.py` on each contract, and stores logs under
`logs/<policy_stem>/` with a per‑run timestamp.
"""
from __future__ import annotations
import argparse
import concurrent.futures as cf
import datetime as dt
import pathlib
import sys
import traceback

# ── project modules ───────────────────────────────────────────────────────────
from suite_manager import SuiteManager
from evolve import run_vocab_alignment
from coevo_engine import CoCoEvoEngine
from prompts import PROLOG_GENERATION_PROMPT  # used when reseeding

# -----------------------------------------------------------------------------
# Helper – single policy worker
# -----------------------------------------------------------------------------

def _run_policy(policy_path: pathlib.Path, generations: int) -> None:
    """Run the evolutionary pipeline on one policy file.

    Parameters
    ----------
    policy_path : Path to the contract text file.
    generations : 0 → evaluate 0‑shot only, otherwise evolutionary steps.
    """
    policy_name = policy_path.stem  # e.g. "policy_042"
    time_tag = dt.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Log root for this run (ensures separation, per requirement #2)
    log_root = pathlib.Path("logs") / policy_name / time_tag

    # 0. Load contract
    contract_text = policy_path.read_text(encoding="utf-8")

    # 1. Seed SuiteManager (small populations for speed)
    sm = SuiteManager(log_root=str(log_root))
    sm.test_cases = sm.generate_test_cases(num_cases=6, contract_text=contract_text)

    # Candidate‑generation prompts (reuse trick with visible tests)
    secret = "\n\nAdditionally, here are the test cases you will be tested on; make sure to match the predicate signature and arity. {test_cases}"
    sol_prompts = [
        (lambda ct, p=PROLOG_GENERATION_PROMPT, sec=secret:
         p.format(contract_text=ct) + sec.format(
             test_cases="\n".join(tc.original_fact for tc in sm.test_cases)))
        for _ in range(4)
    ]
    sm.generate_solutions(num_solutions=4, contract_text=contract_text, prompt_fns=sol_prompts)

    # # 2. Vocab alignment for the initial population
    # run_vocab_alignment(sm, max_iters=5)

    # 3. Evolutionary stage (optional)
    if generations > 0:
        engine = CoCoEvoEngine(
            sm,
            contract_text,
            max_generations=generations,
            pop_cap_programs=10,
            pop_cap_tests=10,
        )
        engine.run()
    else:
        # Just evaluate once and store a summary
        sm.evaluate_fitness(scope="oneshot")

    # 4. Persist a summary
    sm.save_summary()
    print(f"✅ Completed {policy_name} (gens={generations}). Logs at {log_root}")

# -----------------------------------------------------------------------------
# CLI & orchestrator
# -----------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Batch‑run CoCoEvo on benchmark policies.")
    parser.add_argument("-g", "--generations", type=int, default=3,
                        help="Number of evolutionary generations to run (default 3). Use 0 for zero‑shot only.")
    parser.add_argument("--oneshot", action="store_true",
                        help="Shortcut for --generations 0 (mutually exclusive with -g).")
    parser.add_argument("-p", "--parallel", type=int, metavar="N", default=1,
                        help="Run N policies in parallel (simple process pool). Default=1 → sequential.")
    args = parser.parse_args(argv)

    generations = 0 if args.oneshot else args.generations
    if generations < 0:
        parser.error("Generations must be >= 0")

    # Discover policies
    policy_dir = pathlib.Path("benchmark_policy")
    policy_files = sorted(policy_dir.glob("*.txt"))
    if not policy_files:
        sys.exit("❌ No policies found under benchmark_policy/ .")

    print(f"🏃 Running {len(policy_files)} policies | generations={generations} | parallel={args.parallel}")

    # Simple parallel executor (requirement #4)
    if args.parallel > 1:
        with cf.ProcessPoolExecutor(max_workers=args.parallel) as pool:
            futures = [pool.submit(_run_policy, path, generations) for path in policy_files]
            for f in cf.as_completed(futures):
                try:
                    f.result()
                except Exception as e:
                    traceback.print_exc()
                    print(f"⚠️  Skipping policy due to error: {e}")
    else:
        for path in policy_files:
            try:
                _run_policy(path, generations)
            except Exception as e:
                traceback.print_exc()
                print(f"⚠️  Skipping policy due to error: {e}")

    print("🎉 All policies processed.")

# -----------------------------------------------------------------------------

if __name__ == "__main__":
    main()
