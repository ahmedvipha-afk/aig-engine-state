"""Conformance tests for the TRB-50 paper-forward detector (entry 50).

Covers the forward-specific mechanics that the engine conformance tests
(test_engine.py) do NOT cover: Amendment-A single-source-of-truth,
the bar-count fixed-hold exit, the no-new-bar idempotency no-op, the
no-stop convention, and the same-bar re-entry guard.

Run: python tests/test_paper_forward_trb50.py
"""
import importlib.util
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

# Load the detector module by path (it lives in scripts/, not a package).
_spec = importlib.util.spec_from_file_location(
    "pf_trb50", os.path.join(ROOT, "scripts", "paper_forward_trb50.py"))
pf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pf)

import aig.strategy_trb50 as engine
from config import TRB50_HOLD_DAYS


def _df(closes):
    idx = pd.bdate_range("2020-01-01", periods=len(closes))
    c = pd.Series(closes, index=idx, dtype=float)
    return pd.DataFrame({"open": c, "high": c * 1.01, "low": c * 0.99,
                         "close": c, "volume": pd.Series([1e6] * len(c), index=idx)},
                        index=idx)


def test_amendment_a_signals_is_engine_module():
    # The detector's signal function must BE the engine module's function,
    # not a copy — single source of truth for the frozen spec.
    assert pf.signals is engine.signals


def test_bars_held_counts_bars_strictly_after_entry():
    df = _df([100.0] * 30)
    # entry on the bar at index 20 -> 9 bars strictly after it (indices 21..29)
    entry_date = df.index[20].date().isoformat()
    assert pf._bars_held(df, entry_date) == 9
    # entry on the last bar -> 0 bars after
    assert pf._bars_held(df, df.index[-1].date().isoformat()) == 0


def test_exit_due_at_exactly_hold_days():
    assert not pf._exit_due(TRB50_HOLD_DAYS - 1)
    assert pf._exit_due(TRB50_HOLD_DAYS)          # exit at the Nth bar
    assert pf._exit_due(TRB50_HOLD_DAYS + 3)      # late catch-up still exits


def test_no_new_bar_is_idempotent():
    # Same history evaluated twice yields the same bars_held -> no spurious
    # state change. (bars_held is a pure function of df + entry_date.)
    df = _df([100.0] * 25)
    ed = df.index[10].date().isoformat()
    assert pf._bars_held(df, ed) == pf._bars_held(df, ed)


def test_same_bar_reentry_guard():
    state = {"history": [{"ticker": "AAA", "exit_date": "2020-02-10"}]}
    # an entry attempt on the same bar the position just exited is blocked
    assert pf._exited_same_bar(state, "AAA", "2020-02-10") is True
    # a later bar is allowed
    assert pf._exited_same_bar(state, "AAA", "2020-02-11") is False
    # a ticker with no history is allowed
    assert pf._exited_same_bar(state, "BBB", "2020-02-10") is False


def test_no_stop_convention_in_open_position_shape():
    # The detector records stop_price=None for TRB-50 entries (frozen spec:
    # no stop). Assert the module never computes a stop distance.
    src = open(os.path.join(ROOT, "scripts", "paper_forward_trb50.py"),
               encoding="utf-8").read()
    assert "_stop_distance" not in src
    assert '"stop_price": None' in src


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL {fn.__name__}: {e}")
    print(f"\n{passed}/{len(fns)} tests passed")
    sys.exit(0 if passed == len(fns) else 1)
