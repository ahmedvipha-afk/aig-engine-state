# PROJECT_MAP.md — aig_engine master index ("what's done, where it lives, why")

**This is the project's table of contents.** Any "what happened and why" question
should be answerable by reading this one file. Last updated 2026-06-17.

> **APPEND RULE (every future task adds ONE line):** when a task lands, append a
> one-liner to the relevant section as `**what** — why (hash/entry)`. Keep it to
> one line; the detail lives in the decision_log entry / doc it points to.

---

## 1. WHAT THIS IS
A Halal US/UAE/Crypto quant-strategy **validation engine**. It does not chase
returns; it runs an adversarial **validation gate** that decides whether a frozen,
pre-registered strategy has earned **paper-forward** observation. Default verdict
is FAIL. The binding contract is **reproducibility** (config/code hashes + frozen
data) and **audit trail** (every decision logged with who/why).

## 2. LIVE SLOTS (paper-forward) — status
- **US Slot 1: Divergence** — CLEARED (grandfathered, entry 8). Frozen-snapshot
  recheck held CLEAR: PF 1.215 / WR 0.445 / DSR 2.221 (entry 62).
- **US Slot 2: TRB-50** (trb50_us_1d, spec_hash a96ccdf5c0640e4f) — CLEARED entry
  49; recheck held CLEAR: PF 1.151 / WR 0.510 / DSR 2.773 (entry 62).
- **US Slots 3–4:** open. **UAE / Crypto:** no strategy cleared (small-market
  trade-count floor; definitive FAIL pattern across all trials).
- Both live slots **survived the data-freeze drift with zero verdict flips**
  (entry 62).

## 3. THE GATE
- **As it ACTUALLY runs:** [aig/GATE_PLAIN_ENGLISH.md](aig/GATE_PLAIN_ENGLISH.md)
  — now **7 enforced rules**: trades≥1000, expectancy≥1.0, WR≥0.40, coverage≥5%,
  deflated Sharpe≥0.5 @ N_trials=41, bootstrap CI>0, **+ R2 single-name P&L
  concentration ≤10% (entry 67)**, and the multiple-testing N is now an auto-counted
  trial ledger, not a literal (entry 70, config_hash 8d668f736ba1fb10).
  Code: `aig/validation_gate.py`.
- **Unwired amendments** (defined in `config.py PORTFOLIO_GATE`, never enforced):
  per-market floors (PARKED/OUT), PF≥1.5, OOS≥0.7×IS, 24-mo span, GCC. = Strand C.

## 4. STRAND C — gate redesign (NEXT, OPERATOR-SUPERVISED ONLY — not started)
- **Scope:** wire OOS≥0.7×IS + 24-month span, recompute `config_hash`, run the
  migration test. Per-market floors stay **PARKED/OUT** (loosening).
- **Design inputs it MUST open on:**
  - **entry 63** — the WR≥0.40 floor is doing *implicit tail-risk screening*; any
    replacement metric MUST capture tail fragility (skew/kurt/max-trade share) or
    it loosens the gate. PSR saturates ~1.0 → NOT a hurdle. DSR stays binding.
  - **entry 59** — council outcome: raise the haircut, drop flat PF≥1.5.
  - Calibration data: `gate_calibration_dataset_2026-06-16.json` (HASH3 15ef8b3).
  - Benchmark study: [aig/benchmark_study_gate_calibration.md].
  - Workbook: [aig/gate_calibration_workbook_2026-06-16.md].
  - Council brief: [council_brief_gate_integrity_2026-06-16.md].
- **Isolation note (for the migration test):** the `cron_paused.flag` blocks NEW
  sprint launches but does NOT abort an in-flight worker — confirm none running
  before isolating (entry 26; HANDOFF 2026-06-16).
