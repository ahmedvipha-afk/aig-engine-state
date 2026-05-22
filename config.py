"""
AIG Layers 1-2 — FROZEN configuration (pre-registration).

Everything here is written and fixed BEFORE seeing test data. The provenance
module hashes this file; if it changes, the hash changes, and any result
produced under the old hash is no longer claimable. That is the pre-registration
guarantee from the reconciliation directive (Layer B, item 5).

Nothing in here is tuned per ticker. One parameter set per market, by design,
because per-ticker optimisation is overfitting.

CEO v7.0 amendment (2026-05-20): added timeframe support + volume confirmation
+ Divergence strategy params. Frozen BEFORE running any 1H or Divergence tests.
"""

# ---- EMA-200 strategy (frozen) -------------------------------------------
EMA_PERIOD = 200
CONFIRM_BARS = 2          # close must hold above/below EMA this many bars
ATR_PERIOD = 14
STOP_ATR_MULT = 2.0       # initial stop = entry - 2*ATR
LONG_ONLY = True          # Rule 15 — no shorts, ever

# Volume confirmation (frozen 2026-05-20, applied on entry bar)
VOLUME_PERIOD = 20        # SMA window for average volume
VOLUME_MULT = 1.2         # entry-bar volume must be >= VOLUME_MULT * SMA(VOLUME_PERIOD)

# ---- MBV strategy (frozen 2026-05-21, daily) ----------------------------
# Market Bias + Range + Volume. Long-only mean-reversion inside bullish trend.
# Pre-registered before any test data was seen, per v7.0 §19 (third strategy
# in the pipeline). Trial budget extended to 9 to cover MBV × {US, UAE, CRYPTO}.
MBV_TREND_EMA      = 200    # bullish bias filter
MBV_RANGE_BARS     = 20     # trailing range window (high/low)
MBV_RANGE_FLOOR    = 0.33   # entry: range_pct ≤ floor (lower third)
MBV_RANGE_MID      = 0.50   # exit: range_pct ≥ mid (mean reversion target)
MBV_VOLUME_PERIOD  = 20     # SMA window for volume
MBV_VOLUME_MULT    = 1.2    # entry-bar volume ≥ mult × SMA
MBV_STOP_ATR_MULT  = 1.5    # stop distance = mult × ATR(14)

# ---- DBO strategy (frozen 2026-05-21 Fire 1) ----------------------------
# Donchian Breakout + Volume. Long-only trend-following BREAKOUT.
# Pre-registered before any DBO test data was seen, per v7.0 §19 (4th strategy
# in the pipeline, genuinely new methodology distinct from the existing 3
# mean-reversion/trend-confirmation strategies). Trial budget extended to 12
# to cover DBO × {US, UAE, CRYPTO}.
DBO_DONCHIAN_HIGH  = 20    # entry: close > max(high[-N:-1])
DBO_DONCHIAN_LOW   = 10    # exit:  close < min(low[-N:-1])
DBO_VOLUME_PERIOD  = 20    # SMA window for volume
DBO_VOLUME_MULT    = 1.5   # entry-bar volume >= mult x SMA
DBO_STOP_ATR_MULT  = 2.0   # stop = entry - mult x ATR(14)

# ---- ROC strategy (frozen 2026-05-21 Fire 1.5) --------------------------
# Rate-of-Change Momentum. Long-only velocity-based momentum.
# Pre-registered before any ROC test data was seen, per v7.0 §19 (5th
# strategy in the pipeline). Methodologically distinct: NOT level-based
# (EMA/Donchian) and NOT mean-reversion — buys velocity of price change.
# Trial budget extended to 15 to cover ROC × {US, UAE, CRYPTO}.
ROC_PERIOD         = 20    # bars in rate-of-change calculation
ROC_THRESHOLD      = 0.05  # entry threshold: ROC must exceed 5% over window
ROC_TREND_SMA      = 50    # bullish-regime filter
ROC_STOP_ATR_MULT  = 2.0   # stop = entry - mult x ATR(14)

