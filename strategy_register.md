# Strategy Pre-Registration Log

Per v7.0 Section 19, every strategy is FROZEN before test data is seen, and
the provenance hash binds the spec to its results. This file lists the
pre-registered strategy specifications + the explicit **trial budget** that
the portfolio-gate multi-test haircut covers. The actual frozen parameters
live in `config.py`. If parameters change, the config hash changes and prior
results no longer apply to the new spec.

**Amendment 2026-05-21 (audit response):** strategy specs are explicitly
timeframe-agnostic at the rules level; each (strategy × market × timeframe)
combination is one **trial** and must be enumerated below before being run.
Per auditor Concern 5 — `strategy_register` and `config.py` must stay tied;
prior drift between EMA-200's registered "1H primary" and its actual daily
test runs was a provenance issue and is reconciled here.

---

## STRATEGY 1 — EMA-200 + Volume Confirmation (long only)

| Field | Value |
|-------|-------|
| Strategy id | `ema200` |
| Module | `aig/strategy_ema200.py` |
| Timeframes registered | **1H, 1D** (separate trials — see Trial Budget below) |
| Long only | YES (Rule 15) |
| Pre-registered | 2026-05-20 by CEO (1D trial added retroactively 2026-05-21 via this amendment) |

**Entry**: close > EMA(200) held for `CONFIRM_BARS=2` consecutive closes AND
entry-bar volume ≥ `VOLUME_MULT=1.2` × SMA(`VOLUME_PERIOD=20`) of volume.

**Stop**: entry − `STOP_ATR_MULT=2.0` × ATR(`ATR_PERIOD=14`).

**Exit**: close < EMA(200) OR ATR stop hit.

The same rules apply at any timeframe the engine supports (1H, 4H, 1D, 1W).
The TF is part of the trial identifier, not the spec.

---

## STRATEGY 2 — Bullish RSI Divergence (long only, regime-filtered)

| Field | Value |
|-------|-------|
| Strategy id | `divergence` |
| Module | `aig/strategy_divergence.py` |
| Timeframes registered | **1D** |
| Long only | YES — bullish divergence only, by construction |
| Pre-registered | 2026-05-20 by CEO |

**Entry**: a confirmed swing low at bar `i_recent` makes a lower price low than
the prior swing low `i_prior` (both within `DIV_LOOKBACK_BARS=60`) while
RSI(`DIV_RSI_PERIOD=14`) makes a higher low; AND today's close > yesterday's
close; AND today's close > EMA(`DIV_TREND_EMA=200`).

A swing low is confirmed only after `DIV_PIVOT_HALFWIDTH=5` bars have passed
without violating it — no look-ahead.

**Stop**: entry − (recent swing low − `DIV_STOP_ATR_MULT=1.5` × ATR(14)).

**Exit**: RSI ≥ `DIV_RSI_EXIT=65` OR ATR stop hit OR close < EMA(200)
(trend abandonment).

---

## TRIAL BUDGET (binding — multi-test haircut applies to ALL listed)

Per auditor Concern 1, the portfolio-gate's `deflated_sharpe` haircut is
applied over **N_trials_registered**, which equals the row count of this
table. Every entry below is a (strategy × market × timeframe × engine-source)
combination that has been run OR is committed to being run. Adding a new
trial means appending a row here BEFORE the run; the haircut recomputes.

| # | Trial id | Strategy | Market | Timeframe | Engine | Pre-registered | First-run date | Verdict (current) |
|---|----------|----------|--------|-----------|--------|----------------|----------------|-------------------|
| 1 | `ema200_us_1d`        | ema200     | US     | 1D | yfinance        | 2026-05-21 (this amendment) | 2026-05-20 | PORTFOLIO_FAIL (WR floor) |
| 2 | `ema200_uae_1d`       | ema200     | UAE    | 1D | yfinance+cache  | 2026-05-21 (this amendment) | 2026-05-20 | PORTFOLIO_FAIL |
| 3 | `ema200_crypto_1d`    | ema200     | CRYPTO | 1D | yfinance        | 2026-05-21 (this amendment) | 2026-05-20 | PORTFOLIO_FAIL |
| 4 | `divergence_us_1d`    | divergence | US     | 1D | yfinance        | 2026-05-20            | 2026-05-20 (re-confirmed 2026-05-21 under N=6 haircut) | **PORTFOLIO_CLEARED** — dSharpe 2.606, exp 1.227, WR 44.78%, 10,715 trades |
| 5 | `divergence_uae_1d`   | divergence | UAE    | 1D | yfinance+cache  | 2026-05-20            | 2026-05-20 | PORTFOLIO_FAIL (trades) |
| 6 | `divergence_crypto_1d`| divergence | CRYPTO | 1D | yfinance        | 2026-05-20            | 2026-05-20 | PORTFOLIO_FAIL |