- **STRAND-C PLAN (council-enriched; entries 64 + 65 — proposals to TEST, NOT wired):**

  **R0 — NEW TOP-PRIORITY RULE: REGIME / TIME-STABILITY + CROSS-SLOT** (whole-system
  council's strongest finding, Q2 — a gap NO current or proposed rule covers; goes
  AHEAD of R1–R4):
  - (a) **Temporal:** split OOS into halves, require PF>1.0 (edge holds) in BOTH —
    kills strategies whose whole edge came from one window/regime.
  - (b) **Cross-sectional:** pairwise slot correlation + joint-tail check, so two live
    slots can't draw down together invisibly (both load US equity factors).

  **R1–R4 — STAND, validated SAFE for the live book** (Q6 UNANIMOUS: all four wired
  TOGETHER do NOT un-clear either slot, even at DSR 1.5 — set is calibrated, not
  over-harsh):
  1. **Raise DSR floor 0.5 → ~1.0–1.5** — the "stricter on edge" lever (verify via
     migration: Divergence 2.22 / TRB-50 2.77 survive 1.5).
  2. ✅ **WIRED 2026-06-17 (entry 67):** single-name CONCENTRATION CAP = max 10% of
     total NET P&L per ticker (`max_single_name_pnl_share=0.10`), default-FAIL in
     `portfolio_evaluate`. config_hash → 3c56aead8f358363. Migration test: both live
     slots CLEAR (Divergence share 0.0247, TRB-50 0.0233 — zero flip). The first
     redesign rule in code; HHI/Gini complement may follow.
  3. **Tail-fragility check** — reject if WR<0.45 AND skew>4 or kurtosis>50 (entry 63).
  4. **KEEP 40% WR; the 60% idea is REJECTED** (P2 unanimous: clears zero, un-clears
     both slots) — hold 40% until R3 explicitly replaces its tail-screening function.
  - **Sequencing (Q4 consensus):** R2 = safe zero-flip FIRST step; **R3 must land
    BEFORE any WR change**; each step independently migration-tested on the frozen snapshot.

  **R5 — ROUTING-TIME CORRELATION SCREEN** (routing council, entry 68 Q2 — new gap):
  routing (best per-ticker DSR) is currently CORRELATION-BLIND; it can route factor-
  correlated tickers to one strategy, amplifying book-level drawdown the universe-wide
  gate never saw. Add a pairwise-correlation screen at routing time. Candidate alongside
  R0/R2.

  ✅ **WIRED 2026-06-17 (entry 70) — GATE-THRESHOLD DECAY / N-GROWTH FIXED** (the
  foundation item, flagged in councils 65 + 68): the deflated-Sharpe multiple-testing N
  is no longer the hardcoded `n_trials_registered=41` (a literal that claimed to grow but
  didn't) — it is now an **auto-counted `trial_ledger.json`** (distinct strategy×market×
  timeframe specs, idempotent on re-runs; `aig/trials.py`), read LIVE by
  `portfolio_evaluate`, auto-registered by `run_validation`, and hashed into config_hash.
  Self-maintaining + monotonic. config_hash 3c56aead8f358363 → **8d668f736ba1fb10**.
  Migration: both live slots CLEAR (N=41 today; zero flip; immune to realistic N-growth —
  breach only at N≈10²⁰/10³⁰). Option A (auto-track), not B.

  **C SUB-TASKS / OPEN ITEMS (entry 65):**
  - **Parsimony pass** (Q1/Q5): the set has real redundancy but seats named DIFFERENT
    cuts (retire PF / retire bootstrap-CI / fold R3 into DSR). Decide the cut WITH DATA
    — do NOT pre-pick.
  - **Snapshot tension** (Q8, OPEN QUESTION): the frozen snapshot fixes reproducibility
    but may mask alpha-decay. Likely answer: KEEP the frozen snapshot AND add a periodic
    refresh-and-re-test vs fresh data — decide deliberately, don't dismiss.
  - **Engine prerequisites** (Q3): before the cross-sectional engine, add turnover/
    cost-sensitivity + rank-time look-ahead checks; R3/R4 land before the engine.

  **ROUTING / ARCHITECTURE inputs (routing council, entry 68):**
  - **Q1 RESOLVED — universe-wide gate is the RIGHT default** (unanimous lottery defense).
    A sector/SUB-UNIVERSE validation tier is a **GATED FUTURE item** (like the cross-
    sectional engine), admissible ONLY with: pre-registered FIXED sectors + a Bonferroni/
    Šidák-raised DSR floor (~1.05 at 11 sectors; 1.2–1.5 for narrow sleeves) + grok's dual
    bar (a sleeve claim must ALSO clear a diluted full-universe hurdle, coverage≥2% /
    trades≥300). NEVER without the raised stats — unguarded = lottery in disguise.
  - **Q3 OPEN ARCHITECTURE CHOICE (not decided — deliberate operator call):** winner-take-
    one routing (gpt+grok: max edge + auditability + trivial R2) vs deterministic DSR-
    weighted ensemble (gemini: robustness, buffers a bad print, but dilutes edge +
    complicates R2). Constraint if ever ensemble: **fixed-weight only, never data-learned.**
  - **Q4 R0 DESIGN INPUT (for the R0 build session):** R2 stays at the gate on FULL
    contributors (unanimous); R0 cross-slot correlation measured on the ROUTED rosters
    (majority gemini+grok) with an optional full-contributor similarity cap ρ<0.8 (gpt).

  **PARKED — bigger-than-C reframes (entry 65 Q7; capture, don't scope yet):** factor-
  risk-allocation framework; Bayesian posterior expectancy + purged k-fold OOS; program-
  level FDR + subsample/rolling stability + cost stress + capacity model.

  *(Council INFORMS only — none of this is wired. Entries 64 + 65 + 68.)*

## 5. STANDING PRINCIPLES (locked — entry 57; operator memory)
1. **Stricter, never looser** — a gate redesign may only tighten; never reverse-
   engineer a threshold from what admits the current portfolio.
2. **Test breadth, not a winner factory** — measure many strategies fairly; don't
   tune to manufacture passes.
3. **Enforcement verified in code** — a rule counts only if `portfolio_evaluate`
   actually reads it (the entire entry-52 lesson).
4. **Benchmark + council before any gate change.**

## 6. DATA SOURCES
- **Canonical FROZEN snapshot (US+Crypto):** `data_cache/` — 1,727 CSVs, canonical
  sha256 **9d2dc9ff…100b**, frozen 2026-06-16 (HASH2 639eb9b, entries 60/61).
  Closes the repro gap (US data was never snapshotted; yfinance drifts).
- **Live source today:** yfinance (`aig/data.py`, period=15y, auto_adjust, today-
  anchored — drifts; that's why we freeze).
- **MCP / external data inventory + US-Vault consumption options:**
  [DATA_SOURCES_INVENTORY.md](DATA_SOURCES_INVENTORY.md) — incl. the US Vault's
  Sharadar-backed PIT OHLC cache as a candidate canonical US source (read-only).
- **UAE:** pinned via `data_cache` (TradingView-sourced); unaffected by the gap.

## 7. KEY DOCS
- [aig/engine_roadmap.md] — engine roadmap.
- [aig/GATE_PLAIN_ENGLISH.md] — the judge, in plain English (#3 above).
- [AUTONOMY_AND_ROLES.md](AUTONOMY_AND_ROLES.md) — bounded autonomy + 27-agent
  roles + principles + retired mandate.
- [DATA_SOURCES_INVENTORY.md] — MCP + US-Vault data inventory (#6).
- [strategy_register.md] / [winners_registry.md] — strategy specs + rosters.
- `decision_log.{json,md}` — the full audit chain (writer: `scripts/decision_log_append.py`).
- `ceo_brain.md` — **STALE** Phase-1 tracker (superseded; see AUTONOMY_AND_ROLES.md).

## 8. HASH REGISTRY (provenance anchors)
- HASH1 `291f19e` — entry 60 (reproducibility gap recorded).
- HASH2 `639eb9b` — canonical data snapshot frozen (sha256 9d2dc9ff…100b).
- HASH3 `15ef8b3` — entry 62 calibration capture + control (0 flips, faithful).
- `1a5cb27` — entry 63 (Strand-C tail-risk design input).
- spec_hash TRB-50 `a96ccdf5c0640e4f`; TSM-12 `efe8ac7b47f10a0f`.

## 8b. TRACK-1 INFRA HARDENING (separate from gate redesign — TODO, do deliberately)
Operational fixes surfaced 2026-06-18 during the Strand-C N-growth verification
session. NOT gate-redesign work; do NOT bundle into §4. Both UNWIRED — recorded so
they are not lost.
- **T1. Headless `git push` fails on interactive credential dialog.** The Track-1
  sprint commit step pushes via the default credential helper, which pops a
  GUI dialog that never resolves in a headless `claude -p` fire — so origin can lag a
  full sprint while HANDOFF reports "all pushed" (observed: origin stuck at `23a34eb`
  while local was 3 ahead). **Fix:** wire the `GH_TOKEN` / `x-access-token` push path
  (load token from `~/.claude/credentials/gh_token`, push with
  `http.extraheader`/URL form, credential manager disabled) into the Track-1 sprint
  commit step — the same path that recovered this session's push.
- **T2. `git add -A` sweeps transient artifacts into mainline.** The blanket stage in
  the sprint commit captured an ephemeral `scripts/cron_paused.flag` and published it to
  origin (cleaned up in `bfb3b46`). **Fix:** add `scripts/cron_paused.flag` and `*_out.txt`
  to `.gitignore` so transient/ephemeral artifacts can never reach a commit.

## 9. DECISION LOG — 1-63, one line each
1. Withdraw Path 3 (post-hoc gate amendment) — Session-5 audit response.
2. Deploy US Divergence Daily to paper-forward.
3. Watch list = top-5 by per-ticker OOS expectancy (SUPERSEDED).
4. Expand UAE universe 44→64 retrievable tickers.
5. Accept NO CERTIFIABLE CRYPTO EDGE verdict.
6. CC crash auto-recovery — watchdog design choices.
7. Receipt of Phase-1 framework directive (ahmed_response_2026-05-22).
8. Phase-1 cap = 4 candidates; Divergence grandfathered US slot 1.
9. 13 sprint-loop strategies tagged Pre-Framework.
10. Pause autonomous sprint cron (aig-mode1-sprint).
11. WCK US drain to completion as Pre-Framework.
12. Decision Log = dual format (.md + .json) with methodology_source.
13. Amendment 5 (GCC universe) deferred to Phase 2.
14. Amendment 1 auto-execution layer deferred to Phase 2.
15. Improvement 5 — hide tickers with OOS n<30 from per-ticker displays.
16. Improvement 1 — replace cherry-picked watch list with full cleared universe.
17. Fix watchdog false-fire loop — add cron_paused.flag intentional-pause check.
18. Fix crash_log.json JSON-via-argv encoding bug.
19. Flag-removal sequencing — coordination-gap retrospective.
20. Recreate cron_paused.flag (Option A) — coordinated pause restored.
21. 33d93ae commit message overstated completion — SKILL.md never landed.
22. Correction to 21 — SKILL.md DOES exist at user-scoped path; prior was scope error.
23. Cron re-enable — aig-mode1-sprint resumed after SKILL.md verification.
24. Sprint burst killed by watchdog — SKILL.md missing --mark-done between iters.
25. WCK US CLEARED via orphan-spawn — anomalous trigger, gate intact.
26. Watchdog-recovery-spawn gap — pauses stop NEW spawns, in-flight orphans finish.
27. Append to 24 — catch-up cap × iteration budget exceeds stale threshold by design.
28. Correction to 25/26 — timezone label error + second orphan-spawn instance noted.
29. SKILL.md patched — per-iteration --mark-done; catch-up sentinel-stale bug closed.
30. Correction to 29 — MCP description reflects frontmatter not body; verify flaw.
31. Cron re-enable (Option D) — first fire as verification; accept recovery gap.
32. Framework amendment — per-market caps; TV sources qualified; 12-mo coverage target.
33. Walk-forward research (Track 3) added as separate parallel effort.
34. Track-1 restart with explicit acceptance of recovery-spawn architecture gap.
35. Maintenance fire after ~17h gap — coverage/Phase-1 tracker flagged STALE.
36. Sprint iter 4/5 yfinance flap halt.
37. Recovery 2026-05-27 03:00Z — watchdog false-loop broken; orphan gap flagged.
38. Recovery 2026-05-27 04:05Z — watchdog runaway HALTED via flag; orphan isolated.
39. **Retire 3x/10x annual mandate** — replace with Kelly-bound 5–10% CAGR anchor.
40. Archive v7 Scope Document as historical-aspirational reference.
41. Phase-2 verdict — recovery-spawn gap fixed (watchdog v1.5); driver decision open.
42. Reserve Tareq pure-price-action system as Phase-B UAE candidate (lightweight).
43. Track-1 driver change (Task Scheduler + headless claude -p) — first fire FAILED; F1/F2/F3 fixes.
44. Track-1 driver RESTORED — restoration fire passed all 8 criteria; Track 1 LIVE.
45. Pre-register TSM-12 (trial 40) — first three-filter candidate, US slot 2.
46. TSM-12 verdict — PORTFOLIO_FAIL; US slot 2 remains open.
47. Amendment-1 adjudication — provenance ratified, provision dead letter, knobs removed.
48. Pre-register TRB-50 (trial 41) — second three-filter candidate, US slot 2.
49. **TRB-50 verdict — PORTFOLIO_CLEARED; US slot 2 FILLED.**
50. Deploy TRB-50 to paper-forward — watch-list pre-reg + second detector + routing.
51. Relocate Track-1 driver off OneDrive to C:\aig_engine (cured the hang class).
52. **Integrity gap — 2026-05-22 amendments unenforced by gate code.**
53. expectancy == profit factor; documented PF≥1.5 uncleanable (later corrected by 56).
54. Council round (degraded) — single-external-opinion input.
55. Amendment-3 PF≥1.5 intentional; remediation is operator-intent.
56. **Correction to 53/55 — PF≥1.5 IS achievable (ema200 1.556).**
57. **Gate joint-calibration project — setup, gated, four locked principles.**
58. Council charge — migration test for the stricter gate.
59. Gate-calibration council — raise haircut, drop flat PF≥1.5.
60. **Reproducibility gap — US market data was never snapshotted** (HASH1 291f19e).
61. **Canonical data snapshot frozen** — closes entry-60 gap (HASH2 639eb9b).
62. **Calibration capture on frozen snapshot — 0 flips, method proven faithful** (HASH3 15ef8b3).
63. **Calibration input to Strand C — WR floor is implicit tail-risk screening** (1a5cb27).
64. **Gate-redesign council — P2 (WR 0.60) REJECT, P1 (100 trades/stock) REJECT-as-stated; concentration cap is the sound core** (live slots ~310 eff names).
65. **Whole-system gate+roadmap council — 4-rule set keeps both live slots (Q6); regime/time-stability is the #1 uncovered gap** (2f79a2e).
66. **Strand-C plan enriched from entry 65 — regime rule added as top priority, parsimony + snapshot-decay sub-tasks recorded** (PROJECT_MAP §4).
67. **Strand C R2 WIRED — single-name P&L concentration cap (10%), default-FAIL; live slots zero-flip; config_hash → 3c56aead8f358363** (first redesign rule in code).
68. **Routing + universe-breadth council — universe-wide gate is the right default; sub-universe tier gated-future; routing is correlation-blind; Q3 winner-take-one vs ensemble split**.
69. **Routing-council inputs captured into Strand-C plan; N-growth gate-threshold decay elevated to near-term** (PROJECT_MAP §4).
70. **Strand C N-growth re-tighten WIRED — multiple-testing N is now an auto-counted trial ledger (not hardcoded 41); config_hash → 8d668f736ba1fb10; live slots zero-flip** (foundation fix).

---
*Pointers, not prose. Update the relevant section's one-liner whenever a task lands.*
