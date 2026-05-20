"""Convert a single TV data_get_ohlcv-*.txt MCP-saved JSON file -> data_cache CSV.

Usage:
    python universe/tv_bars_to_csv.py <input_json_path> <output_ticker_symbol>

Example:
    python universe/tv_bars_to_csv.py "C:\\Users\\...\\mcp-tradingview-data_get_ohlcv-1779300971136.txt" ADIB.AD

Writes CSV to data_cache/<ticker>.csv with columns:
    date, open, high, low, close, volume
"""
from __future__ import annotations
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
CACHE_DIR = THIS_DIR.parent / "data_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def parse_tv_file(path: Path) -> list[dict]:
    """The MCP tool writes a JSON array of {type,text} entries. The OHLCV
    payload lives inside the 'text' field of the entry whose type=='text'."""
    raw = path.read_text(encoding="utf-8")
    try:
        outer = json.loads(raw)
    except json.JSONDecodeError:
        # not the outer wrapper; maybe direct JSON
        return json.loads(raw).get("bars") or json.loads(raw).get("last_5_bars") or []
    if not isinstance(outer, list):
        outer = [outer]
    bars: list[dict] = []
    for item in outer:
        text = item.get("text") if isinstance(item, dict) else None
        if not text:
            continue
        try:
            payload = json.loads(text)
        except Exception:
            continue
        candidates = payload.get("bars") or payload.get("last_5_bars") or []
        if candidates:
            bars.extend(candidates)
        # Newer schema: full bar list directly under 'bars'
        if not bars and isinstance(payload.get("ohlcv"), list):
            bars.extend(payload["ohlcv"])
    return bars


def main():
    if len(sys.argv) < 3:
        print("usage: tv_bars_to_csv.py <input_path> <output_ticker>", file=sys.stderr)
        sys.exit(2)
    src = Path(sys.argv[1])
    ticker = sys.argv[2]
    if not src.exists():
        print(f"NOT FOUND: {src}", file=sys.stderr)
        sys.exit(3)
    bars = parse_tv_file(src)
    if not bars:
        print(f"WARN: no bars parsed from {src}")
        sys.exit(4)
    bars.sort(key=lambda b: b.get("time") or 0)
    out_path = CACHE_DIR / f"{ticker}.csv"
    with out_path.open("w", encoding="utf-8") as fh:
        fh.write("date,open,high,low,close,volume\n")
        for b in bars:
            t = b.get("time")
            if not t:
                continue
            dt = datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d")
            fh.write(f"{dt},{b['open']},{b['high']},{b['low']},{b['close']},{b.get('volume', 0)}\n")
    print(f"WROTE {out_path}  bars={len(bars)}  start={datetime.fromtimestamp(bars[0]['time'], tz=timezone.utc).date()}  end={datetime.fromtimestamp(bars[-1]['time'], tz=timezone.utc).date()}")


if __name__ == "__main__":
    main()
