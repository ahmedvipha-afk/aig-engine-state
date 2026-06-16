# AUTONOMY & AGENT ROLES — current-reality scope (authoritative)

2026-06-17. **This doc is authoritative for autonomy scope and supersedes the
stale Phase-1 tracker in `ceo_brain.md`.** Read with [PROJECT_MAP.md](PROJECT_MAP.md).

---

## 1. THE MANDATE (current)
- **The 3x/10x annual return mandate is RETIRED** (decision_log entry 39). Replaced
  by a **Kelly-bound realistic anchor (~5–10% CAGR)**. The v7 Scope Document is
  archived as historical-aspirational only (entry 40).
- **This is a validation engine, not a return-chaser.** Success = an honest,
  reproducible, default-FAIL gate that decides paper-forward eligibility — NOT a
  target number. A *target* is aspirational by nature; a *gate* is adversarial by
  nature. Retiring the target does NOT license loosening the gate (entries 39, 57).

## 2. AUTONOMY IS BOUNDED
Autonomous (cron / headless / loop) work is permitted **only up to analysis and
data capture.** Concretely:

**ALLOWED autonomously:**
- Track-1 sprints: pre-registered detector fires, paper-forward observation,
  dashboard, commit/push (self-contained, idempotent).
- Read-only analysis, benchmark/calibration captures on frozen data, audit-log
  appends, doc updates.
- Recording findings (decision_log entries) that change nothing in the gate.

**OPERATOR-SUPERVISED ONLY (never autonomous):**
- **Any gate / config / threshold change**, and the **Strand-C gate redesign**
  (wiring amendments, recomputing `config_hash`, migration test).
- Validation-branch merges (never auto-merge).
- **Path 3** (post-hoc gate amendment) — withdrawn/hard-gated (entries 1, 26-class).
- Per-market trade floors (Amendment 2) — **PARKED/OUT** (loosening).

**Stop-guard:** if autonomous work reaches a point that would require a gate change
or an irreversible/outward action, it STOPS and surfaces to the operator. (This is
how the gate-calibration project ran: capture autonomously, redesign supervised.)

## 3. STANDING PRINCIPLES (locked — entry 57)
1. **Stricter, never looser** — redesigns may only tighten; never reverse-engineer a
   threshold from what admits the current portfolio.
2. **Test breadth, not a winner factory** — measure many strategies fairly.
3. **Enforcement verified in code** — a rule counts only if `portfolio_evaluate`
   actually reads it (entry 52).
4. **Benchmark + council before any gate change.**

## 4. THE "27 AGENTS" — roles & responsibilities
The "27 agents" is an **organisational model, not 27 processes** (`aig/agents.py`):
tagged responsibilities so every audit-trail line says WHICH function made the
decision. The bounded responsibilities actually wired into Layers 1–2:

| Tag | Role | Where |
|---|---|---|
| `IN-L` | Systems / data-feed health | `aig/data.py` (load, cache, feed) |
| `RI-H` | Compliance / data-integrity gate | `aig/data.py` `integrity_check` |
| `RD-B` | R&D backtest engine | `aig/backtest.py` |
| `RD-D` | Validation gate (approval) | `aig/validation_gate.py` |
| `IN-O` | Audit | provenance / run headers |

Every `audit(tag, msg)` call writes `[tag role] msg` to `aig/audit_trail.md`. The
full 27-role org chart is the directive's conceptual model; the **5 tags above are
the ones enforced in code today** — additional roles (research, council, CEO,
operator) act at the human/operator layer, not as code paths.

## 5. SCOPE CONFORMANCE CHECK (doc vs actual behavior)
- **Track-1 (cron sprints):** conforms — pre-registered fires + paper-forward +
  commit/push only; never touches the gate. ✓
- **Gate-calibration project (entries 52–63):** conformed — autonomous capture +
  control + logging; gate redesign explicitly deferred to operator session. ✓
- **Autonomous loop ticks:** conformed — advanced established work (capture, commits,
  resume, docs); stopped and surfaced at every gate/irreversible boundary. ✓
- **DRIFT FLAGGED:** `ceo_brain.md` still shows the **Phase-1 tracker / 6-of-10
  score / 1,107-union coverage** — all **STALE** (self-flagged in-file, predates the
  Track-2 amendment + the three-filter slots + the gate-calibration work). It is NOT
  authoritative for scope; THIS doc is. ceo_brain.md remains the cron's per-fire
  read for operational state, but its mandate/coverage numbers should be treated as
  historical until an operator refresh. No behavioral drift found — only doc drift.
