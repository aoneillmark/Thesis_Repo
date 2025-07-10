import os
import re
import uuid
from datetime import datetime
os.environ["SWI_HOME_DIR"] = r"C:\Program Files\swipl"
from janus_swi import janus

class PrologEvaluator:
    def __init__(self):
        self.log_dir = f"evaluation_logs/run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(self.log_dir, exist_ok=True)

    def run_single_test(self, prolog_program, test_fact, test_index=0):
        """Runs a single test case against a Prolog program."""
        if not prolog_program or not test_fact:
            print(f"❌ Skipping empty test case {test_index}")
            return False

        prog_file = f"temp_prog_{uuid.uuid4().hex[:8]}.pl"
        try:
            with open(prog_file, "w", encoding='utf-8') as f:
                f.write(prolog_program)

            # Load Prolog code
            try:
                janus.consult(prog_file)
            except Exception as e:
                print(f"❌ Prolog consult failed (test {test_index}): {e}")
                return False

            # Extract goal(s) from test(...) or treat as direct query
            goal = self.extract_goal_from_test_fact(test_fact)
            if not goal:
                print(f"❌ Could not parse test case {test_index}: {test_fact}")
                return False
            print(f"[DEBUG] Extracted goal: {goal}")


            # Run Prolog query
            try:
                result = janus.query_once(goal)
                if result is False:
                    print(f"❌ Test {test_index} failed – Goal returned false: {goal}")
                    return False
                else:
                    return True
            except Exception as e:
                print(f"⚠️ Test {test_index} crashed – Goal: {goal}\n   Error: {e}")
                return False

        finally:
            if os.path.exists(prog_file):
                os.remove(prog_file)

    def extract_goal_from_test_fact(self, test_fact):
        """Parses test("label", Goal). Returns goal as a string."""
        test_fact = test_fact.strip().rstrip(".")

        # Match: test("label", Goal) including multi-line goals
        match = re.match(r'test\((?:"[^"]*"|\'[^\']*\')\s*,\s*(.+)\)', test_fact, re.DOTALL)
        if match:
            return match.group(1).strip()

        # Fallback: treat entire thing as a bare goal
        return test_fact

    
    def extract_tests_from_file(self, test_file):
        """Parses full test(...) structures across multiple lines."""
        with open(test_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Use re.DOTALL to make . match newlines
        test_pattern = re.compile(r'test\(.*?\)\.', re.DOTALL | re.MULTILINE)
        tests = test_pattern.findall(content)
        return [t.strip() for t in tests]


    def evaluate_program(self, prolog_file, test_file):
        """Evaluates a Prolog program against a list of test cases."""
        with open(prolog_file, "r", encoding="utf-8") as f:
            program = f.read()

        with open(test_file, "r", encoding="utf-8") as f:
            test_cases = self.extract_tests_from_file(test_file)

        passed = []
        failed = []

        print(f"\n🧪 Evaluating {len(test_cases)} test(s)...\n")

        for i, test in enumerate(test_cases, start=1):
            print(f"🔹 Test {i}: {test}")
            if self.run_single_test(program, test, test_index=i):
                passed.append(test)
                print(f"✅ Passed")
            else:
                failed.append(test)
                print(f"❌ Failed")

        summary = f"""Evaluation Summary
=================
Total Tests: {len(test_cases)}
Passed: {len(passed)}
Failed: {len(failed)}
Success Rate: {(len(passed)/len(test_cases)) * 100:.2f}%

Failed Tests:
{chr(10).join(f"- {t}" for t in failed)}
"""

        summary_path = os.path.join(self.log_dir, "evaluation_summary.txt")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(summary)

        print(f"\n📝 Summary written to: {summary_path}")
        return len(passed) / len(test_cases)


if __name__ == "__main__":
    evaluator = PrologEvaluator()
    path = "./logs/run_20250709_163746"
    # path = "./logs/run_20250707_00000"
    if not os.path.exists(path):
        print(f"❌ Error: The specified path '{path}' does not exist.")
        exit(1)

    # Example usage
    prolog_file_name = "encoding.pl"  # Your Prolog program file
    test_file_name = "test_cases.pl"  # File containing test cases

    prolog_file = os.path.join(path, prolog_file_name)
    test_file = os.path.join(path, test_file_name)

    print(f"📂 Evaluating Prolog program: {prolog_file}")
    print(f"📂 Test cases file: {test_file}")

    # List out files in the path directory
    print("\n📂 Files in the directory:")
    for file in os.listdir(path):
        if file.endswith(".pl"):
            print(f" - {file}")


    
    if os.path.exists(prolog_file) and os.path.exists(test_file):
        fitness = evaluator.evaluate_program(prolog_file, test_file)
        print(f"\n🎯 Overall fitness score: {fitness:.2f}")
    else:
        print("❌ Error: Please ensure both encoding.pl and test_cases.pl exist in the current directory.")