"""AIG Cockpit — generate dashboard.html from current engine state.

Self-contained. Reads:
  - All validation_*.json (most recent per strategy×market)
  - universe/*.txt (coverage counts)
  - ceo_brain.md (decisions queue + state)
  - git log (last 8 commits)
  - scheduled-tasks listing (via filesystem walk of ~/.claude/scheduled-tasks)
  - telegram channel state (bot.pid + access.json + last delivery)

Writes a single self-contained HTML file (vanilla CSS, no external deps) to:
  aig_engine/dashboard.html

Usage:
  python scripts/generate_dashboard.py
"""
from __future__ import annotations
import json
import os
import subprocess
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_PATH = ROOT / "dashboard.html"
UNIVERSE_DIR = ROOT / "universe"
HOME = Path(os.path.expanduser("~"))
SCHEDULED_TASKS_DIR = HOME / ".claude" / "scheduled-tasks"
TELEGRAM_DIR = HOME / ".claude" / "channels" / "telegram"
GST = timezone(timedelta(hours=4))

# ---- helpers ---------------------------------------------------------------

def _safe_read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _count_universe_lines(path: Path) -> int:
    if not path.exists():
        return 0
    n = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            n += 1
    return n


def _git_log(n: int = 8) -> list[dict]:
    try:
        out = subprocess.check_output(
            ["git", "log", f"-{n}", "--pretty=format:%h|%ad|%s", "--date=iso-strict"],
            cwd=str(ROOT), text=True, stderr=subprocess.DEVNULL
        )
    except Exception:
        return []
    rows = []
    for line in out.splitlines():
        parts = line.split("|", 2)
        if len(parts) == 3:
            rows.append({"sha": parts[0], "date": parts[1], "subject": parts[2]})
    return rows


def _git_remote_url() -> str | None:
    try:
        url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=str(ROOT), text=True, stderr=subprocess.DEVNULL
        ).strip()
        if url.endswith(".git"):
            url = url[:-4]
        return url
    except Exception:
        return None


def _scheduled_tasks() -> list[dict]:
    rows = []
    if not SCHEDULED_TASKS_DIR.exists():
        return rows
    for d in SCHEDULED_TASKS_DIR.iterdir():
        if not d.is_dir():
            continue
        skill = d / "SKILL.md"
        if not skill.exists():
            continue
        head = skill.read_text(encoding="utf-8", errors="ignore").splitlines()[:30]
        frontmatter: dict[str, str] = {}
        in_fm = False
        for line in head:
            if line.strip() == "---":
                in_fm = not in_fm
                continue
            if in_fm:
                m = re.match(r"^([\w-]+):\s*(.*)$", line)
                if m:
                    frontmatter[m.group(1)] = m.group(2).strip().strip('"')
        rows.append({
            "name": d.name,
            "cron": frontmatter.get("cron", frontmatter.get("schedule", "—")),
            "description": frontmatter.get("description", ""),
            "enabled": frontmatter.get("enabled", "true"),
        })
    rows.sort(key=lambda r: r["name"])
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


def _latest_validation_results() -> dict:
    """Return the most recent validation_*.json per (strategy, market).
    Market is inferred from filename keywords: us_, uae_, crypto."""
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
        }
    return out


def _ceo_brain_excerpt() -> dict:
    path = ROOT / "ceo_brain.md"
    if not path.exists():
        return {"open_issues": [], "instructions": []}
    text = path.read_text(encoding="utf-8", errors="ignore")
    # Pull the "OPEN ISSUES" / "OPEN APPROVAL REQUESTS" + "DECISION POINT" sections
    def take(heading: str) -> list[str]:
        m = re.search(rf"^##+ .*{heading}.*$", text, flags=re.M | re.I)
        if not m:
            return []
        start = m.end()
        m2 = re.search(r"^---\s*$|^##+ ", text[start:], flags=re.M)
        end = start + m2.start() if m2 else len(text)
        block = text[start:end].strip()
        return [l for l in block.splitlines() if l.strip()][:25]
    return {
        "open_issues": take("OPEN ISSUES"),
        "decision_point": take("DECISION POINT"),
    }


# ---- rendering -------------------------------------------------------------

