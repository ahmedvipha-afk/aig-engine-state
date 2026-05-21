"""DBO — Donchian Breakout + Volume (long only).

FROZEN rules (pre-registered 2026-05-21 Fire 1 in config.py).

Long-only trend-following BREAKOUT strategy. Methodologically distinct from
the three earlier registered strategies (EMA-200 trend-confirmation,
Divergence mean-reversion-on-low, MBV mean-reversion-in-uptrend) — DBO buys
strength on new highs rather than buying weakness or pullbacks.

Filters:
  1. Donchian high breakout — close > 20-day high computed on bars shifted
     by 1 (so the current bar's high doesn't contaminate the breakout test).
  2. Volume confirmation — entry-bar volume >= 1.5 x SMA(20) of volume.

Exit:
  - close < 10-day Donchian low (computed shifted by 1) — trend breakdown, OR
  - ATR stop hit (entry - 2.0 x ATR(14)).

Asymmetric Donchian window (20 in / 10 out) so winners run further than
losers get to recover.

No per-ticker tuning. Deterministic.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from config import (DBO_DONCHIAN_HIGH, DBO_DONCHIAN_LOW, DBO_VOLUME_PERIOD,
                    DBO_VOLUME_MULT, DBO_STOP_ATR_MULT, ATR_PERIOD)


def _atr(df: pd.DataFrame, n: int) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat([(h - l), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def signals(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # Donchian channels, shifted by 1 to remove look-ahead.
    out["donch_hi"] = out["high"].rolling(DBO_DONCHIAN_HIGH).max().shift(1)
    out["donch_lo"] = out["low"].rolling(DBO_DONCHIAN_LOW).min().shift(1)

    # ATR for stop-distance and the engine's _stop_distance dispatcher.
    out["atr"] = _atr(out, ATR_PERIOD)

    # Volume confirmation.
    out["vol_sma"] = out["volume"].rolling(DBO_VOLUME_PERIOD).mean()
    out["vol_ok"] = out["volume"] >= DBO_VOLUME_MULT * out["vol_sma"]

    # EMA column required by the engine's _simulate (it skips bars where ema/atr
    # are NaN). For DBO we use a fast EMA(20) just as a not-NaN sentinel — it
    # does not gate entries or exits (those use donch_hi/lo).
    out["ema"] = out["close"].ewm(span=20, adjust=False).mean()

    # Entry: breakout above 20-day high, volume confirmed. Edge-triggered so
    # we only fire on the bar that FIRST breaks above; consecutive bars above
    # the channel don't keep firing.
    above = out["close"] > out["donch_hi"]
    above_prev = out["close"].shift(1) > out["donch_hi"].shift(1)
    edge = above & ~above_prev.fillna(False)
    out["entry"] = edge & out["vol_ok"].fillna(False)

    # Exit: close below 10-day low (trend breakdown).
    out["exit_signal"] = out["close"] < out["donch_lo"]

    return out
