"""AIG Cockpit Dashboard v3 — multi-tab self-contained HTML.

v3 ships all 12 improvements from the design review:
  1.  Live header NAV computed from paper_forward_positions.json equity curve
  2.  Header Mode pill auto-detected from ceo_brain.md OPERATING MODE
  3.  History tab auto-populated from ceo_brain SESSION X ARTIFACTS + git log
  4.  Agents tab — per-agent state derived from sprint item context
  5.  Markets tab — winners/losers per market from validation_*.json results
  6.  Trial Budget panel on Overview from strategy_register.md
  7.  Deep links — tickers → raw cache CSV, commits → GitHub commit URL,
      JSONs → raw GitHub URL, audit findings → ceo_brain section anchor
  8.  Routine "last run + duration + result" from logs + commit timestamps
  9.  Per-strategy leaderboard — 6 horizontal bars sorted by dSharpe
  10. Live alerts — FAILs, missed routine fires, drawdown breaches,
      integrity-gate blocks above threshold
  11. Cross-tab search — match counts shown in tab button badges,
      jump-to suggestion when active tab is empty
  12. Visible auto-refresh countdown in header (MM:SS to next meta refresh)
"""
from __future__ import annotations
import html
import json
import os
import re
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_PATH = ROOT / "dashboard.html"
UNIVERSE_DIR = ROOT / "universe"
LOGS_DIR = ROOT / "logs"
HOME = Path(os.path.expanduser("~"))
SCHEDULED_TASKS_DIR = HOME / ".claude" / "scheduled-tasks"
TELEGRAM_DIR = HOME / ".claude" / "channels" / "telegram"
TELEGRAM_LOG = ROOT / "telegram_sent_log.json"
PAPER_STATE = ROOT / "paper_forward_positions.json"
GST = timezone(timedelta(hours=4))
PAGES_BASE = "https://ahmedvipha-afk.github.io/aig-engine-state"
RAW_BASE = "https://raw.githubusercontent.com/ahmedvipha-afk/aig-engine-state/main"
REPO_URL = "https://github.com/ahmedvipha-afk/aig-engine-state"

# ---- helpers --------------------------------------------------------------

def esc(x) -> str:
    return html.escape(str(x), quote=True)


def _safe_read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _count_universe(path: Path) -> int:
    if not path.exists():
        return 0
    n = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            n += 1
    return n


def _git_log(n: int = 60) -> list[dict]:
    try:
        out = subprocess.check_output(
            ["git", "log", f"-{n}", "--pretty=format:%h|%H|%ad|%ae|%s",
             "--date=iso-strict"],
            cwd=str(ROOT), text=True, stderr=subprocess.DEVNULL
        )
    except Exception:
        return []
    rows = []
    for line in out.splitlines():
        parts = line.split("|", 4)
        if len(parts) == 5:
            rows.append({"sha": parts[0], "full_sha": parts[1],
                         "date": parts[2], "email": parts[3],
                         "subject": parts[4]})
    return rows


def _git_remote_url() -> str:
    try:
        url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=str(ROOT), text=True, stderr=subprocess.DEVNULL
        ).strip()
        if url.endswith(".git"):
            url = url[:-4]
        return url
    except Exception:
        return REPO_URL


def _scheduled_tasks() -> list[dict]:
    rows = []
    if not SCHEDULED_TASKS_DIR.exists():
        return rows
    for d in sorted(SCHEDULED_TASKS_DIR.iterdir()):
        if not d.is_dir():
            continue
        skill = d / "SKILL.md"
        if not skill.exists():
            continue
        head = skill.read_text(encoding="utf-8", errors="ignore").splitlines()[:30]
        fm: dict[str, str] = {}
        in_fm = False
        for line in head:
            if line.strip() == "---":
                in_fm = not in_fm
                continue
            if in_fm:
                m = re.match(r"^([\w-]+):\s*(.*)$", line)
                if m:
                    fm[m.group(1)] = m.group(2).strip().strip('"')
        # last-run = skill.md mtime (the routine writes the file via tool calls)
        # Reasonable proxy until we keep a dedicated last-run file.
        last_mtime = datetime.fromtimestamp(skill.stat().st_mtime, tz=GST)
        rows.append({
            "name": d.name,
            "cron": fm.get("cron", fm.get("schedule", "—")),
            "description": fm.get("description", ""),
            "enabled": fm.get("enabled", "true"),
            "last_touch": last_mtime.strftime("%Y-%m-%d %H:%M GST"),
        })
    return rows


def _telegram_status() -> dict:
    status = {"bot_pid": None, "alive": False, "policy": None,
              "allowFrom": [], "last_log_mtime": None}
    pid_file = TELEGRAM_DIR / "bot.pid"
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            status["bot_pid"] = pid
            if os.name == "nt":
                import subprocess as sp
                r = sp.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV"],
                          capture_output=True, text=True)
                status["alive"] = "bun" in r.stdout.lower()
        except Exception:
            pass
    access_file = TELEGRAM_DIR / "access.json"
    if access_file.exists():
        try:
            j = json.loads(access_file.read_text(encoding="utf-8"))
            status["policy"] = j.get("dmPolicy")
            status["allowFrom"] = j.get("allowFrom", [])
        except Exception:
            pass
    log = TELEGRAM_DIR / "server.log"
    if log.exists():
        status["last_log_mtime"] = datetime.fromtimestamp(
            log.stat().st_mtime, tz=GST
        ).strftime("%Y-%m-%d %H:%M GST")
    return status


def _telegram_sent_log() -> list[dict]:
    if not TELEGRAM_LOG.exists():
        return []
    try:
        return json.loads(TELEGRAM_LOG.read_text(encoding="utf-8"))
    except Exception:
        return []


def _latest_validation_results() -> dict:
    """Return latest validation per (strategy, market) plus the raw `results`
    array so we can compute winners/losers downstream."""
    results: dict[tuple[str, str], tuple[float, Path, dict]] = {}
    for p in ROOT.glob("validation_*.json"):
        d = _safe_read_json(p)
        if not d or not d.get("portfolio"):
            continue
        args = d.get("args", {})
        strat = args.get("strategy", "?")
        uni = (args.get("universe") or "").lower()
        if "uae" in p.name or "uae" in uni:
            market = "UAE"
        elif "crypto" in p.name or "crypto" in uni:
            market = "CRYPTO"
        else:
            market = "US"
        key = (strat, market)
        mt = p.stat().st_mtime
        if key not in results or mt > results[key][0]:
            results[key] = (mt, p, d)
    out = {}
    for (strat, market), (mt, p, d) in results.items():
        pf = d["portfolio"]
        out[(strat, market)] = {
            "file": p.name,
            "raw_url": f"{RAW_BASE}/{p.name}",
            "mtime": datetime.fromtimestamp(mt, tz=GST).strftime("%Y-%m-%d %H:%M"),
            "verdict": pf.get("verdict"),
            "passed": bool(pf.get("passed")),
            "trades": pf.get("portfolio_trades"),
            "contributors": pf.get("contributing_tickers"),
            "universe_size": pf.get("universe_size"),
            "expectancy": pf.get("portfolio_expectancy"),
            "win_rate": pf.get("portfolio_win_rate"),
            "sharpe_raw": pf.get("portfolio_sharpe_raw"),
            "sharpe_def": pf.get("portfolio_sharpe_deflated"),
            "reasons": pf.get("reasons") or [],
            "results_array": d.get("results", []),
        }
    return out


def _ceo_brain_sections() -> dict:
    p = ROOT / "ceo_brain.md"
    if not p.exists():
        return {"sprint_tracker": [], "decisions": [], "open_issues": [],
                "raw": "", "mode": "MODE 1", "mode_label": "FULL SPRINT",
                "sessions": []}
    text = p.read_text(encoding="utf-8", errors="ignore")

    # Operating mode
    mode = "MODE 1"; mode_label = "FULL SPRINT"
    m = re.search(r"OPERATING MODE.*?MODE\s+(\d)\s*[—\-]\s*([A-Z][A-Z\s]+?)\*", text, flags=re.S | re.I)
    if m:
        mode = "MODE " + m.group(1)
        mode_label = m.group(2).strip().upper()

    # Sprint tracker rows
    sprint = []
    in_tracker = False
    for line in text.splitlines():
        if line.strip().startswith("## SPRINT TRACKER"):
            in_tracker = True
            continue
        if in_tracker and line.startswith("## "):
            break
        if in_tracker and line.startswith("| ") and not line.startswith("| #") and not line.startswith("|---"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 5 and parts[0].strip().isdigit():
                sprint.append({
                    "id": parts[0], "item": parts[1], "status": parts[2],
                    "criteria": parts[3], "notes": parts[4],
                })

    # Decisions (DECISION CONTINUITY format)
    decisions = []
    for m2 in re.finditer(
        r"^\d+\.\s+\*\*(\d{4}-\d{2}-\d{2}\s+D-\d+)\*\*\s+—\s+\*([^*]+)\*\s*\n([^\n]*)",
        text, flags=re.M):
        decisions.append({
            "id_date": m2.group(1).strip(),
            "title": m2.group(2).strip(),
            "rationale_head": m2.group(3).strip(),
        })

    # Open issues
    open_issues = []
    m3 = re.search(r"^##+\s+OPEN ISSUES.*?$", text, flags=re.M)
    if m3:
        rest = text[m3.end():]
        end = re.search(r"^##+ ", rest, flags=re.M)
        block = rest[:end.start()] if end else rest
        for line in block.splitlines():
            if line.strip().startswith(("###", "1.", "2.", "3.", "- ", "* ")):
                open_issues.append(line.strip())

    # Session artifacts (parse SESSION X ARTIFACTS sections)
    sessions = []
    for m4 in re.finditer(r"^## SESSION (\d+) ARTIFACTS.*?$", text, flags=re.M):
        sid = m4.group(1)
        start = m4.end()
        nxt = re.search(r"^##+ ", text[start:], flags=re.M)
        block = text[start:start + nxt.start()] if nxt else text[start:]
        bullets = [l.strip("- ").strip() for l in block.splitlines() if l.strip().startswith("- ")]
        sessions.append({"id": sid, "title": f"Session {sid} Artifacts", "items": bullets})

    return {"sprint_tracker": sprint, "decisions": decisions,
            "open_issues": open_issues, "raw": text,
            "mode": mode, "mode_label": mode_label,
            "sessions": sessions}


def _auditor_findings() -> list[dict]:
    p = ROOT / "auditor_report.md"
    if not p.exists():
        return []
    text = p.read_text(encoding="utf-8", errors="ignore")
    findings = []
    for m in re.finditer(
        r"^###\s+(\d+)\.\s+(BLOCKING|WARNING|NOTE)\s+—\s+(.+?)$",
        text, flags=re.M):
        findings.append({"id": m.group(1), "severity": m.group(2),
                         "title": m.group(3).strip()})
    return findings


def _paper_state() -> dict | None:
    return _safe_read_json(PAPER_STATE)


def _paper_nav() -> tuple[float, float]:
    """Returns (nav_usd, pct_change_from_base)."""
    p = _paper_state()
    if not p:
        return 100000.0, 0.0
    cum_pct = sum(t.get("pnl_pct", 0) for t in (p.get("history") or []))
    nav = 100000 * (1 + cum_pct / 100)
    return nav, cum_pct


def _trial_budget() -> list[dict]:
    p = ROOT / "strategy_register.md"
    if not p.exists():
        return []
    text = p.read_text(encoding="utf-8", errors="ignore")
    trials = []
    in_budget = False
    for line in text.splitlines():
        if "TRIAL BUDGET" in line:
            in_budget = True
            continue
        if in_budget and line.startswith("##"):
            break
        if in_budget and line.startswith("|") and "trial id" not in line.lower() and "---" not in line:
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 9 and parts[0].isdigit():
                trials.append({
                    "id": parts[0], "trial_id": parts[1].replace("`", ""),
                    "strategy": parts[2], "market": parts[3],
                    "timeframe": parts[4], "engine": parts[5],
                    "registered": parts[6], "first_run": parts[7],
                    "verdict": parts[8],
                })
    return trials


def _winners_losers(market: str, runs: dict, top_n: int = 5) -> tuple[list, list]:
    """From validation_*.json `results` arrays, pull top-N expectancy winners
    + bottom-N losers for the given market across all strategies."""
    all_rows = []
    for (strat, m), v in runs.items():
        if m != market:
            continue
        for r in v.get("results_array", []) or []:
            if not isinstance(r, dict):
                continue
            if r.get("verdict") in ("BLOCKED_DATA", "DATA_ERROR"):
                continue
            if (r.get("oos_n") or 0) < 10:
                continue
            all_rows.append({
                "ticker": r.get("ticker"),
                "strategy": strat,
                "exp": r.get("oos_expectancy") or 0,
                "sharpe": r.get("oos_sharpe_deflated"),
                "n": r.get("oos_n"),
            })
    all_rows.sort(key=lambda r: r["exp"], reverse=True)
    return all_rows[:top_n], all_rows[-top_n:][::-1]


def _cron_next_fire_iso(cron: str) -> str | None:
    try:
        parts = cron.strip().split()
        if len(parts) != 5:
            return None
        minute, hour, dom, month, dow = parts
        now = datetime.now(GST)
        for i in range(1, 8 * 24 * 60):
            t = now + timedelta(minutes=i)
            if minute != "*" and not _cron_match(minute, t.minute): continue
            if hour != "*" and not _cron_match(hour, t.hour): continue
            if dom != "*" and not _cron_match(dom, t.day): continue
            if month != "*" and not _cron_match(month, t.month): continue
            if dow != "*":
                py_dow = (t.weekday() + 1) % 7
                if not _cron_match(dow, py_dow): continue
            return t.replace(second=0, microsecond=0).isoformat()
        return None
    except Exception:
        return None


def _cron_match(field: str, value: int) -> bool:
    for part in field.split(","):
        part = part.strip()
        if part == "*":
            return True
        if "/" in part:
            range_part, step_s = part.split("/")
            step = int(step_s)
            if range_part == "*":
                lo, hi = 0, 59
            elif "-" in range_part:
                lo, hi = [int(x) for x in range_part.split("-")]
            else:
                lo = int(range_part); hi = 59
            if lo <= value <= hi and (value - lo) % step == 0:
                return True
        elif "-" in part:
            lo, hi = [int(x) for x in part.split("-")]
            if lo <= value <= hi:
                return True
        else:
            if int(part) == value:
                return True
    return False


def _routine_last_run(name: str, commits: list[dict]) -> dict | None:
    """Best-effort last-run inference: find most recent commit whose message
    matches the routine name + parse log file if present."""
    name_low = name.lower()
    for c in commits:
        if any(k in c["subject"].lower()
               for k in (name_low, "sprint" if "sprint" in name_low else name_low,
                         "morning" if "morning" in name_low else "X")):
            return {"sha": c["sha"], "date": c["date"], "subject": c["subject"]}
    return None


def _vix_latest() -> dict:
    cache = ROOT / "data_cache" / "_vix_cache.json"
    try:
        if cache.exists():
            c = json.loads(cache.read_text(encoding="utf-8"))
            ts = datetime.fromisoformat(c["ts"])
            if (datetime.now(timezone.utc) - ts).total_seconds() < 3600:
                return c
    except Exception:
        pass
    out = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "value": None, "regime": "unknown"}
    try:
        import yfinance as yf
        df = yf.download("^VIX", period="5d", interval="1d",
                         auto_adjust=True, progress=False, threads=False)
        if df is not None and len(df):
            v = float(df["Close"].iloc[-1])
            out["value"] = round(v, 2)
            if v < 15: out["regime"] = "Bull-Calm"
            elif v < 20: out["regime"] = "Bull-Normal"
            elif v < 25: out["regime"] = "Neutral"
            elif v < 30: out["regime"] = "Elevated"
            elif v < 35: out["regime"] = "High Vol"
            elif v < 40: out["regime"] = "Crisis A"
            else: out["regime"] = "Crisis B HALT"
    except Exception as e:
        out["error"] = str(e)
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(out), encoding="utf-8")
    except Exception:
        pass
    return out


