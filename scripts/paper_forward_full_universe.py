"""AIG Paper-Forward Detector — FULL VALIDATED UNIVERSE (Phase 1 directive F3).

DORMANT since 2026-05-26; routing reconciled 2026-06-13 (entry 50 Amendment B).
The LIVE detectors driven by sprint fires are paper_forward_divergence.py
(slot 1) and paper_forward_trb50.py (slot 2). winners_assignment.json now
routes only {divergence, trb50}; Pre-Framework mbv/pmr/str were tagged out
and their 5 open paper positions administratively closed (state key
`administratively_closed_preframework`). Do NOT run this script for trb50
without porting the fixed-hold exit state from paper_forward_trb50.py —
its generic exit logic does not implement the 10-day bar-count hold (an
assignment routed here to trb50 degrades to errors_n, not to wrong exits).

Reads `winners_assignment.json` for the (ticker → strategy) mapping built by
`reassign_best_strategy.py`. For each assigned ticker, runs that strategy's
signals against today's bars and detects entry/exit events.

Differs from `paper_forward_divergence.py` by:
- Watching the FULL cleared universe (1,101 tickers as of 2026-05-21)
  instead of the pre-registered 5-ticker subset.
- Routing each ticker through ITS assigned strategy (divergence or mbv)
  per the best-per-ticker mapping.
- Capping Telegram alerts to top-N per session by per-ticker dSharpe
  (default N=10). Full list always written to JSON for dashboard.

Idempotent: re-running on the same day with no new signals is a no-op
(deduped by (ticker, signal_date)).

Output files:
  - paper_forward_positions_full.json  (per-ticker state + session summary)
  - signals_log.md                      (human-readable journal)

Constraints:
  - Rule 01 paper-only, Rule 15 long-only, Rule 16 no leverage.
  - Selection is deterministic from winners_assignment.json (no cherry-pick).
"""
from __future__ import annotations
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aig.data import get_history, integrity_check
from config import market_of  # noqa: F401

try:
    from scripts.telegram_send import send_message
    TELEGRAM_AVAILABLE = True
except Exception:
    try:
        sys.path.insert(0, str(ROOT / "scripts"))
        from telegram_send import send_message
        TELEGRAM_AVAILABLE = True
    except Exception:
        TELEGRAM_AVAILABLE = False

GST = timezone(timedelta(hours=4))
ASSIGNMENT_FILE = ROOT / "winners_assignment.json"
STATE_FILE = ROOT / "paper_forward_positions_full.json"
SIGNALS_LOG = ROOT / "signals_log.md"

TG_CAP = 10                # Telegram alerts per session (top by dSharpe)
MAX_TICKERS_PER_FIRE = 250 # Throttle to keep within 14-min budget; cycles via offset


def _strategy_signals(strategy: str, df: pd.DataFrame) -> pd.DataFrame:
    if strategy == "divergence":
        from aig.strategy_divergence import signals
        return signals(df)
    if strategy == "mbv":
        from aig.strategy_mbv import signals
        return signals(df)
    if strategy == "ema200":
        from aig.strategy_ema200 import signals
        return signals(df)
    raise ValueError(f"unknown strategy: {strategy}")


def _stop_distance(strategy: str, row) -> float:
    from config import STOP_ATR_MULT, DIV_STOP_ATR_MULT, MBV_STOP_ATR_MULT
    atr = float(row.get("atr") or 0)
    if strategy == "divergence":
        return float(row.get("stop_dist", DIV_STOP_ATR_MULT * atr))
    if strategy == "mbv":
        return MBV_STOP_ATR_MULT * atr
    return STOP_ATR_MULT * atr


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "schema": 2,
        "config_hash_at_deploy": None,
        "deployed_at": None,
        "open_positions": {},       # ticker -> {entry_date, entry_price, strategy, stop_price, dsharpe}
        "history": [],
        "last_run": None,
        "last_run_summary": "",
        "last_offset": 0,            # next-fire starts here for cycling through universe
        "session_alerts_sent": 0,
        "skipped_telegrams": [],     # tickers whose signals fired but were dropped by TG cap
    }


def _save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _append_signals_log(lines: list[str]):
    now = datetime.now(GST).strftime("%Y-%m-%d %H:%M GST")
    block = f"\n## {now} — Paper-Forward Full Universe\n" + "\n".join(lines) + "\n"
    if SIGNALS_LOG.exists():
        existing = SIGNALS_LOG.read_text(encoding="utf-8")
    else:
        existing = "# AIG Signals Log\n\n"
    SIGNALS_LOG.write_text(existing + block, encoding="utf-8")


