# test/tests/evaluator_test.py

import pytest
import shutil
from textwrap import dedent
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import prolog_compiler as pc
from evaluator import Evaluator
from logging_utils import LogManager
from suite_manager import CandidateSolution, TestCase
# Skip integration tests gracefully if SWI‑Prolog is not available in the environment
pytestmark = pytest.mark.skipif(shutil.which("swipl") is None, reason="SWI-Prolog executable not found; integration tests skipped")


# ─────────────────────────────────────────────────────────────
# Toy Prolog program
# ─────────────────────────────────────────────────────────────
TOY_POLICY = dedent("""
    is_claim_covered(Age, Date, male) :- 
                    Date < 19800101,
                    Age < 80.
""")

# ─────────────────────────────────────────────────────────────
# Realistic test cases (from test_cases.pl)
# ─────────────────────────────────────────────────────────────
RAW_TEST_CASES = [
    "test(\"covered_normal_hospitalization\", is_claim_covered(55, 100, 'Sickness')).",
    "test(\"excluded_age_over_80\", \\+is_claim_covered(81, 150, 'Accidental Injury')).",
    "test(\"excluded_military_service\", \\+is_claim_covered(30, 200, 'Accidental Injury_Military Service')).",
    "test(\"covered_wellness_visit_satisfied\", is_claim_covered(40, 180, 'Sickness')).",
    "test(\"excluded_wellness_visit_not_satisfied\", \\+is_claim_covered(50, 300, 'Sickness')).",
    "test(\"excluded_skydiving\", \\+is_claim_covered(25, 50, 'Accidental Injury_Skydiving')).",
]

@pytest.fixture
def dummy_log_manager(tmp_path):
    return LogManager(root=tmp_path)

def test_evaluator_full_matrix_with_realistic_cases(dummy_log_manager):
    evaluator = Evaluator(dummy_log_manager)

    # Create one CandidateSolution from toy policy
    sol = CandidateSolution(contract_text="dummy", program_text=TOY_POLICY)

    # Create TestCase objects from the realistic test strings
    test_cases = [TestCase(tc_str) for tc_str in RAW_TEST_CASES]

    # Run evaluation
    evaluator.evaluate([sol], test_cases, scope="test/full_eval")

    # Assertions
    assert len(evaluator.logic_matrix) == 1
    assert len(evaluator.logic_matrix[0]) == len(test_cases)

    assert isinstance(sol.logic_fitness, float)
    assert isinstance(sol.vocab_fitness, float)
    assert 0.0 <= sol.logic_fitness <= 1.0
    assert 0.0 <= sol.vocab_fitness <= 1.0

    for tc in test_cases:
        assert hasattr(tc, "logic_confidence")
        assert hasattr(tc, "logic_discrimination")


DUMMY_LOG_MANAGER = LogManager(root=".test_logs")

VALID_POLICY = dedent("""
    is_claim_covered(Age, Date, Reason) :-
        Age < 80,
        Date =< 180,
        sub_string(Reason, _, _, _, "Skydiving") -> fail ; true.
""")

BAD_POLICY = dedent("""
    is_claim_covered(Age, Date) :- Age < Date. % wrong arity
""")

TEST_FACTS = [
    ("logic_pass",     "test('ok', is_claim_covered(60, 100, 'Normal'))."),
    ("logic_error",    "test('fail_logic', \\+is_claim_covered(85, 100, 'Normal'))."),
    ("vocab_error",    "test('bad_pred', missing_predicate_call(1, 2, 3))."),
    ("other_error",    ""),  # empty test
    ("vocab_error",    "not even prolog"),
]


@pytest.mark.parametrize("expected, fact", TEST_FACTS)
def test_run_single_test_classification(expected, fact):
    ev = Evaluator(log_manager=DUMMY_LOG_MANAGER)
    result, reason = ev._run_single_test(VALID_POLICY, fact)
    assert result == expected, f"Expected {expected}, got {result} for: {fact}\nReason: {reason}"


def test_vocabulary_error_detection():
    reason = "ERROR: Undefined procedure: foo/2"
    assert Evaluator._is_vocab_error(reason)


def test_logic_error_detection():
    reason = "Goal failed"
    assert Evaluator._is_logic_error(reason)


def test_unknown_error_classified():
    ev = Evaluator(log_manager=DUMMY_LOG_MANAGER)
    result, reason = ev._run_single_test("", "")  # missing everything
    assert result == "other_error"


def test_evaluator_logic_and_vocab_matrix():
    class DummySolution:
        def __init__(self, id, program):
            self.id = id
            self.original_program = program
            self.canonical_program = None
            self.logic_fitness = 0.0
            self.vocab_fitness = 0.0

    class DummyTestCase:
        def __init__(self, id, fact):
            self.id = id
            self.original_fact = fact
            self.canonical_fact = None

    sol = DummySolution("s1", VALID_POLICY)
    test_cases = [DummyTestCase(f"t{i}", fact) for i, (_, fact) in enumerate(TEST_FACTS)]

    ev = Evaluator(log_manager=DUMMY_LOG_MANAGER)
    ev.evaluate([sol], test_cases, scope="test_eval_run")

    assert sol.logic_fitness > 0, "Expected at least one passing logic case"
    assert sol.vocab_fitness > 0, "Expected at least one passing vocab case"