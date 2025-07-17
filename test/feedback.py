from prompts import DIAGNOSIS_PROMPT
from utils import generate_content

def diagnose_solution_failures(solution, test_cases, run_test_fn):
    """
    Runs tests on a solution, collects vocab and logic failures,
    and generates feedback using the LLM if there are any failures.
    
    Returns:
        feedback_text: textual diagnosis from the LLM
        failed_tests_str: formatted list of test cases and reasons
    """
    failed = []
    failure_reasons = []

    for tc in test_cases:
        result, reason = run_test_fn(solution.canonical_program, tc.canonical_fact)

        if result in {"logic_fail", "vocab_error", "invalid_input"}:
            failed.append(tc)
            label = "🧠 Vocab Error" if result == "vocab_error" else (
                    "❌ Logic Fail" if result == "logic_fail" else "⚠️ Invalid Input")
            failure_reasons.append((tc.canonical_fact, f"{label}: {reason}"))

    if not failed:
        return None, None

    failed_tests_str = "\n".join(
        f"- `{fact}` → {reason}" for fact, reason in failure_reasons
    )

    diagnosis_prompt = DIAGNOSIS_PROMPT.format(
        prolog_code=solution.canonical_program or "",
        failed_tests=failed_tests_str
    )

    feedback = generate_content(diagnosis_prompt)
    return feedback, failed_tests_str

def diagnose_test_failures(test_cases, run_test_fn):
    """
    Runs tests on individual test cases, identifies failures,
    and generates LLM-based feedback if any are detected.

    Returns:
        feedback_text: textual diagnosis from the LLM
        failed_tests_str: formatted list of test cases and reasons
    """
    failed = []
    failure_reasons = []

    for tc in test_cases:
        result, reason = run_test_fn(tc)

        if result in {"logic_fail", "vocab_error", "invalid_input"}:
            failed.append(tc)
            label = "🧠 Vocab Error" if result == "vocab_error" else (
                    "❌ Logic Fail" if result == "logic_fail" else "⚠️ Invalid Input")
            failure_reasons.append((tc, f"{label}: {reason}"))

    if not failed:
        return None, None

    failed_tests_str = "\n".join(
        f"- `{tc}` → {reason}" for tc, reason in failure_reasons
    )

    diagnosis_prompt = DIAGNOSIS_PROMPT.format(
        prolog_code="",  # No specific program associated
        failed_tests=failed_tests_str
    )

    feedback = generate_content(diagnosis_prompt)
    return feedback, failed_tests_str