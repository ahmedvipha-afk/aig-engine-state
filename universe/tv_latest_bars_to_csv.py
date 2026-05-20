"""Find the most recent TV data_get_ohlcv-*.txt MCP-saved file and
parse it into data_cache/<ticker>.csv.

Usage:
    python universe/tv_latest_bars_to_csv.py <ticker>

Finds the newest matching file under:
    ~/.claude/projects/*/tool-results/mcp-tradingview-data_get_ohlcv-*.txt
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
HOME = Path(os.path.expanduser("~"))
PROJECTS = HOME / ".claude" / "projects"

if len(sys.argv) < 2:
    print("usage: tv_latest_bars_to_csv.py <ticker>", file=sys.stderr)
    sys.exit(2)

ticker = sys.argv[1]

# scan all tool-results dirs for the newest matching file
candidates = []
for tr in PROJECTS.glob("*/*/tool-results"):
    for f in tr.glob("mcp-tradingview-data_get_ohlcv-*.txt"):
        candidates.append((f.stat().st_mtime, f))

if not candidates:
    print("NO TV data_get_ohlcv files found.", file=sys.stderr)
    sys.exit(3)

candidates.sort(key=lambda x: -x[0])
src = candidates[0][1]
print(f"Latest TV bars file: {src}")

# delegate to tv_bars_to_csv.py
import subprocess
result = subprocess.run(
    [sys.executable, str(THIS_DIR / "tv_bars_to_csv.py"), str(src), ticker],
    capture_output=True, text=True
)
print(result.stdout, end="")
if result.stderr:
    print("STDERR:", result.stderr, file=sys.stderr)
sys.exit(result.returncode)
