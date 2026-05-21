# ceo_brain.md — Persistent CEO State

_Per v7.0 §2.5 — read FIRST at start of every session. Updated end-of-session._

---

## OPERATING MODE: **MODE 1 — FULL SPRINT**

**Sprint 1 started 2026-05-21.** Cloud Routine `aig-mode1-sprint` fires every
2 hours from 06:13–22:13 GST + 00:13 GST, 7 days/week. Each fire:
1. Reads `ceo_brain.md` (this file) + `auditor_report.md`.
2. Identifies the lowest-numbered unfinished item in the SPRINT TRACKER below.
3. Advances that item by one concrete step (whatever fits in 5–20 min).
4. Updates the tracker with progress + new state.
5. Commits + pushes.

**Mode switch trigger:** all 8 items → ✅ DONE.

When all 8 are complete, the sprint routine retires itself, the Mode-2
operational routines (`aig-morning-scan`, `aig-weekly-full-universe`,
`aig-monthly-report`) are re-enabled, and signal-flow to Ahmed begins.

---

## SPRINT TRACKER (Mode 1)

| # | Item | Status | Concrete completion criteria | Notes |
|---|------|--------|------------------------------|-------|
| 1 | Audit BLOCKING items resolved | ✅ **DONE** | All 3 (Concerns 1, 2, 5) fixed and committed; dSharpe 2.606 re-confirmed under N=6 haircut. | See AUDIT RESPONSE section below |
| 2 | Deploy US Divergence paper-forward with alerts | ✅ **DONE** | (a) Pine v6 source committed `pine/aig_divergence_v1.pine`; (b/c/d) TV-slot DEFERRED per routine — Python detector route; (e) Telegram DEPLOYED_PAPER_FWD confirmation sent 2026-05-21 (msg 13) | Detector: `scripts/paper_forward_divergence.py` · state: `paper_forward_positions.json` (deployed_at 2026-05-21T02:41:52+04). Fires every 2h via aig-mode1-sprint. TV slot can be added cosmetically later if DOM friction resolves; not blocking. |
| 3 | Wire UAE data via TV MCP + validate ≥60 tickers | 🔄 **IN PROGRESS** | 60+ UAE tickers retrievable AND validated (gate-evaluated, regardless of pass/fail) | Current: 50 retrievable (25 ADX cached + 4 DFM cached + 21 .AE/.AB yf). Need +10 more. Last advance 65e4910 added METHAQ/TKFL/AJMANBANK/ORIENTTKAFUL/TAKAFUL_EM/UNIONCOOP. Validation re-run launched after that commit. Next: probe more ADX/DFM via TV MCP (when TV Desktop CDP available). |
| 4 | Crypto: ≥100 coverage validated | ⏳ PENDING | 100+ crypto tickers gate-evaluated; portfolio result captured | 140 valid in last run; gate did not clear — needs strategy iteration or further integrity work |
| 5 | Add MBV as 3rd strategy + validate across 3 markets | ⏳ PENDING | `aig/strategy_mbv.py` written, frozen in config, registered in Trial Budget (+3 trials → n_trials_registered=9), run on US+UAE+Crypto | v7.0 §19 spec; will rebalance multi-test haircut |
| 6 | Paper-forward results match backtest expectations | ⏳ PENDING | After ≥10 paper-forward signals fire, compare actual vs backtest expectancy with tolerance ±20% | Activated by Item 2 deployment |
| 7 | All coverage targets met | ⏳ PENDING | US ≥100 ✅ (1027) · UAE ≥60 (currently 50) · Crypto ≥100 ✅ (140) — only UAE remaining | UAE coverage gate depends on Item 3 |
| 8 | All strategies verified with gate clearance per market | ⏳ PENDING | At least one strategy clears `PORTFOLIO_GATE` per market (US ✅, UAE pending, Crypto pending) | UAE/Crypto need either strategy iteration or accept FAIL verdict honestly |

**Currently working:** Item 3 (UAE 60+ retrievable). Items 1–2 done. Items 4–8 queued.

---

## CURRENT STATE (as of 2026-05-21, post-audit response)

**Phase:** Pre-deployment cleanup of auditor BLOCKING findings before
Path 1 (ship US Divergence Daily). Engine and pre-registration framework
reconciled. Re-run with corrected haircut in flight.

