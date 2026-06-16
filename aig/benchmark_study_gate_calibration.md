# BENCHMARK STUDY — strategy-acceptance criteria for the gate joint-calibration project

Input to the gate joint-calibration council (decision_log entries 52–57).
**Proposes nothing as adopted.** Caveat: specific fund internals are proprietary;
this synthesizes the public literature + standard practitioner norms, not insider
data. Only the *reasoning* is adapted — long-short / leverage / intraday / non-halal
mechanics are discarded per mandate (Rules 15/16, daily, halal).

## Q1 — Flat WR + flat PF floors, or a joint/frontier criterion?

- Serious shops do **not** use a flat win-rate floor as a primary test. WR alone is
  uninformative (90% WR can lose money; 30% WR can be superb) — meaningful only
  jointly with payoff. A flat WR floor systematically rejects **convex**
  (trend/momentum/breakout) strategies for an intrinsic property, not a defect —
  exactly the aig finding (DBO/ROC/VCB/ART failed WR≥0.40 with strong deflated Sharpe).
- Profit factor is a retail/practitioner metric; institutions prefer risk-adjusted-
  return statistics **invariant to where a strategy sits on the WR–payoff frontier**:
  - **Sharpe** (net of costs) — Sharpe 1966/1994; the dominant standard.
  - **Deflated Sharpe Ratio + Probabilistic Sharpe Ratio** — Bailey & López de Prado
    2014: correct Sharpe for multiple-testing/selection AND non-normality. PSR>0.95 =
    95% confident true Sharpe>0. [aig already uses a deflated Sharpe — same lineage.]
  - **Sortino** (downside deviation), **Calmar/MAR** (return ÷ maxDD) — drawdown-aware.
  - **Minimum Track Record Length** — data needed for a Sharpe to be significant.
- **Verdict:** rigorous practice is risk-adjusted-return-centric and frontier-aware;
  flat per-metric floors (esp. WR) are not how serious shops accept strategies.

## Q2 — Handling the WR×payoff tradeoff; accepting both archetypes honestly

- Identity: `PF = (WR/(1-WR))·(avgWin/avgLoss)`; a strategy can sit anywhere on an
  iso-expectancy / iso-Sharpe curve. Convex (trend): low WR, big right tail. Concave
  (mean-rev): high WR, small wins + left-tail risk. Both legitimate.
- Admit both by judging edge with a metric **invariant to the split** (Sharpe/Sortino/
  DSR), then guard each archetype's failure mode separately — convex: tail-is-real /
  bootstrap-CI / DSR(skew) / max-single-trade-contribution; concave: drawdown floor /
  CVaR / risk-of-ruin (Kelly) on the rare big loss.
- If a WR/payoff test is kept, it must be a **frontier (iso-curve) criterion** — clear
  a curve in (WR, payoff) space — never two independent flat boxes. Flat boxes on a
  tradeoff dimension are the anti-pattern (and produce the aig WR×PF anti-correlation).

## Q3 — Thresholds the literature treats as "real edge" (after costs + multiple-testing)

- **Multiple testing:** Harvey, Liu & Zhu (RFS 2016) — after the literature's data-mined
  factor zoo, a new factor needs t-stat **> ~3.0** (not 2.0); most published factors
  don't survive. Argues **stricter**. aig's deflated-Sharpe-over-N-trials is the right
  mechanism (haircut ~ √(2 ln N)); aig scales it by **0.25** — lenient vs textbook.
- **Overfitting:** Bailey/Borwein/LdP/Zhu (2014) — spurious Sharpe ~ √(2 ln N) by
  chance; DSR subtracts exactly that.
- **Net-Sharpe bars:** standalone ~≥1.0 common institutional minimum; 0.5–0.7 ok for a
  *diversifying* sleeve in a multi-strategy book; >2 demands extra overfitting scrutiny.
  aig's deflated **0.5** is lenient-but-defensible for a diversifying portfolio — a
  candidate to **raise** under "stricter."
- **OOS/IS degradation:** OOS Sharpe a large fraction of IS. aig Amendment 2-ext
  "OOS≥0.7×IS" is sound + literature-aligned — and currently **UNWIRED** (entry 52).
- **Sample sufficiency:** MinTRL + enough independent trades + ≥24-mo span (Amendment 6,
  also UNWIRED).

## Q4 — Mandate adaptation (reasoning kept; mechanics discarded)

- **Long-only (Rule 15):** cross-sectional long-short norms (BAB, Jegadeesh-Titman)
  adapt to long-only top-fraction — ranking reasoning transfers (needs engine
  cross-sectional dispatch, `engine_roadmap.md`), short leg discarded.
- **No leverage (Rule 16):** Kelly informs *acceptance* reasoning (positive expected
  log-growth) but sizing stays sub-Kelly/capped.
- **Daily/halal:** drop intraday-microstructure norms; keep daily, after-cost,
  halal-filtered reasoning.

## What a frontier-aware, STRICTER-not-looser gate could look like (sketch; adopt nothing)

- **KEEP:** default-FAIL, no-override, pre-registration, deflated-Sharpe-over-N haircut.
- **WIRE** the unwired amendments as genuine added hurdles: PF-CI≥1.0, OOS≥0.7×IS,
  ≥24-mo span, per-market trade floors (closes the entry-52 gap; net-stricter).
- **REPLACE** the flat, archetype-biased WR floor with archetype-neutral risk-adjusted
  acceptance: raise the deflated-Sharpe floor; add Sortino + a Calmar/maxDD floor; add
  PSR>0.95; add a tail-robustness / max-single-trade-contribution check. Net: harder
  for everyone, but stops penalizing convex archetypes for low WR per se.
- **IF a WR/payoff test remains:** a frontier (iso-Sharpe/iso-expectancy) curve
  calibrated ABOVE the current pass region — never two flat boxes.
- **EXPLICITLY NOT:** lowering any threshold to admit the current portfolio. Every
  benchmark vector points toward more rigor (t>3, PSR, DSR, OOS/IS, drawdown) —
  consistent with principle 1 (stricter, never looser).

## COUNCIL QUESTION (the charge)

**Primary migration test:** Under a frontier-aware, risk-adjusted, archetype-neutral
gate that is STRICTER in aggregate (wired amendments + raised DSR floor + Sortino/
Calmar + PSR + tail check), do the current live slots (**Divergence, TRB-50**) still
**CLEAR**? Rule **forward-only**. The operator **ACCEPTS the answer even if it
un-clears a live slot** — that is principle 1 in practice (stricter never looser;
no portfolio-rescue).

**Sub-findings for the council to adjudicate:**
- **(a)** The deflated-Sharpe haircut is scaled by **0.25** (haircut = 0.25·√(2 ln N)).
  Is that too lenient versus the Harvey-Liu-Zhu t>3 literature — should the scaling rise?
- **(b)** **PF≥1.5 appears redundant** under a DSR-centric gate (PF == expectancy;
  risk-adjusted return already captures edge). Keep it (frontier-form only) or drop it?

## Sources

Sharpe 1966/1994; Sortino & van der Meer 1991; Kelly 1956; Bailey & López de Prado
"The Deflated Sharpe Ratio" 2014 + "The Probabilistic Sharpe Ratio"; Bailey/Borwein/
López de Prado/Zhu "Pseudo-Mathematics and Financial Charlatanism" (Notices of the AMS,
2014); López de Prado "Advances in Financial Machine Learning" 2018 [register's primary
source]; Harvey/Liu/Zhu "…and the Cross-Section of Expected Returns" RFS 2016;
Harvey & Liu "Backtesting" 2015.
