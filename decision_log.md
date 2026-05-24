# AIG Decision Log

_Per Phase 1 framework directive Part 7. Append-only; oldest at top, newest at bottom._
_Written by `scripts/decision_log_append.py`. Sync mirror: `decision_log.json`._

## Entries

### Withdraw Path 3 (post-hoc gate amendment) — Session 5 audit response

- **ts_utc:** `2026-05-21T08:00:00+00:00`
- **methodology_source:** `pre_framework_legacy`
- **decision:** Path 3 ('amend PORTFOLIO_GATE for small markets to lower trade-count + drop WR floor') REJECTED. Removed from Decision Point queue. UAE/Crypto FAILs accepted honestly under the original gate.
- **rationale:** Auditor Cowork flagged Path 3 as post-hoc threshold loosening — exactly the failure mode pre-registration discipline exists to prevent. Two acceptable alternatives logged: (a) accept FAILs as honest verdicts, (b) design a small-markets framework prospectively before seeing data.
- **alternatives_considered:**
  - Adopt Path 3 as written (rejected — data-mining via amendment)
  - Design small-markets framework prospectively on untouched data (deferred to Phase B / Phase 2)
- **audit_finding_refs:** `Session 5 Concern 2`
### Deploy US Divergence Daily to paper-forward

- **ts_utc:** `2026-05-21T09:50:00+00:00`
- **methodology_source:** `pre_framework_legacy`
- **decision:** scripts/paper_forward_divergence.py deployed with state file persistence, Telegram alerts on entry/exit. Pine TV-slot route deferred.
- **rationale:** US Divergence Daily passed PORTFOLIO_CLEARED under N=6 haircut (dSharpe 2.606, exp 1.227, WR 44.78%, 10,715 trades). Audit BLOCKING items resolved Session 5. Paper-forward stays paper-forward; no real money until ≥6 months forward data under the same gate.
- **alternatives_considered:**
  - Pine TV-slot deployment (deferred; Python-engine route preferred for now)
  - Defer paper-forward until UAE + Crypto also cleared (rejected; multi-strategy/multi-market not a deployment blocker)
- **audit_finding_refs:** `Session 5 Concern 1`, `Session 5 Concern 5`
### Watch list = top-5 by per-ticker OOS expectancy (SUPERSEDED)

- **ts_utc:** `2026-05-21T09:55:00+00:00`
- **methodology_source:** `pre_framework_legacy`
- **decision:** Initial paper-forward watch list set to DY, EXPGY, PSX, ARW, ROL — the five tickers with the highest per-ticker OOS expectancy in the cleared US Divergence run. SUPERSEDED 2026-05-21 by random-sample N=50 seed=42 stratification; further SUPERSEDED 2026-05-22 by Phase 1 directive Part 2 Improvement 1 (full cleared universe OR stratified sample).
- **rationale:** Original choice was operational — small list for attention budget. Audit NEW-1 BLOCKING flagged this as cherry-picking — high per-ticker expectancy = high sampling noise, not high forward edge.
- **alternatives_considered:**
  - Full cleared universe (Phase 1 Improvement 1 Option A — adopted later)
  - Stratified sample (Phase 1 Improvement 1 Option B — adopted later)
- **audit_finding_refs:** `Session 5 NEW-1`
### Expand UAE universe 44 → 64 retrievable tickers

- **ts_utc:** `2026-05-21T10:18:00+00:00`
- **methodology_source:** `pre_framework_legacy`
- **decision:** Added 20 UAE tickers via TV-MCP cache: ADAVIATION, ADSB, ADNH, BILDCO, others. Universe file universe/uae_tickers_full.txt grew to 64.
- **rationale:** Phase 1 Item 3 required ≥60 retrievable UAE tickers. Pre-existing 44 cached + 20 sourced via TV-MCP. Validation on 60-ticker subset already ran (45 valid, 54 trades, PORTFOLIO_FAIL — expected small-market verdict).
- **alternatives_considered:**
  - Accept 44-ticker universe (rejected — below 60-floor)
  - Source from a non-TV-MCP feed (rejected — TV-MCP is the only halal-verified UAE source we have wired)
### Accept NO CERTIFIABLE CRYPTO EDGE verdict

- **ts_utc:** `2026-05-21T11:35:00+00:00`
- **methodology_source:** `pre_framework_legacy`
- **decision:** Crypto Divergence 1D portfolio result (140 valid, 107 contrib, 644 trades, exp 3.54, WR 37.1%, est dSharpe 0.05) fails multi-criterion (WR floor, trade count, Sharpe). No certifiable crypto edge under current strategies. Crypto FAIL accepted honestly.
- **rationale:** Per audit Concern 2 + Concern 4: WR floor binding as deployability constraint; crypto's 37.1% WR is the primary blocker; adding bars / TF expansion = post-hoc loosening on a failing dataset. Future crypto edge requires a small-markets framework frozen before seeing data.
- **alternatives_considered:**
  - Iterate to 4H or confluence (rejected — same-strategy iteration on failing dataset, Concern 2)
  - Lower WR floor for crypto only (rejected — post-hoc threshold change, Concern 2)
- **audit_finding_refs:** `Session 5 Concern 2`, `Session 5 Concern 4`
### CC crash auto-recovery — watchdog design choices

- **ts_utc:** `2026-05-22T09:35:00+00:00`
- **methodology_source:** `infrastructure_decision`
- **decision:** Built scripts/cc_watchdog.ps1 with sentinel-stale-OR-process-absent detection (not process-presence-only), headless `claude -p` recovery (not SendKeys to Windows Terminal), and sacrificial-subprocess test (not killing the live session). Windows Scheduled Task AIG-CC-Watchdog runs every 60s in user INTERACTIVE session.
- **rationale:** Process-presence-only detection would have missed the 2026-05-21→22 overnight 29-fire-miss incident (the process stayed ALIVE while the REPL hung). SendKeys is fragile under locked-screen / focus-shift conditions; headless claude -p is deterministic. Sacrificial subprocess test preserves the build session.
- **alternatives_considered:**
  - Process-presence only + SendKeys recovery (per original spec — rejected as fragile)
  - Kill claude.exe to test (rejected — would terminate the build session)
### Receipt of Phase 1 framework directive (ahmed_response_2026-05-22)

