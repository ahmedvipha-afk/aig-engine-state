# AIG Engine — Permission Configuration Notes

**Purpose:** persistent zero-prompt permission policy for routine AIG operations.
Survives session crashes, restarts, reboots, Claude Code updates, network drops,
and cron-fire interruptions because it lives in version control.

**Canonical file:** `.claude/settings.json` at the aig_engine repo root.
**Recovery:** if `.claude/settings.json` is ever lost or corrupted, restore from
this document (full intent + rule list below) or from git history.

**Established:** 2026-05-22 by CEO directive ("zero permission prompts during
normal sprint operations and routine work").

---

## Loading semantics

Claude Code merges settings from three scopes in order — user (`~/.claude/settings.json`)
→ project (`.claude/settings.json`) → local (`.claude/settings.local.json`). Later
scopes override earlier ones, but `permissions.allow` and `permissions.deny` arrays
**merge** (do not replace). Project-level rules load only when the CC session's root
is inside the aig_engine tree.

**Practical impact:**
- A CC session launched from `aig_engine/` (or any subdirectory) gets BOTH the
  global allow list AND this project's broad allow list. Effectively zero prompts.
- A CC session launched from `C:/Users/ahmed/` or any path outside aig_engine
  does NOT load this file. The user-level global rules still apply.
- Cron-launched sprint sessions (`aig-mode1-sprint`) inherit this file because
  the scheduled-tasks system sets CWD to the project root before launching.

## Audit — top prompt triggers observed (before this config)

These commands kept triggering permission prompts during sprint flow and routine work.
The project allow list resolves all of them. Listed in rough frequency order:

1. `git rev-list ...` — not covered by global `git log*` / `git diff*` allow
2. `git rev-parse ...` — only in global PowerShell allow, missing on Bash
3. `git show ...` — same gap (PowerShell only globally)
4. `git check-ignore ...` — not in any allow list
5. `git hash-object ...` — not in any allow list
6. `find ...` — POSIX find not in global allow
7. `sed -n ...` / `awk ...` — text processing tools not in global allow
8. Bash compound commands (`for ... do ... done`, multi-line `&&` chains) — fail prefix-match
9. `python -c "..."` inline expressions — globally allowed as `Bash(python *)` but some session variants prompted
10. PowerShell newer cmdlets (`Get-CimInstance`, `Format-List` with custom expressions) — not in PS allow

## Project allow list — full intent

Broad tool-level grants for the AIG project only:

| Rule | Scope |
|------|-------|
| `Bash` | All Bash commands run from inside aig_engine. Denies still apply. |
| `PowerShell` | All PowerShell commands. Denies still apply. |
| `Edit` | File edits anywhere CC can reach in this session. |
| `Write` | File writes. |
| `Read` | File reads. |
| `Glob` | File-pattern search. |
| `Grep` | Content search. |
| `WebFetch` | HTTP fetches (Cowork raw GitHub reads, market data, etc.) |
| `WebSearch` | Web search. |
| `mcp__tradingview__*` | All TradingView MCP tools (Pine edit/compile, chart control, data fetch, strategy tester, screenshots). |
| `mcp__plugin_telegram_telegram__*` | All Telegram MCP tools (reply, edit_message, react, download_attachment). |
| `mcp__scheduled-tasks__*` | List/create/update scheduled tasks (Cloud Routines). |
| `mcp__ccd_session_mgmt__*` | Cowork session management (search transcripts, archive sessions). |

## Project deny list — non-negotiable blocks

These survive even the broad allow above. Deny always wins.

- `Bash(rm -rf /*)`, `Bash(rm -rf ~/*)`, `Bash(rm -rf C:/*)` — destructive recursive removes
- `Bash(sudo *)` — privilege escalation (Windows has no sudo but POSIX-style guard)
- `Bash(git push --force*)`, `Bash(git push -f *)`, `Bash(git push --force-with-lease*)` — force push to remote
- `Bash(git reset --hard*)` — hard reset (loses uncommitted work)
- `Bash(git clean -fd*)` — force clean (removes untracked files irreversibly)
- `Bash(git branch -D *)` — force-delete branch
- PowerShell equivalents of all of the above
- `PowerShell(Remove-Item -Recurse -Force C:\*)`, `PowerShell(Remove-Item -Recurse -Force ~\*)` — destructive recursive removes
- `PowerShell(Format-Volume*)`, `PowerShell(Stop-Computer*)`, `PowerShell(Restart-Computer*)` — system-level destruction
- `PowerShell(Set-ExecutionPolicy*)` — modifies CC security posture
- `PowerShell(Disable-NetAdapter*)` — disables network

The global deny list at `~/.claude/settings.json` carries a SUPERSET of these.
Both lists merge across scopes — defense in depth.

## How to restore if `.claude/settings.json` is lost

Option A — from git:
```bash
git checkout origin/main -- .claude/settings.json
```

Option B — recreate from this document:
1. `mkdir .claude`
2. Re-create `.claude/settings.json` with the allow/deny lists transcribed from
   the tables above. Top-level keys: `permissions.allow` (array of strings),
   `permissions.deny` (array of strings).
3. Validate with `python -c "import json; json.load(open('.claude/settings.json'))"`.

## How to modify

CEO directive 2026-05-22: "Do not modify without my approval."

Changes require a deliberate edit to `.claude/settings.json`, committed with a
human-readable rationale in the commit message. The matching paragraph in
`ceo_brain.md` ("AIG project has zero-prompt permissions configured ...") must
also be updated so the brain's claim stays accurate.

If a new prompt fires repeatedly during routine work, add the offending command
pattern to the project allow list rather than the global one — keeps other
projects safe.

## Verification timestamp

Initial setup: 2026-05-22. Test ops (post-apply) summarised in the commit log and
in ceo_brain.md under PHASE 1 TRACKER infrastructure row.

**2026-05-22 first verification run:** 5 representative AIG ops executed
back-to-back from this CC session — Python read (validation_runs_metadata.json),
git rev-list HEAD count, dashboard.html size inspection, validation_*.json
enumeration, git fetch + log. All returned cleanly with no interactive prompts
observed in this session (caveat: project rules load fully in sessions whose
root is inside aig_engine; this session is rooted at C:\Users\ahmed). Outcome
in cron-launched sprint sessions will be silent because their root IS inside
the project.

## CC crash auto-recovery (2026-05-22)

The Windows Scheduled Task `AIG-CC-Watchdog` (registered by
`scripts/install_watchdog.ps1`) polls every 60 seconds in this user's
INTERACTIVE session and runs `claude -p` headless when it detects a crash
or REPL hang. The recovery session loads the project's zero-prompt
permission config because its working directory is inside `aig_engine`.

Watchdog itself runs as the current user with `RunLevel=Limited`, so it
inherits the same permissions Ahmed has when running CC manually — no
elevation, no SYSTEM context. The claude.exe child process the watchdog
spawns is fully sandboxed inside the project rules.

Design notes + day-to-day operation: see `CRASH_RECOVERY.md`.

**Verification (2026-05-22):** Sacrificial test
(`scripts/cc_watchdog_test.ps1`) backdated the sentinel by 35 minutes,
drove the watchdog 3 ticks, observed CRASH_CONFIRMED → headless `claude -p`
recovery in 7 seconds, exit code 0. Telegram detect/recover/tested
messages all delivered. Crash log entries tagged `[TEST sacrificial]` /
`test=true` so they don't pollute real-incident metrics.
