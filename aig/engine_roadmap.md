# Engine Roadmap — scoped future capabilities (captured, not scheduled)

Future engine capabilities recorded so they are preserved while higher-priority
framework work proceeds. Capture ≠ schedule. Nothing here is started or
authorized to start; each item lists the gates that must hold before any build.

---

## ITEM: Cross-sectional engine capability (FUTURE — not started, gated)

**WHAT:** Add cross-sectional ranking dispatch to the engine (rank the
universe on a metric, select a top fraction, rebalance) alongside the
existing per-ticker dispatch.

**WHY:** Three of five Filter-1 archetypes have their well-sourced T1 forms
blocked by the per-ticker-only engine — momentum (Jegadeesh-Titman),
low-volatility anomaly / BAB (cross-sectional), parts of statistical_arb.
This capability would let them be tested in their real published form
instead of distorted per-ticker adaptations.

**FRAMING (non-negotiable):** this is TEST-BREADTH INFRASTRUCTURE — it
widens what can be HONESTLY tested. It is NOT a "winner-factory." A bigger
engine does not change the Kelly bound (5-10% ceiling, entry 39) and does
not make strategies win more. Edge comes from validation, never from engine
horsepower. Any framing of this as "engine that produces winners" is the
retired phantom mandate and is rejected.

**GATES (all must hold before build starts):**
1. Entry-46 win-rate-floor question resolved first (UPSTREAM blocker — the
   low-win-rate T1 strategies this unlocks, e.g. momentum, would hit the
   same floor; building before that pays off nothing).
2. Track 1 provably stable (it is now, on C:\aig_engine — keep it so).
3. Built and tested through the SAME unchanged validation gate +
   pre-registration discipline. The engine may grow; the gate's honesty
   does not bend to "let winners through."
4. Long-only / no-leverage / halal constraints still bind (rules out the
   short leg of classic cross-sectional momentum and BAB).

**STATUS:** captured, not scheduled. Revisit after entry-46 resolves.
