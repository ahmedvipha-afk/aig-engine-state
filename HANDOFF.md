# Project Handoff State

**Project:** aig_engine
**Last updated:** 2026-06-12 06:18 (GST)
**Current phase:** Block 2 (Track 1 LIVE) — routine fire 01:59Z ran headless end-to-end: all 5 SKILL steps in one turn. Eighth consecutive clean headless fire; contract fixes holding.
**Current task:** idle between scheduled fires (cron_paused.flag DOWN since 2026-06-11T22:01:48Z; AIG-Mode1-Sprint task live)

## Supervised fire 2026-06-11 17:12Z — evidence
- (a) PASS  spawn: PID 22860 at 17:12:01Z, parent=launcher powershell, exe=~\.local\bin\claude.exe
- (b) PART  sentinel advanced once at iteration start: 16:57:29 -> 17:12:43Z; never again
- (c) FAIL  NO sprint commit (HEAD stayed 8258073); steps 3-5 of SKILL never ran
- (d) PART  Telegram start-notification sent (17:12:36Z); no end-of-fire digest
- (e) PASS  worker EXITED cleanly: exit=0 at 17:31:09Z (19m08s); LEFTOVER CLI WORKERS: none (T3 structural claim CONFIRMED)
- (f) FAIL  watchdog stale-check chain started 17:31:17Z (process-absent+sentinel-18min), reached 2/3; flag recreated 17:32:31 GST; 17:33:09Z tick honored flag — NO recovery spawned
- ROOT CAUSE (transcript 94c97cce): worker hit yfinance flaps (EXAS 404/delisted), launched the
  detector retry as a BACKGROUND task, then ended its turn "waiting" for it. In headless
  `claude -p`, ending the turn exits the process — background notifications never arrive.
  Secondary: the single iteration ran 19 min with one sentinel mark; the watchdog's 15-min
  soft threshold fired after the worker exited. v1.5 itself behaved correctly throughout
  (no false reap during the fire, zero leftovers after).
- Worker's uncommitted leftovers in tree: aig/audit_trail.md, telegram_sent_log.json,
  last_sprint_fire.txt (left as-is per fail protocol).

## Pending
- [ ] OPERATOR: A2 fire failed on a fixable SKILL/headless mismatch. Candidate fixes
      (need approval, none applied): (1) SKILL hard rule for headless workers: NEVER use
      background tasks / never end the turn to wait — run detector retries in the
      foreground; (2) refresh sentinel mid-iteration or raise the 15-min soft threshold
      to > iteration budget; (3) launcher could pass an explicit "you are headless,
      finish all 5 steps in one turn" preamble before the SKILL pointer.
      AIG-Mode1-Sprint task stays registered (inert behind the flag); entry 43 NOT
      written (all-pass condition not met).
- [x] RESOLVED 20:35: lost tail re-sent (compact) and executed — crash_log_dryrun.md
      committed (5ce2a93); Step 1.3 refactor applied to _instructions_v7.txt (local-only,
      gitignored — E2/E4 anchors differed, surfaced in report; backup in %TEMP%);
      Tareq reservation appended at position 42 (4193849). Final numbering: 41 = Phase 2
      verdict, 42 = Tareq (transposed vs original plan map; both entries self-document).

## Completed (recent)
- [x] Phase 0 complete: 0.1 cloud routine GONE (list empty — stronger than disabled);
      0.2 orphans cleared by reboot (live audit: zero); 0.3 state file restored + persisting;
      0.4 tree clean (runtime sync 2e293f7, gitignore 930835d: graphify-out/ + _head_wa.json
      [unreferenced 520KB derived snapshot]); 0.5 entry-38 json desync patched (dbdc027).
- [x] Phase 2 complete: cc_watchdog.ps1 v1.5 committed+pushed (d21dee6) — four bugs fixed
      and verified (filter dead post-npm-migration; $ClaudeExe dead paths; Desktop
      agent-session protection; nested-array Count bug). Bug D confirmed status-only.
      Verdict entry at decision_log position 41 (b59d851).
- [x] Phase 1 partial: entry 39 mandate retirement (658ed8c); entry 40 v7 Scope archival
      (2d94f5c) + ARCHIVED banner added to local _scope_v7.txt (file is gitignored by
      design — banner is local-only). Entry "Tareq" + Step 1.3 refactor: blocked on lost text.

