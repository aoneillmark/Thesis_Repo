# main.py

import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv
os.environ["SWI_HOME_DIR"] = r"C:\Program Files\swipl"
from janus_swi import janus
import uuid
from itertools import islice
import datetime

# Assuming prompts.py is in the same directory and is up-to-date
from prompts import GLOBAL_MAPPING_PROMPT, PROLOG_GENERATION_PROMPT, TEST_SUITE_GENERATION_PROMPT

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

def get_predicate_signature(query_or_head):
    """Extracts 'name/arity' from a Prolog query or rule head string."""
    try:
        clean_str = query_or_head.strip().replace('\\+', '').strip() # Handle negation
        name = clean_str.split('(')[0].strip()
        if '(' not in clean_str: return f"{name}/0"
        
        content = clean_str[clean_str.find('(')+1:clean_str.rfind(')')]
        if not content.strip(): arity = 0
        else: arity = content.count(',') + 1
        return f"{name}/{arity}"
    except Exception:
        return None

# --- Core System Classes ---

class CandidateSolution:
    """Represents a single candidate solution (a Prolog program)."""
    def __init__(self, contract_text):
        self.id = f"sol_{uuid.uuid4().hex[:8]}"
        print(f"\n🧬 Creating Solution {self.id}...")
        self.original_program = self._generate_program(contract_text)
        self.canonical_program = None
        self.fitness = 0.0

    def _generate_program(self, contract_text):
        print("  - Generating Prolog program...")
        prompt = PROLOG_GENERATION_PROMPT.format(contract_text=contract_text)
        program = generate_content(prompt)
        print("  ✅ Program generated." if program else "  ❌ Failed to generate program.")
        return program

class TestCase:
    """Represents a single, atomic test case."""
    def __init__(self, original_prolog_fact):
        self.id = f"tc_{uuid.uuid4().hex[:8]}"
        self.original_fact = original_prolog_fact.strip()
        self.canonical_fact = None
        
        # Extract the query goal from the fact
        match = re.search(r"test\((?:'[^']+'|\"[^\"]+\"),\s*(.*?)\)\.", self.original_fact, re.DOTALL)
        self.query_goal = match.group(1) if match else None


# --- Vocabulary Management Class ---
class VocabularyManager:
    """Handles the creation of the global canonical vocabulary."""
    
    def extract_from_solutions(self, solutions):
        """Extracts predicates and their comments (or empty) from candidate solutions."""
        predicates = {}
        # Match rules with or without comments
        head_pattern = re.compile(r"([a-zA-Z_][a-zA-Z0-9_]*\s*\(.*?\))\s*:-", re.DOTALL)
        comment_pattern = re.compile(r"%\s*(.*?)\n\s*([a-zA-Z_][a-zA-Z0-9_]*\s*\(.*?\))")

        for sol in solutions:
            if not sol.original_program:
                continue

            # Add from commented rules
            for comment, head in comment_pattern.findall(sol.original_program):
                sig = get_predicate_signature(head)
                if sig and sig not in predicates:
                    predicates[sig] = comment.strip()

            # Add from non-commented rules
            for head in head_pattern.findall(sol.original_program):
                sig = get_predicate_signature(head)
                if sig and sig not in predicates:
                    predicates[sig] = "No comment (auto-extracted)"
        
        return predicates

    
    def extract_from_test_cases(self, test_cases):
        """Extracts predicates from individual test cases."""
        predicates = {}
        for tc in test_cases:
            if tc.query_goal:
                signature = get_predicate_signature(tc.query_goal)
                if signature and signature not in predicates:
                    predicates[signature] = "From test case" # Placeholder comment
        return predicates

    def build_global_map(self, all_predicates, batch_size=15):
        """Builds the canonical map iteratively."""
        print("   - 🗺️  Building Global Canonical Map...")
        canonical_map = {}
        predicate_items = list(all_predicates.items())
        for i in range(0, len(predicate_items), batch_size):
            batch = dict(islice(predicate_items, i, i + batch_size))
            print(f"     - Processing batch {i//batch_size + 1}...")
            prompt = GLOBAL_MAPPING_PROMPT.format(
                prior_map_json=json.dumps(canonical_map, indent=2),
                predicates_json=json.dumps(batch, indent=2)
            )
            map_json_str = generate_content(prompt, is_json=True)
            if map_json_str:
                try: canonical_map.update(json.loads(map_json_str))
                except json.JSONDecodeError: print(f"     - ❌ Failed to parse map from batch.")
            else: print(f"     - ❌ Failed to generate map from batch.")
        print("   - ✅ Global map complete.")
        return canonical_map

    def translate(self, original_text, global_map):
        """Generic translation function for any piece of Prolog code."""
        if not original_text: return None
        translated_text = original_text
        for original_sig, canonical_sig in global_map.items():
            original_name = original_sig.split('/')[0]
            canonical_name = canonical_sig.split('/')[0]
            if original_name != canonical_name:
                translated_text = re.sub(r'\b' + re.escape(original_name) + r'\(', canonical_name + '(', translated_text)
        return translated_text

