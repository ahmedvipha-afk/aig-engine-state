"""
Best-strategy-per-ticker reassignment (Phase 1 directive F2).

For every ticker that contributes (oos_n > 0) to a CLEARED-portfolio strategy,
compute its per-ticker dSharpe across ALL strategies whose portfolio cleared
that market, and assign the ticker to its best-dSharpe strategy. Re-run
whenever a new strategy clears a market's portfolio gate.

OUTPUTS:
  winners_assignment.json — full per-ticker mapping with metrics
  winners_registry.md     — human-readable, dashboard-rendered

PRINCIPLES:
- Only strategies whose portfolio gate CLEARED are candidates for assignment.
  TV-only winners (sub-engine-gate Sharpe) live in a separate research-watchlist
  section of winners_registry.md, NOT in the paper-forward assignment.
- Criterion is highest deflated Sharpe per ticker. Pre-registered, deterministic.
- Tie-break: highest expectancy.
- Tickers contributing to only one cleared strategy get assigned to that one
  by definition (no comparison needed).
"""
from __future__ import annotations
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)

# CLEARED (strategy, market) sources — update when a new market clears
CLEARED_SOURCES = {
    ("divergence", "US"): "validation_divergence_1d_full_haircut6.json",
    ("mbv",        "US"): "validation_mbv_us_1d.json",
    ("pmr",        "US"): "validation_pmr_us_1d.json",
    ("str",        "US"): "validation_str_us_1d.json",
    # Add new (strategy, market) here as they clear portfolio gate.
}

# Near-miss research strategies (positive dSharpe + positive expectancy,
# blocked only by 40% WR floor — preserved per CEO D-011 for future
# auditor-Warning-4 reconsideration; NOT paper-forward).
NEAR_MISS_RESEARCH = [
    {"trial": "dbo_us_1d",  "dsharpe": 2.941, "expectancy": 1.298, "wr": 0.341, "trades": 11910,
     "note": "Donchian breakout. Math edge; WR floor blocker. First Warning-4 candidate if WR rule amends."},
    {"trial": "roc_us_1d",  "dsharpe": 3.72,  "expectancy": 1.27,  "wr": 0.36,  "trades": 10500,
     "note": "Rate-of-Change momentum. Strong dSharpe; WR floor blocker."},
    {"trial": "vcb_us_1d",  "dsharpe": 1.92,  "expectancy": 1.21,  "wr": 0.37,  "trades": 9100,
     "note": "Volatility contraction breakout. Positive Sharpe; WR floor blocker."},
    {"trial": "hat_us_1d",  "dsharpe": 1.039, "expectancy": 1.071, "wr": 0.3703, "trades": 33451,
     "note": "Heikin-Ashi trend. Closest to clearing (37.0% vs 40% — 3pp gap). WR floor blocker."},
]

# Pending full-universe re-validation (PART B Step 4 — CEO directive 2026-05-21
# evening). PARTIAL sweeps awaiting re-run on expanded universe before counting
# toward Phase-1 coverage tallies.
PENDING_REVALIDATION = {
    "us_gap": {"current": 1603, "target": 1621, "missing": 18,
               "source": "Ahmed authoritative list (not yet merged)"},
    "uae_gap": {"current": 64, "target": 80, "missing": 16,
                "source": "DFM/ADX names not retrievable via yfinance — need TV-MCP cache"},
    "crypto_gap": {"current": 150, "target": 140, "missing": 0,
                   "source": "universe already complete"},
    "uae_partial_reruns": [
        "ema200_uae_1d", "divergence_uae_1d", "mbv_uae_1d", "dbo_uae_1d",
        "roc_uae_1d", "vcb_uae_1d", "hat_uae_1d",
    ],
    "us_priority1_verifications": ["divergence_us_1d", "mbv_us_1d", "pmr_us_1d"],
    "us_priority2_verifications": ["dbo_us_1d", "roc_us_1d", "vcb_us_1d"],
}


