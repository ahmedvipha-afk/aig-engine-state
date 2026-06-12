<!-- PROVENANCE RECOVERY HEADER (added 2026-06-12, decision_log entry 47)
This document was delivered by Ahmed as a TYPED CHAT MESSAGE on
2026-05-22T15:54:21Z (session transcript 57451b12-030b-4860-84e8-8e4538f1f0b4,
line 570, project C--Users-ahmed) and was referenced by commit 33d93ae and the
framework files as ahmed_response_2026-05-22.md WITHOUT ever being saved to
disk. Recovered VERBATIM from the transcript on 2026-06-12 during the Session
A2 provenance adjudication. Operator note: when the Amendment 1 provision was
surfaced on 2026-06-12, the operator did not recall it; authenticity was
established by transcript evidence, not memory (entry 47). Amendment 1 is
SUPERSEDED as a dead letter per entry 47 — see strategy_register.md.
Body below this line is byte-for-byte the 2026-05-22 message.
-->
# ahmed_response_2026-05-22.md — Directives for CC

**From:** Ahmed
**To:** CEO (Claude Code)
**Date:** 2026-05-22
**In response to:** Cowork audit findings (Session 5) + amendment proposal review + strategy-selection methodology discussion
**Read this alongside:** `auditor_report.md` (Session 5 audit), `ceo_brain.md`, `strategy_register.md`
**Status of this file:** Direction to CEO. Items below are to be implemented in pre-registered order. CEO does NOT improvise on top of these — execute as written. Any deviation requires logging in Decision Log with justification before execution.

---

## Framework finality — read this first

This document is the **complete and final framework for Phase 1 amendments.** Once committed to the repo and pushed under its config hash, no further amendments, gate adjustments, methodology revisions, or constraint reframings are to be considered or proposed until **at least 6 months of forward data have accumulated** under this framework — meaning ≥ 6 calendar months of paper-forward execution and re-validation evidence under the amended gate, measured from the commit date of this directive.

This finality is binding by design. It is the disciplinary mechanism that prevents amendment-chasing if Phase 1 results disappoint. If strategies fail under this framework, the response is to accept the verdict, not to amend the framework again. If strategies clear, the response is to deploy under the framework as written. Either way, the framework itself is frozen for 6 months.

**What this finality covers (no changes for 6 months):**
- The six gate amendments in Part 1
- The six watch-list improvements in Part 2
- The re-validation discipline in Part 3
- The three-filter selection methodology in Part 4
- The Phase 1 strategy cap in Part 4
- The Mode 1/Mode 2 framing in Part 5
- The streaming-signals rule in Part 6
- The decision-log infrastructure requirement in Part 7

**What this finality does NOT cover (these remain mutable):**
- Bug fixes in implementation (e.g., a divergence calculation has an off-by-one bug — fix it, log it, continue)
- New strategies entering the test queue via the methodology in Part 4 (the methodology stays frozen; what it outputs is dynamic, up to the Phase 1 cap)
- New tickers added to existing universes via the pre-registered inclusion criteria
- Display, dashboard, and reporting improvements that do not alter gate behavior
- Routine operational maintenance (data refresh, cache rotation, log rotation)

**Process if Ahmed or the CEO believes the framework is wrong before 6 months elapse:**
The belief is recorded in the decision log with full reasoning, dated, but no action is taken on it until the 6-month forward window closes. At that point, accumulated forward evidence is reviewed alongside the recorded concern, and a Phase 2 amendment cycle may begin — under the same pre-registration discipline applied here.

This is the rule that prevents the framework from quietly becoming whatever the most recent disappointing result suggests it should be. Hold it.

---

## Part 1 — Gate amendments (pre-register before applying)

Six amendments to the validation gate. All must be frozen in `config.py`, hashed, and added to `strategy_register.md` Trial Budget BEFORE any re-evaluation runs. The amendments apply prospectively to all future tests AND to a forward re-validation pass on existing strategies (see Part 3). They do NOT retroactively change Session 5 verdicts on the original test data.

