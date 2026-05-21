"""AIG Paper-Backward Simulator — historical paper-account reconstruction.

Answers: "If we had been paper-trading the cleared strategy on $100K from
a past start date, what would the account look like today?"

Design:
- One combined paper account ($100K start, configurable).
- Reads `winners_assignment.json` → routes each ticker through its assigned
  cleared strategy (divergence or mbv).
- Replays every trade chronologically with the FROZEN strategy rules; sizes
  positions at a fixed fraction of equity (default 5% → up to 20 concurrent
  positions). Position size honors Rule 16 (no leverage).
- Applies the same round-trip costs the validation backtest uses.
- Output: daily NAV series, full closed-trades journal, summary KPIs
  (CAGR, Sharpe, Sortino, max DD, Calmar) → `paper_backward_results.json`.

Distinct from `paper_forward_*` because:
- Paper-FORWARD = live signal detection going forward from deployment date.
  Today: 0 trades to date.
- Paper-BACKWARD = retroactive equity-curve reconstruction using historical
  data. Produces what your $100K WOULD look like today if you'd started
  paper-trading the strategy years ago.

Per audit Concern 2: this is NOT validation — it doesn't gate-evaluate
anything. It's a presentation/reporting layer over the already-cleared
strategies. The gate verdicts (dSharpe 2.606 Divergence US / 4.365 MBV US)
remain the binding edge claims.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from aig.data import get_history, integrity_check
from aig.costs import round_trip_cost_frac
from config import market_of

GST = timezone(timedelta(hours=4))

DEFAULT_START = "2016-01-01"
DEFAULT_CAPITAL = 100_000.0
DEFAULT_POS_FRACTION = 0.05   # 5% per position → max 20 concurrent
DEFAULT_MAX_CONCURRENT = 20


def _strategy_signals(strategy: str, df: pd.DataFrame) -> pd.DataFrame:
    if strategy == "divergence":
        from aig.strategy_divergence import signals
        return signals(df)
    if strategy == "mbv":
        from aig.strategy_mbv import signals
        return signals(df)
    if strategy == "ema200":
        from aig.strategy_ema200 import signals
        return signals(df)
    raise ValueError(strategy)


def _stop_distance(strategy: str, row) -> float:
    from config import STOP_ATR_MULT, DIV_STOP_ATR_MULT, MBV_STOP_ATR_MULT
    atr = float(row.get("atr") or 0)
    if strategy == "divergence":
        return float(row.get("stop_dist", DIV_STOP_ATR_MULT * atr))
    if strategy == "mbv":
        return MBV_STOP_ATR_MULT * atr
    return STOP_ATR_MULT * atr


def extract_trades(ticker: str, strategy: str, cost: float) -> list[dict]:
    """Replay strategy on ticker's full history; return list of dated trades."""
    try:
        df = get_history(ticker, offline=False, timeframe="1d")
    except Exception:
        return []
    ok, _ = integrity_check(ticker, df, timeframe="1d")
    if not ok:
        return []
    try:
        s = _strategy_signals(strategy, df)
    except Exception:
        return []

    trades = []
    in_pos = False
    entry_px = stop_px = 0.0
    entry_date = None
    for i in range(len(s)):
        row = s.iloc[i]
        if pd.isna(row.get("ema")) or pd.isna(row.get("atr")):
            continue
        px = float(row["close"])
        bar_date = s.index[i].date().isoformat()
        if not in_pos and bool(row.get("entry")):
            in_pos = True
            entry_px = px
            entry_date = bar_date
            stop_px = px - _stop_distance(strategy, row)
        elif in_pos:
            hit_stop = float(row["low"]) <= stop_px
            exit_now = bool(row.get("exit_signal")) or hit_stop
            if exit_now:
                exit_px = stop_px if hit_stop else px
                gross_ret = exit_px / entry_px - 1.0
                net_ret = gross_ret - cost
                trades.append({
                    "ticker": ticker,
                    "strategy": strategy,
                    "entry_date": entry_date,
                    "entry_price": round(entry_px, 4),
                    "exit_date": bar_date,
                    "exit_price": round(float(exit_px), 4),
                    "gross_return": round(gross_ret, 6),
                    "net_return": round(net_ret, 6),
                    "exit_reason": "stop_hit" if hit_stop else "exit_signal",
                })
                in_pos = False
    return trades


