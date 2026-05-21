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
    "min_trades": 1000,          # certifying a strategy, not a ticker — demand mass
    "min_oos_sharpe": 0.5,       # deflated, with sqrt(2 ln N_trials) haircut
    "min_expectancy": 1.0,       # aggregate expectancy > 1.0
    "min_win_rate": 0.40,        # broad strategies survive on positive expectancy + WR floor
    "min_universe_coverage": 0.05, # at least 5% of universe must contribute trades
    "bootstrap_iters": 2000,
    "bootstrap_conf": 0.95,
    "n_trials_registered": 9,    # 3 strategies (ema200, divergence, mbv) × 3 markets × 1 timeframe (1D).
                                 # MBV added 2026-05-21 — trial budget bumped accordingly.
                                 # Adding a 4H variant → +N. Pre-register in strategy_register.md before running.
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
