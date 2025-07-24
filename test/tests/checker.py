import pytest
import shutil
from textwrap import dedent
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
# import prolog_compiler as pc
# from evaluator import Evaluator
# from logging_utils import LogManager
import re
# Skip integration tests gracefully if SWI‑Prolog is not available in the environment
pytestmark = pytest.mark.skipif(shutil.which("swipl") is None, reason="SWI‑Prolog executable not found; integration tests skipped")
from prolog_compiler import consult, extract_goal

# ────────────────────────────────────────────────────────────────────────────────
# Batch‑runner for an *encoding.pl* (policy) and *test_cases.pl* (facts) file
# ────────────────────────────────────────────────────────────────────────────────
import sys
from pathlib import Path
from typing import List, Tuple

GREEN = "\033[92m"
RED   = "\033[91m"
CYAN  = "\033[96m"
RESET = "\033[0m"

def _read_file(path: str | Path) -> str:
    try:
        return Path(path).read_text(encoding="utf‑8")
    except FileNotFoundError:
        sys.exit(f"❌  File not found: {path}")

def _discover_tests(test_src: str) -> List[Tuple[str, str]]:
    """
    Returns a list of (nice_name, raw_goal) pairs extracted from `test(...)` facts.
    Falls back to bare goals if no wrapper is present.
    """
    tests = []
    for raw in filter(None, (ln.strip() for ln in test_src.splitlines())):
        # Ignore comment‑only lines
        if raw.lstrip().startswith("%"):
            continue

        goal = extract_goal(raw)
        if not goal:
            continue

        # Friendly name = stuff inside the first quoted string if present, else the goal itself
        m = re.match(r"""test\(\s*(['"])(.*?)\1""", raw)
        name = m.group(2) if m else goal
        tests.append((name, goal))
    return tests

# ─────────────────────── helpers copied verbatim from Evaluator ──────────────────
def _is_vocab_error(reason: str | None) -> bool:
    if not reason:
        return False
    return any(substr in reason for substr in (
        "Unknown procedure", "Undefined procedure",
        "Syntax error", "ERROR:"
    ))

def _is_logic_error(reason: str | None) -> bool:
    return reason == "Goal failed"


# ─────────────────────────── enhanced batch runner ──────────────────────────────
def run_suite(encoding_path: str | Path, tests_path: str | Path) -> None:
    policy_code = _read_file(encoding_path)
    test_file   = _read_file(tests_path)

    goals = _discover_tests(test_file)
    if not goals:
        sys.exit("⚠️  No test facts found in the supplied test‑case file.")

    print(f"{CYAN}▶ Running {len(goals)} test(s)…{RESET}")
    passed = 0

    for name, goal in goals:
        ok, reason = consult(policy_code, goal)

        # ── classify outcome (mirrors Evaluator._run_single_test) ──
        if ok:
            tag = "logic_pass"
            colour = GREEN
            passed += 1
        else:
            if _is_vocab_error(reason):
                tag = "vocab_error"
            elif _is_logic_error(reason):
                tag = "logic_error"
            else:
                tag = "other_error"
            colour = RED

        # ── pretty‑print result ───────────────────────────────────
        print(f"  {colour}{'✔' if ok else '✘'} {name}{RESET}  –  {tag}"
              + (f": {reason}" if reason and not ok else ""))

    print(f"\n{CYAN}Summary: {passed}/{len(goals)} passed.{RESET}")
    if passed != len(goals):
        sys.exit(1)   # non‑zero exit code for CI


# ────────────────────────────────────────────────────────────────────────────────
# CLI entry‑point
# ────────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__" and len(sys.argv) >= 3:
    enc_file  = sys.argv[1]
    tests_file = sys.argv[2]
    run_suite(enc_file, tests_file)
