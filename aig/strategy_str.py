"""STR -- Stochastic %K Reversal in Trend (long only).

FROZEN rules (pre-registered 2026-05-22 in config.py).

Long-only mean-reversion driven by the STOCHASTIC %K oscillator. Buys when
%K crosses UP through an oversold floor (recovery has begun) while the
broader regime is bullish, with volume confirmation. Exits quickly at the
midpoint (%K = 50) -- the thesis is "small bounce after extreme low,"
not "full reversal."

Methodologically distinct from the eight prior strategies:

- EMA-200 (trend-confirm): position-based, close > long EMA.
- Divergence (mean-rev-on-low): RSI HIGHER-low against PRICE LOWER-low
  swing-pivot structure (gain/loss ratio).
- MBV (mean-rev-in-uptrend): range_pct in lower third of trailing high/low
  (EDGE condition on raw range bucket).
- DBO (breakout): close crosses Donchian high (level crossing).
- ROC (velocity-momentum): rate of price change (derivative).
- VCB (vol-cycle): ATR-minimum compression (volatility input).
- HAT (smoothed-trend): N consecutive bullish Heikin-Ashi candles
  (recursive smoothing).
- PMR (statistical-zscore-mean-rev): z = (close - SMA_N) / std_N
  (standardized deviation, continuous).
- STR (stochastic-cross-up-mean-rev): %K = 100 * (close - LL_N) / (HH_N - LL_N).
  CROSS-UP event from oversold zone, NOT a level condition. Unlike PMR
  (continuous z) or MBV (lower-third level), STR fires ONLY on the bar
  where %K transitions from <=20 to >20 -- a discrete recovery confirmation
  rather than a static extremity condition. Quick midpoint exit (%K>=50)
  captures small bounces in noisy markets where PMR/Divergence's
  full-mean-reversal exits sit through chop.

Hypothesis: noisy UAE / Crypto markets where prior mean-rev strategies
fail on the 40% WR floor may show edge under a faster-target mean-rev
that exits at the range midpoint rather than the statistical mean. The
small fixed target (range_midpoint) is more reliably hit in noisy markets
than the SMA mean (PMR exit), giving higher WR by construction. Frozen
BEFORE seeing data per audit Concern 2 -- failure acceptable.

Entry (all must hold on the entry bar):
  1. %K(STR_PERIOD=14) > STR_OS_LEVEL=20.0 today AND
     %K(STR_PERIOD).shift(1) <= STR_OS_LEVEL -- the cross-up event from
     oversold zone.
  2. close > SMA(STR_TREND_SMA=200) -- bullish regime; no longs in
     confirmed downtrends.
  3. volume >= STR_VOLUME_MULT=1.2 * SMA(STR_VOLUME_PERIOD=20)
     -- participation confirms the recovery.

Cross event is inherently edge-triggered (the .shift(1) condition
guarantees yesterday's %K <= 20, today's > 20, exactly one bar fires).

Stop: entry - STR_STOP_ATR_MULT=1.5 * ATR(14). Tight stop because the
thesis is small-bounce; deeper drawdowns invalidate it.

Exit:
  - %K(STR_PERIOD) >= STR_EXIT_LEVEL=50.0 (midpoint reached -- small
    bounce captured).
  - close < SMA(STR_TREND_SMA) (regime broke).
  - ATR stop hit.

No per-ticker tuning. Deterministic. Long-only (Rule 15).
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from config import (STR_PERIOD, STR_OS_LEVEL, STR_EXIT_LEVEL, STR_TREND_SMA,
                    STR_VOLUME_PERIOD, STR_VOLUME_MULT,
                    STR_STOP_ATR_MULT, ATR_PERIOD)


def _atr(df: pd.DataFrame, n: int) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat([(h - l), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def signals(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["atr"] = _atr(out, ATR_PERIOD)

    # Stochastic %K over STR_PERIOD bars. Rolling HH / LL are shifted by 0
    # because by convention %K uses the CURRENT bar's high/low in the
    # window (close - LL_N) / (HH_N - LL_N). Look-ahead is bounded: %K
    # itself is published at close, signal uses today's close vs today's
    # %K (not future bars).
    hh_n = out["high"].rolling(STR_PERIOD).max()
    ll_n = out["low"].rolling(STR_PERIOD).min()
    rng = (hh_n - ll_n).replace(0, np.nan)
    out["k"] = 100.0 * (out["close"] - ll_n) / rng

    # SMA(200) regime filter.
    out["sma"] = out["close"].rolling(STR_TREND_SMA).mean()
    # Engine sentinel column required by _simulate.
    out["ema"] = out["sma"]

    # Volume confirmation.
    vol_sma = out["volume"].rolling(STR_VOLUME_PERIOD).mean()
    volume_ok = out["volume"] >= (STR_VOLUME_MULT * vol_sma)

    # Cross-up event from oversold floor.
    k_prev = out["k"].shift(1)
    cross_up = (k_prev <= STR_OS_LEVEL) & (out["k"] > STR_OS_LEVEL)

    trend_ok = out["close"] > out["sma"]

    out["entry"] = (cross_up & trend_ok & volume_ok.fillna(False)).fillna(False)

    # Exit: midpoint reached OR regime broke (ATR stop handled in engine).
    mid_reached = out["k"] >= STR_EXIT_LEVEL
    regime_broke = out["close"] < out["sma"]
    out["exit_signal"] = mid_reached.fillna(False) | regime_broke.fillna(False)

    return out
