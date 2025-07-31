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
            raw_logic = self._generate_decls_constraints(context_text, prompt)

        self.declarations, self.constraints = self._split_decls_constraints(raw_logic)

        # Fitness placeholders (will be filled in by Evaluator)
        self.logic_fitness: float | str = "dummy"
        self.vocab_fitness: float | str = "dummy"
        self.syntax_errors: list[str] = []

    # ───────────────────────── helpers ─────────────────────────

    def _generate_decls_constraints(self, context_text: str, user_prompt: str | None) -> str:
        """Call the LLM to produce the # Declarations + # Constraints block."""
        if user_prompt:
            generation_prompt = user_prompt
        else:
            generation_prompt = Z3_CANDIDATE_SOLUTION_PROMPT.format(PROBLEM=context_text)

        print("  - Generating Declarations / Constraints with LLM …")
        snippet = generate_content(generation_prompt)
        if not snippet:
            raise RuntimeError("❌ LLM failed to generate a candidate solution.")
        print("  ✅ Candidate solution generated.")
        return snippet.strip()

    @staticmethod
    def _split_decls_constraints(block: str) -> Tuple[str, str]:
        """Extract the two sections from a mixed block.

        Raises if either is missing – they *must* be present for the programme to
        be meaningful.
        """
        decl_pat = r"#\s*Declarations(.+?)(?=#\s*Constraints)"
        cons_pat = r"#\s*Constraints(.+)$"
        decl_m = re.search(decl_pat, block, re.DOTALL | re.IGNORECASE)
        cons_m = re.search(cons_pat, block, re.DOTALL | re.IGNORECASE)

        if not (decl_m and cons_m):
            print("🛑 Cannot split declarations / constraints – expected both sections.")
            return "", ""

        declarations = decl_m.group(1).strip()
        constraints = cons_m.group(1).strip()
        return declarations, constraints

    # ───────────────────────── convenience ─────────────────────────

    @property
    def canonical_program(self) -> str:
        """Re‑assemble programme for execution (without # Options)."""
        return (
            "# Declarations\n" + self.declarations + "\n\n" + "# Constraints\n" + self.constraints
        )

# ────────────────────────────────────────────────────────────────────────────────
# Z3TestCase ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
# ────────────────────────────────────────────────────────────────────────────────

class TestCase:
    """A multiple‑choice query block (# Options + gold answer).

    Assumes the *input* is the raw block starting with `# Options`.
    """

    def __init__(self, raw_block: str):
        self.id = f"tc_{uuid.uuid4().hex[:8]}"

        # Split on # Options header (can appear anywhere in the block)
        parts = re.split(r"(?i)(?:^|\n)#\s*Options", raw_block, maxsplit=1)
        if len(parts) != 2:
            raise ValueError("🛑 TestCase must contain a `# Options` section.")
        
        self.nl_prelude = parts[0].strip()  # natural-language portion
        self.options_block = "# Options" + parts[1]  # restore header for consistency

        self.original_block = raw_block.strip()
        self.question_line, self.option_lines = self._split_question_options(self.options_block)
        self.options_dict = self._parse_option_lines(self.option_lines)
        self.correct_label = self._infer_correct_label(self.options_dict)

        self.logic_fitness: float | str = "dummy"
        self.vocab_fitness: float | str = "dummy"
        self.syntax_errors: list[str] = []

    # ───────────────────────── helpers ─────────────────────────

    @staticmethod
    def _split_question_options(block: str) -> Tuple[str, List[str]]:
        # Expect first non‑empty line after `# Options` to start with "Question".
        lines = [l.rstrip() for l in block.splitlines() if l.strip()]

        if not lines[0].lower().startswith("# options"):
            raise ValueError("🛑 TestCase must begin with a `# Options` header.")
        if not lines[1].lower().startswith("question"):
            raise ValueError("🛑 Second line should be the Question statement.")

        question_line = lines[1]
        option_lines = lines[2:]
        return question_line, option_lines

    @staticmethod
    def _parse_option_lines(lines: List[str]) -> dict[str, str]:
        """Return mapping {label → logic‑string} and mark correct if ':::(X) *'."""
        out = {}
        for ln in lines:
            # Match pattern like: some_logic ::: (A) or ::: (E) *
            m = re.match(r"(.+?):::\s*\((.)\)\s*(\*?)$", ln)
            if not m:
                raise ValueError(f"🛑 Option line malformed: {ln}")
            logic, label, is_gold = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
            if is_gold:
                out[label] = logic
                # Attach the gold label now, so _infer_correct_label can pick it up
                out["_gold"] = label
            else:
                out[label] = logic
        return out

    @staticmethod
    def _infer_correct_label(options: dict[str, str]) -> str | None:
        """Pull the gold label if present, and remove helper key."""
        if "_gold" in options:
            gold = options.pop("_gold")
            return gold
        return None

    # ───────────────────────── convenience ─────────────────────────

    @property
    def canonical_block(self) -> str:
        return self.original_block  # already canonical

# ────────────────────────────────────────────────────────────────────────────────
# SuiteManagerZ3 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
# ────────────────────────────────────────────────────────────────────────────────

class SuiteManager:
    """Manages candidate solutions & test cases for the Z3 workflow."""

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
        """Populate self.solutions with *n* new candidates."""
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
        """Generate *n* MCQ test cases and append to self.test_cases."""
        print(f"\n🧪 Generating {n} Z3 test cases …")
        if not user_prompt:
            prompt = Z3_TEST_SUITE_GENERATION_PROMPT.format(
                PROBLEM=problem_text, num_cases=n
            )
        else:
            prompt = user_prompt
        raw = generate_content(prompt)
        if not raw:
            raise RuntimeError("❌ LLM failed to generate test cases.")

        blocks = [blk.strip() for blk in re.split(r"^#####\s*$", raw, flags=re.MULTILINE) if blk.strip()]
        if len(blocks) < n:
            print("⚠️  LLM returned fewer cases than requested – taking what we got.")
        cases = [TestCase(b) for b in blocks[:n]]
        self.test_cases.extend(cases)
        print(f"  ✅ Added {len(cases)} fresh test cases.")

        # Persist raw output for inspection
        out_path = self.logm.run_dir / "raw_test_case_blocks.txt"
        out_path.write_text(raw, encoding="utf-8")

    # ───────────────────────── evaluation scaffold ─────────────────────────

    def evaluate_fitness(self, *, scope: str = "adhoc") -> None:
        """Delegate to EvaluatorZ3 (to be implemented)."""
        if self.evaluator is None:
            raise NotImplementedError("Hook up EvaluatorZ3 before calling evaluate_fitness().")
        self.evaluator.evaluate(self.solutions, self.test_cases, scope)

    # ───────────────────────── convenience ─────────────────────────

    def save_summary(self) -> None:
        """Dump a flat text summary to the run folder."""
        summ = []
        summ.append("\n— Solutions —")
        for sol in sorted(self.solutions, key=lambda s: float(s.logic_fitness if isinstance(s.logic_fitness, (int, float)) else 0), reverse=True):
            summ.append(f"{sol.id}\tlogic={sol.logic_fitness}\tvocab={sol.vocab_fitness}")
        summ.append("\n— Test Cases —")
        for tc in self.test_cases:
            summ.append(f"{tc.id}\tlogic={tc.logic_fitness}\tvocab={tc.vocab_fitness}")

        path = self.logm.run_dir / "summary.txt"
        path.write_text("\n".join(summ), encoding="utf‑8")

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