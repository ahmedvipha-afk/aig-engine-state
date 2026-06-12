"""TRB-50 — Trading Range Breakout, 50-day window (long only).

FROZEN spec (pre-registered 2026-06-12, trial 41, spec_hash a96ccdf5c0640e4f;
canonical spec text + hash derivation in strategy_register.md, params in
config.py per Path 2d-A). Source: Brock, Lakonishok & LeBaron 1992 (Journal
of Finance) Trading Range Breakout rule — window=50, band=1%, 10-day
post-signal window, all from the paper's published rule set.

Signal: resistance = max(close) over the prior 50 trading days, shifted
1 bar (look-ahead-free, trials 1-39 convention). ENTRY when
close > (1 + 0.01) * resistance, evaluated while flat. Fixed hold: exit at
the close of the 10th trading day after the entry bar (the paper's
measurement window). Long-only, no stop, no leverage; re-entry only on a
fresh breakout evaluation after going flat.

Engine mapping (edge-case conventions inherited from trials 1-40; each is
documented in the trial's verdict decision_log entry):
  - The fixed-N-day hold cannot be expressed as a stateless per-row
    exit condition, so this module runs a deterministic single-pass
    position simulation that EXACTLY mirrors the engine's state machine
    (enter at close of the first flat bar with entry=True; exit
    processing starts the next bar; entry flags while in-position are
    no-ops): entry is marked only on bars where the engine would
    actually enter, and exit_signal is marked exactly 10 bars after
    each such entry. First strategy with a position-aware signal pass;
    determinism and engine-equivalence are asserted by conformance
    tests.
  - entry  = flat AND close > (1 + TRB50_BAND) * resistance. The spec
    string freezes a LEVEL condition (close>(1+band)*resistance), not a
    cross condition; because resistance is the trailing close-max, the
    level is a de-facto penetration event. Evaluated only while flat.
  - exit_signal = bar index == entry_index + TRB50_HOLD_DAYS. Exit at
    that bar's close. The engine cannot exit and re-enter on the same
    bar (elif branch); earliest re-entry is the following bar — the
    simulation reproduces this by construction.
  - NO stop: backtest._stop_distance returns +inf for trb50 (frozen
    spec: no stop). The 'atr' column is a 0.0 sentinel for the engine's
    NaN check; ATR plays no role in this strategy.
  - 'ema' sentinel column = resistance itself: NaN during the 50-bar
    warmup (shift(1) + rolling(50)), so the engine skips those bars --
    the insufficient-history convention, same family as EMA-200's
    200-bar warmup. The simulation skips the same bars.
  - An open position at end of history (entry within the last 10 bars)
    gets no exit_signal; the engine discards unclosed trades, identical
    to trials 1-40.

Methodologically distinct from DBO (the Pre-Framework breakout): DBO uses
high/low Donchian channels (20/10), volume confirmation, an ATR stop, and
an open-ended channel exit; TRB-50 uses the close-max level with a 1% band,
no volume condition, no stop, and a fixed calendar-free 10-bar hold.

No per-ticker tuning. Deterministic. Zero parameters beyond
TRB50_WINDOW_DAYS / TRB50_BAND / TRB50_HOLD_DAYS (frozen spec).
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from config import TRB50_WINDOW_DAYS, TRB50_BAND, TRB50_HOLD_DAYS


def signals(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # Trailing 50-day close-max, shifted so the current bar's close never
    # contaminates the level it is tested against (look-ahead-free).
    resistance = out["close"].shift(1).rolling(TRB50_WINDOW_DAYS).max()
    out["resistance"] = resistance

    level = (1.0 + TRB50_BAND) * resistance
    breakout = (out["close"] > level).to_numpy()
    res_vals = resistance.to_numpy()

    n = len(out)
    entry = np.zeros(n, dtype=bool)
    exit_sig = np.zeros(n, dtype=bool)

    in_pos = False
    exit_idx = -1
    for i in range(n):
        if np.isnan(res_vals[i]):
            continue                      # warmup: engine skips these bars
        if not in_pos:
            if breakout[i]:
                entry[i] = True
                in_pos = True
                exit_idx = i + TRB50_HOLD_DAYS
        elif i == exit_idx:
            exit_sig[i] = True
            in_pos = False
    # in_pos True past end of data -> open position, discarded by engine.

    out["entry"] = entry
    out["exit_signal"] = exit_sig

    # Engine sentinels: _simulate skips bars where ema/atr are NaN.
    # ema := resistance (enforces the 50-bar warmup); atr := 0.0 (unused;
    # the stop is +inf via _stop_distance).
    out["ema"] = out["resistance"]
    out["atr"] = 0.0

    return out
