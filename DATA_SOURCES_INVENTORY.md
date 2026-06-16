# DATA SOURCES INVENTORY — MCP servers + US-Vault consumable data

Read-only inventory, 2026-06-16. **Nothing switched.** Recommendation only.
Purpose: prefer structured, reproducible data over live-yfinance going forward.

---

## 1. MCP SERVERS configured/connected (this environment, `claude mcp list`)

| Server | Status | Provides | Market data? |
|---|---|---|---|
| **claude.ai FMP** (Financial Modeling Prep) | ✔ Connected | quotes, **chart = historical OHLCV**, statements/fundamentals, crypto, forex, commodities, indexes, technical indicators, analyst, earnings transcripts, SEC filings, insider/senate trades, economics, 13F, ESG, news | **YES — strongest** |
| **tradingview** (local node server) | ✔ Connected | `data_get_ohlcv`, quotes, indicators, symbol search, chart control | YES (caveats below) |
| claude.ai Morningstar | ! Needs auth | equity/fund research data | YES (unusable until auth) |
| claude.ai Aiera | ! Needs auth | earnings calls/events/transcripts | partial (events) |
| claude.ai Figma | ✔ Connected | design (not data) | no |
| claude.ai higgsfield | ✔ Connected | media generation | no |
| claude.ai Gmail | ✔ Connected | email | no |
| claude.ai Google Drive / Microsoft 365 / Gamma | ! Needs auth | docs/storage/decks | no |

**Note:** the tools named in global CLAUDE.md routing (edgartools, openinsider,
fred, youtube-transcript, chrome-devtools, Context7) are **NOT connected in this
environment** per `claude mcp list` — do not assume they're available here.

### Market-data-capable, assessed as a yfinance alternative
- **FMP (CONNECTED, no per-call auth):** US equities (deep) + crypto + forex +
  commodities + indexes. Gives **raw historical OHLCV** (`chart`) and fundamentals
  (`statements`). Commercial-grade, generally canonical for US. **UAE coverage
  weak** (ADX/DFM — UAE is already cache-pinned via TradingView, so this is moot).
  Caveat: like yfinance, FMP's adjusted series **revises** (splits/divs) — so the
  freeze discipline still applies regardless of source.
- **tradingview (CONNECTED):** very broad (US/UAE/crypto, anything on TV). BUT it is
  **UI/Chrome-driven** via the protected tv-grind Chrome (**port 9222 — never
  attach/disrupt**), one symbol at a time, tied to a live desktop session →
  **not reliable as a bulk canonical historical source.** Good for spot-checks and
  UAE names; not for 1,600-ticker history pulls.
- **Morningstar/Aiera:** need auth; not usable now.

### RECOMMENDATION (inventory only — do NOT switch yet)
1. **Best canonical US source is the US Vault's Sharadar-backed OHLC cache**
   (section 2) — institutional, point-in-time, survivorship-aware — consumed
   **read-only**. Superior to both yfinance and FMP for reproducibility.
2. **FMP** is the best *MCP* fallback/supplement (connected, raw OHLCV, no auth) if
   vault consumption isn't wired.
3. **The frozen `data_cache` snapshot stays the reproducibility anchor regardless**
   — any adjusted source revises, so "freeze then validate" is unchanged. A new
   source changes only where we *regenerate* the snapshot from, not the discipline.

---

## 2. US VAULT (us-strategy-vault) — consumable data (READ-ONLY; never modify)

Repo: `C:\Users\ahmed\us-strategy-vault`. AIG may **consume its outputs, never
modify the vault.** What it exposes:

- **OHLC cache** — `ohlc_cache/` : **1,543 US tickers**, daily OHLCV CSV
  (`date,unix,open,high,low,close,volume`), history back to **1980** (e.g. AAPL
  from 1980-12-12). **Source: Sharadar (Nasdaq Data Link)** — institutional,
  adjusted. Format: per-ticker CSV (same shape AIG's `_cache_read` already expects).
- **Live halal universe** — `data/live_halal_universe_3M.parquet` (+meta):
  provider Halal list ∩ trailing-90d $3M ADDV liquidity floor, **month-end PIT**,
  window 1998-01-31 .. 2026-06-30, ~1,020 current / 1,235 distinct-ever names.
  **Survivorship caveat:** today's provider list carried back (living names only;
  long-only magnitudes biased up — lean on market-excess).
- **L78 survivorship-free PIT halal membership** — `data/L78_halal_membership.parquet`:
  Sharadar-backed, delisted-inclusive (11,345 distinct halal names ever; 7,358
  delisted recovered), 1998–2026 month-end. **⚠ PARKED:** its meta WARNS the
  membership definition is **not yet faith-equivalent** to the provider screen
  (being rebuilt) — the survivorship machinery + dollar-volume cache are valid, but
  **do NOT use L78 for halal membership** until the faith ruling. Use the live
  provider universe instead.
- **Sharadar PIT fundamentals** — `data/sharadar_client.py` + `sharadar_cache/`:
  SF1 (debtusd, cashnequsd, marketcap, receivables, …), restatement-aware
  (`datekey`), incremental watermark pulls. Backs the AAOIFI financial screen
  (r1/r2/r3 < 0.33).
- **Strategy library** — `library/STRATEGY_LIBRARY_V5_CANONICAL.md` + `us_lib.py`:
  tested strategy specs.

**Format/where:** CSV (OHLC) + parquet (universes) + parquet cache (fundamentals),
all under `C:\Users\ahmed\us-strategy-vault\{ohlc_cache,data}`. Coverage: **US only**
(no UAE/Crypto). Provenance: Sharadar PIT — the canonical-grade anchor.

**Proposed (nothing adopted):** AIG could, read-only, regenerate its frozen US
snapshot from the vault's Sharadar `ohlc_cache` instead of yfinance, and source the
halal universe from `live_halal_universe_3M.parquet` (NOT L78 yet). This would make
US data institutional-grade + PIT. Requires an operator decision + a freeze step;
**not done here.**
