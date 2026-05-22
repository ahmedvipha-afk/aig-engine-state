# AIG CC Crash Recovery — Design Notes

Last updated: 2026-05-22.

This doc captures the crash-prevention measures + the auto-recovery
watchdog that ship together. Read top-to-bottom on first encounter; the
"Day-to-day" section is the only one operators need afterward.

## 1. Why this exists

On the night of 2026-05-21→22, the autonomous sprint loop missed 29 cron
fires in a row (~7.5 hours). Root cause: the previous CC session got
stuck mid-turn — process `claude.exe` was ALIVE but the REPL was
unresponsive. Every cron fire in that window hit REPL_BUSY. Because the
REPL was stuck, even `missed_sprints.log` was not appended to in real
time; the gap was reconstructed only after the next live session loaded.

This is the *hang* failure mode. It is distinct from a *crash* (process
death). The watchdog has to catch both. Process-presence alone misses
hangs entirely.

## 2. Known crash patterns

| ID | Pattern | First seen | Frequency | Root cause | Mitigation |
|----|---------|-----------|-----------|------------|------------|
| P-001 | REPL hang during long sprint turn | 2026-05-21 21:30 UTC | 1 observed | unknown — possibly an interactive tool stall, network hang in a fetch, or mid-print encoding error before the I/O timeout | Watchdog detects via sentinel-stale signal (primary). Forward observability captures the next occurrence in detail. |

CC does not expose historical session transcripts that can be grepped
for crash signatures. This table is **observation-forward**: P-001 is
the one incident with evidence. Every future watchdog-triggered recovery
appends to `crash_log.md` and `crash_log.json` so the table can grow
honestly from data rather than guesses.

## 3. Crash-prevention measures (PART A)

These are baseline hygiene, not specific fixes for P-001 (whose cause is
still unknown):

- **Memory hygiene.** `run_validation.py` and `scripts/staged_validate.py`
  now `del df, bt` after each per-ticker iteration and `gc.collect()`
  every 100 tickers / end of batch. Bounds peak memory on full-universe
  sweeps (1,600+ tickers × several years of bars).
- **Subprocess-call protection.** All `subprocess.check_output` /
  `subprocess.run` sites in dashboard / daily / monthly scripts are
  already wrapped in `try/except` that returns sentinel values instead
  of raising. Verified inline 2026-05-22.
- **Concurrent-op cap.** SKILL.md for `aig-mode1-sprint` already runs
  the per-fire pipeline strictly serially: catchup → objective step →
  paper-forward → staged validation step → dashboard regen → commit.
  No parallel sprints within one fire. `MultipleInstances IgnoreNew` is
  set on the watchdog Scheduled Task so it can't pile up either.
- **Subprocess isolation for heavy work.** `staged_validate.py` and
  `run_validation.py` are invoked as separate Python processes by SKILL.md.
  When they finish, their memory is fully reclaimed by the OS — the
  parent CC REPL never grows from these workloads.
- **CC memory limit configuration.** Claude Code CLI does not currently
  expose a memory-limit knob via `~/.claude/settings.json`. If/when one
  appears we'll wire it through here; for now the watchdog catches the
  symptom rather than the cause.

## 4. Auto-recovery (PART B)

### 4.1 Detection logic

Watchdog ticks once per minute (Windows Task Scheduler minimum). Per tick:

1. Read `last_sprint_fire.txt` mtime → compute `sentinel_age_seconds`.
2. `Get-Process claude` → boolean `claude_alive`.
3. Classify:
   - `sentinel_age > 30 min` → **crash candidate** (cause: `sentinel-stale-Nmin`).
     Catches both true crashes AND the hang mode that we observed.
   - `claude_alive == false AND sentinel_age > 15 min` → **crash candidate**
     (cause: `process-absent+sentinel-Nmin`). Catches the case where
     the CC process is gone AND no one is running sprints.
4. Three consecutive crash candidates (3 minutes) ⇒ **CRASH CONFIRMED**.

The 30-min threshold is tuned to the sprint cron's 15-min cadence:
under normal operation the sentinel advances every 12–18 minutes, so
30 min is "two missed fires" and unambiguous.

### 4.2 Recovery logic

Once a crash is confirmed:

