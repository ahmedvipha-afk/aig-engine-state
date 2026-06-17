# COUNCIL BRIEF — WHOLE-SYSTEM REVIEW of the gate + roadmap (2026-06-17)

**Review-prep. Nothing wired.** This is the input for a 3-seat council that reviews
the gate + redesign + roadmap **as a system** — NOT to re-litigate each rule (done
in entries 52–64) but to test **coherence, gaps, interactions, sequencing**.

---

## PART A — SYSTEM SNAPSHOT (the facts the council reviews)

### A1. The 6 gate rules ACTUALLY enforced today (`portfolio_evaluate`, default FAIL, all must pass)
1. pooled OOS trades ≥ 1000 (no per-ticker floor)
2. expectancy ≥ 1.0 (expectancy == profit factor == Σwins/Σ|losses|)
3. win rate ≥ 0.40
4. universe coverage ≥ 5% of tickers contribute trades
5. deflated Sharpe (DSR) ≥ 0.5 [raw annualised Sharpe − 0.25·√(2·ln 41), 41 trials]
6. lower bound of 95% bootstrap CI on mean trade > 0

### A2. Unwired amendments (defined in config, NEVER read by the gate code)
- PF ≥ 1.5 (Amendment 3) — same metric as Rule 2 at a higher bar; never wired; the
  council already advised dropping the flat version (entry 59).
- OOS Sharpe ≥ 0.7×IS Sharpe (Amendment 2-ext) — not wired; IS Sharpe not stored.
- 24-month OOS calendar span (Amendment 6) — not wired.
- per-market trade floors (Amendment 2) — **PARKED/OUT** (loosens small markets;
  violates principle 1).
- GCC universe (Amendment 5) — deferred to Phase 2.

### A3. The 4 candidate redesign rules (entry 64 / PROJECT_MAP §4 — proposals, NOT adopted)
- **R1: raise DSR floor 0.5 → ~1.0–1.5** (the "stricter on edge" lever; unanimous).
- **R2: single-name CONCENTRATION CAP** (max ~10–15% of total P&L per ticker, or an
  HHI/Gini ceiling) — fills a real gap (no concentration guard today).
- **R3: tail-fragility check** — reject if WR<0.45 AND skew>4 or kurtosis>50
  (operationalizes entry-63: the WR floor does implicit tail-screening).
- **R4: keep the 40% WR floor for now; DROP the 60% idea** (P2 unanimous REJECT) —
  hold 40% until R3 can explicitly replace its tail-screening function.

### A4. The roadmap (captured, gated, NOT started) — `aig/engine_roadmap.md`
- **Cross-sectional engine capability:** add rank-the-universe / select-top-fraction
  dispatch alongside per-ticker dispatch, so momentum (Jegadeesh-Titman), low-vol/BAB,
  and stat-arb can be tested in their real published form (not distorted per-ticker).
- Framed as **test-breadth infrastructure, NOT a winner factory**; does not change the
  Kelly 5–10% bound (entry 39).
- **Gates before build:** (1) entry-46 WR-floor question resolved FIRST (the low-WR T1
  strategies it unlocks hit the same floor); (2) Track 1 provably stable; (3) tested
  through the SAME unchanged gate + pre-registration; (4) long-only/no-leverage/halal
  still bind (rules out the short leg of classic momentum/BAB).

### A5. Standing principles (locked, entry 57)
1. Stricter, never looser (no reverse-engineering a threshold to admit the portfolio).
2. Test breadth, not a winner factory.
3. Enforcement verified in code (a rule counts only if `portfolio_evaluate` reads it).
4. Benchmark + council before any gate change.

### A6. Live portfolio state (the real stakes)
- **US Slot 1 Divergence:** PF 1.215 / WR 0.445 / DSR 2.221 (LIVE).
- **US Slot 2 TRB-50:** PF 1.151 / WR 0.510 / DSR 2.773 (LIVE).
- Slots 3–4 open; UAE/Crypto uncleared (small-market trade-count floor).
- **Concentration diagnostic (entry 64, read-only):** both live slots ~310 effective
  names — Divergence max single name 1.07% of gross profit (HHI 0.00322); TRB-50 1.06%
  (HHI 0.00319). Both pass a 10–15% cap with huge margin.
- **Reproducibility fix:** US data is now a frozen canonical snapshot (sha256
  9d2dc9ff…100b, entries 60/61); capture on it showed 0 verdict flips (entry 62).
- Calibration: CLEAR slots low-skew (~0.7–1.5); WR-floor FAILs lottery-shaped
  (skew 5–12, kurt 60–236). DSR is the binding edge metric; PSR saturates (~1.0) at
  these trade counts (non-discriminating).

---

## PART B — THE CHARGE (cross-cutting, whole-system questions)

Answer on the actual data above. Reason independently; bring your own numbers and at
least one challenge not in this brief.

**Q1 — INTERACTION / THICKET.** Do R1–R4 interact badly? Specifically: does
**raised DSR floor (R1) + tail check (R3)** together become too harsh, redundant, or
reject good *convex* strategies (high skew but genuine positive expectancy)? Is the
SET of rules coherent, or is it becoming a thicket (the last council's own warning)?
Which rules are complements vs substitutes?

**Q2 — GAPS.** Is there a failure mode NO current (A1) or proposed (A3) rule catches?
(e.g. regime dependence / all profit in one period; long-only crash exposure;
cost-model fragility; correlation between the two live slots; multiple-testing creep
as trials grow.) Name the highest-priority uncovered failure mode.

**Q3 — ROADMAP CONFLICT.** Does the cross-sectional engine (A4) conflict with any gate
principle, or change what the gate must check? Note: it unlocks low-WR strategies that
hit the WR floor — so does the gate redesign (R3/R4) need to LAND BEFORE the engine
work, and does the engine introduce a need the 6 rules don't cover (e.g. turnover /
rebalance-cost, cross-sectional look-ahead)?

**Q4 — SEQUENCING.** In what ORDER should R1–R4 be wired, and what depends on what?
(We know R3 tail-check must precede any WR-floor change.) Give a dependency-ordered
sequence, each step independently testable via the migration test.

**Q5 — OVERALL.** After the redesign (R1–R4 wired, amendments resolved), is the system
STRICTER and SOUND (principle 1) — or are we adding complexity without adding edge
discrimination? If you'd cut or merge any rule for parsimony, say which and why.

**HARD CONSTRAINT:** every change must be stricter-but-SOUND. Flag anything that
loosens, tightens on a non-edge axis, or is complexity without discriminating power.
Council INFORMS only — nothing is wired from this.

---
*Seats: openai/gpt-5.1 + google/gemini-2.5-pro + x-ai/grok-4.3 (3 distinct families).
Verify distinct IDs + finish_reason=stop at run time; abort on any degrade.*
