"""AIG sprint catch-up: detect missed cron fires + log + Telegram alert.

Called as Step 0 of every aig-mode1-sprint fire. Compares the current cron-fire
timestamp to `last_sprint_fire.txt` and the configured cron expression. Any
cron mark that should have fired between the last successful fire and now is
a MISSED fire (typically caused by REPL busy during the scheduled window).

Outputs:
  - missed_sprints.log         : appends one line per missed window
  - stdout                     : MISSED_FIRES=N (parsed by SKILL prompt)
  - last_sprint_fire.txt       : touched with current timestamp at end
  - Telegram alert if >= ALERT_THRESHOLD missed in a row (default 4)

The SKILL prompt reads MISSED_FIRES from stdout and runs N+1 sprint iterations
back-to-back (N catch-up + 1 current) per CEO directive 2026-05-21.

This script is deterministic and idempotent. Running it twice in the same
minute counts the same missed fires only once because the sentinel advances
on first invocation.
"""
from __future__ import annotations
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)

SENTINEL = ROOT / "last_sprint_fire.txt"
MISSED_LOG = ROOT / "missed_sprints.log"

# Mirror of the cron expression set in the scheduler. Update both together.
CRON_MINUTES = [12, 27, 42, 57]
ALERT_THRESHOLD = 4


def _now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _read_sentinel() -> datetime | None:
    if not SENTINEL.exists():
        return None
    try:
        s = SENTINEL.read_text(encoding="utf-8").strip()
        s = s.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _write_sentinel(ts: datetime) -> None:
    SENTINEL.write_text(ts.isoformat(), encoding="utf-8")


def cron_marks_between(start: datetime, end: datetime,
                       minutes: list[int]) -> list[datetime]:
    """Every cron mark in (start, end] for the given minutes-of-hour."""
    out: list[datetime] = []
    if end <= start:
        return out
    cur = start.replace(second=0, microsecond=0) + timedelta(minutes=1)
    end_minute = end.replace(second=0, microsecond=0)
    while cur <= end_minute:
        if cur.minute in minutes:
            out.append(cur)
        cur += timedelta(minutes=1)
    return out


def _append_missed(marks: list[datetime]) -> None:
    if not marks:
        return
    with open(MISSED_LOG, "a", encoding="utf-8") as fh:
        for m in marks:
            fh.write(f"{m.isoformat()} REPL_BUSY\n")


def _telegram_alert(missed_count: int) -> bool:
    try:
        sys.path.insert(0, str(ROOT / "scripts"))
        from telegram_send import send_message
        send_message(
            f"⚠ Phase 1 sprint: {missed_count} fires missed in a row.\n\n"
            f"Cron windows were skipped because the REPL was busy. Catching up "
            f"all {missed_count} fires now back-to-back, then resuming normal "
            f"15-min cadence.\n\n"
            f"To reduce missed fires, leave the REPL idle for ≥5 minutes "
            f"between messages while Phase 1 runs autonomously.",
            parse_mode="HTML",
        )
        return True
    except Exception as e:
        sys.stderr.write(f"telegram alert failed: {e}\n")
        return False


def _telegram_start(missed_count: int, now_utc: datetime) -> bool:
    """Sprint-start notification per CEO request 2026-05-21. Short, no spam."""
    try:
        sys.path.insert(0, str(ROOT / "scripts"))
        from telegram_send import send_message
        uae = now_utc.astimezone(timezone(timedelta(hours=4)))
        ts = uae.strftime("%H:%M UAE")
        iters = missed_count + 1
        if missed_count == 0:
            line = f"🚀 Sprint fire {ts} — 1 iteration"
        else:
            line = (f"🚀 Sprint fire {ts} — catching up {missed_count} missed → "
                    f"{iters} iterations back-to-back")
        send_message(line, parse_mode="HTML")
        return True
    except Exception as e:
        sys.stderr.write(f"sprint-start telegram failed: {e}\n")
        return False


def main():
    """Detect + log + alert.

    Does NOT update the sentinel — that's the SKILL prompt's job once it has
    actually executed the catch-up iterations. Running this script in detect
    mode is therefore idempotent: re-running it before the SKILL drains the
    queue keeps returning the same missed count.

    Pass `--mark-done` to update the sentinel to NOW (called by the SKILL at
    the end of its catch-up loop).
    """
    if "--mark-done" in sys.argv:
        now = _now_utc()
        _write_sentinel(now)
        print(f"SENTINEL_UPDATED={now.isoformat()}")
        return

    now = _now_utc()
    last = _read_sentinel()
    if last is None:
        # First-ever fire: log nothing, the SKILL will touch sentinel itself
        print("MISSED_FIRES=0")
        print(f"NOW={now.isoformat()}")
        print("INIT=true")
        return

    marks = cron_marks_between(last, now, CRON_MINUTES)
    # The very last mark is the "current" fire (or just before now); everything
    # earlier in the list was a window we missed.
    if marks and (now - marks[-1]).total_seconds() < 60 * 20:
        # Treat the most-recent mark as "current"; the rest are missed.
        missed_marks = marks[:-1]
    else:
        missed_marks = marks

    missed = len(missed_marks)
    _append_missed(missed_marks)

    alerted = False
    if missed >= ALERT_THRESHOLD:
        alerted = _telegram_alert(missed)

    # Sprint-start notification (CEO directive 2026-05-21 — "always notify
    # me when sprint starts"). Sent only when --notify-start is passed so
    # manual diagnostic runs don't spam Telegram.
    notified_start = False
    if "--notify-start" in sys.argv:
        notified_start = _telegram_start(missed, now)

    # NOTE: sentinel intentionally NOT updated here.
    # The SKILL prompt updates it after each catch-up iteration (or at the end
    # of the loop) via `python scripts/sprint_catchup.py --mark-done`.

    print(f"MISSED_FIRES={missed}")
    print(f"LAST_FIRE={last.isoformat()}")
    print(f"NOW={now.isoformat()}")
    print(f"ALERTED={'true' if alerted else 'false'}")
    print(f"NOTIFIED_START={'true' if notified_start else 'false'}")
    if missed_marks:
        print(f"FIRST_MISSED={missed_marks[0].isoformat()}")
        print(f"LAST_MISSED={missed_marks[-1].isoformat()}")


if __name__ == "__main__":
    main()
