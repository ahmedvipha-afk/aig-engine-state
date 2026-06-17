"""
Reproducibility provenance (Layer B item 8).

Every run records a SHA-256 over the frozen config + strategy code + seed.
If any of those change, the hash changes, and prior results no longer apply.
This is what makes a result claimable rather than anecdotal.
"""

from __future__ import annotations
import hashlib
import os
import json
from datetime import datetime, timezone

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _sha(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def provenance() -> dict:
    files = ["config.py", "aig/strategy_ema200.py", "aig/backtest.py",
             "aig/validation_gate.py", "aig/stats.py", "aig/costs.py",
             "aig/trials.py", "trial_ledger.json"]
    # trial_ledger.json is hashed: the multiple-testing N (deflated-Sharpe haircut)
    # is a gate parameter, so config_hash must bind it (decision_log Strand C). As
    # the ledger grows, config_hash changes and prior verdicts are re-confirmed
    # under the honest, larger N — the intended behaviour.
    hashes = {f: _sha(os.path.join(_ROOT, f)) for f in files}
    combined = hashlib.sha256(
        json.dumps(hashes, sort_keys=True).encode()).hexdigest()[:16]
    return {"utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "file_hashes": hashes, "config_hash": combined}
