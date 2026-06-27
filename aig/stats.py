"""
Statistics for the validation gate (Layer B items 2 & 9).

- expectancy ratio: (avgWin*WR)/(avgLoss*LR)
- annualised Sharpe of per-trade returns (approx, trade-frequency aware)
- bootstrap CI on mean trade return
- deflated Sharpe ratio + Bonferroni alpha when many tickers are tested
"""

from __future__ import annotations
import numpy as np

from config import GATE, RANDOM_SEED


def expectancy(trades: list[float]) -> float:
    if not trades:
        return 0.0
    t = np.array(trades)
    wins, losses = t[t > 0], t[t < 0]
    if len(wins) == 0 or len(losses) == 0:
        return 0.0 if len(wins) == 0 else float("inf")
    wr, lr = len(wins) / len(t), len(losses) / len(t)
    return float((wins.mean() * wr) / (abs(losses.mean()) * lr))


def sharpe(trades: list[float], trades_per_year: float = 25.0) -> float:
    """Annualised Sharpe of per-trade returns. trades_per_year must reflect
    actual observed trade frequency (caller computes it from data span)."""
    if len(trades) < 2:
        return 0.0
    t = np.array(trades)
    sd = t.std(ddof=1)
    if sd == 0:
        return 0.0
    return float(t.mean() / sd * np.sqrt(max(trades_per_year, 1.0)))


def bootstrap_ci(trades: list[float]) -> tuple[float, float]:
    if len(trades) < GATE["min_trades"]:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(RANDOM_SEED)
    t = np.array(trades)
    means = [rng.choice(t, len(t), replace=True).mean()
             for _ in range(GATE["bootstrap_iters"])]
    lo = (1 - GATE["bootstrap_conf"]) / 2
    return (float(np.quantile(means, lo)), float(np.quantile(means, 1 - lo)))


def deflated_sharpe(sr: float, n_trials: int) -> float:
    """Bailey & Lopez de Prado style haircut: more trials -> higher bar."""
    if n_trials <= 1:
        return sr
    # expected max Sharpe under the null grows ~ sqrt(2 ln n_trials)
    haircut = np.sqrt(2 * np.log(max(n_trials, 2))) * 0.25
    return sr - haircut


def bonferroni_alpha(n_tests: int) -> float:
    return GATE["alpha"] / max(n_tests, 1)


def trade_moments(trades: list[float]) -> tuple[float, float]:
    """Returns (Fisher skewness, Fisher excess kurtosis) of trade returns.
    Uses population std (ddof=0) for moment standardisation.
    Returns (0.0, 0.0) for fewer than 4 trades or zero variance.
    """
    if len(trades) < 4:
        return (0.0, 0.0)
    t = np.array(trades, dtype=float)
    mean = t.mean()
    std = t.std(ddof=0)
    if std == 0.0:
        return (0.0, 0.0)
    z = (t - mean) / std
    skew = float(np.mean(z ** 3))
    excess_kurtosis = float(np.mean(z ** 4) - 3.0)
    return (skew, excess_kurtosis)
