"""Probe each UAE ticker against yfinance with multiple suffix variants.
Writes a corrected universe file with the working suffix, and logs which
tickers have NO yfinance coverage at all (need an alternate data source).
"""
from __future__ import annotations
import os
import sys
import yfinance as yf

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(THIS_DIR, "uae_stocks.xlsx")

# Read original ticker list from the staged uae_tickers.txt (HALAL active section)
ACTIVE = []
with open(os.path.join(THIS_DIR, "uae_tickers.txt"), "r", encoding="utf-8") as fh:
    for line in fh:
        t = line.strip()
        if not t or t.startswith("#"):
            continue
        ACTIVE.append(t)


def try_yf(symbol: str) -> int:
    try:
        d = yf.download(symbol, period="1y", interval="1d",
                        auto_adjust=True, progress=False, threads=False)
        if d is None:
            return 0
        if hasattr(d.columns, "levels"):
            d.columns = [c[0] for c in d.columns]
        return len(d)
    except Exception:
        return -1


# Suffix variants: AE (Abu Dhabi extended), AD (alt), DU (DFM), DFM
SUFFIXES = [".AE", ".AD", ".DU", ".DFM", ".AB"]


def probe(ticker: str) -> dict:
    # ticker has suffix like ADIB.AD — strip and retry with alternatives
    base = ticker
    for s in SUFFIXES:
        if base.endswith(s):
            base = base[:-len(s)]
            break
    best = None
    for s in SUFFIXES:
        candidate = base + s
        n = try_yf(candidate)
        if n > 100:
            best = (candidate, n)
            break  # first hit wins
    return {"original": ticker, "base": base, "best": best}


print(f"Probing {len(ACTIVE)} UAE tickers across yfinance suffix variants...")
results = []
working = []
broken = []
for t in ACTIVE:
    r = probe(t)
    if r["best"]:
        working.append(r["best"][0])
        print(f"  OK  {t:<14} -> {r['best'][0]:<14} rows={r['best'][1]}")
    else:
        broken.append(t)
        print(f"  BAD {t:<14} (no suffix variant found data)")

print(f"\nWorking: {len(working)}/{len(ACTIVE)}  |  No data: {len(broken)}")
out = os.path.join(THIS_DIR, "uae_tickers_yf.txt")
with open(out, "w", encoding="utf-8") as fh:
    fh.write("# UAE tickers that work via yfinance (CEO probe 2026-05-20)\n")
    fh.write(f"# {len(working)} confirmed-working, {len(broken)} without yfinance coverage\n")
    fh.write("# To re-test or add new: re-run universe/probe_uae_yfinance.py\n\n")
    for t in working:
        fh.write(t + "\n")
    fh.write("\n# --- No yfinance coverage (need alternate data source: TV MCP, etc.) ---\n")
    for t in broken:
        fh.write("# " + t + "\n")
print(f"Wrote {out}")
