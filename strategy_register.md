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

## PHASE 1 EXIT CRITERIA — 75% FULL-HALAL COVERAGE (directive 2026-05-21 evening)

Canonical 10-objective tracker lives in `ceo_brain.md` (single source of truth).
The two rules below are load-bearing for every trial registered in this file:

1. **Coverage target = ≥75% of FULL halal universe per market.** US 1,621
   tickers → ~1,216 must pass under at least one strategy. UAE ~80 → ~60.
   Crypto ~140 → ~105. Coverage = union across cleared strategies, no
   double-counting.
2. **Sweep rule = every trial MUST sweep the FULL halal universe of its
   market.** Staged batches (200 tickers/fire) are acceptable for execution,
   but the trial verdict is only final after the FULL universe has been
   tested. Partial sweeps are flagged in `sweep_coverage_audit.md` and
   require re-validation (PART B Step 2) before contributing to Phase 1
   coverage tallies.

Per audit Concern 2: thresholds, gate parameters, and the WR floor are
frozen ahead of data and must NOT be amended post-hoc to rescue a failing
strategy. Same-strategy iteration on a failing dataset is forbidden.

---

## PHASE 1 FRAMEWORK DIRECTIVE (2026-05-22) — Six Amendments

Per `ahmed_response_2026-05-22.md`. Pre-registered atomically with the
commit that introduces them; the new `config_hash` binds these amendments
to all future runs. **Framework finality:** these amendments are FROZEN
for 6 months from the commit date (~2026-11-22). All amendments apply
PROSPECTIVELY only — existing Session 5 verdicts under the OLD hash are
NOT retroactively re-evaluated (per directive Part 3). Re-evaluation
requires Method A (fresh OOS window) or Method B (forward data ≥ 6 mo).

### Amendment 1 — Archetype-based WR floor (CONDITIONAL, DORMANT)

