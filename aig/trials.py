"""Cumulative trial ledger for the multiple-testing (deflated-Sharpe) haircut.

Fixes the hardcoded-N bug (decision_log Strand C; councils 65/68): the deflated-
Sharpe haircut N must reflect the HONEST cumulative count of distinct frozen specs
ever validated, and must SELF-MAINTAIN as the pipeline grows — not sit as a literal
(`n_trials_registered=41`) that claims to grow but never does.

A TRIAL = a distinct (strategy, market, timeframe) spec that reached a verdict.
Pure same-config same-data re-runs are NOT new trials (idempotent). Genuinely
different universe/timeframe/params DO count. N grows monotonically; the haircut
0.25*sqrt(2*ln N) can therefore never be silently understated.
"""
from __future__ import annotations
import json
from pathlib import Path

_LEDGER = Path(__file__).resolve().parent.parent / "trial_ledger.json"


def _key(strategy: str, market: str, timeframe: str) -> str:
    return f"{strategy}|{market}|{timeframe}".lower()


def load_ledger(path=None) -> dict:
    p = Path(path) if path else _LEDGER
    if not p.exists():
        return {"trials": []}
    return json.loads(p.read_text(encoding="utf-8"))


def _keys(d: dict) -> set:
    out = set()
    for t in d.get("trials", []):
        if isinstance(t, str):
            out.add(t.lower())
        else:
            out.add(_key(t["strategy"], t["market"], t["timeframe"]))
    return out


def cumulative_n_trials(path=None) -> int:
    """Honest cumulative count of distinct (strategy, market, timeframe) specs."""
    return len(_keys(load_ledger(path)))


def register_trial(strategy: str, market: str, timeframe: str, path=None) -> int:
    """Idempotently add a trial key; return the new cumulative N.

    A new distinct spec increments N; an identical (same strategy/market/timeframe)
    re-run does NOT. Writes the ledger only when something new is added.
    """
    p = Path(path) if path else _LEDGER
    d = load_ledger(path)
    keys = _keys(d)
    k = _key(strategy, market, timeframe)
    if k not in keys:
        d.setdefault("trials", []).append(
            {"strategy": strategy, "market": market, "timeframe": timeframe})
        p.write_text(json.dumps(d, indent=1), encoding="utf-8")
    return cumulative_n_trials(path)


def market_from_universe(label: str) -> str:
    """Derive the market label from a universe label/path (best-effort, for
    auto-registration). Unknown -> a stable label so the trial still counts."""
    l = (label or "").lower()
    if "uae" in l:
        return "UAE"
    if "crypto" in l:
        return "CRYPTO"
    if "us" in l or "default" in l or "halal_full" in l or "halal_top" in l:
        return "US"
    return f"OTHER:{l[:24]}"
