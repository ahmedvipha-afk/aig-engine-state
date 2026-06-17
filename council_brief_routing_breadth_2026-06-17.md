# COUNCIL BRIEF — ROUTING + UNIVERSE-BREADTH review (2026-06-17)

**Review-prep. Nothing wired. Council INFORMS only.** Pressure-test the engine's
validation-breadth + strategy-routing architecture. Answer on the ACTUAL code facts
below; reason independently, bring your own numbers/alternatives, flag at least one
challenge not in the brief.

---

## PART A — THE FACTS

### A1. The gate as it ACTUALLY runs (universe-wide, default FAIL, 7 rules)
`portfolio_evaluate` judges a strategy across the WHOLE ~1,600-ticker halal universe
and emits ONE portfolio verdict. All must pass:
1. pooled OOS trades ≥ 1000  2. expectancy ≥ 1.0 (== profit factor)  3. win rate ≥ 0.40
4. universe coverage ≥ 5%  5. deflated Sharpe ≥ 0.5 [raw − 0.25·√(2·ln 41)]
6. bootstrap CI lower bound > 0  7. **single-name P&L concentration ≤ 10%** (R2, wired
2026-06-17). A strategy must clear the FULL universe before it may trade ANY ticker.

### A2. Routing logic (ACTUAL — scripts/reassign_best_strategy.py, post-gate)
- Candidates = ONLY strategies whose portfolio gate CLEARED (today: Divergence, TRB-50;
  US). Per-ticker rows pulled from saved validation JSONs.
- Each contributing ticker (oos_n>0) is assigned to the strategy with the **highest
  per-ticker DEFLATED SHARPE; tie-break highest expectancy** (L153; criterion string
  L176). Deterministic, pre-registered. Winner-take-one: each ticker → exactly ONE
  strategy (no blending, no double-count).
- SELECTION happens ONLY here, post-gate, among already-cleared strategies. The gate
  itself has NO per-ticker selection — it judges universe-wide. Two distinct layers:
  **universe-wide GATE → best-per-ticker ROUTING.**

### A3. Standing principles (locked, entry 57)
1. Stricter, never looser (no reverse-engineering a threshold to admit the portfolio).
2. Test breadth, not a winner factory.
3. Enforcement verified in code.
4. Benchmark + council before any gate change.

### A4. Live portfolio state
- US Slot 1 Divergence: PF 1.215 / WR 0.445 / DSR 2.221 (LIVE).
- US Slot 2 TRB-50: PF 1.151 / WR 0.510 / DSR 2.773 (LIVE).
- Both ~310 effective names (max single-name P&L ~1% of gross); zero concentration.
- Slots 3–4 open; UAE/Crypto uncleared (small-market trade-count floor). Long-only,
  no-leverage, halal-screened universe. Kelly-bound realistic anchor (5–10% CAGR;
  3x/10x mandate retired). Reproducibility via a frozen canonical snapshot.
- Calibration: DSR is the binding edge metric; WR floor does implicit tail-screening.

### A5. The candidate gate redesign (context; R2 wired, rest proposed)
R0 (NEW, top priority) regime/time-stability + CROSS-SLOT correlation; R1 raise DSR
floor 0.5→1.0–1.5; R2 concentration cap (WIRED); R3 tail-fragility (WR<0.45 & skew>4|
kurt>50); R4 keep 40% WR. Plus a roadmap item: a future cross-sectional ranking engine.

---

## PART B — THE CHARGE (the operator's real questions)

**Q1 — UNIVERSE-WIDE BAR.** The gate judges a strategy across the WHOLE ~1,600-ticker
universe before it may trade ANY single ticker — rationale: kill per-ticker lottery/
overfitting (some strategy always looks great on some stock by luck). Is universe-wide
the RIGHT breadth, or too blunt? Should there be a SECTOR-level or ticker-class-level
validation tier for strategies that legitimately work only on a subset (e.g. real on
energy names but diluted to FAIL across the full universe)? What do rigorous shops do —
global vs per-sleeve validation, and how do they control multiple-testing when they
allow sub-universe claims?

**Q2 — ROUTING BASIS.** Routing assigns each ticker to the highest per-ticker DEFLATED
SHARPE among cleared strategies (tie-break expectancy). Is risk-adjusted-per-ticker the
right basis, or should it be diversification-aware / capacity-aware / regime-aware?
What failure mode does highest-per-ticker-Sharpe routing have that the universe-wide
gate does NOT already catch?

**Q3 — THE TWO-LAYER MODEL.** Is "universe-wide gate THEN best-per-ticker routing"
sound architecture, or is there a better one — e.g. an ENSEMBLE/BLEND per ticker
(weight multiple cleared strategies) instead of winner-take-one; or PORTFOLIO-LEVEL
optimization (allocate across cleared strategies × tickers jointly) instead of
independent per-ticker assignment? Name the concrete trade-offs.

**Q4 — INTERACTION.** How should routing interact with R2 (concentration cap, measured
at the gate over full universe-wide contributors) and the proposed R0 (cross-slot
correlation)? Specifically: should R0's correlation be measured on the ROUTED
(partitioned, one-ticker-one-slot) rosters or on the FULL contributor sets — and does
winner-take-one routing help or hurt cross-slot diversification?

**HARD CONSTRAINT:** stricter-but-SOUND; no loosening, no winner-factory, no
reverse-engineering. Flag anything that adds complexity without edge, and flag any
proposal that would let sub-universe cherry-picking reintroduce the overfitting the
universe-wide bar exists to prevent. INFORMS only — nothing is wired from this.

---
*Seats: openai/gpt-5.1 + google/gemini-2.5-pro + x-ai/grok-4.3 (3 distinct families).
Run-time guards: verify distinct IDs + finish_reason=stop; cap gemini reasoning; abort
on any degrade. Answer Q1–Q4, labeled; independent reasoning required.*