> **SUPERSEDED — PERMANENTLY DORMANT DEAD LETTER (decision_log entry 47,
> 2026-06-12).** The activating condition ("auto-execution infrastructure
> exists") is permanently void under the supervised operating model
> (entries 39-40): no such layer exists or is authorized. This provision
> can never activate and its config knobs were removed (entry 47); the
> gate code only ever read the strict `min_win_rate = 0.40`, which bound
> every trial 1-40 including TSM-12. The SUBSTANTIVE archetype-WR
> question (incl. the dSharpe ≥ 1.5 / PF ≥ 2.0 / CI > 0 thresholds
> below) is MERGED into the entry-46 parked discussion item — merits-
> based, deliberate amendment process, decoupled from autonomy,
> forward-only. Source directive recovered verbatim to
> `ahmed_response_2026-05-22.md` (provenance: entry 47). Text below is
> preserved unmodified as historical record.

- `mean_reversion` / `pullback`: WR floor = **0.40 unchanged**.
- `trend_following` / `breakout` / `momentum`: WR floor REMOVED iff
  dSharpe ≥ 1.5 AND profit factor ≥ 2.0 AND bootstrap CI lower bound on
  mean trade return > 0 AND **auto-execution layer exists**.
- `volatility_cycle` / `statistical_arb` / `event_driven`: WR floor = 0.40
  (not explicitly named in Amendment 1 — default strict).
- **Auto-execution layer:** Phase 2 infrastructure build. Does NOT exist
  today. Until `AUTO_EXECUTION_LAYER_EXISTS=True` AND its own validation
  passes, Amendment 1 is DORMANT and all strategies use the strict floor.
- Every strategy gets an `archetype` field at registration. Frozen.

### Amendment 2 — Trade-count floor by universe size

- US: min OOS trades = 1,000 (unchanged)
- UAE: min OOS trades = 200
- Crypto: min OOS trades = 400
- GCC: pre-register at onboarding (Phase 2)

The formula `max(100, sqrt(universe × years × signal_freq))` is **rejected**
— `signal_freq` is a free parameter and creates a tuning backdoor.

Tightening that REMAINS strict regardless of universe:
- Bootstrap CI lower bound on mean trade return strictly > 0
- dSharpe ≥ 0.5 after N-trial multi-test haircut
- **OOS Sharpe ≥ 0.7 × IS Sharpe** (overfitting robustness; new)
- OOS time span ≥ 24 months (see Amendment 6)

### Amendment 3 — Profit factor floor

- OOS PF ≥ 1.5
- Bootstrap CI lower bound on PF ≥ 1.0 (even at the pessimistic end of
  the bootstrap distribution, must be break-even)
- Only evaluated when n ≥ 30 trades

### Amendment 4 — Multi-timeframe testing as separate pre-registered trials

Each (strategy × market × timeframe) is a separate trial in the TRIAL
BUDGET. Adding a TF tightens the multi-test haircut. **Process amendment
— no config knob.** Discipline lives in the TRIAL_BUDGET table below.

### Amendment 5 — GCC universe as discovery-and-validation tool (PHASE 2)

- Trading scope = **UAE only**. GCC is NOT a deployment market.
- GCC (Saudi + Kuwait + Qatar + Bahrain) halal aggregate ~400-500 tickers
  serves as a discovery-and-validation source where UAE alone lacks power.
- Any strategy clearing the GCC-wide gate must ALSO pass a separate
  UAE-only certification (hard gate, same status as Shariah).
- Strategies clearing GCC but failing UAE-only are tagged
  `GCC_only_edge_not_UAE_deployable` and shelved.
- Phase 2 infrastructure build — does NOT exist today, does NOT consume
  Phase 1 slots.

### Amendment 6 — OOS calendar time-span floor

- OOS trades must span ≥ 24 calendar months
- Verdict `INSUFFICIENT_OOS_SPAN` when trade count sufficient but calendar
  span insufficient

---

## PHASE 1 THREE-FILTER SELECTION METHODOLOGY (frozen 2026-05-22)

Per directive Part 4. Replaces the Version-B autonomous strategy-enrollment
loop. CEO runs this methodology automatically; CEO does NOT improvise or
deviate without Ahmed approval logged in `decision_log`.

### Phase 1 strategy cap: 4 candidates total

| Slot | Status | Strategy | Notes |
|------|--------|----------|-------|
| 1 | FILLED | Divergence Daily | Grandfathered from Session 5 framework selection |
| 2 | FILLED | TRB-50 (breakout) | Three-filter output, trial 41 CLEARED 2026-06-12 (entry 49); trend_following tested-and-failed first (TSM-12, trial 40, entry 46) |
| 3 | OPEN | — | Pending methodology output |
| 4 | OPEN | — | Pending methodology output |

After 4 candidates complete (cleared OR failed) under the amended gate,
**Phase 1 testing CLOSES** until Phase 2 review post-6-month freeze.

### Filter 1 — Archetype diversity from cleared strategies

Currently cleared (Phase 1): Divergence (pullback). Next candidate MUST
be from a different archetype. Priority order:

1. `trend_following`
2. `breakout`
3. `momentum`
4. `volatility_cycle`
5. `statistical_arb`

Testing a second `pullback` strategy is disallowed until at least one
strategy from another archetype has cleared OR failed honestly.

### Filter 2 — Evidence tier

- **T1** (highest priority): peer-reviewed academic, multiple markets and
  decades. Trend-following (Moskowitz/Ooi/Pedersen 2012), momentum
  (Jegadeesh & Titman 1993), value-tilted breakout.
- **T2**: practitioner consensus / multiple independent published backtests
  with consistent direction.
- **T3**: single-source claim, blog backtest, single Pine script.

Test T1 BEFORE T2 BEFORE T3. T3 only when T1+T2 queues exhausted for the
relevant archetype.

### Filter 3 — Data and infrastructure readiness

Disqualify (move to deferred queue, not test queue):
- Requires intraday tick data (only daily/1H available)
- Requires short-selling (long-only mandate — Rule 15)
- Requires options/futures/fundamentals not yet wired
- Requires leverage (Rule 16)
- Violates Shariah on instrument level

### Source priority for candidate strategies

1. **López de Prado / Advances in Financial Machine Learning** — explicit
   archetype taxonomy with peer-reviewed evidence + overfitting warnings.
2. **Replication of published results BEFORE building variants** —
   reproduce the original on its original universe first. If you can't
   reproduce, the original was overfit.
3. **Ahmed's Tareq research as a CONSTRAINED source** — prior backtests
   and signal logs are NOT evidence of edge (pre-pre-registration
   discipline). Tareq rules get frozen, then tested through the amended
   gate on data not previously evaluated.

### Explicitly forbidden

- Scanning Pine forum top-returns lists
- Parameter optimization across the universe
- Iterating on failed strategies
- CEO scanning past results to spot patterns and seed new candidates
- Treating Ahmed intuitions as inputs (except via Ahmed-input exception)

### Ahmed-input exception

Ahmed may explicitly request a specific strategy enter the queue. It
receives the standard tier classification and tests in order. It does
NOT jump the queue. Same gate applies.

### Data reuse policy

- Previously collected **DATA** (universe lists, OHLCV caches) = reusable.
- Previously collected **RESULTS / VERDICTS** = NOT reusable as edge
  evidence (pre-pre-registration discipline).

### Autonomous-execution scope

CEO can WITHOUT asking Ahmed:
- Run the three filters against current state and produce next-candidate.
- Pre-register the candidate's full spec BEFORE testing.
- Run the test through the amended gate.
- Log results.
- Move to the next candidate until cap is reached.

CEO MUST ASK AHMED for:
- Modifying any filter in the methodology
- Skipping queue order
- Adding archetypes not in the original list
- Adding a strategy that triggers the deferred queue
- Exceeding the Phase 1 cap of 4 candidates

---

## PRE-FRAMEWORK STRATEGIES (sprint-loop-tested, 2026-05-21 → 2026-05-22)

The 13 strategies registered before the Phase 1 framework directive
(Divergence + EMA-200 + MBV + DBO + ROC + VCB + HAT + PMR + STR + ART +
CMF + GAP + WCK) were enrolled under the autonomous sprint loop's
Version-B methodology that the directive Part 4 forbids. Their verdicts
stand as honest historical record. They are **NOT Phase 1 candidates**
EXCEPT Divergence (grandfathered to Phase 1 slot 1 by Session 5 framework
discipline, pre-autonomous-loop).

If the three-filter methodology selects a Pre-Framework strategy (e.g.,
MBV via the trend_following / pullback filter), the strategy enters
Phase 1 by virtue of selection — but its existing test data is reusable
only as INITIAL evidence; it MUST re-validate under the amended gate on
data not previously evaluated under those amendments (Method A: fresh
OOS window; Method B: post-2026-05-22 forward data).

Pre-Framework strategies retain their `archetype` tag. `n_trials_registered`
remains **39** (cannot selectively reduce N without invalidating the
multi-test haircut discipline).

| # | Strategy | Archetype | Pre-Framework | Phase 1 status |
|---|----------|-----------|---------------|----------------|
| 1 | ema200 | trend_following | YES | Pre-Framework FAIL |
| 2 | divergence | pullback | NO (grandfathered) | **Phase 1 slot 1 CLEARED** |
| 3 | mbv | pullback | YES | Pre-Framework CLEARED (US); Phase 1 only if methodology selects + re-validates |
| 4 | dbo | breakout | YES | Pre-Framework near-miss (WR floor only) |
| 5 | roc | momentum | YES | Pre-Framework near-miss (WR floor only) |
| 6 | vcb | volatility_cycle | YES | Pre-Framework near-miss (WR floor only) |
| 7 | hat | trend_following | YES | Pre-Framework near-miss (WR floor only) |
| 8 | pmr | mean_reversion | YES | Pre-Framework CLEARED (US); Phase 1 only if methodology selects + re-validates |
| 9 | str | mean_reversion | YES | Pre-Framework CLEARED (US); Phase 1 only if methodology selects + re-validates |
| 10 | art | trend_following | YES | Pre-Framework near-miss (WR floor only) |
| 11 | cmf | mean_reversion | YES | Pre-Framework near-miss (WR floor only) |
| 12 | gap | event_driven | YES | Pre-Framework FAIL (small markets); US drain finalized |
| 13 | wck | mean_reversion | YES | Pre-Framework drain in progress (50%); finalize as historical |

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

## STRATEGY 9 — STR: Stochastic %K Reversal in Trend (long only) — NEW 2026-05-22 Sprint Catch-up

| Field | Value |
|-------|-------|
| Strategy id | `str` |
| Module | `aig/strategy_str.py` |
| Timeframes registered | **1D** |
| Long only | YES (Rule 15) |
| Pre-registered | 2026-05-22 Sprint Catch-up (BEFORE seeing any STR data — Phase 1 directive F1) |

**Concept**: long-only **stochastic mean-reversion** triggered by the **cross-up
event** of Stochastic %K through an oversold floor in a bullish regime, with
volume confirmation. Quick midpoint exit (%K>=50). Methodologically distinct
from the eight prior strategies:

- **EMA-200** (trend-confirm): position-based — close > long EMA.
- **Divergence** (mean-rev-on-low): RSI higher-low against price lower-low swing-pivot structure.
- **MBV** (mean-rev-in-uptrend): range_pct lower-third **level** condition.
- **DBO** (breakout): close crosses Donchian high (level).
- **ROC** (velocity-momentum): rate of price change (derivative).
- **VCB** (vol-cycle): ATR-minimum compression (volatility input).
- **HAT** (smoothed-trend): N consecutive bullish Heikin-Ashi candles.
- **PMR** (statistical-zscore-mean-rev): continuous z = (close - SMA_N) / std_N.
- **STR** (stochastic-cross-up-mean-rev): %K = 100 × (close − LL_N) / (HH_N − LL_N).
  EVENT-driven (cross-up from oversold), NOT continuous level — fires only on
  the bar %K transitions from <=20 to >20. Quick midpoint exit captures
  small bounces; **higher WR by construction** than PMR/Divergence full-mean-rev
  exits because the target is closer to entry than the SMA mean is in noisy
  markets.

**Hypothesis**: noisy UAE / Crypto markets where prior mean-rev strategies
fail on the 40% WR floor may show edge under faster-target mean-rev that
exits at range midpoint (%K=50) rather than statistical mean (PMR z=0 / RSI=65).
The small fixed target is more reliably hit in choppy markets where the
SMA mean keeps drifting away. Frozen BEFORE seeing data per audit Concern 2 —
failure is acceptable.

**Entry** (all must hold on the entry bar):
1. `%K(STR_PERIOD=14)` > `STR_OS_LEVEL=20.0` today AND `%K(14).shift(1)` <= 20.0
   — the **cross-up event** from oversold zone.
2. `close > SMA(STR_TREND_SMA=200)` — bullish regime; no longs in confirmed
   downtrends.
3. `volume >= STR_VOLUME_MULT=1.2 × SMA(STR_VOLUME_PERIOD=20)` — participation
   confirms the recovery.

The cross condition is inherently edge-triggered (exactly one bar fires per
recovery from oversold).

**Stop**: entry − `STR_STOP_ATR_MULT=1.5` × ATR(14). Tight stop because the
thesis is small-bounce; deeper drawdowns invalidate it.

**Exit**:
- `%K(14) >= STR_EXIT_LEVEL=50.0` (midpoint reached — small bounce captured)
- `close < SMA(STR_TREND_SMA)` (regime broke)
- ATR stop hit.

---

## STRATEGY 8 — PMR: Price-Mean Z-score Reversion (long only) — NEW 2026-05-21 Fire 15:05 UTC

| Field | Value |
|-------|-------|
| Strategy id | `pmr` |
| Module | `aig/strategy_pmr.py` |
| Timeframes registered | **1D** |
| Long only | YES (Rule 15) |
| Pre-registered | 2026-05-21 Fire 15:05 UTC (BEFORE seeing any PMR data — Phase 1 directive F1) |

**Concept**: long-only **statistical mean-reversion** driven by the
**z-score** of close vs its rolling mean/std. Methodologically distinct
from the seven prior strategies:

- **EMA-200** (trend-confirm): close > long EMA.
- **Divergence** (mean-rev-on-low): RSI hookup on swing-low structure.
- **MBV** (mean-rev-in-uptrend): range_pct in lower third of trailing high/low — RAW range, not statistical.
- **DBO** (breakout): close crosses Donchian high.
- **ROC** (velocity-momentum): rate of price change.
- **VCB** (vol-cycle): ATR-minimum compression.
- **HAT** (smoothed-trend): N consecutive bullish Heikin-Ashi candles.
- **PMR** (statistical-zscore-mean-rev): `z = (close - SMA_N) / std_N`.
  Unlike MBV (range_pct is BOUNDED [0,1] from raw high/low), PMR uses
  STANDARDIZED deviation that auto-adapts to per-ticker volatility. Two
  stocks with identical range_pct but different historical std will have
  very different z-scores; PMR sees the statistical extremity raw-range
  strategies treat as identical.

**Hypothesis**: noisy markets (UAE / Crypto) where raw range or RSI-based
mean-rev rules fail on the WR floor may show edge under z-score-normalized
entry signals, because z-score self-adapts to per-ticker volatility and
flags genuine statistical outliers rather than relative-range outliers.
Frozen BEFORE seeing data per audit Concern 2 — failure is acceptable.

**Entry** (all four must hold on the entry bar, edge-triggered):
1. `z(PMR_PERIOD=20) <= -PMR_Z_FLOOR=1.5` (close is ≥1.5 stddev BELOW
   its 20-day mean — statistical extreme low).
2. `z(20) > z(20).shift(1)` (z is RISING — recovery has begun, do not
   try to catch a falling knife mid-decline).
3. `close > SMA(PMR_TREND_SMA=200)` (bullish regime; no longs in
   confirmed downtrends).
4. `volume >= PMR_VOLUME_MULT=1.2 * SMA(PMR_VOLUME_PERIOD=20)`
   (institutional participation confirms the reversion).

Rolling mean/std use `.shift(1)` so today's close never contaminates
the mean/std it is tested against — look-ahead-free.

**Stop**: entry − `PMR_STOP_ATR_MULT=1.5` × ATR(14).

**Exit**: `z(20) >= PMR_Z_EXIT=0.0` (mean reversion completed) OR
`close < SMA(PMR_TREND_SMA)` (regime broke) OR ATR stop hit.

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

## STRATEGY 10 — ART: Aroon Time-Trend Strength (long only) — NEW 2026-05-22 Sprint

| Field | Value |
|-------|-------|
| Strategy id | `art` |
| Module | `aig/strategy_art.py` |
| Timeframes registered | **1D** |
| Long only | YES (Rule 15) |
| Pre-registered | 2026-05-22 Sprint (BEFORE seeing any ART data — Phase 1 directive F1) |

**Concept**: long-only **TIME-DOMAIN trend-strength** strategy. Aroon
measures BAR-COUNT-SINCE-EXTREME — how recently price made its 14-period
high vs its 14-period low. Methodologically distinct from the nine prior
strategies — every prior strategy is magnitude-domain (levels, derivatives,
oscillator values, range positions, std deviations); ART is time-domain.

- **EMA-200 / MBV / PMR / Divergence / STR**: magnitude (level / std / range / RSI).
- **DBO**: level crossing (magnitude).
- **ROC**: derivative of price (magnitude).
- **VCB**: ATR-min (magnitude of volatility).
- **HAT**: smoothed bar (magnitude of HA-close vs HA-open).
- **ART**: bar-count-since-extreme (TIME). Two stocks with identical price
  series over 14 bars but different EXACT-DAY structure of when the
  highs/lows landed will have very different Aroon values. ART captures
  a regime property no other indicator family measures.

**Hypothesis**: noisy markets (UAE / Crypto) where price-magnitude signals
fail on the 40% WR floor may show edge under time-since-extreme dominance.
Magnitude signals fire on chop and reverse; time-since-extreme dominance
only flips when a structural new-high cluster appears, which is more
selective and may yield higher WR. Frozen BEFORE seeing data per audit
Concern 2 — failure acceptable.

**Aroon definitions** (Tushar Chande, 1995):
- `AroonUp(N)   = 100 * (N - bars_since_N_high) / N`
- `AroonDown(N) = 100 * (N - bars_since_N_low)  / N`
- `AroonOsc(N)  = AroonUp(N) - AroonDown(N)` (range -100 to +100)

**Entry** (all must hold on the entry bar, cross-up edge-triggered):
1. `AroonOsc(ART_AROON_PERIOD=14) > +ART_AROON_OSC_THRESHOLD=50.0` today
   AND `AroonOsc.shift(1) <= 50.0` — cross-up event from <=50 to >50.
2. `close > SMA(ART_TREND_SMA=50)` — bullish regime.
3. `volume >= ART_VOLUME_MULT=1.2 × SMA(ART_VOLUME_PERIOD=20)`.

Cross-up is naturally edge-triggered (yesterday's Osc was <=50; today's > 50;
exactly one bar fires).

**Stop**: entry − `ART_STOP_ATR_MULT=2.0` × ATR(14). Wider than mean-rev
strategies because the thesis is trend-continuation.

**Exit**: `AroonOsc(14) <= 0` (time-domain dominance flipped) OR
`close < SMA(50)` (regime broke) OR ATR stop hit.

---

## STRATEGY 11 — CMF: Chaikin Money Flow Mean-Reversion in Bullish Regime (long only) — NEW 2026-05-22 Sprint Obj-6 advance

| Field | Value |
|-------|-------|
| Strategy id | `cmf` |
| Module | `aig/strategy_cmf.py` |
| Timeframes registered | **1D** |
| Long only | YES (Rule 15) |
| Pre-registered | 2026-05-22 Sprint Obj-6 advance (BEFORE any CMF data was seen — Phase 1 directive F1) |

**Concept**: long-only **VOLUME-FLOW-DOMAIN mean-reversion** strategy.
Chaikin Money Flow integrates the per-bar money-flow multiplier
`((C-L)-(H-C))/(H-L)` (close-position-within-range in [-1, +1]) weighted
by volume, summed over N bars:

  `CMF(N) = sum( ((C-L)-(H-C))/(H-L) * volume ) / sum( volume )` over N bars.

Methodologically distinct from the ten prior strategies — every prior
strategy uses VOLUME only as a CONFIRMATION (>= 1.2 × SMA(20)) layered on
top of a price-derived primary signal. CMF is the first strategy whose
PRIMARY signal IS the integrated volume-weighted money flow. The per-bar
"where did the close land within today's range, weighted by today's
volume" primitive is a different domain altogether — an intra-bar
buying-pressure surrogate, not a between-bar price/momentum/structure
signal.

- **EMA-200 / MBV / PMR / Divergence / STR / DBO / ROC / VCB / HAT / ART**:
  primary signal = price level / RSI / range_pct / z-score / %K cross /
  Donchian high / ROC / ATR-min / HA candle / Aroon. Volume only confirms.
- **CMF**: primary signal IS volume-weighted money-flow integration.

**Hypothesis**: short-term distribution (CMF < -0.05) inside an intact
long-term bullish regime (close > EMA-200) is an oversold-in-trend
setup — the macro trend is up but near-term close-within-range weighting
is bearish, often weak hands selling into strong hands. Mean-reversion to
neutral/positive money flow likely. Quick exit at CMF > +0.10 (accumulation
flip) captures the small reversion; higher-probability target than full
trend retracement. Frozen BEFORE seeing data per audit Concern 2 — failure
acceptable.

**Entry** (all must hold on the entry bar):
1. `CMF(CMF_PERIOD=20) < CMF_OS_LEVEL=-0.05` — distribution dominates
   near-term money flow.
2. `close > EMA(CMF_TREND_EMA=200)` — long-term bullish regime intact.
3. `close > close.shift(CMF_TURNAROUND_BARS=1)` — today's close above
   yesterday's (one-bar turnaround; prevents catching a free-fall).
4. `volume >= CMF_VOLUME_MIN_MULT=1.0 × SMA(CMF_VOLUME_PERIOD=20)` —
   at-or-above average volume sanity check (no signal on near-zero-volume
   distribution).

**Stop**: entry − `CMF_STOP_ATR_MULT=1.5 × ATR(14)`. Tight stop because the
mean-reversion thesis breaks fast if price falls further.

**Exit**:
- `CMF(CMF_PERIOD) > CMF_EXIT_LEVEL=+0.10` (accumulation flipped dominant
  — reversion thesis played out).
- `close < EMA(CMF_TREND_EMA)` (long-term regime broke).
- ATR stop hit.

---

## STRATEGY 12 — GAP: Overnight Gap Continuation in Uptrend (long only) — NEW 2026-05-22 Sprint Obj-6 advance 11:48 UTC

| Field | Value |
|-------|-------|
| Strategy id | `gap` |
| Module | `aig/strategy_gap.py` |
| Timeframes registered | **1D** |
| Long only | YES (Rule 15) |
| Pre-registered | 2026-05-22 Sprint Obj-6 advance 11:48 UTC (BEFORE any GAP data was seen — Phase 1 directive F1) |

**Concept**: long-only **BETWEEN-BAR DISCONTINUITY** strategy. GAP reads the
overnight gap event — today's open versus yesterday's close — a price
discontinuity that exists only at the open print and is NOT captured by any
rolling-window aggregator. Every prior strategy in the pipeline reads
WITHIN-BAR or ROLLING-WINDOW primitives:

- EMA-200 / Divergence / MBV / PMR / STR: rolling levels, RSI, range_pct,
  z-score, %K — all within-bar or rolling-window.
- DBO / VCB: Donchian rolling-window high, ATR-min rolling-window compression.
- ROC / HAT / ART: rate-of-change / smoothed bar / time-since-extreme — all
  rolling-window or recursive.
- CMF: integrated money-flow over N bars — rolling-window.
- **GAP**: between-bar **discontinuity event** at the open print. No prior
  strategy reads this primitive.

**Hypothesis** (frozen pre-data): An overnight gap up of ≥2% in an established
uptrend (close > SMA(50)) that does NOT fade intraday (close > open) and is
confirmed by elevated volume (≥1.5× average) represents an institutional
commitment. Price tends to continue in the gap direction for several bars
before mean-reverting. Failure modes acceptable per audit Concern 2: (a) on
continuous-quote markets (crypto via yfinance 1D bars), gaps are rare —
trade count may fail the 1000 floor — honest FAIL; (b) on noisy small markets
(UAE), gap quality may be too low to clear WR floor — also honest FAIL.

**Entry** (all must hold on the entry bar):
1. `open >= prior_close × (1 + GAP_THRESHOLD=0.02)` — overnight gap up of
   2%+ exists at today's open.
2. `close > open` — the gap held intraday (did NOT fade to a fill).
3. `close > SMA(GAP_TREND_SMA=50)` — bullish regime filter.
4. `volume >= GAP_VOLUME_MULT=1.5 × SMA(GAP_VOLUME_PERIOD=20)` — elevated
   volume confirms institutional commitment.

**Stop**: entry − `GAP_STOP_ATR_MULT=1.5 × ATR(14)`. Tight stop because the
mean-reversion (gap-fade) thesis breaks fast if price retraces.

**Exit**:
- `close < SMA(GAP_EXIT_SMA=10)` — short-term momentum lost.
- ATR stop hit.

---

## STRATEGY 13 — WCK: Lower-Wick Rejection Mean-Reversion (long only) — NEW 2026-05-22 Sprint Obj-6 advance post-GAP

| Field | Value |
|-------|-------|
| Strategy id | `wck` |
| Module | `aig/strategy_wck.py` |
| Timeframes registered | **1D** |
| Long only | YES (Rule 15) |
| Pre-registered | 2026-05-22 Sprint Obj-6 advance post-GAP-finalize (BEFORE any WCK data was seen — Phase 1 directive F1) |

**Concept**: long-only **INTRA-BAR SHAPE-DOMAIN mean-reversion**. WCK is
the FIRST strategy whose primary signal is the SHAPE RATIO of a SINGLE
candle — specifically the lower-wick-to-range ratio. Every prior
strategy reads one of: between-bar (GAP), rolling-window (EMA200/MBV/
DBO/ROC/VCB/PMR/STR/ART), recursive smoothed (HAT), volume-integrated
(CMF), or swing-pivot (Divergence) primitives. The intra-bar single-bar
wick anatomy is unused in any of them.

- **EMA-200 / MBV / PMR / Divergence / STR / DBO / ROC / VCB / HAT /
  ART / CMF / GAP**: rolling-window or between-bar primitives — none
  read the single-bar wick-to-range ratio.
- **WCK**: `lower_wick = min(open, close) - low`; `bar_range = high - low`;
  `lower_wick / bar_range >= 0.5` AND `body / bar_range <= 0.35` —
  the canonical hammer / long-lower-wick pattern. Distinct from CMF
  which uses the close-position-in-range multiplier `((C-L)-(H-C))/(H-L)`
  but immediately integrates it over N bars with volume weighting.
  WCK reads the unaggregated single-bar shape primitive.

**Hypothesis** (frozen pre-data): in a bullish regime (close > SMA(200)),
a single bar with lower wick ≥50% of range AND body ≤35% of range is
intra-bar evidence of buyers rejecting a tested lower price. Volume
confirmation (≥1.2× SMA-20) filters thin-trade fake wicks. Quick exit
when close exceeds prior 5-bar high (small bounce captured) targets a
higher-WR small-target trade than statistical-mean exits (PMR z=0) or
oscillator midpoints (STR %K=50). Failure acceptable per audit Concern 2.

**Entry** (all must hold on the entry bar):
1. `(min(open, close) - low) / (high - low) >= WCK_WICK_RATIO_FLOOR=0.5`
2. `abs(close - open) / (high - low) <= WCK_BODY_RATIO_CEIL=0.35`
3. `(high - low) >= WCK_MIN_RANGE_ATR_RATIO=0.5 × ATR(14)` — skip dojis/
   microscopic bars where wick ratios are unreliable.
4. `close > SMA(WCK_TREND_SMA=200)` — bullish regime filter.
5. `volume >= WCK_VOLUME_MULT=1.2 × SMA(WCK_VOLUME_PERIOD=20)` — volume
   confirms institutional commitment.

**Stop**: entry − `WCK_STOP_ATR_MULT=1.0 × ATR(14)`. Tight stop because
the intra-bar rejection thesis breaks fast if the wick's low is taken
out within a couple bars.

**Exit**:
- `close >= rolling_max(close.shift(1), WCK_EXIT_LOOKBACK=5)` — close
  exceeds prior 5-bar high (small bounce captured).
- `close < SMA(WCK_TREND_SMA)` — regime broke.
- ATR stop hit.

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
| 19 | `hat_uae_1d`          | hat        | UAE    | 1D | yfinance+cache  | 2026-05-21 (Fire 14:55 UTC) | 2026-05-21 | PORTFOLIO_FAIL (255 trades < 1000; exp 0.96 < 1.0; dSharpe -0.83) |
| 20 | `hat_crypto_1d`       | hat        | CRYPTO | 1D | yfinance        | 2026-05-21 (Fire 14:55 UTC) | pending (staged) | pending |
| 21 | `hat_us_1d`           | hat        | US     | 1D | yfinance        | 2026-05-21 (Fire 14:55 UTC) | pending (staged) | pending |
| 22 | `pmr_uae_1d`          | pmr        | UAE    | 1D | yfinance+cache  | 2026-05-21 (Fire 15:05 UTC) | pending (staged) | pending |
| 23 | `pmr_crypto_1d`       | pmr        | CRYPTO | 1D | yfinance        | 2026-05-21 (Fire 15:05 UTC) | pending (staged) | pending |
| 24 | `pmr_us_1d`           | pmr        | US     | 1D | yfinance        | 2026-05-21 (Fire 15:05 UTC) | 2026-05-22 | **PORTFOLIO_CLEARED_FOR_PAPER_FORWARD** — 4,759 trades, exp 1.268, WR 47.3%, **dSharpe 2.263**, 986/1,121 contributors (87.96% strategy coverage). Third US-cleared strategy alongside Divergence + MBV. Reassignment ran; union US contributors still 1,101 (PMR overlaps existing union). |
| 25 | `str_uae_1d`          | str        | UAE    | 1D | yfinance+cache  | 2026-05-22 (Sprint Catch-up) | 2026-05-22 | PORTFOLIO_FAIL (13 trades < 1000; exp 0.11 < 1.0; dSharpe -3.19) |
| 26 | `str_crypto_1d`       | str        | CRYPTO | 1D | yfinance        | 2026-05-22 (Sprint Catch-up) | 2026-05-22 | PORTFOLIO_FAIL (268 trades < 1000; exp 0.47 < 1.0; dSharpe -2.70) |
| 27 | `str_us_1d`           | str        | US     | 1D | yfinance        | 2026-05-22 (Sprint Catch-up) | 2026-05-22 | **PORTFOLIO_CLEARED_FOR_PAPER_FORWARD** — 9,358 trades, exp 1.103, **WR 55.55%** (highest of all cleared strategies — hypothesis CONFIRMED: quick midpoint exit yields higher WR than full-mean-reversal exits), **dSharpe 0.902**, raw Sharpe 1.544, 1,038/1,124 contributors (92.35% strategy coverage), CI [+0.000796, +0.002583]. Fourth US-cleared strategy alongside Divergence + MBV + PMR. Reassignment ran; union US contributors grew 1,101 → 1,107 (STR added 6 unique). |
| 28 | `art_uae_1d`          | art        | UAE    | 1D | yfinance+cache  | 2026-05-22 (Sprint Obj-6 advance) | 2026-05-22 | PORTFOLIO_FAIL (98 trades < 1000; exp 0.697 < 1.0; WR 27.6% < 40%; dSharpe -1.926; CI lo<0) |
| 29 | `art_crypto_1d`       | art        | CRYPTO | 1D | yfinance        | 2026-05-22 (Sprint Obj-6 advance) | 2026-05-22 | PORTFOLIO_FAIL (1,024 trades; WR 27.4% < 40%; dSharpe 0.314 < 0.5; exp 1.667 driven by long-tail outliers — WR floor binding) |
| 30 | `art_us_1d`           | art        | US     | 1D | yfinance        | 2026-05-22 (Sprint Obj-6 advance) | 2026-05-22 | **PORTFOLIO_FAIL on WR-floor only** — 11,733 trades, exp 1.209, WR 34.87% (< 40% floor), raw Sharpe 2.693, **dSharpe 2.041** (4.1× the 0.5 floor), 1,108/1,124 contributors (98.58% strategy coverage). Fourth near-miss in the trend/momentum family (DBO 34.1%, ROC 29.9%, VCB 23.4%, ART 34.87%). Time-domain (Aroon) didn't break the WR-floor pattern. Honest FAIL per audit Concern 2. Reassignment ran; union US contributors unchanged at 1,107. |
| 31 | `cmf_uae_1d`          | cmf        | UAE    | 1D | yfinance+cache  | 2026-05-22 (Sprint Obj-6 advance) | 2026-05-22 | PORTFOLIO_FAIL (93 trades < 1000; exp 0.764 < 1.0; dSharpe -1.54) |
| 32 | `cmf_crypto_1d`       | cmf        | CRYPTO | 1D | yfinance        | 2026-05-22 (Sprint Obj-6 advance) | 2026-05-22 | PORTFOLIO_FAIL (566 trades < 1000; exp 0.482 < 1.0; dSharpe -3.62) |
| 33 | `cmf_us_1d`           | cmf        | US     | 1D | yfinance        | 2026-05-22 (Sprint Obj-6 advance) | 2026-05-22 | **PORTFOLIO_FAIL on WR-floor only** — 17,646 trades, exp 1.396, WR 33.96% (< 40% floor), raw Sharpe 6.5332, **dSharpe 5.872** under N=33 haircut (11.7× the 0.5 floor — HIGHEST near-miss dSharpe to date), 1,108/1,123 contributors (98.66% coverage). Fifth WR-floor near-miss; first volume-flow-domain near-miss (prior 4 are trend/momentum). |
| 34 | `gap_uae_1d`          | gap        | UAE    | 1D | yfinance+cache  | 2026-05-22 (Sprint Obj-6 advance 11:48 UTC) | pending (staged) | pending |
| 35 | `gap_crypto_1d`       | gap        | CRYPTO | 1D | yfinance        | 2026-05-22 (Sprint Obj-6 advance 11:48 UTC) | pending (staged) | pending |
| 36 | `gap_us_1d`           | gap        | US     | 1D | yfinance        | 2026-05-22 (Sprint Obj-6 advance 11:48 UTC) | 2026-05-22 | **PORTFOLIO_FAIL on WR-floor only** — 7,421 trades, exp 1.1812, WR 38.09% (< 40% floor — TIGHTEST gap-to-clearance at 1.91pp), raw Sharpe 2.1313, **dSharpe 1.462** under N=36 haircut (clears 0.5 floor by 192%), 1,077/1,118 contributors (96.33% coverage), CI lower bound positive (+0.0030). Sixth WR-floor near-miss; first between-bar-discontinuity-domain near-miss. |
| 37 | `wck_uae_1d`          | wck        | UAE    | 1D | yfinance+cache  | 2026-05-22 (Sprint Obj-6 advance post-GAP) | pending (staged) | pending |
| 38 | `wck_crypto_1d`       | wck        | CRYPTO | 1D | yfinance        | 2026-05-22 (Sprint Obj-6 advance post-GAP) | pending (staged) | pending |
| 39 | `wck_us_1d`           | wck        | US     | 1D | yfinance        | 2026-05-22 (Sprint Obj-6 advance post-GAP) | pending (staged) | pending |
| 40 | `tsm12_us_1d`         | tsm12      | US     | 1D | yfinance        | 2026-06-12 (Track 2 Session A1, three-filter) | 2026-06-12 | **PORTFOLIO_FAIL** — 3,473 trades, exp 1.0537, WR 29.9% (< 40% floor), raw Sharpe 0.284, dSharpe -0.395 (< 0.5, n=40 haircut), CI lo -0.0085 (not > 0). Honest FAIL, decision_log entry 46. Slot 2 stayed open. |
| 41 | `trb50_us_1d`         | trb50      | US     | 1D | yfinance        | 2026-06-12 (Track 2 Session A2, three-filter) | 2026-06-12 | **PORTFOLIO_CLEARED_FOR_PAPER_FORWARD** — 25,760 trades, exp 1.1521, **WR 50.97%** (first breakout-archetype clear of the 0.40 floor), raw Sharpe 3.483, **dSharpe 2.8021** (n=41 haircut), CI [+0.0032, +0.0052], 1,115/1,122 contributors (99.38% coverage — highest of any trial). decision_log entry 49. **US slot 2 FILLED.** Deployment pending watch-list pre-registration. |

**`config.PORTFOLIO_GATE.n_trials_registered` must equal the row count above.**
Current value: **41** (bumped 40 → 41 when TRB-50 registered 2026-06-12
Track 2 Session A2, in the same commit that added trial row 41 and the
TRB-50 canonical spec below — second Phase 1 three-filter candidate,
second single-market trial. Previously bumped 39 → 40 for TSM-12,
Session A1; the 13 Pre-Framework strategies all ran ×3 markets).

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

### TSM-12 canonical spec (trial 40, frozen 2026-06-12, spec_hash `efe8ac7b47f10a0f`)

Approved by operator 2026-06-12 (Track 2 Session A1). Params live in
config.py (`TSM12_LOOKBACK_DAYS`); the hash binds spec + universe content
(Path 2d-A: params in config.py, hash in register only).

- **Name:** TSM-12 | **Trial id:** `tsm12_us_1d` | **Archetype:**
  `trend_following` | **Tier:** T1 (Moskowitz/Ooi/Pedersen 2012,
  time-series momentum family — per Filter 2 list above)
- **Signal:** per-ticker 12-month total return = 252-trading-day total
  return, computed monthly on the last trading day. LONG if positive,
  FLAT otherwise. Time-series momentum (each ticker vs its own past),
  NOT cross-sectional ranking.
- **Rebalance:** monthly, last trading day. Equal weight across all
  long-signal tickers. Long-only, no stop, no leverage, no shorting
  (negative signal = flat, never short).
- **Universe:** universe/us_halal_full.txt, 1,603 tickers, FROZEN at
  pre-registration. universe_sha256 =
  `6dfca4bd8ddafb0c33a42ced44452157c4108b7e60e768016db09f7aad775e4e`
  (SHA-256 over the 1,603 symbols joined by `\n`, comments excluded).
- **Data/engine:** yfinance daily bars (1D), same as trials 1–39. Costs:
  US market model per `config.MARKET_COSTS` — commission 1.0 bps, spread
  2.0 bps, slippage 3.0 bps (round-trip model, as all prior trials).
- **Filters:** F1 `trend_following` = priority 1, no cleared trend
  strategy ✓; F2 T1 evidence ✓; F3 daily data, long-only (Rule 15),
  no leverage (Rule 16), halal universe ✓.
- **spec_hash:** `efe8ac7b47f10a0f` — first 16 hex of SHA-256 over the
  UTF-8 param string (one line, literal pipes, no whitespace between
  fields):
  `trial_id=tsm12_us_1d|strategy=tsm12|archetype=trend_following|tier=T1|signal=ts_momentum_252d_total_return_monthly|long_if=ret_252d>0|else=flat|rebalance=monthly_last_trading_day|weighting=equal_weight_across_long_signals|side=long_only|stops=none|leverage=none|timeframe=1D|engine=yfinance|costs=US:commission_bps=1.0,spread_bps=2.0,slippage_bps=3.0|universe=us_halal_full.txt|universe_n=1603|universe_sha256=6dfca4bd8ddafb0c33a42ced44452157c4108b7e60e768016db09f7aad775e4e`
  NOTE: this derivation convention is defined HERE (the prior session's
  convention and its hash `10d76bc7e0ee5e28` were lost with that session
  and exist nowhere on disk; not comparable).

### TRB-50 canonical spec (trial 41, frozen 2026-06-12, spec_hash `a96ccdf5c0640e4f`)

Approved by operator 2026-06-12 (Track 2 Session A2 GO, post entry-47
adjudication). Params live in config.py (`TRB50_WINDOW_DAYS`, `TRB50_BAND`,
`TRB50_HOLD_DAYS`); the hash binds spec + universe content (Path 2d-A:
params in config.py, hash in register only — TSM-12 convention).

- **Name:** TRB-50 | **Trial id:** `trb50_us_1d` | **Archetype:**
  `breakout` | **Tier:** T1 (Brock, Lakonishok & LeBaron 1992, Journal of
  Finance — Trading Range Breakout; replications: Bessembinder & Chan
  1995, Hudson/Dempsey/Keasey 1996. Recorded pre-data:
  Sullivan/Timmermann/White 1999 data-snooping critique — the gate
  adjudicates; failure acceptable).
- **Signal:** resistance = max(close) over the prior 50 trading days,
  shifted 1 bar (look-ahead-free, trials 1-39 convention). ENTRY when
  close > (1 + 0.01) × resistance — the paper's 1% band variant.
- **Hold/exit:** fixed 10 trading days; exit at the close of the 10th
  trading day after entry (the paper's post-signal measurement window).
  No stop (infinite stop distance, TSM-12 convention). Long-only —
  no signal = flat, never short. No leverage. Re-entry only on a fresh
  breakout event after flat (edge-triggered).
- **Pre-data rule-set choices (operator-approved, none invented):**
  window=50 (BLL primary variant; most signals → statistical power
  toward the 1,000-trade floor), band=1% (published variant), hold=10
  days (the paper's measurement window). All fixed before any data.
- **Universe:** universe/us_halal_full.txt, 1,603 tickers, FROZEN at
  pre-registration. universe_sha256 =
  `6dfca4bd8ddafb0c33a42ced44452157c4108b7e60e768016db09f7aad775e4e`
  (verified live 2026-06-12 Session A2: 1,603 symbols, zero dupes,
  hash identical to the TSM-12-frozen value — no drift).
- **Data/engine:** yfinance daily bars (1D), same as trials 1–40. Costs:
  US market model per `config.MARKET_COSTS` — commission 1.0 bps, spread
  2.0 bps, slippage 3.0 bps.
- **Filters:** F1 `breakout` = priority 2; trend_following tested-and-
  failed honestly (TSM-12, entry 46) ✓; F2 T1 evidence ✓ (C2 52-week-high
  George & Hwang 2004 → deferred queue: cross-sectional form does not fit
  the per-ticker engine, adaptation = variant-before-replication; C3
  Donchian/Turtle → rejected: T2 + near-duplicate of failed Pre-Framework
  DBO); F3 daily data, long-only (Rule 15), no leverage (Rule 16), halal
  universe ✓.
- **spec_hash:** `a96ccdf5c0640e4f` — first 16 hex of SHA-256 over the
  UTF-8 param string (one line, literal pipes, no whitespace between
  fields; TSM-12 derivation convention):
  `trial_id=trb50_us_1d|strategy=trb50|archetype=breakout|tier=T1|signal=trading_range_breakout_BLL1992|resistance=max_close_prior_50d_shift1|band=0.01|entry=close>(1+band)*resistance|hold=fixed_10_trading_days|exit=close_of_10th_trading_day_after_entry|reentry=new_breakout_event_after_flat|side=long_only|stops=none|leverage=none|timeframe=1D|engine=yfinance|costs=US:commission_bps=1.0,spread_bps=2.0,slippage_bps=3.0|universe=us_halal_full.txt|universe_n=1603|universe_sha256=6dfca4bd8ddafb0c33a42ced44452157c4108b7e60e768016db09f7aad775e4e`

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

### TRB-50 paper-forward deployment (pre-registered, decision_log entry 50, 2026-06-13)

Operator-approved 2026-06-12 22:12Z with Amendments A/B/C. Frozen BEFORE
any TRB-50 forward signal fired:

1. **Source population:** the 1,115 contributing tickers (`oos_n > 0`) from
   the run that certified the strategy (`validation_trb50_us_1d.json`,
   config_hash `c7ff799942e2c8da`, spec_hash `a96ccdf5c0640e4f`, entry 49).
2. **Selection method:** Improvement 1 **Option A** — the ENTIRE
   cleared-contributor set, no subsetting (operator ruling 2026-06-12;
   precedent: 33d93ae full-universe convention). The 7 evaluated-but-
   zero-signal tickers (STRK, STRF, TEM, LOAR, WAY, TTAM, WFF) are
   excluded on a deterministic, NON-performance basis — they produced no
   OOS signals under the frozen spec. Improvement 2 (sector/liquidity
   constraints) recorded as N/A under Option A (no sampling step to
   constrain; operator-confirmed reading).
3. **Frozen artefact:** `universe/trb50_us_paperforward_watchlist.txt`
   (1,115 symbols) committed at deployment. The file IS the watch list.
   Modification requires a new pre-registration entry here.
4. **Audit tag:** detector writes `watch_list_method =
   "full_cleared_contributor_set_n1115_from_validation_trb50_us_1d_cfg_
   c7ff799942e2c8da_entry50_2026-06-13"` into
   `paper_forward_positions_trb50.json` on every run.
5. **Detector:** `scripts/paper_forward_trb50.py` — imports `signals`
   DIRECTLY from `aig/strategy_trb50.py` (Amendment A single source of
   truth; identity asserted by conformance test). Fixed 10-trading-day
   hold driven by the paper entry date (bar-count exit, idempotent,
   no-new-bar no-op); no stop; same-bar re-entry guard mirroring the
   engine. Telegram is DIGEST-ONLY (Amendment C): one summary block per
   fire; the Divergence per-signal contract is unchanged. Migrating
   Divergence to digest later is a pure operational change requiring
   only a logged note.
6. **Routing reconciliation (Amendment B):** `winners_assignment.json`
   rebuilt with sources = {divergence, trb50}; Pre-Framework mbv/pmr/str
   tagged out per the entry-32 grandfathering; their 5 open paper
   positions (CARR, CMI, ADI, MUR, GGDVY — all mbv, entries 2026-05-21)
   administratively closed in `paper_forward_positions_full.json`
   (history preserved, not Phase-1 evidence). That detector is DORMANT;
   live detectors are the two per-strategy scripts above.

- Audit NEW-1: **RESOLVED** by the protocol above + the committed watch
  list file. The detector now scans 50 random names rather than the
  top-5 by expectancy. The deployment has zero closed paper trades, so
  resolving this before any trade fires keeps the audit trail clean.