- **ts_utc:** `2026-05-22T15:55:00+00:00`
- **methodology_source:** `framework_directive`
- **decision:** Ahmed delivered comprehensive Phase 1 framework directive: 6 gate amendments, 6 watch-list improvements, re-validation discipline, three-filter selection methodology, Phase 1 strategy cap=4, framework finality (6-month freeze from commit date).
- **rationale:** Replaces ad-hoc 'what should we try' with frozen executable methodology. Closes audit NEW-1 (watch list), NEW-3 (Decision Log), NEW-5 (Telegram log). Prevents amendment-chasing if Phase 1 results disappoint by binding the framework for 6 months.
- **audit_finding_refs:** `Session 5 NEW-1`, `Session 5 NEW-3`, `Session 5 NEW-5`
### Phase 1 cap = 4 candidates; Divergence grandfathered slot 1

- **ts_utc:** `2026-05-22T15:58:00+00:00`
- **methodology_source:** `ahmed_override`
- **decision:** Phase 1 tests a maximum of 4 candidate strategies total under the three-filter methodology. Divergence fills slot 1 by grandfathering (Session-5 framework selection, pre-autonomous-loop). 3 slots remain. After 4 complete, Phase 1 testing closes until Phase 2 review post-6-month freeze.
- **rationale:** Cap prevents 'keep testing until something clears' from becoming the de facto methodology. Grandfathering Divergence preserves the legitimately-cleared US strategy without inflating the trial budget retroactively.
- **alternatives_considered:**
  - Cap fills with 4 cleared strategies (Divergence+MBV+PMR+STR) — Phase 1 closes immediately (rejected per Ahmed)
  - All 13 strategies count as Phase 1 — directive applies only to Phase 2 (rejected — would defer the new methodology indefinitely)
### 13 sprint-loop strategies tagged Pre-Framework, sprint-loop-tested

- **ts_utc:** `2026-05-22T15:58:30+00:00`
- **methodology_source:** `ahmed_override`
- **decision:** EMA-200, MBV, DBO, ROC, VCB, HAT, PMR, STR, ART, CMF, GAP, WCK + Divergence (grandfathered) get a Pre-Framework field in strategy_register.md. Verdicts stand as historical record. n_trials_registered=39 stays binding (cannot selectively reduce N without invalidating the discipline that produced the count).
- **rationale:** Wipe-slate per Q1=B-modified. Existing test data is reusable as initial evidence for the three-filter methodology, but any Pre-Framework strategy selected by the methodology MUST re-validate under the amended gate on data not previously evaluated under those amendments.
- **alternatives_considered:**
  - Cap fills with 4 cleared (option A — rejected, would close Phase 1 immediately and bypass the new methodology)
  - Phase 1 already complete (option C — rejected, would skip Phase 1 entirely)
### Pause autonomous sprint cron (aig-mode1-sprint)

- **ts_utc:** `2026-05-22T16:00:00+00:00`
- **methodology_source:** `framework_directive`
- **decision:** Disabled Cloud Routine `aig-mode1-sprint`. Watchdog (AIG-CC-Watchdog Windows Scheduled Task) stays running. Paper-forward detector + dashboard regen + commit don't fire automatically until SKILL.md is rewritten to directive-compliant flow.
- **rationale:** The cron was running the Version-B autonomous methodology (enumerate prior primitives → pick unused domain), which Part 4 of the directive explicitly forbids. SKILL.md must be rewritten before the cron can re-enable.
- **alternatives_considered:**
  - Keep cron firing with strategy-enrollment step removed (rejected — risk of stale state piling up, simpler to pause cleanly)
  - Let cron run until WCK finalizes (rejected — risk of Strategy 14 enrolling under old methodology in the window)
### WCK US drain to completion as Pre-Framework

- **ts_utc:** `2026-05-22T16:01:00+00:00`
- **methodology_source:** `ahmed_override`
- **decision:** WCK US (mid-drain at 800/1603 = 50%) is allowed to finish via manual `staged_validate --step` calls. Verdict landed as historical record. Tagged Pre-Framework regardless of outcome — not a Phase 1 candidate.
- **rationale:** Stopping mid-drain creates an INCOMPLETE_SWEEP entry that violates the sweep rule. Finishing honors the discipline that already produced 800 ticker results. Outcome is honest history, not framework data.
- **alternatives_considered:**
  - Stop now, mark INCOMPLETE_SWEEP (rejected — sweep-rule violation per Phase 1 directive)
### Decision Log = dual format (.md + .json) with methodology_source

- **ts_utc:** `2026-05-22T16:01:30+00:00`
- **methodology_source:** `ahmed_override`
- **decision:** decision_log.md (human-readable, append-only Markdown) + decision_log.json (machine-readable mirror, dashboard-readable). Writer helper: scripts/decision_log_append.py. Every entry carries a methodology_source field with one of 6 allowed values.
- **rationale:** Markdown for human read + commit diffs; JSON for dashboard widget + Cowork raw-GitHub reads. methodology_source forces each decision to declare its provenance (directive vs methodology vs override vs audit vs infrastructure vs legacy), preventing decision drift.
- **alternatives_considered:**
  - Markdown only (rejected — no dashboard widget)
  - JSON only (rejected — loses the open-in-editor affordance)
- **audit_finding_refs:** `Session 5 NEW-3`
### Amendment 5 (GCC universe) deferred to Phase 2 infrastructure

- **ts_utc:** `2026-05-22T16:02:00+00:00`
- **methodology_source:** `framework_directive`
- **decision:** GCC universe expansion (Saudi/Kuwait/Qatar/Bahrain halal aggregate ~400-500 tickers) is a Phase 2 infrastructure build. Does NOT consume Phase 1 slots and is NOT required during the 6-month freeze. UAE-only certification remains the deployment gate for any GCC-discovered strategy.
- **rationale:** GCC universe construction is multi-week (sourcing halal lists per market, OHLCV caching, integrity checks). Phase 1 cap=4 leaves no room for new strategy enrollment, so the only 'new Phase 1 work' the framework permits is infrastructure. Ahmed clarified GCC is Phase 2 work.
- **alternatives_considered:**
  - Build GCC universe in Phase 1 (rejected — multi-week build collides with the 6-month freeze on framework)
  - Defer indefinitely (rejected — Phase 2 review is when GCC gets considered for activation)
### Amendment 1 auto-execution layer deferred to Phase 2