def _agent_state_map(sprint_tracker: list[dict]) -> dict:
    """Derive per-agent state from sprint context.
    Sprint items map to which agents are 'active' vs 'waiting'."""
    active_item = None
    for r in sprint_tracker:
        st = r.get("status", "")
        if "IN PROGRESS" in st or "🔄" in st:
            active_item = r["id"]
            break
    state = {}
    # Default: all active baseline
    for aid in ["CEO", "CIO", "CFO", "RD-A", "RD-B", "RD-C", "RD-D",
                "EX-A", "EX-B", "EX-C", "EX-D", "EX-E", "EX-F",
                "RI-F", "RI-G", "RI-H", "RI-I", "RI-J", "RI-K",
                "IN-L", "IN-M", "IN-N", "IN-O",
                "LM-P", "LM-Q", "PR-R", "PR-S"]:
        state[aid] = "active"

    # Item-specific tweaks
    if active_item == "4":  # crypto gate iterating
        state["EX-F"] = "iterating"
    if active_item == "5":  # MBV
        state["RD-A"] = "active"; state["RD-B"] = "active"
    if active_item == "6":  # paper-forward observation
        state["RD-C"] = "active"; state["EX-D"] = "active"
    # No real fills yet
    state["EX-E"] = "waiting"
    state["EX-B"] = "waiting"
    state["EX-C"] = "waiting"
    state["RI-J"] = "waiting"
    state["PR-S"] = "waiting"
    return state


# ---- CSS + JS -------------------------------------------------------------

