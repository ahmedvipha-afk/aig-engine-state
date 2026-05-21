"""ROC — Rate-of-Change Momentum (long only).

FROZEN rules (pre-registered 2026-05-21 Fire 1.5 in config.py).

Long-only velocity-based momentum strategy. Buys when:
  1. ROC(20) > 5% (strong positive momentum over the lookback window).
  2. ROC(20) is rising vs yesterday's ROC (acceleration, not deceleration).
  3. close > SMA(50) (bullish regime confirmed).

Methodologically distinct from the four prior strategies:
- EMA-200 (trend-confirm): position-based — close > long EMA.
- Divergence (mean-rev-on-low): RSI hookup at lows.
- MBV (mean-rev-in-uptrend): low-range pullback inside trend.
- DBO (breakout): close crosses a level (Donchian high).
- ROC (velocity-momentum): captures HOW FAST price is moving, not where it stands.

Two stocks at the same EMA distance can have very different ROC; ROC sees
the regime-state difference that pure level-crossing misses.

Exit:
  - ROC(20) < 0  (momentum has reversed)
  - close < SMA(50)  (regime broke)
  - ATR stop hit (entry - 2.0 x ATR(14))

Edge-triggered entry: must be the FIRST bar where all three entry conditions
hold (prevents continuous re-entry during sustained momentum runs).

No per-ticker tuning. Deterministic.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from config import (ROC_PERIOD, ROC_THRESHOLD, ROC_TREND_SMA,
                    ROC_STOP_ATR_MULT, ATR_PERIOD)


def _atr(df: pd.DataFrame, n: int) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat([(h - l), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def signals(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # Rate of change over ROC_PERIOD bars.
    out["roc"] = out["close"] / out["close"].shift(ROC_PERIOD) - 1.0

    # SMA(50) trend filter.
    out["sma"] = out["close"].rolling(ROC_TREND_SMA).mean()

    # ATR for stop and engine's _stop_distance dispatcher.
    out["atr"] = _atr(out, ATR_PERIOD)

    # EMA sentinel column required by the engine's _simulate (it skips bars
    # where ema/atr are NaN). Using SMA(50) as the not-NaN sentinel — this
    # does NOT gate entries (those use roc + sma); SMA is already computed.
    out["ema"] = out["sma"]

    # Entry conditions (all three must hold):
    threshold_ok = out["roc"] > ROC_THRESHOLD
    rising = out["roc"] > out["roc"].shift(1)
    trend_ok = out["close"] > out["sma"]
    all_three = threshold_ok & rising & trend_ok

    # Edge-trigger: yesterday at least one was false → today first time all hold.
    all_three_prev = all_three.shift(1).fillna(False)
    out["entry"] = all_three & ~all_three_prev

    # Exit conditions: ROC turns negative OR regime breaks.
    out["exit_signal"] = (out["roc"] < 0) | (out["close"] < out["sma"])

    return out