- **ts_utc:** `2026-05-22T16:02:30+00:00`
- **methodology_source:** `framework_directive`
- **decision:** Auto-execution layer (orders fire to broker API without human approval per signal + idempotency + slippage + fail-safe halt) is a Phase 2 infrastructure build. Does NOT consume Phase 1 slots. Amendment 1 (relaxed WR floor for trend-following / breakout / momentum strategies under dSharpe ≥1.5 + PF ≥2.0 + CI positive) stays DORMANT until both auto-execution exists AND passes its own validation.
- **rationale:** Human-in-the-loop execution can't reliably honor a strategy with 4-of-5 losing trades (humans deviate; once execution deviates, certified expectancy no longer applies). Auto-execution is a major build (broker API, slippage modeling, fail-safe halt). Ahmed clarified it's Phase 2 work.
- **alternatives_considered:**
  - Activate Amendment 1 with current Telegram-tap workflow (rejected — workflow is human-in-loop, exactly what Amendment 1 forbids)
  - Drop Amendment 1 entirely (rejected — keeps the low-WR option available for Phase 2 when infrastructure exists)
- **audit_finding_refs:** `Session 5 Concern 4`
### Apply Improvement 5 — hide tickers with OOS n<30 from per-ticker displays

- **ts_utc:** `2026-05-22T16:20:08+00:00`
- **methodology_source:** `framework_directive`
- **decision:** generate_dashboard.py per-ticker WINNERS/LOSERS filter raised from oos_n>=10 to oos_n>=30. Removes DXCM-∞-expectancy and other sub-n=30 outliers from dashboard views. Portfolio verdict remains binding.
- **rationale:** Per Phase 1 directive Part 2 Improvement 5. n<30 estimates are dominated by sampling noise; the right fix is exclusion, not better formatting.
- **alternatives_considered:**
  - Keep at n>=10 with footnote (rejected — misleading by default)
  - Hide only oos_n<30 from WINNERS but show in LOSERS (rejected — asymmetry confuses interpretation)
- **audit_finding_refs:** `Session 5 NEW-1 related cherry-picking pattern`
### Improvement 1 — replace cherry-picked watch list with full cleared universe

- **ts_utc:** `2026-05-22T16:21:45+00:00`
- **methodology_source:** `framework_directive`
- **decision:** universe/divergence_us_paperforward_watchlist.txt now contains all 1,030 contributing US Divergence tickers from the PORTFOLIO_CLEARED run. Option A from Phase 1 directive Part 2 Improvement 1. WATCH_LIST_METHOD constant updated in scripts/paper_forward_divergence.py.
- **rationale:** Per Phase 1 directive: Option A is preferred — deploy detector across the ENTIRE cleared US Divergence universe rather than any selectively-sampled subset. Supersedes the 2026-05-21 random-sample seed=42 n=50, which itself superseded the original top-5-by-expectancy that audit NEW-1 flagged as cherry-picking.
- **alternatives_considered:**
  - Option B stratified sample with sector/liquidity caps (kept available; can switch later if Telegram noise becomes operationally unworkable)
  - Maintain n=50 random sample (rejected — directive prefers full universe)
- **audit_finding_refs:** `Session 5 NEW-1`
### Fix watchdog false-fire loop — add cron_paused.flag intentional-pause check

- **ts_utc:** `2026-05-22T18:33:47+00:00`
- **methodology_source:** `infrastructure_decision`
- **decision:** cc_watchdog.ps1 now checks scripts/cron_paused.flag at the top of every tick. If present, watchdog skips all crash detection, updates last_check_ts, sets mode=monitoring_paused, and exits cleanly. Created the flag with paused_at_utc 2026-05-22T16:00:00+00:00 reason phase1_directive_pending_candidate_2.
- **rationale:** Cron disabled at 16:00 UTC per Q2=A. Sentinel naturally aged because nothing was touching it. Watchdog interpreted silence as crash and fired 18 false recoveries between 16:11 and 17:57 UTC (sentinel age 32->105 min, recoveries cycling every 3-5 min, each completing exit=0 but never touching the sentinel). Root cause: watchdog had no signal source to distinguish off-by-design from broken.
- **alternatives_considered:**
  - Disable watchdog entirely while cron paused (rejected — loses safety net for true crashes)
  - Make watchdog query Cloud Routines state directly (rejected — MCP not accessible from Windows scheduled task)
  - Heuristic on missed_sprints.log absence (rejected — overlaps with successful normal operation)
### Fix crash_log.json JSON-via-argv encoding bug

- **ts_utc:** `2026-05-22T18:33:47+00:00`
- **methodology_source:** `infrastructure_decision`
- **decision:** cc_watchdog.ps1 Append-CrashLogJson now writes the JSON to a temp file and passes --file to crash_log_append.py instead of argv. Eliminates the every-recovery JSON parse failure observed today.
- **rationale:** PowerShell argv handling of strings with curly braces and embedded quotes mangled the JSON in transit (error: Expecting property name enclosed in double quotes line 1 column 2). Result: crash_log.md got appended but crash_log.json did not for every recovery since the watchdog was installed.
- **alternatives_considered:**
  - Use stdin pipe to Python helper (rejected — works but temp file is simpler and the helper already supported --file)
  - Manually quote the JSON in PowerShell (rejected — fragile across PS versions)
### Flag-removal sequencing — retrospective on coordination gap

- **ts_utc:** `2026-05-23T10:29:40+00:00`
- **methodology_source:** `audit_finding_resolution`
- **decision:** Retrospective on cron_paused.flag removal at 2026-05-23T09:58:42Z by prior CC session. Flag and Cloud Routine aig-mode1-sprint are independent guards: removing the flag while the routine itself remains disabled leaves the watchdog blind to an intentional pause with no sentinel-refresher behind it. Resulting v1.4 behavior: 3 false-fire recoveries at 10:04/10:09/10:16 UTC, capped at 5/5 by Fix 3 daily-cap. No user-foreground CC processes killed — kill-event analysis: 10:04 cleanup reached only Access-Denied kernel processes (edge-case PID-0 identification bug worth tracking but harmless because Windows refused), 10:09 cleanup reaped a 12-PID claude-code process tree (parent pid=18152 + 11 descendants) spawned in the 37-second inter-recovery window, 10:16 cleanup produced no descendant kill lines. v1.4 CommandLine filter at scripts/cc_watchdog.ps1:200-209 correctly excluded Claude Desktop from all three cleanups.
- **rationale:** Surface the coordination requirement explicitly so future flag-removal workflows pair flag-delete with Cloud Routine re-enable verification. v1.4 daily cap working as designed prevented v1.0-style runaway — without it this would have replayed the 2026-05-22 18-fire incident at larger scale. Cap operation is the only piece of v1.4 that got a real-world unsupervised test today, and it held.
- **alternatives_considered:**
  - Leave the 2026-05-22T18:33 decision as the only record (rejected — that entry's design-intent is correct but does not capture today's failure-mode demonstration that the coordination is load-bearing)
