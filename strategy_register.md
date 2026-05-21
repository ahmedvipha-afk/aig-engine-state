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

## STRATEGY 3 — MBV: Market Bias + Range + Volume (long only)

| Field | Value |
|-------|-------|
| Strategy id | `mbv` |
| Module | `aig/strategy_mbv.py` |
| Timeframes registered | **1D** |
| Long only | YES (Rule 15) |
| Pre-registered | 2026-05-21 by CEO (before any MBV test data was seen) |

**Concept**: long-only mean-reversion *inside* an established bullish trend.
Three independent filters must align on the entry bar:

1. **Market Bias** — `close > EMA(MBV_TREND_EMA=200)`. Bullish trend intact.
2. **Range** — close sits in the lower third of the trailing
   `MBV_RANGE_BARS=20` high/low range (`range_pct ≤ MBV_RANGE_FLOOR=0.33`),
   computed on bars shifted by 1 so the current bar's high/low never
   contaminates the range it's tested against.
3. **Volume confirmation** — `volume ≥ MBV_VOLUME_MULT=1.2 × SMA(MBV_VOLUME_PERIOD=20)`.

Entry is edge-triggered: the bar must be the FIRST to enter the lower
third (yesterday's `range_pct` must have been above floor). Prevents
re-entry during a sustained decline.

**Stop**: entry − `MBV_STOP_ATR_MULT=1.5` × ATR(14).

**Exit**: `range_pct ≥ MBV_RANGE_MID=0.50` (mean reversion completed) OR
`close < EMA(200)` (trend breakdown) OR ATR stop hit.

**Hypothesis**: in a confirmed uptrend, brief pullbacks to the lower third
of recent range — confirmed by elevated volume — offer asymmetric
risk/reward as institutional buyers step in. v7.0 §19 quoted backtest
estimate: ~112% / -4.65% DD / 52% WR on 1H. AIG registration is on 1D
to match engine-side data depth; 1H variant can be added later as a
separate trial.

---

## STRATEGY 4 — DBO: Donchian Breakout + Volume (long only) — NEW 2026-05-21

| Field | Value |
|-------|-------|
| Strategy id | `dbo` |
| Module | `aig/strategy_dbo.py` |
| Timeframes registered | **1D** |
| Long only | YES (Rule 15) |
| Pre-registered | 2026-05-21 by CEO Fire 1 (BEFORE seeing data — Phase 1 directive F1 genuine new methodology) |

**Concept**: long-only **trend-following BREAKOUT** strategy. Buys on price
strength — when close punches above the trailing 20-day Donchian high *and*
the breakout is confirmed by elevated volume. Methodologically distinct
from the three existing strategies:

- **EMA-200**: trend confirmation via long EMA + recent bullish action
  (buys established trend follow-through).
- **Divergence**: mean-reversion at bullish oversold (buys RSI hookup at lows).
- **MBV**: mean-reversion *inside* uptrend (buys low-range pullback + volume).
- **DBO**: BREAKOUT — buys strength when price makes new highs (NOT mean-rev).

**Hypothesis**: markets that don't show enough mean-reversion edge (UAE, Crypto)
may show breakout edge. The thesis is genuinely different from the three
existing strategies' shared mean-reversion-or-trend-confirmation lineage.
Frozen BEFORE seeing data per audit Concern 2 — failure is acceptable.

**Entry**: close > 20-day Donchian high (`max(high[-20:-1])`) AND
volume ≥ `DBO_VOLUME_MULT=1.5` × SMA(`DBO_VOLUME_PERIOD=20`) of volume.
Donchian high is shifted by 1 bar so the current bar's high never
contaminates its breakout test (look-ahead-free).

**Stop**: entry − `DBO_STOP_ATR_MULT=2.0` × ATR(14).

**Exit**: close < 10-day Donchian low (`min(low[-10:-1])`) — trend
breakdown — OR ATR stop hit. Tighter exit window than entry window
(asymmetric Donchian) so winners run and losers cut quickly.

---

## STRATEGY 5 — ROC: Rate-of-Change Momentum (long only) — NEW 2026-05-21 Fire 1.5

| Field | Value |
|-------|-------|
| Strategy id | `roc` |
| Module | `aig/strategy_roc.py` |
| Timeframes registered | **1D** |
| Long only | YES (Rule 15) |
| Pre-registered | 2026-05-21 Fire 1.5 (BEFORE seeing any ROC data — Phase 1 directive F1) |

**Concept**: long-only **velocity-based momentum**. Buys when the rate of
price change over the lookback window exceeds a positive threshold AND
that velocity is itself accelerating AND the broader regime is bullish.
Methodologically distinct from the four prior strategies:

- **EMA-200** (trend-confirm): position-based — close > long EMA, volume confirm.
- **Divergence** (mean-rev-on-low): RSI hookup at lows in bullish regime.
- **MBV** (mean-rev-in-uptrend): low-range pullback inside trend + volume.
- **DBO** (breakout): close crosses ABOVE a level (Donchian high).
- **ROC** (momentum-velocity): NOT level-based and NOT mean-rev — buys VELOCITY
  of price change. Two stocks at the same EMA distance can have very different
  ROC; ROC captures *how fast* price is moving, not where it stands.

**Hypothesis**: markets that don't show mean-reversion edge or pure breakout edge
may show momentum-velocity edge. Velocity captures regime states that pure
level-crossing misses. Frozen BEFORE seeing data — failure is acceptable.

**Entry** (all three must hold on the entry bar):
1. `ROC(ROC_PERIOD=20) > ROC_THRESHOLD=0.05` (5% over the lookback window) —
   strong positive momentum.
2. `ROC(20) > ROC(20).shift(1)` — velocity is RISING (acceleration), not
   decelerating off a recent peak.
3. `close > SMA(ROC_TREND_SMA=50)` — broader regime is bullish, no
   long-side trades in confirmed downtrends.

**Stop**: entry − `ROC_STOP_ATR_MULT=2.0` × ATR(14).

**Exit**: `ROC(20) < 0` (momentum has reversed) OR ATR stop hit OR
`close < SMA(50)` (regime broke).

Entry is edge-triggered: the bar must be the FIRST to meet all three
conditions (yesterday at least one was false). Prevents continuous re-entry
during sustained momentum runs — those are already captured by the initial
entry.

---

## STRATEGY 6 — VCB: Volatility Compression Breakout (long only) — NEW 2026-05-21 Fire 2

| Field | Value |
|-------|-------|
| Strategy id | `vcb` |
| Module | `aig/strategy_vcb.py` |
| Timeframes registered | **1D** |
| Long only | YES (Rule 15) |
| Pre-registered | 2026-05-21 Fire 2 (BEFORE seeing any VCB data — Phase 1 directive F1) |

**Concept**: long-only **volatility-cycle** strategy. Buys when realized
volatility (ATR) compresses to a 20-day low AND the broader regime is
bullish AND the bar shows directional pickup. Captures the canonical
"compression precedes expansion" cycle. Methodologically distinct from
the five prior strategies:

- **EMA-200** (trend-confirm): position-based — close > long EMA.
- **Divergence** (mean-rev-on-low): RSI hookup at lows.
- **MBV** (mean-rev-in-uptrend): low-range pullback inside trend.
- **DBO** (breakout): close crosses a Donchian level.
- **ROC** (velocity-momentum): rate of price change.
- **VCB** (vol-cycle): **VOLATILITY** is the primary input. Two stocks
  at the same EMA distance / momentum / Donchian level can have very
  different ATR profiles; VCB sees the regime-state difference that
  pure price-based strategies miss.

**Hypothesis**: volatility cycles. Compression-bottoms are followed by
expansion. Restricting to bullish regimes makes expected expansion
direction long. Frozen BEFORE seeing data per audit Concern 2.

**Entry** (all three must hold on the entry bar, edge-triggered):
1. `ATR(14) == min(ATR(14))` over trailing `VCB_ATR_LOOKBACK=20` bars
   (volatility at a local low).
2. `close > SMA(VCB_TREND_SMA=50)` (bullish regime).
3. `close > close.shift(1)` (directional pickup confirmation).

**Stop**: entry − `VCB_STOP_ATR_MULT=2.0` × ATR(14).

**Exit**: `ATR(14) > VCB_EXPANSION_MULT=1.5 × mean(ATR over 20 bars)`
(expansion released), OR `close < SMA(50)` (regime broke), OR ATR stop hit.

---

## STRATEGY 7 — HAT: Heikin-Ashi Trend Continuation (long only) — NEW 2026-05-21 Fire 14:55 UTC

| Field | Value |
|-------|-------|
| Strategy id | `hat` |
| Module | `aig/strategy_hat.py` |
| Timeframes registered | **1D** |
| Long only | YES (Rule 15) |
| Pre-registered | 2026-05-21 Fire 14:55 UTC (BEFORE seeing any HAT data — Phase 1 directive F1) |

**Concept**: long-only signal derived from SMOOTHED (Heikin-Ashi) candles
rather than raw OHLC. Methodologically distinct from the six prior strategies
— every prior strategy operates on RAW bars (close > EMA, close > Donchian
high, range_pct on raw high/low, ROC on raw close, ATR-min on raw ATR). HAT
replaces the raw OHLC input with a recursive filtered representation:
HA_close = (O+H+L+C)/4, HA_open = (prev_HA_open + prev_HA_close)/2. The
recursive filter dampens individual-bar noise and surfaces multi-bar trend
regimes that raw-bar strategies miss.

- **EMA-200** (trend-confirm), **Divergence** (mean-rev-on-low),
  **MBV** (mean-rev-in-uptrend), **DBO** (breakout), **ROC** (velocity-momentum),
  **VCB** (vol-cycle): all RAW-bar inputs.
- **HAT** (smoothed-trend): SMOOTHED-bar input. Two stocks with identical raw
  OHLC but different smoothing trajectories (because HA is recursive — depends
  on prior HA_open) can have different entries. Captures the multi-bar
  cleanliness of a trend that raw-bar strategies see as a single bullish bar.

**Hypothesis**: noisy markets (UAE / Crypto) where raw-bar strategies fail on
WR floor may show edge under noise-smoothed entry/exit signals. The HA filter
is a different functional form than any of the six prior strategies' filters,
not a parameter retune. Frozen BEFORE seeing data per audit Concern 2.

**Entry** (all three must hold on the entry bar, edge-triggered):
1. `HAT_BULLISH_BARS=3` consecutive bullish HA candles ending today
   (HA_close > HA_open for the last 3 bars).
2. raw `close > EMA(HAT_TREND_EMA=200)` — regime filter on raw price.
3. `volume >= HAT_VOLUME_MULT=1.2 * SMA(HAT_VOLUME_PERIOD=20)` of volume.

Edge-triggered: yesterday at least one of (1) or (3) was false. Prevents
continuous re-entry while a sustained bullish HA run persists.

**Stop**: entry − `HAT_STOP_ATR_MULT=2.0` × ATR(14).

**Exit**: HA candle turns bearish (`HA_close <= HA_open`) OR
raw `close < EMA(200)` (regime broke) OR ATR stop hit.

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
| 7 | `mbv_us_1d`           | mbv        | US     | 1D | yfinance        | 2026-05-21            | 2026-05-21 | **PORTFOLIO_CLEARED** — dSharpe 4.365, exp 1.302, WR 53.06%, 10,833 trades, 96.0% coverage |
| 8 | `mbv_uae_1d`          | mbv        | UAE    | 1D | yfinance+cache  | 2026-05-21            | 2026-05-21 | PORTFOLIO_FAIL (36 trades < 1000; CI lo<0) |
| 9  | `mbv_crypto_1d`       | mbv        | CRYPTO | 1D | yfinance        | 2026-05-21            | 2026-05-21 | PORTFOLIO_FAIL (WR 35.9% < 40%, dSharpe -0.175) |
| 10 | `dbo_us_1d`           | dbo        | US     | 1D | yfinance        | 2026-05-21 (Fire 1)   | 2026-05-21 | **PORTFOLIO_FAIL on WR-floor only** — 11,910 trades, exp 1.298, WR 34.1% (< 40% floor), raw Sharpe 3.498, **dSharpe 2.941** (above 0.5 floor), 99.5% coverage. Math is strong (Calmar-like breakout signature: low WR, big winners). Honest FAIL retained per audit Concern 2. Research-grade only. |
| 11 | `dbo_uae_1d`          | dbo        | UAE    | 1D | yfinance+cache  | 2026-05-21 (Fire 1)   | 2026-05-21 | PORTFOLIO_FAIL (104 trades < 1000; exp 0.93 < 1.0; dSharpe -0.78) |
| 12 | `dbo_crypto_1d`       | dbo        | CRYPTO | 1D | yfinance        | 2026-05-21 (Fire 1)   | 2026-05-21 | PORTFOLIO_FAIL (exp 0.98 < 1.0; WR 23.6% < 40%; dSharpe -0.61; CI lo<0) |
| 13 | `roc_us_1d`           | roc        | US     | 1D | yfinance        | 2026-05-21 (Fire 1.5) | 2026-05-21 | **PORTFOLIO_FAIL on WR-floor only** — 34,612 trades, exp 1.217, WR 29.9% (< 40% floor), raw Sharpe 4.306, **dSharpe 3.724** (7.4× the 0.5 floor), 99.7% coverage. Second momentum-family near-miss (after DBO US). |
| 14 | `roc_uae_1d`          | roc        | UAE    | 1D | yfinance+cache  | 2026-05-21 (Fire 1.5) | 2026-05-21 | PORTFOLIO_FAIL (178 trades < 1000; exp 0.58 < 1.0; WR 24.2% < 40%; dSharpe -3.01) |
| 15 | `roc_crypto_1d`       | roc        | CRYPTO | 1D | yfinance        | 2026-05-21 (Fire 1.5) | 2026-05-21 | PORTFOLIO_FAIL (exp 0.84 < 1.0; WR 20.3% < 40%; dSharpe -1.64; CI lo<0) |
| 16 | `vcb_us_1d`           | vcb        | US     | 1D | yfinance        | 2026-05-21 (Fire 2)   | 2026-05-21 | **PORTFOLIO_FAIL on WR-floor only** — 18,221 trades, exp 1.187, WR 23.4% (< 40% floor), **dSharpe 1.924** (3.8× the 0.5 floor), 99.2% coverage. Third near-miss; trend-family WR-pattern consistent (DBO 34.1%, ROC 29.9%, VCB 23.4%). Research-grade only — honest FAIL per audit Concern 2. |
| 17 | `vcb_uae_1d`          | vcb        | UAE    | 1D | yfinance+cache  | 2026-05-21 (Fire 2)   | 2026-05-21 | PORTFOLIO_FAIL (84 trades < 1000; exp 0.56 < 1.0; WR 20.2% < 40%; dSharpe -2.57; CI lo<0) |
| 18 | `vcb_crypto_1d`       | vcb        | CRYPTO | 1D | yfinance        | 2026-05-21 (Fire 2)   | 2026-05-21 | PORTFOLIO_FAIL (1,290 trades; WR 15.8% < 40%; dSharpe -0.07; raw 0.53; CI lo<0). exp 9.54 high but driven by long-tail outliers — WR floor binding. |
| 19 | `hat_uae_1d`          | hat        | UAE    | 1D | yfinance+cache  | 2026-05-21 (Fire 14:55 UTC) | pending (staged) | pending |
| 20 | `hat_crypto_1d`       | hat        | CRYPTO | 1D | yfinance        | 2026-05-21 (Fire 14:55 UTC) | pending (staged) | pending |
| 21 | `hat_us_1d`           | hat        | US     | 1D | yfinance        | 2026-05-21 (Fire 14:55 UTC) | pending (staged) | pending |

**`config.PORTFOLIO_GATE.n_trials_registered` must equal the row count above.**
Current value: **21** (bumped 18 → 21 when HAT registered Fire 14:55 UTC 2026-05-21,
in the same commit that added the trial budget rows above).

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

---

## PAPER-FORWARD WATCH-LIST PROTOCOL (pre-registered)

Added 2026-05-21 in response to **Session 5 audit finding NEW-1 (BLOCKING)**:
the original deployed watch list (DY, EXPGY, PSX, ARW, ROL) was top-5 by
per-ticker OOS expectancy — exactly the cherry-picking failure mode the
portfolio gate exists to prevent.

**Frozen protocol for US Divergence Daily paper-forward:**

1. **Source population:** the set of contributing tickers from the
   `PORTFOLIO_CLEARED_FOR_PAPER_FORWARD` run that certified the strategy
   (`validation_divergence_1d_full_haircut6.json`, config_hash
   `6ce4b38242d54771`, 1,030 US tickers with `oos_n > 0`).
2. **Selection method:** `random.sample(population, k=50)` with **seed=42**,
   drawn once at deployment.
3. **Frozen artefact:** `universe/divergence_us_paperforward_watchlist.txt`
   committed at deployment. The file IS the watch list — the detector
   reads from it. Modification requires bumping `config_hash` and a new
   pre-registration entry in this section.
4. **Audit tag:** the detector writes
   `watch_list_method = "random_sample_seed42_n50_from_cleared_universe_2026-05-21"`
   into `paper_forward_positions.json` on every run.
5. **Rationale (size and method):** N=50 chosen before drawing the sample,
   for operational concentration (attention budget, Telegram noise control);
   randomness chosen as the non-expectancy criterion the auditor named.
   This is option (b) in the audit text ("randomly selected representative
   sample"). Option (a) ("entire cleared universe with Kelly-fraction sizing")
   was rejected on operational grounds: 1,030-ticker yfinance fetch every
   2 hours under the sprint routine would saturate the rate budget without
   adding information value at the paper-forward stage where sizing is unit.

**Future strategy paper-forward deployments must follow the same template:**
draw from the cleared-universe set; pre-register seed and N before sampling;
freeze to a file; tag the state with the method. No expectancy-based
selection is admissible.

- Audit NEW-1: **RESOLVED** by the protocol above + the committed watch
  list file. The detector now scans 50 random names rather than the
  top-5 by expectancy. The deployment has zero closed paper trades, so
  resolving this before any trade fires keeps the audit trail clean.