1. Telegram 🚨 "CC crash detected at … Cause: … Recovery initiated."
2. Touch `scripts/cc_watchdog_recovery.lock` to prevent re-entry.
3. Run `claude -p "$(cat scripts/session_resume_prompt.txt)"` headless,
   in the project directory, with a 10-minute per-attempt timeout.
4. Retry up to 3 times with 30-second delays.
5. On success: Telegram ✅, append OK line to `crash_log.md`, JSON to
   `crash_log.json`, reset counters.
6. On all-attempts-failed: Telegram ❌, append MANUAL line to crash log,
   set state mode = `failed`. Operator must intervene.
7. Remove lock.

### 4.3 Why headless `claude -p` (not SendKeys)

The original directive specified launching Windows Terminal and sending
keystrokes (`claude` + Enter, then paste the resume prompt). Three
failure modes pushed us to `claude -p`:

- SendKeys requires the target window to have focus. Race with terminal
  startup; user's foreground app intercepts the keystrokes.
- Fails silently when the workstation is locked (no input desktop).
- No clean signal that recovery completed — would need to scrape output.

`claude -p` is one-shot, deterministic, exits with a status code, and
captures stdout we can log. No UI, no focus race, locked-screen-safe.

### 4.4 State + history files

| File | Purpose |
|------|---------|
| `scripts/cc_watchdog_state.json` | Counters, mode, last crash/recovery timestamps, recent durations. Source of truth for the dashboard widget. |
| `scripts/cc_watchdog.log` | One line per watchdog tick. Rotates by manual truncation if it grows. |
| `scripts/cc_watchdog_recovery.lock` | Sentinel for "recovery in flight." Auto-cleared after `RecoveryTimeoutSeconds`. |
| `crash_log.md` | Human-readable incident history (append-only). |
| `crash_log.json` | Machine-readable incident history (last 200 entries). |

## 5. Windows Scheduled Task setup

The watchdog runs as a Windows Scheduled Task named `AIG-CC-Watchdog`.

| Property | Value | Rationale |
|----------|-------|-----------|
| Trigger 1 | At logon (user-specific) | Resume after reboot or sign-in |
| Trigger 2 | Every 1 minute, indefinitely | Continuous polling |
| User | Current user (e.g., `ahmed`) | Has UI access if needed |
| LogonType | `Interactive` | Has access to user profile, including `~/.claude/` |
| RunLevel | `Limited` | No admin; sandboxes the watchdog |
| Window | Hidden | No flicker every minute |
| MultipleInstances | IgnoreNew | If a previous tick is still running, skip |
| RestartCount / Interval | 3 / 1 min | Self-heal on transient launch failures |
| ExecutionTimeLimit | 15 min | Long-tail kill; a tick should never take this long |

**Critical: LogonType=Interactive**, not SYSTEM. The watchdog needs to
launch `claude.cmd` in the user's session so it inherits the user's
`~/.claude/settings.json`, OAuth credentials, and project zero-prompt
permissions. Running as SYSTEM would launch CC under `NT AUTHORITY\SYSTEM`
which has no Anthropic credentials, no Telegram bot token, no project
permissions, and no access to `~/.claude` for the current user.

The task only runs while the user is logged on. Locked screen is fine
(the watchdog continues running; locked-screen-safe recovery is exactly
why we use `claude -p` not SendKeys). Logged off is not — if the user
signs out, the cron AND watchdog both stop. That's by design: nothing
on this Windows box should run autonomous trading-system work without
the operator being present-in-account.

## 6. Day-to-day operation

### Installing

```powershell
pwsh -File scripts/install_watchdog.ps1
```

Run once. Idempotent: re-running replaces the task in place. No admin
required.

### Inspecting

```powershell
Get-ScheduledTask -TaskName AIG-CC-Watchdog
Get-ScheduledTaskInfo -TaskName AIG-CC-Watchdog
Get-Content scripts\cc_watchdog.log -Tail 20
Get-Content scripts\cc_watchdog_state.json
```

### Manually triggering a tick

```powershell
Start-ScheduledTask -TaskName AIG-CC-Watchdog
```

### Pausing the watchdog when the sprint cron is intentionally off

If you disable `aig-mode1-sprint` (Cloud Routine) for any reason — e.g.,
during a framework directive transition, a manual catch-up, or operator
review — the watchdog will otherwise interpret the resulting sentinel
silence as a crash and fire false recoveries every 3–5 minutes. This
happened on 2026-05-22 between 16:11 and 17:57 UTC (18 false recoveries
in 1h 46m) and is the canonical example of the failure mode.

