"""
Engine regression tests (Layer B item 7).
Run: python -m pytest tests/ -q   (or: python tests/test_engine.py)
"""
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from aig.strategy_ema200 import ema, atr, signals
from aig.costs import round_trip_cost_frac
from aig.stats import expectancy, sharpe, deflated_sharpe, bonferroni_alpha
from aig.validation_gate import evaluate


def _df(n=400):
    idx = pd.bdate_range("2020-01-01", periods=n)
    c = pd.Series(np.linspace(100, 200, n), index=idx)
    return pd.DataFrame({"open": c, "high": c * 1.01, "low": c * 0.99,
                         "close": c, "volume": pd.Series([1e6] * n, index=idx)},
                        index=idx)


def test_ema_monotone_uptrend_below_price():
    d = _df()
    e = ema(d["close"], 50)
    assert e.iloc[-1] < d["close"].iloc[-1]   # EMA lags a rising series


def test_atr_positive():
    d = _df()
    a = atr(d, 14).dropna()
    assert (a >= 0).all()


def test_signals_columns():
    s = signals(_df())
    for col in ("ema", "atr", "entry", "exit_signal"):
        assert col in s.columns


def test_costs_ordering():
    assert (round_trip_cost_frac("US")
            < round_trip_cost_frac("UAE"))
    assert round_trip_cost_frac("CRYPTO") > 0


def test_expectancy_basic():
    assert expectancy([0.1, 0.1, -0.05]) > 1.0
    assert expectancy([]) == 0.0


def test_sharpe_zero_on_constant():
    assert sharpe([0.01, 0.01, 0.01]) == 0.0


def test_deflated_sharpe_haircut():
    assert deflated_sharpe(2.0, 100) < 2.0
    assert deflated_sharpe(2.0, 1) == 2.0


def test_bonferroni():
    assert bonferroni_alpha(10) < bonferroni_alpha(1)


def test_gate_defaults_fail_on_no_trades():
    bt = {"ticker": "X", "market": "US", "cost_frac": 0.0,
          "is_trades": [], "oos_trades": [], "wf_trades": []}
    r = evaluate(bt, 5)
    assert r["passed"] is False


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