**`config.PORTFOLIO_GATE.n_trials_registered` must equal the row count above.**
Current value: **6**.

### How to add a trial (procedure)

1. Append a new row to this table **before** running. Set "Pre-registered"
   to today's date.
2. Bump `n_trials_registered` in `config.py` to the new row count.
3. Run `python tests/test_engine.py` (must remain green).
4. Commit both files in the same commit (provenance binding).
5. Then run the new trial. Its verdict updates the table on completion.

Trials retired by removal of a strategy DO NOT reduce the haircut count —
the haircut is permanent for the project lifetime to prevent
selective-removal data-mining.

---

## TV Strategy Tester runs (separate from engine trial budget)

TV Strategy Tester runs use TradingView's deeper history but do not enter
the engine's pre-registered trial budget (they're cross-checks against the
engine, not separate claims). Logged for transparency:

| TV-run id | Strategy | Market | Timeframe | Count | Top finding |
|-----------|----------|--------|-----------|------:|-------------|
| `tv_ema200_us_1h_top10` | ema200 | US | 1H (TV history 5–7y) | 10 tickers | 3 CLEAN_EDGE (AAPL, GOOG, TSM); max Sharpe 0.20 — fails v7.0 §19 |

---

## Validation gates (frozen, applies to both strategies)

Two gates run on every validation pass. A strategy can clear one, both, or
neither. Cleared at any level → eligible for paper-forward at that level.

### Per-ticker gate (`GATE`, narrow claim)

Certifies "ticker X with strategy S has edge". OOS (post 60% train cut)
must satisfy ALL:

- OOS trades ≥ 30 (`GATE.min_trades`)
- OOS expectancy ≥ 1.0
- OOS deflated Sharpe ≥ 0.5 (Bailey & López de Prado haircut over **N
  tickers tested**)
- 95% bootstrap CI on mean trade return strictly > 0 (2000 iters)
- Walk-forward expectancy ≥ 1.0 (rolling 5-fold)

### Portfolio-level gate (`PORTFOLIO_GATE`, broad claim) — added 2026-05-20, haircut corrected 2026-05-21

Certifies "strategy S has edge across the universe". Aggregates ALL OOS
trades across the universe into one sample. Multi-testing haircut applied
at **N_trials_registered** (currently 6 per Trial Budget above). ALL must hold:

- Portfolio trades ≥ 1,000 (`PORTFOLIO_GATE.min_trades`)
- Portfolio expectancy ≥ 1.0
- Portfolio win rate ≥ 0.40
- Universe coverage ≥ 5% of non-blocked tickers must contribute trades
- Portfolio deflated Sharpe ≥ 0.5 (haircut over N_trials_registered)
- 95% bootstrap CI on portfolio mean trade strictly > 0

**Why two gates.** Per-ticker gate is statistically pessimistic for broad
strategies — the multi-test haircut scales with N_tickers and crushes any
per-name Sharpe even when the strategy has real aggregate edge. Portfolio
gate is the honest test for broad strategies (Divergence Daily across 1,600
US halal names). The narrow gate remains useful for concentrated single-name
plays.

Default verdict at either gate is FAIL. No override. (Per Decision 1 of the
reconciliation directive — same hard status as Shariah & Tier-1 circuit
breakers.)

---

## Audit linkage

Every run writes to `aig/audit_trail.md` with `config_hash` in the header and
agent tags on each verdict. `validation_<strategy>_<timeframe>.json` carries
the same provenance block. Reproducibility is the binding contract — if
either file's hash changes, the verdict is no longer claimable.

**2026-05-21 audit response** (auditor: Cowork):
- Concern 1 (haircut N=2 → N=6): RESOLVED. Trial budget now binding;
  `n_trials_registered=6`; US Divergence dSharpe recomputed.
- Concern 2 (Path 3 amendment): WITHDRAWN. Post-hoc threshold loosening
  removed from active proposals.
- Concern 5 (register drift): RESOLVED. EMA-200 explicitly timeframe-
  agnostic; trial budget captures every TF/market combination.
