"""
suite_manager_z3.py  ──────────────────────────────────────────────────────────────

High‑level refactor of the original Prolog‑centric Suite Manager to support the new
Z3‑based workflow you described:

• Z3CandidateSolution  – holds *only* the # Declarations and # Constraints block
    of a logic programme.
• Z3TestCase           – holds the # Options block (MCQ question, labelled options
    plus the authoritative correct label).
• SuiteManagerZ3       – orchestrates co‑evolution: it can generate new candidate
    solutions and tests via the LLM, run them through an (external) EvaluatorZ3,
    and keep the same fitness bookkeeping you already have.

This file **does not yet** wire in the concrete EvaluatorZ3 implementation – you
already have a Z3 runner in `LSAT_Z3_Program`; you can import / adapt that for
the `_run_single_test` path.
"""

import os
import re
import uuid
from pathlib import Path
from typing import List, Tuple
from utils import generate_content
from logging_utils import LogManager
from prompts import (
    Z3_CANDIDATE_SOLUTION_PROMPT,
    Z3_TEST_SUITE_GENERATION_PROMPT,
)
from evaluator import Evaluator

# ────────────────────────────────────────────────────────────────────────────────
# Z3CandidateSolution ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
# ────────────────────────────────────────────────────────────────────────────────

class CandidateSolution:
    """A *programme skeleton*: only declarations + constraints.

    The class can be initialised from a *full* logic programme (containing
    # Options etc.) or directly from a block containing only the bits we need.
    """

    def __init__(
        self,
        context_text: str,
        *,
        prompt: str | None = None,
        logic_snippet: str | None = None,
    ) -> None:
        self.id = f"sol_{uuid.uuid4().hex[:8]}"

        if logic_snippet is not None:
            raw_logic = logic_snippet.strip()
        else:
            raw_logic = self._generate_predicates_premises(context_text, prompt)

        self.predicates, self.premises = self._split_predicates_premises(raw_logic)

        # Fitness placeholders (will be filled in by Evaluator)
        self.logic_fitness: float | str = "dummy"
        self.vocab_fitness: float | str = "dummy"
        self.syntax_errors: list[str] = []

    # ───────────────────────── helpers ─────────────────────────

    def _generate_predicates_premises(
        self, context_text: str, user_prompt: str | None
    ) -> str:
        """Call the LLM to produce the Predicates + Premises block."""
        if user_prompt:
            generation_prompt = user_prompt
        else:
            generation_prompt = FOLIO_CANDIDATE_SOLUTION_PROMPT.format(PROBLEM=context_text)

        print("  - Generating Predicates / Premises with LLM …")
        snippet = generate_content(generation_prompt)
        if not snippet:
            raise RuntimeError("❌ LLM failed to generate a candidate solution.")
        print("  ✅ Candidate solution generated.")
        return snippet.strip()

    @staticmethod
    def _split_predicates_premises(block: str) -> Tuple[str, str]:
        """Split the block into predicates and premises sections."""
        predicates_path = r"#\s*Predicates(.+?)(?=#\s*Premises)"
        premises_path = r"#\s*Premises(.+)$"
        predicates_m = re.search(predicates_path, block, re.DOTALL | re.IGNORECASE)
        premises_m = re.search(premises_path, block, re.DOTALL | re.IGNORECASE)

        if not (predicates_m and premises_m):
            print("🛑 Cannot split predicates / premises – expected both sections.")
            return "", ""

        predicates = predicates_m.group(1).strip()
        premises = premises_m.group(1).strip()
        return predicates, premises

    # ───────────────────────── convenience ─────────────────────────

    @property
    def canonical_program(self) -> str:
        """Re‑assemble programme for execution (without # Options)."""
        return (
            "# Predicates\n" + self.predicates + "\n\n" + "# Premises\n" + self.premises
        )
# ────────────────────────────────────────────────────────────────────────────────
# Z3TestCase ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
# ────────────────────────────────────────────────────────────────────────────────

