# Phase 1: Walking Skeleton — Sim Clock & Radar Render Loop - Context

**Gathered:** 2026-07-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Prove the single riskiest architectural bet — a fixed-timestep sim clock fully decoupled from the render loop — on a bare radar canvas showing one hardcoded aircraft. No real navdata (Phase 2), no performance model or FSM (Phase 3), no player instructions (Phase 4). Requirements covered: CORE-01, CORE-02, CORE-03, RADAR-01, RADAR-03, plus the README installation success criterion.

</domain>

<decisions>
## Implementation Decisions

### Radar Visual Style
- **D-01:** Modern flat display styling — dark grey/blue background with white/cyan elements, closer to a modern EFIS/radar workstation than a classic green CRT scope. This style choice should carry forward into later rendering phases (Phase 2 navdata rendering, Phase 4 datablocks, Phase 7 polish) since it's the look the player will stare at every session.

### Phase 1 Test Aircraft
- **D-02:** The one hardcoded aircraft in this skeleton flies a straight line across the canvas at a fixed heading, then wraps around to the opposite side and continues — the simplest possible motion model. This is throwaway motion logic specific to Phase 1; it does not need to resemble any real SID/STAR (those don't exist until Phase 2/3).

### Window Sizing
- **D-03:** Fixed window size (e.g. 1280x800) for this skeleton — no resize/scaling logic needed yet. Revisit resizability in a later phase if desired.

### v1 Scope Confirmation (not a Phase 1 decision, but resolved during this discussion)
- **D-04 [informational]:** During discussion the user initially proposed multiple aircraft picking between several SIDs/STARs for the test path. This was identified as scope creep (belongs to Phase 3+, and directly conflicts with the already-locked v1 decision of one SID/one STAR). **Resolved: v1 scope stays as originally defined — one SID, one STAR.** The multi-procedure idea remains deferred to v2 as `TRAF-01` in REQUIREMENTS.md; no changes made to REQUIREMENTS.md or ROADMAP.md as a result of this discussion.

### Claude's Discretion
- Exact fixed sim tick rate within the 1-4Hz range, the max-ticks-per-frame cap value, and the specific numeric window resolution are implementation details left to the planner/research, per the project's existing STACK.md and ARCHITECTURE.md research.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Scope & Decisions
- `.planning/PROJECT.md` — core value, v1 scope, constraints, key decisions (esp. the "one SID, one STAR" and "simplified performance profiles" decisions)
- `.planning/REQUIREMENTS.md` — CORE-01/02/03, RADAR-01/03 (this phase's requirements), and `TRAF-01` in v2 (the deferred multi-procedure idea from this discussion)
- `.planning/ROADMAP.md` — Phase 1 goal, success criteria (including the README installation criterion), and Phase 2/3 boundaries this phase must not cross

### Research
- `.planning/research/ARCHITECTURE.md` — fixed-timestep accumulator pattern, sim-core-never-imports-Pygame boundary, walking skeleton build order
- `.planning/research/STACK.md` — pygame-ce, Pydantic v2, geographiclib recommendations and accumulator-loop code pattern
- `.planning/research/PITFALLS.md` — spiral-of-death / uncapped accumulator pitfall (Pitfall 1), directly relevant to this phase's CORE-02 requirement

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — this is a greenfield project with no source code yet (only planning docs and README.md exist).

### Established Patterns
- None yet — this phase establishes the first patterns (sim/render decoupling boundary).

### Integration Points
- N/A for this phase — nothing existing to integrate with.

</code_context>

<specifics>
## Specific Ideas

- Radar canvas should use a modern flat dark display style (dark grey/blue background, white/cyan elements), not a classic green monochrome CRT look.
- The Phase 1 test aircraft's motion (straight line, wrap at edge) is intentionally trivial — it exists only to prove the tick/render decoupling, not to preview real flight behavior.

</specifics>

<deferred>
## Deferred Ideas

- **Multiple SIDs/STARs with per-aircraft procedure selection** — raised during this discussion as an idea for how test traffic could eventually behave. Conceptually this is what Phase 3 (autonomous SID/STAR following) already does for one procedure each; extending it to multiple procedures with selection is the already-tracked v2 backlog item `TRAF-01` in REQUIREMENTS.md. No roadmap or requirements changes made — flagged here so Phase 3 planning and any future v2 scoping discussion has this context.

[None else — discussion stayed within phase scope]

</deferred>

---

*Phase: 1-walking-skeleton-sim-clock-radar-render-loop*
*Context gathered: 2026-07-03*
