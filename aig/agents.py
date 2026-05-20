"""
The "27 agents" as an organisational model (accepted from the directive):
not 27 processes, but tagged responsibilities so every decision in the audit
trail says WHICH function made it. This is the lightweight, honest version.
"""

from __future__ import annotations
import os
from datetime import datetime, timezone, timedelta

GST = timezone(timedelta(hours=4))
_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audit_trail.md")

# Bounded responsibilities used by Layers 1-2.
AGENTS = {
    "IN-L": "Systems / data feed health",
    "RI-H": "Compliance / data-integrity gate",
    "RD-B": "R&D backtest engine",
    "RD-D": "Validation gate (approval)",
    "IN-O": "Audit",
}


def stamp() -> str:
    return f"{datetime.now(GST):%Y-%m-%d %H:%M:%S} GST"


def audit(agent: str, msg: str) -> None:
    role = AGENTS.get(agent, agent)
    line = f"- `{stamp()}` **[{agent} {role}]** {msg}\n"
    with open(_LOG, "a") as fh:
        fh.write(line)


def reset_log(header: str) -> None:
    with open(_LOG, "w") as fh:
        fh.write(f"# AIG Audit Trail\n_{header} — {stamp()}_\n\n")
