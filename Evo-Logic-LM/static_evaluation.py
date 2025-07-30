import os
import re
import uuid
import subprocess
from datetime import datetime
os.environ["SWI_HOME_DIR"] = r"C:\Program Files\swipl"


class PrologEvaluator:
    def __init__(self):
        self.log_dir = f"evaluation_logs/run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(self.log_dir, exist_ok=True)

    def run_single_test(self, prolog_program, test_fact, test_index=0):
        """Runs a single test case against a Prolog program using SWI-Prolog subprocess."""
        if not prolog_program or not test_fact:
            print(f"❌ Skipping empty test case {test_index}")
            return False

        temp_file_path = f"temp_prog_{uuid.uuid4().hex[:8]}.pl"
        goal = self.extract_goal_from_test_fact(test_fact)
        if not goal:
            print(f"❌ Could not parse test case {test_index}: {test_fact}")
            return False

        try:
            with open(temp_file_path, "w", encoding="utf-8") as f:
                f.write(prolog_program.strip() + "\n\n")
                f.write(":- initialization(main).\n")
                f.write("main :-\n")
                f.write(f"    (catch(({goal} -> writeln('__PASS__'); writeln('__FAIL__')), Error, (print_message(error, Error), writeln('__ERROR__')))),\n")
                f.write("    halt.\n")

            result = subprocess.run(
                ["swipl", "-q", "-f", temp_file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,
                encoding="utf-8"
            )

            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            if '__PASS__' in stdout:
                return True
            elif '__FAIL__' in stdout:
                return False
            elif '__ERROR__' in stdout or "ERROR" in stderr.upper():
                print(f"🛑 Prolog error on Test {test_index}:\n{stdout}\n{stderr}")
                return False
            else:
                print(f"⚠️ Unexpected output (Test {test_index}):\n{stdout}\n{stderr}")
                return False

        except subprocess.TimeoutExpired:
            print(f"⏰ Test {test_index} timed out.")
            return False
        except Exception as e:
            print(f"💥 Error running test {test_index}: {e}")
            return False
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)


    def extract_goal_from_test_fact(self, test_fact):
        """Parses test("label", Goal). Returns goal as a string."""
        test_fact = test_fact.strip().rstrip(".")

        match = re.match(r'test\((?:"[^"]*"|\'[^\']*\')\s*,\s*(.+)\)', test_fact, re.DOTALL)
        if match:
            return match.group(1).strip()
        return test_fact  # Fallback: treat as plain goal

    def extract_tests_from_file(self, test_file):
        """Parses full test(...) structures across multiple lines."""
        with open(test_file, "r", encoding="utf-8") as f:
            content = f.read()

        test_pattern = re.compile(r'test\(.*?\)\.', re.DOTALL | re.MULTILINE)
        return [t.strip() for t in test_pattern.findall(content)]

    def evaluate_program(self, prolog_file, test_file):
        """Evaluates a Prolog program against a list of test cases."""
        with open(prolog_file, "r", encoding="utf-8") as f:
            program = f.read()

        test_cases = self.extract_tests_from_file(test_file)

        passed = []
        failed = []

        print(f"\n🧪 Evaluating {len(test_cases)} test(s)...\n")

        for i, test in enumerate(test_cases, start=1):
            print(f"🔹 Test {i}: {test}")
            if self.run_single_test(program, test, test_index=i):
                passed.append(test)
                print("✅ Passed")
            else:
                failed.append(test)
                print("❌ Failed")

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


# --- Runner ---
if __name__ == "__main__":
    evaluator = PrologEvaluator()
    path = "./logs/run_20250710_174617"  # Update this path as needed

    if not os.path.exists(path):
        print(f"❌ Error: The specified path '{path}' does not exist.")
        exit(1)

    prolog_file = os.path.join(path, "encoding.pl")
    test_file = os.path.join(path, "test_cases.pl")

    print(f"📂 Evaluating Prolog program: {prolog_file}")
    print(f"📂 Test cases file: {test_file}")

    print("\n📂 Files in the directory:")
    for file in os.listdir(path):
        if file.endswith(".pl"):
            print(f" - {file}")

    if os.path.exists(prolog_file) and os.path.exists(test_file):
        fitness = evaluator.evaluate_program(prolog_file, test_file)
        print(f"\n🎯 Overall fitness score: {fitness:.2f}")
    else:
        print("❌ Error: encoding.pl and/or test_cases.pl not found.")
