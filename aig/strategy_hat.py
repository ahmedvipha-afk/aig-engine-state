"""HAT — Heikin-Ashi Trend Continuation (long only).

FROZEN rules (pre-registered 2026-05-21 Fire 14:55 UTC in config.py).

Long-only signal derived from SMOOTHED (Heikin-Ashi) candles rather than
raw OHLC. Methodologically distinct from the six prior strategies — every
prior strategy operates on RAW bars (close > EMA, close > Donchian high,
range_pct on raw high/low, ROC on raw close, ATR-min on raw ATR). HAT
replaces the raw OHLC input with a recursive filtered representation:

    HA_close[t] = (open[t] + high[t] + low[t] + close[t]) / 4
    HA_open[t]  = (HA_open[t-1] + HA_close[t-1]) / 2   (seeded with first bar)
    HA_high[t]  = max(high[t], HA_open[t], HA_close[t])
    HA_low[t]   = min(low[t],  HA_open[t], HA_close[t])

The recursive filter dampens individual-bar noise and surfaces multi-bar
trend regimes that raw-bar strategies miss. A bullish HA candle
(HA_close > HA_open) is structurally noise-robust because both inputs
are blends of multiple raw values.

Hypothesis: noisy markets (UAE / Crypto) where raw-bar strategies fail
on WR floor may show edge under noise-smoothed entry/exit signals. The
HA filter is a different functional form than any of the six prior
strategies' filters, not a parameter retune of one of them.

Entry (all must hold on the entry bar, edge-triggered):
  1. HAT_BULLISH_BARS=3 consecutive bullish HA candles ending today
     (HA_close > HA_open for the last 3 bars).
  2. raw close > EMA(HAT_TREND_EMA=200) — regime filter on raw price
     so the smoothed signal cannot fire in a confirmed downtrend.
  3. volume >= HAT_VOLUME_MULT=1.2 * SMA(HAT_VOLUME_PERIOD=20) of volume.

Edge-triggered: yesterday at least one of (1) or (3) was false. The
bar must be the FIRST that completes the run-of-3 + volume confirm;
prevents continuous re-entry while a sustained bullish HA run persists
(those are already captured by the initial entry).

Stop: entry - HAT_STOP_ATR_MULT=2.0 * ATR(14).

Exit:
  - HA candle turns bearish (HA_close <= HA_open) — smoothed trend
    has broken on the filter the strategy uses.
  - raw close < EMA(HAT_TREND_EMA) — regime broke.
  - ATR stop hit.

No per-ticker tuning. Deterministic. Long-only (Rule 15).
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from config import (HAT_BULLISH_BARS, HAT_TREND_EMA,
                    HAT_VOLUME_PERIOD, HAT_VOLUME_MULT,
                    HAT_STOP_ATR_MULT, ATR_PERIOD)


def _atr(df: pd.DataFrame, n: int) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat([(h - l), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def _heikin_ashi(df: pd.DataFrame) -> pd.DataFrame:
    o, h, l, c = df["open"], df["high"], df["low"], df["close"]
    ha_close = (o + h + l + c) / 4.0
    ha_open = pd.Series(index=df.index, dtype=float)
    if len(df) > 0:
        ha_open.iloc[0] = (o.iloc[0] + c.iloc[0]) / 2.0
        for i in range(1, len(df)):
            ha_open.iloc[i] = (ha_open.iloc[i - 1] + ha_close.iloc[i - 1]) / 2.0
    ha_high = pd.concat([h, ha_open, ha_close], axis=1).max(axis=1)
    ha_low = pd.concat([l, ha_open, ha_close], axis=1).min(axis=1)
    return pd.DataFrame({
        "ha_open": ha_open,
        "ha_high": ha_high,
        "ha_low": ha_low,
        "ha_close": ha_close,
    }, index=df.index)


def signals(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # ATR(14) for the stop.
    out["atr"] = _atr(out, ATR_PERIOD)

    # EMA(200) regime filter on RAW close.
    out["ema"] = out["close"].ewm(span=HAT_TREND_EMA, adjust=False).mean()

    # Heikin-Ashi smoothed candles.
    ha = _heikin_ashi(out)
    out = pd.concat([out, ha], axis=1)
    out["ha_bullish"] = out["ha_close"] > out["ha_open"]

    # N consecutive bullish HA bars ending today.
    run = out["ha_bullish"].astype(int).rolling(HAT_BULLISH_BARS).sum()
    bullish_run = run == HAT_BULLISH_BARS

    # Regime filter on raw close.
    trend_ok = out["close"] > out["ema"]

    # Volume confirmation.
    vol_sma = out["volume"].rolling(HAT_VOLUME_PERIOD).mean()
    volume_ok = out["volume"] >= (HAT_VOLUME_MULT * vol_sma)

    all_three = bullish_run & trend_ok & volume_ok

    # Edge-trigger: yesterday at least one was false → today first time all hold.
    all_three_prev = all_three.shift(1).fillna(False)
    out["entry"] = all_three & ~all_three_prev

    # Exit: HA bearish OR regime broke (ATR stop handled in engine).
    ha_bearish = out["ha_close"] <= out["ha_open"]
    regime_broke = out["close"] < out["ema"]
    out["exit_signal"] = ha_bearish | regime_broke

    return out
