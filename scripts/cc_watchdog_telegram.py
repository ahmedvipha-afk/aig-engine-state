"""Telegram helper for cc_watchdog.ps1 — emits canned recovery-lifecycle messages.

Keeps emoji + multi-line formatting entirely on the Python side so the
PowerShell watchdog never has to worry about argv encoding of non-ASCII.

Usage:
    python scripts/cc_watchdog_telegram.py detected --cause sentinel-stale-32min
    python scripts/cc_watchdog_telegram.py recovered --duration-seconds 104
    python scripts/cc_watchdog_telegram.py failed --attempts 3
    python scripts/cc_watchdog_telegram.py tested --duration-seconds 42
"""
from __future__ import annotations
import argparse
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

def _now_uae() -> str:
    return datetime.now(timezone(timedelta(hours=4))).strftime("%H:%M UAE %Y-%m-%d")

def _send(text: str) -> int:
    try:
        from telegram_send import send_message
        r = send_message(text)
        return 0 if r.get("ok") else 1
    except Exception as e:
        sys.stderr.write(f"telegram send failed: {e}\n")
        return 2

def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="kind", required=True)

    p_det = sub.add_parser("detected")
    p_det.add_argument("--cause", required=True)

    p_rec = sub.add_parser("recovered")
    p_rec.add_argument("--duration-seconds", type=int, required=True)

    p_fail = sub.add_parser("failed")
    p_fail.add_argument("--attempts", type=int, required=True)

    p_test = sub.add_parser("tested")
    p_test.add_argument("--duration-seconds", type=int, required=True)

    args = ap.parse_args()
    ts = _now_uae()

    if args.kind == "detected":
        msg = (
            f"🚨 CC crash detected at {ts}.\n"
            f"Cause: {args.cause}.\n"
            f"Recovery initiated."
        )
    elif args.kind == "recovered":
        lag_min = max(1, args.duration_seconds // 60)
        msg = (
            f"✅ CC recovered at {ts}.\n"
            f"Session resumed via headless `claude -p`.\n"
            f"Lag: ~{lag_min} min ({args.duration_seconds}s wall-clock)."
        )
    elif args.kind == "failed":
        msg = (
            f"❌ CC recovery failed at {ts}.\n"
            f"All {args.attempts} attempts exhausted.\n"
            f"Manual intervention needed."
        )
    elif args.kind == "tested":
        msg = (
            f"🛡️ Watchdog tested — CC killed and recovered in {args.duration_seconds}s. "
            f"Auto-recovery operational."
        )
    else:
        return 2

    return _send(msg)


if __name__ == "__main__":
    sys.exit(main())
