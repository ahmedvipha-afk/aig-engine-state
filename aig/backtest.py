"""
LAYER 2 — Backtest engine.

Simulates a frozen strategy on one ticker, after realistic costs. Produces
per-trade returns split into in-sample and out-of-sample, plus a walk-forward
pass over rolling folds of the full history. Also estimates observed
trades-per-year from the OOS sample for honest Sharpe annualisation.

No optimisation. The engine measures; it does not fit.

CEO v7.0 amendment (2026-05-20): strategy is now selectable (EMA-200 default,
Divergence available). bars_per_year for the chosen timeframe is recorded so
the gate can pass it to sharpe() — was previously hard-coded to 25.
"""

from __future__ import annotations
import numpy as np
import pandas as pd

from config import GATE, BARS_PER_YEAR, market_of
from aig.costs import round_trip_cost_frac


def _strategy_signals(name: str, df: pd.DataFrame) -> pd.DataFrame:
    if name == "ema200":
        from aig.strategy_ema200 import signals
        return signals(df)
    if name == "divergence":
        from aig.strategy_divergence import signals
        return signals(df)
    if name == "mbv":
        from aig.strategy_mbv import signals
        return signals(df)
    if name == "dbo":
        from aig.strategy_dbo import signals
        return signals(df)
    if name == "roc":
        from aig.strategy_roc import signals
        return signals(df)
    raise ValueError(f"unknown strategy: {name}")


def _stop_distance(name: str, row) -> float:
    if name == "ema200":
        from config import STOP_ATR_MULT
        return STOP_ATR_MULT * row["atr"]
    if name == "divergence":
        from config import DIV_STOP_ATR_MULT
        # Divergence stop is (entry - swing_low_buffer) but the strategy fills
        # row["stop_dist"] with the precomputed distance.
        return float(row.get("stop_dist", DIV_STOP_ATR_MULT * row["atr"]))
    if name == "mbv":
        from config import MBV_STOP_ATR_MULT
        return MBV_STOP_ATR_MULT * row["atr"]
    if name == "dbo":
        from config import DBO_STOP_ATR_MULT
        return DBO_STOP_ATR_MULT * row["atr"]
    if name == "roc":
        from config import ROC_STOP_ATR_MULT
        return ROC_STOP_ATR_MULT * row["atr"]
    raise ValueError(name)


def _simulate(df: pd.DataFrame, cost: float, strategy: str) -> list[float]:
    """Return list of per-trade net returns (fraction)."""
    s = _strategy_signals(strategy, df)
    trades: list[float] = []
    in_pos = False
    entry_px = stop_px = 0.0
    for i in range(len(s)):
        row = s.iloc[i]
        if np.isnan(row.get("ema", np.nan)) or np.isnan(row.get("atr", np.nan)):
            continue
        px = row["close"]
        if not in_pos and bool(row["entry"]):
            in_pos = True
            entry_px = px
            stop_px = px - _stop_distance(strategy, row)
        elif in_pos:
            hit_stop = row["low"] <= stop_px
            exit_now = bool(row["exit_signal"]) or hit_stop
            if exit_now:
                exit_px = stop_px if hit_stop else px
                gross = exit_px / entry_px - 1.0
                trades.append(gross - cost)   # net of round-trip cost
                in_pos = False
    return trades


def split_backtest(ticker: str, df: pd.DataFrame,
                   timeframe: str = "1d",
                   strategy: str = "ema200") -> dict:
    mkt = market_of(ticker)
    cost = round_trip_cost_frac(mkt)
    n = len(df)
    cut = int(n * GATE["train_frac"])
    is_tr = _simulate(df.iloc[:cut], cost, strategy)
    is_oos = _simulate(df.iloc[cut:], cost, strategy)

    # walk-forward: rolling folds across full history, collect OOS-style returns
    wf: list[float] = []
    folds = GATE["wf_folds"]
    step = n // (folds + 1)
    for k in range(1, folds + 1):
        seg = df.iloc[k * step:(k + 2) * step]
        if len(seg) > 250:
            wf += _simulate(seg, cost, strategy)

    # honest annualisation: OOS span in years × observed trade frequency.
    bpy = BARS_PER_YEAR.get(timeframe, 252)
    oos_bars = max(n - cut, 1)
    oos_years = oos_bars / bpy
    trades_per_year = len(is_oos) / oos_years if oos_years > 0 else 0.0

    return {"ticker": ticker, "market": mkt, "cost_frac": cost,
            "timeframe": timeframe, "strategy": strategy,
            "is_trades": is_tr, "oos_trades": is_oos, "wf_trades": wf,
            "oos_trades_per_year": round(trades_per_year, 2)}