**Workflow:** before disabling the cron, create the flag file:

```powershell
Set-Content -Path "<aig>\scripts\cron_paused.flag" -Value @'
paused_at_utc: <ISO timestamp>
paused_by: <who/why>
reason: <one-line>
remove_when: cron re-enabled
'@ -Encoding utf8
```

The watchdog checks for this file at the top of every tick. If present,
it skips crash detection entirely, sets `mode=monitoring_paused` in
`scripts/cc_watchdog_state.json`, updates `last_check_ts`, and exits
cleanly. No recovery, no Telegram, no crash log entry.

**To resume:** re-enable the Cloud Routine via `mcp__scheduled-tasks__update_scheduled_task`
or the schedule MCP UI, then delete `scripts/cron_paused.flag`. The
watchdog returns to active crash detection on its next tick.

### Dashboard widget

The Live Status tab of `dashboard.html` renders a small "Crash Watchdog"
card from `scripts/cc_watchdog_state.json` and `crash_log.json`:

- **Crashes today**: `recoveries_today`
- **Total recoveries**: `total_recoveries`
- **Avg recovery duration**: mean of `recent_recovery_durations` (last 20)
- **Longest sprint gap**: `longest_gap_seconds` (peak observed sentinel age)
- **Last crash cause**: `last_crash_cause`
- **Mode**: `normal` / `detecting` / `recovering` / `failed`

### Testing

The sacrificial test (`scripts/cc_watchdog_test.ps1`) spawns a throwaway
`claude -p` subprocess, kills it, and observes the watchdog's detect→
recover code path on a fresh sentinel. Does NOT touch the live session.

### Uninstalling

```powershell
pwsh -File scripts/install_watchdog.ps1 -Uninstall
```

## 7. Recovery semantics — what does `claude -p` actually do?

The recovery session reads `scripts/session_resume_prompt.txt` as its
sole prompt. The prompt text:

> Session resume. Read ceo_brain.md to see where we left off. The
> previous session crashed mid-turn. Verify: (1) what was the last
> sprint fire that completed, (2) what was the last commit pushed to
> GitHub, (3) are Cloud Routines still active, (4) is the Telegram bot
> still running, (5) has any work been lost. Report status before
> continuing.

The session will read the brain, run state checks, and — if it sees a
sentinel gap — invoke `python scripts/sprint_catchup.py --notify-start`
and proceed to drain the queue (per the existing SKILL.md flow).
Recovery is therefore *additive* to the existing sprint pipeline, not a
replacement: the watchdog only kicks off the catch-up; the catch-up
itself uses the same code paths as a normal cron fire.

## 8. Persistence across reboots / updates / reinstalls

| Event | Effect | Recovery |
|-------|--------|----------|
| Reboot | Scheduled Task survives. Re-fires at next logon trigger. | Automatic — `-AtLogOn` trigger handles this. |
| User signs out | Task pauses (Interactive logon type). Cron also pauses. | Automatic on next sign-in. |
| CC update via `claude update` | `claude.cmd` path unchanged. Watchdog unaffected. | None. |
| Project re-clone | Scripts come back; watchdog already registered. Re-run `install_watchdog.ps1` only if paths changed. | Manual: re-run installer if the project moved. |
| Forced sign-out / kill watchdog | Scheduled Task auto-restarts up to 3× with 1 min delay. | Automatic via `RestartCount`. |
| Windows update (post-reboot) | Task survives Windows feature updates. | Automatic. |

## 9. Known limitations

- The watchdog cannot recover if the workstation is signed out. By
  design — no headless trading on this box outside the operator's session.
- The watchdog cannot recover from a corrupted `~/.claude` profile.
  Recovery will keep failing; operator must intervene.
- If `claude -p` itself takes longer than 10 minutes for the resume
  prompt (e.g., the project state is so broken that the recovery turn
  loops on errors), the watchdog will kill it and treat as a failed
  attempt. After 3 such failures, manual mode.
- Memory limits in CC are not configurable through the user's
  `settings.json` today. If a future CC release exposes this, wire it
  here.

## 10. Change log

- **2026-05-22**: Initial implementation. P-001 incident motivated the
  build. Detection via sentinel-stale + process-absence; recovery via
  headless `claude -p`; Windows Scheduled Task in user session.
