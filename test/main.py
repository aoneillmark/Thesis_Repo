# main_coco_run.py
from suite_manager import SuiteManager
from evolve import run_vocab_alignment
from coevo_engine import CoCoEvoEngine
from prompts import PROLOG_GENERATION_PROMPT           # already in your repo

CONTRACT_PATH = "insurance_contract.txt"

if __name__ == "__main__":
    # ── 0. Load contract text ──────────────────────────────────────────
    with open(CONTRACT_PATH, encoding="utf-8") as fh:
        contract_text = fh.read()

    # ── 1. Seed an initial population ──────────────────────────────────
    sm = SuiteManager()
    sm.test_cases = sm.generate_test_cases(num_cases=6, contract_text=contract_text)

    sol_prompts = [
        (lambda ct, p=PROLOG_GENERATION_PROMPT: p.format(contract_text=ct))
        for _ in range(4)
    ]
    sm.generate_solutions(num_solutions=4,
                          contract_text=contract_text,
                          prompt_fns=sol_prompts)

    # ── 2. Stage-1: vocabulary alignment (re-uses evolve.py) ───────────
    run_vocab_alignment(sm, max_iters=10)

    # ── 3. Stage-2: logic-level co-evolution ───────────────────────────
    engine = CoCoEvoEngine(sm,
                           contract_text,
                           max_generations=30,     # tweak as desired
                           pop_cap_programs=30,
                           pop_cap_tests=30)
    engine.run()

    # (Optional) dump a summary
    sm.save_summary()
