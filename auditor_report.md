# auditor_report.md — Independent Audit (Session 4 close)

**Auditor:** Cowork (independent, read-only — no write access to engine, no autonomous action)
**Audit date:** 2026-05-21
**Audits CEO state:** `ceo_brain.md` Session 4 close (2026-05-20 EOD GST)
**Sources reviewed:** `ceo_brain.md`, `strategy_register.md` (via GitHub raw)
**Sources unreachable at audit time:** `dashboard.html` (raw 404 — CDN cache; not material to audit, dashboard is rendering of state already reviewed)
**Binding effect:** This is advisory. The auditor has no authority to block deployment. Findings are listed with severity tags so the CEO and Ahmed can decide how to weight them. Items tagged **BLOCKING** are the auditor's recommended preconditions for paper-forward deployment.

---

## Top-line read

Session 4 produced the first genuinely promising finding in this project's history. **US Divergence Daily cleared the portfolio gate**: 10,729 trades across 1,027 contributing tickers, expectancy 1.22, win rate 44.7%, deflated Sharpe 2.72. If the result holds under audit, it is a real, statistically significant edge signature, and v7.0 §19 mandates paper-forward deployment.

UAE and crypto did not clear. The CEO is correct that those are sample-size constrained rather than absence-of-edge, but the brain overstates how strong the small-market signal actually is (Concern 3).

Discipline broadly held: pre-registration intact, default-FAIL, no overrides, gate-amendment correctly routed for Ahmed's sign-off rather than CEO unilateral action.

Six findings follow. Three are **BLOCKING** for paper-forward; two are **WARNING**; one is **NOTE**.

---

## Quick-scan summary

| # | Finding | Severity | Required action |
|---|---------|---------:|-----------------|
| 1 | Multi-test haircut undercounts trials (2 vs ≥6) | BLOCKING | Recompute dSharpe under corrected N_trials before deployment |
| 2 | Path-3 amendment is post-hoc threshold adjustment | BLOCKING | Reject as proposed; prospective small-market framework only |
| 3 | "Edge across all three markets" claim overconfident | WARNING | Restate with bootstrap CIs; do not claim UAE/crypto edge yet |
| 4 | Removing WR floor crosses math/deployability boundary | WARNING | Keep floor or write binding deployability constraint |
| 5 | Strategy register drift (registered 1H, ran daily) | BLOCKING | Reconcile register vs config before next run |
| 6 | UAE TV-MCP cache pipeline brittle | NOTE | Timestamp cache files; integrity gate enforces freshness |

---

## Detailed findings

### 1. BLOCKING — Multi-testing haircut undercounts trials

The portfolio gate currently deflates Sharpe over N_strategies = 2. But Session 4 ran 2 strategies × 3 markets = **6 portfolio-level claims**. The Bailey & López de Prado haircut must be applied over the full claim set the CEO chose between, not the subset that happened to clear.

Under N_trials = 6:
- Haircut: √(2 ln 6) × 0.25 ≈ **0.34** (vs current 0.21).
- US Divergence dSharpe: 2.72 raw_haircut → recompute under correct haircut → estimated **~2.59**.
- Still passes the 0.5 threshold by a wide margin, so this does not kill the deployment.

The principle is non-negotiable: the gate's correction must reflect every claim that was on the table, including the failing ones. If Path 2 (add MBV) proceeds, that's 9 trials; a 4H variant takes it to 12; and so on. Adding strategies barely hurts the gate (the CEO is right about that part) but the accounting must be correct.

**Required action before paper-forward deployment:**
1. Pre-register an explicit **trial budget**: every (strategy × market × timeframe) combination is one trial.
2. Re-run the deflation calculation on US Divergence under the full trial count.
3. Confirm dSharpe still ≥ 0.5 (likely yes, with margin).
4. Log the trial budget into `strategy_register.md` so future additions are accounted for.

---

### 2. BLOCKING — Path-3 amendment is post-hoc threshold adjustment