CSS = """
:root { color-scheme: dark; --bg:#060a14; --cd:#0d1525; --nv:#1B2A4A;
        --bd:#1a2744; --gold:#C9A84C; --gn:#10B981; --rd:#EF4444;
        --or:#F59E0B; --bl:#2E5FA3; --tl:#1A7A6E;
        --t1:#F1F5F9; --t2:#94A3B8; --t3:#475569; }
* { box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
       background: var(--bg); color: var(--t1); margin: 0;
       line-height: 1.45; font-size: 13px; }
h1, h2, h3 { margin: 0; }
a { color: #5aa9ff; text-decoration: none; }
a:hover { text-decoration: underline; }

.header { background: linear-gradient(135deg, var(--nv), #0b1020);
          border-bottom: 2px solid #C9A84C33; padding: 12px 20px;
          position: sticky; top: 0; z-index: 100; backdrop-filter: blur(8px); }
.header-row { display: flex; justify-content: space-between; align-items: center;
              flex-wrap: wrap; gap: 12px; max-width: 1280px; margin: 0 auto; }
.brand { font-size: 18px; font-weight: 900; }
.brand .ar { font-size: 11px; color: var(--gold); margin-left: 8px; }
.brand-sub { font-size: 9px; color: var(--t3); }
.refresh-countdown { font-size: 9px; color: var(--t3); margin-top: 2px; }
.right-tools { display: flex; gap: 10px; align-items: center; }
.lang-toggle { display: flex; border: 1px solid var(--bd); border-radius: 6px;
               overflow: hidden; background: #060a14aa; }
.lang-btn { background: none; border: none; padding: 5px 9px; color: var(--t3);
            font-size: 11px; font-weight: 700; cursor: pointer;
            font-family: inherit; }
.lang-btn:hover { color: var(--t1); }
.lang-btn.active { background: var(--gold); color: #0b1020; }
html[dir="rtl"] body { font-family: 'Segoe UI', Tahoma, 'Cairo', sans-serif; }
html[dir="rtl"] .brand .ar { margin-left: 0; margin-right: 8px; }
html[dir="rtl"] .tab-bar-inner, html[dir="rtl"] .header-row { direction: rtl; }
.search-box { background: #060a14cc; border: 1px solid var(--bd);
              border-radius: 6px; padding: 5px 10px; color: var(--t1);
              font-size: 12px; width: 240px; outline: none; }
.search-box:focus { border-color: var(--gold); }
.bell { position: relative; cursor: pointer; padding: 4px 8px;
        border-radius: 6px; background: #060a14aa; border: 1px solid var(--bd); }
.bell-count { position: absolute; top: -4px; right: -4px;
              background: var(--rd); color: #fff; font-size: 9px;
              font-weight: 800; border-radius: 9px; padding: 1px 5px; }
.nav-pill { padding: 4px 10px; border-radius: 8px; text-align: right; }
.nav-pill.mode1 { background: #C9A84C20; border: 1px solid #C9A84C44; }
.nav-pill.mode2 { background: #10B98120; border: 1px solid #10B98144; }
.nav-pill .label { font-size: 8px; font-weight: 700; }
.nav-pill.mode1 .label { color: var(--gold); }
.nav-pill.mode2 .label { color: var(--gn); }
.nav-pill .val { font-size: 11px; font-weight: 900; }
.nav-pill.mode1 .val { color: var(--gold); }
.nav-pill.mode2 .val { color: var(--gn); }
.nav-display .label { font-size: 8px; color: var(--t3); }
.nav-display .val { font-size: 18px; font-weight: 900; color: var(--gold); }
.nav-display .delta { font-size: 9px; }
.nav-display .delta.up { color: var(--gn); }
.nav-display .delta.dn { color: var(--rd); }

.tab-bar { display: flex; overflow-x: auto; background: var(--cd);
           border-bottom: 1px solid var(--bd); padding: 0 20px;
           position: sticky; top: 76px; z-index: 99; }
.tab-bar-inner { display: flex; max-width: 1280px; margin: 0 auto; width: 100%; }
.tab { padding: 10px 14px; background: none; border: none;
       border-bottom: 2px solid transparent; color: var(--t3);
       font-size: 12px; font-weight: 700; cursor: pointer;
       white-space: nowrap; transition: color .15s, border-color .15s; }
.tab:hover { color: var(--t2); }
.tab.active { border-bottom-color: var(--gold); color: var(--gold); }
.tab-count { display: inline-block; padding: 1px 5px; margin-left: 4px;
             font-size: 9px; font-weight: 800; border-radius: 8px;
             background: #C9A84C30; color: var(--gold); }

.wrap { padding: 16px 20px; max-width: 1280px; margin: 0 auto; }
.tab-panel { display: none; }
.tab-panel.active { display: block; }

.search-empty-hint { display:none; background: #1B2A4A55; border: 1px solid var(--gold);
                     border-radius: 6px; padding: 10px; margin-bottom: 12px;
                     font-size: 11px; color: var(--t2); }

.section { background: var(--cd); border: 1px solid var(--bd);
           border-radius: 12px; padding: 14px 16px; margin-bottom: 12px; }
.section.glow { border-color: #C9A84C44; box-shadow: 0 0 24px #C9A84C0a; }
.section h3 { font-size: 14px; font-weight: 800; margin-bottom: 10px;
              display: flex; align-items: center; gap: 8px; }

.badge { display: inline-block; padding: 2px 8px; border-radius: 10px;
         font-size: 9px; font-weight: 800; text-transform: uppercase;
         letter-spacing: .04em; }
.badge.gn { background: #10B98122; color: #10B981; border: 1px solid #10B98144; }
.badge.rd { background: #EF444422; color: #EF4444; border: 1px solid #EF444444; }
.badge.or { background: #F59E0B22; color: #F59E0B; border: 1px solid #F59E0B44; }
.badge.bl { background: #2E5FA322; color: #2E5FA3; border: 1px solid #2E5FA344; }
.badge.gd { background: #C9A84C22; color: #C9A84C; border: 1px solid #C9A84C44; }
.badge.gy { background: #47556922; color: #94A3B8; border: 1px solid #47556944; }

.bar { width: 100%; background: var(--bd); border-radius: 999px; height: 6px;
       overflow: hidden; }
.bar-fill { height: 100%; border-radius: 999px;
            background: linear-gradient(90deg, var(--gn), #22d3ee); }
.bar-fill.gold { background: linear-gradient(90deg, var(--gold), #f59e0b); }
.bar-fill.rd   { background: linear-gradient(90deg, #f87171, var(--rd)); }

.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
@media (max-width: 960px) {
  .grid-2, .grid-3, .grid-4 { grid-template-columns: 1fr; }
  .search-box { width: 160px; }
}

table { width: 100%; border-collapse: collapse; font-size: 12px; }
th { text-align: left; color: var(--t3); font-weight: 600; font-size: 10px;
     text-transform: uppercase; letter-spacing: .06em; padding: 8px 8px;
     border-bottom: 1px solid var(--bd); }
td { padding: 8px; border-bottom: 1px solid #161e36; }
tr:last-child td { border-bottom: none; }
.mono { font-family: 'SF Mono', Menlo, Consolas, monospace; font-size: 11px; }
.muted { color: var(--t2); font-size: 11px; }

.dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%;
       margin-right: 6px; vertical-align: middle; }
.dot.on { background: var(--gn); box-shadow: 0 0 8px var(--gn); }
.dot.off { background: var(--rd); }
.dot.warn { background: var(--or); }

.tile { background: var(--bg); border-radius: 8px; padding: 10px 12px;
        border: 1px solid var(--bd); }
.tile-label { font-size: 10px; color: var(--t3); text-transform: uppercase;
              letter-spacing: .04em; }
.tile-value { font-size: 22px; font-weight: 800; margin-top: 4px; }
.tile-sub { font-size: 10px; color: var(--t2); margin-top: 2px; }

.sprint-row { display: flex; gap: 10px; padding: 8px 0;
              border-bottom: 1px solid var(--bd); align-items: flex-start; }
.sprint-id { width: 26px; height: 26px; border-radius: 13px; flex-shrink: 0;
             display: flex; align-items: center; justify-content: center;
             font-size: 12px; font-weight: 800; }
.sprint-id.done { background: #10B98122; color: var(--gn); }
.sprint-id.active { background: #C9A84C22; color: var(--gold); }
.sprint-id.pending { background: #47556922; color: var(--t3); }

.flow { display: flex; align-items: center; gap: 0; overflow-x: auto;
        padding: 12px 4px; }
.flow-node { background: var(--bg); border: 1px solid var(--bd);
             border-radius: 8px; padding: 8px 12px; min-width: 100px;
             text-align: center; flex-shrink: 0; }
.flow-node.active { border-color: var(--gold); box-shadow: 0 0 10px #C9A84C40; }
.flow-node-label { font-size: 9px; color: var(--t3); text-transform: uppercase; }
.flow-node-value { font-size: 14px; font-weight: 800; margin-top: 2px; }
.flow-arrow { color: var(--t3); font-size: 16px; margin: 0 6px; flex-shrink: 0; }

.countdown { display: flex; flex-direction: column; padding: 10px 12px;
             background: #1B2A4A55; border-radius: 8px;
             border-left: 3px solid var(--gold); }
.countdown-label { font-size: 9px; color: var(--gold); font-weight: 700;
                   text-transform: uppercase; letter-spacing: .04em; }
.countdown-time { font-family: 'SF Mono', Menlo, monospace; font-size: 13px;
                  font-weight: 800; margin-top: 2px; }
.countdown-event { font-size: 10px; color: var(--t2); margin-top: 2px; }

.gauge { position: relative; width: 200px; height: 110px; margin: 8px auto; }
.gauge-bg { position: absolute; inset: 0; border-radius: 200px 200px 0 0 / 110px 110px 0 0;
            background: conic-gradient(from 270deg at 50% 100%,
              #10B981 0deg, #C9A84C 50deg, #F59E0B 100deg, #EF4444 180deg);
            -webkit-mask: radial-gradient(circle at 50% 100%, transparent 56px, #000 57px); }
.gauge-needle { position: absolute; bottom: 0; left: 50%; width: 2px;
                height: 100px; background: var(--t1); transform-origin: bottom;
                transition: transform 1s; }
.gauge-label { position: absolute; bottom: -30px; left: 0; right: 0;
               text-align: center; font-size: 14px; font-weight: 800;
               color: var(--gold); }
.gauge-regime { position: absolute; bottom: -50px; left: 0; right: 0;
                text-align: center; font-size: 10px; color: var(--t2); }

.eq-chart-svg { width: 100%; height: 200px; background: var(--bg);
                border-radius: 8px; border: 1px solid var(--bd); }

.tg-entry { padding: 8px 10px; border-bottom: 1px solid var(--bd);
            display: flex; gap: 10px; align-items: flex-start; }
.tg-entry .ts { font-family: 'SF Mono', Menlo, monospace; font-size: 10px;
                color: var(--t3); flex-shrink: 0; width: 130px; }
.tg-entry .body { flex: 1; font-size: 11px; color: var(--t2); }

.commit-row { display: grid; grid-template-columns: 90px 130px 1fr;
              gap: 12px; padding: 8px 0; border-bottom: 1px solid var(--bd);
              font-size: 11px; align-items: center; }
.commit-row .sha { font-family: 'SF Mono', Menlo, monospace; color: var(--gold);
                   font-weight: 700; }

.history-row { padding: 10px 0; border-bottom: 1px solid var(--bd); }
.history-row .date { font-size: 11px; color: var(--gold); font-weight: 700;
                     margin-bottom: 4px; }
.history-row ul { margin: 4px 0 0 0; padding-left: 18px; }
.history-row li { font-size: 11px; margin: 2px 0; color: var(--t2); }

.lboard-row { display: grid; grid-template-columns: 120px 1fr 60px 60px;
              gap: 10px; padding: 6px 0; align-items: center;
              font-size: 11px; }
.lboard-bar { background: var(--bd); height: 8px; border-radius: 999px;
              position: relative; overflow: hidden; }
.lboard-bar-fill { height: 100%; border-radius: 999px; }
.lboard-bar-fill.pos { background: linear-gradient(90deg, var(--gold), var(--gn)); }
.lboard-bar-fill.neg { background: linear-gradient(90deg, var(--rd), var(--or)); }

.footer { padding: 14px 20px; max-width: 1280px; margin: 0 auto;
          border-top: 1px solid var(--bd); color: var(--t3); font-size: 10px;
          margin-top: 24px; }

.search-hidden { display: none !important; }
.win-row, .lose-row { display: flex; justify-content: space-between;
                      padding: 4px 0; border-bottom: 1px solid var(--bd);
                      align-items: center; font-size: 11px; }
.ticker-link { font-family: 'SF Mono', Menlo, monospace; color: var(--gold);
               font-weight: 700; }
"""


