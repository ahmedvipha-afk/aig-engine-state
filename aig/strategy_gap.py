"""GAP -- Overnight Gap Continuation in Uptrend (long only).

FROZEN rules (pre-registered 2026-05-22 Sprint Obj-6 advance in config.py
BEFORE any GAP data was seen, per audit Concern 2).

12th strategy in the pipeline. Methodologically distinct from the eleven
prior strategies (EMA-200 / Divergence / MBV / DBO / ROC / VCB / HAT /
PMR / STR / ART / CMF): every prior strategy reads WITHIN-BAR or
ROLLING-WINDOW primitives. GAP reads the BETWEEN-BAR discontinuity --
today's open versus yesterday's close. The gap exists only at the open
print and is not captured by any rolling aggregator.

Entry (all must hold on the entry bar):
  1. open >= prior_close * (1 + GAP_THRESHOLD=0.02) -- overnight gap up
     of 2%+ exists at today's open.
  2. close > open -- the gap held intraday (did NOT fade to a fill).
  3. close > SMA(GAP_TREND_SMA=50) -- bullish regime filter (no longs in
     downtrends; gap-and-go thesis needs trend tailwind).
  4. volume >= GAP_VOLUME_MULT=1.5 * SMA(GAP_VOLUME_PERIOD=20) -- elevated
     volume confirms institutional commitment (vs thin-trade gap).

Stop: entry - GAP_STOP_ATR_MULT=1.5 * ATR(14). Tight stop because the
mean-reversion (gap-fade) thesis breaks fast if price retraces.

Exit:
  - close < SMA(GAP_EXIT_SMA=10) -- short-term momentum lost.
  - ATR stop hit (engine).

The entry-bar open price is captured as the entry-price; the engine's
default behavior uses entry = close, which is acceptable here since
entry only fires when close > open (the gap held), so close >= open
and the close-entry is conservative vs an open-fill.

No per-ticker tuning. Deterministic. Long-only (Rule 15).

Hypothesis (frozen pre-data): An overnight gap up of >=2% in an
established uptrend that does not fade intraday and is confirmed by
elevated volume represents an institutional commitment. Price tends
to continue in the gap direction for several bars before mean-reverting.
Failure modes acceptable: (a) on continuous markets (crypto via yfinance
1D bars), gaps are rare and trade count may fail the 1000 floor -- honest
FAIL per Concern 2; (b) on noisy small markets (UAE) gap quality may be
too low to clear WR floor -- also honest FAIL. The strategy is genuinely
new methodology; the verdict is what the data gives.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from config import (GAP_THRESHOLD, GAP_TREND_SMA, GAP_EXIT_SMA,
                    GAP_VOLUME_PERIOD, GAP_VOLUME_MULT,
                    GAP_STOP_ATR_MULT, ATR_PERIOD)


def _atr(df: pd.DataFrame, n: int) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat([(h - l), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def signals(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["atr"] = _atr(out, ATR_PERIOD)

    # Engine sentinel column required by _simulate -- use SMA(GAP_TREND_SMA)
    # as the "ema" sentinel (any non-NaN trend reference works; engine only
    # tests np.isnan on it).
    out["ema"] = out["close"].rolling(GAP_TREND_SMA).mean()

    # Short-term momentum SMA for exit.
    out["sma_exit"] = out["close"].rolling(GAP_EXIT_SMA).mean()

    # Gap event: today's open vs yesterday's close.
    prior_close = out["close"].shift(1)
    gap_up = out["open"] >= prior_close * (1.0 + GAP_THRESHOLD)

    # Intraday strength: the gap held, did not fade to a fill.
    held = out["close"] > out["open"]

    # Regime filter: bullish trend intact.
    regime_ok = out["close"] > out["ema"]

    # Volume confirmation.
    vol_sma = out["volume"].rolling(GAP_VOLUME_PERIOD).mean()
    volume_ok = out["volume"] >= (GAP_VOLUME_MULT * vol_sma)

    out["entry"] = (
        gap_up.fillna(False)
        & held.fillna(False)
        & regime_ok.fillna(False)
        & volume_ok.fillna(False)
    )

    # Exit: short-term momentum lost (close below SMA(10)).
    momentum_lost = out["close"] < out["sma_exit"]
    out["exit_signal"] = momentum_lost.fillna(False)

    return out
