#!/usr/bin/env python3
"""generate_queries.py – turn top encodings + claims into Prolog queries.

Folder layout assumed
---------------------
test/
 └─ logs/
     └─ policy_*/
         └─ <timestamp_run>/
             ├─ summary.txt
             ├─ oneshot/solutions/sol_<id>.pl
             └─ evo_gen_000*/solutions/sol_<id>.pl
test/
 └─ benchmark_claim/claim_*.txt
benchmark_policy/
 └─ policy_*.txt            (not strictly needed in the prompt)

Usage
-----
$ python generate_queries.py                # sequential
$ python generate_queries.py -p 4           # 4 processes
$ python generate_queries.py --dry          # just print work
"""
from __future__ import annotations
import argparse, pathlib, re, concurrent.futures as cf, time, traceback
from typing import List, Optional
import os

from utils import generate_content  # your existing helper

# ─────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────
SCRIPT_DIR = pathlib.Path(__file__).parent
ROOT_LOGS     = SCRIPT_DIR / "logs"
CLAIM_DIR     = SCRIPT_DIR / "benchmark_claim"
CLAIM_GLOB    = "claim_*.txt"
SUMMARY_NAME  = "summary.txt"

QUERY_PROMPT = """You are an expert Prolog developer.
You are given a Prolog program that encodes an insurance contract, and a claim in English.
Your task is to generate a Prolog query that can query whether the claim is covered under the contract.
You are to write a single Prolog query that uses the predicates defined in the program.
The query should be a single line, ending with a period.
**Return only the query - no explanation.**

### Contract encoding
{program}

### Claim
{claim}
"""

# ───────────────────────── helpers ──────────────────────────────────────
rank_re = re.compile(r"Rank\s+#1\s+\|\s+Solution\s+(\w+)", re.I)

def first_rank_solution(summary_path: pathlib.Path) -> Optional[str]:
    """Return the solution id (e.g. 'sol_34668981') that is Rank #1."""
    for line in summary_path.read_text(encoding="utf-8").splitlines():
        m = rank_re.search(line)
        if m:
            return m.group(1)
    return None

# def find_pl(run_root: pathlib.Path, sol_id: str) -> Optional[pathlib.Path]:
#     """Search immediate child dirs (* /solutions/sol_id.pl)."""
#     patt = f"*/solutions/{sol_id}.pl"
#     hits = list(run_root.glob(patt))
#     return hits[0] if hits else None

def run_kind(pl_path: pathlib.Path, run_root: pathlib.Path) -> str:
    """
    Return the *first* path component under <timestamp_run>/…

    examples
    --------
    …/oneshot/solutions/…            → "oneshot"
    …/initial/solutions/…            → "initial"
    …/evo_gen_0002/post/solutions/…  → "evo_gen_0002"   (drops 'post')
    """
    rel = pl_path.relative_to(run_root)          # e.g. evo_gen_0002/post/solutions/…
    parts = rel.parts
    return parts[0] if parts else "unknown"

rank_re = re.compile(r"Rank\s+#1\s+\|\s+Solution\s+(\w+)", re.I)

def first_rank_solution(summary_path: pathlib.Path) -> Optional[str]:
    for line in summary_path.read_text(encoding="utf-8").splitlines():
        if (m := rank_re.search(line)):
            return m.group(1)
    return None


def find_pl(run_root: pathlib.Path,
            sol_id: str,
            debug: bool = False) -> Optional[pathlib.Path]:
    """
    Look for the Champion .pl inside *any* <run_root>/<something>/solutions/.
    Prints lots of diagnostics when debug=True.
    """
    # 1 — exact one‑level pattern  (oneshot or evo_gen_000X)
    patt = f"*/solutions/{sol_id}.pl"
    hits = list(run_root.glob(patt))
    if hits:
        if debug:
            print(f"• Found with pattern '{patt}': {hits[0].relative_to(run_root)}")
        return hits[0]

    # 2 — no hit: do a recursive scan & show what *is* there
    if debug:
        print(f"• No match for '{patt}' in {run_root}")
        print("  Listing available .pl files under solutions/:")
        for p in run_root.rglob("solutions/*.pl"):
            print("   ├─", p.relative_to(run_root))
        print("  End of listing.\n")

    # 3 — try a recursive fuzzy search (sometimes filenames have suffixes)
    fuzzy = list(run_root.rglob(f"solutions/*{sol_id}*.pl"))
    if fuzzy:
        if debug:
            print(f"• Fuzzy hit: {fuzzy[0].relative_to(run_root)}")
        return fuzzy[0]

    return None


def call_llm(program: str, claim: str, retries: int = 3) -> str:
    if not program or not claim:
        print("❌ Empty program or claim")
    prompt = QUERY_PROMPT.format(program=program.strip(), claim=claim.strip())
    for _ in range(retries):
        out = (generate_content(prompt)).strip()
        if not out:
            print("❌ Empty LLM response")
            return ""
        if out:
            print(f"✓ LLM response: {out}")
            # normalise – ensure single trailing period
            return out if out.endswith(".") else out + "."
        time.sleep(1.5)
    return ""

def save_query(target_dir: pathlib.Path, claim_stem: str, query: str) -> None:
    out_dir = target_dir / "queries"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{claim_stem}.pl").write_text(query + "\n", encoding="utf-8")

