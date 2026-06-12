"""TSM-12 — Time-Series Momentum, 12-month lookback (long only).

FROZEN spec (pre-registered 2026-06-12, trial 40, spec_hash efe8ac7b47f10a0f;
canonical spec text + hash derivation in strategy_register.md, params in
config.py per Path 2d-A).

Signal: per-ticker 12-month total return = close[t] / close[t-252] - 1,
evaluated MONTHLY on the last trading day of the month. LONG if positive,
FLAT otherwise. Time-series momentum (Moskowitz/Ooi/Pedersen 2012) -- each
ticker measured against its own past; NOT cross-sectional ranking.

Engine mapping (edge-case conventions inherited from trials 1-39; each is
documented in the trial's verdict decision_log entry):
  - Evaluation day = a bar whose NEXT bar falls in a different calendar
    month within the available history. The final bar of the series is
    never an evaluation day (its month may be incomplete).
  - entry       = evaluation day AND ret252 > 0. The engine enters at that
    bar's close if flat; while in-position, repeated positive evaluations
    are no-ops (the engine's in_pos guard holds the position).
  - exit_signal = evaluation day AND NOT (ret252 > 0). The engine exits at
    that bar's close. Entry/exit are mutually exclusive by construction.
  - NO stop: backtest._stop_distance returns +inf for tsm12 (frozen spec:
    no stop). The 'atr' column is a 0.0 sentinel for the engine's NaN
    check; ATR plays no role in this strategy.
  - 'ema' sentinel column = ret252 itself: NaN during the 252-bar warmup,
    so the engine skips those bars -- the insufficient-history convention,
    same family as EMA-200's 200-bar warmup.
  - An open position at end of history is discarded by the engine
    (unclosed trades never append), identical to trials 1-39.

Methodologically distinct from the 13 Pre-Framework strategies: TSM-12 is
the first CALENDAR-SCHEDULED strategy (decisions only at month boundaries)
and the first with a 12-month formation window; every prior strategy
evaluates per-bar with windows <= 200 bars.

No per-ticker tuning. Deterministic. Zero parameters beyond
TSM12_LOOKBACK_DAYS (frozen spec).
"""
from __future__ import annotations
import pandas as pd

from config import TSM12_LOOKBACK_DAYS


def signals(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # 12-month (252 trading day) total return.
    out["ret252"] = out["close"] / out["close"].shift(TSM12_LOOKBACK_DAYS) - 1.0

    # Last trading day of each calendar month: the next bar's month differs.
    # The final bar has no next bar -> never an evaluation day.
    idx = pd.DatetimeIndex(out.index)
    month = idx.to_period("M")
    is_eval = [month[i] != month[i + 1] for i in range(len(month) - 1)] + [False]
    eval_day = pd.Series(is_eval, index=out.index)

    positive = out["ret252"] > 0

    out["entry"] = eval_day & positive
    out["exit_signal"] = eval_day & ~positive

    # Engine sentinels: _simulate skips bars where ema/atr are NaN.
    # ema := ret252 (enforces the 252-bar warmup); atr := 0.0 (unused; the
    # stop is +inf via _stop_distance).
    out["ema"] = out["ret252"]
    out["atr"] = 0.0

    return out