**Config hash:** `daafa5c1b0b18de7` (bound to amended `PORTFOLIO_GATE`
with `n_trials_registered=6`).

**Active strategies + trial budget:** see `strategy_register.md`. Six trials
binding the multi-test haircut. Adding any trial requires appending to that
table BEFORE running.

**Universes:**
- `universe/us_halal_full.txt` — 1,603 unique tickers (Ahmed authoritative).
- `universe/uae_tickers_full.txt` — 50 retrievable (29 TV-MCP cache + 21 yfinance .AE/.AB hybrid). Sprint Item 3 target ≥60.
- `universe/halal_crypto_150_USD.txt` — 150 tickers (Ahmed authoritative).

---

## AUDIT RESPONSE — Session 5 (2026-05-21)

External audit by Cowork (read-only, advisory) on Session 4 close.
Six findings: three BLOCKING, two WARNING, one NOTE.

### Concern 1 (BLOCKING) — multi-test haircut undercounted. RESOLVED.

The portfolio gate was deflating Sharpe over `n_strategies_registered=2`.
The auditor correctly noted the haircut must cover the **full trial set**
the CEO chose between — 2 strategies × 3 markets × 1 timeframe = **6 trials**.

Action taken:
1. Renamed `n_strategies_registered` → `n_trials_registered` in
   `PORTFOLIO_GATE`. Value set to 6 reflecting Session 4 run set.
2. Added explicit Trial Budget table in `strategy_register.md`. Adding
   any new trial requires appending to that table BEFORE the run.
3. `aig/validation_gate.portfolio_evaluate` updated to use the new key
   (back-compat alias retained for prior callers).
4. US Divergence 1603 re-run completed (background task `b384nkuu9`,
   result file `validation_divergence_1d_full_haircut6.json`):
   - Raw Sharpe (re-run): 3.0795
   - Haircut (N=6): √(2 ln 6) × 0.25 = 0.474
   - **Deflated Sharpe (corrected): 2.6063 — PASSES the 0.5 threshold by 5.2x margin.**
   - Verdict: PORTFOLIO_CLEARED_FOR_PAPER_FORWARD ✅
   - Trades 10,715 · contributors 1,030/1,124 · coverage 91.64% · exp 1.227 · WR 44.78%
5. Trial budget pre-registration discipline now load-bearing — any
   future trial added MUST update the table and bump `n_trials_registered`
   in the same commit.

### Concern 2 (BLOCKING) — Path 3 amendment rejected. WITHDRAWN.

Proposal to scale `min_trades` by universe size and drop the WR floor was
correctly flagged as **post-hoc threshold adjustment** — exactly the failure
mode pre-registration exists to prevent.

Action taken:
- **Path 3 REJECTED as proposed.** Removed from Decision Point queue below.
- The auditor's two acceptable alternatives logged for future consideration:
  (a) accept small-market FAILs as honest verdict of the framework; or
  (b) design a small-markets framework prospectively, freeze it BEFORE
  seeing new data, validate on next ≥ 6 months of UAE/crypto bars the
  CEO has not yet touched.
- I will pursue (a) for now and consider (b) as a Phase B improvement
  candidate, NOT as a means to retroactively pass Session 4's UAE/crypto
  results.

### Concern 5 (BLOCKING) — strategy register drift. RESOLVED.

`strategy_register.md` had EMA-200 listed with "Timeframe: 1H (also runnable
on 1D for cross-check)" — loose language. Session 4 ran EMA-200 on 1D
without re-pre-registration.

Action taken:
1. EMA-200 spec rewritten as **timeframe-agnostic at the rules level**;
   each (strategy × market × timeframe) is a separate trial entry.
2. Explicit Trial Budget table enumerates all 6 trials.
3. New `config_hash=daafa5c1b0b18de7` binds the corrected register.
4. Old hash `d2c90fd7a64f27ef` (Session 4) results are not claimable
   under the new register — but the re-run currently in flight will
   produce a clean Session-5-hash US Divergence result.

### Concern 3 (WARNING) — overconfident edge claim. ADDRESSED.

The Session 4 brain said "edge confirmed real across all three markets."
Auditor was right that small-sample point estimates aren't process properties.

