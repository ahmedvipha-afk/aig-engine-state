#!/bin/bash
# Temp watcher for the 2026-06-12 recovery session: emits one line when the
# first catch-up sprint commit lands, or when a failure signal appears.
# Safe to delete after the session (not committed).
cd "/c/Users/ahmed/OneDrive/Documents/Projects/stocks/Ahmed group/Working Area/aig_engine" || exit 1
base=9f3c27d872aea9f165a8256f5aab35dc6704e2f1
while true; do
  h=$(git rev-parse HEAD 2>/dev/null)
  if [ -n "$h" ] && [ "$h" != "$base" ]; then
    echo "SPRINT COMMIT LANDED: $(git log --oneline -1)"
    exit 0
  fi
  if [ -e scripts/cron_paused.flag ]; then
    echo "FAIL: cron_paused.flag recreated by watchdog"
    exit 0
  fi
  if ! tasklist //FI "PID eq 17268" 2>/dev/null | grep -q 17268; then
    sleep 5
    h=$(git rev-parse HEAD 2>/dev/null)
    if [ "$h" != "$base" ]; then
      echo "SPRINT COMMIT LANDED: $(git log --oneline -1)"
    else
      echo "WORKER 17268 EXITED, NO sprint commit (6/11 failure mode repeat)"
    fi
    exit 0
  fi
  sleep 30
done
