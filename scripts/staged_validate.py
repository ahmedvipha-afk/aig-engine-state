"""Staged-batch validation runner — CEO directive 2026-05-21 Path (a).

New strategies are validated in 200-ticker batches per sprint fire so that:
  * every fire produces visible progress (commits, dashboard updates)
  * other agents work in parallel within the same fire
  * one long task never blocks the system
  * small-market failures surface early so weak strategies get flagged
    before all 8 US batches finish

USAGE
=====

  # Pre-registration: add a strategy's 3 markets to the queue.
  python scripts/staged_validate.py --enroll vcb

  # Each sprint fire calls this to drain the next batch.
  python scripts/staged_validate.py --step

  # Status read-only (debug / dashboard).
  python scripts/staged_validate.py --status

QUEUE FILE
==========

  staged_validation_queue.json (root)
  {
    "version": 1,
    "plans": [
      {
        "trial_id": "vcb_uae_1d",
        "strategy": "vcb",
        "market": "UAE",
        "timeframe": "1d",
        "universe_file": "universe/uae_tickers_full.txt",
        "tickers": ["...",  ...],
        "batch_size": 200,
        "next_index": 0,
        "partials_dir": "staging/vcb_uae_1d",
        "status": "pending|running|complete"
      },
      ...
    ],
    "completed": [ {trial_id, completed_at}, ... ]
  }

PARTIAL FILES
=============

  staging/<trial_id>/batch_<N>.json  — one per batch, contains:
    {"batch": N, "tickers": [...], "results": [{ticker, market, oos_trades, ...}]}

  At finalization the partials are concatenated and the standard portfolio
  gate runs on the union, producing the canonical
  validation_<strategy>_<market>_<timeframe>.json the dashboard reads.

GATE INTERACTION
================

  The portfolio gate is applied ONCE at finalization, not after each batch.
  Per-batch JSONs are pure intermediate state. Provenance is bound to the
  same config_hash as the strategy pre-registration.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

QUEUE_FILE = ROOT / "staged_validation_queue.json"
STAGING_ROOT = ROOT / "staging"

BATCH_SIZE_DEFAULT = 200

# (market, universe_file) per market the engine knows.
MARKET_UNIVERSE = {
    "US": "universe/us_halal_full.txt",
    "UAE": "universe/uae_tickers_full.txt",
    "CRYPTO": "universe/halal_crypto_150_USD.txt",
}


def _now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_universe(path: Path) -> list[str]:
    out = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        t = line.strip()
        if t and not t.startswith("#"):
            out.append(t)
    # de-dupe preserving order
    seen = set()
    deduped = []
    for t in out:
        if t not in seen:
            seen.add(t)
            deduped.append(t)
    return deduped


def _load_queue() -> dict:
    if QUEUE_FILE.exists():
        try:
            return json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"version": 1, "plans": [], "completed": []}


def _save_queue(q: dict) -> None:
    QUEUE_FILE.write_text(json.dumps(q, indent=2), encoding="utf-8")


def cmd_enroll(strategy: str, batch_size: int = BATCH_SIZE_DEFAULT):
    """Add the strategy's 3 markets to the queue (UAE, CRYPTO first for early failure signal, then US)."""
    q = _load_queue()
    order = ["UAE", "CRYPTO", "US"]  # small markets first per CEO spec
    existing = {p["trial_id"] for p in q["plans"]} | {c["trial_id"] for c in q.get("completed", [])}
    added = []
    for market in order:
        trial_id = f"{strategy}_{market.lower()}_1d"
        if trial_id in existing:
            print(f"  [skip] {trial_id} already in queue or completed")
            continue
        uni_path = ROOT / MARKET_UNIVERSE[market]
        tickers = _read_universe(uni_path)
        partials_dir = f"staging/{trial_id}"
        (ROOT / partials_dir).mkdir(parents=True, exist_ok=True)
        plan = {
            "trial_id": trial_id,
            "strategy": strategy,
            "market": market,
            "timeframe": "1d",
            "universe_file": MARKET_UNIVERSE[market],
            "tickers": tickers,
            "batch_size": batch_size,
            "next_index": 0,
            "partials_dir": partials_dir,
            "status": "pending",
            "enrolled_at": _now_iso(),
        }
        q["plans"].append(plan)
        added.append(trial_id)
        print(f"  enrolled {trial_id} ({len(tickers)} tickers, batch={batch_size})")
    _save_queue(q)
    print(f"\nEnrollment complete. {len(added)} trial(s) queued.")
    return added


def _run_batch(plan: dict) -> dict:
    """Run the next batch for this plan. Returns the batch dict written to partial JSON."""
    import gc
    from aig.data import get_history, integrity_check
    from aig.backtest import split_backtest
    from aig.validation_gate import evaluate
    from aig.agents import audit
    from aig.provenance import provenance

    prov = provenance()
    start = plan["next_index"]
    end = min(start + plan["batch_size"], len(plan["tickers"]))
    batch_tickers = plan["tickers"][start:end]
    batch_n = start // plan["batch_size"]
    strategy = plan["strategy"]
    timeframe = plan["timeframe"]

    print(f"  running {plan['trial_id']} batch {batch_n} "
          f"(tickers[{start}:{end}], {len(batch_tickers)} names) "
          f"under config_hash={prov['config_hash']}")

    results = []
    n_trials_universe = len(plan["tickers"])  # per-ticker haircut uses the full universe
    for tk in batch_tickers:
        try:
            df = get_history(tk, offline=False, timeframe=timeframe)
        except Exception as e:
            results.append({"ticker": tk, "verdict": "DATA_ERROR", "reasons": [str(e)]})
            continue
        ok, fails = integrity_check(tk, df, timeframe=timeframe)
        if not ok:
            results.append({"ticker": tk, "verdict": "BLOCKED_DATA", "reasons": fails})
            del df
            continue
        bt = split_backtest(tk, df, timeframe=timeframe, strategy=strategy)
        r = evaluate(bt, n_trials_universe)
        results.append(r)
        del df, bt
    # Memory hygiene: force collection at end of batch so the next sprint
    # fire starts with a clean working set.
    gc.collect()

    out = {
        "batch": batch_n,
        "start_index": start,
        "end_index": end,
        "tickers": batch_tickers,
        "results": results,
        "config_hash": prov["config_hash"],
        "timestamp": _now_iso(),
    }
    partial_file = ROOT / plan["partials_dir"] / f"batch_{batch_n:03d}.json"
    partial_file.write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out


