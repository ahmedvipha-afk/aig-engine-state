"""Telegram sender — reusable across daily/weekly/monthly routines.

Loads bot token from `~/.claude/channels/telegram/.env` and recipient(s)
from `~/.claude/channels/telegram/access.json::allowFrom`.

Usage from another script:
    from telegram_send import send_message, send_document
    send_message("Hello", parse_mode="HTML")
    send_document("path/to/scorecard.xlsx", caption="Weekly KPI scorecard")

Usage from CLI:
    python scripts/telegram_send.py text "message body"
    python scripts/telegram_send.py file path/to/file.xlsx "optional caption"
"""
from __future__ import annotations
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
TG_DIR = HOME / ".claude" / "channels" / "telegram"


def _load_token() -> str:
    env_path = TG_DIR / ".env"
    if not env_path.exists():
        raise RuntimeError(f"missing token file: {env_path}")
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.lstrip("﻿").strip()
        if line.startswith("TELEGRAM_BOT_TOKEN="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("TELEGRAM_BOT_TOKEN not found in .env")


def _recipients() -> list[int]:
    access_path = TG_DIR / "access.json"
    if not access_path.exists():
        return []
    j = json.loads(access_path.read_text(encoding="utf-8"))
    out = []
    for x in j.get("allowFrom", []):
        try:
            out.append(int(x))
        except Exception:
            pass
    return out


def _log_send(kind: str, target: int, text: str, result: dict):
    """Append every Telegram send (text or document) to telegram_sent_log.json
    so the dashboard can show a recent-messages log."""
    try:
        import datetime
        log = Path(__file__).resolve().parent.parent / "telegram_sent_log.json"
        existing = []
        if log.exists():
            try:
                existing = json.loads(log.read_text(encoding="utf-8"))
            except Exception:
                existing = []
        entry = {
            "ts_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "kind": kind,
            "to": target,
            "ok": bool(result.get("ok")),
            "message_id": result.get("result", {}).get("message_id") if result.get("ok") else None,
            "preview": (text or "")[:200],
        }
        existing.append(entry)
        # keep last 200 entries
        existing = existing[-200:]
        log.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    except Exception:
        pass


def send_message(text: str, parse_mode: str | None = None,
                 chat_id: int | None = None,
                 disable_preview: bool = True) -> dict:
    token = _load_token()
    targets = [chat_id] if chat_id is not None else _recipients()
    if not targets:
        return {"ok": False, "err": "no recipients in allowFrom"}
    last = {}
    for tid in targets:
        body = {
            "chat_id": tid,
            "text": text[:4096],
            "disable_web_page_preview": disable_preview,
        }
        if parse_mode:
            body["parse_mode"] = parse_mode
        data = urllib.parse.urlencode(body).encode("utf-8")
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                last = json.loads(r.read().decode("utf-8"))
        except Exception as e:
            last = {"ok": False, "err": str(e)}
        _log_send("text", tid, text, last)
    return last


def send_document(path: str | Path, caption: str = "",
                  chat_id: int | None = None) -> dict:
    """Multipart upload — urllib only, no extra deps."""
    token = _load_token()
    targets = [chat_id] if chat_id is not None else _recipients()
    if not targets:
        return {"ok": False, "err": "no recipients in allowFrom"}
    p = Path(path)
    if not p.exists():
        return {"ok": False, "err": f"file not found: {p}"}
    content = p.read_bytes()
    boundary = "----AIGTelegramBoundary7c1b9d"
    last = {}
    for tid in targets:
        parts: list[bytes] = []
        def field(name: str, value: str):
            parts.append(f"--{boundary}\r\n".encode())
            parts.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
            parts.append(value.encode("utf-8"))
            parts.append(b"\r\n")
        field("chat_id", str(tid))
        if caption:
            field("caption", caption[:1024])
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(
            f'Content-Disposition: form-data; name="document"; filename="{p.name}"\r\n'.encode()
        )
        parts.append(b"Content-Type: application/octet-stream\r\n\r\n")
        parts.append(content)
        parts.append(b"\r\n")
        parts.append(f"--{boundary}--\r\n".encode())
        body = b"".join(parts)
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendDocument",
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                last = json.loads(r.read().decode("utf-8"))
        except Exception as e:
            last = {"ok": False, "err": str(e)}
        _log_send("document", tid, f"[{p.name}] {caption}", last)
    return last


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("text", "file"):
        print(__doc__)
        sys.exit(2)
    mode = sys.argv[1]
    if mode == "text":
        text = " ".join(sys.argv[2:])
        r = send_message(text)
    else:
        path = sys.argv[2]
        caption = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
        r = send_document(path, caption=caption)
    print(json.dumps(r, indent=2))


if __name__ == "__main__":
    main()