**Restated claim (replaces the prior phrasing):**
> Statistically significant edge on US Divergence Daily (n=10,729 trades,
> raw Sharpe 3.01, 95% CI on mean trade [+0.0029, +0.0052] — strictly
> positive lower bound). Preliminary positive signal on UAE Divergence
> Daily (n=38, expectancy 1.65, raw Sharpe 1.05) and Crypto Divergence
> Daily (n=644, expectancy 3.54, raw Sharpe 0.52) — sample-undersized
> to certify edge under the same portfolio gate that certified US.

Future reporting will follow this discipline. The brain claim line is
the canonical version; dashboards and Telegram summaries are downstream.

### Concern 4 (WARNING) — WR floor + deployability. ACKNOWLEDGED, NOT ACTED ON.

Auditor argued the 40% WR floor is a deployability constraint, not a
math constraint — low-WR strategies are operationally hard to paper-
forward via human-approval flow because the loss streaks invite deviation.

For the current deployment (US Divergence with WR 44.7%), this does not
bind. Action deferred: if a future low-WR strategy gets a real edge
verdict, I will return to this and either (a) keep the floor as a
hard deployability constraint or (b) accept it with a binding
"systematic-execution-only" amendment to v7.0 §19. Not pursuing today.

### Concern 6 (NOTE) — UAE TV-MCP cache freshness. ACKNOWLEDGED, FUTURE.

Audit-trail risk: a Cloud Routine re-running UAE validation against a
stale cache will log "fresh validation" of stale data. Recommendation
to write sibling `.meta` files with fetch timestamps + integrity-gate
freshness check is sound. Not pursuing today (no UAE re-run scheduled
until next cache refresh anyway), but logged as a Phase B item.

---

## SESSION 4 VALIDATION RUNS (with audit-corrected dSharpe)

| Trial id | Universe | Coverage | Trades | Exp | WR | dSharpe (N=6) | Verdict |
|----------|----------|---------:|-------:|----:|----|--------------:|---------|
| `divergence_us_1d`     | 1,603 | 1030/1124 | 10,715 | 1.23 | 44.8% | **2.61 (confirmed N=6)** | **PORTFOLIO_CLEARED** ✅ |
| `ema200_us_1d`         | 1,603 | 1072  | 5,361  | 1.56 | 18.6% | 1.78 expected | FAIL: WR<40% (and Concern 4 acknowledged) |
| `divergence_uae_1d`    | 44    | 13/31 | 38     | 1.65 | 47.4% | 0.57 expected | FAIL: trades<<1000 |
| `ema200_uae_1d`        | 44    | 25/31 | 40     | 0.29 | 10%   | -3.04 expected | FAIL multi |
| `divergence_crypto_1d` | 150   | 107/140 | 644  | 3.54 | 37.1% | 0.05 expected | FAIL: WR + trades + Sharpe |
| `ema200_crypto_1d`     | 150   | 132/140 | 550  | 0.95 | 18.2% | -0.60 expected | FAIL multi |

**Note:** the dSharpe values above for non-US trials are pre-computed
estimates under N=6; their verdicts remain PORTFOLIO_FAIL and were not
re-run (no claim to revise). US Divergence value is authoritative from the
`b384nkuu9` re-run.

---

## COVERAGE vs TARGETS (unchanged from Session 4 close)

| Universe | Target | Valid retrievable | Portfolio cleared? |
|----------|-------:|------------------:|--------------------|
| US halal | ≥100 | 1,123 (1,027 contributing) | YES (Divergence, pending re-confirm) |
| UAE halal | ≥60 | 31 valid / 44 retrievable | NO — structural per Session 4 finding |
| Crypto halal | ≥100 | 140 valid / 150 retrievable | NO — Sharpe + WR + trade count |

---

## DECISION POINT — post-audit

Three forward paths from Session 4 close, revised per audit:

1. **Deploy US Divergence Daily to paper-forward.** APPROVED, conditional on:
   - Concern 1 resolved (✅ — `n_trials_registered=6` in place; re-run
     in flight to confirm dSharpe ≥ 0.5 under corrected haircut).
   - Concern 5 resolved (✅ — strategy register reconciled,
     `config_hash=daafa5c1b0b18de7`).
   - Concern 3 acknowledged (✅ — edge claim restated above).
   - Paper-forward stays paper-forward. No real-money discussion until
     ≥ 6 months of forward results under the same gate that certified.