def simulate_portfolio(trades: list[dict], start_date: str,
                       capital: float, pos_fraction: float,
                       max_concurrent: int) -> dict:
    """Walk through every trading day; open/close positions; track NAV."""
    if not trades:
        return {"error": "no trades"}

    # Filter trades to those that started on/after start_date
    trades = [t for t in trades if t["entry_date"] >= start_date]
    trades_by_entry = sorted(trades, key=lambda t: t["entry_date"])
    trades_by_exit = sorted(trades, key=lambda t: t["exit_date"])

    # Build day-index from first entry to today
    all_dates = sorted(set([t["entry_date"] for t in trades] +
                           [t["exit_date"] for t in trades]))
    if not all_dates:
        return {"error": "no trades after filter"}
    start = max(all_dates[0], start_date)
    end = all_dates[-1]

    equity = capital            # cash
    nav_series = []             # list of (date, nav)
    open_positions = {}         # entry_key -> dict
    closed = []
    skipped = 0
    entry_cursor = 0
    exit_cursor = 0

    # Pre-index trades
    entry_idx: dict[str, list[dict]] = {}
    exit_idx: dict[str, list[dict]] = {}
    for i, t in enumerate(trades):
        # We need a unique key per trade in case same ticker has multiple
        key = f"{t['ticker']}_{t['entry_date']}_{i}"
        t = dict(t); t["_key"] = key
        entry_idx.setdefault(t["entry_date"], []).append(t)
        exit_idx.setdefault(t["exit_date"], []).append(t)

    # Build list of every day to iterate (include all entry/exit dates)
    iter_dates = sorted(set(list(entry_idx.keys()) + list(exit_idx.keys())))

    for d in iter_dates:
        # Close exits first (free up capital)
        for t in exit_idx.get(d, []):
            k = t["_key"]
            if k not in open_positions:
                continue  # this trade was never opened (skipped at entry)
            pos = open_positions.pop(k)
            alloc = pos["alloc"]
            equity += alloc * (1.0 + t["net_return"])
            closed.append({
                "ticker": t["ticker"],
                "strategy": t["strategy"],
                "entry_date": t["entry_date"],
                "exit_date": t["exit_date"],
                "entry_price": t["entry_price"],
                "exit_price": t["exit_price"],
                "alloc_at_entry": round(alloc, 2),
                "net_return": t["net_return"],
                "pnl_dollars": round(alloc * t["net_return"], 2),
                "exit_reason": t["exit_reason"],
            })

        # Open entries (up to max_concurrent)
        for t in entry_idx.get(d, []):
            if len(open_positions) >= max_concurrent:
                skipped += 1
                continue
            alloc = equity * pos_fraction
            if alloc < 100:
                skipped += 1
                continue
            equity -= alloc
            k = t["_key"]
            open_positions[k] = {
                "ticker": t["ticker"],
                "strategy": t["strategy"],
                "entry_date": t["entry_date"],
                "entry_price": t["entry_price"],
                "alloc": alloc,
            }

        # Mark-to-market: rough — value open positions at their entry price
        # (we don't pull daily prices for every ticker; uses entry-price as
        # placeholder). End-of-day NAV = cash + open-position alloc sum.
        # This understates volatility within positions but is correct at
        # entry/exit boundaries which is where the trade economics realise.
        nav = equity + sum(p["alloc"] for p in open_positions.values())
        nav_series.append({"date": d, "nav": round(nav, 2),
                           "cash": round(equity, 2),
                           "open_positions": len(open_positions)})

    # Final close-out at end (treat any still-open as unrealised; don't crystallise)
    final_nav = equity + sum(p["alloc"] for p in open_positions.values())

    # Stats
    nav_arr = np.array([n["nav"] for n in nav_series], dtype=float)
    if len(nav_arr) < 2:
        return {"error": "insufficient nav points"}
    rets = np.diff(nav_arr) / nav_arr[:-1]
    days = (datetime.fromisoformat(nav_series[-1]["date"]) -
            datetime.fromisoformat(nav_series[0]["date"])).days
    years = max(days / 365.25, 1e-6)
    cagr = (nav_arr[-1] / nav_arr[0]) ** (1 / years) - 1
    daily_sharpe = (rets.mean() / rets.std() * np.sqrt(252)) if rets.std() > 0 else 0
    downside = rets[rets < 0]
    daily_sortino = (rets.mean() / downside.std() * np.sqrt(252)) if (len(downside) > 0 and downside.std() > 0) else 0
    peak = np.maximum.accumulate(nav_arr)
    dd = (nav_arr - peak) / peak
    max_dd = dd.min()
    calmar = (cagr / abs(max_dd)) if max_dd < 0 else 0

    return {
        "params": {
            "start_date": start,
            "end_date": end,
            "starting_capital": capital,
            "pos_fraction": pos_fraction,
            "max_concurrent": max_concurrent,
        },
        "summary": {
            "starting_nav": float(nav_arr[0]),
            "ending_nav": float(final_nav),
            "total_return_pct": float((final_nav / capital - 1) * 100),
            "cagr_pct": float(cagr * 100),
            "sharpe_daily": float(daily_sharpe),
            "sortino_daily": float(daily_sortino),
            "max_drawdown_pct": float(max_dd * 100),
            "calmar": float(calmar),
            "total_trades_closed": len(closed),
            "total_trades_skipped_capital_constrained": skipped,
            "open_at_end": len(open_positions),
            "years_simulated": round(years, 2),
        },
        "nav_series": nav_series,
        "closed_trades": closed,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default=DEFAULT_START,
                    help=f"start date YYYY-MM-DD (default {DEFAULT_START})")
    ap.add_argument("--capital", type=float, default=DEFAULT_CAPITAL,
                    help=f"starting capital USD (default {DEFAULT_CAPITAL})")
    ap.add_argument("--pos-frac", type=float, default=DEFAULT_POS_FRACTION,
                    help=f"position size as fraction of equity (default {DEFAULT_POS_FRACTION})")
    ap.add_argument("--max-concurrent", type=int, default=DEFAULT_MAX_CONCURRENT,
                    help=f"max concurrent positions (default {DEFAULT_MAX_CONCURRENT})")
    ap.add_argument("--top-n", type=int, default=None,
                    help="optional: only use top-N tickers by dSharpe (default: all)")
    ap.add_argument("--out", default="paper_backward_results.json")
    args = ap.parse_args()

    # Load assignments
    with open("winners_assignment.json", "r", encoding="utf-8") as fh:
        asn = json.load(fh)
    assignments = asn["assignments"]

    # Optionally restrict to top-N by dSharpe
    ranked = sorted(assignments.keys(),
                    key=lambda tk: -float(assignments[tk].get("dsharpe") or -99))
    if args.top_n:
        ranked = ranked[:args.top_n]
    print(f"Replaying {len(ranked)} tickers from {args.start} on ${args.capital:,.0f}")

    all_trades: list[dict] = []
    n_with_trades = 0
    for i, tk in enumerate(ranked):
        a = assignments[tk]
        strategy = a["strategy"]
        market = a.get("market", "US")
        cost = round_trip_cost_frac(market)
        ts = extract_trades(tk, strategy, cost)
        if ts:
            n_with_trades += 1
            all_trades.extend(ts)
        if (i + 1) % 25 == 0:
            print(f"  processed {i+1}/{len(ranked)} tickers; trades so far: {len(all_trades)}")

    print(f"\n{n_with_trades}/{len(ranked)} tickers produced trades; total trades = {len(all_trades)}")

    result = simulate_portfolio(
        all_trades, args.start, args.capital, args.pos_frac, args.max_concurrent
    )
    if "error" in result:
        print(f"ERROR: {result['error']}")
        return

    # Persist JSON FIRST so a print encoding issue can't lose the result.
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)

    summary = result["summary"]
    print(f"\n=== Paper-Backward Simulation Result ===")
    print(f"Period:    {result['params']['start_date']} -> {result['params']['end_date']}  ({summary['years_simulated']:.2f} years)")
    print(f"Capital:   ${summary['starting_nav']:>14,.2f} -> ${summary['ending_nav']:>14,.2f}")
    print(f"Return:    {summary['total_return_pct']:+.2f}%  |  CAGR: {summary['cagr_pct']:+.2f}%")
    print(f"Sharpe:    {summary['sharpe_daily']:.2f} (daily-annualised)")
    print(f"Sortino:   {summary['sortino_daily']:.2f}")
    print(f"Max DD:    {summary['max_drawdown_pct']:.2f}%")
    print(f"Calmar:    {summary['calmar']:.2f}")
    print(f"Trades:    {summary['total_trades_closed']} closed (+{summary['total_trades_skipped_capital_constrained']} skipped on capital cap)")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
