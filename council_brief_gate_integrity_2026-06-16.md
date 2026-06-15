# COUNCIL BRIEF — VALIDATION-GATE INTEGRITY (aig_engine, 2026-06-16)

**Source records:** decision_log entries 52 (`a2760f4`) + 53 (`ce07997`). Read-only.
No verdict has been changed; no code/config/gate touched. This document is the
input to the council / cross-check round. The questions below are **POSED, not
answered** — the council answers them.

---

## CONTEXT

The Phase-1 framework adopted six amendments on 2026-05-22 (per-market trade
floors, profit-factor floor, OOS-Sharpe ≥ 0.7×IS robustness, 24-mo OOS span,
GCC-deferral, MTF-as-trials). The register presents them as binding/frozen. Two
facts about how they actually operate were discovered while preparing the
entry-46 win-rate-floor discussion.

## FINDING 1 — THE AMENDED GATE WAS NEVER WIRED (entry 52)

`config.py` `PORTFOLIO_GATE` **defines** the amendment keys
(`min_trades_by_market`, `min_profit_factor` [+`_ci_lower`/`_min_n`],
`min_oos_calendar_months`, `min_oos_to_is_sharpe_ratio`; L425-432). But
`aig/validation_gate.py` `portfolio_evaluate()` (L71-165) **reads none of them** —
it enforces only the legacy six (`min_trades`, `min_expectancy`,
`min_win_rate`=0.40, coverage, `min_oos_sharpe`=0.5, CI>0). `config.py` L407 itself
labels the enforced subset *"back-compat with existing validation_gate.py."*

⇒ **Every** portfolio verdict to date — all clears (Divergence, MBV, PMR, STR,
TRB-50 = slots 1-2 + paper-forward) and all fails — was produced by the
**original** gate. The amended gate has never executed. (Same class as
entry-47's Amendment-1 finding; broader: 5 of 6 amendments unenforced.)

## FINDING 2 — THE DOCUMENTED GATE IS, AS WRITTEN, UNCLEANABLE (entry 53)

`aig/stats.py` `expectancy()` (L16-24) = `sum(wins)/sum(|losses|)` = **profit
factor**. So the enforced `min_expectancy`=1.0 already imposes PF≥1.0, and
Amendment 3's `min_profit_factor`=1.5 is the **same statistic at a higher bar**.
No trial ever reached PF 1.5: cleared slots PF 1.10-1.30 (Divergence 1.227,
MBV 1.302, PMR 1.268, STR 1.103, TRB-50 1.152); all-time max cmf 1.396.

⇒ Enforcing the documented gate literally **fails every strategy ever tested** —
live slots 1-2 included — on Amendment 3 alone.

## THE CORE QUESTION SET (for the council — unanswered)

- **(a)** WHICH GATE IS REAL? The code gate that produced a working,
  paper-forward portfolio, or the documented gate that nothing passes?
- **(b)** Was PF≥1.5 ever achievable / feasibility-checked? (1.5 > observed max
  1.396.) Was the threshold set against data or aspiration?
- **(c)** Is "PF" even the intended metric, or was a different statistic meant
  (the code is unambiguous: `expectancy` == PF)?
- **(d)** If the documented amendments are unsound, is the remediation to FIX
  THE CODE to match the docs, or FIX THE DOCS to match a sound gate?
- **(e)** Forward-only vs re-validation of live slots — noting forward-only does
  NOT dodge it: under PF≥1.5 no FUTURE strategy could clear either.

## THE WR-FLOOR QUESTION (entry 46) — DEMOTED

The original WR-floor-by-archetype question is now one criterion among several
the documented gate imposes, and not the binding one. Revisit only AFTER the
gate-integrity question (a-e) resolves.

## HONEST FRAMING (for the council to confirm or reject)

This resembles the retired 3x/10x phantom-mandate pattern (entry 39) one level
down: an aspirational number embedded in the methodology, never checked against
achievable reality. If that read is correct, the fix is not to enforce the
number but to reconcile the framework with what an honest gate can actually
demand. The council should assess whether that characterization holds.

## CONSTRAINT ON THE COUNCIL'S ANSWER

The 3x/10x parallel has a limit the council must respect. Retiring an
aspirational **RETURN TARGET** to match reality was honest. Relaxing a
**VALIDATION GATE** to admit the existing portfolio is the OPPOSITE — it is the
goalpost-gravity the gate exists to resist. These are asymmetric: a target is
aspirational by nature, a gate is adversarial by nature.

Therefore "PF≥1.5 was never achievable" does NOT license "lower it to ~1.2 so
our strategies pass." The council must distinguish:

- PF≥1.5 was an error (wrong metric, or a number never feasibility-checked) and
  the REAL intended gate is the sound code gate (PF≥1.0 via `min_expectancy`)
  → then the fix is to FIX THE DOCS, gate unchanged, nothing re-cleared, no
  candidate admitted that wasn't already passing.
- vs. reverse-engineering ANY threshold from "what lets our current portfolio
  through" → **forbidden**; that is selection bias wearing a remediation costume.

The council should also test whether "PF" in Amendment 3 was meant as a
DIFFERENT statistic than the code's `expectancy` (which would mean the criterion
was non-redundant and simply unimplemented — a third option).

One evidentiary asymmetry the council should weigh: the **code gate has a track
record** (it produced a working paper-forward portfolio and correctly
discriminated TSM-12 FAIL from TRB-50 CLEAR); the **documented gate has never
executed and is uncleanable as written**. "Which gate is real" is therefore not
symmetric — one is an evidenced instrument, the other an untested spec with a
demonstrated math error.

## WHAT IS NOT IN QUESTION

The validation DISCIPLINE (pre-registration, OOS, multi-test haircut,
default-FAIL, no override) is intact and is not what failed here. What failed is
that a documented threshold set was neither wired nor feasibility-checked. Edge
still comes from validation, not from relaxing it.
