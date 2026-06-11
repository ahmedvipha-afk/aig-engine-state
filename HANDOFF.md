# Project Handoff State

**Project:** aig_engine
**Last updated:** 2026-06-11 21:40 (GST)
**Current phase:** Block 2 (Track 1 driver, Option A2) — supervised fire FAILED criteria (c)+(f); flag BACK UP per protocol. Driver infrastructure built and validated; SKILL/headless mismatch is the blocker.
**Current task:** idle (scripts/cron_paused.flag recreated 2026-06-11T17:32Z; AIG-Mode1-Sprint task registered but inert behind the flag)

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
- [19:46] pushed v1.5 as d21dee6 (root-caused push failure: logged-out gh helper shadows GCM; fix: -c credential.https://github.com.helper=manager)
- [19:52] Step 0.4: 2e293f7 runtime sync; 930835d gitignore; _head_wa.json unreferenced -> ignored; crash_log_dryrun.md meaningful -> reported
- [19:58] Step 0.5: entry 38 mirrored into decision_log.json, dbdc027 pushed
- [20:00] found work-block plan in transcript 60142804 line 124 — TRUNCATED at 7,857 chars mid Step 1.3; exhaustive search: no full copy exists
- [20:03] entry 39 appended via decision_log_append.py, 658ed8c pushed (Rule 8 1.5% cap verified verbatim at _instructions_v7.txt:192)
- [20:06] entry 40 + ARCHIVED banner on _scope_v7.txt (verified: 3x/10x line 14, CEO Fully Autonomous line 11, 27 agents line 92), 2d94f5c pushed
- [20:08] Bug D verified: session_resume_prompt.txt is status-only (5 verify items + "Report status before continuing"; no sprint instruction)
- [20:09] Phase 2 verdict entry appended at position 41 with numbering note, b59d851 pushed

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
1. Get the Track 1 driver decision + the lost plan tail (Tareq entry text, Step 1.3 edits)
   from the operator.
2. If driver = watchdog: rewrite session_resume_prompt.txt to actually fire a sprint
   (per-iteration --mark-done per entry 29's SKILL patch), THEN delete cron_paused.flag
   and watch scripts/cc_watchdog.log through the first recovery cycle.
3. If driver = cloud routine: recreate it via /schedule (RemoteTrigger create), verify one
   fire, then decide whether the watchdog flag should also come down.