# ---- VCB strategy (frozen 2026-05-21 Fire 2) ----------------------------
# Volatility Compression Breakout. Long-only volatility-cycle strategy.
# Pre-registered BEFORE any VCB test data was seen, per v7.0 §19 (6th
# strategy in the pipeline). Methodologically distinct: VOLATILITY (ATR)
# is the primary input — not price level, not price momentum, not range
# position. Captures the "compression precedes expansion" regime cycle.
# Trial budget extended to 18 to cover VCB × {US, UAE, CRYPTO}.
VCB_ATR_LOOKBACK   = 20    # window for ATR-minimum detection (compression bar)
VCB_TREND_SMA      = 50    # bullish-regime filter (no longs in downtrends)
VCB_EXPANSION_MULT = 1.5   # exit when ATR(14) > VCB_EXPANSION_MULT * mean(ATR over lookback)
VCB_STOP_ATR_MULT  = 2.0   # stop = entry - mult x ATR(14)

# ---- PMR strategy (frozen 2026-05-21 Fire 15:05 UTC) --------------------
# Price-Mean Z-score Reversion. Long-only statistical mean-reversion.
# Pre-registered BEFORE any PMR data was seen, per v7.0 §19 (8th strategy
# in the pipeline). Methodologically distinct from the seven prior strategies
# -- uses standardized z-score (close - SMA_N) / std_N as the entry filter.
# MBV uses range_pct (bounded [0,1] from raw high/low); PMR uses standardized
# deviation that AUTOMATICALLY adapts to per-ticker volatility. Two stocks
# with identical range_pct but different historical std have very different
# z-scores; PMR sees the statistical extremity raw-range strategies miss.
# Hypothesis: noisy markets (UAE / Crypto) where raw range / RSI-based mean-rev
# fails on WR floor may show edge under z-score-normalized entry signals.
# Trial budget extended to 24 to cover PMR x {US, UAE, CRYPTO}.
PMR_PERIOD         = 20    # rolling window for mean + std of close
PMR_Z_FLOOR        = 1.5   # entry: z <= -PMR_Z_FLOOR (1.5 stddev below mean)
PMR_Z_EXIT         = 0.0   # exit:  z >= PMR_Z_EXIT (mean reverted)
PMR_TREND_SMA      = 200   # bullish-regime filter (no longs below SMA(200))
PMR_VOLUME_PERIOD  = 20    # SMA window for volume confirmation
PMR_VOLUME_MULT    = 1.2   # entry-bar volume >= mult * SMA(VOLUME_PERIOD)
PMR_STOP_ATR_MULT  = 1.5   # stop = entry - mult * ATR(14)

# ---- STR strategy (frozen 2026-05-22 Sprint Catch-up) -------------------
# Stochastic %K Reversal in Trend. Long-only mean-reversion driven by the
# Stochastic %K oscillator cross-up event from oversold zone in bullish
# regime, with volume confirmation. Pre-registered BEFORE any STR data was
# seen, per v7.0 §19 (9th strategy in the pipeline). Methodologically
# distinct: %K = 100 * (close - LL_N) / (HH_N - LL_N) uses high-low RANGE
# normalization, NOT RSI gain/loss (Divergence), NOT z-score std (PMR),
# NOT range_pct lower-third bucket (MBV). Cross-up EVENT (yesterday <=20,
# today >20) is a discrete recovery confirmation, NOT a continuous level
# condition. Quick midpoint exit (%K>=50) targets small bounces -- higher
# WR by construction than full-mean-reversal exits. Hypothesis: noisy
# UAE / Crypto markets failing on the 40% WR floor may show edge with
# faster-target mean-rev that exits at range midpoint not statistical mean.
# Trial budget extended to 27 to cover STR x {US, UAE, CRYPTO}.
STR_PERIOD         = 14    # lookback for stochastic high/low range
STR_OS_LEVEL       = 20.0  # cross-up from <= this level fires entry
STR_EXIT_LEVEL     = 50.0  # midpoint exit -- captures small bounce
STR_TREND_SMA      = 200   # regime filter (no longs below SMA(200))
STR_VOLUME_PERIOD  = 20    # SMA window for volume confirmation
STR_VOLUME_MULT    = 1.2   # entry-bar volume >= mult * SMA(VOLUME_PERIOD)
STR_STOP_ATR_MULT  = 1.5   # tight stop -- mean-rev thesis breaks fast

