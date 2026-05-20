"""
LAYER 1 — Data, with the data-integrity gate (Layer B item 4).

Two paths:
  • yfinance adapter — primary live data source (free, reliable, intraday-capable).
  • Offline synthetic — deterministic, so the engine runs and tests pass
    anywhere (including no-network sandboxes).

The data-integrity gate runs BEFORE any backtest. Bad data produces a
convincing lie, so a failed integrity check hard-blocks the ticker.

CEO v7.0 amendment (2026-05-20): added `timeframe` param. Switched live
adapter from OpenBB to yfinance directly (one less indirection, reliable
1H/4H intraday support). Integrity gate is now timeframe-aware: the
spike/split heuristic uses 30% for 1H bars (vs 50% for daily) and the gap
heuristic uses 7 calendar days (was 10) for intraday.
"""

from __future__ import annotations
import numpy as np
import pandas as pd

from config import RANDOM_SEED, market_of
from aig.agents import audit


# ---- Live data via yfinance (real, runs on the user's machine) -----------
_TIMEFRAME_YF = {"1d": "1d", "1h": "1h", "60m": "60m", "4h": "4h", "1w": "1wk"}


def _yf_history(ticker: str, timeframe: str = "1d") -> pd.DataFrame:
    import yfinance as yf
    interval = _TIMEFRAME_YF.get(timeframe, timeframe)
    market = market_of(ticker)
    # yfinance limits: 1h = 730 days max. Daily = unlimited.
    # Crypto: limit to 7y on daily to skip the 2017-2018 pump-era data where
    # many alts legitimately had >100% daily moves that confuse the integrity
    # gate. 7y is still enough sample for portfolio-level validation.
    if interval in ("1h", "60m", "4h"):
        period = "730d"
    elif market == "CRYPTO":
        period = "7y"
    else:
        period = "15y"
    df = yf.download(ticker, period=period, interval=interval,
                     auto_adjust=True, progress=False, threads=False)
    if df is None or len(df) == 0:
        raise RuntimeError(f"yfinance returned empty frame for {ticker} @ {interval}")
    # Newer yfinance returns MultiIndex columns for single tickers — flatten.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    df = df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]]
    df.index = pd.to_datetime(df.index)
    df = df.dropna(subset=["close"])
    return df


# ---- Offline deterministic synthetic OHLCV -------------------------------
def _synthetic_history(ticker: str, days: int = 1500) -> pd.DataFrame:
    rng = np.random.default_rng((abs(hash(ticker)) ^ RANDOM_SEED) % (2**32))
    drift = {"AAPL": 4e-4, "MSFT": 3e-4, "NVDA": 7e-4, "XOM": 1e-4,
             "BTC-USD": 5e-4}.get(ticker, 2e-4)
    vol = 0.035 if ticker.endswith("-USD") else 0.016
    r = rng.normal(drift, vol, days)
    close = pd.Series(100 * np.exp(np.cumsum(r)))
    high = close * (1 + np.abs(rng.normal(0, vol / 2, days)))
    low = close * (1 - np.abs(rng.normal(0, vol / 2, days)))
    op = close.shift(1).fillna(close.iloc[0])
    idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=days * 2)[-days:]
    return pd.DataFrame({"open": op.values, "high": high.values, "low": low.values,
                         "close": close.values,
                         "volume": rng.integers(1e6, 9e6, days)}, index=idx)


def get_history(ticker: str, offline: bool = True,
                timeframe: str = "1d") -> pd.DataFrame:
    if offline:
        return _synthetic_history(ticker)
    try:
        return _yf_history(ticker, timeframe=timeframe)
    except Exception as e:
        audit("IN-L", f"yfinance fetch failed for {ticker} @ {timeframe}: {e}. "
                      f"NOT falling back to synthetic for a real run — ticker skipped.")
        raise


# ---- Data-integrity gate -------------------------------------------------
def integrity_check(ticker: str, df: pd.DataFrame,
                    timeframe: str = "1d") -> tuple[bool, list[str]]:
    """Hard pre-backtest checks. Any failure blocks the ticker."""
    fails: list[str] = []
    if df is None or len(df) < 300:
        fails.append(f"insufficient history ({0 if df is None else len(df)} rows < 300)")
        audit("RI-H", f"{ticker} integrity FAIL: {fails[-1]}")
        return False, fails

    if df[["open", "high", "low", "close"]].isna().any().any():
        fails.append("NaN in OHLC")
    if (df["close"] <= 0).any():
        fails.append("non-positive close prices")
    # high/low sanity with scale-relative tolerance (1e-7 of close) — yfinance
    # auto-adjusted bars occasionally have high==close differing by machine
    # epsilon (~1e-15) which is real data, not corruption.
    tol = df["close"].abs() * 1e-7
    if ((df["high"] + tol < df["low"]) |
            (df["high"] + tol < df["close"]) |
            (df["low"] - tol > df["close"])).any():
        fails.append("high/low/close inconsistency")
    # date monotonicity + gap check (look-ahead / corporate-action guard)
    if not df.index.is_monotonic_increasing:
        fails.append("non-monotonic dates")
    # gap threshold: intraday bars are dense so gap >2d is suspicious; daily allows 10d.
    gap_days_threshold = 2 if timeframe in ("1h", "60m", "4h") else 10
    gaps = df.index.to_series().diff().dt.days.dropna()
    if (gaps > gap_days_threshold).sum() > len(df) * 0.02:
        fails.append(f"excessive date gaps (>2% of bars gap >{gap_days_threshold}d)")
    # extreme unadjusted-split jump heuristic. Market-aware: crypto can
    # legitimately move >50%, so use a looser threshold for it.
    rets = df["close"].pct_change().dropna()
    market = market_of(ticker)
    if market == "CRYPTO":
        spike_threshold = 0.60 if timeframe in ("1h", "60m", "4h") else 1.00
    else:
        spike_threshold = 0.30 if timeframe in ("1h", "60m", "4h") else 0.50
    if (rets.abs() > spike_threshold).sum() > 0:
        fails.append(f"unadjusted split/spike suspected (|ret|>{int(spike_threshold*100)}%)")

    ok = len(fails) == 0
    audit("RI-H", f"{ticker}@{timeframe} integrity {'PASS' if ok else 'FAIL ' + str(fails)}")
    return ok, fails
