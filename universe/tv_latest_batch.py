"""Process the N most recent TV data_get_ohlcv-*.txt files, mapping them
in mtime-ascending order to a list of tickers (comma-separated).

Usage:
    python universe/tv_latest_batch.py <ticker1,ticker2,...>

Example after 5 sequential fetches:
    python universe/tv_latest_batch.py ADNOCDIST.AD,ADNOCDRILL.AD,ADNOCGAS.AD,ADNOCLS.AD,ADPORTS.AD
"""
from __future__ import annotations
import os
import sys
import subprocess
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
HOME = Path(os.path.expanduser("~"))
PROJECTS = HOME / ".claude" / "projects"
TO_CSV = THIS_DIR / "tv_bars_to_csv.py"

if len(sys.argv) < 2:
    print("usage: tv_latest_batch.py <ticker1,ticker2,...>", file=sys.stderr)
    sys.exit(2)

tickers = [t.strip() for t in sys.argv[1].split(",") if t.strip()]
n = len(tickers)
if n == 0:
    sys.exit(2)

candidates: list[tuple[float, Path]] = []
for tr in PROJECTS.glob("*/*/tool-results"):
    for f in tr.glob("mcp-tradingview-data_get_ohlcv-*.txt"):
        candidates.append((f.stat().st_mtime, f))
if len(candidates) < n:
    print(f"FAIL: only {len(candidates)} TV bar files; need {n}", file=sys.stderr)
    sys.exit(3)

# newest N (sorted ascending so order matches the order of fetches)
candidates.sort(key=lambda x: -x[0])
selected = candidates[:n]
selected.sort(key=lambda x: x[0])    # mtime ascending — matches fetch order

print(f"Mapping {n} files -> {n} tickers (mtime ascending == fetch order):")
for (mt, f), tk in zip(selected, tickers):
    r = subprocess.run(
        [sys.executable, str(TO_CSV), str(f), tk],
        capture_output=True, text=True
    )
    print(r.stdout.strip())
    if r.returncode != 0:
        print(f"  ERROR on {tk}: rc={r.returncode} stderr={r.stderr}", file=sys.stderr)
