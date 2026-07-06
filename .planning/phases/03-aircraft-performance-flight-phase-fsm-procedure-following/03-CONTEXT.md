# Phase 3: Aircraft Performance, Flight-Phase FSM & Procedure Following - Context

**Gathered:** 2026-07-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace the single placeholder aircraft (currently a bare x/y/heading/speed model flying a straight line, per Phase 1/2) with type-differentiated aircraft that autonomously fly a full departure or arrival end-to-end — spawn, taxi, takeoff/climb-out via the OLNEY 2B SID (departure) or descend via the DET 2A STAR toward the airport (arrival) — driven by an explicit flight-phase state machine and per-type performance profiles. No player instructions yet (Phase 4 — click/panel/vectoring/ILS capture), no scripted scenario loader yet (Phase 6 — this phase's traffic is two hardcoded demo aircraft, not scenario-file-driven). Requirements covered: PERF-01, PERF-02, PERF-03, PERF-04, PROC-01.

</domain>

<decisions>
## Implementation Decisions

### Aircraft Fleet
- **D-01:** Which 3-5 real aircraft types to model is left to the Phase 3 researcher to pick during research — the user does not have specific types locked in. The researcher should choose a realistic, well-documented mix with clear performance-envelope spread (e.g. narrowbody jet vs. turboprop/GA), sourcing simplified (not BADA-table) climb/descent rate, speed envelope, and turn-rate data for each.

### Demo Harness (no instructions or scenario loader exist yet)
- **D-02:** This phase's autonomous departure/arrival loop is demonstrated by two hardcoded aircraft spawned when the app starts — one departure aircraft (spawns at a stand, taxis, takes off, climbs out via the OLNEY 2B SID's legs/restrictions) and one arrival aircraft (spawns airborne at the DET 2A STAR entry fix with a realistic initial altitude/speed, flies the STAR's legs/restrictions toward the airport). This replaces Phase 1/2's single placeholder aircraft entirely — it is not additive to it.
- **D-03:** Once the departure aircraft passes the SID's final/exit fix, it is removed from active traffic (mirrors the arrival's removal after landing + taxi-in, per success criterion #5). Once both the departure and arrival aircraft have been removed, the demo loops — a fresh departure/arrival pair spawns automatically — so the app keeps demonstrating the full loop without needing a restart.

### Visual Differentiation
- **D-04:** Aircraft types are differentiated by behavior only (visibly different climb/descent rate, speed, and turn rate during flight) — no new visual symbol system (e.g. per-type dot size/shape) is added this phase. This satisfies the phase's "visibly differentiated" success criterion as literally worded (differentiated *during flight*, i.e. behaviorally) without adding a rendering system that Phase 4's planned datablock (showing aircraft type/callsign directly) will likely make redundant anyway.

### Taxi Visibility
- **D-05:** During the abstracted timer-based taxi (pushback/taxi-out before departure roll, and taxi-in after landing), the aircraft renders as a stationary dot at a stand/gate position — it does not disappear or stay hidden during taxi. This makes the full aircraft lifecycle (spawn → taxi → takeoff → climb, or land → taxi-in → removed) visually continuous and observable, directly supporting success criterion #4 (phase transitions are always legal and observable).

### Claude's Discretion
- Exact stand/gate coordinate(s) used for the taxi-visible departure spawn and arrival taxi-in position — pick a plausible position near the apron/terminal area relative to the runway 25 threshold; does not need to be sourced from a real published stand chart.
- Exact numeric performance profile values (climb rate, descent rate, speed envelope, turn rate per bank angle/groundspeed) for each chosen aircraft type — per the project's existing PITFALLS.md Pitfall 7 guidance (avoid decoupling that produces numerically-correct-but-experientially-wrong behavior; some coupling between altitude/speed/configuration should exist even in a simplified v1 model).
- Flight-Phase enum exact membership and legal-transitions table — per the project's existing ARCHITECTURE.md Pattern 2 recommendation (hand-rolled `Enum` + legal-transitions `dict`, not the `transitions` library, for v1's short mostly-linear phase list).
- Procedure-following mechanism (leg-index tracking, restriction application) — per ARCHITECTURE.md's "procedure-following-with-vectoring-override-layer" pattern (Pattern 3), building the `compute_target()` seam now even though the vectoring-override side doesn't exist until Phase 4.
- Timer duration(s) for the taxi abstraction (how many seconds/ticks a taxi takes) are an implementation detail, not a user vision decision.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Scope & Decisions
- `.planning/PROJECT.md` — core value, v1 scope, constraints (esp. "simplified per-aircraft-type performance profiles, not BADA-style tables or full physics")
- `.planning/REQUIREMENTS.md` — PERF-01/02/03/04, PROC-01 (this phase's requirements)
- `.planning/ROADMAP.md` — Phase 3 goal, success criteria, and Phase 4/5/6 boundaries this phase must not cross (no instructions, no vectoring, no separation checking, no scenario loader yet)

### Research
- `.planning/research/ARCHITECTURE.md` — Pattern 2 (explicit hand-rolled flight-phase FSM), Pattern 3 (procedure-following-with-vectoring-override-layer, `compute_target()` seam), Anti-Pattern 2 (implicit phase via scattered thresholds — avoid), Anti-Pattern 3 (renderer must never mutate sim state), recommended `sim/aircraft.py` / `sim/performance.py` module split
- `.planning/research/PITFALLS.md` — Pitfall 7 (simplified performance profiles producing numerically-correct-but-experientially-wrong behavior — altitude/speed/configuration coupling matters even in a simplified model), the meta-risk pitfall about fidelity investment before the thin end-to-end loop works (this phase IS the thin loop for performance/procedure-following — don't over-invest in fidelity beyond what's needed to prove it)
- `.planning/research/SUMMARY.md` — original Phase 3/4 delivery summary (§"Phase 3: Aircraft Performance Model + Flight-Phase FSM" and §"Phase 4: Procedure-Following (SID/STAR)" — note these two research-sketch phases are merged into this single roadmap Phase 3)

### Prior Phase Context
- `.planning/phases/02-navdata-coordinate-projection/02-CONTEXT.md` and `02-RESEARCH.md` — real OLNEY 2B SID / DET 2A STAR fix data (names, coordinates, restrictions), shared cosine-corrected projection (`navdata/geo.py`), runway 25 real-world data
- `.planning/phases/01-walking-skeleton-sim-clock-radar-render-loop/01-CONTEXT.md` — D-01 (dark flat modern-EFIS palette) still applies; no new visual system needed per D-04 above
- `.planning/phases/01-05-SUMMARY.md` through `02-05-SUMMARY.md` — what exists today: `src/atc_sim/sim/aircraft.py` (current placeholder `Aircraft` model, x/y/heading/speed only, no phase/type/procedure fields yet), `src/atc_sim/sim/clock.py` (`SimClock`), `src/atc_sim/sim/interpolation.py`, `src/atc_sim/navdata/{models,geo,eggw}.py` (Runway, ILS, Fix, Procedure, `OLNEY_2B_SID`, `DET_2A_STAR`), `src/atc_sim/render/{window,radar}.py`, `src/atc_sim/app.py`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/atc_sim/sim/aircraft.py::Aircraft` — current model is x/y pixel coordinates + heading_deg + speed_px_per_sec only. This phase must substantially evolve it (or introduce a richer model) to add: aircraft type reference, flight-phase field, procedure reference + leg index, and altitude/vertical-speed state — while preserving the existing Pydantic v2 conventions (`ConfigDict`, `validate_assignment=True` for live state, `Field(ge=...)` bounds).
- `src/atc_sim/navdata/models.py::Procedure`, `ProcedureLeg`, `Fix`, `AltitudeRestriction`, `SpeedRestriction` (from Phase 2) — procedure-following reads leg/restriction data directly off these frozen navdata objects; do not copy or duplicate this data onto the Aircraft model.
- `src/atc_sim/navdata/eggw.py::OLNEY_2B_SID`, `DET_2A_STAR` — the two real procedures this phase's demo aircraft fly.
- `src/atc_sim/render/radar.py` — `RenderState` Protocol pattern (established Phase 1) for giving render code typed access to sim state without importing sim modules directly; extend this pattern if the renderer needs new derived fields (e.g. aircraft phase, for future datablock work in Phase 4).

### Established Patterns
- Sim/render architectural boundary: only `app.py` may import both `pygame` and `atc_sim.sim.*` (enforced by `tests/test_boundary.py`). Performance profiles, the flight-phase FSM, and procedure-following logic all belong in `atc_sim.sim.*` (pygame-free, unit-testable with plain pytest — critical per the project's "sim never lies" bar, and per ARCHITECTURE.md's note that phase/procedure logic needs to be testable in isolation).
- Frozen Pydantic v2 models for read-only reference data (navdata, and likely per-type performance profiles too, since a performance profile is "facts about an aircraft type," not "state of a specific aircraft" — same category as navdata).
- `validate_assignment=True` + `Field` bounds for live/mutable per-aircraft state (matches the existing `Aircraft` model's convention).

### Integration Points
- The demo-harness spawn logic (D-02) replaces `Aircraft.spawn_default()` and its single call site in `app.py`'s main loop — this is a call-site change, not just an addition.
- Procedure-following's `compute_target()` seam (ARCHITECTURE.md Pattern 3) should be built now so Phase 4's vectoring-override logic can layer on top of it later without a rework.

</code_context>

<specifics>
## Specific Ideas

- The taxi-visible stand position and the overall "watch the whole lifecycle happen" framing (D-05) came directly from wanting success criterion #4 (legal, observable phase transitions) to be something you can literally watch happen on screen, not just something proven by a test suite.
- The looping demo (D-03) was motivated by wanting to be able to leave the app running and repeatedly observe the full departure/arrival loop for visual verification, rather than needing to restart the app each time.

</specifics>

<deferred>
## Deferred Ideas

- **Distinct visual symbols per aircraft type** (different dot size/shape on radar) — considered and explicitly deferred; behavioral differentiation is sufficient for this phase, and Phase 4's datablock (showing type/callsign as text) will likely cover the "how do I know what type this is" need more directly than a new symbol system would.
- **Scripted, file-driven traffic** — the two-hardcoded-aircraft demo harness (D-02) is explicitly a stand-in for the real scenario loader, which is Phase 6 (SCEN-01/02). No scenario-file work happens in this phase.

[None else — discussion stayed within phase scope]

</deferred>

---

*Phase: 3-aircraft-performance-flight-phase-fsm-procedure-following*
*Context gathered: 2026-07-06*