### Recreate cron_paused.flag (Option A) restoring coordinated pause

- **ts_utc:** `2026-05-23T10:29:41+00:00`
- **methodology_source:** `infrastructure_decision`
- **decision:** scripts/cron_paused.flag recreated with paused_at_utc=2026-05-23T10:29:40Z. Watchdog v1.4 will see flag on next 60s tick and transition effective mode to monitoring_paused. Daily cap (5/5) remains in state.json until UTC midnight reset but is now redundant — flag short-circuits stale detection before cap evaluation. Cron re-enable remains a SEPARATE pending decision contingent on SKILL.md rewrite completing Part 4 three-filter methodology enforcement per Phase 1 framework directive.
- **rationale:** Smallest reversible action that restores design-intent from 2026-05-22T18:33 decision. Defers the deeper cron re-enable question as a separate deliberate choice after SKILL.md rewrite is complete. Option B (re-enable cron now) rejected because next fire could enroll Strategy 14 under forbidden Version-B methodology. Option C (do nothing, wait for cap reset at UTC midnight) rejected because it leaves a 9.5h window with no real-crash recovery and the same false-fire loop would recur tomorrow at cap reset.
- **alternatives_considered:**
  - Option B: re-enable Cloud Routine aig-mode1-sprint (rejected — SKILL.md rewrite not complete; cron firing now could enroll Strategy 14 under forbidden Version-B methodology per Phase 1 directive Part 4)
  - Option C: do nothing, let daily cap expire at 2026-05-24T00:00 UTC (rejected — 9.5h window with no crash protection; same loop recurs tomorrow at cap reset)
### 33d93ae commit message overstated completion -- SKILL.md never landed in code

- **ts_utc:** `2026-05-23T10:59:28+00:00`
- **methodology_source:** `audit_finding_resolution`
- **decision:** Record that commit 33d93ae's message asserted "aig-mode1-sprint SKILL.md rewritten directive-compliant" as part of the Phase 1 directive landing, but git evidence shows no SKILL.md was ever added, modified, or deleted in any commit in this repo's history. Phase 1 directive Part 8 actual status was 4/10 implemented in code at commit time, not 5/10 as the message implied.
- **rationale:** Cowork audit cycle reads commit messages on raw GitHub and would treat the assertion as fact. Capturing the drift in decision_log makes the audit chain self-correcting rather than self-reinforcing. The pause + decision-log infrastructure + Improvement 1 + Improvement 5 all landed honestly; the SKILL.md rewrite was asserted in prose but never implemented. SKILL.md rewrite (Task 2 this session) closes the actual gap.
- **alternatives_considered:**
  - amend the original commit (rejected -- rewriting history breaks audit chain integrity)
  - ignore and rewrite SKILL.md silently (rejected -- drift goes unrecorded, future audits cannot distinguish 'never done' from 'done but undocumented')
### Correction to entry 21 -- SKILL.md DOES exist at user-scoped scheduled-tasks path; prior conclusion was scope error

- **ts_utc:** `2026-05-23T11:58:57+00:00`
- **methodology_source:** `audit_finding_resolution`
- **decision:** Retract entry 21's central conclusion. Entry 21 (committed 2026-05-23 in commit 2bfa0af, ts_utc 2026-05-23T10:59:28Z) stated that 'no SKILL.md was ever added, modified, or deleted in any commit in this repo's history' and concluded that 33d93ae's commit message therefore overstated completion. The premise was true; the conclusion was wrong. The SKILL.md exists at C:\\Users\\ahmed\\.claude\\scheduled-tasks\\aig-mode1-sprint\\SKILL.md (outside the AIG git repo, by Claude Code's scheduling-system design -- scheduled-task definitions are user-scoped, not project-scoped). MCP scheduled-tasks listing confirms the canonical path, cron 12,27,42,57 * * * *, enabled=false, lastRunAt 2026-05-22T16:03:28.671Z. The SKILL.md body line 6-11 explicitly identifies itself as 'AIG Phase 1 directive-compliant sprint ... Replaces the prior Version-B autonomous strategy-enrollment SKILL after Ahmed's 2026-05-22 framework directive.' The 33d93ae commit message assertion 'aig-mode1-sprint SKILL.md rewritten directive-compliant' was TRUE -- the rewrite landed into a file outside the AIG repo's tracking. No commit-message-vs-actual-contents drift exists for SKILL.md.
- **rationale:** Faithful audit chain requires correcting wrong conclusions, not only logging new ones. Entry 21 was based on a path-scope error: prior session's 'git log --all -- SKILL.md' and recursive search under aig_engine/ both correctly returned zero, but those searches were the wrong scope for scheduled-task definitions, which Claude Code stores in ~/.claude/scheduled-tasks/<taskId>/SKILL.md (user scope, not project scope). Cowork reading entry 21 on raw GitHub would form the wrong picture of system state (would conclude 'SKILL.md never landed, cron re-enable blocked indefinitely on a non-existent task'). This entry supersedes entry 21's conclusion. Append-only discipline preserves entry 21 as historical record; this entry is the authoritative current state on the SKILL.md question.
- **alternatives_considered:**
  - amend entry 21 in place (rejected -- violates append-only discipline; future readers would not know the original conclusion existed and was corrected)
  - amend the 2bfa0af commit (rejected -- same history-rewriting hazard flagged in entry 21 itself for the 33d93ae case; consistency with the discipline that entry 21 invoked)
  - leave entry 21 standing and update only the next SKILL.md-related entry (rejected -- entry 21 is the canonical-looking record on this topic; without explicit retraction downstream readers will treat its conclusion as truth)
### Cron re-enable -- Cloud Routine aig-mode1-sprint resumed after SKILL.md verification

