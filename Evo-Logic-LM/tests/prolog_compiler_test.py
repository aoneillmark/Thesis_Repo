# prolog_compiler_test.py

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
# Skip integration tests gracefully if SWI‑Prolog is not available in the environment
pytestmark = pytest.mark.skipif(shutil.which("swipl") is None, reason="SWI‑Prolog executable not found; integration tests skipped")

# -----------------------------------------------------------------------------
# Toy Prolog policy for coverage checks
# -----------------------------------------------------------------------------
TOY_POLICY = dedent("""
    % ---- Toy insurance policy rules ----
    % Covers any male born before 1 Jan 1980.
    % Name parameter is currently ignored.
    is_claim_covered(_Name, Date, male) :- Date < 19800101.

    % All other cases are not covered.  (Closed-world assumption)
    % A query that fails simply returns false in Prolog, handling the negative case.
""")

# -----------------------------------------------------------------------------
# consult() helper tests
# -----------------------------------------------------------------------------

def test_consult_success():
    """A valid goal that should succeed returns (True, None)."""
    passed, reason = pc.consult(
        TOY_POLICY,
        "is_claim_covered('Johnny Appleseed', 19730101, male)."
    )
    assert passed is True
    assert reason is None


def test_consult_failure():
    """A goal expected to fail should return (False, "Goal failed")."""
    passed, reason = pc.consult(
        TOY_POLICY,
        "is_claim_covered('Jane Appleseed', 19850101, female)."
    )
    assert passed is False
    assert reason == "Goal failed"



def test_consult_error():
    """An invalid Prolog program should surface a 'Prolog error' reason."""
    bad_prog = 'this is definitely not valid prolog.'
    passed, reason = pc.consult(bad_prog, 'fake_goal.')
    assert passed is False
    assert reason and 'Prolog error' in reason

# -----------------------------------------------------------------------------
# Helper‑function unit tests (do not need SWI‑Prolog)
# -----------------------------------------------------------------------------

def test_extract_goal_from_test_wrapper():
    """extract_goal should unwrap test(...) and remove trailing period."""
    src = "test('basic_cover', is_claim_covered('Johnny Appleseed', 01011973, Male))."
    goal = pc.extract_goal(src)
    assert goal == "is_claim_covered('Johnny Appleseed', 01011973, Male)"


def test_extract_goal_bare_goal():
    """When given a bare goal the function should return it unchanged (minus period)."""
    assert pc.extract_goal('likes(mary, pizza).') == 'likes(mary, pizza)'


def test_drop_comments():
    """_drop_comments should strip both full‑line and inline % comments."""
    src = '% full line comment\nlikes(mary, pizza). % trailing comment'
    out = pc._drop_comments(src)
    assert out.strip() == 'likes(mary, pizza).'

def test_extract_goal_with_negation_and_quotes():
    src = r"test('negated_case', \+is_claim_covered(81, 150, 'Accidental Injury'))."
    goal = pc.extract_goal(src)
    assert goal == r"\+is_claim_covered(81, 150, 'Accidental Injury')"


MULTI_CASE_POLICY = dedent("""
    % Same logic as above
    is_claim_covered(ClaimantAge, HospitalizationDateRelativeToEffectiveDate, ReasonForHospitalization) :-
        (sub_string(ReasonForHospitalization, _, _, _, "Military Service") -> ClaimantMilitaryService = true ; ClaimantMilitaryService = false),
        (sub_string(ReasonForHospitalization, _, _, _, "Skydiving") -> ClaimantSkydivingActivity = true ; ClaimantSkydivingActivity = false),
        ClaimantFirefighterService = false,
        ClaimantPoliceService = false,
        wellness_visit_condition_satisfied(HospitalizationDateRelativeToEffectiveDate),
        not(general_exclusion_applies(ClaimantAge, ClaimantMilitaryService, ClaimantFirefighterService, ClaimantPoliceService, ClaimantSkydivingActivity)).

    wellness_visit_condition_satisfied(DateRelativeToEffectiveDate) :-
        DateRelativeToEffectiveDate =< 180.

    general_exclusion_applies(Age, Military, Firefighter, Police, Skydiving) :-
        Skydiving == true;
        Military == true;
        Firefighter == true;
        Police == true;
        Age >= 80.
""")

MULTI_CASE_TESTS = [
    # (Description, Goal, Expected)
    ("covered_normal_hospitalization", "is_claim_covered(55, 100, 'Sickness')", True),
    ("excluded_age_over_80", r"\+is_claim_covered(81, 150, 'Accidental Injury')", True),
    ("excluded_military_service", r"\+is_claim_covered(30, 200, 'Accidental Injury_Military Service')", True),
    ("covered_wellness_visit_satisfied", "is_claim_covered(40, 180, 'Sickness')", True),
    ("excluded_wellness_visit_not_satisfied", r"\+is_claim_covered(50, 300, 'Sickness')", True),
    ("excluded_skydiving", r"\+is_claim_covered(25, 50, 'Accidental Injury_Skydiving')", True),
]

@pytest.mark.parametrize("desc, goal, expected", MULTI_CASE_TESTS)
def test_policy_multi_case(desc, goal, expected):
    passed, reason = pc.consult(MULTI_CASE_POLICY, goal)
    assert passed == expected, f"Test failed: {desc}\nReason: {reason}"


def test_evaluator_classifies_correctly():
    policy = MULTI_CASE_POLICY
    test_fact = "test('neg_case', \\+is_claim_covered(81, 150, 'Accidental Injury'))."
    evaluator = Evaluator(log_manager=LogManager())
    result, reason = evaluator._run_single_test(policy, test_fact)
    assert result == "logic_pass", f"Expected logic_pass, got {result}: {reason}"



if __name__ == "__main__":
    # Run the tests if this file is executed directly
    pytest.main([__file__, "-v", "--tb=short"])
    # Note: In practice, you would run this with `python -m pytest` from the command line.