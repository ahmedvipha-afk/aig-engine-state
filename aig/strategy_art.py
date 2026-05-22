"""ART -- Aroon Time-Trend Strength (long only).

FROZEN rules (pre-registered 2026-05-22 in config.py BEFORE any ART data
was seen, per audit Concern 2).

Long-only TIME-DOMAIN trend-strength strategy. Aroon measures how RECENTLY
price made its N-period high vs its N-period low. Unlike every prior
strategy (which is magnitude-domain -- using levels, derivatives, oscillator
values, range positions, etc.), Aroon is bar-count-since-extreme. Two stocks
with identical price action over 14 days but different EXACT-DAY structure
of where the highs/lows landed can have very different Aroon values.

Methodologically distinct from the nine prior strategies:

- EMA-200 (trend-confirm): close > long EMA (level).
- Divergence (mean-rev-on-low): RSI vs price swing-pivot structure.
- MBV (mean-rev-in-uptrend): range_pct lower third (level).
- DBO (breakout): close crosses Donchian high (level crossing).
- ROC (velocity-momentum): rate of price change (derivative).
- VCB (vol-cycle): ATR-min compression (volatility input).
- HAT (smoothed-trend): N consecutive bullish HA candles (recursive bar
  filter).
- PMR (statistical-zscore-mean-rev): z = (close - SMA) / std (standardized
  deviation).
- STR (stochastic-cross-up): %K cross-up event from oversold zone.
- ART (TIME-since-extreme dominance): Aroon Up - Aroon Down crosses ABOVE
  +50 -- a TIME-DOMAIN signal that yesterday's bar-count balance was
  neutral-or-bearish and today's tilted hard-bullish. ART sees regime
  transitions invisible to magnitude-based strategies: a stock that has
  been making fresh 14-day highs every 2-3 bars while its 14-day lows are
  10+ bars in the past has Aroon Osc >> +50, even if price levels are
  flat and momentum is mild. This 'recency-of-high-vs-low' geometry
  captures a regime property no other indicator family measures.

Hypothesis: noisy markets (UAE / Crypto) where price-magnitude signals
fail on the 40% WR floor may show edge under TIME-since-extreme dominance.
In noisy markets, magnitude signals fire on chop and reverse; time-since-
extreme dominance only flips when a structural new-high cluster appears,
which is more selective and may yield higher WR. Frozen BEFORE seeing
data per audit Concern 2 -- failure acceptable.

Entry (all must hold on the entry bar, cross-up edge-triggered):
  1. AroonOsc(ART_AROON_PERIOD=14) > +ART_AROON_OSC_THRESHOLD=50.0 today
     AND AroonOsc.shift(1) <= ART_AROON_OSC_THRESHOLD -- yesterday it was
     <=50, today it crossed above. Cross event is naturally edge-triggered.
  2. close > SMA(ART_TREND_SMA=50) -- bullish regime; no longs in
     confirmed downtrends.
  3. volume >= ART_VOLUME_MULT=1.2 * SMA(ART_VOLUME_PERIOD=20) -- volume
     participation confirms the recency-of-new-high pattern is genuine.

Stop: entry - ART_STOP_ATR_MULT=2.0 * ATR(14). Wider stop than
mean-reversion strategies because the thesis is trend-continuation; small
pullbacks are expected.

Exit:
  - AroonOsc(ART_AROON_PERIOD) <= 0 (time-domain dominance flipped to
    bearish-or-neutral -- new-low recency caught up to new-high recency).
  - close < SMA(ART_TREND_SMA) (regime broke).
  - ATR stop hit.

Aroon definitions (Tushar Chande, 1995):
  AroonUp(N)   = 100 * (N - bars_since_N_period_high) / N
  AroonDown(N) = 100 * (N - bars_since_N_period_low)  / N
  AroonOsc(N)  = AroonUp(N) - AroonDown(N)   (range -100 to +100)

When the most recent N-period high is today, AroonUp = 100. When it was
N bars ago, AroonUp = 0. Symmetric for AroonDown.

No per-ticker tuning. Deterministic. Long-only (Rule 15).
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from config import (ART_AROON_PERIOD, ART_AROON_OSC_THRESHOLD, ART_TREND_SMA,
                    ART_VOLUME_PERIOD, ART_VOLUME_MULT,
                    ART_STOP_ATR_MULT, ATR_PERIOD)


def _atr(df: pd.DataFrame, n: int) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat([(h - l), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def signals(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["atr"] = _atr(out, ATR_PERIOD)

    n = ART_AROON_PERIOD
    # Rolling window of N+1 bars so the index-of-max / index-of-min can range
    # over [0, N] (today inclusive). Convert "argmax position" within window
    # to "bars since extreme" = (N - argmax_position). When today is the new
    # high, argmax == N (last position) so bars_since = 0 -> AroonUp = 100.
    def _bars_since_high(s: pd.Series) -> pd.Series:
        return s.rolling(n + 1).apply(lambda w: n - int(np.argmax(w)), raw=True)

    def _bars_since_low(s: pd.Series) -> pd.Series:
        return s.rolling(n + 1).apply(lambda w: n - int(np.argmin(w)), raw=True)

    bsh = _bars_since_high(out["high"])
    bsl = _bars_since_low(out["low"])
    aroon_up = 100.0 * (n - bsh) / n
    aroon_dn = 100.0 * (n - bsl) / n
    out["aroon_osc"] = aroon_up - aroon_dn

    # SMA(50) regime filter. Engine sentinel column required by _simulate.
    out["sma"] = out["close"].rolling(ART_TREND_SMA).mean()
    out["ema"] = out["sma"]

    # Volume confirmation.
    vol_sma = out["volume"].rolling(ART_VOLUME_PERIOD).mean()
    volume_ok = out["volume"] >= (ART_VOLUME_MULT * vol_sma)

    # Cross-up event from <= threshold to > threshold.
    osc_prev = out["aroon_osc"].shift(1)
    cross_up = (osc_prev <= ART_AROON_OSC_THRESHOLD) & (out["aroon_osc"] > ART_AROON_OSC_THRESHOLD)

    trend_ok = out["close"] > out["sma"]

    out["entry"] = (cross_up & trend_ok & volume_ok.fillna(False)).fillna(False)

    # Exit: dominance flipped to <=0 OR regime broke (ATR stop in engine).
    dominance_lost = out["aroon_osc"] <= 0.0
    regime_broke = out["close"] < out["sma"]
    out["exit_signal"] = dominance_lost.fillna(False) | regime_broke.fillna(False)

    return out