The proposal to scale `min_trades` by universe size and remove the WR floor is plausible **on its merits**. It is also exactly the failure mode pre-registration exists to prevent: **changing the gate after seeing which markets failed**, with a coherent-sounding reason attached.

The CEO correctly flagged "Ahmed sign-off required," but the framing should be harder. If the gate was wrong for small markets, it should have been pre-registered as different for small markets **before any test ran**. Doing it now is the textbook way to convert a "no" into a "yes" with rationalisation.

**Required action — reject Path 3 in current form.** Two acceptable alternatives:

(a) **Accept the small-market FAILs** as the honest verdict of the framework as written. Treat the UAE/crypto positive-expectancy signal as motivation for future testing, not as edge evidence today.

(b) **Design a small-markets framework prospectively.** Freeze thresholds before seeing the next test data. Validate it on data the CEO has not yet touched (e.g., the next ≥6 months of UAE/crypto bars). Do not apply it retroactively to Session 4 results.

Do **not** mix the two: do not loosen-now and validate-later. That is just loosening with a delayed conscience.

---

### 3. WARNING — "Edge confirmed real across all three markets" is overconfident

The brain states: *"The divergence pattern shows real positive expectancy in all three markets (US 1.22, UAE 1.65, crypto 3.54)."*

The numbers:
- **UAE:** expectancy 1.65 on **38 trades**. Estimated 95% bootstrap CI on the point estimate is roughly **[0.4, 3.0]** — the lower bound is below 1.0, meaning the data does **not** rule out "no edge" in UAE.
- **Crypto:** expectancy 3.54 on 644 trades. Firmer than UAE, but raw Sharpe is near the noise floor (deflated 0.23).
- **US:** statistically sound — point estimate 1.22 with n=10,729 has a tight CI well above 1.0.

The CEO is conflating point estimates with strategy properties. Small-sample point estimates are properties of the *sample*, not of the underlying process.

**Required action:** Restate the brain claim as:
> *"Statistically significant edge on US Divergence (n=10,729). Preliminary positive signal on UAE and crypto, but sample-undersized to certify edge in either."*

Add bootstrap CIs to every per-market portfolio result in the validation JSONs. The "edge across three markets" framing should not appear in any reporting until UAE and crypto cross statistical significance under the same gate that certified US.

---

### 4. WARNING — Removing the win-rate floor crosses a math/deployability boundary

The CEO notes US EMA-200 1d fails only on WR (18.6%) and proposes removing the WR floor on the grounds that "different archetypes have different natural WRs." The first half of that reasoning is correct — trend-following strategies do have structurally low WRs.

The second half is incomplete. The WR floor is not (or should not be) there to filter strategy archetype. It is there because **very low WR strategies are operationally undeployable in practice**. An 18.6% WR strategy means roughly 4 of every 5 trades lose. Even with positive expectancy, that is structurally hard to paper-forward without human deviation — and once deviation enters, the certified expectancy no longer applies.

**Two acceptable resolutions:**

(a) **Keep the WR floor** as a deployability constraint, not a math constraint. Strategies that fail it are R&D-shelf only.

(b) **Remove the WR floor** but add an explicit binding constraint that any strategy below 40% WR can only be deployed under **fully systematic execution** (no human override of individual signals). Write this into v7.0 §19. Then a low-WR strategy is deployable but only inside a closed-loop execution wrapper — not via Telegram-and-manual-approval.

Do not silently remove the floor and assume operational deployability stays the same. It doesn't.

---

### 5. BLOCKING — Strategy register drift (provenance integrity)

`strategy_register.md` pre-registers EMA-200 for **1H** timeframe with "Universe: US halal top-30 (then full US halal, then UAE, then crypto)" as the planned scope. Session 4 ran EMA-200 on **daily** across the full universe.

Either:
- The strategy register is stale and needs updating, **or**
- The actual config diverged from the registered spec without re-pre-registration.

Either way, this is a provenance issue. The whole binding-contract premise depends on the register and the config staying tied. If they drift, the "pre-registered" claim becomes notional.