class TestCase:
    """Container for a single FOLIO test case (# Questions / # Conclusions)."""

    def __init__(self, raw_block: str):
        self.id = f"tc_{uuid.uuid4().hex[:8]}"
        self.original_block = raw_block.strip()

        # Parse the two mandatory sections
        self.questions, self.conclusions = self._split_questions_conclusions(self.original_block)

        # Fitness placeholders (populated by the Evaluator later)
        self.logic_fitness: float | str = "dummy"
        self.vocab_fitness: float | str = "dummy"
        self.syntax_errors: list[str] = []

    # ───────────────────────── helpers ─────────────────────────

    @staticmethod
    def _split_questions_conclusions(block: str) -> Tuple[List[str], List[str]]:
        """Return the question lines and conclusion lines (both stripped)."""
        q_pat = r"#\s*Question(.+?)(?=#\s*Conclusions)"
        c_pat = r"#\s*Conclusions(.+)$"

        q_m = re.search(q_pat, block, re.DOTALL | re.IGNORECASE)
        c_m = re.search(c_pat, block, re.DOTALL | re.IGNORECASE)
        if not (q_m and c_m):
            raise ValueError(
                "🛑 TestCase must include both `# Questions` and `# Conclusions` blocks."
            )

        q_lines = [ln.strip() for ln in q_m.group(1).strip().splitlines() if ln.strip()]
        c_lines = [ln.strip() for ln in c_m.group(1).strip().splitlines() if ln.strip()]
        return q_lines, c_lines

    # ───────────────────────── convenience ─────────────────────────

    @property
    def canonical_block(self) -> str:
        return self.original_block

# ────────────────────────────────────────────────────────────────────────────────
# SuiteManagerZ3 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
# ────────────────────────────────────────────────────────────────────────────────

class SuiteManager:
    """Manages co‑evolution of CandidateSolutions and TestCases in FOLIO land."""

    def __init__(self, *, log_root: str = "logs", run_id: str | None = None):
        self.logm = LogManager(root=log_root, run_id=run_id)
        self.solutions: List[CandidateSolution] = []
        self.test_cases: List[TestCase] = []
        self.evaluator = Evaluator(self.logm)

    # ───────────────────────── generation helpers ─────────────────────────

    def generate_candidate_solutions(
        self,
        n: int,
        problem_text: str,
        prompts: List[str | None] | None = None,
    ) -> None:
        prompts = prompts or [None] * n
        for i in range(n):
            print(f"\n🧬 Creating Solution {i+1}/{n} …")
            sol = CandidateSolution(problem_text, prompt=prompts[i])
            self.solutions.append(sol)

    def generate_test_cases(
        self,
        n: int,
        problem_text: str,
        user_prompt: str | None = None,
    ) -> None:
        print(f"\n🧪 Generating {n} FOLIO test cases …")
        prompt = (
            user_prompt
            if user_prompt is not None
            else FOLIO_TEST_SUITE_GENERATION_PROMPT.format(PROBLEM=problem_text, num_cases=n)
        )
        raw = generate_content(prompt)
        if not raw:
            raise RuntimeError("❌ LLM failed to generate test cases.")

        # Expect the LLM to separate individual cases with five # characters
        blocks = [b.strip() for b in re.split(r"^#####\s*$", raw, flags=re.MULTILINE) if b.strip()]
        if len(blocks) < n:
            print("⚠️  LLM returned fewer cases than requested – using what we got.")
        cases = [TestCase(b) for b in blocks[:n]]
        self.test_cases.extend(cases)
        print(f"  ✅ Added {len(cases)} fresh test cases.")

        # Persist raw LLM output
        out_path = self.logm.run_dir / "raw_test_case_blocks.txt"
        Path(out_path).write_text(raw, encoding="utf-8")

    # ───────────────────────── evaluation scaffold ─────────────────────────

    def evaluate_fitness(self, *, scope: str = "adhoc") -> None:
        if self.evaluator is None:
            raise NotImplementedError(
                "Hook up EvaluatorFOLIO before calling evaluate_fitness()."
            )
        self.evaluator.evaluate(self.solutions, self.test_cases, scope)

    # ───────────────────────── convenience ─────────────────────────

    def save_summary(self) -> None:
        summ = ["\n— Solutions —"]
        for sol in sorted(
            self.solutions,
            key=lambda s: float(s.logic_fitness if isinstance(s.logic_fitness, (int, float)) else 0),
            reverse=True,
        ):
            summ.append(
                f"{sol.id}\tlogic={sol.logic_fitness}\tvocab={sol.vocab_fitness}"
            )
        summ.append("\n— Test Cases —")
        for tc in self.test_cases:
            summ.append(
                f"{tc.id}\tlogic={tc.logic_fitness}\tvocab={tc.vocab_fitness}"
            )

        path = self.logm.run_dir / "summary.txt"
        Path(path).write_text("\n".join(summ), encoding="utf-8")