### Amendment 1 — Win-rate floor by strategy archetype (CONDITIONAL)

**Rule:**
- Mean-reversion / pullback strategies: WR floor stays at 0.40 (unchanged).
- Trend-following / breakout / momentum strategies: WR floor removed IF AND ONLY IF all of the following hold:
  - dSharpe ≥ 1.5 (three times the standard floor)
  - Profit factor ≥ 2.0
  - Bootstrap CI lower bound on mean trade return > 0
  - Fully systematic auto-execution infrastructure exists (defined below).

**Binding constraint — auto-execution requirement:**
A strategy that uses the relaxed WR floor cannot be deployed under the current "Telegram → Ahmed taps approve" workflow. That workflow is human-in-the-loop, which is exactly what the binding constraint forbids — humans don't reliably execute strategies with 4-of-5 losing trades, and once execution deviates, the certified expectancy no longer applies.

**Status until auto-execution exists:** Amendment 1 is PRE-REGISTERED but DORMANT. Cannot activate until:
1. An auto-execution layer is built (orders fire to broker API without human approval per signal), AND
2. That layer passes its own validation (idempotency, slippage modeling, fail-safe halt).

Until both conditions hold, the WR floor stays at 0.40 for all strategies regardless of archetype. CEO does not deploy a low-WR strategy via the current Telegram workflow.

**Add to strategy_register.md:** an `archetype` field on every strategy: one of `mean_reversion`, `pullback`, `trend_following`, `breakout`, `momentum`, `volatility_cycle`, `statistical_arb`, `event_driven`. Frozen at registration.

### Amendment 2 — Trade-count floor by universe size

**Rule:**
- US (universe ≥ 500 tickers): min OOS trades = 1,000 (unchanged)
- UAE (universe < 100 tickers): min OOS trades = 200
- Crypto (universe < 200 tickers): min OOS trades = 400
- Any future market: pre-register the floor at universe-onboarding time, before any test runs.

**Formula NOT to use:** the originally proposed `max(100, sqrt(universe × years × signal_frequency_estimate))` — `signal_frequency_estimate` is a free parameter and creates a tuning backdoor. Use the fixed per-market table above. Add new entries only when a new market is onboarded, and freeze the entry before testing on that market.

**Binding constraints that REMAIN STRICT regardless of universe (do not relax these):**
- Bootstrap CI lower bound on mean trade return strictly > 0
- dSharpe ≥ 0.5 after N-trial multi-test haircut
- OOS performance > IS performance (the lower-noise version: OOS Sharpe ≥ 0.7 × IS Sharpe at minimum)
- OOS time span ≥ 24 months (see Amendment 6)

### Amendment 3 — Profit factor floor

**Rule:** Every cleared strategy must have OOS Profit Factor ≥ 1.5.

**Constraint:** PF only counted on samples with n ≥ 30 trades. Below n=30, PF estimate is too noisy (one outsized winner can produce PF > 3 by accident).

**Add:** bootstrap 95% CI on PF the same way the gate currently bootstraps mean trade return. Lower bound of CI must be ≥ 1.0 (i.e., even at the pessimistic end of the bootstrap distribution, the strategy is at break-even on a profit-factor basis).

### Amendment 4 — Multi-timeframe testing as separate pre-registered trials

**Rule:** A cleared strategy may be re-tested on a different timeframe (e.g., Divergence Daily → Divergence 4H → Divergence Weekly). Each timeframe is a NEW TRIAL added to the Trial Budget in `strategy_register.md`. The multi-test haircut updates: N=6 today → N=9 if three timeframes per strategy are added across two strategies.

**Constraint:** This amendment TIGHTENS the gate, not loosens it. A timeframe variant must clear the gate under the new (larger) N. CEO does NOT present timeframe-multiplication as "more chances to find edge" — it is robustness validation.

**Pre-registration:** Before testing a new timeframe, append a row to the Trial Budget table with planned timeframe, market, expected trade frequency estimate, and the new N_trials value. Hash config. Then run.

### Amendment 5 — GCC universe as a discovery-and-validation tool, NOT a deployment market

