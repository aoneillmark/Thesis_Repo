#!/usr/bin/env python3
"""
Evaluate all candidate solutions in a CoCoEvo *run_* directory against a FOLIO‑style
multiple‑choice dataset **with vocabulary alignment**.

Change log (2025‑08‑02):
-----------------------
* **Per‑solution × per‑question LLM calls** – we now translate the question into a
  first‑order‑logic conclusion *using the solution text as additional context*,
  ensuring the generated formula reuses the same predicate / constant names.
* The helper `generate_fol_conclusion()` therefore receives the *solution
  encoding* and includes it in the prompt.
* This means we make **N_solutions × N_questions** LLM calls.

Usage example
-------------
python evaluate_run.py \
    --run_dir runs/run_20250802T161542_33a790 \
    --dataset folio_dev.json \
    --openai_api_key $OPENAI_API_KEY
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import List, Tuple

from fol_solver.prover9_solver import FOL_Prover9_Program  

from utils import generate_content
import re
from pathlib import Path
from typing import Tuple, List

# ---------------------------------------------------------------------------
# Dataset and file utilities
# ---------------------------------------------------------------------------

def load_dataset(path: str | Path) -> list[dict]:
    with open(path, "r", encoding="utf8") as fh:
        return json.load(fh)


def map_answer(answer: str) -> str:
    return {"True": "A", "False": "B", "Unknown": "C"}.get(answer, "D")


EXTENSIONS = {".txt", ".pl", ".p9", ".in", ".fol"}
GEN_PAT    = re.compile(r"(initial|vocab_round_\d+|evo_gen_(\d{4}))")

def generation_key(path: Path) -> Tuple[int, int]:
    """Map a solution path to a sortable (major, minor) key."""
    label = next((p for p in path.parts if GEN_PAT.match(p)), "zzz")

    if label == "initial":
        return (0, 0)
    if label.startswith("vocab_round_"):
        return (1, int(label.split("_")[-1]))          # vocab_round_00 -> (1, 0)
    m = re.match(r"evo_gen_(\\d{4})", label)
    if m:
        return (2, int(m.group(1)))                   # evo_gen_0001 -> (2, 1)
    return (9, 0)                                     # unknown -> bottom


def find_solution_files(run_dir: Path) -> List[Path]:
    files = [
        p for p in run_dir.rglob("*")
        if p.is_file()
        and p.suffix in EXTENSIONS
        and "solutions" in p.parts
        and "spawned_programs" not in p.parts
    ]
    return sorted(files, key=generation_key)

# ---------------------------------------------------------------------------
# LLM interaction
# ---------------------------------------------------------------------------

def generate_fol_conclusion(
    *,
    context: str,
    question: str,
    solution_text: str,
) -> str:
    """Return ONLY the FOL formula as a string.

    We show the LLM the *solution_text* so it can mirror predicate / constant
    names.  The model is instructed **not to alter the solution code**, only to
    provide a conclusion that compiles with it.
    """

    system_msg = (
        "You are a formal‑logic assistant specialised in generating Prover9‑"
        "compatible first‑order‑logic (FOL) formulas. Given a candidate solution "
        "program that already defines predicates and constants, translate the "
        "natural‑language statement into *one* FOL formula that is syntactically "
        "consistent with the candidate's vocabulary. Do NOT repeat or modify the "
        "solution program. Return ONLY the formula, on a single line."
        "Here is some notation:"
        """