# if __name__ == "__main__":
#     tc = TestCase("""Question:
# If R speaks second at meeting 2 and first at meeting 3, which one of the following is a complete and accurate list of those time slots any one of which could be the time slot in which R speaks at meeting 1?
# Choices:
# (A) fourth, fifth
# (B) first, second, fifth
# (C) second, third, fifth
# (D) third, fourth, fifth
# (E) second, third, fourth, fifth
# # Options
# Question ::: Which one of the following is a complete and accurate list of those time slots any one of which could be the time slot in which R speaks at meeting 1?
# is_accurate_list([speaks(1, R) == 4, speaks(1, R) == 5]) ::: (A)
# is_accurate_list([speaks(1, R) == 1, speaks(1, R) == 2, speaks(1, R) == 5]) ::: (B)
# is_accurate_list([speaks(1, R) == 2, speaks(1, R) == 3, speaks(1, R) == 5]) ::: (C)
# is_accurate_list([speaks(1, R) == 3, speaks(1, R) == 4, speaks(1, R) == 5]) ::: (D)
# is_accurate_list([speaks(1, R) == 2, speaks(1, R) == 3, speaks(1, R) == 4, speaks(1, R) == 5]) ::: (E) *
# """)
#     print(tc.nl_prelude)
#     print("\n")
    
#     print(tc.question_line)
#     print("\n")
#     # print(tc.options_block)
#     # print options_block without asterisks (options block just without any asterisks at all), simple parse
#     options_no_asterisks = re.sub(r"\s*\*\s*$", "", tc.options_block, flags=re.MULTILINE)
#     print(options_no_asterisks)
#     print("\n")

#     print(tc.options_dict)
#     print("\n")
#     print(tc.correct_label)


if __name__ == "__main__":
    # Example usage
    sm = SuiteManager(log_root="test_logs")
    number_of_cases = 3
    number_of_solutions = 2

    problem = "Of the eight students—George, Helen, Irving, Kyle, Lenore, Nina, Olivia, and Robert—in a seminar, exactly six will give individual oral reports during three consecutive days—Monday, Tuesday, and Wednesday. Exactly two reports will be given each day—one in the morning and one in the afternoon—according to the following conditions: Tuesday is the only day on which George can give a report. Neither Olivia nor Robert can give an afternoon report. If Nina gives a report, then on the next day Helen and Irving must both give reports, unless Nina's report is given on Wednesday."

    sm.generate_test_cases(number_of_cases, problem)

    prompts = [ 
        Z3_CANDIDATE_SOLUTION_PROMPT.format(PROBLEM=problem).join("\n Here are the test cases:".join(tc.canonical_block for tc in sm.test_cases))
        for idx in range(number_of_solutions)
    ]

    sm.generate_candidate_solutions(number_of_solutions, problem, prompts)

    # Evaluate fitness (requires an Evaluator implementation)
    sm.evaluate_fitness(scope="test_run")

    # Save a summary of the run
    sm.save_summary()