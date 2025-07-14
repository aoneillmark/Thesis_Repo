# main.py

import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv
import uuid
from itertools import islice
import datetime

from evaluator import Evaluator
from prompts import PROLOG_GENERATION_PROMPT, TEST_SUITE_GENERATION_PROMPT

# --- Configuration ---
load_dotenv()
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
except KeyError:
    print("❌ Error: GEMINI_API_KEY environment variable not set.")
    exit()

model = genai.GenerativeModel('models/gemini-2.5-flash-lite-preview-06-17') # RPM: 15, TPM: 250,000, RPD: 1,000

# --- Helper Functions ---
def generate_content(prompt, is_json=False):
    """A helper function to call the generative AI model and handle potential errors."""
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if "```" in text:
            lang = "json" if is_json else "prolog"
            text = text.split(f"```{lang}\n")[1].split("\n```")[0]
        return text
    except Exception as e:
        print(f"❗️ LLM Generation Error: {e}")
        return None
    

# --- Core System Classes ---

class CandidateSolution:
    def __init__(self, contract_text, prompt=None):
        self.id = f"sol_{uuid.uuid4().hex[:8]}"
        print(f"\n🧬 Creating Solution {self.id}...")
        self.original_program = self._generate_program(contract_text, prompt)
        self.canonical_program = None
        self.logic_fitness = 0.0
        self.vocab_fitness = 0.0

    def _generate_program(self, contract_text, prompt=None):
        print("  - Generating Prolog program...")
        if prompt:
            generation_prompt = prompt
        else:
            generation_prompt = PROLOG_GENERATION_PROMPT.format(contract_text=contract_text)
        program = generate_content(generation_prompt)
        print("  ✅ Program generated." if program else "  ❌ Failed to generate program.")
        return program

class TestCase:
    """Represents a single, atomic test case."""
    def __init__(self, original_prolog_fact):
        self.id = f"tc_{uuid.uuid4().hex[:8]}"
        self.original_fact = original_prolog_fact.strip()
        self.canonical_fact = None
        self.logic_fitness = 0.0
        self.vocab_fitness = 0.0
        
        # Extract the query goal from the fact
        match = re.search(r"test\((?:'[^']+'|\"[^\"]+\"),\s*(.*?)\)\.", self.original_fact, re.DOTALL)
        self.query_goal = match.group(1) if match else None
        

# --- Main System Class ---
class EvolutionarySystem:
    def __init__(self, log_dir=None):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir = log_dir or f"logs/run_{timestamp}"
        os.makedirs(self.log_dir, exist_ok=True)

        self.solutions = []
        self.test_cases = []
        self.evaluator = Evaluator(self.log_dir)

    def evaluate_fitness(self):
        self.evaluator.evaluate(self.solutions, self.test_cases)
    
    def _run_single_test(self, canonical_program, canonical_test_fact):
        return self.evaluator._run_single_test(canonical_program, canonical_test_fact)

    def generate_test_cases(self, num_cases, contract_text):
        """Generates test cases from the contract text using the TEST_SUITE_GENERATION_PROMPT."""
        print(f"\n--- 🧪 Generating {num_cases} Test Cases ---")
        prompt = TEST_SUITE_GENERATION_PROMPT.format(contract_text=contract_text)
        raw_output = generate_content(prompt)
        if not raw_output:
            print("❌ Failed to generate test cases.")
            return []

        # Split using the '#####' marker
        raw_tests = [tc.strip() for tc in raw_output.split('#####') if tc.strip()]
        parsed_tests = [TestCase(tc) for tc in raw_tests[:num_cases]]
        print(f"✅ Generated {len(parsed_tests)} test cases.")
        return parsed_tests
    
    def generate_solutions(self, num_solutions, contract_text, prompt_fns=None):
        """Generates candidate solutions from the contract text using the given prompt functions."""
        print(f"\n--- 🧬 Generating {num_solutions} Candidate Solutions ---")

        for i in range(num_solutions):
            print(f"\n--- 🔁 Solution {i + 1}/{num_solutions} ---")
            if prompt_fns and prompt_fns[i] is None:
                print(f"⏭️ Skipping solution {i + 1} (vocab-valid and frozen)")
                continue
            prompt = prompt_fns[i](contract_text) if prompt_fns and i < len(prompt_fns) else None
            candidate = CandidateSolution(contract_text, prompt)
            self.solutions.append(candidate)


            
    def save_summary(self):
        """Prints a summary of the final population."""
        print("\n\n--- Final Results ---")
        sorted_solutions = sorted(self.solutions, key=lambda x: x.logic_fitness, reverse=True)
        
        print("\n--- Ranked Solutions ---")
        for i, sol in enumerate(sorted_solutions):
            print(f"\n--- Rank #{i+1} | Solution {sol.id} | logic_fitness: {sol.logic_fitness:.2f} --- vocab_fitness: {sol.vocab_fitness:.2f} ---")

        
        summary_path = os.path.join(self.log_dir, "summary.txt")
        with open(summary_path, "w", encoding="utf-8") as f:
            for i, sol in enumerate(sorted(self.solutions, key=lambda x: x.logic_fitness, reverse=True)):
                f.write(f"Rank #{i+1} | Solution {sol.id} | logic_fitness: {sol.logic_fitness:.2f} --- vocab_fitness: {sol.vocab_fitness:.2f}\n")

# --- Main Execution ---
if __name__ == "__main__":
    try:
        with open("insurance_contract.txt", "r", encoding='utf-8') as file:
            contract_text = file.read()
    except FileNotFoundError:
        print("❌ Error: 'insurance_contract.txt' not found. Please create it.")
        exit()

    NUM_SOLUTIONS = 3
    NUM_TEST_CASES = 10

    system = EvolutionarySystem()
    
    # 🧪 Generate test cases first
    system.test_cases = system.generate_test_cases(NUM_TEST_CASES, contract_text)
    
    # 🧬 Generate candidate solutions with default prompt
    prompt_fns = [
        (lambda: (lambda ct: PROLOG_GENERATION_PROMPT.format(contract_text=ct)))()
        for _ in range(NUM_SOLUTIONS)
    ]
    system.generate_solutions(NUM_SOLUTIONS, contract_text, prompt_fns)

    # 🧮 Evaluate
    system.evaluate_logic_fitness()

    system.print_results()