**Critical clarification from Ahmed:** Trading scope is UAE only. GCC markets (Saudi Tadawul, Kuwait, Qatar, Bahrain) are NOT deployment markets and signals will NOT be sent to Telegram for GCC tickers.

**The honest use of GCC data:**
1. Aggregate the full GCC halal universe (target ~400–500 tickers when data permits).
2. Test candidate strategies on the FULL GCC universe to get the statistical power UAE alone cannot provide.
3. For any strategy that clears the GCC-wide gate: run a separate UAE-only certification step on UAE tickers only.
4. Strategy clears GCC AND UAE-only certification → deploy on UAE.
5. Strategy clears GCC but FAILS UAE-only → mark as `GCC_only_edge_not_UAE_deployable` in strategy_register. Shelf. Do not deploy.

**Pre-register:** the UAE-only certification step is a hard gate, same status as Shariah. It uses the per-market trade-count floor from Amendment 2 (UAE: 200) and all standard statistical gates.

**Add to strategy_register.md:** a `deployment_market` field separate from `discovery_universe`. For UAE strategies: `discovery_universe = GCC_halal`, `deployment_market = UAE`. Make this distinction explicit and tracked.

### Amendment 6 — OOS time-span floor

**Rule:** Every cleared strategy must have OOS trades distributed across ≥ 24 months of calendar time, in addition to the trade-count floor.

**Why:** A strategy with 1,200 trades concentrated in the last 18 months of OOS data is statistically dense but temporally narrow — could be a regime artifact. The 24-month minimum forces the OOS sample to span enough calendar time to cross at least one regime boundary.

**Constraint:** This applies on top of trade-count floors. A strategy needs both ≥ N trades AND ≥ 24 months OOS span to be evaluable. Strategies failing on time span only (sufficient trades, insufficient span) get verdict `INSUFFICIENT_OOS_SPAN` rather than `CLEARED`.

---

## Part 2 — Six watch-list and ticker-handling improvements

To be implemented BEFORE the next paper-forward signal fires.

### Improvement 1 — Replace top-N-by-expectancy watch list

**Action:** Drop the current top-5-by-expectancy watch list (DY, EXPGY, PSX, ARW, ROL). Replace with one of these two pre-registered selection methods (CEO picks one and freezes it; do not switch later):

**Option A (preferred):** Deploy detector across the ENTIRE cleared US Divergence universe (~1,027 contributing tickers). Telegram fires when ANY ticker in the cleared universe meets the strategy's forward entry criteria.

**Option B:** If Option A is too noisy, deploy on a randomly selected stratified sample of the cleared universe — stratify by sector (US GICS sectors) and average daily dollar volume tier. Pre-register the random seed and the stratification before sampling. Cannot re-sample later.

**Do NOT:** continue using the top-N-by-expectancy method. It is the cherry-picking failure mode flagged in the audit and it reconstructs a concentrated bet on noise inside a wrapper that says "the portfolio cleared."

### Improvement 2 — Sector and liquidity diversification in the watch list

**Action:** Whichever selection method (A or B) is used in Improvement 1, the resulting watch list must satisfy:
- No more than 30% of tickers in any one GICS sector
- No more than 50% of tickers in the top liquidity quintile (because mega-caps are over-represented and most-efficient)
- Minimum 20% of tickers in liquidity quintiles 2–4 (real names with real volume but not the most-followed)

**Pre-register:** these constraints in strategy_register.md before generating the watch list.

### Improvement 3 — Regime filter on signal firing

**Pre-register and add to strategy specification:**

A Divergence signal only fires on a ticker when ALL of the following hold at the time of the signal bar:
- VIX < 25 at last close
- Ticker is above its own 200-day moving average at last close

Tag the strategy spec with this filter. Freeze before deployment. Re-validate the cleared US Divergence portfolio under this added filter — the multi-test haircut updates because this is effectively a new trial. Run the portfolio gate again; verdict must still be CLEARED under the new haircut for the filtered version to deploy.

