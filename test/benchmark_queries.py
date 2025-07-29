#!/usr/bin/env python3
from __future__ import annotations
import pathlib, re, csv, collections
from typing import Dict, List, Tuple, Optional

from prolog_compiler import consult

SCRIPT_DIR = pathlib.Path(__file__).parent
ROOT = SCRIPT_DIR / "logs"  # Fixed: Use relative path from script location

CLAIM_RE = re.compile(r"claim_(\d+)\.pl")
EVO_RE   = re.compile(r"evo_gen_(\d+)")

Result = collections.namedtuple("Result",
                                "policy claim baseline_status evolved_status delta")

# ── helper functions ────────────────────────────────────────
def parse_summary(path: pathlib.Path) -> Optional[str]:
    m = re.search(r"Rank\s+#1\s+\|\s+Solution\s+(\w+)", path.read_text(encoding="utf-8"))
    return m.group(1) if m else None

def load_programs(run_root: pathlib.Path, sol_id: str) -> Dict[str, pathlib.Path]:
    programs = {}
    for pl in run_root.rglob(f"solutions/{sol_id}.pl"):
        kind = pl.relative_to(run_root).parts[0]   # oneshot / initial / evo_gen_000X
        programs[kind] = pl
    return programs

def best_evo_kind(kinds: List[str]) -> Optional[str]:
    evo = [(int(EVO_RE.match(k).group(1)), k) for k in kinds if EVO_RE.match(k)]
    return max(evo)[1] if evo else None

def collect(policy_dir: pathlib.Path):
    """Return baseline bundle & best‑evo bundle gathered across all runs."""
    baseline = {}          # {claim_id: (pl_path, query)}
    evo      = {}
    best_gen = -1

    print(f"    🔍 Collecting from {policy_dir}")
    # Fixed: Use broader pattern to match your actual directory structure
    run_roots = list(policy_dir.glob("*/run_*"))
    print(f"    📁 Found {len(run_roots)} run directories: {[r.name for r in run_roots]}")

    for run_root in run_roots:
        print(f"      📂 Processing {run_root.relative_to(policy_dir)}")
        summary = run_root / "summary.txt"
        print(f"        📄 Summary exists: {summary.exists()}")
        
        sol_id = parse_summary(summary)
        print(f"        🔍 Solution ID: {sol_id}")
        if not sol_id:
            continue

        progs = load_programs(run_root, sol_id)
        print(f"        💾 Programs found: {list(progs.keys())}")
        
        qmap = load_queries(run_root)
        print(f"        🔍 Queries found: {len(qmap)} total - {list(qmap.keys())}")

        for kind, pl in progs.items():
            if kind in {"oneshot", "initial"}:
                matching_queries = [(k, cid) for (k, cid) in qmap.keys() if k == kind]
                print(f"          📊 Baseline {kind}: {len(matching_queries)} matching queries")
                for (k, cid), q in qmap.items():
                    if k == kind:
                        baseline[cid] = (pl, q)
                        print(f"            ✅ Added baseline claim {cid}")

            elif EVO_RE.match(kind):
                gen = int(EVO_RE.match(kind).group(1))
                print(f"          🧬 Evolution {kind} (gen {gen}), best_gen={best_gen}")
                if gen < best_gen:
                    print(f"            ⏭️  Skipping older generation")
                    continue
                if gen > best_gen:
                    print(f"            🆕 New best generation, clearing old")
                    evo.clear(); best_gen = gen
                matching_queries = [(k, cid) for (k, cid) in qmap.keys() if k == kind]
                print(f"            🔍 {len(matching_queries)} matching queries for {kind}")
                for (k, cid), q in qmap.items():
                    if k == kind:
                        evo[cid] = (pl, q)
                        print(f"            ✅ Added evolution claim {cid}")

    return baseline, evo