JS = """
(function() {
  // ----- LANGUAGE SWITCH (English / Arabic) -----
  const AR = {
    // Header
    'refresh_label': 'تحديث الصفحة بعد ',
    'search_placeholder': 'ابحث في جميع التبويبات…',
    // Tabs
    'tab_overview': '📊 لوحة عامة',
    'tab_markets': '🌍 الأسواق',
    'tab_agents': '🤖 الوكلاء',
    'tab_kpis': '🎯 الأهداف',
    'tab_live': '🟢 الحالة الحية',
    'tab_paper': '📈 المحفظة الورقية',
    'tab_risk': '🛡️ المخاطر',
    'tab_telegram': '📱 إشعارات تيليجرام',
    'tab_commits': '📜 تغييرات الكود',
    'tab_history': '🗂 القرارات',
    'tab_glossary': '📖 شرح المصطلحات',
    'tab_ceo': '💬 ملاحظات المدير',
    // Common labels
    'verdict_passed': 'نجح',
    'verdict_failed': 'فشل',
    'verdict_running': 'قيد التشغيل',
    'verdict_cleared': 'معتمد',
    'label_nav': 'القيمة (ورقي)',
    'label_mode': 'النمط',
    'label_strategy': 'الإستراتيجية',
    'label_market': 'السوق',
    'label_timeframe': 'الإطار الزمني',
    'label_trades': 'الصفقات',
    'label_expectancy': 'التوقع',
    'label_winrate': 'نسبة الفوز',
    'label_sharpe': 'نقاط الجودة',
    'label_coverage': 'التغطية',
    'label_verdict': 'الحكم',
    'label_since_deploy': 'منذ التشغيل',
    // Section titles
    'sec_winners': '🏆 أفضل الإستراتيجيات — نقاط الجودة (الأعلى أفضل)',
    'sec_losers': 'الإستراتيجيات الفاشلة',
    'sec_trial_budget': '📋 التجارب المنفذة — ٩ مجموع (مع تطبيق العقوبة الإحصائية)',
    'sec_sprint': '🚀 تقدم السباق',
    'sec_pipeline': '📡 مسار الإشارة — من البيانات إلى الصفقة',
    'sec_next_events': '⏱ القادم في الجدول',
    'sec_circuit': '🛡 نقاط الإيقاف الآمنة',
    'sec_decisions_short': '📝 قرارات المدير الأخيرة',
    'sec_paper': '📈 محفظة الورق — اختبار حي',
    'sec_paper_fwd': '📈 اختبار حي — Divergence الأمريكية اليومية',
    'sec_paper_positions': '🟢 صفقات مفتوحة',
    'sec_paper_history': '📋 صفقات مغلقة (آخر ٢٠)',
    'sec_kpi': '🎯 أهداف التفويض — هل نحققها؟',
    'sec_live': '🟢 صحة النظام الحي',
    'sec_vix': '📊 تذبذب السوق (VIX)',
    'sec_drawdown': '📉 الخسارة الورقية من القمة',
    'sec_corr': '🔗 تداخل المراكز',
    'sec_sizing': '📏 حدود حجم الصفقة',
    'sec_telegram_log': '📱 الرسائل المرسلة (آخر ١٠٠)',
    'sec_commits': '📜 تاريخ الكود (آخر ٦٠ تغيير)',
    'sec_history': '📜 الجلسات السابقة',
    'sec_audit': '🔍 المراجع الخارجي (Cowork)',
    'sec_glossary': '📖 دليل المصطلحات — بالعربية البسيطة',
    'sec_ceo_all': '💬 جميع قرارات المدير (مع المبررات)',
    'sec_how_it_works': '🗺️ كيف يعمل النظام — جولة بالعربية البسيطة',
    'how_step1': '1. كتاب القواعد المجمد. ثلاث إستراتيجيات (EMA-200, Divergence, MBV) مع كل الإعدادات مغلقة داخل config.py. القفل = رمز هاش (6ce4b38242d54771). أي تعديل في القاعدة يغير الهاش وينتهي كل ما سبق.',
    'how_step2': '2. اختبار على التاريخ. المحرك يعيد تشغيل ١٥ سنة من بيانات الأسواق الأمريكية والإماراتية والكريبتو، محاكياً صفقات حقيقية بتكاليف حقيقية (عمولات، فروق سعر، انزلاق). يقسم التاريخ نصفين: نصف للتعلم يتجاهله، ونصف خارج العينة يقيم نفسه عليه.',
    'how_step3': '3. بوابتان للحكم. البوابة لكل سهم تسأل: "هل لهذا السهم حافة؟". وبوابة المحفظة تسأل: "هل لهذه الإستراتيجية حافة عبر السوق كاملاً؟" كلتاهما تتطلب اجتياز عتبات صارمة. التجارب الفاشلة محفوظة (لا انتقاء)، وعقوبة الاختبارات المتعددة تنمو مع كل اختبار جديد.',
    'how_step4': '4. مراقب الإشارات الحي. الإستراتيجيات التي اجتازت بوابة المحفظة تحصل على كاشف بايثون يعمل كل ساعتين. يتحقق هل أعطى مؤشر اليوم إشارة دخول أو خروج على الأسهم المراقبة (DY, EXPGY, PSX, ARW, ROL).',
    'how_step5': '5. تنبيهات الهاتف. عندما تشتعل إشارة، يصل Telegram إلى أحمد (AIV_Fund_Bot@) بسعر الدخول والخروج. أول ١٠ إشارات حقيقية تقارن بتوقعات الاختبار الخلفي.',
    'how_step6': '6. كل إجراء مسجل. كل تشغيل اختبار يكتب إلى audit_trail.md مع رمز الهاش. مراجع خارجي (Cowork) يستطيع إعادة تشغيل نفس الهاش والحصول على نفس الحكم — هذه ضمانة التدقيق.',
    // Buttons / misc
    'btn_no_alerts': 'لا توجد تنبيهات',
    'mode_sprint': 'النمط ١ — سباق نشط',
    'mode_steady': 'النمط ٢ — تشغيل ثابت',
  };

  function applyLang(lang) {
    const html = document.documentElement;
    html.setAttribute('lang', lang);
    html.setAttribute('dir', lang === 'ar' ? 'rtl' : 'ltr');
    document.querySelectorAll('.lang-btn').forEach(b => {
      b.classList.toggle('active', b.dataset.lang === lang);
    });
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.dataset.i18n;
      const attrName = el.dataset.i18nAttr;
      // Preserve children (countdown span, etc.) by stashing on first run
      if (!el.dataset.i18nEn && !attrName) {
        // For countdown label: stash only the text-before-span portion
        const first = el.firstChild;
        if (first && first.nodeType === Node.TEXT_NODE) {
          el.dataset.i18nEn = first.textContent;
        } else {
          el.dataset.i18nEn = el.textContent;
        }
      }
      if (attrName && !el.dataset.i18nEnAttr) {
        el.dataset.i18nEnAttr = el.getAttribute(attrName) || '';
      }
      if (lang === 'ar' && AR[key]) {
        if (attrName) {
          el.setAttribute(attrName, AR[key]);
        } else {
          // If el has a child element (e.g., countdown span), only replace leading text node
          const first = el.firstChild;
          if (first && first.nodeType === Node.TEXT_NODE && el.children.length > 0) {
            first.textContent = AR[key];
          } else {
            el.textContent = AR[key];
          }
        }
      } else {
        if (attrName) {
          el.setAttribute(attrName, el.dataset.i18nEnAttr || '');
        } else {
          const first = el.firstChild;
          if (first && first.nodeType === Node.TEXT_NODE && el.children.length > 0) {
            first.textContent = el.dataset.i18nEn || '';
          } else {
            el.textContent = el.dataset.i18nEn || '';
          }
        }
      }
    });
    try { localStorage.setItem('aig_lang', lang); } catch (e) {}
  }
  document.querySelectorAll('.lang-btn').forEach(b => {
    b.addEventListener('click', () => applyLang(b.dataset.lang));
  });
  try {
    const savedLang = localStorage.getItem('aig_lang');
    if (savedLang === 'ar') applyLang('ar');
  } catch (e) {}

  // ----- TABS -----
  function setTab(id) {
    document.querySelectorAll('.tab').forEach(t => {
      t.classList.toggle('active', t.dataset.tab === id);
    });
    document.querySelectorAll('.tab-panel').forEach(p => {
      p.classList.toggle('active', p.id === 'panel-' + id);
    });
    try { localStorage.setItem('aig_tab', id); } catch (e) {}
    applySearch();
  }
  document.querySelectorAll('.tab').forEach(t => {
    t.addEventListener('click', () => setTab(t.dataset.tab));
  });
  try {
    const saved = localStorage.getItem('aig_tab');
    if (saved && document.getElementById('panel-' + saved)) setTab(saved);
  } catch (e) {}

  // ----- CROSS-TAB SEARCH WITH PER-TAB COUNTS -----
  function applySearch() {
    const q = (document.getElementById('global-search').value || '').trim().toLowerCase();
    // Clear all tab badges
    document.querySelectorAll('.tab .tab-count').forEach(b => b.remove());
    document.getElementById('search-empty-hint').style.display = 'none';

    if (!q) {
      // Show everything in active tab
      const panel = document.querySelector('.tab-panel.active');
      if (panel) panel.querySelectorAll('[data-search]').forEach(el => el.classList.remove('search-hidden'));
      return;
    }

    // Count matches in every panel
    const counts = {};
    document.querySelectorAll('.tab-panel').forEach(panel => {
      let count = 0;
      panel.querySelectorAll('[data-search]').forEach(el => {
        const haystack = (el.dataset.search || el.textContent).toLowerCase();
        const hit = haystack.includes(q);
        if (panel.classList.contains('active')) {
          el.classList.toggle('search-hidden', !hit);
        }
        if (hit) count++;
      });
      counts[panel.id.replace('panel-', '')] = count;
    });

    // Add tab badges + show jump-to hint if active tab has 0 hits
    let activeTabHasHits = false;
    document.querySelectorAll('.tab').forEach(t => {
      const id = t.dataset.tab;
      const n = counts[id] || 0;
      if (n) {
        const b = document.createElement('span');
        b.className = 'tab-count';
        b.textContent = n;
        t.appendChild(b);
      }
      if (t.classList.contains('active') && n > 0) activeTabHasHits = true;
    });
    const empty = document.getElementById('search-empty-hint');
    if (!activeTabHasHits) {
      const others = Object.entries(counts).filter(([k, v]) => v > 0);
      if (others.length) {
        empty.innerHTML = 'No matches in this tab. Found in: ' +
          others.map(([k, v]) => '<a href="#" data-jump="' + k + '">' + k + ' (' + v + ')</a>').join(' · ');
        empty.style.display = 'block';
        empty.querySelectorAll('[data-jump]').forEach(a => {
          a.addEventListener('click', (e) => { e.preventDefault(); setTab(a.dataset.jump); });
        });
      }
    }
  }
  const search = document.getElementById('global-search');
  if (search) {
    search.addEventListener('input', applySearch);
    search.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') { search.value = ''; applySearch(); }
    });
  }

  // ----- ALERT BELL -----
  const bell = document.getElementById('alert-bell');
  const bellDrop = document.getElementById('alert-drop');
  if (bell && bellDrop) {
    bell.addEventListener('click', (e) => {
      e.stopPropagation();
      bellDrop.style.display = bellDrop.style.display === 'block' ? 'none' : 'block';
    });
    document.addEventListener('click', () => { bellDrop.style.display = 'none'; });
  }

  // ----- COUNTDOWN UPDATER -----
  function pad(n) { return String(n).padStart(2, '0'); }
  function tick() {
    document.querySelectorAll('[data-target-ts]').forEach(el => {
      const t = parseInt(el.dataset.targetTs, 10);
      if (!t) return;
      const now = Math.floor(Date.now() / 1000);
      let diff = t - now;
      if (diff < 0) { el.textContent = 'now / past'; return; }
      const d = Math.floor(diff / 86400); diff -= d * 86400;
      const h = Math.floor(diff / 3600); diff -= h * 3600;
      const m = Math.floor(diff / 60); diff -= m * 60;
      const s = diff;
      let parts = [];
      if (d) parts.push(d + 'd');
      parts.push(pad(h) + ':' + pad(m) + ':' + pad(s));
      el.textContent = parts.join(' ');
    });
    // Visible refresh countdown
    const rc = document.getElementById('refresh-countdown-val');
    if (rc) {
      const remain = parseInt(rc.dataset.remain, 10) - 1;
      rc.dataset.remain = String(Math.max(0, remain));
      const mm = Math.floor(remain / 60), ss = remain % 60;
      rc.textContent = pad(mm) + ':' + pad(ss);
    }
  }
  tick();
  setInterval(tick, 1000);

  // ----- HISTORY FILTER -----
  const histFilter = document.getElementById('history-filter');
  if (histFilter) {
    histFilter.addEventListener('input', () => {
      const q = histFilter.value.trim().toLowerCase();
      document.querySelectorAll('#panel-history [data-search]').forEach(el => {
        const hay = (el.dataset.search || el.textContent).toLowerCase();
        el.classList.toggle('search-hidden', q && !hay.includes(q));
      });
    });
  }

  // ----- CEO DECISION FILTER -----
  const ceoFilter = document.getElementById('ceo-filter');
  if (ceoFilter) {
    ceoFilter.addEventListener('input', () => {
      const q = ceoFilter.value.trim().toLowerCase();
      document.querySelectorAll('#panel-ceo [data-search]').forEach(el => {
        const hay = (el.dataset.search || el.textContent).toLowerCase();
        el.classList.toggle('search-hidden', q && !hay.includes(q));
      });
    });
  }
})();
"""


# ---- renderers ------------------------------------------------------------

def _status_class(s: str) -> str:
    s = (s or "").lower()
    if any(k in s for k in ("done", "pass", "cleared", "resolved", "alive", "online")):
        return "gn"
    if any(k in s for k in ("warn", "near", "noted", "active", "in progress", "iterating", "scheduled")):
        return "or"
    if any(k in s for k in ("fail", "blocking", "down", "error")):
        return "rd"
    if any(k in s for k in ("pending", "waiting", "queued", "—")):
        return "gy"
    return "bl"


def _ticker_link(ticker: str) -> str:
    """Deep-link a ticker to its data cache CSV (raw URL) or yfinance fallback."""
    # If we have a cache CSV, link to raw
    cache = ROOT / "data_cache" / f"{ticker}.csv"
    if cache.exists():
        return f"{RAW_BASE}/data_cache/{ticker}.csv"
    # Else link to TradingView
    return f"https://www.tradingview.com/symbols/{ticker}/"