If the filtered version fails the gate (insufficient remaining trades, lower dSharpe), revert to the unfiltered version. Do not deploy the filtered version on the same evidence that cleared the unfiltered one.

### Improvement 4 — Confluence signal tagging

**Action:** When a Divergence signal fires on a ticker, ALSO compute whether the ticker has a bullish EMA-200 trend setup on the same bar (close > EMA-200, EMA-200 sloping up over last 50 bars).

If yes → tag the Telegram alert as `★★★ CONFLUENCE (Divergence + EMA-200 trend)`.
If no → tag as `★★ Divergence only`.

**Do NOT:** size confluence signals differently from non-confluence signals based on the tag alone. Sizing stays per the frozen strategy spec. The tag is informational. Differential sizing would require a separately validated confluence strategy with its own gate clearance.

### Improvement 5 — Hard minimum n for per-ticker stats display

**Action in dashboard.html and any per-ticker leaderboard:**

No ticker is shown in WINNERS or LOSERS tables, or in any per-ticker statistic display, unless its OOS n ≥ 30 trades. Below n=30, the ticker is excluded from per-ticker views entirely. The portfolio-level result remains the binding verdict.

Specifically: this fixes the DXCM-∞-expectancy display issue and the ZWS/PEP outlier display by removing them from view, not by formatting them better. They have n < 30; they are not winners; they should not appear as such.

### Improvement 6 — Auto-demote tickers on forward decay

**Action (Phase B / autonomous maintenance loop):**

For every ticker in the deployed watch list, after the paper-forward detector has accumulated ≥ 20 closed forward trades on that ticker:
- Compute the forward expectancy.
- Compare to the OOS expectancy that contributed to the cleared portfolio result.
- If forward expectancy < 0.7 × OOS expectancy → AUTO-DEMOTE the ticker from the watch list. Log to decision log with reason and the two expectancy numbers.
- If forward expectancy ≥ 0.7 × OOS expectancy → leave on watch list.

**Safe to automate because:** this only ever REMOVES exposure. CEO autonomy boundary respected.

---

## Part 3 — Re-validation discipline (the discipline that protects everything else)

**Critical:** All six amendments above APPLY PROSPECTIVELY. They do NOT automatically reopen Session 5 verdicts.

Specifically:
- US Divergence remains CLEARED on the original Session 5 evidence. Paper-forward deployment continues.
- UAE FAIL and Crypto FAIL verdicts remain on the original evidence.
- EMA-200 FAILs remain on the original evidence.

**To re-evaluate any prior verdict under the amended gate:**

1. The strategy must be re-run on data the strategy has NOT previously been evaluated against. Two acceptable methods:
   - **Method A — fresh OOS window:** cut a new OOS window from a different time period than the original test used. Original Session 5 tests used post-60% train cut. New window: pre-2018 data (if available) as a separate OOS sample, OR a different rolling-window cut documented in the Trial Budget.
   - **Method B — forward data accumulation:** wait until 6+ months of new bars have accumulated post-Session 5 (~Nov 2026). Re-run with that genuinely-unseen data appended.
2. Anything that clears under the new gate on Method A or Method B data is a real clear under the new framework.
3. Anything that only clears on re-running the original Session 5 OOS data is suspect and gets tagged `RECLEARED_ON_SAME_DATA_FLAG` in strategy_register. CEO does not deploy these without auditor review.

**Do NOT:** apply the amended gate to the original Session 5 test data and report "additional strategies cleared." That is the textbook data-mining-via-amendment pattern.

---

## Part 4 — Methodology for selecting which strategies to test next

To replace ad-hoc "what should we try" with a frozen, executable methodology. CEO can run this methodology autonomously without asking Ahmed each time — but does not deviate from the methodology itself without Ahmed approval.

### Autonomy scope distinction

**Version A — autonomous execution of a pre-decided selection methodology.** CEO runs the frozen filters below and pre-registers the candidate it outputs. The method is fixed in writing; the CEO just executes it. **This is the version adopted here.** Automation of a decision rule, not delegation of judgment.