def load_queries(run_root: pathlib.Path) -> Dict[Tuple[str,int], str]:
    """
    Return {(kind, claim_id): query_string} scanning every place a query
    might live under *this* run_root.

    Fixed to handle the actual directory structure:
    queries/KIND/queries/claim_*.pl
    """
    queries = {}
    patterns = [
        "queries/*/queries/claim_*.pl",     # Main pattern based on actual structure
        "query/claim_*.pl",                 # Fallback patterns
        "queries/claim_*.pl",               
        "queries/*/claim_*.pl",             
        "query/*/claim_*.pl",               
    ]

    for patt in patterns:
        for qpath in run_root.glob(patt):
            parts = qpath.relative_to(run_root).parts
            
            # Handle the nested structure: queries/KIND/queries/claim_*.pl
            if len(parts) >= 3 and parts[0] == "queries" and parts[2] == "queries":
                kind = parts[1]  # The KIND is the middle directory
            elif len(parts) >= 2:
                kind = parts[0]  # Fallback to first directory
            else:
                continue
                
            m = CLAIM_RE.match(qpath.name)
            if not m:
                continue
            cid = int(m.group(1))
            queries[(kind, cid)] = qpath.read_text(encoding="utf-8").strip()
    return queries

def eval_pair(program_path: pathlib.Path, query: str) -> str:
    code = program_path.read_text(encoding="utf-8")
    ok, reason = consult(code, query, timeout=8)
    if ok:
        return "PASS"
    if reason and "Prolog error" in reason:
        return "ERROR"
    return "FAIL"

def benchmark_run(policy: str, run_root: pathlib.Path) -> List[Result]:
    print(f"  🚀 Benchmarking: {policy} - {run_root.name}")
    
    summary_path = run_root / "summary.txt"
    print(f"    Looking for summary: {summary_path} (exists: {summary_path.exists()})")
    
    sol_id = parse_summary(summary_path)
    if not sol_id:
        print(f"    ❌ No solution ID found in summary")
        return []
    print(f"    ✅ Solution ID: {sol_id}")

    programs = load_programs(run_root, sol_id)
    print(f"    📂 Programs found: {list(programs.keys())}")
    
    queries = load_queries(run_root)
    print(f"    🔍 Queries found: {len(queries)} total")
    
    if not programs or not queries:
        print(f"    ❌ Missing programs ({len(programs)}) or queries ({len(queries)})")
        return []

    baseline_kind = "oneshot" if "oneshot" in programs else "initial"
    evo_kind = best_evo_kind(list(programs.keys()))
    print(f"    📊 Baseline: {baseline_kind}, Evolution: {evo_kind}")
    
    if not evo_kind or baseline_kind not in programs:
        print(f"    ❌ Missing baseline ({baseline_kind in programs}) or evolution ({evo_kind is not None})")
        return []

    results = []
    unique_claims = sorted({cid for (_, cid) in queries})
    print(f"    🎯 Processing claims: {unique_claims}")
    
    for cid in unique_claims:
        q_b = queries.get((baseline_kind, cid))
        q_e = queries.get((evo_kind, cid))
        print(f"      Claim {cid}: baseline={q_b is not None}, evolved={q_e is not None}")
        
        if not (q_b and q_e):
            print(f"      ⚠️  Skipping claim {cid} - missing queries")
            continue
            
        print(f"        Baseline query: {q_b[:50]}...")
        print(f"        Evolution query: {q_e[:50]}...")
        
        b = eval_pair(programs[baseline_kind], q_b)
        e = eval_pair(programs[evo_kind], q_e)
        print(f"        Results: {b} -> {e}")
        
        delta = ("Same" if b == e else
                 "Improved"  if b == "ERROR" and e != "ERROR" else
                 "Regressed" if b != "ERROR" and e == "ERROR" else
                 "Changed")
        results.append(Result(policy, cid, b, e, delta))
        print(f"        Delta: {delta}")
    
    print(f"    📈 Total results: {len(results)}")
    return results