CSS = """
:root { color-scheme: dark; }
* { box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  background: #0b1020;
  color: #e6e9ef;
  margin: 0;
  padding: 24px;
  line-height: 1.45;
}
h1, h2, h3 { margin: 0; }
h1 { font-size: 22px; font-weight: 700; letter-spacing: -0.01em; }
h2 { font-size: 14px; text-transform: uppercase; letter-spacing: 0.08em;
     color: #9aa3b2; margin: 28px 0 12px; font-weight: 600; }
h3 { font-size: 12px; color: #9aa3b2; text-transform: uppercase;
     letter-spacing: 0.06em; }
a { color: #5aa9ff; text-decoration: none; }
a:hover { text-decoration: underline; }
.wrap { max-width: 1280px; margin: 0 auto; }
.header { display: flex; justify-content: space-between; align-items: baseline;
          margin-bottom: 4px; flex-wrap: wrap; gap: 12px; }
.subtitle { color: #9aa3b2; font-size: 13px; }
.grid { display: grid; gap: 16px; }
.grid-4 { grid-template-columns: repeat(4, 1fr); }
.grid-3 { grid-template-columns: repeat(3, 1fr); }
.grid-2 { grid-template-columns: repeat(2, 1fr); }
@media (max-width: 900px) {
  .grid-4 { grid-template-columns: repeat(2, 1fr); }
  .grid-3, .grid-2 { grid-template-columns: 1fr; }
}
.card { background: #131a2e; border: 1px solid #1f2944; border-radius: 12px;
        padding: 16px 18px; }
.metric { font-size: 26px; font-weight: 700; margin-top: 4px; }
.metric .unit { font-size: 14px; color: #9aa3b2; margin-left: 4px; }
.status { display: inline-block; font-size: 11px; padding: 3px 8px;
          border-radius: 999px; font-weight: 600; letter-spacing: 0.04em;
          text-transform: uppercase; }
.status-pass { background: #103a23; color: #4ade80; }
.status-near { background: #3a2e10; color: #fbbf24; }
.status-fail { background: #3a1010; color: #f87171; }
.status-info { background: #102640; color: #5aa9ff; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { text-align: left; color: #9aa3b2; font-weight: 500; font-size: 11px;
     text-transform: uppercase; letter-spacing: 0.06em; padding: 8px 10px;
     border-bottom: 1px solid #1f2944; }
td { padding: 10px; border-bottom: 1px solid #161e36; }
tr:last-child td { border-bottom: none; }
.bar-row { display: flex; align-items: center; gap: 12px; margin: 8px 0; }
.bar-label { width: 110px; color: #9aa3b2; font-size: 13px; }
.bar { flex: 1; height: 10px; background: #1f2944; border-radius: 999px;
       overflow: hidden; position: relative; }
.bar-fill { height: 100%; border-radius: 999px;
            background: linear-gradient(90deg, #4ade80, #22d3ee); }
.bar-fill-warn { background: linear-gradient(90deg, #fbbf24, #f59e0b); }
.bar-fill-low  { background: linear-gradient(90deg, #f87171, #ef4444); }
.bar-target { position: absolute; top: -4px; bottom: -4px; width: 2px;
              background: #e6e9ef; }
.bar-value { width: 130px; font-size: 12px; color: #cbd5e1; text-align: right; }
.muted { color: #9aa3b2; font-size: 12px; }
.mono { font-family: 'SF Mono', Menlo, Consolas, monospace; font-size: 12px; }
.footer { color: #6b7280; font-size: 11px; margin-top: 32px;
          padding-top: 12px; border-top: 1px solid #1f2944; }
.kpi-row td:first-child { font-weight: 500; }
ul.tight { margin: 0; padding-left: 18px; }
ul.tight li { margin: 4px 0; font-size: 13px; }
.refresh { font-size: 11px; color: #6b7280; }
.dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%;
       margin-right: 6px; vertical-align: middle; }
.dot-on { background: #4ade80; box-shadow: 0 0 6px #4ade80; }
.dot-off { background: #f87171; }
"""


def _status_class(verdict: str | None, passed: bool, key_metric: float | None = None) -> str:
    if passed:
        return "status-pass"
    if verdict == "PORTFOLIO_FAIL":
        # near miss heuristic: deflated Sharpe above 0
        return "status-near" if (key_metric or 0) > 0 else "status-fail"
    return "status-info"