def _tg(msg: str):
    if not TELEGRAM_AVAILABLE:
        return
    try:
        send_message(msg, parse_mode="HTML")
    except Exception:
        pass


def detect():
    if not ASSIGNMENT_FILE.exists():
        print(f"ERROR: {ASSIGNMENT_FILE.name} not found. Run reassign_best_strategy.py first.")
        return {"ok": False, "summary": "no assignment file"}

    asn = json.loads(ASSIGNMENT_FILE.read_text(encoding="utf-8"))
    assignments: dict = asn.get("assignments") or {}
    if not assignments:
        return {"ok": False, "summary": "no assignments"}

    state = _load_state()
    if state["deployed_at"] is None:
        try:
            from aig.provenance import provenance
            state["config_hash_at_deploy"] = provenance()["config_hash"]
        except Exception:
            state["config_hash_at_deploy"] = "unknown"
        state["deployed_at"] = datetime.now(GST).isoformat(timespec="seconds")

    # Order tickers by assigned dSharpe (best first) so highest-priority always
    # gets evaluated within the per-fire throttle.
    ranked = sorted(assignments.keys(),
                    key=lambda tk: -float(assignments[tk].get("dsharpe") or -99))

    # Cycle through universe across fires — start where last fire left off.
    n = len(ranked)
    offset = state.get("last_offset", 0) % n
    cycle = ranked[offset:] + ranked[:offset]
    batch = cycle[:MAX_TICKERS_PER_FIRE]
    next_offset = (offset + len(batch)) % n
    state["last_offset"] = next_offset

    today = datetime.now(GST).date().isoformat()
    log_lines = []
    new_entries = []   # list of dicts with 'ticker', 'dsharpe', 'entry_price', 'stop_price', 'strategy', 'date'
    new_exits = []
    errors_n = 0

    for ticker in batch:
        a = assignments[ticker]
        strategy = a["strategy"]
        ds = float(a.get("dsharpe") or 0)
        try:
            df = get_history(ticker, offline=False, timeframe="1d")
        except Exception:
            errors_n += 1
            continue
        ok, _fails = integrity_check(ticker, df, timeframe="1d")
        if not ok:
            errors_n += 1
            continue
        try:
            s = _strategy_signals(strategy, df)
        except Exception:
            errors_n += 1
            continue
        if len(s) < 2:
            continue
        last = s.iloc[-1]
        last_date = s.index[-1].date().isoformat()

        # ENTRY
        if bool(last.get("entry")) and ticker not in state["open_positions"]:
            entry_price = float(last["close"])
            stop_d = _stop_distance(strategy, last)
            stop_price = round(entry_price - stop_d, 2) if stop_d > 0 else None
            state["open_positions"][ticker] = {
                "entry_date": last_date,
                "entry_price": round(entry_price, 4),
                "stop_price": stop_price,
                "strategy": strategy,
                "dsharpe": ds,
            }
            new_entries.append({
                "ticker": ticker, "strategy": strategy, "dsharpe": ds,
                "entry_price": entry_price, "stop_price": stop_price,
                "date": last_date,
            })
            log_lines.append(
                f"- 🟢 ENTRY **{ticker}** [{strategy}] @ ${entry_price:.2f} on {last_date} · "
                f"stop ${stop_price if stop_price else '—'} · dSharpe {ds:+.2f}"
            )

        # EXIT
        if ticker in state["open_positions"]:
            pos = state["open_positions"][ticker]
            exit_now = bool(last.get("exit_signal"))
            stop_hit = (pos.get("stop_price") is not None
                        and float(last["low"]) <= pos["stop_price"])
            if exit_now or stop_hit:
                exit_price = (float(pos["stop_price"])
                              if (stop_hit and not exit_now)
                              else float(last["close"]))
                pnl_pct = (exit_price / pos["entry_price"] - 1.0) * 100
                closed = {
                    "ticker": ticker, "strategy": pos.get("strategy"),
                    "entry_date": pos["entry_date"],
                    "entry_price": pos["entry_price"],
                    "exit_date": last_date,
                    "exit_price": round(exit_price, 4),
                    "exit_reason": "stop_hit" if stop_hit else "exit_signal",
                    "pnl_pct": round(pnl_pct, 3),
                    "dsharpe_at_entry": pos.get("dsharpe"),
                }
                state["history"].append(closed)
                new_exits.append(closed)
                del state["open_positions"][ticker]
                emoji = "🟢" if pnl_pct > 0 else "🔴"
                log_lines.append(
                    f"- {emoji} EXIT **{ticker}** [{pos.get('strategy')}] @ ${exit_price:.2f} · "
                    f"P&L {pnl_pct:+.2f}% · {'stop hit' if stop_hit else 'exit signal'}"
                )

    state["last_run"] = datetime.now(GST).isoformat(timespec="seconds")
    state["last_run_summary"] = (
        f"batch {len(batch)}/{n} (offset {offset}→{next_offset}) · "
        f"{len(new_entries)} new entries · {len(new_exits)} exits · "
        f"open {len(state['open_positions'])} · history {len(state['history'])} · "
        f"errors {errors_n}"
    )

    # Telegram cap: top N by dSharpe
    if new_entries or new_exits:
        # Rank entries by dSharpe desc, exits by dSharpe_at_entry desc
        new_entries_ranked = sorted(new_entries, key=lambda e: -e.get("dsharpe", 0))
        new_exits_ranked = sorted(new_exits, key=lambda e: -(e.get("dsharpe_at_entry") or 0))
        tg_entries = new_entries_ranked[:TG_CAP]
        tg_exits = new_exits_ranked[:TG_CAP]
        dropped_entries = new_entries_ranked[TG_CAP:]
        dropped_exits = new_exits_ranked[TG_CAP:]
        state["skipped_telegrams"] = [
            {"ticker": e["ticker"], "strategy": e["strategy"], "event": "ENTRY"}
            for e in dropped_entries
        ] + [
            {"ticker": e["ticker"], "strategy": e["strategy"], "event": "EXIT"}
            for e in dropped_exits
        ]
        state["session_alerts_sent"] = len(tg_entries) + len(tg_exits)

        msg_lines = [
            f"📡 <b>AIG Paper-Forward (full universe) — {today}</b>",
            f"<i>{len(new_entries)} entries · {len(new_exits)} exits — "
            f"showing top {len(tg_entries)+len(tg_exits)} by dSharpe (cap={TG_CAP})</i>",
            "",
        ]
        for e in tg_entries:
            sp = f"stop ${e['stop_price']}" if e["stop_price"] else "no stop"
            msg_lines.append(
                f"🟢 ENTRY <b>{e['ticker']}</b> [{e['strategy']}] "
                f"${e['entry_price']:.2f} ({sp}) · dSh {e['dsharpe']:+.2f}"
            )
        for c in tg_exits:
            msg_lines.append(
                f"{'🟢' if c['pnl_pct'] > 0 else '🔴'} EXIT "
                f"<b>{c['ticker']}</b> [{c['strategy']}] "
                f"${c['exit_price']:.2f} P&L {c['pnl_pct']:+.2f}%"
            )
        if dropped_entries or dropped_exits:
            msg_lines.append(
                f"\n<i>+{len(dropped_entries)+len(dropped_exits)} more signals "
                f"(see dashboard / paper_forward_positions_full.json)</i>"
            )
        msg_lines.append("")
        msg_lines.append(
            f"Open: {len(state['open_positions'])} · "
            f"Closed-to-date: {len(state['history'])}"
        )
        _tg("\n".join(msg_lines))

    _save_state(state)

    if log_lines:
        _append_signals_log([f"_Batch: {len(batch)}/{n} (offset {offset})_"] + log_lines)

    return {
        "ok": True,
        "summary": state["last_run_summary"],
        "new_entries": new_entries,
        "new_exits": new_exits,
    }


def main():
    r = detect()
    try:
        print(f"Paper-forward full: {r.get('summary')}")
        if r.get("new_entries"):
            print(f"  NEW ENTRIES: {len(r['new_entries'])} -> top 5: "
                  f"{[e['ticker'] for e in r['new_entries'][:5]]}")
        if r.get("new_exits"):
            print(f"  NEW EXITS:   {len(r['new_exits'])} -> top 5: "
                  f"{[e['ticker'] for e in r['new_exits'][:5]]}")
    except UnicodeEncodeError:
        # console codec can't encode unicode in summary; state was already written
        print(f"Paper-forward full: detection complete (summary contains non-ascii)")


if __name__ == "__main__":
    main()
