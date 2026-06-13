"""AIG Paper-Forward Detector — US TRB-50 Daily (Phase 1 slot 2).

Deployed per decision_log entry 50 (2026-06-13, operator-approved plan with
Amendments A/B/C). Mirrors the paper_forward_divergence.py pattern: frozen
per-strategy watch list, per-strategy state file, idempotent per-day
detection. Runs as the second detector in sprint SKILL step 2.

AMENDMENT A (single source of truth): the entry signal is computed by
importing `signals` DIRECTLY from `aig.strategy_trb50` — the exact module
the validation engine dispatches to (frozen spec a96ccdf5c0640e4f). No
re-implementation of the breakout rule exists in this file.

EXIT CONVENTION (the one forward-specific mechanic): the frozen spec's
fixed 10-trading-day hold is driven by the PAPER position's own entry
date, not by the module's simulated exit flag — the paper book is the
deployed reality, and a backfill/revision in the fetched history could
shift the simulation's entry placement relative to the recorded paper
entry. bars_held = count of bars in the fetched history strictly AFTER
the recorded entry_date; exit at the latest close when bars_held >=
TRB50_HOLD_DAYS. Re-running intraday adds no bars -> no-op (idempotent).
If fires were paused and bars_held > the hold when first evaluated, the
position exits immediately at the current close with exit_reason
"hold_expired_late" (logged distinctly — late administrative catch-up,
not a spec deviation).

NO STOP (frozen spec): positions carry stop_price=None; no stop checks.

SAME-BAR RE-ENTRY GUARD: the engine cannot exit and re-enter on the same
bar (backtest.py elif structure). The detector mirrors this: an entry is
skipped if a history record for the ticker carries exit_date == the
latest bar's date.

TELEGRAM (Amendment C — DIGEST MODE): one compact summary block per fire
(counts + ticker lists), never per-signal lines. The divergence
detector's per-signal contract is untouched.

Watch list: universe/trb50_us_paperforward_watchlist.txt — the FULL
1,115-ticker cleared-contributor set (oos_n > 0) from
validation_trb50_us_1d.json under config_hash c7ff799942e2c8da
(Improvement 1 Option A; pre-registered in strategy_register.md before
any forward signal fired). The 7 evaluated-but-zero-signal tickers are
excluded on a deterministic, non-performance basis.

Output files:
  - paper_forward_positions_trb50.json  (state: open positions, history)
  - signals_log.md                       (shared human-readable journal)
"""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from aig.data import get_history, integrity_check
from aig.strategy_trb50 import signals          # AMENDMENT A: the engine module itself
from config import TRB50_HOLD_DAYS, market_of   # noqa: F401

try:
    from telegram_send import send_message
    TELEGRAM_AVAILABLE = True
except Exception:
    TELEGRAM_AVAILABLE = False

GST = timezone(timedelta(hours=4))
STATE_FILE = ROOT / "paper_forward_positions_trb50.json"
SIGNALS_LOG = ROOT / "signals_log.md"
WATCHLIST_FILE = ROOT / "universe" / "trb50_us_paperforward_watchlist.txt"

WATCH_LIST_METHOD = ("full_cleared_contributor_set_n1115_from_validation_trb50_us_1d"
                     "_cfg_c7ff799942e2c8da_entry50_2026-06-13")


def _load_default_watch() -> list[str]:
    if WATCHLIST_FILE.exists():
        lines = WATCHLIST_FILE.read_text(encoding="utf-8").splitlines()
        return [ln.strip() for ln in lines
                if ln.strip() and not ln.strip().startswith("#")]
    # Missing watch list = broken audit trail; refuse to improvise a selection.
    return []


DEFAULT_WATCH = _load_default_watch()


def _bars_held(df: pd.DataFrame, entry_date: str) -> int:
    """Trading bars strictly AFTER the paper entry date present in df.

    Pure function (unit-tested). Counting by date comparison (not index
    lookup) survives history revisions where the entry bar itself shifts.
    Re-running on the same day adds no bars -> same count (idempotent).
    """
    ed = pd.Timestamp(entry_date).date()
    idx = pd.DatetimeIndex(df.index)
    return int((idx.date > ed).sum())


def _exit_due(bars_held: int) -> bool:
    """Frozen spec: exit at the close of the TRB50_HOLD_DAYS-th bar after entry."""
    return bars_held >= TRB50_HOLD_DAYS


def _exited_same_bar(state: dict, ticker: str, last_date: str) -> bool:
    """Engine convention guard: no exit-then-reenter on the same bar."""
    for h in reversed(state.get("history", [])):
        if h.get("ticker") == ticker:
            return h.get("exit_date") == last_date
    return False


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "schema": 1,
        "strategy": "trb50",
        "timeframe": "1d",
        "spec_hash": "a96ccdf5c0640e4f",
        "config_hash_at_deploy": None,
        "deployed_at": None,
        "open_positions": {},   # ticker -> {entry_date, entry_price, stop_price=None, bars_held}
        "history": [],          # closed paper trades
        "last_run": None,
        "last_run_summary": "",
        "watch_list": DEFAULT_WATCH,
    }


def _save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _append_signals_log(lines: list[str]):
    now = datetime.now(GST).strftime("%Y-%m-%d %H:%M GST")
    block = f"\n## {now} — Paper-Forward TRB-50\n" + "\n".join(lines) + "\n"
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


