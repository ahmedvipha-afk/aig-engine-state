"""WCK -- Lower-Wick Rejection Mean-Reversion (long only).

FROZEN rules (pre-registered 2026-05-22 Sprint Obj-6 advance post-GAP in
config.py BEFORE any WCK data was seen, per audit Concern 2).

13th strategy in the pipeline. Methodologically distinct from the twelve
prior strategies: WCK is the FIRST strategy whose PRIMARY signal is the
INTRA-BAR SHAPE RATIO of a single candle. Every prior strategy reads
either between-bar (GAP), rolling-window (EMA200 / MBV / DBO / ROC / VCB /
PMR / STR / ART), recursive smoothed (HAT), volume-integrated (CMF), or
swing-pivot (Divergence) primitives. The single-bar wick-to-range anatomy
is unused as a primary signal in any of them. CMF uses the per-bar
close-position-in-range multiplier but immediately integrates it over N
bars with volume weighting -- WCK reads the unaggregated single-bar shape.

Entry (all must hold on the entry bar):
  1. lower_wick / bar_range >= WCK_WICK_RATIO_FLOOR=0.5 -- the lower wick
     is at least half the bar's range (canonical hammer / long-lower-wick
     pattern indicating intra-bar rejection of lower prices).
  2. body / bar_range <= WCK_BODY_RATIO_CEIL=0.35 -- body is small relative
     to range (filters bullish marubozu / large-body up days that happen
     to have a tiny lower wick).
  3. bar_range >= WCK_MIN_RANGE_ATR_RATIO=0.5 * ATR(14) -- bar range is
     meaningful (skips dojis / microscopic bars where wick ratios are
     unreliable).
  4. close > SMA(WCK_TREND_SMA=200) -- bullish regime filter; the
     accumulation-at-rejection thesis only works in uptrends.
  5. volume >= WCK_VOLUME_MULT=1.2 * SMA(WCK_VOLUME_PERIOD=20) -- elevated
     volume confirms institutional commitment vs a thin-trade fake wick.

Stop: entry - WCK_STOP_ATR_MULT=1.0 * ATR(14). Tight stop because the
intra-bar-rejection thesis breaks fast if the wick's low is taken out
within a couple bars.

Exit:
  - close >= rolling_max(close.shift(1), WCK_EXIT_LOOKBACK=5) -- close
    exceeds the prior 5-bar high -- small bounce captured.
  - close < SMA(WCK_TREND_SMA) -- regime broke.
  - ATR stop hit (engine).

Note on body sign: lower_wick = min(open, close) - low. Whether the
candle is bullish (close > open) or bearish (close < open) does NOT
affect entry by itself -- a bearish hammer (small bearish body + long
lower wick) and a bullish hammer (small bullish body + long lower wick)
both satisfy the entry. The thesis is rejection of lower prices, which
is captured by the wick regardless of the body's direction.

Hypothesis (frozen pre-data): noisy markets (UAE / Crypto) where prior
mean-rev strategies hit the 40% WR floor may show edge under a
single-bar-shape entry with a fast 5-bar-high exit. The small fixed
target (recover to prior 5-bar high) is more reliably hit than a
statistical mean exit (PMR z=0) or oscillator midpoint (STR %K=50)
in choppy markets. Failure acceptable per audit Concern 2.

No per-ticker tuning. Deterministic. Long-only (Rule 15).
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from config import (WCK_WICK_RATIO_FLOOR, WCK_BODY_RATIO_CEIL,
                    WCK_MIN_RANGE_ATR_RATIO, WCK_TREND_SMA,
                    WCK_VOLUME_PERIOD, WCK_VOLUME_MULT,
                    WCK_EXIT_LOOKBACK, ATR_PERIOD)


def _atr(df: pd.DataFrame, n: int) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat([(h - l), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def signals(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["atr"] = _atr(out, ATR_PERIOD)

    # SMA(200) regime filter. Engine sentinel column required by _simulate.
    out["sma"] = out["close"].rolling(WCK_TREND_SMA).mean()
    out["ema"] = out["sma"]

    # Intra-bar geometry. Guard against zero-range bars with replace(0, NaN).
    bar_range = (out["high"] - out["low"]).replace(0, np.nan)
    body_top = np.maximum(out["open"], out["close"])
    body_bot = np.minimum(out["open"], out["close"])
    body = (body_top - body_bot).abs()
    lower_wick = body_bot - out["low"]

    wick_ratio = lower_wick / bar_range
    body_ratio = body / bar_range

    # Single-bar wick anatomy conditions.
    wick_ok = wick_ratio >= WCK_WICK_RATIO_FLOOR
    body_ok = body_ratio <= WCK_BODY_RATIO_CEIL
    range_ok = bar_range >= (WCK_MIN_RANGE_ATR_RATIO * out["atr"])

    # Regime filter.
    regime_ok = out["close"] > out["sma"]

    # Volume confirmation.
    vol_sma = out["volume"].rolling(WCK_VOLUME_PERIOD).mean()
    volume_ok = out["volume"] >= (WCK_VOLUME_MULT * vol_sma)

    out["entry"] = (
        wick_ok.fillna(False)
        & body_ok.fillna(False)
        & range_ok.fillna(False)
        & regime_ok.fillna(False)
        & volume_ok.fillna(False)
    )

    # Exit signal: close exceeds the rolling max of the prior N closes
    # (small bounce captured) OR regime broke. ATR stop is handled by
    # the engine.
    prior_max = out["close"].shift(1).rolling(WCK_EXIT_LOOKBACK).max()
    bounce_captured = out["close"] >= prior_max
    regime_broke = out["close"] < out["sma"]
    out["exit_signal"] = bounce_captured.fillna(False) | regime_broke.fillna(False)

    return out
