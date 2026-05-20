# AIG — Layers 1 & 2 (Data + Validation Engine)

The first **runnable** deliverable of the reconciled architecture. It does the
one thing everything else depends on: tell you, honestly, whether the frozen
EMA-200 strategy has any edge per ticker — out-of-sample, after realistic
costs, with multiple-testing correction.

## What it is (and is not)
- It is the real Layer 1-2 engine: data-integrity gate, frozen pre-registered
  EMA-200, realistic per-market costs, train/test split + walk-forward,
  bootstrap CI, deflated Sharpe, the non-negotiable validation gate,
  reproducibility hashing, agent-tagged audit trail, regression tests.
- It is NOT "proven" anything. Passing the gate means **cleared for
  paper-forward**, not proven. (Per the agreed language.)
- "Cleared: 0" is the EXPECTED, correct result most of the time. The gate
  rejects by default. That is the design working.

## Run it
Offline (no network, runs anywhere — proves the machine works):
```
pip install -r requirements.txt
python run_validation.py
python tests/test_engine.py
```
Live, real data on YOUR machine (this is where real verdicts come from):
```
pip install openbb
python run_validation.py --live --tickers AAPL MSFT NVDA XOM
```
Outputs: console summary, `audit_trail.md` (every decision, agent-tagged),
`validation_results.json` (full detail + provenance hash).

## Honest boundary
This sandbox has no market-data network, so offline mode uses deterministic
synthetic data — enough to prove the engine is correct, not to judge EMA-200.
The real answer comes from `--live` on your machine with OpenBB connected.
Whatever number clears (often zero) is a real result, not a target to hit.
