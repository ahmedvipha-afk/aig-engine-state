"""
THE VALIDATION GATE — non-negotiable (same hard status as Shariah & Tier-1 CBs).

A ticker/strategy is CLEARED FOR PAPER-FORWARD only if it passes every check
on OUT-OF-SAMPLE data, after realistic costs, with the multiple-testing
correction applied. Default verdict is FAIL. There is no override.

"Cleared for paper-forward" is NOT "proven" — it has only earned the right to
be watched live on paper. (Accepted language, per Decision 1.)
"""

from __future__ import annotations

import numpy as np

from config import GATE, PORTFOLIO_GATE
from aig.stats import (expectancy, sharpe, bootstrap_ci,
                       deflated_sharpe, bonferroni_alpha)
from aig.agents import audit


def evaluate(bt: dict, n_trials: int) -> dict:
    """bt = output of backtest.split_backtest. n_trials = total tickers tested."""
    oos = bt["oos_trades"]
    wf = bt["wf_trades"]
    tk = bt["ticker"]
    tpy = bt.get("oos_trades_per_year", 25.0)
    reasons: list[str] = []

    n_oos = len(oos)
    if n_oos < GATE["min_trades"]:
        reasons.append(f"OOS trades {n_oos} < {GATE['min_trades']}")

    exp = expectancy(oos)
    if exp < GATE["min_expectancy"]:
        reasons.append(f"OOS expectancy {exp:.2f} < {GATE['min_expectancy']}")

    sr = sharpe(oos, trades_per_year=tpy)
    dsr = deflated_sharpe(sr, n_trials)
    if dsr < GATE["min_oos_sharpe"]:
        reasons.append(f"deflated OOS Sharpe {dsr:.2f} < {GATE['min_oos_sharpe']} "
                       f"(raw {sr:.2f}, {n_trials} trials)")

    lo, hi = bootstrap_ci(oos)
    if not (lo == lo) or lo <= 0:   # NaN or non-positive lower bound
        reasons.append(f"95% CI lower bound on mean trade not > 0 (lo={lo})")

    # walk-forward must also be non-negative in aggregate expectancy
    if wf and expectancy(wf) < 1.0:
        reasons.append(f"walk-forward expectancy {expectancy(wf):.2f} < 1.0")

    a = bonferroni_alpha(n_trials)
    passed = len(reasons) == 0
    verdict = "CLEARED_FOR_PAPER_FORWARD" if passed else "FAIL"
    audit("RD-D", f"{tk}[{bt.get('strategy','?')}@{bt.get('timeframe','?')}]: {verdict}"
                  + ("" if passed else f" — {reasons}")
                  + f" | OOS n={n_oos} exp={exp:.2f} dSharpe={dsr:.2f} "
                    f"CI=({lo:.4f},{hi:.4f}) tpy={tpy} alpha={a:.4f}")
    return {"ticker": tk, "market": bt["market"], "verdict": verdict,
            "passed": passed, "oos_n": n_oos,
            "timeframe": bt.get("timeframe"),
            "strategy": bt.get("strategy"),
            "oos_trades_per_year": tpy,
            "oos_expectancy": round(exp, 3),
            "oos_sharpe_raw": round(sr, 3), "oos_sharpe_deflated": round(dsr, 3),
            "ci_low": None if lo != lo else round(lo, 5),
            "oos_trades": bt["oos_trades"],  # carried for portfolio aggregation
            "reasons": reasons}