def detect(watch_list: list[str] | None = None) -> dict:
    watch = watch_list or DEFAULT_WATCH
    if not watch:
        print("ERROR: TRB-50 watch list missing "
              "(universe/trb50_us_paperforward_watchlist.txt). Refusing to run.")
        return {"ok": False, "summary": "no watch list"}

    state = _load_state()
    state["watch_list"] = watch
    state["watch_list_method"] = WATCH_LIST_METHOD
    state["watch_list_size"] = len(watch)
    if state["deployed_at"] is None:
        try:
            from aig.provenance import provenance
            state["config_hash_at_deploy"] = provenance()["config_hash"]
        except Exception:
            state["config_hash_at_deploy"] = "unknown"
        state["deployed_at"] = datetime.now(GST).isoformat(timespec="seconds")

    today = datetime.now(GST).date().isoformat()
    log_lines = []
    new_entries = []   # (ticker, date, entry_price)
    new_exits = []     # closed dicts
    errors = []

    for ticker in watch:
        try:
            df = get_history(ticker, offline=False, timeframe="1d")
        except Exception as e:
            errors.append(f"{ticker}: data fetch failed — {e}")
            continue
        ok, fails = integrity_check(ticker, df, timeframe="1d")
        if not ok:
            errors.append(f"{ticker}: data integrity fail — {fails[0]}")
            continue

        # EXIT FIRST: bar-count exit needs no signal computation, and
        # processing exits before entries cannot create a same-run
        # exit-then-reenter (the same-bar guard below blocks that).
        last_date = pd.DatetimeIndex(df.index)[-1].date().isoformat()
        if ticker in state["open_positions"]:
            pos = state["open_positions"][ticker]
            held = _bars_held(df, pos["entry_date"])
            pos["bars_held"] = held
            if _exit_due(held):
                exit_price = float(df["close"].iloc[-1])
                pnl_pct = (exit_price / pos["entry_price"] - 1.0) * 100
                closed = {
                    "ticker": ticker,
                    "entry_date": pos["entry_date"],
                    "entry_price": pos["entry_price"],
                    "exit_date": last_date,
                    "exit_price": round(exit_price, 4),
                    "exit_reason": ("hold_expired_10d" if held == TRB50_HOLD_DAYS
                                    else "hold_expired_late"),
                    "bars_held": held,
                    "pnl_pct": round(pnl_pct, 3),
                }
                state["history"].append(closed)
                del state["open_positions"][ticker]
                new_exits.append(closed)
                emoji = "🟢" if pnl_pct > 0 else "🔴"
                log_lines.append(
                    f"- {emoji} EXIT **{ticker}** @ ${exit_price:.2f} on {last_date} · "
                    f"P&L {pnl_pct:+.2f}% · held {held} bars"
                )

        # ENTRY: the engine module's own signal on the latest bar.
        if ticker not in state["open_positions"]:
            if _exited_same_bar(state, ticker, last_date):
                continue   # engine convention: earliest re-entry is the next bar
            try:
                s = signals(df)
            except Exception as e:
                errors.append(f"{ticker}: signals failed — {e}")
                continue
            if len(s) < 2:
                continue
            last_bar = s.iloc[-1]
            if bool(last_bar.get("entry")):
                entry_price = float(last_bar["close"])
                state["open_positions"][ticker] = {
                    "entry_date": last_date,
                    "entry_price": round(entry_price, 4),
                    "stop_price": None,           # frozen spec: no stop
                    "bars_held": 0,
                    "resistance_at_entry": round(float(last_bar["resistance"]), 4),
                }
                new_entries.append((ticker, last_date, entry_price))
                log_lines.append(
                    f"- 🟢 ENTRY **{ticker}** @ ${entry_price:.2f} on {last_date} · "
                    f"no stop · fixed {TRB50_HOLD_DAYS}-day hold"
                )

    state["last_run"] = datetime.now(GST).isoformat(timespec="seconds")
    state["last_run_summary"] = (
        f"watched {len(watch)} tickers · "
        f"{len(new_entries)} new entries · "
        f"{len(new_exits)} exits · "
        f"open positions {len(state['open_positions'])} · "
        f"history {len(state['history'])}"
    )
    _save_state(state)

    if log_lines:
        _append_signals_log(log_lines)

    # Telegram — AMENDMENT C: digest mode only. One compact block per fire,
    # no per-signal lines. Sent only when something happened.
    if new_entries or new_exits:
        ent_tks = [t for (t, _, _) in new_entries]
        ext_tks = [c["ticker"] for c in new_exits]
        wins = sum(1 for c in new_exits if c["pnl_pct"] > 0)
        pnl_sum = sum(c["pnl_pct"] for c in new_exits)

        def _join(tks: list[str], cap: int = 15) -> str:
            return (", ".join(tks[:cap]) +
                    (f" +{len(tks)-cap} more" if len(tks) > cap else ""))

        msg = [f"🔷 <b>AIG TRB-50 digest — {today}</b> <i>(paper-forward, slot 2)</i>"]
        if ent_tks:
            msg.append(f"ENTRIES {len(ent_tks)}: {_join(ent_tks)}")
        if ext_tks:
            msg.append(f"EXITS {len(ext_tks)} ({wins}W/{len(ext_tks)-wins}L, "
                       f"ΣP&L {pnl_sum:+.1f}%): {_join(ext_tks)}")
        msg.append(f"Open: {len(state['open_positions'])} · "
                   f"Closed-to-date: {len(state['history'])}")
        _tg("\n".join(msg))

    return {
        "ok": True,
        "summary": state["last_run_summary"],
        "new_entries": new_entries,
        "new_exits": new_exits,
        "errors": errors,
    }


def main():
    r = detect()
    print(f"Paper-forward TRB-50 run: {r.get('summary')}")
    if r.get("new_entries"):
        print(f"  NEW ENTRIES: {[e[0] for e in r['new_entries']]}")
    if r.get("new_exits"):
        print(f"  NEW EXITS:   {[c['ticker'] for c in r['new_exits']]}")
    if r.get("errors"):
        print(f"  errors: {len(r['errors'])}")


if __name__ == "__main__":
    main()