- **ts_utc:** `2026-05-23T12:14:42+00:00`
- **methodology_source:** `ahmed_override`
- **decision:** Cloud Routine aig-mode1-sprint re-enabled after Ahmed's explicit approval of the 6-step unpause sequence. Preconditions verified this session: (1) SKILL.md at ~/.claude/scheduled-tasks/aig-mode1-sprint/SKILL.md exists and is directive-compliant per Q2 structured verification (7 items + 6 prohibitions all COVERED); (2) MCP-side description in sync with SKILL.md frontmatter (byte-identical); (3) sprint scripts do not enroll new strategies at runtime (grep of strategy_register references shows zero enforcement reads in sprint_catchup/paper_forward_divergence/staged_validate; single read in generate_dashboard for display rendering only); (4) sprint_catchup.py confirmed absorbed-by-pause semantics -- MISSED_FIRES count is reported but cap-at-4 lives in SKILL prompt, no replay queue, missed marks just logged. Sequence executed: step 0 this decision_log entry, step 1 last_sprint_fire.txt refreshed to current UTC, step 2 watchdog state.json reset (recoveries_today=0, mode=normal, recoveries_today_date=2026-05-23), step 3 cron_paused.flag renamed to cron_paused.flag.removed-20260523T121442 for evidence preservation, step 4 MCP scheduled task enabled=true (next turn, after this commit lands cleanly).
- **rationale:** SKILL.md rewrite (stated precondition for cron re-enable per 2026-05-22T16:00:00Z pause decision) has been verified complete this session. Entry 22 retracted entry 21's incorrect 'SKILL.md never landed' conclusion based on path-scope error; the file has been in place at the user-scoped Claude Code scheduled-tasks path since 33d93ae. The 6-step sequence accounts for the latent state from the v1.4 cap-incident (sentinel stale ~17.5h, recoveries_today=5/5, mode=capped) by manually refreshing each piece rather than waiting for UTC-midnight auto-reset; 12h vulnerability window with no crash recovery declined when manual reset is one JSON edit.
- **alternatives_considered:**
  - Wait for UTC midnight (~12h from now) for watchdog cap auto-reset (rejected -- 12h with no crash recovery is unnecessary exposure when manual reset is one JSON edit)
  - Re-enable without sentinel refresh (rejected -- watchdog would fire recovery in the gap between flag removal and first cron tick, contradicting the deliberate unpause)
  - Defer cron re-enable until after watching one sprint fire under flag-still-present mode (impossible -- sprint cannot fire while paused on MCP side)
### Sprint burst killed by watchdog -- SKILL.md missing --mark-done between catch-up iterations

- **ts_utc:** `2026-05-23T13:20:16+00:00`
- **methodology_source:** `audit_finding_resolution`
- **decision:** First cron fire post-unpause at 2026-05-23T12:35:25Z executed a long catch-up burst (~70 missed fires absorbed; SKILL agent capped at 4 catch-up iterations + 1 current = 5 sprint cycles, each up to 10 min). SKILL.md does NOT instruct the agent to call sprint_catchup.py --mark-done between iterations; the script's docstring at sprint_catchup.py:247 says 'after each catch-up iteration (or at the end of the loop)' -- agent discretion. Agent did not refresh sentinel between iterations, so last_sprint_fire.txt stayed at 2026-05-23T12:14:42+00:00 (the manual touch from cron-re-enable step 1). At 12:44:42Z the sentinel hit the watchdog's 30-min stale threshold; v1.4 correctly detected stale-check 3/3, fired CRASH CONFIRMED, killed the in-flight sprint, then continued firing recoveries until manual cron_paused.flag recreation at 13:07Z stopped the loop. Belts-and-suspenders: MCP-side Cloud Routine aig-mode1-sprint set enabled=false in addition to the local cron_paused.flag. SKILL.md patch (add explicit --mark-done call between iterations or at top of each sprint step) and clean re-unpause deferred to next fresh session.
- **rationale:** The architecture's safety mechanism worked correctly -- v1.4 watchdog detected a genuine stale sentinel and acted per design. The failure surface was the SKILL prompt being ambiguous about sentinel-refresh discipline. The script comment at sprint_catchup.py:247 leaves the question to agent interpretation; the agent chose the conservative 'at end of full burst' pattern, which is incompatible with a long catch-up window where the burst itself exceeds the 30-min stale threshold. Surfacing this as a SKILL gap prevents reading the watchdog's intervention as a v1.4 bug -- it isn't, it's the absence of an explicit instruction in the SKILL. The flag-then-MCP disable belts-and-suspenders pattern matches the lesson from entries 21/22: flag and Cloud Routine are independent guards, both should be in the same state for unambiguous pause.
- **alternatives_considered:**
  - Recreate flag only, leave MCP enabled (rejected -- repeats the entries 21/22 coordination mistake in reverse direction; if flag gets removed in a future session without MCP awareness, Cloud Routine would resume against an unfinished investigation)
  - Edit SKILL.md inline this session and re-unpause immediately (rejected -- session is long, edit-then-test sequence deserves a fresh session with proper verification; cron stays disabled is the safe state until the fix lands)
  - Disable watchdog instead of cron (rejected -- watchdog acted correctly here; disabling it would expose to real future crashes for no benefit)
  - Patch sprint_catchup.py to self-touch sentinel on --notify-start (rejected for this session -- changes script semantics; safer fix is in SKILL.md which is operational instruction not engine code)
### WCK US 1D PORTFOLIO_CLEARED via orphan-spawn -- anomalous trigger, pre-registered gate intact

