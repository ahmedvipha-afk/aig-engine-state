# URLs for Cowork + browser viewing

## Dashboard (browser-rendered HTML — opens like a real webpage)

**Use this URL when opening dashboard.html in a browser:**

```
https://ahmedvipha-afk.github.io/aig-engine-state/dashboard.html
```

Hosted via **GitHub Pages**. Serves `Content-Type: text/html` so browsers
render it instead of showing source code. Updates after every Cloud
Routine fire (push to main triggers Pages rebuild — ~30s).

Local fallback (Ahmed's machine):
```
file:///C:/Users/ahmed/OneDrive/Documents/Projects/stocks/Ahmed%20group/Working%20Area/aig_engine/dashboard.html
```

## Raw file ingestion (for Cowork to parse JSON/Markdown)

Use the raw URL pattern. Returns the file as `text/plain` — perfect for
machine parsing, NOT for browser rendering of HTML.

```
https://raw.githubusercontent.com/ahmedvipha-afk/aig-engine-state/main/<path>
```

**Common mistake:** using `github.com/.../blob/main/<file>` returns the HTML
viewer, not the file. Use `raw.githubusercontent.com` exactly as above.

## CDN cache notes

raw.githubusercontent.com sets `Cache-Control: max-age=300` (5 min). Two
options if Cowork needs a fresh fetch immediately:

1. Append a cache-buster query string. The CDN ignores unknown query params
   but the cache key includes them, forcing a fresh upstream fetch:
   ```
   https://raw.githubusercontent.com/ahmedvipha-afk/aig-engine-state/main/ceo_brain.md?t=<unix_timestamp>
   ```

2. Pin to a specific commit SHA — these URLs are immutable, never cached
   incorrectly, and always return that exact snapshot:
   ```
   https://raw.githubusercontent.com/ahmedvipha-afk/aig-engine-state/<commit_sha>/ceo_brain.md
   ```
   The commit SHA is in every Telegram daily summary and in the dashboard
   footer.

## Index of Cowork-relevant files

### State files (read every poll)
| Path | Purpose |
|------|---------|
| `ceo_brain.md` | Current CEO state, decisions, instructions to future self |
| `auditor_report.md` | Latest independent audit (if present) |
| `strategy_register.md` | Pre-registered strategies + binding trial budget |
| `dashboard.html` | Rendered cockpit (open in browser) |

### Validation results (read after each Cloud Routine fires)
| Path | Purpose |
|------|---------|
| `validation_divergence_1d_full_haircut6.json` | Latest US Divergence portfolio (audit-corrected N=6 haircut) |
| `validation_uae_divergence_1d_v3.json` | Latest UAE Divergence portfolio |
| `validation_crypto150_divergence_1d_v3.json` | Latest Crypto Divergence portfolio |
| `validation_us_ema200_1d_full.json` | Latest US EMA-200 portfolio |
| `validation_morning_<YYYYMMDD>.json` | Daily morning-scan portfolio (top-30) |
| `validation_weekly_divergence_<YYYYMMDD>.json` | Sunday weekly full-universe |

### Universes (read once + re-poll when CEO updates)
| Path | Purpose |
|------|---------|
| `universe/us_halal_full.txt` | 1,603 US halal tickers (mcap-sorted) |
| `universe/us_halal_top30.txt` | Top 30 by mcap |
| `universe/us_halal_meta.json` | Per-ticker name/ISIN/sector/mcap |
| `universe/uae_tickers_full.txt` | 44 UAE retrievable (cache + yfinance) |
| `universe/halal_crypto_150_USD.txt` | 150 crypto tickers (-USD suffix) |

### Reports (Telegram-attached, also web-fetchable)
| Path | Purpose |
|------|---------|
| `reports/kpi_<YYYY-WW>.xlsx` | Weekly KPI scorecard |
| `reports/monthly_<YYYY-MM>.xlsx` | Monthly multi-sheet report |

### Strategy code (frozen specs)
| Path | Purpose |
|------|---------|
| `config.py` | All frozen parameters (gates + strategies) |
| `aig/strategy_ema200.py` | EMA-200 + volume confirm rules |
| `aig/strategy_divergence.py` | RSI divergence rules |
| `aig/validation_gate.py` | Per-ticker + portfolio gate logic |
| `pine/aig_ema200_vol_v1.pine` | Pine v6 mirror of EMA-200 |

## Provenance binding

Every validation JSON includes a `provenance` block with the SHA-256 of the
strategy modules + config. If Cowork sees a result whose `provenance.config_hash`
does NOT match the current `config.py` hash, that result was produced under
a prior frozen spec and is no longer claimable under the current register.

Current `config_hash`: see `config.py` `provenance()` call output, or compute:
```
python -c "from aig.provenance import provenance; print(provenance()['config_hash'])"
```

As of 2026-05-21: `daafa5c1b0b18de7` (bound to `n_trials_registered=6`
amendment).