# ---- ART strategy (frozen 2026-05-22 Sprint) ----------------------------
# Aroon Time-Trend Strength. Long-only TIME-DOMAIN trend-strength strategy.
# Pre-registered BEFORE any ART data was seen, per v7.0 §19 (10th strategy
# in the pipeline). Methodologically distinct: Aroon measures BAR-COUNT-
# SINCE-EXTREME (time domain), while every prior strategy is magnitude-domain
# (levels, derivatives, oscillator values, range positions, std deviations).
# AroonUp(N) = 100*(N - bars_since_N_high)/N; AroonDown(N) symmetric on lows.
# AroonOsc = AroonUp - AroonDown. Cross-up of Osc above +50 fires entry.
# Hypothesis: noisy UAE / Crypto markets failing on the 40% WR floor may
# show edge under time-since-extreme dominance, which only flips when a
# structural new-high cluster appears -- more selective than magnitude
# signals that fire on chop. Trial budget extended 27 -> 30 to cover
# ART x {US, UAE, CRYPTO}.
ART_AROON_PERIOD         = 14   # lookback for Aroon Up / Down (Chande default)
ART_AROON_OSC_THRESHOLD  = 50.0 # cross-up of (AroonUp - AroonDown) above this fires entry
ART_TREND_SMA            = 50   # regime filter (no longs below SMA(50))
ART_VOLUME_PERIOD        = 20   # SMA window for volume confirmation
ART_VOLUME_MULT          = 1.2  # entry-bar volume >= mult * SMA(VOLUME_PERIOD)
ART_STOP_ATR_MULT        = 2.0  # wider stop -- trend-continuation thesis

# ---- CMF strategy (frozen 2026-05-22 Sprint Obj-6 advance) --------------
# Chaikin Money Flow mean-reversion in bullish regime. Long-only.
# Pre-registered BEFORE any CMF data was seen, per v7.0 §19 (11th strategy
# in the pipeline). Methodologically distinct: CMF is the FIRST strategy
# whose PRIMARY signal is volume-weighted money-flow INTEGRATED over a
# rolling window. Every prior strategy uses volume only as a confirmation
# (>= 1.2 * SMA(20)). CMF is a different domain altogether:
#   CMF(N) = sum_{i=t-N+1..t}( MFV_i ) / sum_{i=t-N+1..t}( volume_i )
#   where MFV_i = ((close_i - low_i) - (high_i - close_i)) / (high_i - low_i) * volume_i.
# The per-bar money-flow multiplier ((C-L)-(H-C))/(H-L) records WHERE in
# its range each bar closed, weighted by volume. CMF integrates this over
# N bars -- positive means accumulation dominated, negative means
# distribution dominated. No prior strategy reads this signal.
# Hypothesis: short-term distribution (CMF < -0.05) inside an intact
# long-term bullish regime (close > EMA-200) is an oversold-in-trend
# setup -- price is being sold into in the near term while the macro
# trend is up. Mean-reversion to neutral/positive money flow likely.
# Higher-probability target than full-trend retrace; quick exit at
# CMF > +0.10 (accumulation flip) targets a small reversion, similar in
# spirit to STR's midpoint exit. Long-only by construction (CMF acts on
# the close-position-in-range signal -- inherently directional).
# Trial budget extended 30 -> 33 to cover CMF x {US, UAE, CRYPTO}.
CMF_PERIOD          = 20    # lookback bars for money-flow accumulation
CMF_OS_LEVEL        = -0.05 # entry threshold: CMF below this is distribution
CMF_EXIT_LEVEL      = 0.10  # exit threshold: CMF above this is accumulation flip
CMF_TREND_EMA       = 200   # regime filter (no longs unless close > EMA(200))
CMF_TURNAROUND_BARS = 1     # require today's close > yesterday's close (turnaround)
CMF_VOLUME_PERIOD   = 20    # SMA window for volume sanity check
CMF_VOLUME_MIN_MULT = 1.0   # entry-bar volume >= mult * SMA(VOLUME_PERIOD); 1.0 = at-or-above-average
CMF_STOP_ATR_MULT   = 1.5   # tight stop -- mean-rev thesis breaks fast

