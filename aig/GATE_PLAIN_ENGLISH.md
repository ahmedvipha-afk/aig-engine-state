# THE VALIDATION GATE — IN PLAIN ENGLISH (what the judge ACTUALLY requires)

**Authoritative as-run reference.** Written from `aig/validation_gate.py`
`portfolio_evaluate()` **as it executes** — NOT from the documented/amended spec.
Last verified against code 2026-06-16 (decision_log entries 52–63).

A strategy is **CLEARED_FOR_PAPER_FORWARD** only if it passes EVERY rule below on
out-of-sample (OOS) data, after realistic costs, with the multiple-testing
correction applied. **Default verdict is FAIL. No override.** "Cleared" means
"earned the right to be watched live on paper" — not "proven."

The binding decision is the **PORTFOLIO** verdict (`portfolio_evaluate`), which
pools the OOS trades of every contributing ticker. (A per-ticker gate also runs
in `evaluate()`, but deployment is decided at the portfolio level.)

## THE 6 RULES ACTUALLY ENFORCED (all must pass; pooled OOS trade stream)

1. **Enough trades** — pooled OOS trades ≥ **1000** (`min_trades`).
   *Why:* too few trades = noise; you can't trust an edge measured on a handful.

2. **Makes money after costs** — expectancy ≥ **1.0** (`min_expectancy`).
   Expectancy here is **exactly the profit factor** = sum(winning returns) /
   sum(|losing returns|). ≥1.0 means total wins ≥ total losses, net of costs.
   *Why:* the floor of any real edge — it must not lose money.

3. **Wins often enough** — win rate ≥ **0.40** (`min_win_rate`), i.e. ≥40% of
   trades are profitable. Strict floor, binding for ALL strategy types.
   *Why:* (established in entry 63) this is **implicit tail-risk screening** — it
   rejects "lottery" edges whose profit hides in a few huge winners (high
   skew/kurtosis). Any future change replacing this MUST keep a tail-fragility
   check or it loosens the gate.

4. **Edge is broad, not a few names** — universe coverage ≥ **5%**
   (`min_universe_coverage`): at least 5% of the non-blocked universe must
   actually produce trades. *Why:* a strategy that only fires on a handful of
   tickers isn't a universe-level edge.

5. **Risk-adjusted edge survives the multiple-testing haircut** — deflated
   Sharpe ≥ **0.5** (`min_oos_sharpe`). Deflated Sharpe = raw annualised Sharpe
   − 0.25·√(2·ln(N_trials)), with **N_trials = 41** (every pre-registered trial,
   including the failures). *Why:* if you try many strategies, some look good by
   luck; the haircut raises the bar for having tried 41.

6. **The positive result is statistically robust** — the lower bound of the 95%
   bootstrap confidence interval on the mean trade must be **> 0** (and not NaN);
   2000 resamples, seeded. *Why:* the average trade must be reliably positive, not
   a fluke of the sample.

## WHAT IS **DEFINED IN config.py BUT NOT ENFORCED** (the unwired amendments)

`portfolio_evaluate()` reads NONE of these — they exist in `PORTFOLIO_GATE` but
the gate code never references them. They are **Strand-C territory** (operator-
supervised), NOT part of today's judge:
- `min_trades_by_market` (Amendment 2 — per-market trade floors) — **PARKED/OUT**
  (would loosen small markets; violates stricter-never-looser).
- `min_profit_factor` = 1.5 + `min_profit_factor_ci_lower` (Amendment 3) — same
  metric as Rule 2 at a higher bar; never wired. (entries 53–56)
- `min_oos_calendar_months` (Amendment 6 — 24-month OOS span).
- `min_oos_to_is_sharpe_ratio` (Amendment 2-ext — OOS ≥ 0.7×IS Sharpe).
- `gcc_universe_enabled` (Amendment 5 — GCC universe) — deferred to Phase 2.

→ Every verdict to date (all CLEARs incl. live slots Divergence + TRB-50, and all
FAILs) was produced by the **6 rules above only**. See decision_log entry 52.

## PER-TICKER GATE (context; not the deployment decision)
`evaluate()` applies the same family per ticker (min_trades, expectancy≥1.0,
deflated Sharpe≥0.5 with N_trials = ticker count, bootstrap CI>0, plus
walk-forward expectancy≥1.0). Per-ticker clearance is informational; **portfolio
clearance is the binding edge evidence** and contributors inherit deployability.

## STANDING CONSTRAINT
Any gate redesign must be **stricter, never looser**, and thresholds may **never**
be reverse-engineered from what admits the current portfolio. See
[standing principles] in PROJECT_MAP.md and decision_log entry 57.