## Last actions
- [05:59] routine fire started headless (claude -p): MISSED_FIRES=0, 1 iteration
- [06:17] step 2 done foreground (detector ~17 min; harness auto-backgrounded, worker blocked on TaskOutput foreground wait per contract): 1030 watched, 7 entries, 7 exits, 36 open, 211 history; 2 fetch fails (EXAS/HOLX yfinance flaps) + 31 data-integrity skips
- [06:18] steps 3-5: queue still EMPTY (WCK finalized, no auto-enrollment); dashboard regenerated (1.1 MB); sprint commit 2ecda93 pushed; sentinel marked after every step (last 02:17:59Z)
- [05:29] routine fire started headless (claude -p): MISSED_FIRES=0, 1 iteration
- [05:46] step 2 done foreground (detector ~16 min; harness auto-backgrounded, worker polled process-exit foreground per contract, sentinel refreshed every 30s during poll): 1030 watched, 8 entries, 7 exits, 36 open, 204 history; 2 fetch fails (EXAS/HOLX yfinance flaps) + ~30 data-integrity skips
- [05:47] steps 3-5: queue still EMPTY (WCK finalized, no auto-enrollment); dashboard regenerated (1.1 MB); sprint commit 1d51fb0 pushed; sentinel marked after every step (last 01:47:14Z)
- [04:59] routine fire started headless (claude -p): MISSED_FIRES=0, 1 iteration
- [05:17] step 2 done foreground (detector ~17 min; harness auto-backgrounded, worker polled process-exit foreground per contract): 1030 watched, 6 entries, 6 exits, 35 open, 197 history; 2 fetch fails (EXAS/HOLX yfinance flaps) + 32 data-integrity skips
- [05:18] steps 3-5: queue still EMPTY (WCK finalized, no auto-enrollment); dashboard regenerated (1.1 MB); sprint commit eb236fb pushed; sentinel marked after every step (last 01:18:11Z)
- [04:29] routine fire started headless (claude -p): MISSED_FIRES=0, 1 iteration
- [04:47] step 2 done foreground (detector ~17 min; harness auto-backgrounded, worker polled process-exit foreground per contract): 1030 watched, 6 entries, 6 exits, 35 open, 191 history; 2 fetch fails (EXAS/HOLX yfinance flaps) + 32 data-integrity skips
- [04:48] steps 3-5: queue still EMPTY (WCK finalized, no auto-enrollment); dashboard regenerated (1.1 MB); sprint commit c5347fe pushed; sentinel marked after every step (last 00:48:52Z)
- [04:00] routine fire started headless (claude -p): MISSED_FIRES=0, 1 iteration
- [04:17] step 2 done foreground (detector ~17 min; harness auto-backgrounded, worker blocked on TaskOutput foreground wait per contract): 1030 watched, 6 entries, 6 exits, 35 open, 185 history; 2 fetch fails (EXAS/HOLX yfinance flaps) + 32 data-integrity skips
- [04:18] steps 3-5: queue still EMPTY (WCK finalized, no auto-enrollment); dashboard regenerated (1.1 MB); sprint commit ee4c545 pushed; sentinel marked after every step (last 00:18:18Z)
- [03:30] routine fire started headless (claude -p): MISSED_FIRES=0, 1 iteration
- [03:47] step 2 done foreground (detector ~17 min; harness auto-backgrounded, worker blocked on TaskOutput foreground wait per contract): 1030 watched, 8 entries, 6 exits, 35 open, 179 history; 2 fetch fails (EXAS/HOLX yfinance flaps) + 31 data-integrity skips
- [03:48] steps 3-5: queue still EMPTY (WCK finalized, no auto-enrollment); dashboard regenerated (1.1 MB); sprint commit 1dfeaf9 pushed; sentinel marked after every step
- [02:15-02:46] restoration fire: clean end-to-end (detector 23 entries/17 exits; commit 5f4152f); entry 44 written 02:55 post-exit (see "How to resume")

## Gotchas / context next session needs
- Decision-log numbering is POSITIONAL (no id field). Planned map was 39 mandate / 40 scope /
  41 Tareq / 42 verdict; with Tareq's text lost, the verdict sits at position 41 and says so
  in its body. When Tareq's text arrives it lands at 42+ out of planned order.
- Headless git push: gh (logged out) is configured as the github.com per-host credential
  helper and CLEARS the GCM 'manager' helper first. Use:
  git -c credential.https://github.com.helper=manager push
- Never classify CC CLI processes by the substring 'claude-code' — Desktop's agent-mode
  sessions live under Roaming\Claude\claude-code\<ver>\. See cc_watchdog.ps1 v1.5 header.
- cron_paused.flag checklist items are all remediated; the flag now functions purely as the
  Track 1 hold. scripts/cc_watchdog_recovery.lock (5/27) self-clears on first active tick.
- GITHUB_TRADING_PAT env var is scoped to a different repo (403 on aig-engine-state).

## How to resume right now
1. DONE 2026-06-12 02:55 GST: post-exit criteria verified — (e) exit=0 at 22:47:37Z,
   33m11s, zero leftover CLI workers; (f) watchdog quiet (mode=normal, 0 stale checks,
   0 recoveries); (h) transcript f20c010e: zero voluntary background launches (one
   harness auto-background, foreground-waited per contract). Entry 44 WRITTEN.
   TRACK 1 IS LIVE — fires every 15 min (12,27,42,57 +jitter), IgnoreNew dedupes.
2. Phase 1 note: WCK queue is now EMPTY. Next strategy slot requires the Ahmed-supervised
   three-filter methodology + pre-registration in strategy_register.md before enrollment.
3. If Track 1 must ever be paused: create scripts/cron_paused.flag — BOTH the launcher
   and the watchdog honor it (one flag stops driver + recovery together).
