#!/usr/bin/env python3
"""Aggregate accuracy *per directory generation* — not just first‑appearance.

This script reads the JSON produced by **evaluate_run.py** and then, *using the
run folder*, recomputes accuracy for every generation directory (`initial/`,
`vocab_round_XX/`, `evo_gen_000N/` …) **based on the files that actually live
there** (duplicates carried forward between generations are now counted in every
generation where they appear).

Example
-------
python analyze_generation_accuracy.py \
    --results folio_evaluation_run_20250802T161542_33a790.json \
    --plot  # optional – saves generation_accuracy.png
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import matplotlib.pyplot as plt  # optional
except ImportError:  # pragma: no cover – plotting is optional
    plt = None

EXTENSIONS = {".txt", ".pl", ".p9", ".in", ".fol"}
# GEN_RE = re.compile(r"^(initial|vocab_round_\d+|evo_gen_\d{4})$")
GEN_RE = re.compile(r"^(initial|evo_gen_\d{4})$")  # Remove vocab_round from regex


# ---------------------------------------------------------------------------
# Helper: sort generations
# ---------------------------------------------------------------------------

def generation_sort_key(gen: str) -> Tuple[int, int]:
    if gen == "initial":
        return (0, 0)
    if gen.startswith("vocab_round_"):
        return (1, int(gen.split("_")[-1]))
    if gen.startswith("evo_gen_"):
        return (2, int(gen.split("_")[-1]))
    return (9, 0)  # unknown ­→ bottom

# ---------------------------------------------------------------------------
# Load evaluation JSON and build lookup tables
# ---------------------------------------------------------------------------

def load_eval(json_path: Path) -> Tuple[Path, Dict[str, Tuple[int, int]]]:
    """Return (run_dir, mapping filename → (correct, total))."""
    with open(json_path, "r", encoding="utf8") as fh:
        data = json.load(fh)
    run_dir = Path(data["run_dir"])
    lookup: Dict[str, Tuple[int, int]] = {}
    for sol in data["solutions"]:
        lookup[sol["solution_name"]] = (sol["correct"], sol["total"])
    return run_dir, lookup

# ---------------------------------------------------------------------------
# Enumerate generation directories and files present in them
# ---------------------------------------------------------------------------

def list_generation_dirs(run_dir: Path) -> List[Path]:
    gens = [p for p in run_dir.iterdir() if p.is_dir() and GEN_RE.match(p.name)]
    return sorted(gens, key=lambda p: generation_sort_key(p.name))


def files_in_generation(gen_dir: Path) -> List[Path]:
    """All solution files *present* in this generation directory."""
    return [
        p
        for p in gen_dir.rglob("solutions/*")
        if p.is_file()
        and p.suffix in EXTENSIONS
        and "spawned_programs" not in p.parts
    ]

# ---------------------------------------------------------------------------
# Aggregation logic
# ---------------------------------------------------------------------------

def aggregate_by_presence(run_dir: Path, score_table: Dict[str, Tuple[int, int]]):
    agg: Dict[str, Tuple[int, int, int]] = {}  # gen → (corr, tot, n_unique)

    for gen_dir in list_generation_dirs(run_dir):
        seen_names = set()
        corr_sum = tot_sum = 0
        for path in files_in_generation(gen_dir):
            name = path.name
            if name in seen_names:
                continue  # de‑dup inside same gen dir
            seen_names.add(name)
            if name not in score_table:
                print(f"[WARN] No evaluation result for {name} — skipping", file=sys.stderr)
                continue
            c, t = score_table[name]
            corr_sum += c
            tot_sum += t
        agg[gen_dir.name] = (corr_sum, tot_sum, len(seen_names))
    return agg

# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def print_table(agg: Dict[str, Tuple[int, int, int]]):
    print("Generation        Solutions Accuracy")
    print("────────────────────────────────────")
    for gen in sorted(agg.keys(), key=generation_sort_key):
        corr, tot, n = agg[gen]
        acc = corr / tot if tot else 0.0
        print(f"{gen:<15} {n:>3}        {acc:.1%}")


def save_plot(agg: Dict[str, Tuple[int, int, int]]):
    if plt is None:
        print("matplotlib not installed; cannot plot.")
        return
    gens = sorted(agg.keys(), key=generation_sort_key)
    accs = [agg[g][0] / agg[g][1] if agg[g][1] else 0 for g in gens]
    plt.figure()
    plt.bar(gens, accs)
    plt.ylabel("Accuracy")
    plt.title("Accuracy by Generation (files present)")
    plt.ylim(0, 1)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig("generation_accuracy.png", dpi=300, bbox_inches="tight")
    print("Plot saved as generation_accuracy.png")
    plt.close()

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: List[str] | None = None):
    ap = argparse.ArgumentParser(description="Accuracy aggregated by *presence* in each generation dir.")
    ap.add_argument("--results", required=True, help="Path to evaluation JSON file")
    ap.add_argument("--plot", action="store_true", help="Save a bar‑chart to generation_accuracy.png")
    args = ap.parse_args(argv)

    run_dir, score_table = load_eval(Path(args.results))
    agg = aggregate_by_presence(run_dir, score_table)
    print_table(agg)
    if args.plot:
        save_plot(agg)


if __name__ == "__main__":
    main()