# --- Main System Class ---
class EvolutionarySystem:
    """Orchestrates the evolutionary process."""
    def __init__(self, num_solutions, num_test_cases, contract_text):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir = f"logs/run_{timestamp}"
        os.makedirs(self.log_dir, exist_ok=True)

        self.solutions = [CandidateSolution(contract_text) for _ in range(num_solutions)]
        self.test_cases = self._generate_test_cases(num_test_cases, contract_text)
        self.vocab_manager = VocabularyManager()

    # def _generate_test_cases(self, num_to_generate, contract_text):
    #     """Generates a pool of individual TestCase objects."""
    #     print(f"\n🧪 Generating a pool of {num_to_generate} test cases...")
    #     all_test_cases = []
    #     # For efficiency, we generate suites and parse them into individual cases.
    #     # This reduces the number of LLM calls.
    #     while len(all_test_cases) < num_to_generate:
    #         print(f"  - Requesting a new suite from LLM to parse... ({len(all_test_cases)}/{num_to_generate})")
    #         prompt = TEST_SUITE_GENERATION_PROMPT.format(contract_text=contract_text)
    #         suite_text = generate_content(prompt)
    #         if suite_text:
    #             # Find all 'test(...).' facts in the generated text
    #             newly_parsed = [TestCase(fact) for fact in re.findall(r"test\(.*?\)\.", suite_text, re.DOTALL)]
    #             all_test_cases.extend(newly_parsed)
    #             print(f"  - ✅ Parsed {len(newly_parsed)} new test cases.")
        
    #     return all_test_cases[:num_to_generate]

    def _generate_test_cases(self, num_to_generate, contract_text):
        print(f"\n🧪 Generating a pool of {num_to_generate} test cases...")
        all_test_cases = []
        while len(all_test_cases) < num_to_generate:
            print(f"  - Requesting a new suite from LLM to parse... ({len(all_test_cases)}/{num_to_generate})")
            prompt = TEST_SUITE_GENERATION_PROMPT.format(contract_text=contract_text)
            suite_text = generate_content(prompt)

            if suite_text:
                # Safer extraction: break on individual 'test(...)' facts
                raw_tests = re.findall(r"(test\((?:.|\n)*?\)\.)", suite_text)
                for raw in raw_tests:
                    try:
                        # Basic structural validation
                        if raw.count('test(') != 1:
                            continue
                        if '"' not in raw and "'" not in raw:
                            continue
                        if raw.count(',') < 1:
                            continue
                        if '"' in raw.split(",")[0] or "'" in raw.split(",")[0]:
                            test_case = TestCase(raw.strip())
                            if test_case.query_goal and not test_case.query_goal.startswith('"') and not test_case.query_goal.endswith('"'):
                                all_test_cases.append(test_case)
                    except Exception as e:
                        print(f"⚠️ Skipping malformed test: {e}")
                        continue
                print(f"  - ✅ Parsed {len(all_test_cases)} total test cases so far.")

        return all_test_cases[:num_to_generate]


    def _run_single_test(self, canonical_program, canonical_test_fact):
        """Runs a single canonical test case against a canonical solution."""
        if not canonical_program or not canonical_test_fact:
            return False

        # Write and consult program
        prog_file = f"temp_prog_{uuid.uuid4().hex[:8]}.pl"
        with open(prog_file, "w", encoding='utf-8') as f:
            f.write(canonical_program)
        try:
            janus.consult(prog_file)
        except Exception as e:
            print(f"❌ Prolog consult failed: {e}")
            return False
        finally:
            os.remove(prog_file)

        # Extract goal from test("label", Goal).
        match = re.search(r"test\((?:'[^']+'|\"[^\"]+\"),\s*(.*?)\)\.", canonical_test_fact, re.DOTALL)
        if not match:
            print("⚠️ Test fact malformed:", canonical_test_fact)
            return False

        goal = match.group(1)

        try:
            result = janus.query_once(goal)
            return result is not False
        except Exception as e:
            # Penalize goal failures (including arity mismatch, undefined predicate, etc.)
            print(f"⚠️ Query failed for goal: {goal}\n   Reason: {e}")
            return False



    def evaluate_fitness(self):
        """Calculates fitness using the Global Canonical Mapping approach."""
        print("\n--- 🏆 Starting Fitness Evaluation ---")
        
        # 1. Extract predicates from both populations
        sol_preds = self.vocab_manager.extract_from_solutions(self.solutions)
        tc_preds = self.vocab_manager.extract_from_test_cases(self.test_cases)
        all_predicates = {**tc_preds, **sol_preds}
        print(f"   - 💡 Found {len(all_predicates)} unique predicates in total.")

        # 2. Build the global map
        global_map = self.vocab_manager.build_global_map(all_predicates)
        print(f"\nFinal Global Map:\n{json.dumps(global_map, indent=2)}")

        # 3. Translate all solutions and test cases
        print("\n   - ✍️  Translating all assets to canonical vocabulary...")
        for sol in self.solutions:
            sol.canonical_program = self.vocab_manager.translate(sol.original_program, global_map)
        for tc in self.test_cases:
            tc.canonical_fact = self.vocab_manager.translate(tc.original_fact, global_map)
        print("   - ✅ All assets translated.")

        # 4. Save all canonical programs and test cases to files
        print("\n   - 💾 Saving canonical programs and test cases to files...")
        for sol in self.solutions:
            fname = os.path.join(self.log_dir, f"solution_{sol.id}.pl")
            with open(fname, "w", encoding="utf-8") as f:
                f.write(sol.canonical_program or "❌ No canonical program available.")
        test_log_path = os.path.join(self.log_dir, "test_cases.pl")
        with open(test_log_path, "w", encoding="utf-8") as f:
            for tc in self.test_cases:
                f.write((tc.canonical_fact or "❌ Invalid test case") + "\n")


        # 4. Evaluate fitness
        print("\n   - 🚀 Evaluating solution fitness against individual test cases...")
        for sol in self.solutions:
            passed_count = 0
            for tc in self.test_cases:
                if self._run_single_test(sol.canonical_program, tc.canonical_fact):
                    passed_count += 1
            
            sol.fitness = passed_count / len(self.test_cases) if self.test_cases else 0
            print(f"     - Solution {sol.id} Fitness: {sol.fitness:.2f} ({passed_count}/{len(self.test_cases)} tests passed)")
            
    def print_results(self):
        """Prints a summary of the final population."""
        # print("\n\n--- Final Results ---")
        # sorted_solutions = sorted(self.solutions, key=lambda x: x.fitness, reverse=True)
        
        # print("\n--- Ranked Solutions ---")
        # for i, sol in enumerate(sorted_solutions):
        #     print(f"\n--- Rank #{i+1} | Solution {sol.id} | Fitness: {sol.fitness:.2f} ---")
        #     print("--- Canonical Program ---")
        #     print(sol.canonical_program)
        
        # print("\n\n--- 🧪 Pool of Individual Test Cases ---")
        # for i, tc in enumerate(self.test_cases):
        #      print(f"TC #{i+1} | {tc.id} | Canonical Fact: {tc.canonical_fact}")
        
        summary_path = os.path.join(self.log_dir, "summary.txt")
        with open(summary_path, "w", encoding="utf-8") as f:
            for i, sol in enumerate(sorted(self.solutions, key=lambda x: x.fitness, reverse=True)):
                f.write(f"Rank #{i+1} | Solution {sol.id} | Fitness: {sol.fitness:.2f}\n")

# --- Main Execution ---
if __name__ == "__main__":
    try:
        with open("insurance_contract.txt", "r", encoding='utf-8') as file:
            contract_text = file.read()
    except FileNotFoundError:
        print("❌ Error: 'insurance_contract.txt' not found. Please create it.")
        exit()

    NUM_SOLUTIONS = 3      # Number of candidate programs to generate
    NUM_TEST_CASES = 10    # Total number of individual test cases to generate
    
    system = EvolutionarySystem(NUM_SOLUTIONS, NUM_TEST_CASES, contract_text)
    system.evaluate_fitness()
    system.print_results()