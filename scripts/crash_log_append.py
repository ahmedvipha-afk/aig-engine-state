"""Append a crash log entry to crash_log.json as a clean JSON array.

PowerShell 5.1's ConvertTo-Json wraps Collection<T> with Count/Value keys
when the input has been round-tripped through a corrupted state — which
breaks downstream dashboard parsing. This helper keeps the file as a
plain JSON array always.

Usage:
    python crash_log_append.py <json_str>
Where <json_str> is a single JSON object representing the new entry.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "crash_log.json"
MAX_ENTRIES = 200


def main() -> int:
    if len(sys.argv) < 2:
        sys.stderr.write("usage: crash_log_append.py <json_entry>\n")
        return 2
    try:
        entry = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        sys.stderr.write(f"invalid JSON entry: {e}\n")
        return 2

    arr: list = []
    if LOG.exists():
        try:
            raw = LOG.read_text(encoding="utf-8").lstrip("﻿")
            data = json.loads(raw)
            if isinstance(data, list):
                arr = data
            elif isinstance(data, dict):
                # Heal the wrapped-Collection form from prior PS bug
                if "value" in data and isinstance(data["value"], list):
                    arr = data["value"]
                else:
                    arr = [data]
        except json.JSONDecodeError:
            arr = []

    arr.append(entry)
    if len(arr) > MAX_ENTRIES:
        arr = arr[-MAX_ENTRIES:]

    LOG.write_text(json.dumps(arr, indent=2), encoding="utf-8")
    print(f"appended; total={len(arr)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