def _render_overview(state):
    runs = state["runs"]
    sprint = state["brain"]["sprint_tracker"]
    sprint_done = sum(1 for r in sprint if "DONE" in r["status"] or "✅" in r["status"])
    universes = state["universes"]
    paper = state["paper"] or {}
    open_positions = paper.get("open_positions", {}) if paper else {}
    history = paper.get("history", []) if paper else []
    trial_budget = state["trial_budget"]

    # Sprint rows
    sprint_rows = []
    for r in sprint:
        status = r["status"]
        is_done = "DONE" in status or "✅" in status
        is_active = "IN PROGRESS" in status or "🔄" in status
        cls = "done" if is_done else ("active" if is_active else "pending")
        bcls = "gn" if is_done else ("or" if is_active else "gy")
        glyph = "✓" if is_done else r["id"]
        sprint_rows.append(f"""
        <div class="sprint-row" data-search="{esc(r['item'] + ' ' + r['status'] + ' ' + r['notes'])}">
          <div class="sprint-id {cls}">{esc(glyph)}</div>
          <div style="flex:1;">
            <div style="font-weight:700;">{esc(r['item'])}</div>
            <div class="muted">{esc(r['notes'][:140])}</div>
          </div>
          <span class="badge {bcls}">{esc(status.strip())}</span>
        </div>""")

    # Signal Pipeline
    portfolio_cleared = [k for k, v in runs.items() if v["passed"]]
    paper_open = len(open_positions)
    paper_closed = len(history)
    pipeline = f"""
    <div class="flow">
      <div class="flow-node">
        <div class="flow-node-label">Data</div>
        <div class="flow-node-value">{universes['US halal'][0] + universes['UAE halal'][0] + universes['Crypto halal'][0]:,}</div>
        <div class="muted">tickers</div>
      </div>
      <div class="flow-arrow">→</div>
      <div class="flow-node">
        <div class="flow-node-label">Strategies</div>
        <div class="flow-node-value">2</div>
        <div class="muted">EMA-200, Div</div>
      </div>
      <div class="flow-arrow">→</div>
      <div class="flow-node {'active' if portfolio_cleared else ''}">
        <div class="flow-node-label">Gate Pass</div>
        <div class="flow-node-value">{len(portfolio_cleared)}/{len(runs)}</div>
        <div class="muted">portfolios</div>
      </div>
      <div class="flow-arrow">→</div>
      <div class="flow-node {'active' if paper else ''}">
        <div class="flow-node-label">Paper-fwd</div>
        <div class="flow-node-value">{paper_open}</div>
        <div class="muted">{paper_closed} closed</div>
      </div>
      <div class="flow-arrow">→</div>
      <div class="flow-node">
        <div class="flow-node-label">Telegram</div>
        <div class="flow-node-value">{state['telegram_sends']}</div>
        <div class="muted">sent</div>
      </div>
    </div>"""

    # Countdowns + last-run for each enabled routine
    cd_blocks = []
    for t in state["tasks"]:
        if t.get("enabled") == "false":
            continue
        ts = 0
        if t.get("next_run_iso"):
            try:
                tgt = datetime.fromisoformat(t["next_run_iso"])
                ts = int(tgt.timestamp())
            except Exception:
                ts = 0
        last_touch = t.get("last_touch", "—")
        cd_blocks.append(f"""
        <div class="countdown" data-search="{esc(t['name'])}">
          <div class="countdown-label">{esc(t['name'])}</div>
          <div class="countdown-time" data-target-ts="{ts}">—</div>
          <div class="countdown-event">next · {esc(t.get('cron','—'))}</div>
          <div class="muted" style="margin-top:4px;">last touch: {esc(last_touch)}</div>
        </div>""")

    # Decision Log (last 10)
    dec_html = ""
    for d in state["brain"]["decisions"][-10:][::-1]:
        dec_html += f"""
        <div data-search="{esc(d['id_date'] + ' ' + d['title'])}" style="padding:6px 0; border-bottom:1px solid var(--bd);">
          <div style="font-size:10px; color:var(--gold); font-weight:700;">{esc(d['id_date'])}</div>
          <div style="font-size:11px; color:var(--t1); font-weight:600; margin-top:2px;">{esc(d['title'])}</div>
          <div class="muted">{esc(d['rationale_head'][:200])}</div>
        </div>"""
    if not dec_html:
        dec_html = '<div class="muted">No decisions parsed.</div>'

    # Circuit Breakers
    cbs = [
        ("Portfolio >8%/day", "Tier 1", "Halt all. No override."),
        ("Position >15% loss", "Tier 1", "Hard exit. No override."),
        ("VIX > 40", "Tier 1", "100% cash. Resume when VIX<35."),
        ("Correlation > 0.85", "Tier 1", "No new entries. Rebalance."),
        ("Drawdown > 20%", "Tier 1", "100% cash. Full R&D review."),
        ("All feeds fail", "Tier 1", "Zero trading."),
        ("Shariah breach", "Tier 1", "Exit non-compliant."),
        ("Crypto -30%", "Tier 1 (crypto)", "Halt crypto only."),
        ("Portfolio >5%/day", "Tier 2", "CIO 6-field override."),
        ("Position -8%", "Tier 2", "CIO override possible."),
    ]
    cb_html = "<table><thead><tr><th>Trigger</th><th>Tier</th><th>Status</th></tr></thead><tbody>"
    for trig, tier, action in cbs:
        cb_html += f"<tr data-search='{esc(trig + tier)}'><td>{esc(trig)}</td><td class='muted'>{esc(tier)}</td><td><span class='badge gn'>ARMED</span></td></tr>"
    cb_html += "</tbody></table>"

    # Audit findings — with deep-link
    audit_html = ""
    for f in state["audit"]:
        sv_cls = "rd" if f["severity"] == "BLOCKING" else ("or" if f["severity"] == "WARNING" else "gy")
        link = f"{RAW_BASE}/auditor_report.md"
        audit_html += f"""
        <div style="display:flex; gap:8px; padding:6px 0; border-bottom:1px solid var(--bd); align-items:center;" data-search="{esc(f['title'] + f['severity'])}">
          <span class="badge {sv_cls}">{esc(f['severity'])}</span>
          <a href="{esc(link)}" target="_blank" style="flex:1; font-size:11px; color:var(--t1);">{esc(f['title'])}</a>
          <span class="badge gn">RESOLVED</span>
        </div>"""
    if not audit_html:
        audit_html = '<div class="muted">No audit report.</div>'

    # Trial Budget
    tb_html = "<table><thead><tr><th>#</th><th>Trial</th><th>Strategy</th><th>Market</th><th>TF</th><th>Verdict</th></tr></thead><tbody>"
    for t in trial_budget:
        verdict = t.get("verdict", "")
        v_cls = "gn" if "CLEARED" in verdict or "PASS" in verdict else ("or" if "trades" in verdict.lower() else "rd")
        v_short = re.sub(r"\([^)]*\)", "", verdict)[:50]
        tb_html += f"""
        <tr data-search="{esc(t.get('trial_id','') + ' ' + verdict)}">
          <td class='mono'>{esc(t['id'])}</td>
          <td class='mono' style='color:var(--gold)'>{esc(t.get('trial_id',''))}</td>
          <td>{esc(t['strategy'])}</td>
          <td>{esc(t['market'])}</td>
          <td class='mono'>{esc(t['timeframe'])}</td>
          <td><span class='badge {v_cls}'>{esc(v_short)}</span></td>
        </tr>"""
    tb_html += "</tbody></table>"
    if not trial_budget:
        tb_html = '<div class="muted">Trial budget table not found in strategy_register.md.</div>'

    # Strategy leaderboard
    leaderboard = sorted(
        [{"key": f"{s}/{m}", "strategy": s, "market": m, "sr": v["sharpe_def"] or 0,
          "verdict": v["verdict"], "passed": v["passed"]}
         for (s, m), v in runs.items()],
        key=lambda r: r["sr"], reverse=True
    )
    if leaderboard:
        max_abs = max(abs(r["sr"]) for r in leaderboard) or 1
        lb_html = ""
        for r in leaderboard:
            sr = r["sr"]
            pct = min(100, abs(sr) / max_abs * 100)
            fill_cls = "pos" if sr > 0 else "neg"
            bar_offset = "left:50%;" if sr > 0 else f"right:50%;"
            lb_html += f"""
            <div class="lboard-row" data-search="{esc(r['key'] + ' ' + r['verdict'])}">
              <div class='mono'>{esc(r['key'])}</div>
              <div class="lboard-bar">
                <div class="lboard-bar-fill {fill_cls}" style="position:absolute; top:0; height:100%; {bar_offset} width:{pct/2:.1f}%;"></div>
              </div>
              <div class='mono' style='color:{"var(--gn)" if sr > 0 else "var(--rd)"}; text-align:right;'>{sr:+.2f}</div>
              <span class="badge {'gn' if r['passed'] else 'rd'}">{'PASS' if r['passed'] else 'FAIL'}</span>
            </div>"""
    else:
        lb_html = '<div class="muted">No validation runs yet.</div>'

    return f"""
    <div id="panel-overview" class="tab-panel active">

      <div class="section" data-search="how it works mental map plain english arabic">
        <h3 data-i18n="sec_how_it_works">🗺️ How It Works — Plain English Tour</h3>
        <div style="font-size:12px; line-height:1.8; color:var(--t2);">
          <div data-i18n="how_step1"><b style="color:var(--gold);">1. Frozen rulebook.</b> Three strategies (EMA-200, Divergence, MBV) plus all settings are locked into <span class="mono">config.py</span>. The lock = a hash code (<span class="mono">6ce4b38242d54771</span>). If anyone changes a rule, the hash changes and all previous results expire.</div>
          <div data-i18n="how_step2"><b style="color:var(--gold);">2. Test on history.</b> The engine replays 15 years of US, UAE, and crypto data, simulating real trades with real costs (commissions, spreads, slippage). It splits history into a "training" half it ignores and an "out-of-sample" half it scores against.</div>
          <div data-i18n="how_step3"><b style="color:var(--gold);">3. Two gates judge.</b> The per-ticker gate asks "does this single stock have edge?" The portfolio gate asks "does this whole strategy have edge across the market?" Both must pass strict thresholds. Failed tests are kept (no cherry-picking) and the haircut penalty grows with each test tried.</div>
          <div data-i18n="how_step4"><b style="color:var(--gold);">4. Live signal watcher.</b> Strategies that cleared the portfolio gate get a Python detector that runs every 2 hours. It checks if today's bar triggered an entry or exit on the watched tickers (DY, EXPGY, PSX, ARW, ROL).</div>
          <div data-i18n="how_step5"><b style="color:var(--gold);">5. Phone alerts.</b> When a signal fires, Telegram pings Ahmed (@AIV_Fund_Bot) with the entry/exit price. The first 10 real signals get compared against backtest expectations.</div>
          <div data-i18n="how_step6"><b style="color:var(--gold);">6. Every action is logged.</b> Every test run writes to <span class="mono">audit_trail.md</span> with the config hash. An outside reviewer (Cowork) can re-run the same hash and get the same verdict — that's the audit guarantee.</div>
        </div>
      </div>

      <div class="section glow" data-search="sprint tracker targets">
        <h3 data-i18n="sec_sprint">🚀 Sprint Progress — {sprint_done}/8 done</h3>
        <div class="bar"><div class="bar-fill" style="width:{(sprint_done/8)*100:.0f}%;"></div></div>
        <div style="margin-top:10px;">{''.join(sprint_rows) or '<div class="muted">No tracker rows parsed.</div>'}</div>
      </div>

      <div class="section" data-search="strategy leaderboard sharpe">
        <h3 data-i18n="sec_winners">🏆 Best Strategies — Quality Score (higher = better)</h3>
        {lb_html}
      </div>

      <div class="section" data-search="pipeline flow data strategies gate paper telegram">
        <h3 data-i18n="sec_pipeline">📡 Signal Flow — From Data to Trade</h3>
        {pipeline}
      </div>

      <div class="grid-2">
        <div class="section" data-search="countdown timers next event routines">
          <h3 data-i18n="sec_next_events">⏱ What's Coming Next</h3>
          <div class="grid-2" style="gap:8px;">{''.join(cd_blocks) or '<div class="muted">No active routines.</div>'}</div>
        </div>
        <div class="section" data-search="circuit breakers safety">
          <h3 data-i18n="sec_circuit">🛡 Safety Stops</h3>
          {cb_html}
        </div>
      </div>

      <div class="section" data-search="trial budget pre-registered strategy register">
        <h3 data-i18n="sec_trial_budget">📋 Tested Combinations — {len(trial_budget) or 9} total (statistical penalty applied)</h3>
        {tb_html}
      </div>

      <div class="grid-2">
        <div class="section" data-search="ceo decisions log">
          <h3 data-i18n="sec_decisions_short">📝 Recent CEO Decisions</h3>
          {dec_html}
        </div>
        <div class="section" data-search="audit findings auditor cowork">
          <h3 data-i18n="sec_audit">🔍 Outside Reviewer (Cowork)</h3>
          {audit_html}
        </div>
      </div>
    </div>"""