# TV Strategy Tester winners (research watchlist — NOT paper-forward)
TV_WATCHLIST = [
    {"ticker": "AAPL", "strategy_tv": "ema200_1h_tv", "tv_verdict": "CLEAN_EDGE",
     "note": "max Sharpe 0.20 — fails v7.0 §19 engine floor; preserved per F2 as research watchlist"},
    {"ticker": "GOOG",  "strategy_tv": "ema200_1h_tv", "tv_verdict": "CLEAN_EDGE",
     "note": "see AAPL"},
    {"ticker": "TSM",   "strategy_tv": "ema200_1h_tv", "tv_verdict": "CLEAN_EDGE",
     "note": "see AAPL"},
    {"ticker": "NVDA",  "strategy_tv": "ema200_1h_tv", "tv_verdict": "near_miss",
     "note": "TV near-miss EMA-200 1H — include if Calmar criterion adopted"},
    {"ticker": "GOOGL", "strategy_tv": "ema200_1h_tv", "tv_verdict": "near_miss",
     "note": "see NVDA"},
    {"ticker": "ORCL",  "strategy_tv": "ema200_1h_tv", "tv_verdict": "near_miss",
     "note": "see NVDA"},
]


def load_contributors(strategy: str, market: str, source_file: str) -> dict:
    """Return {ticker: row_dict} of tickers with oos_n > 0 in source file."""
    out = {}
    path = ROOT / source_file
    if not path.exists():
        print(f"  [skip] {source_file} not found")
        return out
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    for r in data.get("results") or []:
        if not isinstance(r, dict):
            continue
        if r.get("verdict") in ("BLOCKED_DATA", "DATA_ERROR"):
            continue
        oos_n = r.get("oos_n") or 0
        if oos_n <= 0:
            continue
        tk = r.get("ticker")
        if not tk:
            continue
        out[tk] = {
            "strategy": strategy, "market": market,
            "dsharpe": float(r.get("oos_sharpe_deflated") or -99),
            "expectancy": float(r.get("oos_expectancy") or 0),
            "oos_n": oos_n,
            "raw_sharpe": float(r.get("oos_sharpe_raw") or 0),
            "source_file": source_file,
        }
    return out


def reassign():
    """Build best-strategy-per-ticker assignment from all cleared sources."""
    per_ticker: dict[str, list[dict]] = {}
    for (strat, mkt), fn in CLEARED_SOURCES.items():
        rows = load_contributors(strat, mkt, fn)
        print(f"  loaded {len(rows)} contributors from {fn} ({strat}/{mkt})")
        for tk, row in rows.items():
            per_ticker.setdefault(tk, []).append(row)

    assignments: dict[str, dict] = {}
    for tk, entries in per_ticker.items():
        # Sort by (dSharpe, expectancy) descending; pick best.
        best = max(entries, key=lambda e: (e["dsharpe"], e["expectancy"]))
        best = dict(best)
        best["candidates_count"] = len(entries)
        best["alternatives"] = [
            {"strategy": e["strategy"], "dsharpe": e["dsharpe"], "expectancy": e["expectancy"]}
            for e in entries if e["strategy"] != best["strategy"]
        ]
        assignments[tk] = best

    by_strat: dict[str, list[str]] = {}
    for tk, a in assignments.items():
        by_strat.setdefault(a["strategy"], []).append(tk)

    return assignments, by_strat, per_ticker


def write_assignment_json(assignments: dict, by_strat: dict, per_ticker: dict):
    out = {
        "generated_at": "2026-05-22",
        "criterion": "highest_oos_sharpe_deflated_then_expectancy_within_cleared_portfolios",
        "cleared_sources": {f"{s}/{m}": fn for (s, m), fn in CLEARED_SOURCES.items()},
        "tally": {s: len(tks) for s, tks in by_strat.items()},
        "tickers_in_both_strategies": sum(1 for tk in per_ticker if len(per_ticker[tk]) > 1),
        "tickers_in_one_only": sum(1 for tk in per_ticker if len(per_ticker[tk]) == 1),
        "assignments": assignments,
    }
    (ROOT / "winners_assignment.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8"
    )


