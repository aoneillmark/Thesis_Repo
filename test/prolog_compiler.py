# prolog_compiler.py

import os
import re
import uuid
import subprocess

os.environ["SWI_HOME_DIR"] = r"C:\Program Files\swipl"


def consult(prolog_code: str, goal: str, timeout: int = 5):
    """
    Executes a Prolog query by writing the program to a temp file and invoking SWI-Prolog.

    Returns:
        (passed: bool, reason: str | None)
    """
    if not prolog_code or not goal:
        return False, "Missing code or goal"

    temp_file = f"temp_prog_{uuid.uuid4().hex[:8]}.pl"

    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(prolog_code.strip() + "\n\n")
            f.write(":- initialization(main).\n")
            f.write("main :-\n")
            f.write(f"    (catch(({goal} -> writeln('__PASS__'); writeln('__FAIL__')), "
                    "Error, (print_message(error, Error), writeln('__ERROR__')))),\n")
            f.write("    halt.\n")

        result = subprocess.run(
            ["swipl", "-q", "-f", temp_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            encoding="utf-8"
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if '__PASS__' in stdout:
            return True, None
        elif '__FAIL__' in stdout:
            return False, "Goal failed"
        elif '__ERROR__' in stdout or "ERROR" in stderr.upper():
            return False, f"Prolog error:\n{stdout}\n{stderr}"
        else:
            return False, f"Unexpected output:\n{stdout}\n{stderr}"

    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, f"Execution error: {e}"
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


def extract_goal(test_fact: str):
    """
    Extracts the goal from test("label", Goal). format.
    """
    test_fact = test_fact.strip().rstrip(".")
    match = re.match(r'test\((?:"[^"]*"|\'[^\']*\')\s*,\s*(.+)\)', test_fact, re.DOTALL)
    if match:
        return match.group(1).strip()
    return test_fact