**Version B — autonomous judgment about what strategies to look for.** CEO scans literature, reads patterns in past results, decides "this looks promising," pursues it. **This is explicitly NOT adopted.** Produces convincing-looking strategy choices shaped by whatever the CEO recently "noticed," which is not a defensible methodology.

### The three-criteria selection methodology (frozen, pre-registered)

Rank every candidate strategy on three filters, in order of priority:

**Filter 1 — Archetype diversity from cleared strategies.**

Currently cleared: Divergence (archetype: `pullback` / mean-reversion).

Next candidate MUST be from a different archetype. In priority order:
1. `trend_following` (e.g., MBV, channel breakout, Donchian)
2. `breakout` (volatility expansion, range breakout)
3. `momentum` (factor-based, relative strength)
4. `volatility_cycle` (RV-based, IV-RV spread)
5. `statistical_arb` (pair trades — note: long-only constraint limits options here)

Testing a second `pullback` strategy is disallowed until at least one strategy from another archetype has cleared, OR has failed the gate honestly. Rationale: archetype diversification is a hard portfolio-construction principle, not optional polish.

**Filter 2 — Evidence tier of prior support.**

Tag every candidate with one of:
- **T1 (highest priority):** peer-reviewed academic evidence across multiple markets and decades. Examples: trend-following (Moskowitz, Ooi, Pedersen 2012), momentum (Jegadeesh & Titman 1993, replicated extensively), value-tilted breakout.
- **T2:** practitioner consensus / multiple independent published backtests with consistent direction. Includes well-documented Pine strategies with multi-year live track records.
- **T3:** single-source claim, blog backtest, single Pine script with no independent validation.

Test T1 candidates BEFORE T2, T2 BEFORE T3. Do not test T3 candidates until T1 and T2 queues are exhausted for the relevant archetype.

**Filter 3 — Data and infrastructure readiness.**

Disqualify (move to deferred queue, not test queue):
- Strategies requiring intraday tick data if only daily/1H data is available
- Strategies requiring short-selling (long-only mandate)
- Strategies requiring options data, futures data, or fundamental data feeds not yet wired
- Strategies requiring leverage (Rule 16)
- Strategies that violate Shariah on instrument level (interest-bearing instruments, derivatives that fail screen)

A strategy moves from deferred → testable only when the required infrastructure is built and validated separately.

### Source priority for candidate strategies

In honest order of value:

1. **López de Prado / Advances in Financial Machine Learning literature** — explicit list of strategy archetypes with peer-reviewed evidence, methodology for testing them, and (critically) explicit warnings about how each one is usually overfit. Highest-quality starting list available publicly. Pick from this taxonomy first.

2. **Replication of published academic results before testing variants.** Before building "EMA-200 with my volume tweak," replicate the original EMA-200 result on the original universe and confirm the claimed Sharpe reproduces. If you can't reproduce the published result, the original was already overfit and any variant inherits that. This is unglamorous and most people skip it. Don't skip it.

3. **Ahmed's own Tareq research as a constrained source.** Years of work on the Tareq strategy family is a legitimate strategy-discovery source — but apply the same gate to it as to anything else. "I designed this" does not lower the bar. Prior Tareq backtests and signal logs are NOT evidence of edge — they were produced before pre-registration discipline. Tareq rules get frozen, then tested through the amended gate on data the strategy has not been evaluated against.

**What this methodology explicitly DOES NOT do:**

- Scan Pine forum top-returns lists to seed candidates
- Optimize strategy parameters across the universe to find what fits
- Iterate on failed strategies to "find what would have worked"
- Let the CEO scan past results to spot "patterns" and seed new candidates from them
- Take Ahmed's intuitions or hot tips as inputs (with one exception, below)

**The one Ahmed-input exception:** Ahmed may explicitly request a specific strategy be tested (e.g., a Tareq variant). When this happens, the strategy enters the queue but receives the standard tier classification and is tested in order. It does not jump the queue, and it gets the same gate treatment as anything else.

### Data reuse policy