def render_dashboard() -> str:
    now_gst = datetime.now(GST).strftime("%Y-%m-%d %H:%M GST")
    universes = {
        "US halal":     ("us_halal_full.txt", 100),
        "UAE halal":    ("uae_tickers_full.txt", 60),
        "Crypto halal": ("halal_crypto_150_USD.txt", 100),
    }
    universe_counts = {k: (_count_universe_lines(UNIVERSE_DIR / fn), tgt)
                       for k, (fn, tgt) in universes.items()}
    runs = _latest_validation_results()
    cleared = [k for k, v in runs.items() if v["passed"]]
    tasks = _scheduled_tasks()
    tg = _telegram_status()
    commits = _git_log(8)
    remote = _git_remote_url() or "—"
    brain = _ceo_brain_excerpt()

    # cards
    cards = [
        ("Cleared strategies", f"{len(cleared)}",
         "Portfolio-gate passes across market × strategy",
         "status-pass" if cleared else "status-info"),
        ("Open positions", "0",
         "Rule 01: paper portfolio only, no live exec yet",
         "status-info"),
        ("Universe coverage",
         f"{sum(c for c,_ in universe_counts.values())}",
         f"Targets: US ≥100, UAE ≥60, crypto ≥100",
         "status-info"),
        ("Telegram bot",
         "ONLINE" if tg["alive"] else "DOWN",
         f"policy={tg['policy'] or '—'}; allowFrom {len(tg['allowFrom'])}",
         "status-pass" if tg["alive"] else "status-fail"),
    ]
    card_html = "\n".join(
        f"""<div class="card"><h3>{t}</h3>
            <div class="metric">{m}</div>
            <div class="muted">{sub}</div>
            <div style="margin-top:8px;"><span class="status {sc}">{sc.replace('status-','').upper()}</span></div>
        </div>"""
        for (t, m, sub, sc) in cards
    )

    # coverage bars
    bar_rows = []
    for name, (count, target) in universe_counts.items():
        pct = min(100, int(100 * count / target)) if target else 0
        cls = "bar-fill" if count >= target else ("bar-fill-warn" if count >= target/2 else "bar-fill-low")
        bar_rows.append(
            f"""<div class="bar-row">
              <div class="bar-label">{name}</div>
              <div class="bar"><div class="{cls}" style="width:{pct}%;"></div></div>
              <div class="bar-value">{count} / {target} target</div>
            </div>"""
        )
    bar_html = "\n".join(bar_rows)

    # strategy results table
    strat_rows = []
    for (strat, market), v in sorted(runs.items()):
        sc = "status-pass" if v["passed"] else ("status-near" if (v["sharpe_def"] or -99) > 0 else "status-fail")
        reason = v["reasons"][0] if v["reasons"] else ""
        strat_rows.append(f"""
        <tr>
          <td><b>{strat}</b></td>
          <td>{market}</td>
          <td><span class="status {sc}">{v['verdict']}</span></td>
          <td class="mono">{v['contributors']}/{v['universe_size']}</td>
          <td class="mono">{v['trades']:,}</td>
          <td class="mono">{v['expectancy']:.2f}</td>
          <td class="mono">{(v['win_rate'] or 0)*100:.1f}%</td>
          <td class="mono">{v['sharpe_def']:.2f}</td>
          <td class="muted">{reason}</td>
        </tr>""")
    strat_html = "".join(strat_rows) or '<tr><td colspan="9" class="muted">No validation runs yet.</td></tr>'

    # KPI table (v7.0 §24, 14 KPIs — values placeholder until live trading)
    kpis = [
        ("Annual return",         "—",            "≥3x (hard min), 10x asp",  "Paper not started"),
        ("Sharpe ratio",          "2.72 (US Div portfolio)", "≥1.5 / target ≥2.5", "Pre-paper, portfolio-level"),
        ("Max drawdown",          "—",            "<20%",                     "Paper not started"),
        ("Alpha vs S&P 500",      "—",            ">0",                       "Paper not started"),
        ("Win rate ★★★★+",        "—",            ">50%",                     "Rolling 30 trades"),
        ("Halal compliance",      "100%",         "100%",                     "Universes pre-screened"),
        ("Max equity positions",  "0",            "8",                        "No open positions"),
        ("Max crypto positions",  "0",            "3",                        "No open positions"),
        ("Crypto allocation",     "0%",           "≤10% NAV",                 "—"),
        ("BTC-SPY correlation",   "—",            "alert >0.70",              "Not yet monitored"),
        ("Strategy pipeline",     f"{len(set(s for s,_ in runs))}",     "≥3",                       "MBV is the missing third"),
        ("Data uptime",           "~95%",         ">99.5%",                   "yfinance gaps on UAE; mitigated via TV cache"),
        ("Audit coverage",        "100%",         "100%",                     "audit_trail.md per run"),
        ("Notification latency",  "—",            "<60s",                     "Telegram online; first signal pending"),
    ]
    kpi_html = "".join(
        f"<tr class='kpi-row'><td>{n}</td><td class='mono'>{v}</td><td class='mono'>{t}</td><td class='muted'>{note}</td></tr>"
        for (n, v, t, note) in kpis
    )

    # routines
    task_html = "".join(
        f"<tr><td><b>{r['name']}</b></td><td class='mono'>{r['cron']}</td><td class='muted'>{r['description']}</td></tr>"
        for r in tasks
    ) or "<tr><td colspan='3' class='muted'>No scheduled tasks.</td></tr>"

    # commits
    commit_html = "".join(
        f"<tr><td class='mono'>{c['sha']}</td><td class='mono muted'>{c['date'][:16]}</td><td>{c['subject']}</td></tr>"
        for c in commits
    ) or "<tr><td colspan='3' class='muted'>No git history.</td></tr>"

    # CEO brain excerpts
    issues_html = "".join(f"<li>{l}</li>" for l in brain["open_issues"][:12]) or "<li class='muted'>none</li>"
    decisions_html = "".join(f"<li>{l}</li>" for l in brain["decision_point"][:12]) or "<li class='muted'>none</li>"

    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta http-equiv="refresh" content="900">
