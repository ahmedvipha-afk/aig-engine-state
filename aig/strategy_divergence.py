"""
Bullish RSI Divergence — FROZEN rules (pre-registered in config.py, 2026-05-20).

LONG-ONLY by construction (Rule 15). Designed for the DAILY timeframe.

Definition (frozen):
  1. Compute RSI(14) on close.
  2. Identify "swing lows" — bars whose `low` is the local minimum across
     `DIV_PIVOT_HALFWIDTH` bars on each side.
  3. Within `DIV_LOOKBACK_BARS` of bar i, find the TWO most recent confirmed
     swing lows. (A swing low is confirmed only after `DIV_PIVOT_HALFWIDTH`
     bars have passed — so signals never look ahead.)
  4. Bullish divergence at bar i iff:
       - recent swing-low price < prior swing-low price (price LL)
       - recent swing-low RSI   > prior swing-low RSI   (RSI HL)
       - and bar i's close > previous bar's close (entry confirmation)
       - and trend filter: close > EMA(DIV_TREND_EMA)
  5. Stop distance: entry_close - (recent_swing_low - DIV_STOP_ATR_MULT*ATR(14))
  6. Exit: RSI closes >= DIV_RSI_EXIT OR price hits stop OR price closes
     below EMA(DIV_TREND_EMA) (trend abandonment).

No per-ticker tuning. Look-ahead-free by virtue of swing-low confirmation lag.
"""

from __future__ import annotations
import numpy as np
import pandas as pd

from config import (DIV_RSI_PERIOD, DIV_PIVOT_HALFWIDTH, DIV_LOOKBACK_BARS,
                    DIV_TREND_EMA, DIV_RSI_EXIT, DIV_STOP_ATR_MULT, ATR_PERIOD)


def _rsi(close: pd.Series, n: int) -> pd.Series:
    delta = close.diff()
    up = delta.clip(lower=0.0)
    dn = (-delta).clip(lower=0.0)
    rs = up.ewm(alpha=1.0 / n, adjust=False).mean() / \
        dn.ewm(alpha=1.0 / n, adjust=False).mean().replace(0, np.nan)
    return (100.0 - 100.0 / (1.0 + rs)).fillna(50.0)


def _ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def _atr(df: pd.DataFrame, n: int) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat([(h - l), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def _swing_lows(low: pd.Series, half: int) -> pd.Series:
    """Boolean series — True at bars confirmed as swing lows (after `half`
    bars have passed without violating)."""
    window = 2 * half + 1
    rolling_min = low.rolling(window, center=True).min()
    is_min = (low == rolling_min)
    # Confirm by shifting forward so the signal isn't visible until `half`
    # bars after the pivot bar (no look-ahead).
    return is_min.shift(half).fillna(False)


def signals(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["rsi"] = _rsi(out["close"], DIV_RSI_PERIOD)
    out["ema"] = _ema(out["close"], DIV_TREND_EMA)   # used as trend filter
    out["atr"] = _atr(out, ATR_PERIOD)
    out["swing"] = _swing_lows(out["low"], DIV_PIVOT_HALFWIDTH)

    entries = np.zeros(len(out), dtype=bool)
    stop_dist = np.zeros(len(out), dtype=float)
    swing_idx = np.where(out["swing"].values)[0]

    low_v = out["low"].values
    rsi_v = out["rsi"].values
    close_v = out["close"].values
    ema_v = out["ema"].values
    atr_v = out["atr"].values

    for i in range(DIV_LOOKBACK_BARS, len(out)):
        # collect the two most recent confirmed swing lows in the lookback window
        recent = swing_idx[(swing_idx <= i) & (swing_idx >= i - DIV_LOOKBACK_BARS)]
        if len(recent) < 2:
            continue
        i_recent, i_prior = recent[-1], recent[-2]
        price_ll = low_v[i_recent] < low_v[i_prior]
        rsi_hl = rsi_v[i_recent] > rsi_v[i_prior]
        if not (price_ll and rsi_hl):
            continue
        # confirmation: close > previous close
        if close_v[i] <= close_v[i - 1]:
            continue
        # trend filter: close above DIV_TREND_EMA
        if not (close_v[i] > ema_v[i]):
            continue
        entries[i] = True
        # stop distance = entry close - (recent swing low - buffer)
        buf = DIV_STOP_ATR_MULT * atr_v[i]
        sd = float(close_v[i] - (low_v[i_recent] - buf))
        stop_dist[i] = max(sd, 0.0001)

    out["entry"] = entries
    out["stop_dist"] = stop_dist
    # exit when RSI back at or above DIV_RSI_EXIT, or trend filter breaks
    out["exit_signal"] = ((out["rsi"] >= DIV_RSI_EXIT) |
                          (out["close"] < out["ema"]))
    return out