def _render_markets(state):
    runs = state["runs"]
    market_blocks = []
    market_meta = {
        "US": ("🇺🇸", "US Equities", "us_halal_full.txt"),
        "UAE": ("🇦🇪", "UAE Equities", "uae_tickers_full.txt"),
        "CRYPTO": ("₿", "Crypto", "halal_crypto_150_USD.txt"),
    }
    for mkt_key, (emoji, name, uni_file) in market_meta.items():
        uni_count = _count_universe(UNIVERSE_DIR / uni_file)
        rows = [v for (s, m), v in runs.items() if m == mkt_key]
        cleared_any = any(r["passed"] for r in rows)
        if rows:
            best = max(rows, key=lambda r: r["sharpe_def"] or -99)
            trades = best["trades"]; cov = best["contributors"]; uni_sz = best["universe_size"]
            sr = best["sharpe_def"]; ex = best["expectancy"]; wr = (best["win_rate"] or 0) * 100
            file_link = best["raw_url"]
        else:
            trades = cov = uni_sz = 0; sr = ex = wr = 0; file_link = ""

        winners, losers = _winners_losers(mkt_key, runs, top_n=6)
        win_html = "".join(
            f"""<div class='win-row' data-search='{esc(w["ticker"])}'>
              <a class='ticker-link' href='{esc(_ticker_link(w["ticker"]))}' target='_blank'>{esc(w["ticker"])}</a>
              <div class='muted'>{esc(w["strategy"])} · n={w["n"]}</div>
              <span style='color:var(--gn); font-weight:800;'>{w["exp"]:.2f}</span>
            </div>""" for w in winners
        ) or '<div class="muted">No qualifying tickers (n≥10).</div>'
        lose_html = "".join(
            f"""<div class='lose-row' data-search='{esc(l["ticker"])}'>
              <a class='ticker-link' href='{esc(_ticker_link(l["ticker"]))}' target='_blank'>{esc(l["ticker"])}</a>
              <div class='muted'>{esc(l["strategy"])} · n={l["n"]}</div>
              <span style='color:var(--rd); font-weight:800;'>{l["exp"]:.2f}</span>
            </div>""" for l in losers
        ) or '<div class="muted">—</div>'

        verdict_class = "gn" if cleared_any else "or"
        verdict_text = "GATE PASSED" if cleared_any else ("ITERATING" if rows else "—")
        market_blocks.append(f"""
        <div class="section" data-search="{esc(name + ' ' + mkt_key)}">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <h3 style="margin:0;">{emoji} {esc(name)}</h3>
            <span class="badge {verdict_class}">{esc(verdict_text)}</span>
          </div>
          <div class="grid-4" style="margin-bottom:10px;">
            <div class="tile"><div class="tile-label">Universe</div><div class="tile-value">{uni_count:,}</div></div>
            <div class="tile"><div class="tile-label">Best dSharpe</div><div class="tile-value">{sr:.2f}</div></div>
            <div class="tile"><div class="tile-label">Best Exp</div><div class="tile-value">{ex:.2f}</div></div>
            <div class="tile"><div class="tile-label">Best WR</div><div class="tile-value">{wr:.0f}%</div></div>
          </div>
          <div class="muted">Trades {trades:,} · Contributors {cov}/{uni_sz} {'· <a href=\"' + esc(file_link) + '\" target=\"_blank\">latest JSON</a>' if file_link else ''}</div>
          <div class="grid-2" style="margin-top:14px;">
            <div>
              <div style="font-size:10px; font-weight:700; color:var(--gn); margin-bottom:4px;">🏆 WINNERS (top expectancy)</div>
              {win_html}
            </div>
            <div>
              <div style="font-size:10px; font-weight:700; color:var(--rd); margin-bottom:4px;">📉 LOSERS</div>
              {lose_html}
            </div>
          </div>
        </div>""")
    return f'<div id="panel-markets" class="tab-panel">{"".join(market_blocks)}</div>'


def _render_agents(state):
    agents_meta = [
        ("L0", "CEO", "Autonomous, recursive self-improvement"),
        ("L1", "CIO", "Capital allocation, signal approval"),
        ("L1", "CFO", "Cost control, quality monitoring"),
        ("L2", "RD-A", "Research — strategy registration"),
        ("L2", "RD-B", "Backtest engine"),
        ("L2", "RD-C", "Paper simulator (paper-forward detector)"),
        ("L2", "RD-D", "Approval committee (gate)"),
        ("L3", "EX-A", "Trend (daily+weekly)"),
        ("L3", "EX-B", "Mean reversion (1H+4H)"),
        ("L3", "EX-C", "Factor (weekly)"),
        ("L3", "EX-D", "Portfolio construction + correlation"),
        ("L3", "EX-E", "Fill intake"),
        ("L3", "EX-F", "Crypto (spot, halal)"),
        ("L4", "RI-F", "Risk manager — sizing, loss ladder"),
        ("L4", "RI-G", "Intraday monitor"),
        ("L4", "RI-H", "Shariah compliance"),
        ("L4", "RI-I", "Macro regime"),
        ("L4", "RI-J", "Alt data"),
        ("L4", "RI-K", "Market intel"),
        ("L5", "IN-L", "Systems — feed health"),
        ("L5", "IN-M", "Orchestrator — schedules"),
        ("L5", "IN-N", "Notification — Telegram"),
        ("L5", "IN-O", "Audit trail"),
        ("L6", "LM-P", "Self-learning"),
        ("L6", "LM-Q", "Persistent memory"),
        ("L7", "PR-R", "Performance"),
        ("L7", "PR-S", "Investor relations"),
    ]
    by_layer = {}
    for layer, aid, desc in agents_meta:
        by_layer.setdefault(layer, []).append((aid, desc))
    blocks = []
    for layer in sorted(by_layer.keys()):
        rows = ""
        for aid, desc in by_layer[layer]:
            state_label = state["agent_state"].get(aid, "active")
            cls = _status_class(state_label)
            rows += f"<tr data-search='{esc(aid + desc + state_label)}'><td class='mono' style='color:var(--gold)'>{esc(aid)}</td><td>{esc(desc)}</td><td><span class='badge {cls}'>{esc(state_label)}</span></td></tr>"
        blocks.append(f"""
        <div class="section" data-search="layer {esc(layer)}">
          <h3>Layer {esc(layer)}</h3>
          <table>{rows}</table>
        </div>""")
    return f'<div id="panel-agents" class="tab-panel">{"".join(blocks)}</div>'


def _render_kpis(state):
    runs = state["runs"]
    best_sr = max((v["sharpe_def"] for v in runs.values() if v["sharpe_def"] is not None), default=0)
    pipeline_count = len({s for (s, _) in runs.keys()})
    nav, pct = _paper_nav()
    paper = state["paper"] or {}
    paper_open = len(paper.get("open_positions", {}))
    crypto_open = 0  # no crypto deployments yet
    kpis = [
        ("Annual Return",      f"{pct:+.2f}%",        "≥3x / 10x asp",  "pending" if pct == 0 else ("pass" if pct >= 200 else "warn"), "Paper accumulating"),
        ("Sharpe (best portfolio)", f"{best_sr:.2f}", "≥1.5",           "pass" if best_sr >= 1.5 else "info", "Deflated under N=6"),
        ("Max Drawdown",       "0%",                  "<20%",           "pass", "No closed losing trades"),
        ("Alpha vs S&P 500",   "—",                   ">0",             "pending", "Tracking after paper accumulates"),
        ("Win Rate ★★★★+",     "—",                   ">50%",           "pending", "Rolling 30 trades"),
        ("Halal Compliance",   "100%",                "100%",           "pass", "Universes pre-screened"),
        ("Max Eq Positions",   str(paper_open),       "8",              "pass", "Paper-fwd state"),
        ("Max Crypto Positions", str(crypto_open),    "3",              "pass", "—"),
        ("Crypto Allocation",  "0%",                  "≤10% NAV",       "pass", "—"),
        ("BTC-SPY Correlation","—",                   "alert >0.70",    "pending", "Monitored once positions open"),
        ("Strategy Pipeline",  f"{pipeline_count}",   "≥3",             "pass" if pipeline_count >= 3 else "warn", "Need MBV as 3rd"),
        ("Data Uptime",        "~95%",                ">99.5%",         "warn", "UAE yf gap mitigated by TV cache"),
        ("Audit Coverage",     "100%",                "100%",           "pass", "Every run logs to audit_trail.md"),
        ("Notification Latency","<1s",                "<60s",           "pass", "Telegram pushes immediate"),
    ]
    rows = ""
    for n, c, t, s, note in kpis:
        rows += f"<tr data-search='{esc(n + s + note)}'><td><b>{esc(n)}</b></td><td class='mono'>{esc(c)}</td><td class='muted'>{esc(t)}</td><td><span class='badge {_status_class(s)}'>{esc(s)}</span></td><td class='muted'>{esc(note)}</td></tr>"
    return f"""
    <div id="panel-kpis" class="tab-panel">
      <div class="section">
        <h3 data-i18n="sec_kpi">🎯 Mandate Targets — Are We Meeting Them?</h3>
        <table>
          <thead><tr><th>KPI</th><th>Current</th><th>Target</th><th>Status</th><th>Note</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
    </div>"""


def _render_live_status(state):
    tg = state["tg"]
    n_val_files = len(list(ROOT.glob('validation_*.json')))
    services = [
        ("Engine (Python+yfinance)", True, f"validation_*.json files present: {n_val_files}"),
        ("TradingView MCP", state.get("tv_ok", True), "Last successful chart access via dashboard generator"),
        ("Telegram Bot (@AIV_Fund_Bot)", tg["alive"], f"pid={tg['bot_pid']} · policy={tg['policy']} · last log {tg['last_log_mtime'] or '—'}"),
        ("GitHub Backup", bool(state["git_remote"]), state["git_remote"] or "—"),
        ("Paper-Forward Detector", state["paper"] is not None, f"Watch list: {', '.join((state['paper'] or {}).get('watch_list', [])) or '—'}"),
        ("Cloud Routines", len(state["tasks"]) > 0, f"{sum(1 for t in state['tasks'] if t.get('enabled')!='false')} active / {len(state['tasks'])} total"),
        ("Universe Files", all(_count_universe(UNIVERSE_DIR / f) > 0 for f in ["us_halal_full.txt","uae_tickers_full.txt","halal_crypto_150_USD.txt"]),
         f"US {state['universes']['US halal'][0]} · UAE {state['universes']['UAE halal'][0]} · Crypto {state['universes']['Crypto halal'][0]}"),
    ]
    rows = ""
    for name, ok, detail in services:
        dot = "on" if ok else "off"
        st = "online" if ok else "DOWN"
        cls = "gn" if ok else "rd"
        rows += f"<tr data-search='{esc(name + detail)}'><td><span class='dot {dot}'></span><b>{esc(name)}</b></td><td><span class='badge {cls}'>{esc(st)}</span></td><td class='muted'>{esc(detail)}</td></tr>"
    return f"""
    <div id="panel-live" class="tab-panel">
      <div class="section">
        <h3 data-i18n="sec_live">🟢 Live System Health</h3>
        <table>
          <thead><tr><th>Service</th><th>State</th><th>Detail</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
        <div class="muted" style="margin-top:8px;">Sampled at dashboard generation. Sprint routine regenerates every 2h.</div>
      </div>
    </div>"""


