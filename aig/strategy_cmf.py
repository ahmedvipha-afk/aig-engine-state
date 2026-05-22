"""CMF -- Chaikin Money Flow mean-reversion in bullish regime (long only).

FROZEN rules (pre-registered 2026-05-22 in config.py BEFORE any CMF data
was seen, per audit Concern 2).

Long-only volume-flow-domain mean-reversion strategy. CMF integrates the
per-bar money-flow multiplier over a rolling window:

  MFV_i  = ((C_i - L_i) - (H_i - C_i)) / (H_i - L_i) * volume_i
  CMF(N) = sum_{i=t-N+1..t}( MFV_i ) / sum_{i=t-N+1..t}( volume_i )

Each bar's money-flow multiplier in [-1, +1] records WHERE in its range
the bar closed (top of range = +1 accumulation, bottom = -1 distribution),
weighted by that bar's traded volume. CMF aggregates this into a
volume-weighted accumulation/distribution score in roughly [-1, +1].

Methodologically distinct from the ten prior strategies. Every prior
strategy uses VOLUME only as a CONFIRMATION (>= 1.2 * SMA(20)) layered
on top of a price-derived primary signal:

- EMA-200 / Divergence / MBV / PMR / STR / DBO / ROC / VCB / HAT / ART:
  primary signal = price level / RSI / range_pct / z-score / %K cross /
  Donchian high / ROC / ATR-min / HA candle / Aroon. Volume is only the
  >=1.2*SMA(20) confirmation filter.
- CMF: primary signal IS the integrated volume-weighted money flow. The
  bar's CLOSE-WITHIN-RANGE position is multiplied by VOLUME and summed
  over N bars. This is a different domain -- a tick-by-tick (intra-bar)
  buying-pressure surrogate, not a between-bar price/momentum/structure
  signal. No prior strategy reads this primitive.

Hypothesis: short-term distribution (CMF < -0.05) inside an intact
long-term bullish regime (close > EMA-200) is an oversold-in-trend
setup -- the macro trend is up but the near-term close-within-range
weighting is bearish, often a sign of weak hands selling into strong
hands. Mean-reversion to neutral/positive money flow likely. Quick
exit at CMF > +0.10 (accumulation flip) captures a small reversion;
higher-probability target than waiting for full trend retracement.
Frozen BEFORE seeing data per audit Concern 2 -- failure acceptable.

Entry (all must hold on the entry bar):
  1. CMF(CMF_PERIOD=20) < CMF_OS_LEVEL=-0.05 -- distribution dominates
     near-term money flow.
  2. close > EMA(CMF_TREND_EMA=200) -- long-term bullish regime intact.
  3. close > close.shift(CMF_TURNAROUND_BARS=1) -- today's close above
     yesterday's, a one-bar turnaround confirmation (prevents catching
     a free-fall).
  4. volume >= CMF_VOLUME_MIN_MULT=1.0 * SMA(CMF_VOLUME_PERIOD=20) --
     at-or-above average volume sanity check (no signal on near-zero-
     volume distribution).

Stop: entry - CMF_STOP_ATR_MULT=1.5 * ATR(14). Tight stop because the
mean-reversion thesis breaks fast if price falls further.

Exit:
  - CMF(CMF_PERIOD) > CMF_EXIT_LEVEL=+0.10 (accumulation has flipped
    dominant -- our reversion thesis played out).
  - close < EMA(CMF_TREND_EMA) (long-term regime broke).
  - ATR stop hit.

No per-ticker tuning. Deterministic. Long-only (Rule 15).
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from config import (CMF_PERIOD, CMF_OS_LEVEL, CMF_EXIT_LEVEL, CMF_TREND_EMA,
                    CMF_TURNAROUND_BARS, CMF_VOLUME_PERIOD, CMF_VOLUME_MIN_MULT,
                    CMF_STOP_ATR_MULT, ATR_PERIOD)


def _atr(df: pd.DataFrame, n: int) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat([(h - l), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def signals(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["atr"] = _atr(out, ATR_PERIOD)

    # EMA(200) regime filter. Engine sentinel column required by _simulate.
    out["ema"] = out["close"].ewm(span=CMF_TREND_EMA, adjust=False).mean()

    # Money-flow multiplier per bar in [-1, +1]:
    # ((close - low) - (high - close)) / (high - low).
    # When high == low (flat bar) the multiplier is undefined; treat as 0
    # (no directional info).
    rng = (out["high"] - out["low"]).replace(0.0, np.nan)
    mfm = ((out["close"] - out["low"]) - (out["high"] - out["close"])) / rng
    mfm = mfm.fillna(0.0)
    mfv = mfm * out["volume"]

    # Rolling sums for CMF.
    mfv_sum = mfv.rolling(CMF_PERIOD).sum()
    vol_sum = out["volume"].rolling(CMF_PERIOD).sum().replace(0.0, np.nan)
    out["cmf"] = (mfv_sum / vol_sum).fillna(0.0)

    # Volume sanity check.
    vol_sma = out["volume"].rolling(CMF_VOLUME_PERIOD).mean()
    volume_ok = out["volume"] >= (CMF_VOLUME_MIN_MULT * vol_sma)

    # One-bar turnaround confirmation.
    turnaround = out["close"] > out["close"].shift(CMF_TURNAROUND_BARS)

    # Regime + distribution flags.
    regime_ok = out["close"] > out["ema"]
    distribution = out["cmf"] < CMF_OS_LEVEL

    out["entry"] = (distribution & regime_ok & turnaround & volume_ok.fillna(False)).fillna(False)

    # Exit: accumulation flip OR regime broke (ATR stop in engine).
    accumulation_flip = out["cmf"] > CMF_EXIT_LEVEL
    regime_broke = out["close"] < out["ema"]
    out["exit_signal"] = accumulation_flip.fillna(False) | regime_broke.fillna(False)

    return out
