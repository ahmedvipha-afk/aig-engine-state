# Gate-calibration workbook — Strand B (calibration data) + Strand A (amendment-wiring scope)

2026-06-16. Read-only analysis for the gate joint-calibration redesign (decision_log
52–59). **No gate/config/code changed.** Strand A is **PROPOSED, NOT EXECUTED.**

---

## STRAND B — candidate gate metrics: computable now vs needs capture

**Saved-artifact schema (what the validation JSONs actually store):**
- per-ticker `results[*]`: `ci_low, market, oos_expectancy(=PF), oos_n,
  oos_sharpe_deflated(=DSR), oos_sharpe_raw, oos_trades_per_year, passed, reasons,
  strategy, ticker, timeframe, verdict`
- `portfolio`: `portfolio_expectancy(PF), portfolio_win_rate, portfolio_sharpe_raw,
  portfolio_sharpe_deflated(DSR), portfolio_ci_low/high, portfolio_trades,
  universe_coverage, verdict`
- **The OOS trade-return arrays are STRIPPED on save. No skew/kurtosis, no
  max-drawdown / equity curve, no trade dates.**

### Computable NOW from artifacts (the EXISTING metrics) — US full-universe trials

| strat | PF | WR | SR_raw | DSR | CI_lo | trades | cov | verdict |
|-------|----:|----:|------:|----:|------:|-------:|----:|---------|
| cmf | 1.396 | 0.340 | 6.533 | 5.872 | +0.0091 | 17646 | 0.987 | FAIL |
| mbv | 1.302 | 0.531 | 4.889 | 4.365 | +0.0052 | 10833 | 0.960 | CLEAR |
| roc | 1.217 | 0.299 | 4.306 | 3.724 | +0.0050 | 34612 | 0.997 | FAIL |
| dbo | 1.298 | 0.341 | 3.498 | 2.941 | +0.0082 | 11910 | 0.995 | FAIL |
| trb50 | 1.152 | 0.510 | 3.483 | 2.802 | +0.0032 | 25760 | 0.994 | CLEAR |
| divergence | 1.227 | 0.448 | 3.080 | 2.606 | +0.0030 | 10715 | 0.916 | CLEAR |
| pmr | 1.268 | 0.473 | 2.894 | 2.263 | +0.0042 | 4759 | 0.880 | CLEAR |
| art | 1.209 | 0.349 | 2.693 | 2.041 | +0.0044 | 11733 | 0.986 | FAIL |
| ema200 | 1.556 | 0.186 | 2.257 | 1.962 | +0.0130 | 5361 | 0.954 | FAIL |
| vcb | 1.187 | 0.234 | 2.525 | 1.924 | +0.0035 | 18221 | 0.992 | FAIL |
| gap | 1.181 | 0.381 | 2.131 | 1.462 | +0.0030 | 7421 | 0.963 | FAIL |
| wck | 1.096 | 0.537 | 1.921 | 1.244 | +0.0008 | 16621 | 0.947 | CLEAR |
| hat | 1.071 | 0.370 | 1.669 | 1.039 | +0.0006 | 33451 | 0.995 | FAIL |
| str | 1.103 | 0.556 | 1.544 | 0.902 | +0.0008 | 9358 | 0.924 | CLEAR |
| tsm12 | 1.054 | 0.299 | 0.284 | -0.395 | -0.0085 | 3473 | 0.898 | FAIL |

(UAE/Crypto trials excluded from calibration: nearly all failed on trade-count/power,
not edge — low-N, not informative for threshold setting.)

### NOT computable from artifacts — need trade-level capture

| candidate metric | needs | in artifacts? |
|---|---|---|
| PSR (proper) | per-trade returns → SR + skew + kurtosis + n | NO (no skew/kurt) |
| Sortino | per-trade returns → downside deviation | NO |
| Calmar/MAR + maxDD | ordered trade returns → equity curve | NO (trades stripped) |
| tail / max-single-trade contribution | individual trade returns | NO |
| skew/kurtosis-corrected DSR | per-trade returns → moments | NO |

### Capture requirement (NOT executed — per instruction)

`split_backtest` already produces the ordered per-ticker `oos_trades` (return floats),
`is_trades`, and `oos_years` — they are dropped on save. A one-time **analysis re-run
(or re-save) that RETAINS the ordered OOS trade-return stream per ticker + `oos_years`**
makes **all** candidate metrics computable **without per-trade dates** (order +
window-years suffice for maxDD/Calmar; returns suffice for PSR/Sortino/tail/skew-kurt
DSR). Read-only w.r.t. the gate, but it is compute + needs Track-1 isolation.

---

## STRAND A — wiring the 3 unwired amendments: scope (PROPOSED, NOT EXECUTED)

| amendment | code change | data-plumbing prerequisite | depth |
|---|---|---|---|
| per-market trade floors (Am.2) | `portfolio_evaluate`: `g["min_trades"]` → `g["min_trades_by_market"].get(market, g["min_trades"])` (market from contributors/args) | none — data present | **LOCAL / trivial** |
| OOS ≥ 0.7×IS (Am.2-ext) | `evaluate()` carries `is_trades` into its result; `portfolio_evaluate` aggregates IS trades, computes IS Sharpe, checks `OOS_SR ≥ 0.7×IS_SR` | `is_trades` ALREADY produced by `split_backtest` (L178) but dropped at `evaluate()`; surface it through 2 spots; need `is_trades_per_year` for IS annualisation (compute as OOS does) | **MODERATE** (no backtest change) |
| 24-mo OOS span (Am.6) | **PROXY:** `portfolio_evaluate` checks contributing tickers' OOS-window span ≥ 24mo via `oos_years`. **EXACT:** per-trade dates | **PROXY:** surface `oos_years` (already computed, L173). **EXACT:** `_simulate` must emit per-trade entry/exit dates (deeper) | **LIGHT** (proxy) / **DEEP** (exact) |

### Caveats / coupling
- **per-market floors LOOSEN small markets** (UAE 1000→200, Crypto 1000→400) per the
  amendment's power-calibration; **US (the live market) is unchanged**. Not a rescue,
  but not strictly tightening for small markets — flag for principle-1 review.
- **OOS≥0.7×IS and span are `config_hash`-affecting and WILL re-run verdicts → they
  TRIGGER the migration test.** Their effect on the live slots **cannot be predicted
  from artifacts** (IS Sharpe is not stored). So **A's EXECUTION is coupled to C** —
  wire + re-run the migration test together; do **not** wire blindly before C.

### Pre-registration / test requirements for any A wiring
1. `decision_log` entry stating exactly what is enforced + the thresholds.
2. Recompute `config_hash`; commit `config.py` + `validation_gate.py` + register +
   tests **atomically** (provenance binding).
3. Unit tests per newly-enforced criterion: OOS≥0.7×IS triggers/passes correctly; a
   narrow-window sample fails span; per-market floors apply per market.
4. `tests/test_engine.py` green.
5. Anti-thicket: wire each only on proving incremental value; calibrate jointly; since
   wiring re-runs the migration test, sequence A's execution as the **first step of C**,
   not as a standalone change before it.
