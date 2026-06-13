# Project Handoff State

**Project:** aig_engine
**Last updated:** 2026-06-14 02:30 (GST)
**Current phase:** Block 2 — Track 2 Session A2 CLOSED: TRB-50 (trial 41, trb50_us_1d, spec_hash a96ccdf5c0640e4f) CLEARED — PORTFOLIO_CLEARED_FOR_PAPER_FORWARD at 20:37Z (entry 49: 25,760 trades, exp 1.1521, WR 50.97%, dSharpe 2.8021 @ n=41, CI strictly positive, 99.38% coverage). **US SLOT 2 FILLED** (slots: 1 Divergence, 2 TRB-50, 3-4 open). Session also produced entry 47 (Amendment 1 adjudication: provenance ratified from transcript 57451b12, provision superseded as dead letter, directive recovered to ahmed_response_2026-05-22.md, config knobs removed) and entry 48 (TRB-50 pre-registration).
**Current task:** remove cron_paused.flag, verify catch-up fire, then idle; Track 1 routine fires resume

## Track 2 status (after Session A2)
- TRB-50 CLEARED honestly under the strict gate (same code that failed trials 1-40);
  win-rate hypothesis confirmed: fixed 10-day hold → WR 50.97% vs trend-family ~23-35%.
- TRB-50 is CLEARED-NOT-DEPLOYED. NEXT operator-supervised step: paper-forward
  deployment per the frozen watch-list protocol — selection from the 1,115-ticker
  cleared-contributor set must be PRE-REGISTERED before any signal fires
  (Improvement 1 / audit NEW-1 precedent). Do NOT let routine fires improvise this.
- Slots 3-4: next candidate per Filter 1 priority (momentum is next untested archetype;
  trend_following failed honestly via TSM-12, breakout cleared via TRB-50) — Session A3.
- Entry 46 parked item now also carries the Amendment-1 substantive question (entry 47
  merge): archetype-WR floor relief on merits, proper amendment process, forward-only.
- Universe/exclusion convention: identical 481-exclusion profile in trials 40 and 41
  (63 DATA_ERROR, 418 BLOCKED_DATA: 394 split/spike, 23 short history, 2 hi/lo) —
  documented in entries 46/49. The 394 split/spike blocks remain a data-quality
  investigation item for infrastructure time.