def main() -> None:
    print("🏁 Starting benchmark analysis...")
    all_results: List[Result] = []

    for policy_dir in sorted(ROOT.glob("policy_*")):
        policy = policy_dir.name
        print(f"\n🔍 Processing {policy}")
        
        # Find oneshot run and best evolution run separately
        oneshot_data = {}  # {claim_id: (program_path, query)}
        evolution_data = {}  # {claim_id: (program_path, query)}
        initial_data = {}  # {claim_id: (program_path, query)}
        
        for run_root in policy_dir.glob("*/run_*"):
            summary = run_root / "summary.txt"
            sol_id = parse_summary(summary)
            if not sol_id:
                continue
                
            programs = load_programs(run_root, sol_id)
            queries = load_queries(run_root)
            
            print(f"  📂 Processing {run_root.name}")
            print(f"    🔍 Solution ID: {sol_id}")
            print(f"    💾 Programs: {list(programs.keys())}")
            print(f"    🔍 Queries: {list(queries.keys())}")
            
            # Collect all types of queries
            for (kind, cid), query in queries.items():
                if kind == "oneshot" and "oneshot" in programs:
                    oneshot_data[cid] = (programs["oneshot"], query)
                    print(f"    📊 Found oneshot for claim {cid}")
                elif kind == "initial" and "initial" in programs:
                    initial_data[cid] = (programs["initial"], query)
                    print(f"    📊 Found initial for claim {cid}")
                elif EVO_RE.match(kind) and kind in programs:
                    evolution_data[cid] = (programs[kind], query)
                    print(f"    🧬 Found evolution ({kind}) for claim {cid}")
        
        print(f"  📊 Oneshot claims: {sorted(oneshot_data.keys())}")
        print(f"  📊 Initial claims: {sorted(initial_data.keys())}")
        print(f"  🧬 Evolution claims: {sorted(evolution_data.keys())}")
        
        # For each claim, find the best comparison:
        # Priority: oneshot vs evolution > oneshot vs initial > initial vs evolution
        all_claims = set(oneshot_data.keys()) | set(initial_data.keys()) | set(evolution_data.keys())
        
        for cid in sorted(all_claims):
            baseline_data = None
            evolved_data = None
            comparison_type = None
            
            # Priority 1: oneshot vs evolution
            if cid in oneshot_data and cid in evolution_data:
                baseline_data = oneshot_data[cid]
                evolved_data = evolution_data[cid]
                comparison_type = "oneshot vs evolution"
            # Priority 2: oneshot vs initial (baseline comparison)
            elif cid in oneshot_data and cid in initial_data:
                baseline_data = oneshot_data[cid]
                evolved_data = initial_data[cid]
                comparison_type = "oneshot vs initial"
            # Priority 3: initial vs evolution
            elif cid in initial_data and cid in evolution_data:
                baseline_data = initial_data[cid]
                evolved_data = evolution_data[cid]
                comparison_type = "initial vs evolution"
            
            if baseline_data and evolved_data:
                prog_b, q_b = baseline_data
                prog_e, q_e = evolved_data
                print(f"  🎯 Claim {cid} ({comparison_type}): {prog_b.name} vs {prog_e.name}")
                
                b_stat = eval_pair(prog_b, q_b)
                e_stat = eval_pair(prog_e, q_e)
                delta = ("Same" if b_stat == e_stat else
                        "Improved" if b_stat == "ERROR" and e_stat != "ERROR" else
                        "Regressed" if b_stat != "ERROR" and e_stat == "ERROR" else
                        "Changed")
                all_results.append(Result(policy, cid, b_stat, e_stat, delta))
                print(f"    Results: {b_stat} -> {e_stat} ({delta})")

    print(f"\n📊 Total results collected: {len(all_results)}")
    
    if not all_results:
        print("No comparable data found.")
        return

    csv_path = pathlib.Path("benchmark_results.csv")
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(Result._fields)
        for row in all_results:
            w.writerow(row)

    by_delta = collections.Counter(r.delta for r in all_results)
    print("\nSummary across all policies & claims")
    for k, v in by_delta.items():
        print(f"{k:9}: {v}")
    print(f"\nDetailed results written to {csv_path.resolve()}")
    
if __name__ == "__main__":
    main()