def _finalize_plan(plan: dict) -> dict:
    """Aggregate partials, run portfolio gate, write canonical validation JSON."""
    from aig.validation_gate import portfolio_evaluate
    from aig.provenance import provenance

    prov = provenance()
    partials_dir = ROOT / plan["partials_dir"]
    all_results = []
    for f in sorted(partials_dir.glob("batch_*.json")):
        b = json.loads(f.read_text(encoding="utf-8"))
        all_results.extend(b["results"])
    pf = portfolio_evaluate(all_results, strategy=plan["strategy"], timeframe=plan["timeframe"])

    # strip heavy oos_trades arrays to keep canonical JSON readable
    lite = []
    for r in all_results:
        if isinstance(r, dict):
            lite.append({k: v for k, v in r.items() if k != "oos_trades"})
        else:
            lite.append(r)

    out_path = ROOT / f"validation_{plan['strategy']}_{plan['market'].lower()}_{plan['timeframe']}.json"
    final = {
        "provenance": prov,
        "args": {
            "strategy": plan["strategy"],
            "timeframe": plan["timeframe"],
            "universe": plan["universe_file"],
            "live": True,
            "staged": True,
            "batches": len(list(partials_dir.glob("batch_*.json"))),
        },
        "portfolio": pf,
        "results": lite,
    }
    out_path.write_text(json.dumps(final, indent=2), encoding="utf-8")
    print(f"  finalized {plan['trial_id']} -> {out_path.name}")
    print(f"  portfolio verdict: {pf.get('verdict')} (passed={pf.get('passed')})")
    print(f"  trades={pf.get('portfolio_trades')} exp={pf.get('portfolio_expectancy')} "
          f"dSh={pf.get('portfolio_sharpe_deflated')}")
    return pf


def cmd_step():
    """Process the next pending plan: run one batch OR finalize if all batches done."""
    q = _load_queue()
    pending = [p for p in q["plans"] if p["status"] in ("pending", "running")]
    if not pending:
        print("staged queue empty. Nothing to do.")
        return None
    plan = pending[0]
    plan["status"] = "running"

    total = len(plan["tickers"])
    if plan["next_index"] >= total:
        # Finalize
        pf = _finalize_plan(plan)
        plan["status"] = "complete"
        plan["completed_at"] = _now_iso()
        plan["portfolio_verdict"] = pf.get("verdict")
        plan["portfolio_passed"] = pf.get("passed")
        q.setdefault("completed", []).append({
            "trial_id": plan["trial_id"],
            "completed_at": plan["completed_at"],
            "portfolio_verdict": pf.get("verdict"),
            "portfolio_passed": pf.get("passed"),
        })
        q["plans"] = [p for p in q["plans"] if p["trial_id"] != plan["trial_id"]]
        _save_queue(q)
        return {"action": "finalized", "trial_id": plan["trial_id"], "verdict": pf}

    # Run one batch
    batch = _run_batch(plan)
    plan["next_index"] = batch["end_index"]
    progress_pct = plan["next_index"] / max(total, 1) * 100
    print(f"  progress {plan['next_index']}/{total} ({progress_pct:.1f}%)")
    _save_queue(q)
    return {"action": "batch_done", "trial_id": plan["trial_id"],
            "batch": batch["batch"], "progress_pct": progress_pct}


def cmd_status():
    q = _load_queue()
    plans = q.get("plans", [])
    completed = q.get("completed", [])
    print(f"Active plans: {len(plans)}")
    for p in plans:
        total = len(p["tickers"])
        pct = p["next_index"] / max(total, 1) * 100
        print(f"  {p['trial_id']:30s} {p['status']:8s} {p['next_index']}/{total} ({pct:.1f}%)")
    print(f"\nCompleted plans: {len(completed)}")
    for c in completed[-10:]:
        print(f"  {c['trial_id']:30s} {c.get('portfolio_verdict','?')} @ {c.get('completed_at','?')}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--enroll", help="enroll a strategy id (queues UAE+CRYPTO+US plans)")
    ap.add_argument("--step", action="store_true", help="run next batch or finalize next pending plan")
    ap.add_argument("--status", action="store_true", help="print queue state")
    ap.add_argument("--batch-size", type=int, default=BATCH_SIZE_DEFAULT)
    args = ap.parse_args()

    if args.enroll:
        cmd_enroll(args.enroll, batch_size=args.batch_size)
    elif args.step:
        result = cmd_step()
        if result:
            print(f"\nstep result: {result.get('action')} on {result.get('trial_id')}")
    else:
        cmd_status()


if __name__ == "__main__":
    main()