def process_run(summary_path: pathlib.Path,
                claim_paths: List[pathlib.Path],
                dry: bool = False) -> None:
    run_root = summary_path.parent
    
    # Extract policy number from path (e.g., "policy_0" -> 0)
    policy_match = re.search(r'policy_(\d+)', str(summary_path))
    if not policy_match:
        print(f"⚠️  Cannot extract policy number from {summary_path}")
        return
    
    policy_num = int(policy_match.group(1))
    
    # Find matching claim file
    matching_claim = None
    for cpath in claim_paths:
        claim_match = re.search(r'claim_(\d+)\.txt', cpath.name)
        if claim_match and int(claim_match.group(1)) == policy_num:
            matching_claim = cpath
            break
    
    if not matching_claim:
        print(f"⚠️  No matching claim_{policy_num}.txt found for {summary_path}")
        return
    
    sol_id = first_rank_solution(summary_path)
    if not sol_id:
        print(f"⚠️  No Rank #1 line in {summary_path}")
        return

    pl_path = find_pl(run_root, sol_id)
    if not pl_path:
        print(f"⚠️  Cannot find .pl for {sol_id} in {run_root}")
        return

    program_text = pl_path.read_text(encoding="utf-8")
    claim_txt = matching_claim.read_text(encoding="utf-8")
    
    if dry:
        rel = run_root.relative_to(ROOT_LOGS)
        print(f"[dry] {rel}  ←  {matching_claim.name}")
        return

    query = call_llm(program_text, claim_txt)
    if not query:
        print(f"⚠️  LLM failed for {pl_path} + {matching_claim.name}")
        return

    kind      = run_kind(pl_path, run_root)
    target    = run_root / "queries" / kind         # …/<ts_run>/queries/<kind>/
    save_query(target, matching_claim.stem, query)

    rel = target.relative_to(ROOT_LOGS)
    print(f"✓ {rel}/{matching_claim.stem}.pl")

# ───────────────────────── CLI entry ────────────────────────────────────
# … imports unchanged …
import os                                 # NEW

# ───────────────────────── helpers ──────────────────────────────────────
# (unchanged helpers)

# ───────────────────────── CLI entry ────────────────────────────────────
def main(argv: List[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Generate Prolog queries for claims.")
    ap.add_argument("-p", "--parallel", type=int, default=1,
                    help="Worker processes (default 1 = sequential).")
    ap.add_argument("--dry", action="store_true",
                    help="Just list planned work without calling the LLM.")
    ap.add_argument("--debug", action="store_true",
                    help="Print directory diagnostics.")
    args = ap.parse_args(argv)

    if args.debug:
        print("🔍  Debug info:")
        print(f"• Working directory: {os.getcwd()}")
        print(f"• ROOT_LOGS        : {ROOT_LOGS.resolve()}")
        print(f"• CLAIM_DIR        : {CLAIM_DIR.resolve()}")
        print(f"• Looking for      : {CLAIM_GLOB}")
        print()

    # --- discover claims ------------------------------------------------
    claim_paths = sorted(CLAIM_DIR.glob(CLAIM_GLOB))
    if args.debug:
        print(f"• Found {len(claim_paths)} claim files:")
        for p in claim_paths:
            print("    ", p)
        print()

    if not claim_paths:
        print(f"❌ No files matching {CLAIM_GLOB} in {CLAIM_DIR}")
        # Show immediate contents of CLAIM_DIR to help spot typos
        if CLAIM_DIR.exists():
            print("   Contents of CLAIM_DIR:")
            for child in CLAIM_DIR.iterdir():
                print("   ", child)
        else:
            print("   CLAIM_DIR does not exist.")
        return    # early exit instead of argparse error, so debug prints stay visible

    # --- discover summaries --------------------------------------------
    summaries = sorted(ROOT_LOGS.rglob(SUMMARY_NAME))
    if args.debug:
        print(f"• Found {len(summaries)} summary.txt files.")
        for s in summaries[:5]:
            print("    ", s)
        if len(summaries) > 5:
            print("    …")

    if not summaries:
        print(f"❌ No {SUMMARY_NAME} files under {ROOT_LOGS}")
        return

    # --- banner ---------------------------------------------------------
    print(f"🏁 {len(summaries)} runs × {len(claim_paths)} claims "
          f"| parallel={args.parallel} | dry={args.dry} | debug={args.debug}")

    # --- process runs ---------------------------------------------------
    if args.parallel == 1:
        # Sequential processing
        for summary_path in summaries:
            try:
                process_run(summary_path, claim_paths, dry=args.dry)
            except Exception as e:
                print(f"❌ Error processing {summary_path}: {e}")
                if args.debug:
                    traceback.print_exc()
    else:
        # Parallel processing
        def worker(summary_path: pathlib.Path) -> None:
            try:
                process_run(summary_path, claim_paths, dry=args.dry)
            except Exception as e:
                print(f"❌ Error processing {summary_path}: {e}")
                if args.debug:
                    traceback.print_exc()

        with cf.ProcessPoolExecutor(max_workers=args.parallel) as executor:
            executor.map(worker, summaries)

    print("✅ Done!")

if __name__ == "__main__":
    main()