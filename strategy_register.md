# Strategy Pre-Registration Log

Per v7.0 Section 19, every strategy is FROZEN before test data is seen, and
the provenance hash binds the spec to its results. This file lists the
pre-registered strategy specifications; the actual frozen parameters live in
`config.py`. If parameters change, the config hash changes and prior results
no longer apply to the new spec.

---

## STRATEGY 1 — EMA-200 1H (long-only, with volume confirmation)

| Field | Value |
|-------|-------|
| Strategy id | `ema200` |
| Module | `aig/strategy_ema200.py` |
| Timeframe | **1H** (also runnable on 1D for cross-check) |
| Universe | US halal top-30 (then full US halal, then UAE, then crypto) |
| Long only | YES (Rule 15) |
| Pre-registered | 2026-05-20 by CEO |

**Entry**: close > EMA(200) held for `CONFIRM_BARS=2` consecutive closes AND
entry-bar volume ≥ `VOLUME_MULT=1.2` × SMA(`VOLUME_PERIOD=20`) of volume.

**Stop**: entry − `STOP_ATR_MULT=2.0` × ATR(`ATR_PERIOD=14`).

**Exit**: close < EMA(200) OR ATR stop hit.

**Hypothesis**: trend persistence on 1H beats daily because the 1H bar count
gives ≥6× more crossings per year, yielding the OOS sample size (n≥30) the
daily run failed on. Volume confirmation filters weak EMA-pierce noise.

---

## STRATEGY 2 — Bullish RSI Divergence Daily (long-only, regime-filtered)

| Field | Value |
|-------|-------|
| Strategy id | `divergence` |
| Module | `aig/strategy_divergence.py` |
| Timeframe | **1D** |
| Universe | US halal top-30 (then full US halal) |
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

**Hypothesis**: deep-pullback reversal in established uptrends offers
asymmetric reward (mean-reversion at a structural support level inside a
secular trend). Daily timeframe captures swing structure that 1H smooths
over.

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

### Portfolio-level gate (`PORTFOLIO_GATE`, broad claim) — added 2026-05-20

Certifies "strategy S has edge across the universe". Aggregates ALL OOS
trades across the universe into one sample. Multi-testing haircut applied
at **N_strategies registered** (currently 2), not N_tickers. ALL must hold:

- Portfolio trades ≥ 1,000 (`PORTFOLIO_GATE.min_trades`)
- Portfolio expectancy ≥ 1.0
- Portfolio win rate ≥ 0.40
- Universe coverage ≥ 5% of non-blocked tickers must contribute trades
- Portfolio deflated Sharpe ≥ 0.5 (haircut over N_strategies, not N_tickers)
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
