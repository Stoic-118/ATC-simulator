# Phase 1: Walking Skeleton — Sim Clock & Radar Render Loop - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-03
**Phase:** 1-walking-skeleton-sim-clock-radar-render-loop
**Areas discussed:** Radar Visual Style, Phase 1 Test Aircraft Path, Window Sizing, v1 Scope Confirmation

---

## Radar Visual Style

| Option | Description | Selected |
|--------|-------------|----------|
| Classic green scope | Dark/black background, monochrome green vector lines and text | |
| Modern flat display | Dark grey/blue background with white/cyan elements | ✓ |
| Doesn't matter yet | Any readable placeholder, visual polish is a later phase | |

**User's choice:** Modern flat display
**Notes:** Should carry forward into later rendering phases since it's the look the player stares at every session.

---

## Phase 1 Test Aircraft Path

| Option | Description | Selected |
|--------|-------------|----------|
| Continuous circular orbit | Loops indefinitely, easy to observe drift/stalls over time | |
| Straight line, then wrap | Flies a straight heading, reappears on the opposite side | |
| Let me explain | User describes something else | (initial pick) |

**User's choice (first pass):** User initially proposed multiple aircraft picking between several SIDs/STARs (departures and arrivals) — see "Scope Creep" section below for how this was resolved.

**User's choice (final, after scope resolution):** Straight line, then wrap
**Notes:** Simplest possible motion model; intentionally does not preview real flight behavior since no navdata exists until Phase 2.

---

## Window Sizing

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed size (Recommended) | Sensible fixed resolution (e.g. 1280x800) | ✓ |
| Resizable from day one | Canvas handles window resize correctly from the start | |

**User's choice:** Fixed size
**Notes:** Avoids resize/scaling logic this early; can revisit later.

---

## Scope Creep: Multiple SIDs/STARs with Selection

The user's first answer to the "Phase 1 Test Aircraft Path" question described multiple aircraft, each picking between several SID departures or STAR approaches. This was flagged as scope creep for two reasons: (1) Phase 1 has no real navdata or procedure modeling at all — that's Phase 2/3 — and (2) it directly reverses the earlier locked v1 decision of "one SID, one STAR" (already tracked as the deferred v2 item `TRAF-01` in REQUIREMENTS.md).

| Option | Description | Selected |
|--------|-------------|----------|
| Keep v1 as scoped (Recommended) | One SID, one STAR for v1; note the idea for later v2 planning | ✓ |
| Promote to v1 now | Update REQUIREMENTS.md/ROADMAP.md to support multiple SIDs/STARs now | |

**User's choice:** Keep v1 as scoped
**Notes:** No changes made to REQUIREMENTS.md or ROADMAP.md. The multi-procedure idea remains `TRAF-01` in v2, with this discussion logged as context for whenever that item is prioritized.

---

## Claude's Discretion

- Exact fixed sim tick rate within the 1-4Hz range
- Max-ticks-per-frame cap value
- Specific numeric window resolution (within "fixed size" constraint)

## Deferred Ideas

- Multiple SIDs/STARs with per-aircraft procedure selection — already tracked as `TRAF-01` in REQUIREMENTS.md v2; this discussion is additional context for Phase 3 planning and future v2 scoping.