**Required action before next validation run:**
1. Reconcile `strategy_register.md` with the current `config.py` for both strategies.
2. If daily-timeframe EMA-200 is a genuinely new variant, give it a new strategy_id (e.g., `ema200_1d`) and pre-register it as a separate frozen spec.
3. Update the provenance hash to bind the corrected register.
4. Note in the audit trail that prior results produced under the drifted spec are no longer claimable under the corrected register.

This is the single integrity issue most worth fixing, because once the binding contract is loose, every subsequent verdict has an asterisk.

---

### 6. NOTE — UAE TV-MCP cache pipeline is brittle

The TV-MCP → CSV cache pattern is clever engineering and necessary given yfinance's gaps on UAE exchanges. But it makes UAE results depend on a manual upstream step. If a Cloud Routine re-runs UAE validation against a stale cache, the audit trail will show "fresh validation" of stale data.

**Recommended action (not blocking, but tighten before next UAE run):**
1. Every CSV in `data_cache/` writes its UTC fetch timestamp to a sibling `.meta` file.
2. The integrity gate reads the `.meta` and **rejects** any cache file older than N days (suggest 7 for daily data) unless a `--allow-stale` flag is set and the staleness is logged.
3. Cloud Routine prompt includes a freshness check: if any required cache is stale, refresh-first or skip the universe.

---

## What the CEO did well (named explicitly so this audit is not all critique)

1. **Held the line on the v7.0 §19 Sharpe>1.5 graduation criterion** for EMA-200 1H despite real edge on top US names. That is the exact discipline this project depends on; deploying anyway would have been the failure mode.

2. **The portfolio-level gate is conceptually the right answer** to the N_tickers haircut problem. Per-ticker haircuts crush broad strategies even when they have aggregate edge. The portfolio gate is the honest test for broad-claim strategies. Sound statistics.

3. **Self-flagged the V31 Production Pine overwrite honestly**, including the wrong assumption (`pine_new` safety) that caused it. That kind of honest postmortem is the only way the system improves.

4. **Routed the gate amendment as needing Ahmed sign-off** rather than CEO unilateral action. That boundary held. The fact that the auditor disagrees with the amendment itself does not diminish the correctness of routing it for approval.

5. **The data-cache + TV-MCP workaround** is real engineering and unlocks markets yfinance can't serve. Brittleness aside (see Concern 6), the pattern is the right shape.

6. **The session 4 finding itself.** US Divergence portfolio result, with the haircut correction, remains a genuinely impressive piece of work. This is the first thing in the project that has earned a "yes" instead of an honest "no."

---

## Recommendation on the three forward paths

**Path 1 — Deploy US Divergence to paper-forward.**
**APPROVE, conditional on:**
- Concern 1 resolved (recompute dSharpe under correct N_trials; confirm still ≥ 0.5).
- Concern 3 resolved (restate brain claim; per-market CIs computed and logged).
- Concern 5 resolved (strategy_register reconciled with config; new hash issued).
- Paper-forward stays paper-forward. No real-money discussion until ≥ 6 months of forward results exist under the same gate that certified the strategy.

**Path 2 — Add MBV as third strategy.**
**DEFER.** Adding strategy now widens the R&D queue while the deployment workflow for the first cleared strategy has never been run end-to-end. Ship Path 1 first; observe one full deployment cycle; *then* add the next strategy with an updated trial budget.

**Path 3 — Amend PORTFOLIO_GATE for small markets.**
**REJECT as proposed.** Post-hoc threshold adjustment. If a small-markets framework is genuinely needed, design it prospectively, freeze it before seeing data, and validate it on the next ≥ 6 months of UAE/crypto bars that the CEO has not yet touched.

---

## Closing note on the auditor role

The auditor exists to be the friction that protects the fund. That friction matters most exactly when something is finally working — because that is the moment when caution feels least necessary and is most necessary.

Nothing in this report is meant to diminish Session 4's progress. The US Divergence result is real. The audit findings are preconditions for converting that result into a deployment, not reasons to reject it.

The auditor has no write access to the engine, no autonomous action, and no role in deployment decisions. This report is read-only input to the CEO and Ahmed. They decide.

— End of audit —
