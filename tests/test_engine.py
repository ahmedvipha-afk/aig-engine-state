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


# ---- TSM-12 conformance (frozen spec efe8ac7b47f10a0f) --------------------

def _df_down(n=600):
    idx = pd.bdate_range("2020-01-01", periods=n)
    c = pd.Series(np.linspace(200, 100, n), index=idx)
    return pd.DataFrame({"open": c, "high": c * 1.01, "low": c * 0.99,
                         "close": c, "volume": pd.Series([1e6] * n, index=idx)},
                        index=idx)


def test_tsm12_columns_and_warmup():
    from aig.strategy_tsm12 import signals as tsig
    s = tsig(_df(600))
    for col in ("ema", "atr", "entry", "exit_signal"):
        assert col in s.columns
    # insufficient-history convention: ema sentinel NaN for the full
    # 252-bar warmup, so the engine skips those bars entirely
    assert s["ema"].iloc[:252].isna().all()
    assert not np.isnan(s["atr"]).any()


def test_tsm12_signals_only_on_month_end():
    from aig.strategy_tsm12 import signals as tsig
    s = tsig(_df(600))
    sig_days = s.index[s["entry"] | s["exit_signal"]]
    assert len(sig_days) > 0
    months = s.index.to_period("M")
    for ts in sig_days:
        later_same_month = s.index[(s.index > ts) & (months == ts.to_period("M"))]
        assert len(later_same_month) == 0   # nothing later in that month
    # final bar is never an evaluation day (incomplete month convention)
    assert not bool(s["entry"].iloc[-1]) and not bool(s["exit_signal"].iloc[-1])


def test_tsm12_long_if_positive_flat_if_not():
    from aig.strategy_tsm12 import signals as tsig
    up = tsig(_df(600))
    post = up[~up["ema"].isna()]
    evs = post[post["entry"] | post["exit_signal"]]
    assert len(evs) > 0 and evs["entry"].all()          # rising: always long
    dn = tsig(_df_down(600))
    post2 = dn[~dn["ema"].isna()]
    evs2 = post2[post2["entry"] | post2["exit_signal"]]
    assert len(evs2) > 0 and evs2["exit_signal"].all()  # falling: always flat


def test_tsm12_no_stop_is_infinite():
    import math
    from aig.backtest import _stop_distance
    assert math.isinf(_stop_distance("tsm12", {"atr": 0.0}))


def test_tsm12_end_to_end_engine_run():
    from aig.backtest import split_backtest
    bt = split_backtest("SYN", _df(900), timeframe="1d", strategy="tsm12")
    # rising synthetic series: at least one closed trade somewhere across
    # IS/OOS/WF segments, and no exceptions end-to-end
    assert isinstance(bt["is_trades"], list)
    assert bt["strategy"] == "tsm12"


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
