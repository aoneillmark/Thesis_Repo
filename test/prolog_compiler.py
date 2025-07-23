# prolog_compiler.py

import os
import re
import uuid
import subprocess
import re, textwrap
import logging
logging.basicConfig(level=logging.DEBUG)

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
    keep_file = False 

    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(prolog_code.strip() + "\n\n")
            f.write(":- initialization(main).\n")
            f.write("main :-\n")
            f.write(f"    (catch(({goal.rstrip('.')} -> writeln('__PASS__'); writeln('__FAIL__')), "
                    "Error, (print_message(error, Error), writeln('__ERROR__')))),\n")
            f.write("    halt.\n")

        # print("Temp file looks like this:")
        # print(open(temp_file, "r", encoding="utf-8").read())
        

        # cmd = [
        #     "swipl", "--quiet",
        #     "--on-error=halt",      # <-- die on *any* error, no prompt :contentReference[oaicite:0]{index=0}
        #     "-g", "main", "-t", "halt",
        #     "-s", temp_file
        # ]

        cmd = ["swipl", "-q", "-f", temp_file]
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            encoding="utf-8"
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if '__PASS__' in stdout:
            return True, None
        if '__FAIL__' in stdout:
            return False, "Goal failed"
        if '__TIMEOUT__' in stdout: 
            return False, 'Timeout'
        if '__ERROR__' in stdout or "ERROR" in stderr.upper():
            return False, f"Prolog error:\n{stdout}\n{stderr}"
        # if 'Missing program or test fact' in stdout:
        #     return False, "Missing program or test fact"
        else:
            print(f"⚠️ Unexpected output:\n{stdout}\n{stderr}")
            return False, f"Unexpected output:\n{stdout}\n{stderr}"

    except subprocess.TimeoutExpired:
        print("Subprocess timed out.")
        keep_file = True
        return False, "Timeout"
    except Exception as e:
        return False, f"Execution error: {e}"
    finally:
        # if os.path.exists(temp_file) and not keep_file:
        if os.path.exists(temp_file) and not keep_file:
            os.remove(temp_file)


TEST_RE = re.compile(
    r'''test\(            # literal "test("
        (?:".*?"|'.*?')   # quoted name
        \s*,\s*
        (.*)              # GOAL (greedy)
    \)\s*\.?\s*$          # closing )   and optional "."
    ''', re.VERBOSE | re.DOTALL
)


def _drop_comments(src: str) -> str:
    """Remove full-line `% ...` and inline comments."""
    cleaned = []
    for line in src.splitlines():
        line = line.split('%', 1)[0]        # ditch inline comment part
        if line.strip():                    # keep only non-empty code
            cleaned.append(line)
    return "\n".join(cleaned)

def extract_goal(fact: str) -> str | None:
    """
    • Works whether the query is wrapped in `test(Name, Goal).`
      or already a bare goal.
    • Ignores leading/trailing comments & whitespace.
    """
    fact = textwrap.dedent(fact).strip()
    fact = _drop_comments(fact)

    m = TEST_RE.search(fact)
    if m:
        return m.group(1).strip().rstrip('.')

    # fallback = bare goal
    logging.debug(f"Falling back to raw goal extraction: {fact!r}")
    return fact.rstrip('.')