# ---- GAP strategy (frozen 2026-05-22 Sprint Obj-6 advance, 11:48 UTC) ---
# Overnight Gap Continuation in Uptrend. Long-only between-bar discontinuity
# strategy. Pre-registered BEFORE any GAP data was seen, per v7.0 §19 (12th
# strategy in the pipeline). Methodologically distinct from the eleven prior
# strategies: every prior strategy reads WITHIN-BAR or ROLLING-WINDOW
# primitives -- close vs EMA, close vs Donchian, range_pct, z-score, %K,
# Aroon bars-since-extreme, Heikin-Ashi smoothed bars, CMF integrated money
# flow. GAP reads the BETWEEN-BAR price discontinuity: today's open versus
# yesterday's close. The gap event exists only at the open print and is not
# captured by any rolling-window aggregator. Hypothesis (frozen pre-data):
# an overnight gap up of >= 2% in an established uptrend that does NOT fade
# intraday (close > open) and is confirmed by elevated volume (>= 1.5x
# average) represents an institutional commitment; price tends to continue
# in the gap direction for several bars before mean-reverting. The exit
# logic targets both continuation profits (close < SMA(10) -> short-term
# momentum lost) and gap-fade protection (close < entry-bar open -> the
# gap filled, hypothesis broken). Distinct from EMA-200 (trend confirm,
# not gap event), DBO (rolling-window high breakout, not open print), VCB
# (volatility compression, not directional price discontinuity). May trade
# rarely on continuous-quote markets (crypto via yfinance 1D bars have
# defined opens but small gaps -- if too rare, FAIL is honest verdict per
# audit Concern 2, no parameter loosening). Trial budget extended 33 -> 36
# to cover GAP x {US, UAE, CRYPTO}.
GAP_THRESHOLD       = 0.02  # entry: open >= prior_close * (1 + threshold) -- 2% overnight gap up
GAP_TREND_SMA       = 50    # regime filter (no longs unless close > SMA(50))
GAP_EXIT_SMA        = 10    # exit when close < SMA(GAP_EXIT_SMA) -- short-term momentum lost
GAP_VOLUME_PERIOD   = 20    # SMA window for volume confirmation
GAP_VOLUME_MULT     = 1.5   # entry-bar volume >= mult * SMA -- elevated volume confirms gap
GAP_STOP_ATR_MULT   = 1.5   # stop = entry - mult * ATR(14); tight -- mean-rev fast if thesis fails

# ---- WCK strategy (frozen 2026-05-22 Sprint Obj-6 advance, post-GAP) ----
# Lower-Wick Rejection Mean-Reversion in bullish regime. Long-only.
# Pre-registered BEFORE any WCK data was seen, per v7.0 §19 (13th strategy
# in the pipeline). Methodologically distinct: WCK is the FIRST strategy
# whose PRIMARY signal is the INTRA-BAR SHAPE RATIO of a single candle --
# specifically the lower-wick-to-range ratio (min(O,C) - L) / (H - L). Every
# prior strategy reads either between-bar (GAP open-vs-prior-close), rolling-
# window (EMA200/MBV/DBO/ROC/VCB/PMR/STR/ART), recursive smoothed (HAT HA
# bars), volume-integrated (CMF), or swing-pivot (Divergence) primitives.
# CMF uses ((C-L)-(H-C))/(H-L) (close-position within range) BUT then
# integrates over N bars with volume weighting -- the SINGLE-BAR shape
# primitive itself is unused as a primary signal. WCK reads the unaggregated
# single-bar wick anatomy. Hypothesis (frozen pre-data): in a bullish regime
# (close > SMA(200)), a single bar with lower wick >= 50% of bar range AND
# body <= 35% of range -- the canonical hammer / long-lower-wick pattern --
# is intra-bar evidence of buyers rejecting a tested lower price. Coupled
# with elevated volume, this signals institutional accumulation at a
# perceived low. Quick exit when close exceeds prior 5-bar high (small
# bounce captured) targets a higher-WR small-target trade. Long-only by
# construction (long-lower-wick pattern is asymmetrically bullish; the
# inverse "shooting-star" pattern would be the short equivalent under
# Rule 15, which forbids shorts). Trial budget extended 36 -> 39 to
# cover WCK x {US, UAE, CRYPTO}.
WCK_WICK_RATIO_FLOOR     = 0.5    # lower wick must be >= this fraction of bar range
WCK_BODY_RATIO_CEIL      = 0.35   # body must be <= this fraction of bar range
WCK_MIN_RANGE_ATR_RATIO  = 0.5    # bar range must be >= mult * ATR(14) -- skip dojis/microscopic bars
WCK_TREND_SMA            = 200    # bullish regime filter
WCK_VOLUME_PERIOD        = 20     # SMA window for volume confirmation
WCK_VOLUME_MULT          = 1.2    # entry-bar volume >= mult * SMA(VOLUME_PERIOD)
WCK_EXIT_LOOKBACK        = 5      # exit when close >= rolling max of prior N closes
WCK_STOP_ATR_MULT        = 1.0    # tight stop -- wick rejection thesis breaks fast

