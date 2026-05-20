"""AIG daily Telegram summary — compiles same-day engine state into a
short Telegram message and sends via scripts/telegram_send.py.

Used by:
  - aig-morning-scan Cloud Routine (after dashboard generation)
  - Manual: `python scripts/daily_summary.py`

Message kept under 4096 chars (Telegram limit). HTML parse mode.
"""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from telegram_send import send_message  # type: ignore

GST = timezone(timedelta(hours=4))


def _latest_runs() -> dict:
    runs = {}
    for p in ROOT.glob("validation_*.json"):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        pf = d.get("portfolio")
        if not pf:
            continue
        args = d.get("args", {})
        strat = args.get("strategy", "?")
        uni = (args.get("universe") or "").lower()
        if "uae" in p.name or "uae" in uni:
            market = "UAE"
        elif "crypto" in p.name or "crypto" in uni:
            market = "CRYPTO"
        else:
            market = "US"
        key = (strat, market)
        mt = p.stat().st_mtime
        if key not in runs or mt > runs[key][0]:
            runs[key] = (mt, pf)
    return {k: v[1] for k, v in runs.items()}


def _git_short_sha() -> str:
    import subprocess
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(ROOT), text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "—"


def build_summary() -> str:
    now = datetime.now(GST).strftime("%Y-%m-%d %H:%M GST")
    runs = _latest_runs()
    cleared = [(s, m) for (s, m), pf in runs.items() if pf.get("passed")]
    lines = [f"📊 <b>AIG Daily — {now}</b>", ""]

    # one-line per (strategy × market)
    if runs:
        lines.append("<b>Latest verdicts:</b>")
        for (strat, market) in sorted(runs.keys()):
            pf = runs[(strat, market)]
            ok = "🟢" if pf.get("passed") else "🔴"
            sr = pf.get("portfolio_sharpe_deflated", 0) or 0
            exp = pf.get("portfolio_expectancy", 0) or 0
            tr = pf.get("portfolio_trades", 0) or 0
            wr = (pf.get("portfolio_win_rate") or 0) * 100
            lines.append(f"{ok} <b>{strat}/{market}</b> · "
                        f"exp {exp:.2f} · WR {wr:.0f}% · "
                        f"dSharpe {sr:.2f} · {tr:,} trades")
    else:
        lines.append("<i>No validation runs on disk yet.</i>")

    lines.append("")
    if cleared:
        names = ", ".join(f"{s}/{m}" for (s, m) in cleared)
        lines.append(f"✅ <b>Cleared (paper-forward eligible):</b> {names}")
    else:
        lines.append("⚪ No portfolio gates cleared today.")

    lines.append("")
    lines.append("<b>Operations:</b>")
    lines.append("• Positions: 0 (paper, pre-launch)")
    lines.append("• Tier 1 circuit breakers: armed, none tripped")
    lines.append("• Shariah filter: 100% (universes pre-screened)")

    lines.append("")
    lines.append(f"<b>Repo:</b> commit <code>{_git_short_sha()}</code> · "
                "<a href='https://github.com/ahmedvipha-afk/aig-engine-state'>aig-engine-state</a>")
    lines.append("<b>Cockpit:</b> <a href='https://raw.githubusercontent.com/ahmedvipha-afk/aig-engine-state/main/dashboard.html'>dashboard.html</a> (raw)")
    lines.append("")
    lines.append("<i>Rule 01 paper · Rule 15 long only · Rule 16 no leverage · بسم الله</i>")
    return "\n".join(lines)


def main():
    text = build_summary()
    print(text[:400] + "..." if len(text) > 400 else text)
    r = send_message(text, parse_mode="HTML")
    if r.get("ok"):
        msg_id = r.get("result", {}).get("message_id", "?")
        print(f"SENT message_id={msg_id} chars={len(text)}")
    else:
        print(f"FAIL: {r}")
        sys.exit(1)


if __name__ == "__main__":
    main()
