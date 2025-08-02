# main_coco_run.py
from suite_manager import SuiteManager
from evolve import run_vocab_alignment
from coevo_engine import CoCoEvoEngine
from prompts import FOLIO_CANDIDATE_SOLUTION_PROMPT           # already in your repo


if __name__ == "__main__":
    problem_text = (
"""
If people perform in school talent shows often, then they attend and are very engaged with school events. 
People either perform in school talent shows often or are inactive and disinterested members of their community. 
If people chaperone high school dances, then they are not students who attend the school. 
All people who are inactive and disinterested members of their community chaperone high school dances. 
All young children and teenagers who wish to further their academic careers and educational opportunities are students who attend the school. 
Bonnie either both attends and is very engaged with school events and is a student who attends the school, or she neither attends and is very engaged with school events nor is a student who attends the school.
"""
    )

    n_tests      = 5   # how many MCQ blocks to generate
    n_solutions  = 5   # how many candidate programmes to spawn
    log_root     = "runs"  # folder for all logs


    # ── 1. Seed an initial population ──────────────────────────────────
    sm = SuiteManager(log_root=log_root)
    sm.generate_test_cases(n_tests, problem_text)


    questions = "\n".join(tc.questions for tc in sm.test_cases)
    conclusions = "\n".join(tc.conclusions for tc in sm.test_cases)

    base_prompt = FOLIO_CANDIDATE_SOLUTION_PROMPT.format(PROBLEM=problem_text, QUESTION=questions, CONCLUSION=conclusions)


    sm.generate_candidate_solutions(n_solutions, problem_text, prompts=[base_prompt] * n_solutions)


    # ── 3. Stage-2: logic-level co-evolution ───────────────────────────
    engine = CoCoEvoEngine(sm,
                           problem_text=problem_text,
                           max_generations=5,     # tweak as desired
                           pop_cap_programs=10,
                           pop_cap_tests=10,
                           max_reseed_attempts=5  # number of reseeds if initial pop fails vocab alignment
                           )
                           
    engine.run()

    # (Optional) dump a summary
    sm.save_summary()
