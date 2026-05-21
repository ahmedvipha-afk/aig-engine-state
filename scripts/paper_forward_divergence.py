"""AIG Paper-Forward Detector — US Divergence Daily.

Runs the frozen divergence rules against today's bars for a watch list,
detects entries triggered on the most recent confirmed pivot, logs to
signals_log.md, and sends Telegram alerts. Also detects exits on any
open paper position.

Used by the sprint routine (Mode 1) and by aig-morning-scan (Mode 2)
once Mode 2 activates. Idempotent: re-running the same day doesn't
duplicate signals (deduped by (ticker, signal_date) key).

Default watch list: top-5 US Divergence contributors from the latest
PORTFOLIO_CLEARED run (DY, EXPGY, PSX, ARW, ROL).

Output files:
  - paper_forward_positions.json  (state: open positions, history)
  - signals_log.md                 (human-readable journal)

Telegram: sends on every NEW signal (entry or exit) at v7.0 §22 format.
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
sys.path.insert(0, str(ROOT / "scripts"))

from aig.data import get_history, integrity_check
from aig.strategy_divergence import signals
from config import market_of  # noqa: F401  (used by data adapter)

try:
    from telegram_send import send_message
    TELEGRAM_AVAILABLE = True
except Exception:
    TELEGRAM_AVAILABLE = False

GST = timezone(timedelta(hours=4))
STATE_FILE = ROOT / "paper_forward_positions.json"
SIGNALS_LOG = ROOT / "signals_log.md"

DEFAULT_WATCH = ["DY", "EXPGY", "PSX", "ARW", "ROL"]


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "schema": 1,
        "strategy": "divergence",
        "timeframe": "1d",
        "config_hash_at_deploy": None,
        "deployed_at": None,
        "open_positions": {},   # ticker -> {entry_date, entry_price, stop, signals_count}
        "history": [],          # closed paper trades
        "last_run": None,
        "last_run_summary": "",
        "watch_list": DEFAULT_WATCH,
    }


def _save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _append_signals_log(lines: list[str]):
    now = datetime.now(GST).strftime("%Y-%m-%d %H:%M GST")
    block = f"\n## {now} — Paper-Forward Detector\n" + "\n".join(lines) + "\n"
    if SIGNALS_LOG.exists():
        existing = SIGNALS_LOG.read_text(encoding="utf-8")
    else:
        existing = "# AIG Signals Log\n\nPaper-forward signals + status updates from the engine routines.\n"
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
    state = _load_state()
    state["watch_list"] = watch
    if state["deployed_at"] is None:
        try:
            from aig.provenance import provenance
            state["config_hash_at_deploy"] = provenance()["config_hash"]
        except Exception:
            state["config_hash_at_deploy"] = "unknown"
        state["deployed_at"] = datetime.now(GST).isoformat(timespec="seconds")

    today = datetime.now(GST).date().isoformat()
    log_lines = []
    new_entries = []
    new_exits = []
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

        s = signals(df)
        last_idx = len(s) - 1
        if last_idx < 1:
            continue
        last_bar = s.iloc[-1]
        last_date = s.index[-1].date().isoformat()
        prev_bar = s.iloc[-2]

        # ENTRY: divergence entry signal fires on the latest bar
        if bool(last_bar.get("entry")) and ticker not in state["open_positions"]:
            entry_price = float(last_bar["close"])
            stop_dist = float(last_bar.get("stop_dist") or 0.0)
            stop_price = round(entry_price - stop_dist, 2) if stop_dist > 0 else None
            state["open_positions"][ticker] = {
                "entry_date": last_date,
                "entry_price": round(entry_price, 4),
                "stop_price": stop_price,
                "rsi_at_entry": round(float(last_bar["rsi"]), 2),
                "ema_at_entry": round(float(last_bar["ema"]), 4),
            }
            new_entries.append((ticker, last_date, entry_price, stop_price))
            log_lines.append(
                f"- 🟢 ENTRY **{ticker}** @ ${entry_price:.2f} on {last_date} · "
                f"stop ${stop_price if stop_price else '—'} · RSI {float(last_bar['rsi']):.1f}"
            )

        # EXIT: any open position whose latest bar has exit_signal=True
        if ticker in state["open_positions"]:
            pos = state["open_positions"][ticker]
            exit_now = bool(last_bar.get("exit_signal"))
            # stop check (intraday): if last bar low <= stop, exit
            stop_hit = (pos.get("stop_price") is not None
                        and float(last_bar["low"]) <= pos["stop_price"])
            if exit_now or stop_hit:
                exit_price = float(pos["stop_price"]) if stop_hit and not exit_now else float(last_bar["close"])
                pnl_pct = (exit_price / pos["entry_price"] - 1.0) * 100
                closed = {
                    "ticker": ticker,
                    "entry_date": pos["entry_date"],
                    "entry_price": pos["entry_price"],
                    "exit_date": last_date,
                    "exit_price": round(exit_price, 4),
                    "exit_reason": "stop_hit" if stop_hit else "rsi_or_trend_exit",
                    "pnl_pct": round(pnl_pct, 3),
                }
                state["history"].append(closed)
                del state["open_positions"][ticker]
                new_exits.append(closed)
                emoji = "🟢" if pnl_pct > 0 else "🔴"
                log_lines.append(
                    f"- {emoji} EXIT **{ticker}** @ ${exit_price:.2f} on {last_date} · "
                    f"P&L {pnl_pct:+.2f}% · {'stop hit' if stop_hit else 'RSI/trend exit'}"
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
        log_lines.insert(0, f"_Watch list:_ {', '.join(watch)}")
        _append_signals_log(log_lines)

    # Telegram on any new event
    if new_entries or new_exits:
        msg_lines = [f"📡 <b>AIG Paper-Forward — {today}</b>", ""]
        for (tk, dt, ep, sp) in new_entries:
            sp_s = f"stop ${sp}" if sp else "no stop"
            msg_lines.append(f"🟢 ENTRY <b>{tk}</b> ${ep:.2f} ({sp_s})")
        for c in new_exits:
            msg_lines.append(
                f"{'🟢' if c['pnl_pct'] > 0 else '🔴'} EXIT <b>{c['ticker']}</b> "
                f"${c['exit_price']:.2f} P&L {c['pnl_pct']:+.2f}% · {c['exit_reason']}"
            )
        msg_lines.append("")
        msg_lines.append(f"Open: {len(state['open_positions'])} · "
                         f"Closed-to-date: {len(state['history'])}")
        msg_lines.append("<i>Strategy: AIG Divergence Daily · paper-forward · "
                         "Rule 01/15/16 enforced</i>")
        _tg("\n".join(msg_lines))

    return {
        "ok": True,
        "summary": state["last_run_summary"],
        "new_entries": new_entries,
        "new_exits": new_exits,
        "errors": errors,
    }


def main():
    r = detect()
    print(f"Paper-forward run: {r['summary']}")
    if r["new_entries"]:
        print(f"  NEW ENTRIES: {[e[0] for e in r['new_entries']]}")
    if r["new_exits"]:
        print(f"  NEW EXITS:   {[e['ticker'] for e in r['new_exits']]}")
    if r["errors"]:
        for e in r["errors"]:
            print(f"  ERR: {e}")


if __name__ == "__main__":
    main()
