# evolve.py
import copy
from test import EvolutionarySystem, generate_content
from prompts import PROLOG_GENERATION_PROMPT
import os
import json
from feedback import diagnose_solution_failures

# --- DIAGNOSIS PROMPT ---
from prompts import DIAGNOSIS_PROMPT

# --- FEEDBACK LOOP EXECUTION ---
def run_evolutionary_refinement(solutions, test_cases):
    """
    Dummy implementation. Just prints the solutions and test cases.
    """

    print("\n--- 🏁 Evolutionary Refinement Results ---")
    print(f"Total Solutions: {len(solutions)}")
    print(f"Total Test Cases: {len(test_cases)}")

    for sol in solutions:
        print(f"\nSolution ID: {sol.id}", 
              f"Logic Fitness: {sol.logic_fitness:.2f}",
              f"Vocab Fitness: {sol.vocab_fitness:.2f}")


def make_prompt_fn(sol_index, previous_solution_ids, per_solution_advice, contract_text, gen):
    """Creates a prompt function for generating Prolog code based on previous solutions and advice."""
    def prompt_fn(contract_text):
        sol_id = previous_solution_ids[sol_index] if gen > 1 and previous_solution_ids[sol_index] is not None else None
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



def initialize_system(contract_text, num_test_cases, regenerate):
    system = EvolutionarySystem()
    test_cases = system.generate_test_cases(num_test_cases, contract_text)
    if not regenerate:
        return system, test_cases
    return system, None



def run_vocab_feedback_loop(system, contract_text, test_cases,
                             num_generations, num_solutions, max_feedback_iterations,
                             regenerate_tests_each_round,
                             SELECTION_THRESHOLD = 0.8):

    per_solution_advice = {}
    feedback_iteration_count = {}
    previous_solution_ids = []
    frozen_solutions = []
    frozen_indexes = set()  # Tracks indexes (0-based) of vocab-valid solutions


    for gen in range(1, num_generations + 1):
        print(f"\n\n🧬🔁 === Generation {gen}/{num_generations} === 🔁🧬")

        # Create per-generation sub-log folder
        gen_log_dir = os.path.join(system.log_dir, f"gen_{gen}")
        os.makedirs(gen_log_dir, exist_ok=True)
        system.evaluator.log_dir = gen_log_dir  # Ensure Evaluator logs to this folder

        if regenerate_tests_each_round or not test_cases:
            test_cases = system.generate_test_cases(len(test_cases) if test_cases else 10, contract_text)

        system.test_cases = test_cases

        prompt_fns = [
            None if i in frozen_indexes else make_prompt_fn(i, previous_solution_ids, per_solution_advice, contract_text, gen)
            for i in range(num_solutions)
        ]

        system.solutions = [] # So folders don't get clogged up
        system.generate_solutions(num_solutions, contract_text, prompt_fns)
        # previous_solution_ids = [sol.id for sol in system.solutions]
        previous_solution_ids = [
            sol.id if i not in frozen_indexes else None
            for i, sol in enumerate(system.solutions)
        ]


        system.evaluate_fitness()

        new_advice = {}
        for i, sol in enumerate(system.solutions):
            if sol.vocab_fitness < 1:
                feedback_iteration_count[sol.id] = feedback_iteration_count.get(sol.id, 0) + 1
                if feedback_iteration_count[sol.id] <= max_feedback_iterations:
                    feedback, failed_str = diagnose_solution_failures(sol, test_cases, system._run_single_test)
                    if feedback:
                        print(f"\n❌ Solution {sol.id} failed test(s):\n{failed_str}")
                        print(f"\n📋 Advice for {sol.id}:\n{feedback}")
                        new_advice[sol.id] = feedback
                    continue
            # Vocab fixed or maxed-out — freeze it
            # frozen_solutions.append(sol)
            frozen_indexes.add(i)  # Prevent it from regenerating next round

        if not new_advice:
            print("✅ All solutions are vocab-valid or maxed out.")
            break

        per_solution_advice = new_advice


    # Filter out completely broken ones
    valid_candidates = [sol for sol in system.solutions if sol.vocab_fitness > 0]

    # Sort by combined fitness
    ranked = sorted(valid_candidates, key=lambda s: s.vocab_fitness, reverse=True)

    # Retain top-k% of valid candidates
    retain_count = max(1, int(len(ranked) * SELECTION_THRESHOLD))
    retained = ranked[:retain_count]

    # Mark retained solutions as frozen
    frozen_solutions = retained    

    return frozen_solutions, test_cases


def evolve_with_feedback(contract_text, num_generations=3, num_solutions=3,
                         num_test_cases=10, regenerate_tests_each_round=True,
                         max_feedback_iterations=3,
                         SELECTION_THRESHOLD = 0.8):
    system, test_cases = initialize_system(contract_text, num_test_cases, regenerate_tests_each_round)
    frozen_solutions, _ = run_vocab_feedback_loop(system, contract_text, test_cases, num_generations,
                                                  num_solutions, max_feedback_iterations,
                                                  regenerate_tests_each_round, 
                                                  SELECTION_THRESHOLD)
    run_evolutionary_refinement(frozen_solutions, test_cases)


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


    evolve_with_feedback(
        contract_text,
        num_generations=3,
        num_solutions=3,
        num_test_cases=10,
        regenerate_tests_each_round=regenerate,
        SELECTION_THRESHOLD = 0.8
    )

