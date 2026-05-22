"""Decision Log writer — appends to both decision_log.md and decision_log.json.

Per Phase 1 framework directive Part 7. Schema (every entry):

    ts_utc:                 ISO 8601 with timezone offset
    title:                  short noun-phrase, <60 chars
    decision:               1-3 sentence body
    rationale:              why this decision was taken
    alternatives_considered: list of options considered
    audit_finding_refs:     list of refs (e.g., "Session 5 NEW-1")
    methodology_source:     one of:
        - framework_directive            (Ahmed's binding directives)
        - three_filter_methodology       (Phase 1 candidate selection)
        - ahmed_override                 (Ahmed's explicit case-by-case)
        - audit_finding_resolution       (response to auditor)
        - infrastructure_decision        (tools / scaffolding / ops)
        - pre_framework_legacy           (backfilled Session 5 decisions)
    commit_sha:             null at write time; backfilled by git hook later

Usage (CLI):
    python scripts/decision_log_append.py --json '<entry-json>'
    python scripts/decision_log_append.py --interactive

Usage (Python):
    from decision_log_append import append
    append({
        "title": "Pause autonomous sprint cron",
        "decision": "Disabled aig-mode1-sprint Cloud Routine.",
        "rationale": "Phase 1 directive received; cron was running Version-B autonomous methodology, which the directive forbids.",
        "alternatives_considered": ["Keep cron running with strategy-enrollment disabled", "Let cron continue until WCK finalizes"],
        "audit_finding_refs": [],
        "methodology_source": "framework_directive",
    })
"""
from __future__ import annotations
import argparse
import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG_MD = ROOT / "decision_log.md"
LOG_JSON = ROOT / "decision_log.json"
MAX_ENTRIES = 1000

VALID_SOURCES = {
    "framework_directive",
    "three_filter_methodology",
    "ahmed_override",
    "audit_finding_resolution",
    "infrastructure_decision",
    "pre_framework_legacy",
}


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _validate(entry: dict) -> None:
    required = {"title", "decision", "rationale", "methodology_source"}
    missing = required - set(entry.keys())
    if missing:
        raise ValueError(f"missing required fields: {missing}")
    if entry["methodology_source"] not in VALID_SOURCES:
        raise ValueError(
            f"methodology_source must be one of {VALID_SOURCES}, "
            f"got {entry['methodology_source']!r}"
        )


def _ensure_defaults(entry: dict) -> dict:
    out = dict(entry)
    out.setdefault("ts_utc", _now_iso())
    out.setdefault("alternatives_considered", [])
    out.setdefault("audit_finding_refs", [])
    out.setdefault("commit_sha", None)
    return out


def _append_json(entry: dict) -> int:
    arr: list = []
    if LOG_JSON.exists():
        try:
            raw = LOG_JSON.read_text(encoding="utf-8").lstrip("﻿")
            data = json.loads(raw)
            if isinstance(data, list):
                arr = data
            elif isinstance(data, dict) and "value" in data and isinstance(data["value"], list):
                arr = data["value"]
        except json.JSONDecodeError:
            arr = []
    arr.append(entry)
    if len(arr) > MAX_ENTRIES:
        arr = arr[-MAX_ENTRIES:]
    LOG_JSON.write_text(json.dumps(arr, indent=2), encoding="utf-8")
    return len(arr)


def _format_md(entry: dict) -> str:
    alts = entry.get("alternatives_considered") or []
    audits = entry.get("audit_finding_refs") or []
    lines = [
        f"### {entry['title']}",
        "",
        f"- **ts_utc:** `{entry['ts_utc']}`",
        f"- **methodology_source:** `{entry['methodology_source']}`",
        f"- **decision:** {entry['decision']}",
        f"- **rationale:** {entry['rationale']}",
    ]
    if alts:
        lines.append("- **alternatives_considered:**")
        for a in alts:
            lines.append(f"  - {a}")
    if audits:
        lines.append("- **audit_finding_refs:** " + ", ".join(f"`{a}`" for a in audits))
    if entry.get("commit_sha"):
        lines.append(f"- **commit_sha:** `{entry['commit_sha']}`")
    lines.append("")
    return "\n".join(lines)


def _append_md(entry: dict) -> None:
    if not LOG_MD.exists():
        header = (
            "# AIG Decision Log\n\n"
            "_Per Phase 1 framework directive Part 7. Append-only; oldest at top, newest at bottom._\n"
            "_Written by `scripts/decision_log_append.py`. Sync mirror: `decision_log.json`._\n\n"
            "## Entries\n\n"
        )
        LOG_MD.write_text(header, encoding="utf-8")
    with LOG_MD.open("a", encoding="utf-8") as fh:
        fh.write(_format_md(entry))


def append(entry: dict) -> dict:
    entry = _ensure_defaults(entry)
    _validate(entry)
    total = _append_json(entry)
    _append_md(entry)
    return {"ok": True, "total_entries": total, "title": entry["title"]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="JSON string for a single entry")
    ap.add_argument("--file", help="Path to a JSON file with a single entry or a list")
    args = ap.parse_args()

    if args.json:
        entries = [json.loads(args.json)]
    elif args.file:
        data = json.loads(Path(args.file).read_text(encoding="utf-8"))
        entries = data if isinstance(data, list) else [data]
    else:
        sys.stderr.write("usage: --json <entry-json> | --file <path>\n")
        return 2

    for e in entries:
        r = append(e)
        print(json.dumps(r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
