"""Pre-push check: no big files, no lender identifiers in CSV headers."""
import subprocess, sys
from pathlib import Path
import pandas as pd

LIMIT = 50 * 1024 ** 2                       # GitHub warns at 50 MB, rejects at 100 MB
BAD_COLS = {"lei", "lender_code"}            # Decision D-O

files = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                       capture_output=True, text=True, check=True).stdout.splitlines()
problems = []
for f in files:
    p = Path(f)
    if p.exists() and p.stat().st_size > LIMIT:
        problems.append(f"BIG ({p.stat().st_size / 1024**2:,.1f} MB): {f}")
    if p.suffix.lower() == ".csv" and p.exists():
        cols = {c.lower() for c in pd.read_csv(p, nrows=0).columns}
        if cols & BAD_COLS:
            problems.append(f"LENDER ID COLUMN {sorted(cols & BAD_COLS)}: {f}")
print("\n".join(problems) or "OK: no big files, no lender identifiers in CSV headers")
sys.exit(1 if problems else 0)