# ---- HAT strategy (frozen 2026-05-21 Fire 14:55 UTC) --------------------
# Heikin-Ashi Trend Continuation. Long-only signal derived from SMOOTHED
# (Heikin-Ashi) candles rather than raw OHLC. Pre-registered BEFORE any
# HAT data was seen, per v7.0 §19 (7th strategy in the pipeline).
# Methodologically distinct from the six prior strategies — every prior
# strategy operates on RAW bars (close > EMA, close > Donchian high,
# range_pct on raw high/low, ROC on close, ATR-min on raw ATR). HAT
# replaces the raw OHLC input with a recursive filtered representation
# (HA_close = (O+H+L+C)/4, HA_open = (prev_HA_open + prev_HA_close)/2).
# The filter dampens individual-bar noise and surfaces multi-bar trend
# regimes that raw-bar strategies miss. Hypothesis: noisy markets
# (UAE / Crypto) where raw-bar strategies fail on WR floor may show edge
# under noise-smoothed entry/exit signals. Trial budget extended to 21
# to cover HAT × {US, UAE, CRYPTO}.
HAT_BULLISH_BARS   = 3     # entry: N consecutive bullish HA candles (HA_close > HA_open)
HAT_TREND_EMA      = 200   # regime filter (no longs unless raw close > EMA(200))
HAT_VOLUME_PERIOD  = 20    # SMA window for volume confirmation
HAT_VOLUME_MULT    = 1.2   # entry-bar volume >= mult x SMA(VOLUME_PERIOD)
HAT_STOP_ATR_MULT  = 2.0   # stop = entry - mult x ATR(14)

# ---- Divergence strategy (frozen 2026-05-20, daily) ----------------------
# Bullish RSI divergence on swing lows, long-only, with EMA-200 trend filter.
DIV_RSI_PERIOD = 14
DIV_PIVOT_HALFWIDTH = 5    # a "swing low" = local minimum over 5 bars each side
DIV_LOOKBACK_BARS = 60     # compare two most recent swing lows within this window
DIV_TREND_EMA = 200        # only take divergence longs above this trend EMA
DIV_RSI_EXIT = 65          # exit when RSI closes >= this (or stop hit)
DIV_STOP_ATR_MULT = 1.5    # stop = swing-low - 1.5*ATR(14)

# ---- Timeframe support ---------------------------------------------------
# bars per trading year, used for annualising Sharpe per timeframe.
# US equities: 252 days * 6.5h = 1638 trading hours/yr.
# Crypto: 24*365 = 8760 hours/yr (24/7 markets).
BARS_PER_YEAR = {
    "1d": 252,
    "1h": 1638,          # US equities; for crypto we'd use 8760 but engine uses observed freq
    "4h": 410,           # ~1638/4
    "1w": 52,
}

# ---- Per-market cost model (round-trip, applied in backtest) -------------
# bps = basis points of notional; slippage modelled separately in costs.py
MARKET_COSTS = {
    "US":     {"commission_bps": 1.0,  "spread_bps": 2.0,  "slippage_bps": 3.0},
    "UAE":    {"commission_bps": 2.75, "spread_bps": 8.0,  "slippage_bps": 12.0},
    "CRYPTO": {"commission_bps": 10.0, "spread_bps": 6.0,  "slippage_bps": 15.0},
}

# ---- Phase 1 framework directive amendments (frozen 2026-05-22) ---------
# Six amendments to the validation gate per Ahmed's Phase 1 framework
# directive 2026-05-22 (ahmed_response_2026-05-22.md). Pre-registered
# atomically in the commit that introduces them; the new config_hash binds
# them to all future runs. Apply PROSPECTIVELY only -- existing Session 5
# verdicts under the OLD hash are NOT re-evaluated retroactively (per
# directive Part 3). Re-evaluation requires Method A (fresh OOS window) or
# Method B (forward data accumulation, ~Nov 2026+).
#
# Framework finality: these amendments + the three-filter methodology in
# strategy_register.md are FROZEN for 6 months from this commit date.