def write_registry_md(assignments: dict, by_strat: dict):
    """Render winners_registry.md from the assignment + TV watchlist."""
    lines = [
        "# Winners Registry — Best-Strategy-Per-Ticker Assignment",
        "",
        "Phase 1 directive F2 (CEO 2026-05-21). Each ticker assigned to ITS",
        "best-performing strategy by per-ticker deflated Sharpe (with positive",
        "expectancy preferred). Reassignment re-runs whenever a new strategy",
        "clears its market's portfolio gate.",
        "",
        f"**Criterion:** `highest_oos_sharpe_deflated_then_expectancy` (pre-registered, deterministic).",
        f"**Cleared sources:** {', '.join(f'{s}/{m}' for (s,m) in CLEARED_SOURCES.keys())}",
        f"**Total assigned tickers:** {len(assignments)}",
        "",
        "---",
        "",
        "## Paper-Forward Roster (assigned by cleared portfolio)",
        "",
    ]
    for strat in sorted(by_strat.keys()):
        tks = by_strat[strat]
        # Sort within strategy by dSharpe descending
        tks_sorted = sorted(tks, key=lambda t: -assignments[t]["dsharpe"])
        lines.append(f"### {strat.upper()} — {len(tks)} tickers")
        lines.append("")
        lines.append("| Ticker | Market | dSharpe | Expectancy | OOS n | Alt strategies |")
        lines.append("|--------|--------|---------|-----------:|------:|----------------|")
        # show top 50 for readability; full list in JSON
        for tk in tks_sorted[:50]:
            a = assignments[tk]
            alts = ", ".join(f"{x['strategy']}({x['dsharpe']:.2f})" for x in a.get("alternatives", []))
            lines.append(f"| {tk} | {a['market']} | {a['dsharpe']:+.3f} | {a['expectancy']:.3f} | {a['oos_n']} | {alts or '—'} |")
        if len(tks_sorted) > 50:
            lines.append(f"| _...{len(tks_sorted)-50} more (see `winners_assignment.json`)_ | | | | | |")
        lines.append("")

    # --- Near-Miss Research Strategies section ---
    lines.extend([
        "---",
        "",
        "## Near-Miss Research Strategies (NOT paper-forward — math edge, WR floor blocked)",
        "",
        "Per CEO D-011 (2026-05-21): strategies with positive dSharpe + positive",
        "expectancy + sufficient trades but failing the 40% WR floor are preserved",
        "here as research watchlist. They do NOT enter the paper-forward detector.",
        "If auditor Warning-4 is later formally addressed (e.g. fully-systematic",
        "execution track without WR floor), these become the first candidates.",
        "",
        "| Trial | dSharpe | Expectancy | WR | Trades | Note |",
        "|-------|--------:|-----------:|---:|-------:|------|",
    ])
    for nm in NEAR_MISS_RESEARCH:
        lines.append(
            f"| {nm['trial']} | {nm['dsharpe']:+.3f} | {nm['expectancy']:.3f} | "
            f"{nm['wr']*100:.1f}% | {nm['trades']:,} | {nm['note']} |"
        )

    # --- Pending Full-Universe Re-Validation section (PART B Step 4) ---
    lines.extend([
        "",
        "---",
        "",
        "## Pending Full-Universe Re-Validation (PART B Step 4 — CEO directive 2026-05-21 eve)",
        "",
        "Holding section per PART B remediation queue. PARTIAL sweeps and",
        "universe gaps below MUST be resolved before Phase-1 exit-criteria",
        "tallies (Obj 3/4/5) can be claimed final.",
        "",
        "### Universe gaps",
        "",
        "| Market | Current file | Full halal target | Missing | Source |",
        "|--------|-------------:|------------------:|--------:|--------|",
        f"| US     | {PENDING_REVALIDATION['us_gap']['current']} | "
        f"{PENDING_REVALIDATION['us_gap']['target']} | "
        f"{PENDING_REVALIDATION['us_gap']['missing']} | "
        f"{PENDING_REVALIDATION['us_gap']['source']} |",
        f"| UAE    | {PENDING_REVALIDATION['uae_gap']['current']} | "
        f"{PENDING_REVALIDATION['uae_gap']['target']} | "
        f"{PENDING_REVALIDATION['uae_gap']['missing']} | "
        f"{PENDING_REVALIDATION['uae_gap']['source']} |",
        f"| Crypto | {PENDING_REVALIDATION['crypto_gap']['current']} | "
        f"{PENDING_REVALIDATION['crypto_gap']['target']} | "
        f"{PENDING_REVALIDATION['crypto_gap']['missing']} | "
        f"{PENDING_REVALIDATION['crypto_gap']['source']} |",
        "",
        "### UAE PARTIAL sweeps awaiting re-run on expanded UAE-80 universe",
        "",
    ])
    for trial in PENDING_REVALIDATION["uae_partial_reruns"]:
        lines.append(f"- [ ] `{trial}` — re-run via `staged_validate.py --enroll-market` (after UAE-80 expansion)")
    lines.extend([
        "",
        "### US priority-1 verifications (cleared strategies — confirm clearance holds on 1,621)",
        "",
    ])
    for trial in PENDING_REVALIDATION["us_priority1_verifications"]:
        lines.append(f"- [ ] `{trial}` — re-run on expanded US-1,621 universe; confirm dSharpe still clears")
    lines.extend([
        "",
        "### US priority-2 verifications (near-miss strategies — confirm near-miss profile holds)",
        "",
    ])
    for trial in PENDING_REVALIDATION["us_priority2_verifications"]:
        lines.append(f"- [ ] `{trial}` — re-run on expanded US-1,621; confirm near-miss profile holds")

    lines.extend([
        "",
        "---",
        "",
        "## TV Strategy Tester Watchlist (NOT paper-forward — research only)",
        "",
        "Per audit Concern 2 + Path A: TV-only winners whose engine-gate Sharpe",
        "falls below the v7.0 §19 floor are preserved here as research watchlist.",
        "They DO NOT enter the paper-forward detector unless their strategy",
        "subsequently clears the engine portfolio gate.",
        "",
        "| Ticker | TV Strategy | Verdict | Note |",
        "|--------|-------------|---------|------|",
    ])
    for w in TV_WATCHLIST:
        lines.append(f"| {w['ticker']} | {w['strategy_tv']} | {w['tv_verdict']} | {w['note']} |")

    lines.extend([
        "",
        "---",
        "",
        "## How to update this file",
        "",
        "Do NOT hand-edit the per-strategy tables — regenerate by running:",
        "```",
        "python scripts/reassign_best_strategy.py",
        "```",
        "",
        "Updating procedure when a new strategy clears its market's gate:",
        "1. Append the new `(strategy, market): filename` to `CLEARED_SOURCES`",
        "   in `scripts/reassign_best_strategy.py`.",
        "2. Re-run the script. It re-tests every previously-assigned ticker",
        "   against the new strategy AND existing strategies, then reassigns",
        "   to the new best dSharpe per ticker.",
        "3. Commit the updated `winners_registry.md` + `winners_assignment.json`",
        "   in the same commit.",
        "",
    ])
    (ROOT / "winners_registry.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    print("Phase-1 F2 reassignment — best strategy per ticker")
    assignments, by_strat, per_ticker = reassign()

    print(f"\nResult: {len(assignments)} tickers assigned across {len(by_strat)} strategies")
    for s, tks in sorted(by_strat.items()):
        pos = sum(1 for tk in tks if assignments[tk]["expectancy"] > 1.0)
        avg = sum(assignments[tk]["dsharpe"] for tk in tks) / max(1, len(tks))
        print(f"  {s}: {len(tks)} tickers (avg dSharpe {avg:+.3f}, {pos} with exp>1.0)")
    both = sum(1 for tk in per_ticker if len(per_ticker[tk]) > 1)
    print(f"  tickers in BOTH strategies (reassigned by best): {both}")

    write_assignment_json(assignments, by_strat, per_ticker)
    write_registry_md(assignments, by_strat)
    print(f"\nwrote winners_assignment.json ({len(assignments)} entries)")
    print(f"wrote winners_registry.md")


if __name__ == "__main__":
    main()
