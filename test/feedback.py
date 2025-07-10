# feedback.py

from prompts import DIAGNOSIS_PROMPT
from test import generate_content

def diagnose_solution_failures(solution, test_cases, run_test_fn):
    """
    Runs tests on a solution, collects reasons for failures, and generates LLM diagnosis.
    
    Returns:
        feedback_text: the textual diagnosis from the LLM
        failed_tests_str: formatted list of test cases and reasons
    """
    failed = []
    failure_reasons = []

    for tc in test_cases:
        passed, reason = run_test_fn(solution.canonical_program, tc.canonical_fact)
        if not passed:
            failed.append(tc)
            failure_reasons.append((tc.canonical_fact, reason or "Unknown failure"))

    if not failed:
        return None, None

    failed_tests_str = "\n".join(
        f"- `{fact}` → ❌ {reason}" for fact, reason in failure_reasons
    )

    diagnosis_prompt = DIAGNOSIS_PROMPT.format(
        prolog_code=solution.canonical_program or "",
        failed_tests=failed_tests_str
    )

    feedback = generate_content(diagnosis_prompt)
    return feedback, failed_tests_str
