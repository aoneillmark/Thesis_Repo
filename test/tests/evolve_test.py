import pytest
import shutil
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from evolve import compute_pass_rates, select_refactor_target, repair_program, repair_test
from collections import defaultdict
from suite_manager import CandidateSolution, TestCase, SuiteManager


def test_compute_pass_rates_basic():
    matrix = [
        [1, 0, 1],
        [1, 1, 0],
    ]
    prog_rates, test_rates = compute_pass_rates(matrix)
    assert prog_rates == [2/3, 2/3]
    assert test_rates == [1.0, 0.5, 0.5]


def test_select_refactor_target_chooses_lowest(monkeypatch):
    prog_rates = [0.9, 0.4]
    test_rates = [0.3, 0.7]
    repair_attempts = defaultdict(int)
    last_fixed_iter = {}

    target, idx = select_refactor_target(prog_rates, test_rates, iteration=1,
                                         repair_attempts=repair_attempts,
                                         last_fixed_iter=last_fixed_iter)
    # Should return test index 0 (rate=0.3) as lowest among eligible
    print(f"Selected target: {target}, index: {idx}")
    assert target == "test"
    assert idx == 0


@pytest.fixture
def dummy_suite():
    suite = SuiteManager()
    suite.solutions = [
        CandidateSolution("dummy", program_text="p1."),
        CandidateSolution("dummy", program_text="p2."),
    ]
    suite.test_cases = [
        TestCase("test('t1', test_pred(1))."),
        TestCase("test('t2', test_pred(2))."),
    ]
    return suite


def test_repair_program_passes_failing_tests(monkeypatch, dummy_suite):
    called = {}

    def fake_generate(prompt):
        called['prompt'] = prompt
        return "fixed_program."

    monkeypatch.setattr("evolve.generate_content", fake_generate)

    # simulate failing on test 0, passing on test 1
    failing_tests = [dummy_suite.test_cases[0]]
    repair_program(dummy_suite, p_idx=0, failing_tests=failing_tests)

    print("yahoo")
    print("Called prompt:", called.get('prompt', 'No prompt called'))

    assert (1==2)
    assert "test('t1', test_pred(1))" in called['prompt']
    assert "fixed_program" in dummy_suite.solutions[0].original_program


def test_repair_test_passes_failing_programs(monkeypatch, dummy_suite):
    called = {}

    def fake_generate(prompt):
        called['prompt'] = prompt
        return "fixed_test."

    monkeypatch.setattr("evolve.generate_content", fake_generate)

    failing_progs = [dummy_suite.solutions[1]]
    repair_test(dummy_suite, t_idx=1, failing_progs=failing_progs)

    assert "p2." in called['prompt']  # program text used
    assert "fixed_test" in dummy_suite.test_cases[1].original_fact

