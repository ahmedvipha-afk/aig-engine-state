"""PMR -- Price-Mean Z-score Reversion (long only).

FROZEN rules (pre-registered 2026-05-21 Fire 15:05 UTC in config.py).

Long-only mean-reversion driven by the STATISTICAL z-score of close vs its
rolling mean / std. Methodologically distinct from the seven prior strategies:

- EMA-200 (trend-confirm): position-based, close > long EMA.
- Divergence (mean-rev-on-low): RSI hookup at swing-low structure.
- MBV (mean-rev-in-uptrend): range_pct in lower third of trailing high/low.
- DBO (breakout): close crosses Donchian high.
- ROC (velocity-momentum): rate-of-change threshold.
- VCB (vol-cycle): ATR-minimum compression.
- HAT (smoothed-trend): N consecutive bullish Heikin-Ashi candles.
- PMR (statistical-zscore-mean-rev): z = (close - SMA_N) / std_N. Unlike
  MBV (range_pct is bounded [0,1] from raw high/low) PMR uses standardized
  deviation -- AUTOMATICALLY adapts to per-ticker volatility. Two stocks
  with identical range_pct but different historical std will have very
  different z-scores; PMR sees the statistical extremity raw-range strategies
  treat as identical.

Hypothesis: noisy markets (UAE / Crypto) where raw range or RSI-based
mean-rev rules fail on the WR floor may show edge under z-score-normalized
entry signals, because z-score self-adapts to per-ticker volatility and
flags genuine statistical outliers rather than relative-range outliers.
Frozen BEFORE seeing data per audit Concern 2 -- failure acceptable.

Entry (all must hold on the entry bar, edge-triggered):
  1. z(PMR_PERIOD=20) <= -PMR_Z_FLOOR=1.5 (close is >= 1.5 stddev BELOW
     its 20-day mean -- statistically extreme low).
  2. z(20) > z(20).shift(1) (z is RISING -- recovery has begun; do not
     try to catch a falling knife mid-decline).
  3. close > SMA(PMR_TREND_SMA=200) (bullish regime; no longs in
     confirmed downtrends).
  4. volume >= PMR_VOLUME_MULT=1.2 * SMA(PMR_VOLUME_PERIOD=20)
     (institutional participation confirms the reversion).

Edge-triggered: yesterday at least one of (1), (2), (4) was false.
Prevents continuous re-entry while a sustained statistical-low run persists.

Stop: entry - PMR_STOP_ATR_MULT=1.5 * ATR(14). Mean-reversion stops tend
to be tighter than breakout stops because the thesis is symmetric retracement.

Exit:
  - z(20) >= PMR_Z_EXIT=0.0 (mean reversion completed: price reached
    or crossed its 20-day mean).
  - close < SMA(PMR_TREND_SMA) (regime broke).
  - ATR stop hit.

No per-ticker tuning. Deterministic. Long-only (Rule 15).
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from config import (PMR_PERIOD, PMR_Z_FLOOR, PMR_Z_EXIT, PMR_TREND_SMA,
                    PMR_VOLUME_PERIOD, PMR_VOLUME_MULT,
                    PMR_STOP_ATR_MULT, ATR_PERIOD)


def _atr(df: pd.DataFrame, n: int) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat([(h - l), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def signals(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["atr"] = _atr(out, ATR_PERIOD)

    # Rolling mean / std of close over PMR_PERIOD, shifted by 1 so today's
    # close never contaminates the mean/std that it is tested against.
    mean_n = out["close"].rolling(PMR_PERIOD).mean().shift(1)
    std_n = out["close"].rolling(PMR_PERIOD).std().shift(1).replace(0, np.nan)
    out["z"] = (out["close"] - mean_n) / std_n

    # SMA(200) regime filter. Backtest engine looks for "ema" column to gate
    # NaN-skipping; use SMA(200) here -- does NOT gate entries, just a sentinel.
    out["sma"] = out["close"].rolling(PMR_TREND_SMA).mean()
    out["ema"] = out["sma"]

    # Volume confirmation.
    vol_sma = out["volume"].rolling(PMR_VOLUME_PERIOD).mean()
    volume_ok = out["volume"] >= (PMR_VOLUME_MULT * vol_sma)

    # Composite entry conditions:
    extreme_low = out["z"] <= -PMR_Z_FLOOR
    z_rising = out["z"] > out["z"].shift(1)
    trend_ok = out["close"] > out["sma"]

    all_conds = extreme_low & z_rising & trend_ok & volume_ok.fillna(False)

    # Edge-trigger: yesterday at least one was false -- today is the first
    # bar that all four conditions align.
    all_prev = all_conds.shift(1).fillna(False)
    out["entry"] = all_conds & ~all_prev

    # Exit: z reverted to mean OR regime broke (ATR stop handled in engine).
    mean_reached = out["z"] >= PMR_Z_EXIT
    regime_broke = out["close"] < out["sma"]
    out["exit_signal"] = mean_reached.fillna(False) | regime_broke.fillna(False)

    return out