def portfolio_evaluate(per_ticker_results: list[dict],
                       strategy: str, timeframe: str,
                       n_trials: int | None = None,
                       n_strategies: int | None = None) -> dict:
    """Aggregate per-ticker OOS trades into a portfolio-level verdict.

    Rationale: per-ticker gates are statistically pessimistic for
    broad-universe strategies — the multi-testing haircut scales with
    N_tickers (3000+ for our halal universe) and crushes any per-name
    Sharpe. The honest claim is portfolio-level: "across this universe,
    after costs, the strategy has positive expectancy and Sharpe > 0.5
    on the aggregate trade stream." Multi-testing is then applied at the
    TRIAL count (strategy × market × timeframe combinations
    pre-registered, not ticker count).

    Per auditor 2026-05-21: the haircut MUST account for every trial in
    the pre-registered budget, including failing ones. n_trials must
    reflect the full claim set, not the winning subset.
    """
    g = PORTFOLIO_GATE
    # back-compat shim: old callers passed n_strategies; treat as alias.
    n_trials_val = (n_trials if n_trials is not None
                    else n_strategies if n_strategies is not None
                    else g.get("n_trials_registered", g.get("n_strategies_registered", 2)))
    n_strats = n_trials_val
    # only count tickers that produced trades (others are noise carriers)
    contributors = [r for r in per_ticker_results
                    if isinstance(r, dict) and r.get("oos_trades")]
    n_universe = len([r for r in per_ticker_results
                      if isinstance(r, dict) and r.get("verdict") not in
                      ("BLOCKED_DATA", "DATA_ERROR")])

    all_trades: list[float] = []
    total_tpy = 0.0
    per_ticker_net: list[float] = []   # R2: per-ticker net P&L (Σ OOS trade returns)
    for r in contributors:
        tr = r["oos_trades"]
        all_trades.extend(tr)
        total_tpy += float(r.get("oos_trades_per_year", 0.0) or 0.0)
        per_ticker_net.append(float(sum(tr)))

    reasons: list[str] = []
    n_total = len(all_trades)
    if n_total < g["min_trades"]:
        reasons.append(f"portfolio trades {n_total} < {g['min_trades']}")

    exp = expectancy(all_trades)
    if exp < g["min_expectancy"]:
        reasons.append(f"portfolio expectancy {exp:.3f} < {g['min_expectancy']}")

    arr = np.array(all_trades) if all_trades else np.array([0.0])
    wr = float((arr > 0).sum() / len(arr)) if len(arr) > 0 else 0.0
    if wr < g["min_win_rate"]:
        reasons.append(f"portfolio win rate {wr:.3f} < {g['min_win_rate']}")

    coverage = (len(contributors) / max(n_universe, 1)) if n_universe else 0.0
    if coverage < g["min_universe_coverage"]:
        reasons.append(f"universe coverage {coverage:.3f} < "
                       f"{g['min_universe_coverage']} "
                       f"({len(contributors)}/{n_universe} tickers traded)")

    # R2 (Strand C): single-name P&L concentration cap. No single ticker may
    # contribute more than max_single_name_pnl_share of total NET portfolio P&L.
    # Guards: only meaningful when total net P&L > 0 (a net-negative strategy is
    # already caught by the expectancy rule, so we do not double-penalise it).
    total_net = sum(per_ticker_net)
    max_name_share = ((max(per_ticker_net) / total_net)
                      if (per_ticker_net and total_net > 0) else 0.0)
    if max_name_share > g["max_single_name_pnl_share"]:
        reasons.append(f"single-name P&L concentration {max_name_share:.3f} > "
                       f"{g['max_single_name_pnl_share']} "
                       f"(most-concentrated ticker carries too much of the edge)")

    # aggregate Sharpe annualised by SUM of trades-per-year across contributors
    sr = sharpe(all_trades, trades_per_year=max(total_tpy, 1.0))
    dsr = deflated_sharpe(sr, n_strats)   # strategy-level multi-test haircut
    if dsr < g["min_oos_sharpe"]:
        reasons.append(f"portfolio deflated Sharpe {dsr:.3f} < "
                       f"{g['min_oos_sharpe']} (raw {sr:.3f}, "
                       f"{n_strats} strategies)")

    lo, hi = bootstrap_ci(all_trades) if n_total >= 30 else (float("nan"),
                                                              float("nan"))
    if not (lo == lo) or lo <= 0:
        reasons.append(f"95% CI lower bound on mean trade not > 0 (lo={lo})")

    passed = len(reasons) == 0
    verdict = "PORTFOLIO_CLEARED_FOR_PAPER_FORWARD" if passed else "PORTFOLIO_FAIL"
    audit("RD-D", f"PORTFOLIO[{strategy}@{timeframe}]: {verdict}"
          + ("" if passed else f" — {reasons}")
          + f" | trades={n_total} contributors={len(contributors)}/{n_universe} "
            f"exp={exp:.3f} sr={sr:.3f} dsr={dsr:.3f} wr={wr:.3f} "
            f"CI=({lo:.5f},{hi:.5f}) n_trials={n_strats}")
    return {
        "strategy": strategy, "timeframe": timeframe,
        "verdict": verdict, "passed": passed,
        "portfolio_trades": n_total,
        "contributing_tickers": len(contributors),
        "universe_size": n_universe,
        "universe_coverage": round(coverage, 4),
        "portfolio_expectancy": round(exp, 4),
        "portfolio_win_rate": round(wr, 4),
        "portfolio_sharpe_raw": round(sr, 4),
        "portfolio_sharpe_deflated": round(dsr, 4),
        "portfolio_ci_low": None if lo != lo else round(lo, 6),
        "portfolio_ci_high": None if hi != hi else round(hi, 6),
        "max_single_name_pnl_share": round(max_name_share, 4),  # R2 diagnostic
        "n_trials_haircut": n_strats,
        "n_strategies_haircut": n_strats,  # back-compat alias for old callers
        "reasons": reasons,
    }
