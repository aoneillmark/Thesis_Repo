import pathlib

ROOT = pathlib.Path("logs")

for policy_dir in sorted(ROOT.glob("policy_*")):
    print(f"\n=== {policy_dir.name} ===")
    for date_dir in policy_dir.iterdir():
        if not date_dir.is_dir():
            continue
        for run_root in date_dir.glob("run_*"):
            print(f"  {run_root.name}:")
            # Look for any .pl files
            for pl_file in run_root.rglob("*.pl"):
                if "claim_" in pl_file.name:
                    rel_path = pl_file.relative_to(run_root)
                    print(f"    {rel_path}")