- HOST DISK WARNING: C: (253GB) hit 0 bytes free 2026-06-12 ~19:57Z and killed the
  first validation launch (no state corruption; clean restart). Reclaimed ~3.9GB
  (npm cache, stale temp). Remaining big levers need operator decision: Recycle Bin
  12.7GB; OneDrive local-copy dehydration. This WILL recur.

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
- [22:30Z] routine fire complete headless (claude -p): MISSED_FIRES=0, 1 iteration. Divergence: 1,030 watched, 5 entries/5 exits (BROS/CAVA/FOR/HCSG/MTH same-day round trips), 45 open, 351 history; persistent errors EXAS/HOLX yfinance empty, MCW short history, VRRM split-spike. TRB-50: 1,115 watched, 0 entries/0 exits, 26 open. Queue EMPTY. Dashboard 1.19 MB. Commit 277a1f6 pushed.
- [18:15Z] routine fire complete headless (claude -p): MISSED_FIRES=51 → 5 iterations (cap 4 catch-up + 1 current). Per-iteration results — iter 1: divergence 7 entries/6 exits (45 open, 321 hist), TRB-50 26 entries/0 exits (26 open, 0 hist), commit 8480692; iter 2: divergence 5/5 (45 open, 331), TRB-50 0/0, commit 986174b; iter 3: divergence 5/5 (45 open, 336), TRB-50 0/0, commit 929a774; iter 4: divergence 5/5 (45 open, 341), TRB-50 0/0, commit a5ecc76; iter 5 (current): divergence 5/5 (45 open, 346), TRB-50 0/0, commit 214b9ec. Queue EMPTY all iters. Persistent errors: EXAS/HOLX yfinance empty, MCW short history, CNR/VRRM split-spike.
- [14:49Z] routine fire complete headless (claude -p): MISSED_FIRES=0, 1 iteration; FIRST two-detector fire verified end-to-end. Divergence: ~63 min foreground-waited, 1030 watched, 5 entries/5 exits (BROS/CAVA/FOR/HCSG/MTH same-day round trips), 45 open, 326 history; TRB-50: ~48 min, 1115 watched, 0 entries/0 exits, 26 open (first live fire), 0 history; persistent errors EXAS/HOLX yfinance empty, MCW short history, VRRM split-spike; queue EMPTY; dashboard 1.19 MB; commit 61f8cec pushed.
- [14:52Z] cron_paused.flag STATUS: flag remains on disk + now in git (61f8cec staged it again — same pattern as e3077e5). Flag content written by supervisor session at ~14:32Z citing host doom-loop (15 orphaned claude procs, 2.2GB free RAM, taskkill /T failing → repeated leaks → slow detectors → more timeouts). ENTRY-50 DEPLOYMENT VERIFIED per flag body — a fully-completing fire was the remaining gate and we completed it. OPERATOR ACTION REQUIRED: run zombie_kill.py to clear orphans, then assess whether to remove flag. Track 1 WILL remain paused (launcher checks flag) until operator removes it.
- [TRB-50 DEPLOYMENT, entry 50] paper-forward slot 2 deployed under flag isolation (Amendments A/B/C): scripts/paper_forward_trb50.py (imports signals from aig.strategy_trb50 — Amendment A, identity-tested; fixed 10-day bar-count hold; no stop; digest-only Telegram — Amendment C); universe/trb50_us_paperforward_watchlist.txt frozen (1,115 cleared contributors; 7 zero-signal STRK/STRF/TEM/LOAR/WAY/TTAM/WFF excluded deterministically; Option A); winners_assignment.json rebuilt to {divergence, trb50} (Amendment B) — Pre-Framework mbv/pmr/str tagged out + their 5 mbv open positions (CARR/CMI/ADI/MUR/GGDVY) administratively closed in paper_forward_positions_full.json (history preserved, not Phase-1 evidence); paper_forward_full_universe.py marked DORMANT; SKILL step 2 runs BOTH detectors foreground; tests 6/6 (detector) + 20/20 (engine) green. config_hash unchanged. NEXT: flag down + verify first two-detector fire end-to-end.
- [HOST] memory pressure during build (git 'paging file too small' once, recovered) — accumulated 2026-06-11 orphan claude.exe workers (the documented in-flight-orphans gap); operator zombie_kill recommended. Disk OK (~15GB free; Recycle Bin emptied).
- [02:26] routine fire complete headless (claude -p): MISSED_FIRES=0, 1 iteration; detector ~22 min foreground-waited (blocking TaskOutput per headless contract, sentinel refreshed mid-run + per step): 1030 watched, 5 entries/5 exits (BROS/CAVA/FOR/HCSG/MTH same-day round trips), 44 open, 315 history; persistent data errors EXAS/HOLX yfinance empty, CNR/VRRM split-spike, MCW short history; queue EMPTY (no auto-enroll per directive); dashboard regenerated (1.1 MB); sprint commit e3077e5 pushed
- [02:28] CONCURRENCY NOTE for the TRB-50 deployment session: cron_paused.flag (entry-50 deployment isolation) was created 22:12Z, MID-FIRE — this fire launched 22:02Z, before the hold. Commit e3077e5 inadvertently swept the flag file itself into the repo (it's now tracked; deleting it at deployment end will need a commit, not just a file delete). NO deployment files were swept: only audit_trail/dashboard/positions/signals_log + the flag were staged; paper_forward_full_universe.py, winners_assignment.json, register untouched by this fire. Detector run was paper_forward_divergence.py only (not the script under modification). This HANDOFF edit deliberately left uncommitted to avoid further sweeps; deployment session owns the next commit.
- [01:52] routine fire complete headless (claude -p): MISSED_FIRES=2 → 3 iterations of steps 2-5, all foreground (detector waited via blocking TaskOutput, sentinel refreshed per step + mid-run); each iter: 1030 watched, 5 entries/5 exits (BROS/CAVA/FOR/MTH + MAS or HCSG round trips), 44 open, history 300→305→310; queue EMPTY all iters (no auto-enroll per directive); dashboard regenerated 3x; commits f4087f8, 66efee3, 94e91f6 pushed to origin/main; persistent data errors: EXAS/HOLX yfinance empty, CNR/VRRM split-spike, MCW short history
- [00:37] TRB-50 staged run FINALIZED: PORTFOLIO_CLEARED_FOR_PAPER_FORWARD — 25,760 trades / 1,115 contributors / exp 1.1521 / WR 0.5097 / dSharpe 2.8021 @ n=41 / CI [+0.0032,+0.0052]; one clean 31-min pass (9 batches + finalize) under config_hash c7ff799942e2c8da
- [00:50] entry 49 verdict written; register row 41 + slot table updated (slot 2 FILLED); HANDOFF updated; committing verdict package then removing cron_paused.flag
- [23:57] first validation launch DIED 5 min in: C: disk 0 bytes free; queue verified clean (0/1603, no partial); reclaimed ~3.9GB regenerable caches (npm 2GB, temp 360MB); relaunched clean
- [23:50] cron_paused.flag UP (A2 validation isolation, documented reason); trb50_us_1d enrolled US-only (1,603 tickers, universe sha verified = frozen value)
- [23:45] TRB-50 implemented spec-exact: aig/strategy_trb50.py (position-aware pass), dispatch + inf stop, 6 conformance tests, suite 20/20 green (715e38d)
- [23:30] entry 48 pre-registration committed (03df618) after atomic pre-reg 91fad62 (row 41 + canonical spec + n_trials 40->41 + TRB50 params)
- [23:15] entry 47 adjudication committed (c95fe0d): directive recovered verbatim from transcript 57451b12 to ahmed_response_2026-05-22.md; Amendment 1 superseded (register banner); config knobs removed, config_hash -> 2fa0e2f8cef4093d (then -> c7ff799942e2c8da at pre-reg); same-session-file rule recorded
- [18:44] routine fire complete headless (claude -p): MISSED_FIRES=0, 1 iteration; detector ~26 min foreground-waited (sentinel refreshed mid-run): 1030 watched, 6 entries/6 exits (BROS, CAVA, FOR, GCO, MAS, MTH — same-day round trips), 44 open/295 history; EXAS/HOLX yfinance fetch fails, CNR/VRRM split-spike + MCW history integrity skips; queue EMPTY; dashboard regenerated (1.1 MB); commit 5479be7 pushed to origin/main
- [22:17] catch-up fire VERIFIED by supervising session: sprint commit 23fa516 landed 18:11Z and is on origin/main; worker PID 17268 (spawned 17:44:43Z, 17:43 slot + jitter) exited cleanly 18:13:08Z (~28.5 min), ZERO leftover CLI workers; watchdog back to mode=normal (0 stale checks, 0 recoveries burned — transient 17:37Z recovering state self-healed on first sentinel mark); worker's uncommitted runtime state (HANDOFF/sentinel/missed_sprints.log/telegram log) committed by supervisor
- [22:14] catch-up fire steps 3-5: queue EMPTY (no auto-enrollment); dashboard regenerated (1.1 MB); committing now; sentinel marked after every step
- [22:09] step 2 done foreground (detector ~21 min in background, worker blocked on TaskOutput foreground wait per headless contract, sentinel refreshed at 10/20 min): 1030 watched, 14 entries, 8 exits, 44 open, 289 history; 2 fetch fails (EXAS/HOLX yfinance flaps) + 2 data-integrity skips (MCW/VRRM)
- [21:47] catch-up fire started headless (claude -p): MISSED_FIRES=41 (flag-paused interval); cap = 5 iterations, but iteration 1 (~25 min) exhausted the SKILL's 10-min total time budget — ran 1 full iteration, overflow drains next fires per SKILL TIME BUDGET section (Track 1 cadence 15 min, sentinel kept fresh so next MISSED_FIRES is small)
- [21:33] decision_log entry 46 written: TSM-12 PORTFOLIO_FAIL verdict, full numbers + universe convention (1,603 frozen / 1,122 evaluated, exclusion rule listed); slot 2 OPEN, Session A2 next
- [21:35] HANDOFF updated (verdict, slot status, Track 2 next step); committing verdict + validation_tsm12_us_1d.json + validation-session leftovers, then removing cron_paused.flag (rename convention) to resume Track 1
- [10:45] routine fire started headless (claude -p): MISSED_FIRES=0, 1 iteration
- [11:12] step 2 done foreground (detector ~26 min; harness auto-backgrounded, worker blocked on TaskOutput foreground wait per contract, sentinel refreshed at 20 min): 1030 watched, 8 entries, 8 exits, 38 open, 281 history; 2 fetch fails (EXAS/HOLX yfinance flaps) + 2 data-integrity skips (MCW/VRRM)
- [11:13] steps 3-5: queue still EMPTY (WCK finalized, no auto-enrollment); dashboard regenerated (1.1 MB); sprint commit pushed; sentinel marked after every step
- [10:15] routine fire started headless (claude -p): MISSED_FIRES=0, 1 iteration
- [10:36] step 2 done foreground (detector ~20 min; harness auto-backgrounded, worker blocked on TaskOutput foreground wait per contract, sentinel refreshed at 20 min): 1030 watched, 8 entries, 8 exits, 38 open, 273 history; 3 fetch fails (ACVA/EXAS/HOLX yfinance flaps) + 2 data-integrity skips (MCW/VRRM)
- [10:36] steps 3-5: queue still EMPTY (WCK finalized, no auto-enrollment); dashboard regenerated (1.1 MB); sprint commit pushed; sentinel marked after every step
- [09:30] routine fire started headless (claude -p): MISSED_FIRES=0, 1 iteration
- [09:47] step 2 first attempt CRASHED ~16 min in: PermissionError writing aig/audit_trail.md (transient OneDrive lock); write access re-verified OK, retried foreground per headless contract
- [10:05] step 2 retry done foreground (harness auto-backgrounded, worker blocked on TaskOutput foreground wait per contract, sentinel refreshed between attempts): 1030 watched, 8 entries, 8 exits, 38 open, 265 history; 2 fetch fails (EXAS/HOLX yfinance flaps) + 2 data-integrity skips (MCW/VRRM)
- [10:06] steps 3-5: queue still EMPTY (WCK finalized, no auto-enrollment); dashboard regenerated (1.1 MB); sprint commit pushed; sentinel marked after every step
- [09:00] routine fire started headless (claude -p): MISSED_FIRES=0, 1 iteration
- [09:18] step 2 done foreground (detector ~18 min; harness auto-backgrounded, worker blocked on TaskOutput foreground wait per contract, sentinel refreshed at 10 min): 1030 watched, 8 entries, 8 exits, 38 open, 257 history; 2 fetch fails (EXAS/HOLX yfinance flaps) + 2 data-integrity skips (MCW/VRRM)
- [09:19] steps 3-5: queue still EMPTY (WCK finalized, no auto-enrollment); dashboard regenerated (1.1 MB); sprint commit pushed; sentinel marked after every step
- [08:30] routine fire started headless (claude -p): MISSED_FIRES=0, 1 iteration
- [08:48] step 2 done foreground (detector ~18 min; harness auto-backgrounded, worker blocked on TaskOutput foreground wait per contract): 1030 watched, 8 entries, 8 exits, 38 open, 249 history; 2 fetch fails (EXAS/HOLX yfinance flaps) + 2 data-integrity skips (MCW/VRRM)
- [08:48] steps 3-5: queue still EMPTY (WCK finalized, no auto-enrollment); dashboard regenerated (1.1 MB); sprint commit pushed; sentinel marked after every step
- [07:59] routine fire started headless (claude -p): MISSED_FIRES=0, 1 iteration
- [08:17] step 2 done foreground (detector ~17 min; harness auto-backgrounded, worker blocked on TaskOutput foreground wait per contract): 1030 watched, 11 entries, 9 exits, 38 open, 241 history; 2 fetch fails (EXAS/HOLX yfinance flaps) + 3 data-integrity skips (CNR/MCW/VRRM)
- [08:18] steps 3-5: queue still EMPTY (WCK finalized, no auto-enrollment); dashboard regenerated (1.1 MB); sprint commit 6dbb1b6 pushed; sentinel marked after every step
- [07:29] routine fire started headless (claude -p): MISSED_FIRES=0, 1 iteration
- [07:46] step 2 done foreground (detector ~16 min; harness auto-backgrounded, worker blocked on TaskOutput foreground wait per contract): 1030 watched, 7 entries, 7 exits, 36 open, 232 history; 2 fetch fails (EXAS/HOLX yfinance flaps) + ~73 data-integrity skips
- [07:47] steps 3-5: queue still EMPTY (WCK finalized, no auto-enrollment); dashboard regenerated (1.1 MB); sprint commit 82146ac pushed; sentinel marked after every step
- [06:59] routine fire started headless (claude -p): MISSED_FIRES=0, 1 iteration
- [07:17] step 2 done foreground (detector ~17 min; harness auto-backgrounded, worker blocked on TaskOutput foreground wait per contract, sentinel refreshed at 8 and 16 min): 1030 watched, 7 entries, 7 exits, 36 open, 225 history; 2 fetch fails (EXAS/HOLX yfinance flaps) + ~40 data-integrity skips
- [07:18] steps 3-5: queue still EMPTY (WCK finalized, no auto-enrollment); dashboard regenerated (1.1 MB); sprint commit 62e8741 pushed; sentinel marked after every step (last 03:18:07Z)

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
