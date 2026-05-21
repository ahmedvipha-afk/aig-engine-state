"""MBV — Market Bias + Range + Volume (long only).

FROZEN rules (pre-registered 2026-05-21 in config.py).

Long-only mean-reversion-inside-bullish-trend. Three independent filters:
  1. Market Bias (trend) — close > EMA(MBV_TREND_EMA). Long signal only
     when the broader uptrend is intact.
  2. Range (position) — close sits in the lower third of the trailing
     N-bar range. Buying weakness within strength.
  3. Volume confirmation — entry-bar volume ≥ 1.2 × SMA(20) of volume.

Range is computed with `shift(1)` so the current bar's high/low never
leaks into the range used to evaluate it — look-ahead-free.

Exit when price reaches mid-range (mean reversion completed) OR trend
breaks (close drops below EMA-200). Hard stop at entry − stop_atr × ATR.

No per-ticker tuning. Deterministic.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from config import (MBV_TREND_EMA, MBV_RANGE_BARS, MBV_RANGE_FLOOR,
                    MBV_RANGE_MID, MBV_VOLUME_PERIOD, MBV_VOLUME_MULT,
                    MBV_STOP_ATR_MULT, ATR_PERIOD)


def _ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def _atr(df: pd.DataFrame, n: int) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat([(h - l), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def signals(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["ema"] = _ema(out["close"], MBV_TREND_EMA)
    out["atr"] = _atr(out, ATR_PERIOD)

    # Range over the trailing MBV_RANGE_BARS, shifted by 1 to avoid the
    # current bar's own high/low contaminating its range position.
    high_n = out["high"].rolling(MBV_RANGE_BARS).max().shift(1)
    low_n  = out["low"].rolling(MBV_RANGE_BARS).min().shift(1)
    rng = (high_n - low_n).replace(0, np.nan)
    out["range_pct"] = (out["close"] - low_n) / rng

    # Volume confirmation
    out["vol_sma"] = out["volume"].rolling(MBV_VOLUME_PERIOD).mean()
    out["vol_ok"] = out["volume"] >= MBV_VOLUME_MULT * out["vol_sma"]

    # Composite entry: bullish bias + lower-third range + volume confirm.
    # Edge-trigger so we only enter on the bar the conditions first align.
    trend_ok = out["close"] > out["ema"]
    in_floor = out["range_pct"] <= MBV_RANGE_FLOOR
    in_floor_prev = out["range_pct"].shift(1) <= MBV_RANGE_FLOOR
    edge = in_floor & ~in_floor_prev.fillna(False)
    out["entry"] = trend_ok & edge & out["vol_ok"].fillna(False)

    # Exit when range_pct reaches the mid-range OR trend breaks.
    out["exit_signal"] = (out["range_pct"] >= MBV_RANGE_MID) | (out["close"] < out["ema"])

    return out
