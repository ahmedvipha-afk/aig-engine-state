# Universes

The validation engine reads ticker universes from this folder. One ticker per line. Blank
lines and `#` comments are ignored. Market is auto-classified by `config.market_of(ticker)`.

## Files

- `us_halal_top30.txt` — top-30 US halal large caps (working HLAL proxy, **pending Ahmed's ADIB list**)
- `us_halal_full.txt` — full 1,621-ticker ADIB halal universe **(NOT YET PROVIDED by Ahmed)**
- `uae_tickers.txt` — ~80 UAE Shariah-compliant tickers **(NOT YET PROVIDED by Ahmed)**
- `crypto_halal.txt` — Ahmed's halal crypto list **(NOT YET PROVIDED by Ahmed)**

## Status

The CEO is proceeding with the HLAL proxy for the first 1H scan because the ADIB list has
not yet been placed in the working directory (the brief stated it should be, but the file
is absent). When Ahmed drops the real `.txt` / `.csv` lists into this folder, the engine
will read them automatically — no code change needed. Re-run with `--universe universe/us_halal_full.txt`.

## Conventions

- US tickers: bare symbol (e.g. `NVDA`)
- UAE: suffix `.AD` (ADX) or `.DU`/`.DFM` (DFM)
- Crypto: suffix `-USD` (e.g. `BTC-USD`) — yfinance convention