# Amendment 1 -- archetype-based WR floor (DORMANT until auto-execution exists)
# Mean-reversion + pullback strategies keep the 0.40 floor unchanged.
# Trend-following / breakout / momentum strategies may use a relaxed floor
# IF AND ONLY IF dSharpe >= 1.5 AND PF >= 2.0 AND bootstrap CI lower bound
# on mean trade return > 0 AND auto-execution layer exists. None of these
# qualifying conditions hold today -- AUTO_EXECUTION_LAYER_EXISTS = False.
WR_FLOOR_BY_ARCHETYPE = {
    "pullback":         0.40,
    "mean_reversion":   0.40,
    "trend_following":  None,   # relaxation eligible (gated by auto-execution)
    "breakout":         None,   # relaxation eligible
    "momentum":         None,   # relaxation eligible
    "volatility_cycle": 0.40,   # not explicitly named in Amendment 1 -- strict
    "statistical_arb":  0.40,   # long-only constraint limits these
    "event_driven":     0.40,   # not explicitly named in Amendment 1 -- strict
}

WR_FLOOR_RELAXATION_THRESHOLDS = {
    "min_dsharpe":             1.5,    # 3x the standard 0.5 floor
    "min_profit_factor":       2.0,
    "min_bootstrap_ci_lower":  0.0,    # mean trade return CI strictly > 0
    "requires_auto_execution": True,
}

# Auto-execution layer is a Phase 2 infrastructure build. Until True, the
# relaxed WR floor cannot activate; ALL strategies use the strict floor
# regardless of archetype. Set this to True only after the auto-execution
# layer is implemented AND passes its own validation (idempotency, slippage
# modeling, fail-safe halt).
AUTO_EXECUTION_LAYER_EXISTS = False

# Amendment 2 -- per-market trade-count floor
# Replaces a single global min_trades with a fixed table keyed by market.
# New markets pre-register the floor at universe-onboarding time, BEFORE
# any test runs on that market. The formula
# `max(100, sqrt(universe * years * signal_freq))` proposed earlier is
# explicitly rejected (signal_freq is a tuning backdoor).
MIN_TRADES_BY_MARKET = {
    "US":     1000,
    "UAE":    200,
    "CRYPTO": 400,
    "GCC":    None,   # Phase 2 infrastructure -- set at GCC onboarding
}

# Amendment 3 -- profit factor floor
# OOS PF >= 1.5. Bootstrap CI lower bound on PF >= 1.0 (even at the pessimistic
# end of the bootstrap distribution, the strategy must be break-even on a
# profit-factor basis). Only evaluated when n >= 30 trades.
MIN_PROFIT_FACTOR = 1.5
MIN_PROFIT_FACTOR_CI_LOWER = 1.0
PROFIT_FACTOR_MIN_N = 30

# Amendment 4 -- multi-timeframe as separate pre-registered trials
# Process amendment, not a config knob. Each (strategy x market x timeframe)
# is one trial in strategy_register.md TRIAL_BUDGET. Adding a TF tightens
# the multi-test haircut. No config flag needed.

# Amendment 5 -- GCC universe (DEFERRED TO PHASE 2 INFRASTRUCTURE)
# Trading scope remains UAE-only. GCC (Saudi + Kuwait + Qatar + Bahrain)
# halal aggregate ~400-500 tickers is a discovery-and-validation tool, NOT
# a deployment market. Any strategy that clears the GCC-wide gate must ALSO
# pass a separate UAE-only certification (hard gate, same status as Shariah).
# Strategies clearing GCC but failing UAE-only are tagged
# GCC_only_edge_not_UAE_deployable in strategy_register and shelved.
# Phase 2 infrastructure -- does NOT exist yet, does NOT consume Phase 1 slots.
GCC_UNIVERSE_ENABLED = False

# Amendment 6 -- OOS calendar time-span floor
# OOS trades must span at least 24 calendar months. A strategy with sufficient
# trades but temporally narrow OOS sample (e.g., last 18 months only) could
# be a regime artifact. Verdict INSUFFICIENT_OOS_SPAN when sufficient trades
# but insufficient calendar span. This applies on top of trade-count floors.
MIN_OOS_CALENDAR_MONTHS = 24

# OOS-to-IS Sharpe ratio robustness check (paired with Amendment 6)
# A strategy that aces in-sample and barely passes OOS is suspect for
# overfitting even if both nominally clear gates. Require OOS Sharpe >= 0.7 x
# IS Sharpe at minimum (the lower-noise version Amendment 2 invokes).
MIN_OOS_TO_IS_SHARPE_RATIO = 0.7

