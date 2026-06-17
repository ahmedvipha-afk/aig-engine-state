"""
AIG Layers 1-2 runner.

Validates a FROZEN strategy across a ticker list, per market, through the
data-integrity gate and the validation gate, with multiple-testing correction.

Offline (default): deterministic synthetic data, runs anywhere.
Live: --live uses yfinance on your machine (network required).

Examples:
  # default smoke: synthetic, EMA-200, daily, default 5-ticker list
  python run_validation.py

  # CEO production: EMA-200 1H on US halal top-30
  python run_validation.py --live --timeframe 1h \\
      --universe universe/us_halal_top30.txt --strategy ema200

  # Divergence daily on US halal top-30
  python run_validation.py --live --timeframe 1d \\
      --universe universe/us_halal_top30.txt --strategy divergence
"""

from __future__ import annotations
import argparse
import gc
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import market_of  # noqa: E402
from aig.agents import audit, reset_log  # noqa: E402
from aig.data import get_history, integrity_check  # noqa: E402
from aig.backtest import split_backtest  # noqa: E402
from aig.validation_gate import evaluate, portfolio_evaluate  # noqa: E402
from aig.provenance import provenance  # noqa: E402

DEFAULT = ["AAPL", "MSFT", "NVDA", "XOM", "BTC-USD"]


def _read_universe(path: str) -> list[str]:
    tickers: list[str] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            t = line.strip()
            if not t or t.startswith("#"):
                continue
            tickers.append(t)
    return tickers


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", nargs="+", default=None,
                    help="explicit ticker list; takes precedence over --universe")
    ap.add_argument("--universe", default=None,
                    help="path to a file with one ticker per line "
                         "(blank/# ignored)")
    ap.add_argument("--live", action="store_true",
                    help="use yfinance real data (network required)")
    ap.add_argument("--timeframe", default="1d",
                    choices=["1d", "1h", "60m", "4h", "1w"],
                    help="bar resolution")
    ap.add_argument("--strategy", default="ema200",
                    choices=["ema200", "divergence", "mbv", "dbo", "roc", "vcb"],
                    help="frozen strategy module to run")
    ap.add_argument("--out", default=None,
                    help="output JSON path (default: validation_<strategy>_<tf>.json)")
    args = ap.parse_args()

    if args.tickers:
        tickers = args.tickers
        universe_label = f"explicit({len(tickers)})"
    elif args.universe:
        tickers = _read_universe(args.universe)
        universe_label = args.universe
    else:
        tickers = DEFAULT
        universe_label = "default"

    # Self-maintaining multiple-testing N (decision_log Strand C): register this
    # run's distinct (strategy, market, timeframe) spec in the trial ledger. New
    # specs grow N (tightening the deflated-Sharpe haircut); identical re-runs are
    # idempotent. Replaces the old hardcoded n_trials_registered literal.
    from aig.trials import register_trial, market_from_universe
    register_trial(args.strategy, market_from_universe(universe_label), args.timeframe)

    offline = not args.live
    prov = provenance()

    reset_log(f"{args.strategy.upper()} validation run "
              f"(offline={offline}, tf={args.timeframe}, universe={universe_label}) "
              f"config_hash={prov['config_hash']}")
    audit("IN-O", f"provenance {json.dumps(prov)}")
    print(f"AIG Layers 1-2 — {args.strategy.upper()} validation")
    print(f"Mode: {'OFFLINE synthetic' if offline else 'LIVE yfinance'}  "
          f"| timeframe={args.timeframe} | strategy={args.strategy}")
    print(f"Universe: {universe_label} | {len(tickers)} tickers | "
          f"multiple-testing correction over all")
    print(f"config_hash={prov['config_hash']}\n")

    n_trials = len(tickers)
    results = []
    GC_EVERY = 100
    for i, tk in enumerate(tickers):
        try:
            df = get_history(tk, offline=offline, timeframe=args.timeframe)
        except Exception as e:
            print(f"  {tk:<10} DATA ERROR: {e}")
            results.append({"ticker": tk, "verdict": "DATA_ERROR",
                            "reasons": [str(e)]})
            continue
        ok, fails = integrity_check(tk, df, timeframe=args.timeframe)
        if not ok:
            print(f"  {tk:<10} BLOCKED (data integrity): {fails}")
            results.append({"ticker": tk, "verdict": "BLOCKED_DATA",
                            "reasons": fails})
            del df
            if (i + 1) % GC_EVERY == 0:
                gc.collect()
            continue
        bt = split_backtest(tk, df, timeframe=args.timeframe,
                            strategy=args.strategy)
        r = evaluate(bt, n_trials)
        results.append(r)
        tag = "[OK] PASS" if r["passed"] else "[X] fail"
        print(f"  {tk:<10} [{r['market']:<6}] {tag}  "
              f"OOS n={r['oos_n']:>3} exp={r['oos_expectancy']:>5} "
              f"dSharpe={r['oos_sharpe_deflated']:>6} "
              f"tpy={r['oos_trades_per_year']:>5}")
        if not r["passed"]:
            print(f"             reason: {r['reasons'][0]}")
        # Memory hygiene: bound peak memory on 1,600-ticker sweeps. Drop the
        # per-ticker DataFrame + backtest object explicitly and force a
        # collection every GC_EVERY tickers.
        del df, bt
        if (i + 1) % GC_EVERY == 0:
            gc.collect()

    cleared = [r for r in results if r.get("passed")]
    print(f"\nPer-ticker cleared: {len(cleared)} / {len(tickers)}")

    # Portfolio-level aggregation (the honest claim for broad-universe
    # strategies). Multi-test haircut is N_strategies, not N_tickers.
    pf = portfolio_evaluate(results, strategy=args.strategy,
                            timeframe=args.timeframe)
    print(f"\nPortfolio verdict: {pf['verdict']}")
    print(f"  trades={pf['portfolio_trades']} "
          f"contributors={pf['contributing_tickers']}/{pf['universe_size']} "
          f"(coverage {pf['universe_coverage']*100:.1f}%)")
    print(f"  exp={pf['portfolio_expectancy']:.3f}  "
          f"wr={pf['portfolio_win_rate']:.3f}  "
          f"raw Sharpe={pf['portfolio_sharpe_raw']:.3f}  "
          f"deflated={pf['portfolio_sharpe_deflated']:.3f}")
    if pf["portfolio_ci_low"] is not None:
        print(f"  95% CI on mean trade: "
              f"({pf['portfolio_ci_low']:.5f}, {pf['portfolio_ci_high']:.5f})")
    if not pf["passed"]:
        for reason in pf["reasons"]:
            print(f"  - fail: {reason}")

    out_path = args.out or f"validation_{args.strategy}_{args.timeframe}.json"
    # strip the heavy oos_trades arrays from per-ticker before saving to keep
    # JSON readable; keep them for portfolio computation above.
    results_lite = []
    for r in results:
        rl = {k: v for k, v in r.items() if k != "oos_trades"}
        results_lite.append(rl)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump({"provenance": prov, "args": vars(args),
                   "portfolio": pf, "results": results_lite},
                  fh, indent=2)
    print(f"\nAudit trail: aig/audit_trail.md")
    print(f"Full results: {out_path}")


if __name__ == "__main__":
    main()
