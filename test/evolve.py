import copy
from test import EvolutionarySystem, generate_content
from prompts import PROLOG_GENERATION_PROMPT
import os
import json
from feedback import diagnose_solution_failures

# --- DIAGNOSIS PROMPT ---
from prompts import DIAGNOSIS_PROMPT

# --- FEEDBACK LOOP EXECUTION ---
def evolve_with_feedback(contract_text, num_generations=3, num_solutions=3, num_test_cases=10,
                         regenerate_tests_each_round=True, use_vocabulary=True):
    per_solution_advice = {}
    test_cases_to_reuse = None
    previous_solution_ids = []

    for gen in range(1, num_generations + 1):
        print(f"\n\n🧬🔁 === Generation {gen}/{num_generations} === 🔁🧬")

        system = EvolutionarySystem(use_vocabulary=use_vocabulary)

        # Generate or reuse test cases
        if regenerate_tests_each_round or not test_cases_to_reuse:
            test_cases = system.generate_test_cases(num_test_cases, contract_text)
            system.test_cases = test_cases
            if not regenerate_tests_each_round:
                test_cases_to_reuse = test_cases
        else:
            system.test_cases = test_cases_to_reuse

        # Define prompt functions with correct advice by solution index
        def make_prompt_fn(sol_index):
            def prompt_fn(contract_text):
                sol_id = previous_solution_ids[sol_index] if gen > 1 else None
                advice = per_solution_advice.get(sol_id, "")
                if advice:
                    print(f"\n# ADDITIONAL FEEDBACK FOR {sol_id or '??'}:\n{advice.strip()}")
                    return (
                        "# ADDITIONAL FEEDBACK TO INCORPORATE:\n"
                        f"# {advice.strip()}\n\n"
                        + PROLOG_GENERATION_PROMPT.format(contract_text=contract_text)
                    )
                else:
                    print(f"⚠️ No additional feedback for solution {sol_index} (ID: {sol_id or 'N/A'})")
                    return PROLOG_GENERATION_PROMPT.format(contract_text=contract_text)
            return prompt_fn

        prompt_fns = [make_prompt_fn(i) for i in range(num_solutions)]

        # Generate solutions with appropriate prompts
        system.generate_solutions(num_solutions, contract_text, prompt_fns=prompt_fns)

        # Save current solution IDs to track them across generations
        previous_solution_ids = [sol.id for sol in system.solutions]

        # Evaluate fitness
        system.evaluate_fitness()

        # Diagnose and gather new feedback
        new_advice = {}
        for sol in system.solutions:
            feedback, failed_str = diagnose_solution_failures(sol, system.test_cases, system._run_single_test)
            if feedback:
                print(f"\n❌ Solution {sol.id} failed test(s):")
                print(failed_str)
                print(f"\n📋 Advice for {sol.id}:\n{feedback}")
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

