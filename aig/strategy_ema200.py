"""
EMA-200 strategy — FROZEN rules (pre-registered in config.py).

Long-only. Enter when close has held above the EMA-200 for CONFIRM_BARS,
AND the entry bar's volume >= VOLUME_MULT * SMA(VOLUME_PERIOD).
Exit when close closes back below the EMA-200, or the ATR stop is hit.
No per-ticker tuning. Deterministic.

CEO v7.0 amendment (2026-05-20): added volume confirmation. The new rule is
applied on the entry bar only; held/exit logic unchanged.
"""

from __future__ import annotations
import numpy as np
import pandas as pd

from config import (EMA_PERIOD, CONFIRM_BARS, ATR_PERIOD, STOP_ATR_MULT,
                    VOLUME_PERIOD, VOLUME_MULT)


def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def atr(df: pd.DataFrame, n: int) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat([(h - l), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def signals(df: pd.DataFrame) -> pd.DataFrame:
    """Return df with columns: ema, atr, vol_sma, vol_ok, entry, exit (booleans)."""
    out = df.copy()
    out["ema"] = ema(out["close"], EMA_PERIOD)
    out["atr"] = atr(out, ATR_PERIOD)
    out["vol_sma"] = out["volume"].rolling(VOLUME_PERIOD).mean()
    out["vol_ok"] = out["volume"] >= VOLUME_MULT * out["vol_sma"]
    above = out["close"] > out["ema"]
    held = above.rolling(CONFIRM_BARS).sum() == CONFIRM_BARS
    # entry = first bar the "held above" becomes true AND volume confirms
    entry_raw = held & ~held.shift(1, fill_value=False)
    out["entry"] = entry_raw & out["vol_ok"].fillna(False)
    out["exit_signal"] = (out["close"] < out["ema"])  # cross back below
    return out