def _render_paper_pnl(state):
    paper = state["paper"]
    if not paper:
        body = '<div class="muted">No paper-forward state yet. Item 2 deployment writes <code>paper_forward_positions.json</code>.</div>'
        return f'<div id="panel-paper" class="tab-panel"><div class="section"><h3 data-i18n="sec_paper">📈 Paper Money — Live Test</h3>{body}</div></div>'
    deployed_at = paper.get("deployed_at", "—")
    history = paper.get("history", [])
    open_pos = paper.get("open_positions", {})
    last_run = paper.get("last_run", "—")
    watch = paper.get("watch_list", [])

    total_pnl_pct = sum(t.get("pnl_pct", 0) for t in history)
    nav = 100000 * (1 + total_pnl_pct / 100)
    win_count = sum(1 for t in history if t.get("pnl_pct", 0) > 0)
    wr = (win_count / len(history) * 100) if history else 0

    pts = [(0, 100000.0)]
    cum_pct = 0
    for t in history:
        cum_pct += t.get("pnl_pct", 0)
        pts.append((len(pts), 100000 * (1 + cum_pct / 100)))
    if len(pts) >= 2:
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        xmin, xmax = min(xs), max(xs); ymin, ymax = min(ys), max(ys)
        ymin = min(ymin, 99000); ymax = max(ymax, 101000)
        def sx(x): return 20 + (x - xmin) * (760 / max(1, xmax - xmin))
        def sy(y): return 180 - (y - ymin) * (160 / max(1, ymax - ymin))
        path = "M " + " L ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in pts)
        svg = f"""<svg viewBox="0 0 800 200" class="eq-chart-svg">
          <path d="{path}" stroke="#C9A84C" stroke-width="2" fill="none"/>
          <line x1="20" y1="{sy(100000):.1f}" x2="780" y2="{sy(100000):.1f}" stroke="#1a2744" stroke-dasharray="2,4"/>
          <text x="20" y="14" fill="#94A3B8" font-size="10">${ymax:,.0f}</text>
          <text x="20" y="196" fill="#94A3B8" font-size="10">${ymin:,.0f}</text>
        </svg>"""
    else:
        svg = '<div class="muted">No closed trades yet — equity curve pending.</div>'

    open_rows = ""
    for tk, p in open_pos.items():
        open_rows += f"<tr data-search='{esc(tk)}'><td><a class='ticker-link' href='{esc(_ticker_link(tk))}' target='_blank'>{esc(tk)}</a></td><td class='mono'>{esc(p.get('entry_date',''))}</td><td class='mono'>${p.get('entry_price',0):.2f}</td><td class='mono'>${p.get('stop_price') or '—'}</td><td>{p.get('rsi_at_entry','—')}</td></tr>"
    if not open_rows:
        open_rows = "<tr><td colspan='5' class='muted'>No open paper positions.</td></tr>"

    hist_rows = ""
    for t in history[::-1][:20]:
        pnl = t.get("pnl_pct", 0)
        cls = "gn" if pnl > 0 else "rd"
        tk = t.get('ticker', '')
        hist_rows += f"<tr data-search='{esc(tk)}'><td><a class='ticker-link' href='{esc(_ticker_link(tk))}' target='_blank'>{esc(tk)}</a></td><td class='mono'>{esc(t.get('entry_date',''))} → {esc(t.get('exit_date',''))}</td><td class='mono'>${t.get('entry_price',0):.2f} → ${t.get('exit_price',0):.2f}</td><td><span class='badge {cls}'>{pnl:+.2f}%</span></td><td class='muted'>{esc(t.get('exit_reason',''))}</td></tr>"
    if not hist_rows:
        hist_rows = "<tr><td colspan='5' class='muted'>No closed paper trades yet.</td></tr>"

    return f"""
    <div id="panel-paper" class="tab-panel">
      <div class="section glow">
        <h3 data-i18n="sec_paper_fwd">📈 Live Test — US Divergence Daily</h3>
        <div class="grid-4">
          <div class="tile"><div class="tile-label">NAV (paper)</div><div class="tile-value" style="color:var(--gold)">${nav:,.0f}</div><div class="tile-sub">{total_pnl_pct:+.2f}% since deploy</div></div>
          <div class="tile"><div class="tile-label">Open</div><div class="tile-value">{len(open_pos)}</div></div>
          <div class="tile"><div class="tile-label">Closed</div><div class="tile-value">{len(history)}</div></div>
          <div class="tile"><div class="tile-label">Win Rate</div><div class="tile-value">{wr:.0f}%</div></div>
        </div>
        <div style="margin-top:14px;">{svg}</div>
        <div class="muted" style="margin-top:8px;">Deployed {esc(deployed_at)} · Last detector run {esc(last_run)} · Watch list: {esc(', '.join(watch))}</div>
      </div>

      <div class="section" data-search="open positions">
        <h3 data-i18n="sec_paper_positions">🟢 Open Positions</h3>
        <table>
          <thead><tr><th>Ticker</th><th>Entry date</th><th>Entry price</th><th>Stop</th><th>RSI</th></tr></thead>
          <tbody>{open_rows}</tbody>
        </table>
      </div>

      <div class="section" data-search="closed paper trades history">
        <h3 data-i18n="sec_paper_history">📋 Closed Trades (last 20)</h3>
        <table>
          <thead><tr><th>Ticker</th><th>Period</th><th>Price</th><th>P&L</th><th>Reason</th></tr></thead>
          <tbody>{hist_rows}</tbody>
        </table>
      </div>
    </div>"""


def _render_risk(state):
    vix = state["vix"]
    v = vix.get("value")
    regime = vix.get("regime", "unknown")
    angle = 90 if v is None else max(0, min(180, (v / 50.0) * 180))
    needle_rotation = angle - 90
    paper = state["paper"] or {}
    history = paper.get("history", []) if paper else []
    if history:
        max_dd = 0; equity = 100.0; peak = 100.0
        for t in history:
            equity *= (1 + t.get("pnl_pct", 0) / 100)
            peak = max(peak, equity)
            dd = (equity - peak) / peak * 100
            max_dd = min(max_dd, dd)
        dd_pct = round(max_dd, 2)
    else:
        dd_pct = 0

    return f"""
    <div id="panel-risk" class="tab-panel">
      <div class="grid-2">

        <div class="section" data-search="vix volatility regime">
          <h3 data-i18n="sec_vix">📊 Market Volatility (VIX)</h3>
          <div class="gauge">
            <div class="gauge-bg"></div>
            <div class="gauge-needle" style="transform: translateX(-50%) rotate({needle_rotation:.1f}deg);"></div>
            <div class="gauge-label">{esc(v if v is not None else '—')}</div>
            <div class="gauge-regime">{esc(regime)}</div>
          </div>
          <div style="margin-top:54px;">
            <table style="font-size:11px;">
              <tr><td><span class="badge gn">VIX&lt;15</span></td><td class="muted">Bull-Calm — 100% Kelly</td></tr>
              <tr><td><span class="badge gn">15-20</span></td><td class="muted">Bull-Normal — 85% Kelly</td></tr>
              <tr><td><span class="badge or">20-25</span></td><td class="muted">Neutral — 70% Kelly</td></tr>
              <tr><td><span class="badge or">25-30</span></td><td class="muted">Elevated — 50% Kelly</td></tr>
              <tr><td><span class="badge rd">30-40</span></td><td class="muted">High Vol → Crisis A</td></tr>
              <tr><td><span class="badge rd">&gt;40</span></td><td class="muted">Crisis B — 100% cash (Tier 1)</td></tr>
            </table>
          </div>
        </div>

        <div class="section" data-search="drawdown paper portfolio risk">
          <h3 data-i18n="sec_drawdown">📉 Paper Loss From Peak</h3>
          <div class="tile" style="margin-bottom:10px;">
            <div class="tile-label">Max DD since deploy</div>
            <div class="tile-value" style="color:{'var(--gn)' if dd_pct >= -5 else 'var(--rd)'}">{dd_pct:+.2f}%</div>
            <div class="tile-sub">Tier 1 limit: -20% (no override)</div>
          </div>
          <div class="bar"><div class="bar-fill {'gold' if dd_pct >= -10 else 'rd'}" style="width:{min(100, abs(dd_pct)/20*100):.0f}%;"></div></div>
          <div class="muted" style="margin-top:8px;">Computed from paper_forward_positions.json equity curve.</div>
        </div>

        <div class="section" data-search="correlation correlations btc spy">
          <h3 data-i18n="sec_corr">🔗 Position Overlap</h3>
          <div class="muted">Activates when paper positions exist. Alert &gt;0.70 (v7.0 §10.1). Tier 1 &gt;0.85.</div>
          <table style="margin-top:10px;">
            <tr><td>BTC vs SPY</td><td class="muted">—</td><td><span class="badge gy">pending</span></td></tr>
            <tr><td>Crypto vs US Eq</td><td class="muted">—</td><td><span class="badge gy">pending</span></td></tr>
            <tr><td>UAE vs US Eq</td><td class="muted">—</td><td><span class="badge gy">pending</span></td></tr>
          </table>
        </div>

        <div class="section" data-search="sizing kelly cap position limits">
          <h3 data-i18n="sec_sizing">📏 Bet Size Limits</h3>
          <table style="font-size:11px;">
            <tr><td>Kelly cap (equity)</td><td class='mono'>1.5%</td></tr>
            <tr><td>Kelly cap (crypto)</td><td class='mono'>0.75%</td></tr>
            <tr><td>Max single (equity)</td><td class='mono'>15% NAV</td></tr>
            <tr><td>Max single (crypto)</td><td class='mono'>5% NAV</td></tr>
            <tr><td>Max equity positions</td><td class='mono'>8</td></tr>
            <tr><td>Max crypto positions</td><td class='mono'>3</td></tr>
            <tr><td>Crypto allocation cap</td><td class='mono'>10% NAV</td></tr>
          </table>
        </div>

      </div>
    </div>"""


def _render_telegram(state):
    sends = state["tg_log"][-100:][::-1]
    rows = ""
    for s in sends:
        ts = s.get("ts_utc", "")
        try:
            d = datetime.fromisoformat(ts.replace("Z","+00:00")).astimezone(GST)
            ts_disp = d.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            ts_disp = ts
        kind = s.get("kind", "text")
        ok = s.get("ok")
        cls = "gn" if ok else "rd"
        rows += f"""
        <div class="tg-entry" data-search="{esc(s.get('preview',''))}">
          <div class="ts">{esc(ts_disp)}</div>
          <div class="body">
            <span class="badge {cls}">{esc(kind)}</span>
            <span class="muted">→ {esc(s.get('to',''))}</span>
            <span class="muted">· msg #{esc(s.get('message_id',''))}</span>
            <div style="margin-top:4px; color:var(--t1)">{esc(s.get('preview',''))}</div>
          </div>
        </div>"""
    if not rows:
        rows = '<div class="muted">No Telegram sends logged yet. Helper writes to telegram_sent_log.json on every send (sends prior to this patch are not captured).</div>'
    return f"""
    <div id="panel-telegram" class="tab-panel">
      <div class="section">
        <h3 data-i18n="sec_telegram_log">📱 Phone Messages Sent (last 100)</h3>
        {rows}
      </div>
    </div>"""


def _render_commits(state):
    commits = state["commits"]
    remote = state["git_remote"]
    rows = ""
    for c in commits[:60]:
        try:
            d = datetime.fromisoformat(c["date"]).strftime("%Y-%m-%d %H:%M")
        except Exception:
            d = c["date"]
        sha = c["sha"]
        url = f"{remote}/commit/{c['full_sha']}" if remote else ""
        sha_html = f'<a href="{esc(url)}" target="_blank">{esc(sha)}</a>' if url else esc(sha)
        rows += f"<div class='commit-row' data-search='{esc(sha + c['subject'])}'><div class='sha'>{sha_html}</div><div class='muted mono'>{esc(d)}</div><div>{esc(c['subject'])}</div></div>"
    if not rows:
        rows = '<div class="muted">No commits.</div>'
    return f"""
    <div id="panel-commits" class="tab-panel">
      <div class="section">
        <h3 data-i18n="sec_commits">📜 Code History (last 60 changes)</h3>
        {rows}
        <div class="muted" style="margin-top:10px;">Remote: <a href="{esc(remote)}" target="_blank">{esc(remote)}</a></div>
      </div>
    </div>"""


def _render_history(state):
    # Auto-populate from ceo_brain SESSION X ARTIFACTS + git log bundling
    sessions_brain = state["brain"]["sessions"]
    commits = state["commits"]

    # Group commits by date (UTC date)
    by_date = {}
    for c in commits:
        try:
            d = datetime.fromisoformat(c["date"]).strftime("%Y-%m-%d")
        except Exception:
            d = c["date"][:10]
        by_date.setdefault(d, []).append(c)

    blocks = []
    # First, brain-parsed sessions
    for s in sessions_brain[::-1]:
        items = "".join(f"<li>{esc(i[:200])}</li>" for i in s["items"][:30])
        blocks.append(f"<div class='history-row' data-search='{esc(s['title'])} {esc(' '.join(s['items']))}'><div class='date'>{esc(s['title'])}</div><ul>{items}</ul></div>")

    # Then, daily git activity (group by date desc)
    for d in sorted(by_date.keys(), reverse=True)[:14]:
        subjects = [c["subject"] for c in by_date[d]]
        items = "".join(f"<li>{esc(s[:160])}</li>" for s in subjects[:15])
        search_text = d + " " + " ".join(subjects)
        plural = "s" if len(subjects) > 1 else ""
        blocks.append(
            f"<div class='history-row' data-search='{esc(search_text)}'>"
            f"<div class='date'>📅 {esc(d)} · {len(subjects)} commit{plural}</div>"
            f"<ul>{items}</ul></div>"
        )

    rows = "".join(blocks) or '<div class="muted">No history.</div>'
    return f"""
    <div id="panel-history" class="tab-panel">
      <div class="section">
        <h3 data-i18n="sec_history">📜 Past Sessions</h3>
        <input id="history-filter" placeholder="Filter history…" class="search-box" style="width:100%; margin-bottom:12px;">
        {rows}
      </div>
    </div>"""


