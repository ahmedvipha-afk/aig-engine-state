"""One-shot backfill of Phase 1 framework Decision Log.

Run once after decision_log_append.py is in place. Idempotent: if the log
already has entries, this only appends what's missing (by title match).
Delete this file after the initial backfill commit lands.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from decision_log_append import append, LOG_JSON

# Read existing titles for idempotency
existing_titles: set[str] = set()
if LOG_JSON.exists():
    try:
        for e in json.loads(LOG_JSON.read_text(encoding="utf-8")):
            existing_titles.add(e.get("title", ""))
    except json.JSONDecodeError:
        pass

ENTRIES = [
    # ----- Session 5 backfill (pre_framework_legacy) -----
    {
        "ts_utc": "2026-05-21T08:00:00+00:00",
        "title": "Withdraw Path 3 (post-hoc gate amendment) — Session 5 audit response",
        "decision": "Path 3 ('amend PORTFOLIO_GATE for small markets to lower trade-count + drop WR floor') REJECTED. Removed from Decision Point queue. UAE/Crypto FAILs accepted honestly under the original gate.",
        "rationale": "Auditor Cowork flagged Path 3 as post-hoc threshold loosening — exactly the failure mode pre-registration discipline exists to prevent. Two acceptable alternatives logged: (a) accept FAILs as honest verdicts, (b) design a small-markets framework prospectively before seeing data.",
        "alternatives_considered": [
            "Adopt Path 3 as written (rejected — data-mining via amendment)",
            "Design small-markets framework prospectively on untouched data (deferred to Phase B / Phase 2)"
        ],
        "audit_finding_refs": ["Session 5 Concern 2"],
        "methodology_source": "pre_framework_legacy",
    },
    {
        "ts_utc": "2026-05-21T09:50:00+00:00",
        "title": "Deploy US Divergence Daily to paper-forward",
        "decision": "scripts/paper_forward_divergence.py deployed with state file persistence, Telegram alerts on entry/exit. Pine TV-slot route deferred.",
        "rationale": "US Divergence Daily passed PORTFOLIO_CLEARED under N=6 haircut (dSharpe 2.606, exp 1.227, WR 44.78%, 10,715 trades). Audit BLOCKING items resolved Session 5. Paper-forward stays paper-forward; no real money until ≥6 months forward data under the same gate.",
        "alternatives_considered": [
            "Pine TV-slot deployment (deferred; Python-engine route preferred for now)",
            "Defer paper-forward until UAE + Crypto also cleared (rejected; multi-strategy/multi-market not a deployment blocker)"
        ],
        "audit_finding_refs": ["Session 5 Concern 1", "Session 5 Concern 5"],
        "methodology_source": "pre_framework_legacy",
    },
    {
        "ts_utc": "2026-05-21T09:55:00+00:00",
        "title": "Watch list = top-5 by per-ticker OOS expectancy (SUPERSEDED)",
        "decision": "Initial paper-forward watch list set to DY, EXPGY, PSX, ARW, ROL — the five tickers with the highest per-ticker OOS expectancy in the cleared US Divergence run. SUPERSEDED 2026-05-21 by random-sample N=50 seed=42 stratification; further SUPERSEDED 2026-05-22 by Phase 1 directive Part 2 Improvement 1 (full cleared universe OR stratified sample).",
        "rationale": "Original choice was operational — small list for attention budget. Audit NEW-1 BLOCKING flagged this as cherry-picking — high per-ticker expectancy = high sampling noise, not high forward edge.",
        "alternatives_considered": [
            "Full cleared universe (Phase 1 Improvement 1 Option A — adopted later)",
            "Stratified sample (Phase 1 Improvement 1 Option B — adopted later)"
        ],
        "audit_finding_refs": ["Session 5 NEW-1"],
        "methodology_source": "pre_framework_legacy",
    },
    {
        "ts_utc": "2026-05-21T10:18:00+00:00",
        "title": "Expand UAE universe 44 → 64 retrievable tickers",
        "decision": "Added 20 UAE tickers via TV-MCP cache: ADAVIATION, ADSB, ADNH, BILDCO, others. Universe file universe/uae_tickers_full.txt grew to 64.",
        "rationale": "Phase 1 Item 3 required ≥60 retrievable UAE tickers. Pre-existing 44 cached + 20 sourced via TV-MCP. Validation on 60-ticker subset already ran (45 valid, 54 trades, PORTFOLIO_FAIL — expected small-market verdict).",
        "alternatives_considered": [
            "Accept 44-ticker universe (rejected — below 60-floor)",
            "Source from a non-TV-MCP feed (rejected — TV-MCP is the only halal-verified UAE source we have wired)"
        ],
        "audit_finding_refs": [],
        "methodology_source": "pre_framework_legacy",
    },
    {
        "ts_utc": "2026-05-21T11:35:00+00:00",
        "title": "Accept NO CERTIFIABLE CRYPTO EDGE verdict",
        "decision": "Crypto Divergence 1D portfolio result (140 valid, 107 contrib, 644 trades, exp 3.54, WR 37.1%, est dSharpe 0.05) fails multi-criterion (WR floor, trade count, Sharpe). No certifiable crypto edge under current strategies. Crypto FAIL accepted honestly.",
        "rationale": "Per audit Concern 2 + Concern 4: WR floor binding as deployability constraint; crypto's 37.1% WR is the primary blocker; adding bars / TF expansion = post-hoc loosening on a failing dataset. Future crypto edge requires a small-markets framework frozen before seeing data.",
        "alternatives_considered": [
            "Iterate to 4H or confluence (rejected — same-strategy iteration on failing dataset, Concern 2)",
            "Lower WR floor for crypto only (rejected — post-hoc threshold change, Concern 2)"
        ],
        "audit_finding_refs": ["Session 5 Concern 2", "Session 5 Concern 4"],
        "methodology_source": "pre_framework_legacy",
    },
    # ----- Infrastructure: watchdog (2026-05-22) -----
    {
        "ts_utc": "2026-05-22T09:35:00+00:00",
        "title": "CC crash auto-recovery — watchdog design choices",
        "decision": "Built scripts/cc_watchdog.ps1 with sentinel-stale-OR-process-absent detection (not process-presence-only), headless `claude -p` recovery (not SendKeys to Windows Terminal), and sacrificial-subprocess test (not killing the live session). Windows Scheduled Task AIG-CC-Watchdog runs every 60s in user INTERACTIVE session.",
        "rationale": "Process-presence-only detection would have missed the 2026-05-21→22 overnight 29-fire-miss incident (the process stayed ALIVE while the REPL hung). SendKeys is fragile under locked-screen / focus-shift conditions; headless claude -p is deterministic. Sacrificial subprocess test preserves the build session.",
        "alternatives_considered": [
            "Process-presence only + SendKeys recovery (per original spec — rejected as fragile)",
            "Kill claude.exe to test (rejected — would terminate the build session)"
        ],
        "audit_finding_refs": [],
        "methodology_source": "infrastructure_decision",
    },
    # ----- 2026-05-22 directive day -----
    {
        "ts_utc": "2026-05-22T15:55:00+00:00",
        "title": "Receipt of Phase 1 framework directive (ahmed_response_2026-05-22)",
        "decision": "Ahmed delivered comprehensive Phase 1 framework directive: 6 gate amendments, 6 watch-list improvements, re-validation discipline, three-filter selection methodology, Phase 1 strategy cap=4, framework finality (6-month freeze from commit date).",
        "rationale": "Replaces ad-hoc 'what should we try' with frozen executable methodology. Closes audit NEW-1 (watch list), NEW-3 (Decision Log), NEW-5 (Telegram log). Prevents amendment-chasing if Phase 1 results disappoint by binding the framework for 6 months.",
        "alternatives_considered": [],
        "audit_finding_refs": ["Session 5 NEW-1", "Session 5 NEW-3", "Session 5 NEW-5"],
        "methodology_source": "framework_directive",
    },
    {
        "ts_utc": "2026-05-22T15:58:00+00:00",
        "title": "Phase 1 cap = 4 candidates; Divergence grandfathered slot 1",
        "decision": "Phase 1 tests a maximum of 4 candidate strategies total under the three-filter methodology. Divergence fills slot 1 by grandfathering (Session-5 framework selection, pre-autonomous-loop). 3 slots remain. After 4 complete, Phase 1 testing closes until Phase 2 review post-6-month freeze.",
        "rationale": "Cap prevents 'keep testing until something clears' from becoming the de facto methodology. Grandfathering Divergence preserves the legitimately-cleared US strategy without inflating the trial budget retroactively.",
        "alternatives_considered": [
            "Cap fills with 4 cleared strategies (Divergence+MBV+PMR+STR) — Phase 1 closes immediately (rejected per Ahmed)",
            "All 13 strategies count as Phase 1 — directive applies only to Phase 2 (rejected — would defer the new methodology indefinitely)"
        ],
        "audit_finding_refs": [],
        "methodology_source": "ahmed_override",
    },
    {
        "ts_utc": "2026-05-22T15:58:30+00:00",
        "title": "13 sprint-loop strategies tagged Pre-Framework, sprint-loop-tested",
        "decision": "EMA-200, MBV, DBO, ROC, VCB, HAT, PMR, STR, ART, CMF, GAP, WCK + Divergence (grandfathered) get a Pre-Framework field in strategy_register.md. Verdicts stand as historical record. n_trials_registered=39 stays binding (cannot selectively reduce N without invalidating the discipline that produced the count).",
        "rationale": "Wipe-slate per Q1=B-modified. Existing test data is reusable as initial evidence for the three-filter methodology, but any Pre-Framework strategy selected by the methodology MUST re-validate under the amended gate on data not previously evaluated under those amendments.",
        "alternatives_considered": [
            "Cap fills with 4 cleared (option A — rejected, would close Phase 1 immediately and bypass the new methodology)",
            "Phase 1 already complete (option C — rejected, would skip Phase 1 entirely)"
        ],
        "audit_finding_refs": [],
        "methodology_source": "ahmed_override",
    },
    {
        "ts_utc": "2026-05-22T16:00:00+00:00",
        "title": "Pause autonomous sprint cron (aig-mode1-sprint)",
        "decision": "Disabled Cloud Routine `aig-mode1-sprint`. Watchdog (AIG-CC-Watchdog Windows Scheduled Task) stays running. Paper-forward detector + dashboard regen + commit don't fire automatically until SKILL.md is rewritten to directive-compliant flow.",
        "rationale": "The cron was running the Version-B autonomous methodology (enumerate prior primitives → pick unused domain), which Part 4 of the directive explicitly forbids. SKILL.md must be rewritten before the cron can re-enable.",
        "alternatives_considered": [
            "Keep cron firing with strategy-enrollment step removed (rejected — risk of stale state piling up, simpler to pause cleanly)",
            "Let cron run until WCK finalizes (rejected — risk of Strategy 14 enrolling under old methodology in the window)"
        ],
        "audit_finding_refs": [],
        "methodology_source": "framework_directive",
    },
    {
        "ts_utc": "2026-05-22T16:01:00+00:00",
        "title": "WCK US drain to completion as Pre-Framework",
        "decision": "WCK US (mid-drain at 800/1603 = 50%) is allowed to finish via manual `staged_validate --step` calls. Verdict landed as historical record. Tagged Pre-Framework regardless of outcome — not a Phase 1 candidate.",
        "rationale": "Stopping mid-drain creates an INCOMPLETE_SWEEP entry that violates the sweep rule. Finishing honors the discipline that already produced 800 ticker results. Outcome is honest history, not framework data.",
        "alternatives_considered": [
            "Stop now, mark INCOMPLETE_SWEEP (rejected — sweep-rule violation per Phase 1 directive)"
        ],
        "audit_finding_refs": [],
        "methodology_source": "ahmed_override",
    },
    {
        "ts_utc": "2026-05-22T16:01:30+00:00",
        "title": "Decision Log = dual format (.md + .json) with methodology_source",
        "decision": "decision_log.md (human-readable, append-only Markdown) + decision_log.json (machine-readable mirror, dashboard-readable). Writer helper: scripts/decision_log_append.py. Every entry carries a methodology_source field with one of 6 allowed values.",
        "rationale": "Markdown for human read + commit diffs; JSON for dashboard widget + Cowork raw-GitHub reads. methodology_source forces each decision to declare its provenance (directive vs methodology vs override vs audit vs infrastructure vs legacy), preventing decision drift.",
        "alternatives_considered": [
            "Markdown only (rejected — no dashboard widget)",
            "JSON only (rejected — loses the open-in-editor affordance)"
        ],
        "audit_finding_refs": ["Session 5 NEW-3"],
        "methodology_source": "ahmed_override",
    },
    {
        "ts_utc": "2026-05-22T16:02:00+00:00",
        "title": "Amendment 5 (GCC universe) deferred to Phase 2 infrastructure",
        "decision": "GCC universe expansion (Saudi/Kuwait/Qatar/Bahrain halal aggregate ~400-500 tickers) is a Phase 2 infrastructure build. Does NOT consume Phase 1 slots and is NOT required during the 6-month freeze. UAE-only certification remains the deployment gate for any GCC-discovered strategy.",
        "rationale": "GCC universe construction is multi-week (sourcing halal lists per market, OHLCV caching, integrity checks). Phase 1 cap=4 leaves no room for new strategy enrollment, so the only 'new Phase 1 work' the framework permits is infrastructure. Ahmed clarified GCC is Phase 2 work.",
        "alternatives_considered": [
            "Build GCC universe in Phase 1 (rejected — multi-week build collides with the 6-month freeze on framework)",
            "Defer indefinitely (rejected — Phase 2 review is when GCC gets considered for activation)"
        ],
        "audit_finding_refs": [],
        "methodology_source": "framework_directive",
    },
    {
        "ts_utc": "2026-05-22T16:02:30+00:00",
        "title": "Amendment 1 auto-execution layer deferred to Phase 2",
        "decision": "Auto-execution layer (orders fire to broker API without human approval per signal + idempotency + slippage + fail-safe halt) is a Phase 2 infrastructure build. Does NOT consume Phase 1 slots. Amendment 1 (relaxed WR floor for trend-following / breakout / momentum strategies under dSharpe ≥1.5 + PF ≥2.0 + CI positive) stays DORMANT until both auto-execution exists AND passes its own validation.",
        "rationale": "Human-in-the-loop execution can't reliably honor a strategy with 4-of-5 losing trades (humans deviate; once execution deviates, certified expectancy no longer applies). Auto-execution is a major build (broker API, slippage modeling, fail-safe halt). Ahmed clarified it's Phase 2 work.",
        "alternatives_considered": [
            "Activate Amendment 1 with current Telegram-tap workflow (rejected — workflow is human-in-loop, exactly what Amendment 1 forbids)",
            "Drop Amendment 1 entirely (rejected — keeps the low-WR option available for Phase 2 when infrastructure exists)"
        ],
        "audit_finding_refs": ["Session 5 Concern 4"],
        "methodology_source": "framework_directive",
    },
]


def _safe(s: str) -> str:
    # Windows cp1252 console can't encode arrows/em-dashes. The file content
    # is unaffected (utf-8); only the console echo is filtered.
    return s.encode("ascii", "replace").decode("ascii")


def main() -> int:
    appended = 0
    skipped = 0
    for e in ENTRIES:
        if e["title"] in existing_titles:
            print(f"skip (already exists): {_safe(e['title'])}")
            skipped += 1
            continue
        r = append(e)
        print(f"appended ({r['total_entries']:>2}): {_safe(r['title'])}")
        appended += 1
    print(f"\nbackfill summary: {appended} appended, {skipped} already present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
