# Phase 3: Aircraft Performance, Flight-Phase FSM & Procedure Following - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-06
**Phase:** 3-aircraft-performance-flight-phase-fsm-procedure-following
**Areas discussed:** Aircraft fleet, Demo harness for this phase, Visual differentiation, Taxi visibility

---

## Aircraft Fleet

| Option | Description | Selected |
|--------|-------------|----------|
| Common EGGW mix | A320-family, B737-family, and a regional/GA type (e.g. ATR72 or C172) | |
| Let the researcher pick | Researcher sources real performance figures for whatever mix has good available data | ✓ |
| I have specific types in mind | User names specific aircraft types to lock in now | |

**User's choice:** Let the researcher pick
**Notes:** No further questions raised in this area.

---

## Demo Harness for This Phase

| Option | Description | Selected |
|--------|-------------|----------|
| Two hardcoded aircraft at startup | One departure + one arrival, spawned when the app starts, both autonomous | ✓ |
| Departure only this phase | Smaller scope but leaves arrival success criteria unmet | |

**User's choice:** Two hardcoded aircraft at startup
**Notes:** Follow-up question asked about end-of-lifecycle behavior for the departure aircraft and whether the demo should loop.

| Option | Description | Selected |
|--------|-------------|----------|
| Remove on exit, loop the demo | Departure removed after passing SID's last fix; once both aircraft gone, respawn a fresh pair | ✓ |
| Remove on exit, no loop | Same removal, but radar sits empty until app restart | |

**User's choice:** Remove on exit, loop the demo

---

## Visual Differentiation

| Option | Description | Selected |
|--------|-------------|----------|
| Behavior-only for now | Single cyan-dot symbol retained; differentiation shows via climb/speed/turn-rate behavior | ✓ |
| Distinct symbol per type now | Different dot size/shape per aircraft type immediately | |

**User's choice:** Behavior-only for now
**Notes:** No further questions raised in this area.

---

## Taxi Visibility

| Option | Description | Selected |
|--------|-------------|----------|
| Rendered stationary at stand | Aircraft shown as a stationary dot at a stand position during taxi | ✓ |
| Hidden during taxi | Aircraft doesn't appear until departure roll / disappears immediately after landing | |

**User's choice:** Rendered stationary at stand
**Notes:** No further questions raised in this area.

---

## Claude's Discretion

- Exact stand/gate coordinate(s) for taxi-visible positions.
- Exact numeric performance profile values (climb/descent rate, speed envelope, turn rate) per aircraft type.
- Flight-Phase enum membership and legal-transitions table (hand-rolled per ARCHITECTURE.md Pattern 2, not the `transitions` library).
- Procedure-following mechanism details (leg-index tracking, `compute_target()` seam per ARCHITECTURE.md Pattern 3).
- Taxi timer duration(s).

## Deferred Ideas

- **Distinct visual symbols per aircraft type** — deferred; behavioral differentiation is sufficient, and Phase 4's datablock will likely cover type identification more directly.
- **Scripted, file-driven traffic** — the two-hardcoded-aircraft demo harness is an explicit stand-in for the real scenario loader (Phase 6, SCEN-01/02).