- **ts_utc:** `2026-05-24T06:32:00+00:00`
- **methodology_source:** `audit_finding_resolution`
- **decision:** Record that commit 687fd7e (`Sprint 2026-05-23_17-57`) finalized WCK US 1D at 1603/1603 tickers (100% sweep), trades=16621, dSharpe=1.2437, verdict PORTFOLIO_CLEARED_FOR_PAPER_FORWARD. The fire that produced this commit originated from a watchdog-recovery-spawned headless `claude -p` worker, NOT from a scheduled cron tick. At 17:57Z Cloud Routine `aig-mode1-sprint` was disabled MCP-side and the local `scripts/cron_paused.flag` was in place (both restored at 13:07Z per entry 24's belts-and-suspenders pause). The recovery worker had been spawned during the 12:44Z-13:07Z watchdog crash-confirm loop, persisted into the post-pause window, and ran its SKILL through to completion -- final WCK batches drained, finalize-on-100% triggered, commit landed, push succeeded. The trigger pathway is off-design; the work executed under it is methodologically identical to a normal sprint: frozen `config_hash` binding intact, frozen WCK spec per `strategy_register.md` row 13 intact, no parameter touches, no gate amendment, single finalization at 100% sweep. WCK retains its Pre-Framework tag per the 2026-05-22T15:58:30Z entry; the PORTFOLIO_CLEARED verdict is retained as historical record. WCK remains eligible for Phase 1 selection if the three-filter methodology mechanically selects it in a future selection cycle -- this entry does not pre-empt or foreclose that path.
- **rationale:** Two facts must coexist on the audit chain. (1) The trigger was an architecture gap (companion entry below documents the gap as a system property). (2) The data is methodologically clean. Conflating them would mean either discarding valid pre-registered evidence on procedural grounds or letting the architecture gap go undocumented for Cowork's next read. Recording both, and linking them explicitly, preserves gate discipline AND surfaces the architecture gap that Task C remediates. Cowork reading raw GitHub will see 687fd7e's commit message claim a Pre-Framework PORTFOLIO_CLEARED and find this entry explaining why the SKILL execution was methodologically sound despite the anomalous trigger.
- **alternatives_considered:**
  - Discard 687fd7e and re-run WCK from a normal cron tick post-restart (rejected -- the run honored the pre-registered config_hash and the 100% sweep rule, no post-hoc parameter change occurred, a re-run would be spec-identical and burn compute; the discipline that matters -- 'no post-hoc parameter change on a failing or in-flight dataset' -- was not breached)
  - Log clearance without linking to the architecture-gap entry (rejected -- audit-chain coherence requires the architectural framing be discoverable one click away from any reader who lands on this entry)
  - Tag WCK as `PORTFOLIO_TAINTED_BY_TRIGGER` (rejected -- 'tainted' would imply the gate's discipline was breached; orphan-spawn is an OPS/scheduler issue, not a methodology issue)
### Watchdog-recovery-spawn architecture gap -- pause guards stop new spawns, in-flight orphans run SKILL to completion

- **ts_utc:** `2026-05-24T06:32:30+00:00`
- **methodology_source:** `audit_finding_resolution`
- **decision:** Surface a system property exposed by the 12:44-17:57Z timeline on 2026-05-23. The three pause guards in current operation -- `scripts/cron_paused.flag`, MCP-side `aig-mode1-sprint enabled=false`, and the watchdog's flag-aware short-circuit (per entry 17, 2026-05-22T18:33:47Z) -- collectively stop NEW spawns: cron will not fire, MCP will not trigger, the watchdog will not initiate fresh crash-recovery workers. They do NOT stop already-spawned headless `claude -p` recovery workers from running their SKILL.md to completion. Once a recovery worker has been launched (typically a 10-15 min headless run), no in-process signal currently exists to interrupt it short of force-killing the PID tree. The companion WCK finalization entry above is one concrete instance of this gap. Overnight stability evidence (2026-05-23 evening through 2026-05-24 morning): a 16-PID claude-code-related process pile was identified at session start. 11 of those were Claude Desktop processes (left alive, not orphans). 7 were CC workers, killed individually with per-PID verification (none respawned). Process count went 16 -> 9 and held at 9 with zero respawn. Watchdog log showed continuous skip-paused entries from 13:07Z through this morning's 06:02Z with zero crash-confirm triggers. Zero new sprint commits, zero new sentinel touches, zero new Telegram messages were generated between 17:57Z and reaping time. This bounds the gap as ONE-SHOT -- orphans exit cleanly after SKILL completion, they do not persist as daemons and do not re-spawn. Risk window per orphan = one SKILL execution (~10-15 min); risk window per pause incident = (orphans spawned during the kill-burst) * (orphan SKILL duration).
- **rationale:** Naming a system property is the precondition for closing it. The 2026-05-22T18:33:47Z fix added `cron_paused.flag` as a watchdog signal but framed pause as 'stop new fires'. The WCK orphan-spawn revealed that 'in-flight workers' is a third category alongside cron-driven fires and watchdog-driven recoveries. Recording the gap as ONE-SHOT is load-bearing -- it means future pause incidents do not require unbounded vigilance, they require a finite drain wait. Cowork reading the audit chain should see this gap stated explicitly, not inferred from a sequence of incident entries. Remediation options (NOT implemented this session, future work): (a) recovery workers consult `cron_paused.flag` at SKILL preamble and self-exit, (b) explicit kill-orphans step in pause workflow, (c) Cloud Routine architecture replaces headless-orphan recovery with sentinel-only signaling.
- **alternatives_considered:**
  - Defer documenting until a remediation is implemented (rejected -- audit chain self-correctness requires the gap be visible BEFORE the fix lands so Cowork sees the system honestly)
  - Treat the WCK orphan as one-off and not generalize (rejected -- the same architectural shape will recur on any future pause + still-running-worker overlap; one-off framing would force the next reader to re-derive the property)
  - Disable the watchdog entirely to eliminate the spawn-source (rejected -- watchdog acted correctly in the 2026-05-23 incident; the gap is in pause-coordination, not in watchdog detection)
### Append to entry 24 (2026-05-23T13:20:16Z) -- catch-up cap x iteration budget exceeds stale threshold by design

- **ts_utc:** `2026-05-24T06:33:00+00:00`
- **methodology_source:** `audit_finding_resolution`
- **decision:** Add to entry 24's analysis the explicit arithmetic that makes the SKILL gap binding regardless of agent discretion. Catch-up cap = 4 iterations; per-iteration sprint budget = ~10 min; max catch-up window = 4 x 10 = ~40 min. Watchdog stale-sentinel threshold = 30 min. 40 > 30 by 33%. A fully-utilizing cap-bound catch-up burst will exceed the stale threshold even if every iteration is healthy and progressing. Entry 24 framed the missing `--mark-done` as 'agent discretion' (sprint_catchup.py:247 docstring leaves the question to the agent); this entry sharpens that to: agent discretion CANNOT resolve the timing conflict -- the budget math forecloses any safe choice that does not refresh the sentinel mid-burst. Therefore the SKILL.md patch in Task C is necessary, not optional. Without explicit `sprint_catchup.py --mark-done` between iterations, the SKILL race-loses to the watchdog by design on long catch-up windows.
- **rationale:** Entry 24 documents the WHAT (sprint killed because sentinel went stale during burst); this entry documents the WHY in arithmetic the next reader can verify without re-deriving. Existence-proof analysis ('one incident occurred') is weaker evidence for patch necessity than design-proof analysis ('math forecloses any non-patching choice'). Cowork reading the chain would see entry 24 say 'agent did not refresh sentinel between iterations' and could reasonably ask 'why didn't the agent just refresh?'. This entry answers: the agent COULD have refreshed; the patch makes that the default instead of leaving it as discretion. Both entries together close the question.
- **alternatives_considered:**
  - Edit entry 24 in-place to add the math (rejected -- append-only discipline; entry 24 is in commit c92d080 on origin/main; rewriting would violate the same discipline invoked at entries 21/22)
  - Skip the entry and put the math only into the SKILL.md patch commit message (rejected -- the decision log is the canonical Cowork audit surface; commit messages are downstream documentation, not primary audit chain)
  - Wait until Task C lands and write both entries together (rejected -- decision log is append-only and timestamps are monotonic; backdating to align with the patch commit would obscure temporal order)
### Correction to entries 25/26 (17:57Z timezone label error) + 97cdf93 named as second orphan-spawn instance + 687fd7e flag-creation noted

- **ts_utc:** `2026-05-24T06:50:00+00:00`
- **methodology_source:** `audit_finding_resolution`
- **decision:** Three Task-B-derived corrections on the 2026-05-23 orphan-spawn incident record. (a) **Timezone label error in entries 25 and 26.** Three instances of `17:57Z` across the two entries incorrectly attach a UTC `Z` suffix to digits that come from the LOCAL GST sprint-name convention. The actual UTC time of commit 687fd7e is `2026-05-23T13:57:09Z`; the local GST time is `2026-05-23T17:57:09+04:00`. The digits `17:57` are correct when used as the sprint identifier (`Sprint 2026-05-23_17-57`, retained verbatim from the commit message) but wrong when suffixed with `Z`. Specific instances: entry 25 decision -- `At 17:57Z Cloud Routine aig-mode1-sprint was disabled MCP-side`; entry 26 decision -- `the 12:44-17:57Z timeline on 2026-05-23`; entry 26 decision -- `between 17:57Z and reaping time`. All three should be read as `13:57Z` (UTC) or equivalently `17:57+04:00` (GST). The authoritative UTC timeline for the 2026-05-23 incident is: 12:14:42Z manual sentinel touch + cron unpause prep (entry 23); 12:34:51Z c6dec3d sprint commit; 12:44:42Z watchdog crash-confirm and burst kill (entry 24); 12:44-13:07Z watchdog recovery-spawn loop; 13:07Z manual cron_paused.flag recreation halting the loop; 13:07:26Z 97cdf93 sprint commit (first orphan-spawn artifact, see (b)); 13:20:17Z c92d080 entry-24 documentation commit; 13:57:09Z 687fd7e WCK finalization commit (second orphan-spawn artifact). Entries 25 and 26 remain unedited on origin/main per append-only discipline; this entry is the authoritative timeline. (b) **97cdf93 named as second orphan-spawn instance.** Entry 25 names only 687fd7e as a concrete orphan-spawn artifact; entry 26 frames the architecture gap as a system property without naming 97cdf93. Commit 97cdf93 (committed `2026-05-23T13:07:26Z` per git author date) landed at-or-just-after the manual flag recreation, ~50 minutes before 687fd7e in the timeline. Work product is clean: full WCK batches 6 and 7 (1600/1603 = 99.8% sweep) and paper-forward delta +23/-5 (18 open, 5 history). Trigger is anomalous: commit time is post-kill (kill at 12:44:42Z) so the producing worker was a watchdog-recovery-spawn or persistent orphan rather than the post-unpause cron burst (which was killed). 97cdf93 is therefore the FIRST orphan-spawn artifact on 2026-05-23 (by commit time); 687fd7e is the SECOND, ~50 min later. Entry 26's `(orphans spawned during the kill-burst) * (orphan SKILL duration)` risk-window formula covers both artifacts; this entry just names the specific commits so future readers do not have to derive the set from git timestamps. (c) **687fd7e unmessaged flag-file creation.** Commit 687fd7e incidentally creates `scripts/cron_paused.flag` as a new empty file (`new file mode 100644`, blob `e69de29`) without naming it in the commit message. Inverse direction of the 33d93ae drift documented in entry 21: 33d93ae claimed a change that did not land in the repo; 687fd7e landed a change that was not claimed in the message. Severity low -- the change is just the pause-flag the operator manually recreated locally at 13:07Z (per entry 24) being correctly tracked in git via the sprint's `git add` step. Naming it here closes the audit chain on 'when did the flag get re-tracked in git after the 64db7d7 rename' without forcing future readers to derive the answer from the diff alone.
- **rationale:** Append-only discipline requires correction entries when load-bearing audit-surface text is wrong. The three sub-fixes above are bundled into one entry because they share temporal and topical context (all relate to the 2026-05-23 orphan-spawn incident and its decision_log treatment): a reader landing on any one of (a)-(c) finds the others one screen away, and future Cowork raw-GitHub reads see a single self-contained correction record rather than three scattered entries. (a) is the most load-bearing -- a 4-hour audit-timeline error in two consecutive entries would otherwise propagate into future incident reconstructions and contradict the watchdog log / git timestamps the next auditor would cross-reference. (b) closes the implicit-vs-explicit gap (entry 26's framing covers 97cdf93 categorically, but explicit naming prevents the next reader from missing the specific instance). (c) preserves the 'no unclaimed mutations' discipline parallel to the 33d93ae lesson, inverted direction.
- **alternatives_considered:**
  - Three separate decision_log entries, one per sub-fix (rejected -- temporal/topical coherence of the 2026-05-23 incident set makes one bundled correction more legible than three scattered records; entries 21/22 precedent shows a single-topic correction entry is the established convention, but this incident's three sub-findings are all instances of the same audit-chain hygiene problem so one entry is the closer match)
  - Edit entries 25 and 26 in-place to fix the '17:57Z' label (rejected -- violates append-only discipline invoked at entries 21/22; the precedent says corrections REPLACE the original conclusion via a new entry, not by mutating the original)
  - Skip sub-fix (c) on the 687fd7e flag-file creation (rejected -- the 33d93ae lesson at entries 21/22 explicitly calls out commit-message-vs-content drift; including the inverse-direction case keeps the audit chain symmetric and prevents a future reader from concluding 'drift in only one direction is recorded' from a non-symmetric chain)
  - Include a sub-fix (d) on c6dec3d trigger timing (rejected -- diagnostic data this session revealed c6dec3d, 97cdf93, and 687fd7e ALL lack normal-cron-sprint housekeeping fingerprints (no sentinel touch, no Telegram send, no missed_sprints update), pointing to a category-level no-housekeeping execution path rather than a single timing imprecision; deferred to a future fresh-budget session as a separate investigation requiring reads of session_resume_prompt.txt, the sprint_catchup.py SKILL preamble, and the watchdog spawn command, rather than bundling a hasty conclusion with the three solid corrections in this entry)
### SKILL.md patched -- per-iteration sprint_catchup.py --mark-done; catch-up sentinel-stale bug closed; no-housekeeping execution path remains deferred

- **ts_utc:** `2026-05-24T07:05:00+00:00`
- **methodology_source:** `audit_finding_resolution`
- **decision:** This entry records the SKILL.md patch applied 2026-05-24 to close the cron-triggered catch-up burst sentinel-stale bug captured in entry 24 (`2026-05-23T13:20:16Z`, commit c92d080) and analyzed arithmetically in entry 27 (commit 22792bc). **Patch.** Modifies the iteration-structure prose in step 1 of `C:\Users\ahmed\.claude\scheduled-tasks\aig-mode1-sprint\SKILL.md`. Adds explicit loop wrapping (`Run steps 2-5 below min(N, 4) + 1 times total`) and inserts a sentinel-refresh call (`python scripts/sprint_catchup.py --mark-done`) at the START of each iteration body, including iteration 1. Also disambiguates the prior `Cap at 4 iterations/fire` line to `Cap at 4 catch-up iterations + 1 current = 5 total sprint cycles per fire` matching entry 24's framing. Includes inline rationale referencing entries 24 and 27 so future readers of SKILL.md see both the what (call --mark-done per iteration) and the why (cap times budget exceeds stale-threshold without refresh). **Scope: CRON-TRIGGERED CATCH-UP BURST SENTINEL-STALE BUG ONLY.** Without per-iteration sentinel refresh, the 4-iter cap times ~10-min budget reaches ~50 min and exceeds the watchdog's 30-min stale-sentinel threshold, causing the watchdog to kill the running sprint burst mid-iteration (as observed `2026-05-23T12:44:42Z`). With per-iteration refresh at iteration START, the watchdog sees stale age <= one iteration runtime (~10 min) and will not fire spuriously during the burst. Start-of-iteration placement (rather than end-of-iteration) is the monotonically safer choice: if the sentinel was already ~25 min stale at fire entry, a 10-min iteration ending at 35 min stale would trigger the watchdog mid-iteration -- start-of-iteration refresh eliminates that vulnerability. **Scope: this patch does NOT address the no-housekeeping execution path** used by watchdog-recovery-spawned workers. That category-level finding -- the three sprint commits on 2026-05-23 (c6dec3d, 97cdf93, 687fd7e) share a no-sentinel-touch / no-Telegram / no-missed_sprints-update fingerprint -- is a separate bug class deferred to a future fresh-budget session per entry 28's `alternatives_considered` item 4. The deferred investigation requires reads of `scripts/session_resume_prompt.txt`, the sprint_catchup.py SKILL preamble path, and the watchdog's exact spawn command in `scripts/cc_watchdog.ps1`. **Both fixes needed for full coverage.** This patch covers normal cron-fired sprints; the deferred investigation covers watchdog-recovery-spawned workers. Until the second fix lands, orphan-spawn artifacts may still produce sprint commits without proper housekeeping touches. **SKILL.md location.** Outside the aig_engine git repo at user-scoped `C:\Users\ahmed\.claude\scheduled-tasks\aig-mode1-sprint\SKILL.md` per Claude Code's scheduling-system design (see entry 22). The SKILL.md edit therefore produces no git artifact; this decision_log entry IS the audit-chain record of the patch. Re-unpause sequencing (cron_paused.flag removal + MCP enable=true) is deferred to a separate session with explicit checkpoints -- the cron-paused state from 2026-05-23T13:07Z remains in effect. **Verification step queued for the re-unpause session (not this one):** confirm Claude Code reads SKILL.md fresh on each cron fire vs caching it between fires. The simplest check after applying the SKILL.md edit is to inspect MCP `list_scheduled_tasks` output for `aig-mode1-sprint` -- if the description field reflects the updated text, the harness has loaded the new SKILL; if it still shows the old description, a cache may need clearing before re-unpause is safe.
- **rationale:** The audit chain requires a concrete record when a documented bug gets patched, especially when the patched file lives outside the git surface (so the audit chain cannot rely on `git log` to find the change). Without this entry, a future Cowork audit would see entries 24/27/28 documenting the bug + corrections but no record that the bug was actually fixed. Entry 29 closes that loop. The scope-carving language (what the patch does and does not cover) prevents a future reader from assuming the SKILL.md patch is the complete fix -- it is not; orphan-spawn artifacts via the recovery-spawn path are still possible until the deferred investigation lands its own fix.
- **alternatives_considered:**
  - Skip decision_log entry, rely on chat-transcript memory of the patch (rejected -- audit-chain integrity requires a permanent record; chat transcripts are not part of the audit surface and Cowork reads only the git-tracked decision_log)
  - methodology_source = infrastructure_decision (defensible alternative -- the patch IS an infrastructure/tooling fix; chose audit_finding_resolution because the bug was specifically documented in entries 24/27/28 and this patch closes that documented finding, which fits the enum's intent more tightly; CEO leaned this direction in the approval message)
  - Commit SKILL.md into the aig_engine repo for direct git tracking (rejected this session -- would require rethinking Claude Code's user-scoped scheduled-tasks design; not in scope for Task C. Could be considered as a future infrastructure decision when the scheduling architecture is revisited)
  - Apply the patch without writing a decision_log entry (rejected -- inconsistent with the audit-chain discipline that documented the bug; the patch resolution must be recorded in the same surface where the bug was named)
  - End-of-iteration --mark-done placement instead of start-of-iteration (rejected -- end-of-iteration leaves iteration 1 vulnerable when the sentinel was already stale at fire entry; start-of-iteration is monotonically safer and was confirmed by CEO this session)
- **audit_finding_refs:** `entry 24 (2026-05-23T13:20:16Z)`, `entry 27 (2026-05-24T06:33:00+00:00)`, `entry 28 (2026-05-24T06:50:00+00:00)`
