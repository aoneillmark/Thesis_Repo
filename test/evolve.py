import copy
from test import EvolutionarySystem, generate_content
from prompts import PROLOG_GENERATION_PROMPT
import os
import json

# --- DIAGNOSIS PROMPT ---
from prompts import DIAGNOSIS_PROMPT

# --- FEEDBACK LOOP EXECUTION ---
def evolve_with_feedback(contract_text, num_generations=3, num_solutions=3, num_test_cases=10,
                         regenerate_tests_each_round=True, use_vocabulary=True):
    per_solution_advice = {}
    test_cases_to_reuse = None

    for gen in range(1, num_generations + 1):
        print(f"\n\n🧬🔁 === Generation {gen}/{num_generations} === 🔁🧬")

        system = EvolutionarySystem(use_vocabulary=use_vocabulary)

        # Only regenerate test cases if requested
        if regenerate_tests_each_round or not test_cases_to_reuse:
            test_cases = system.generate_test_cases(num_test_cases, contract_text)
            system.test_cases = test_cases
            if not regenerate_tests_each_round:
                test_cases_to_reuse = test_cases
        else:
            system.test_cases = test_cases_to_reuse



        # Build prompt functions for each solution (ID-free at first)
        prompt_fns = []
        for i in range(num_solutions):
            def make_prompt_fn(index=i):
                def prompt_fn(contract_text):
                    advice = per_solution_advice.get(f"sol_{index}", "")
                    if advice:
                        return (
                            "# ADDITIONAL FEEDBACK TO INCORPORATE:\n"
                            f"# {advice.strip()}\n\n"
                            + PROLOG_GENERATION_PROMPT.format(contract_text=contract_text)
                        )
                    else:
                        return PROLOG_GENERATION_PROMPT.format(contract_text=contract_text)
                return prompt_fn
            prompt_fns.append(make_prompt_fn())

        # Generate candidate solutions with associated prompts
        system.generate_solutions(num_solutions, contract_text, prompt_fns)

        # Evaluate them
        system.evaluate_fitness()

        # Diagnose and gather feedback
        new_advice = {}

        for idx, sol in enumerate(system.solutions):
            failed_tests = []
            failure_reasons = []

            for tc in system.test_cases:
                passed, reason = system._run_single_test(sol.canonical_program, tc.canonical_fact)
                if not passed:
                    failed_tests.append(tc)
                    failure_reasons.append((tc.canonical_fact, reason or "Unknown failure"))

            if failed_tests:
                failed_tests_str = "\n".join(
                    f"- `{fact}` → ❌ {reason}" for fact, reason in failure_reasons
                )
                print(f"\n❌ Solution {sol.id} failed {len(failed_tests)} test(s):")
                print(failed_tests_str)
                diagnosis_prompt = DIAGNOSIS_PROMPT.format(
                    prolog_code=sol.canonical_program or "",
                    failed_tests=failed_tests_str
                )
                feedback = generate_content(diagnosis_prompt)
                print(f"\n📋 Advice for {sol.id}:\n", feedback)
                new_advice[sol.id] = feedback


        if not new_advice:
            print("✅ All solutions passed all tests!")
            break

        per_solution_advice = new_advice

    system.save_summary()
    print("\n✅ Evolution complete.")




# --- RUN EVOLUTION ---
if __name__ == "__main__":
    try:
        with open("insurance_contract.txt", "r", encoding='utf-8') as file:
            contract_text = file.read()
    except FileNotFoundError:
        print("❌ Error: 'insurance_contract.txt' not found.")
        exit()

    # --- Ask the user about test case regeneration ---
    regenerate = input("🧪 Regenerate test cases each round? (y/n): ").strip().lower() == "y"
    use_vocab = input("📚 Use vocabulary canonicalization? (y/n): ").strip().lower() == "y"


    evolve_with_feedback(
        contract_text,
        num_generations=3,
        num_solutions=3,
        num_test_cases=10,
        regenerate_tests_each_round=regenerate,
        use_vocabulary=use_vocab
    )