<title>AIG Cockpit — Ahmed Investment Group</title>
<style>{CSS}</style>
</head>
<body><div class="wrap">

<div class="header">
  <div>
    <h1>AIG Fund Cockpit</h1>
    <div class="subtitle">Ahmed Investment Group · Paper $100,000 · UAE GST</div>
  </div>
  <div class="refresh">Refreshed {now_gst} · auto-refresh 15 min</div>
</div>

<h2>Status</h2>
<div class="grid grid-4">{card_html}</div>

<h2>Universe coverage vs target</h2>
<div class="card">{bar_html}</div>

<h2>Strategy verdicts (latest run per market × strategy)</h2>
<div class="card"><table>
<thead><tr><th>Strategy</th><th>Market</th><th>Verdict</th><th>Contrib</th><th>Trades</th><th>Exp</th><th>WR</th><th>dSharpe</th><th>Top fail reason</th></tr></thead>
<tbody>{strat_html}</tbody></table></div>

<div class="grid grid-2" style="margin-top:16px;">
  <div class="card">
    <h3>KPI scorecard (v7.0 §24)</h3>
    <table style="margin-top:8px;"><thead><tr><th>KPI</th><th>Current</th><th>Target</th><th>Note</th></tr></thead>
    <tbody>{kpi_html}</tbody></table>
  </div>
  <div class="card">
    <h3>Cloud routines</h3>
    <table style="margin-top:8px;"><thead><tr><th>Task</th><th>Schedule</th><th>Description</th></tr></thead>
    <tbody>{task_html}</tbody></table>
    <h3 style="margin-top:18px;">Telegram channel</h3>
    <div class="muted">
      <span class="dot {'dot-on' if tg['alive'] else 'dot-off'}"></span>
      Bot {'ALIVE' if tg['alive'] else 'DOWN'} · pid={tg['bot_pid'] or '—'} ·
      policy={tg['policy'] or '—'} ·
      allowlist {len(tg['allowFrom'])} user(s) ·
      log last touched {tg['last_log_mtime'] or '—'}
    </div>
  </div>
</div>

<h2>Recent commits</h2>
<div class="card"><table>
<thead><tr><th>SHA</th><th>Date</th><th>Subject</th></tr></thead>
<tbody>{commit_html}</tbody></table>
<div class="muted" style="margin-top:8px;">Remote: <a href="{remote}" target="_blank">{remote}</a></div>
</div>

<div class="grid grid-2" style="margin-top:16px;">
  <div class="card">
    <h3>Open issues (from ceo_brain.md)</h3>
    <ul class="tight">{issues_html}</ul>
  </div>
  <div class="card">
    <h3>Decision queue</h3>
    <ul class="tight">{decisions_html}</ul>
  </div>
</div>

<div class="footer">
  AIG v7.0 · engine + cockpit unified · backup repo {remote} ·
  state files in <span class="mono">{ROOT}</span> ·
  Rule 01 paper only · Rule 15 long only · Rule 16 no leverage · بسم الله
</div>

</div></body></html>
"""


def main():
    html = render_dashboard()
    DASHBOARD_PATH.write_text(html, encoding="utf-8")
    print(f"Wrote {DASHBOARD_PATH}  ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