Previously collected data (UAE ticker lists, ADIB halal list, TV-MCP CSV caches, OpenBB pulls) is reusable as a **data source** for new tests.

Previously collected **strategy results** (Tareq backtests, alsahmo.com 241% figure, prior Pine Strategy Tester outputs) are NOT reusable as evidence of edge. They were produced before pre-registration discipline and do not count toward gate clearance.

**Data: yes. Verdicts: no.**

### Phase 1 strategy cap

Phase 1 tests a maximum of **4 candidate strategies total**, including Divergence (already cleared). With Divergence counted, that leaves **3 additional candidates** to be tested through the methodology in this Part.

After 4 candidates have completed (cleared or failed), Phase 1 testing closes. No new candidates enter the test queue until the 6-month framework freeze elapses and a Phase 2 review is opened.

This cap is not a target. It is a ceiling. If the methodology produces only 2 viable candidates given Filter 1 (archetype diversity), Filter 2 (evidence tier T1/T2), and Filter 3 (infrastructure readiness), Phase 1 closes at 3 total. The cap prevents "keep testing until something clears" from quietly becoming the methodology in practice.

**What "closes" means:**
- The selection methodology stops running until Phase 2.
- The decision log records "Phase 1 candidate slots exhausted on [date]."
- Paper-forward deployment of any cleared Phase 1 strategy continues.
- The autonomous maintenance loop continues operating.
- Re-validation of failed strategies under Method A or Method B can still occur AFTER the 6-month freeze, in Phase 2.

If at Phase 2 review the accumulated forward evidence and the framework's protective effect are both holding, Phase 2 may open additional slots under a Phase 2 directive. That decision is for then, not now.

### The methodology in action

Given the current state:
- Cleared: Divergence Daily (pullback) — counts as Phase 1 candidate #1
- Need: a different archetype, T1 evidence, infrastructure-ready
- Phase 1 slots remaining: 3

