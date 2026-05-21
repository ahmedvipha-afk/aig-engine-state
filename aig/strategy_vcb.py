"""VCB — Volatility Compression Breakout (long only).

FROZEN rules (pre-registered 2026-05-21 Fire 2 in config.py).

Long-only volatility-cycle strategy. Buys when realized volatility
(ATR) has compressed to a 20-day low AND the broader regime is bullish
AND today's bar shows a directional pickup. Captures the
"compression precedes expansion" regime cycle.

Methodologically distinct from the five prior strategies:
- EMA-200 (trend-confirm): position-based — close > long EMA.
- Divergence (mean-rev-on-low): RSI hookup at lows.
- MBV (mean-rev-in-uptrend): low-range pullback inside trend.
- DBO (breakout): close crosses a level (Donchian high).
- ROC (velocity-momentum): rate of price change.
- VCB (vol-cycle): VOLATILITY is the primary input. Two stocks at
  the same EMA distance / momentum / Donchian level can have very
  different ATR profiles; VCB sees the regime-state difference that
  pure price-based strategies miss.

Hypothesis: volatility cycles. Compression-bottoms are followed by
expansion. Restricting to bullish regimes (close > SMA(50)) makes the
expected expansion-direction long. Pre-registered BEFORE any data was
seen per audit Concern 2.

Entry (all three must hold on the entry bar):
  1. ATR(14)[today] == min(ATR(14)) over the trailing VCB_ATR_LOOKBACK
     bars — volatility is at a local low.
  2. close > SMA(VCB_TREND_SMA=50) — bullish regime intact.
  3. close > yesterday's close — directional pickup confirmation.

Edge-triggered entry: yesterday at least one entry condition was false
(prevents continuous re-entry during prolonged low-vol regimes).

Exit:
  - ATR(14) > VCB_EXPANSION_MULT * mean(ATR over VCB_ATR_LOOKBACK) —
    compression has released into expansion (mission accomplished).
  - close < SMA(VCB_TREND_SMA) — regime broke.
  - ATR stop hit (entry - VCB_STOP_ATR_MULT * ATR(14)).

No per-ticker tuning. Deterministic. Long-only (Rule 15).
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from config import (VCB_ATR_LOOKBACK, VCB_TREND_SMA,
                    VCB_EXPANSION_MULT, VCB_STOP_ATR_MULT, ATR_PERIOD)


def _atr(df: pd.DataFrame, n: int) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat([(h - l), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def signals(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # ATR(14) — primary input (volatility).
    out["atr"] = _atr(out, ATR_PERIOD)

    # Trailing minimum and mean of ATR over the lookback window.
    out["atr_min_lookback"] = out["atr"].rolling(VCB_ATR_LOOKBACK).min()
    out["atr_mean_lookback"] = out["atr"].rolling(VCB_ATR_LOOKBACK).mean()

    # SMA(50) trend filter.
    out["sma"] = out["close"].rolling(VCB_TREND_SMA).mean()

    # EMA sentinel column required by the engine's _simulate (skips bars
    # where ema/atr are NaN). Use SMA(50) here — does NOT gate entries.
    out["ema"] = out["sma"]

    # Entry conditions:
    compression = out["atr"] <= out["atr_min_lookback"]
    trend_ok = out["close"] > out["sma"]
    bullish_bar = out["close"] > out["close"].shift(1)
    all_three = compression & trend_ok & bullish_bar

    # Edge-trigger: yesterday at least one was false → today first time all hold.
    all_three_prev = all_three.shift(1).fillna(False)
    out["entry"] = all_three & ~all_three_prev

    # Exit: vol expansion OR regime broke.
    expansion = out["atr"] > (VCB_EXPANSION_MULT * out["atr_mean_lookback"])
    regime_broke = out["close"] < out["sma"]
    out["exit_signal"] = expansion | regime_broke

    return out