2. **Add MBV as third strategy.** DEFERRED per audit recommendation.
   Adding a strategy now widens the R&D queue while no first cleared
   strategy has run a full deployment cycle end-to-end. Ship Path 1
   first; observe one full deployment cycle; then add the next strategy
   with an updated trial budget (would become 9 trials with MBV × 3
   markets).

3. **~~Amend PORTFOLIO_GATE for small markets~~** — **REJECTED.** See
   Concern 2 resolution above. If a small-markets framework is genuinely
   needed, design it prospectively and freeze before seeing data.

---

## CONTEXT RESUME

1. Read this file (you are reading it now).
2. Audit BLOCKING findings all resolved (Session 5). Path 1 unblocked.
3. **Execute Path 1 deployment** per Session 4 plan, now with audit conditions met:
   - Port `aig/strategy_divergence.py` to Pine v6 → fresh slot `AIG_Divergence_V1`
     via the Make-a-copy DOM flow (NEVER touch existing slots — Ahmed's rule).
   - TV Strategy Tester per-ticker on top 5 contributors (DY, EXPGY, PSX,
     ARW, ROL) to cross-check engine portfolio result.
   - Set TV MCP alerts on top 5 contributors: condition = strategy entry
     fires (RSI bullish divergence + close > EMA-200 confirmation bar).
   - Send Telegram daily summary marking Divergence as DEPLOYED_PAPER_FWD.
4. Paper-forward stays paper-forward. No real-money discussion until
   ≥ 6 months of forward results exist under the SAME gate that certified.

---

## INSTRUCTIONS TO FUTURE SELF

1. **Trial budget is binding.** Every new strategy/market/timeframe combo
   appends a row to `strategy_register.md::TRIAL_BUDGET` BEFORE running.
   Bump `n_trials_registered` in the same commit. Otherwise the
   pre-registration claim is notional.
2. **No post-hoc gate amendments.** If a threshold needs to change,
   design it prospectively, validate on data the CEO has not touched.
3. **Per-market CIs are now mandatory in claims.** Restate edge claims
   with bootstrap CIs; never with point estimates alone.
4. **Path 1 first, then Path 2.** Don't widen the R&D queue while
   deployment workflow has never been exercised end-to-end.
5. **WR floor stays as deployability constraint** for current Path 1
   strategy. Low-WR strategy decisions handled if/when they arise.

---

## GITHUB BACKUP REPO (visibility flipped 2026-05-21)

**Repo:** https://github.com/ahmedvipha-afk/aig-engine-state — PUBLIC.

Defense-in-depth secret exclusion via `.gitignore` + `scripts/commit_session.ps1`
safety regex. Pre-flip audit returned zero secret-shaped tracked files.

**Cowork read pattern** (no auth needed):
`https://raw.githubusercontent.com/ahmedvipha-afk/aig-engine-state/main/<path>`

Key endpoints for Cowork ingestion:
- `ceo_brain.md`, `auditor_report.md`, `strategy_register.md`,
  `dashboard.html`, `validation_divergence_1d_full*.json`,
  `reports/kpi_*.xlsx`, `reports/monthly_*.xlsx`.

---

## SESSION 5 ARTIFACTS (in progress)

- `config.py` — `n_trials_registered=6` (was `n_strategies_registered=2`)
- `aig/validation_gate.py` — `n_trials` parameter; back-compat alias
- `strategy_register.md` — Trial Budget table; EMA-200 timeframe-agnostic;
  audit-response footer
- `validation_divergence_1d_full_haircut6.json` — pending background `b384nkuu9`
- `auditor_report.md` — incoming Cowork audit (read-only)

_End of brain dump. When the b384nkuu9 background lands and dSharpe ≥ 0.5
is confirmed, Path 1 deployment proceeds._

---

## DECISION CONTINUITY (sprint log)

- 2026-05-21 09:50 D-001 — Item 2 → ✅ DONE. Python detector route operational (`scripts/paper_forward_divergence.py`, state file persists open_positions + history, Telegram alerts on entry/exit). Deployment confirmation Telegram sent (msg 13). Pine TV-slot remains DEFERRED per routine note. Sprint focus shifts to Item 3 (UAE 60+ retrievable).