Likely next 3 candidates the methodology selects:
1. **Trend-following daily** (T1 evidence: Moskowitz/Ooi/Pedersen TS-momentum). Compatible with daily bars, long-only, no leverage, halal-universe-compatible. **Recommended next test.**
2. **Cross-sectional momentum** (T1 evidence: Jegadeesh & Titman). Compatible with daily bars, long-only top-decile, no leverage needed.
3. **Volatility breakout / Donchian channel** (T1-T2 evidence: Bollinger band-based variants, Donchian's original work). Compatible with current infrastructure.

These are not selected because they look promising — they are selected because the methodology selects them mechanically given the inputs. That is the entire point.

### Autonomous execution scope

CEO can autonomously, without asking Ahmed:
- Run the three-filter methodology on the current state and produce the next-candidate list
- Pre-register the next candidate's full specification before testing
- Run the test through the (amended) gate
- Log results, clear or fail
- Move to the next candidate when current one completes (until Phase 1 cap is reached)

CEO must ask Ahmed (one-tap approve via Telegram) before:
- Modifying any filter in the methodology
- Skipping queue order
- Adding a new archetype not in the original list
- Adding a strategy that triggers the deferred queue (requires infrastructure build)
- Exceeding the Phase 1 cap of 4 candidates

---

## Part 5 — Mode 1 / Mode 2 clarification

**From Ahmed:** Mode 1 sprint continues until all eight tracker items are complete. Items 5 (next candidate via methodology) and 6 (paper-forward results match backtest) are the remaining two.

**Honest CEO acknowledgment required:**
- Item 6 cannot be sprint-accelerated. It requires time for paper-forward signals to fire and trades to close. The sprint routine should reflect this: idle on Item 6 while accumulating live evidence, sprint on items that can be done now.
- Item 5 is gated on Part 4 methodology output. If the methodology says trend-following is next, that may or may not be MBV specifically. CEO does not force MBV — runs the methodology and accepts the output.

**Mode 1 → Mode 2 transition** occurs ONLY when all eight items are genuinely DONE, not when item 6 is "running" or "pending." Mode 2 begins with the 6-month forward window from Phase 1 framework finality.

**Return targets (3x / 10x):** these are NOT Mode 1 exit conditions. They are aspirational reporting only. Sprint does not target return numbers. Confirm in the dashboard: relabel KPI scorecard "Annual Return" target column as "Aspirational — not gate" or remove the row entirely until measurable.

---

## Part 6 — Streaming Telegram signals from cleared strategies

**From Ahmed:** Send signals to Telegram as they fire on cleared strategies. Do not wait for all markets to clear before signals flow.

**CEO implementation:**
- US Divergence has cleared its gate. Telegram signals fire as the detector hits forward entry conditions. Already the design — continue.
- UAE and crypto have not cleared. NO Telegram signals fire on those markets until they pass an honest gate (under the amended thresholds + re-validation per Part 3).
- Watch list selection: per Improvement 1, signals fire from the full cleared universe or a stratified sample — NOT from the top-N-by-expectancy.

---

## Part 7 — Decision Log infrastructure

**From audit Finding NEW-3:** Decision Log is currently empty despite Session 5 making multiple decisions.

**Required action this session:**
1. Implement or fix the decision-log writer if it's broken.
2. Backfill Session 5's major decisions from commit messages and ceo_brain:
   - Withdrew Path 3 (date, commit, rationale: avoid post-hoc threshold loosening)
   - Deployed US Divergence paper-forward (date, commit, rationale)
   - Selected top-5 watch list (date, rationale — and now mark this as SUPERSEDED by Part 2 Improvement 1)
   - Expanded UAE universe (date, rationale)
   - Accepted no-edge-crypto verdict (date, rationale)
3. Every new decision going forward gets logged with: timestamp, decision, rationale, alternatives considered, and audit-finding-reference if applicable.

---

## Part 8 — Order of operations for next CC session

Execute in this order. Do not reorder:

1. **First — Decision Log backfill** (Part 7). Cannot make new decisions without recording them.
2. **Second — Apply Improvement 5** (hide n<30 tickers from displays). Quick fix, removes misleading visuals immediately.
3. **Third — Apply Improvement 1 + 2** (replace cherry-picked watch list with full universe or stratified sample). This resolves audit BLOCKING NEW-1.
4. **Fourth — Pre-register all six gate amendments** (Part 1). Write to config.py, freeze, hash, update strategy_register.md Trial Budget.
5. **Fifth — Pre-register the three-filter selection methodology AND the Phase 1 strategy cap** (Part 4). Add to strategy_register.md.
6. **Sixth — Apply Improvement 3 + 4** (regime filter, confluence tagging). Re-validate filtered Divergence as a new trial.
7. **Seventh — Run methodology, output next candidate** (Part 4). Pre-register fully before testing. This is Phase 1 candidate #2.
8. **Eighth — Test next candidate** through the amended gate.
9. **Ninth — Update dashboard:** KPI scorecard fix (Part 5), Telegram log fix (audit NEW-5), display drift sweep. Add Phase 1 candidate counter (X of 4 used).
10. **Tenth — Push to repo.** Auditor will read and respond.

---

## Closing constraints (do not relax)

- Pre-registration discipline: any rule change rehashes config. Verdicts under old hash are not claimable.
- Audit findings are binding by directive — BLOCKING items must be addressed before unblocking next phase.
- Statistical gates remain non-negotiable: deflated Sharpe haircut, bootstrap CI, OOS > IS, walk-forward, pre-registration, realistic costs, no post-hoc amendment, no same-strategy iteration ban.
- Long-only, no-leverage, Shariah-compliant, paper-only — permanent constraints from project foundation.
- Auto-execution layer does not exist yet. Amendment 1 (low-WR strategies) stays dormant until it does.
- No retroactive gate amendments applied to Session 5 results. All re-evaluations on Method A (fresh OOS window) or Method B (forward data) only.
- Framework finality holds for 6 months from commit date. Concerns logged but not acted on during that window.
- Phase 1 cap of 4 candidates is hard. CEO cannot exceed without explicit Ahmed approval.

— End of directive —