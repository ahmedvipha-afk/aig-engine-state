---
name: aig-mode1-sprint
description: AIG Phase 1 directive-compliant sprint — drains existing queue, runs paper-forward detector, regenerates dashboard, commits. No autonomous strategy enrollment. Strategy slots driven by the three-filter methodology in strategy_register.md, not by queue-emptiness.
---

AIG Phase 1 directive-compliant sprint. **Replaces** the prior Version-B
autonomous strategy-enrollment SKILL after Ahmed's 2026-05-22 framework
directive. This SKILL does NOT enroll new strategies autonomously. The
methodology in `strategy_register.md` PHASE 1 THREE-FILTER SELECTION
METHODOLOGY governs which Phase 1 candidates run, and Ahmed approves
any deviation from the methodology before execution.

Working dir:
  C:\Users\ahmed\OneDrive\Documents\Projects\stocks\Ahmed group\Working Area\aig_engine

# HEADLESS CONTRACT (added 2026-06-12 after the 2026-06-11 17:12Z failed fire)

You may be running as `claude -p` (headless): the process EXITS the moment
your turn ends, and background-task notifications will NEVER arrive.
Therefore:
- NEVER launch background tasks (no run_in_background, no detached retries).
- NEVER end your turn to wait for anything.
- Run every retry FOREGROUND to completion.
- The fire is complete only when steps 1-5 below ALL ran in THIS turn.

LIVENESS (per-step sentinel): after completing EACH of steps 2, 3, 4 and 5,
run `python scripts/sprint_catchup.py --mark-done` (timestamp-only write).
This keeps the watchdog's stale clock at <= one step's runtime even when a
step (e.g. the detector under yfinance retries) runs long.

# WHAT THIS SPRINT DOES (per fire)

1. **Catch-up notification.**
   `python scripts/sprint_catchup.py --notify-start`
   Parses MISSED_FIRES=N. Cap at 4 catch-up iterations + 1 current = 5
   total sprint cycles per fire (was 8 catch-up — reduced 2026-05-22
   because strategy-enrollment is no longer in flight per fire).

   **Iteration structure (fixed 2026-05-24 per decision_log entry 27).**
   Run steps 2–5 below `min(N, 4) + 1` times total. Before EACH iteration
   body — including iteration 1 — refresh the sentinel:

       python scripts/sprint_catchup.py --mark-done

   This is load-bearing. Without per-iteration refresh, the cap × 10-min
   budget (max ~50 min) exceeds the watchdog's 30-min stale-sentinel
   threshold, and the watchdog will kill the burst mid-iteration (as it
   did 2026-05-23 — see decision_log entry 24). With per-iteration
   refresh, the watchdog sees stale age ≤ one iteration runtime (~10 min).

   `--mark-done` writes the current UTC ISO timestamp to
   `last_sprint_fire.txt`. Output `SENTINEL_UPDATED=<ts>` confirms the
   write.

2. **Paper-forward detectors on cleared Phase 1 strategies (slots 1 + 2).**
   Run BOTH, in order, foreground:
   `python scripts/paper_forward_divergence.py`
   Reads `universe/divergence_us_paperforward_watchlist.txt` (full 1,030-ticker
   cleared universe per Phase 1 directive Part 2 Improvement 1). Sends
   Telegram on entry/exit (per-signal contract, unchanged).
   `python scripts/paper_forward_trb50.py`
   (added 2026-06-13 per decision_log entry 50 — slot 2 TRB-50 deployment).
   Reads `universe/trb50_us_paperforward_watchlist.txt` (full 1,115-ticker
   cleared-contributor set). Fixed 10-day-hold exits, no stop. Telegram is
   DIGEST-ONLY (one summary block per fire — Amendment C); do NOT convert
   it to per-signal alerts. Mark the sentinel between the two detectors if
   the first ran long:
   `python scripts/sprint_catchup.py --mark-done`
   Phase 1 cleared strategies that also reach paper-forward (when slot
   3/4 land) get added here.

3. **Drain existing staged validation queue (Pre-Framework cleanup).**
   `python scripts/staged_validate.py --step`
   This drains the WCK US queue (Pre-Framework strategy, ~4 batches
   remaining). After WCK finalizes, the queue is empty.

   The sprint does **NOT** auto-enroll a new strategy when the queue
   empties. Phase 1 candidate enrollment is a separate Ahmed-supervised
   step (run the three-filter methodology, pre-register the candidate spec
   in strategy_register.md, then enroll via staged_validate).

4. **Regenerate dashboard.**
   `python scripts/generate_dashboard.py`

5. **Commit + push.**
   `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/commit_session.ps1 -Message "Sprint $(Get-Date -Format yyyy-MM-dd_HH-mm): <brief>"`

# WHAT THIS SPRINT DOES NOT DO

- Does NOT enroll new strategies autonomously (Version B forbidden by directive Part 4).
- Does NOT run the three-filter methodology on its own (that's a deliberate
  Ahmed-supervised step that pre-registers the candidate spec).
- Does NOT amend gate parameters, the framework freeze rules, or the Phase 1
  cap. All those are frozen for 6 months from the directive commit date.
- Does NOT enable disabled Mode-2 routines (`aig-morning-scan`,
  `aig-weekly-full-universe`, `aig-monthly-report`) until Phase 1 closes
  (all 4 candidates complete) AND the 6-month framework freeze elapses.

# CONSTRAINTS (do not relax)

- Long-only (Rule 15), no leverage (Rule 16), paper-only, Shariah-screened.
- NEVER touch TV slots.
- NEVER commit secrets (commit_session.ps1 has a safety regex).
- Pre-registration discipline: ANY config / strategy / gate change rehashes
  the config; verdicts under the old hash are not claimable.
- Decision Log entries required for any deviation from this SKILL or from
  the methodology (`scripts/decision_log_append.py`).

# TIME BUDGET

10-min hard cap per iteration. Catch-up + current iteration caps at 10 min
total. Overflow drains next fire.

# END-OF-FIRE SUMMARY

"Sprint fire <ts>: catch-up=N, drained Pre-Framework queue (WCK ~X%),
Phase 1 slot 1 (Divergence) paper-forward N open / M history, slot 2
(TRB-50) paper-forward N open / M history, dashboard regenerated,
commit <sha>."