# ---- Validation gate thresholds (frozen) ---------------------------------
# Per-ticker gate: certifies "ticker X with strategy S has edge". Strict
# n>=30 with multi-test haircut over N_tickers — appropriate for narrow
# focused claims, harsh for broad-universe strategies.
GATE = {
    "min_trades": 30,            # below this, sample too small to judge
    "min_oos_sharpe": 0.5,       # annualised, out-of-sample, AFTER costs
    "min_expectancy": 1.0,       # (avgWin*WR)/(avgLoss*LR) > 1 = positive edge
    "bootstrap_iters": 2000,
    "bootstrap_conf": 0.95,      # 95% CI lower bound on mean trade return must be > 0
    "alpha": 0.05,               # significance level before multiple-testing correction
    "train_frac": 0.6,           # in-sample / out-of-sample split point
    "wf_folds": 5,               # walk-forward rolling folds over the full history
}

# Portfolio-level gate (frozen 2026-05-20, trial-budget amendment 2026-05-21):
# aggregates ALL trades across the universe into one sample, certifies
# "strategy S has edge across the universe". Multi-testing is applied at the
# TRIAL level — one trial per (strategy × market × timeframe) combination
# the CEO has run. Pre-registered trial budget lives in strategy_register.md.
#
# Per auditor finding 2026-05-21 (Concern 1): the haircut MUST cover every
# trial the CEO chose between, including the failing ones, not just the
# winning subset. n_trials_registered is the binding count.
PORTFOLIO_GATE = {
    # Legacy keys (preserved for back-compat with existing validation_gate.py)
    "min_trades": 1000,          # US default; per-market table is binding via min_trades_by_market
    "min_oos_sharpe": 0.5,       # deflated, with sqrt(2 ln N_trials) haircut
    "min_expectancy": 1.0,       # aggregate expectancy > 1.0
    "min_win_rate": 0.40,        # legacy strict floor; superseded by wr_floor_by_archetype when archetype set
    "min_universe_coverage": 0.05, # at least 5% of universe must contribute trades
    "bootstrap_iters": 2000,
    "bootstrap_conf": 0.95,
    "n_trials_registered": 39,   # 13 sprint-loop strategies (ema200..wck) x 3 markets x 1D.
                                 # WCK added 2026-05-22 (post-GAP). Phase 1 framework directive 2026-05-22
                                 # tags all 13 as Pre-Framework, sprint-loop-tested. Phase 1 candidates
                                 # under the new three-filter methodology will add NEW trials on top of
                                 # this count -- n_trials_registered will grow, the haircut tightens.

    # ---- Phase 1 directive amendments (2026-05-22) -----------------------
    "min_trades_by_market":              MIN_TRADES_BY_MARKET,             # Amendment 2
    "min_profit_factor":                 MIN_PROFIT_FACTOR,                # Amendment 3
    "min_profit_factor_ci_lower":        MIN_PROFIT_FACTOR_CI_LOWER,       # Amendment 3
    "profit_factor_min_n":               PROFIT_FACTOR_MIN_N,              # Amendment 3
    "min_oos_calendar_months":           MIN_OOS_CALENDAR_MONTHS,          # Amendment 6
    "min_oos_to_is_sharpe_ratio":        MIN_OOS_TO_IS_SHARPE_RATIO,       # Amendment 2 extension
    "wr_floor_by_archetype":             WR_FLOOR_BY_ARCHETYPE,            # Amendment 1
    "wr_floor_relaxation_thresholds":    WR_FLOOR_RELAXATION_THRESHOLDS,   # Amendment 1
    "auto_execution_layer_exists":       AUTO_EXECUTION_LAYER_EXISTS,      # Amendment 1 gate
    "gcc_universe_enabled":              GCC_UNIVERSE_ENABLED,             # Amendment 5

    # Framework finality (binding): freeze begins on this commit's date.
    "framework_freeze_start":            "2026-05-22",
    "framework_freeze_months":           6,
}

# ---- Reproducibility -----------------------------------------------------
RANDOM_SEED = 20260517

# ---- Markets & how a ticker is classified --------------------------------
def market_of(ticker: str) -> str:
    if ticker.endswith("-USD") or ticker.endswith("USDT"):
        return "CRYPTO"
    if ticker.endswith(".AD") or ticker.endswith(".DU") or ticker.endswith(".DFM"):
        return "UAE"
    return "US"