The grammar of the first-order logic formular is defined as follows:
1) logical conjunction of expr1 and expr2: expr1 ∧ expr2
2) logical disjunction of expr1 and expr2: expr1 ∨ expr2
3) logical exclusive disjunction of expr1 and expr2: expr1 ⊕ expr2
4) logical negation of expr1: ¬expr1
5) expr1 implies expr2: expr1 → expr2
6) expr1 if and only if expr2: expr1 ↔ expr2
7) logical universal quantification: ∀x
8) logical existential quantification: ∃x
"""
    )

    user_prompt = (
        "Candidate solution (context for vocabulary):\n" +
        solution_text[-4000:] +  # keep last ~4000 chars to stay within tokens
        "\n\nProblem context (informal premises):\n" + context.strip() +
        "\n\nSTATEMENT TO TRANSLATE:\n" + question.strip() +
        "\n\nReturn exactly one line encoding the FOL formula."
    )

    completion = generate_content(
        prompt=system_msg+user_prompt,
    )

    content = completion.strip()
    return content


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate_solution_against_dataset(solution_text: str, dataset: list[dict]) -> Tuple[int, int, list]:
    correct = total = 0
    detailed_results = []

    for item in dataset:
        fol_conclusion = generate_fol_conclusion(
            context=item["context"],
            question=item["question"],
            solution_text=solution_text,
        )

        combined_program = (
            solution_text.strip() +
            "\n\n# Conclusion:\n" + fol_conclusion + "\n"
        )

        prover9_program = FOL_Prover9_Program(combined_program)
        answer, error_message = prover9_program.execute_program()
        
        # Always increment total count
        total += 1
        
        # Track detailed results for this question
        question_result = {
            "question_id": item["id"],
            "context": item["context"],
            "question": item["question"],
            "expected_answer": item["answer"],
            "generated_fol_conclusion": fol_conclusion,
            "combined_program": combined_program,
            "prover9_answer": answer,
            "error_message": error_message,
            "predicted_answer": None,
            "is_correct": False
        }
        
        if error_message:
            print(
                f"[ERROR] Prover9 error on {item['id']}: {error_message}",
                file=sys.stderr,
            )
            # Don't increment correct count for errors
            question_result["predicted_answer"] = "ERROR"
        else:
            predicted = map_answer(answer)
            question_result["predicted_answer"] = predicted
            question_result["is_correct"] = predicted == item["answer"]
            correct += question_result["is_correct"]
        
        detailed_results.append(question_result)

    return correct, total, detailed_results

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Evaluate CoCoEvo run outputs with vocab‑aware conclusions.")
    parser.add_argument("--run_dir", required=True, help="Path to a run_* directory")
    parser.add_argument("--dataset", required=True, help="Path to dataset JSON list")
    parser.add_argument("--output_file", help="Optional: save detailed results to JSON file")

    args = parser.parse_args(argv)

    dataset = load_dataset(args.dataset)
    files = find_solution_files(Path(args.run_dir))  # Convert string to Path

    # Deduplicate by filename and read content
    unique: dict[str, tuple[Path, str]] = {}
    for path in find_solution_files(Path(args.run_dir)):
        name = path.name
        if name in unique:          # already saw earlier generation → skip
            continue
        with open(path, "r", encoding="utf8") as fh:
            unique[name] = (path, fh.read())

    if not unique:
        print("No solutions found.")
        return

    overall_correct = overall_total = 0
    results = {
        "run_dir": str(args.run_dir),
        "dataset": str(args.dataset),
        "solutions": [],
        "summary": {}
    }
    
    print(f"Evaluating {len(unique)} solutions, {len(dataset)} questions each...\n")

    for key, (path, sol_text) in sorted(unique.items()):
        correct, total, detailed_results = evaluate_solution_against_dataset(sol_text, dataset)
        acc = correct / total if total else 0.0
        
        # Save per-solution results with detailed question-level data
        solution_result = {
            "solution_name": key,
            "solution_path": str(path),
            "correct": correct,
            "total": total,
            "accuracy": acc,
            "question_results": detailed_results
        }
        results["solutions"].append(solution_result)
        
        print(f"{key:<50} {correct:>2}/{total:<2}  ({acc:.1%})")
        overall_correct += correct
        overall_total += total

    # Save summary
    if overall_total:
        overall_acc = overall_correct / overall_total
        results["summary"] = {
            "total_correct": overall_correct,
            "total_questions": overall_total,
            "overall_accuracy": overall_acc
        }
        
        print("\n────────────────────────────────────────")
        print(f"Overall accuracy: {overall_correct}/{overall_total} ({overall_acc:.1%})")
        
        # Save results to file if requested
        if hasattr(args, 'output_file') and args.output_file:
            with open(args.output_file, "w", encoding="utf8") as f:
                json.dump(results, f, indent=2)
            print(f"Results saved to: {args.output_file}")

if __name__ == "__main__":
    main()