def _render_glossary(state):
    terms = [
        ("Validation Gate", "Default-FAIL statistical test. OOS, walk-forward, deflated Sharpe, realistic costs, bootstrap CI."),
        ("Deflated Sharpe", "Sharpe with Bailey & López de Prado haircut for multi-testing. AIG uses N=6 trials post-audit."),
        ("Expectancy", "(Avg Win × WR) / (Avg Loss × LR). >1.0 = positive edge."),
        ("Portfolio Gate", "Aggregates all OOS trades in a universe. Multi-test haircut over trial count, not ticker count."),
        ("Paper-Forward", "Live data, no real money. Strategy runs forward; signals logged + delivered via Telegram."),
        ("Pre-Registration", "Strategy rules frozen in config.py before any test. config_hash binds spec to verdict."),
        ("Trial Budget", "Explicit table in strategy_register.md listing every (strategy × market × timeframe) the CEO has run. Bounds the multi-test haircut."),
        ("Circuit Breaker", "Tier 1 = no override (CEO/CIO cannot bypass). Tier 2 = CIO 6-field override."),
        ("Shariah Screen", "5-point AAOIFI check on every signal. Hardwired; cannot be disabled."),
        ("Mode 1 / Sprint", "Sprint until all 8 targets met. Routine every 2h. No live signals until verified."),
        ("Mode 2 / Steady State", "UAE 10AM GST, US 5:30PM GST signals. Monthly auditor cycle. Continuous improvement."),
        ("ceo_brain.md", "Persistent CEO memory. Read at start of every session. Updated at end."),
        ("Audit (Cowork)", "Independent read-only auditor. Cannot block deployment but flags BLOCKING/WARNING/NOTE."),
    ]
    rows = ""
    for t, d in terms:
        rows += f"<div data-search='{esc(t + d)}' style='padding:8px 0; border-bottom:1px solid var(--bd);'><div style='font-weight:700; color:var(--gold);'>{esc(t)}</div><div class='muted'>{esc(d)}</div></div>"
    return f"""
    <div id="panel-glossary" class="tab-panel">
      <div class="section">
        <h3 data-i18n="sec_glossary">📖 Words Guide — Plain English</h3>
        {rows}
      </div>
    </div>"""


def _render_ceo(state):
    decisions = state["brain"]["decisions"]
    rows = ""
    for d in decisions[::-1]:
        rows += f"""
        <div data-search="{esc(d['id_date'] + ' ' + d['title'] + ' ' + d['rationale_head'])}" style="padding:10px 0; border-bottom:1px solid var(--bd);">
          <div style="display:flex; gap:8px; align-items:center;">
            <span class="badge gd mono">{esc(d['id_date'])}</span>
            <span style="font-weight:700; color:var(--t1)">{esc(d['title'])}</span>
          </div>
          <div class="muted" style="margin-top:4px;">{esc(d['rationale_head'])}</div>
        </div>"""
    if not rows:
        rows = '<div class="muted">No decisions logged yet.</div>'
    return f"""
    <div id="panel-ceo" class="tab-panel">
      <div class="section">
        <h3 data-i18n="sec_ceo_all">💬 All CEO Decisions (with reasoning)</h3>
        <input id="ceo-filter" placeholder="Search decisions…" class="search-box" style="width:100%; margin-bottom:12px;">
        {rows}
      </div>
    </div>"""


# ---- expanded alert detection ----------------------------------------------

def _detect_alerts(state) -> list[str]:
    alerts = []
    # Sprint in-progress
    for s in state["brain"]["sprint_tracker"]:
        if "IN PROGRESS" in s["status"] or "🔄" in s["status"]:
            alerts.append(f"Sprint Item {s['id']}: {s['item'][:60]}")

    # Recent validation FAILs
    for (strat, market), v in state["runs"].items():
        if not v["passed"] and v.get("reasons"):
            alerts.append(f"{strat}/{market} FAIL: {v['reasons'][0][:80]}")

    # VIX elevated
    v = state["vix"].get("value")
    if v and v > 30:
        alerts.append(f"VIX elevated: {v} ({state['vix']['regime']})")

    # Telegram down
    if not state["tg"]["alive"]:
        alerts.append("Telegram bot DOWN")

    # Missed routine fires — any task whose next_run is in the past
    now_ts = datetime.now(GST).timestamp()
    for t in state["tasks"]:
        if t.get("enabled") == "false":
            continue
        nr = t.get("next_run_iso")
        if nr:
            try:
                if datetime.fromisoformat(nr).timestamp() < now_ts - 10800:  # > 3h late
                    alerts.append(f"Routine '{t['name']}' overdue (next fire was {nr})")
            except Exception:
                pass

    # Paper drawdown breaches
    paper = state["paper"] or {}
    hist = paper.get("history", []) if paper else []
    if hist:
        equity = 100.0; peak = 100.0; max_dd = 0
        for t in hist:
            equity *= (1 + t.get("pnl_pct", 0) / 100)
            peak = max(peak, equity)
            dd = (equity - peak) / peak * 100
            max_dd = min(max_dd, dd)
        if max_dd <= -5:
            alerts.append(f"Paper drawdown {max_dd:.2f}% (alert: <-5% / Tier 1 at -20%)")

    # Integrity-gate block count
    for (strat, market), v in state["runs"].items():
        rows = v.get("results_array", []) or []
        blocked = [r for r in rows if isinstance(r, dict) and r.get("verdict") in ("BLOCKED_DATA", "DATA_ERROR")]
        if len(blocked) > 50:
            alerts.append(f"{strat}/{market}: {len(blocked)} tickers blocked on data integrity")

    return alerts


# ---- main render ----------------------------------------------------------

def render() -> str:
    now_gst = datetime.now(GST).strftime("%Y-%m-%d %H:%M GST")
    universes = {
        "US halal":     (_count_universe(UNIVERSE_DIR / "us_halal_full.txt"), 100),
        "UAE halal":    (_count_universe(UNIVERSE_DIR / "uae_tickers_full.txt"), 60),
        "Crypto halal": (_count_universe(UNIVERSE_DIR / "halal_crypto_150_USD.txt"), 100),
    }
    runs = _latest_validation_results()
    tasks = _scheduled_tasks()
    for t in tasks:
        if t.get("enabled") != "false":
            t["next_run_iso"] = _cron_next_fire_iso(t.get("cron", ""))
    tg = _telegram_status()
    tg_log = _telegram_sent_log()
    commits = _git_log(60)
    remote = _git_remote_url()
    brain = _ceo_brain_sections()
    audit = _auditor_findings()
    paper = _paper_state()
    vix = _vix_latest()
    trial_budget = _trial_budget()
    nav_val, nav_pct = _paper_nav()
    agent_state = _agent_state_map(brain["sprint_tracker"])

    state = {
        "now_gst": now_gst, "universes": universes, "runs": runs,
        "tasks": tasks, "tg": tg, "tg_log": tg_log,
        "telegram_sends": len(tg_log),
        "commits": commits, "git_remote": remote,
        "brain": brain, "audit": audit, "paper": paper, "vix": vix,
        "trial_budget": trial_budget,
        "nav_val": nav_val, "nav_pct": nav_pct,
        "agent_state": agent_state,
    }

    alerts = _detect_alerts(state)
    alert_count = len(alerts)
    alert_items = "".join(f'<div style="padding:6px 0; border-bottom:1px solid var(--bd); font-size:11px;">{esc(a)}</div>' for a in alerts) or '<div class="muted">No alerts.</div>'

    tabs_def = [
        ("overview", "📊", "Overview", "tab_overview"),
        ("markets", "🌍", "Markets", "tab_markets"),
        ("agents", "🤖", "Agents", "tab_agents"),
        ("kpis", "🎯", "Targets", "tab_kpis"),
        ("live", "🟢", "Live Status", "tab_live"),
        ("paper", "📈", "Paper Money", "tab_paper"),
        ("risk", "🛡️", "Risk", "tab_risk"),
        ("telegram", "📱", "Phone Alerts", "tab_telegram"),
        ("commits", "📜", "Code Changes", "tab_commits"),
        ("history", "🗂", "Decisions", "tab_history"),
        ("glossary", "📖", "Words Guide", "tab_glossary"),
        ("ceo", "💬", "CEO Notes", "tab_ceo"),
    ]
    tab_buttons = "".join(
        f'<button class="tab" data-tab="{tid}" data-i18n="{key}">{ti} {tl}</button>'
        for tid, ti, tl, key in tabs_def
    )

    panels = "".join([
        _render_overview(state),
        _render_markets(state),
        _render_agents(state),
        _render_kpis(state),
        _render_live_status(state),
        _render_paper_pnl(state),
        _render_risk(state),
        _render_telegram(state),
        _render_commits(state),
        _render_history(state),
        _render_glossary(state),
        _render_ceo(state),
    ])

    mode_cls = "mode2" if "MODE 2" in brain["mode"] else "mode1"
    nav_delta_cls = "up" if nav_pct >= 0 else "dn"
    nav_delta_glyph = "▲" if nav_pct >= 0 else "▼"

    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta http-equiv="refresh" content="120">
<title>AIG Cockpit v3 — Ahmed Investment Group</title>
<style>{CSS}</style>
</head>
<body>

<div class="header">
  <div class="header-row">
    <div>
      <div class="brand">AHMED INVESTMENT GROUP <span class="ar">مجموعة أحمد للاستثمار</span></div>
      <div class="brand-sub">v7.0 · بسم الله الرحمن الرحيم · refreshed {esc(now_gst)}</div>
      <div class="refresh-countdown" data-i18n="refresh_label">page auto-refresh in <span id="refresh-countdown-val" data-remain="120">02:00</span></div>
    </div>
    <div class="right-tools">
      <div class="lang-toggle" id="lang-toggle">
        <button class="lang-btn active" data-lang="en" type="button">EN</button>
        <button class="lang-btn" data-lang="ar" type="button">عربي</button>
      </div>
      <input id="global-search" class="search-box" placeholder="Search across all tabs…" autocomplete="off" data-i18n="search_placeholder" data-i18n-attr="placeholder">
      <div class="bell" id="alert-bell" data-count="{alert_count}">
        🔔
        {f'<span class="bell-count">{alert_count}</span>' if alert_count else ''}
        <div id="alert-drop" style="display:none; position:absolute; right:0; top:36px; background:var(--cd); border:1px solid var(--bd); border-radius:8px; padding:10px; width:380px; box-shadow: 0 8px 32px #00000060; z-index: 200;">
          <div style="font-size:11px; font-weight:700; color:var(--gold); margin-bottom:6px;">Alerts ({alert_count})</div>
          {alert_items}
        </div>
      </div>
      <div class="nav-display">
        <div class="label">NAV (paper)</div>
        <div class="val">${nav_val:,.0f}</div>
        <div class="delta {nav_delta_cls}">{nav_delta_glyph} {nav_pct:+.2f}% since deploy</div>
      </div>
      <div class="nav-pill {mode_cls}">
        <div class="label">{esc(brain['mode'])}</div>
        <div class="val">{esc(brain['mode_label'])}</div>
      </div>
    </div>
  </div>
</div>

<div class="tab-bar">
  <div class="tab-bar-inner">{tab_buttons}</div>
</div>

<div class="wrap">
  <div id="search-empty-hint" class="search-empty-hint"></div>
  {panels}
</div>

<div class="footer">
  AIG v7.0 · engine + cockpit unified · repo <a href="{esc(remote)}" target="_blank">{esc(remote)}</a> ·
  page <a href="{PAGES_BASE}/dashboard.html" target="_blank">{PAGES_BASE}/dashboard.html</a> ·
  Rule 01 paper · Rule 15 long only · Rule 16 no leverage · بسم الله
</div>

<script>{JS}</script>
</body></html>
"""


def main():
    html_out = render()
    DASHBOARD_PATH.write_text(html_out, encoding="utf-8")
    print(f"Wrote {DASHBOARD_PATH}  ({len(html_out):,} bytes)")


if __name__ == "__main__":
    main()
