---
phase: 03-aircraft-performance-flight-phase-fsm-procedure-following
plan: 04
subsystem: sim
tags: [pydantic, coordinate-migration, procedure-following, kinematics, fsm-dispatch]

# Dependency graph
requires:
  - phase: 03-01
    provides: "tests/test_procedure_following.py (PROC-01 spec), shared phase_recorder fixture"
  - phase: 03-02
    provides: "sim/performance.py: PerformanceProfile, FLEET, turn_rate_deg_per_sec, step_toward_value, step_toward_heading, glidepath_altitude_ft"
  - phase: 03-03
    provides: "sim/phase.py: Phase enum, LEGAL_TRANSITIONS, transition_to"
provides:
  - "Aircraft evolved into the shared local-nm coordinate space (x_nm/y_nm) with altitude_ft/speed_kt/heading_deg(magnetic)/phase/phase_elapsed_sec/procedure/procedure_leg_index/performance state"
  - "sim/procedure.py: Targets, compute_target() with restriction look-ahead, advance_leg_if_reached()"
  - "sim_step() per-phase kinematics dispatcher (_step_taxi/_step_departure_roll/_step_airborne/_step_landed) with legal-only phase transitions via transition_to()"
  - "AircraftSnapshot renamed x_nm/y_nm in lockstep (interpolation.py); render/radar.py's RenderState Protocol + draw_frame renamed in lockstep"
affects: [03-05, 03-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Aircraft.x_nm/y_nm share navdata/geo.py's local tangent-plane coordinate space, eliminating per-tick geodesic calls in favor of planar trigonometry"
    - "procedure.py imports Aircraft only under TYPE_CHECKING (from __future__ import annotations) to avoid a circular import with aircraft.py, which imports procedure.py at runtime"
    - "Small named per-phase dispatch helpers (_step_taxi/_step_departure_roll/_step_airborne/_step_landed) called from one short sim_step(), instead of a scattered inline if/elif kinematics block"
    - "Phase-completion logic (_is_phase_complete) lives in aircraft.py, not phase.py, keeping phase.py a pure leaf with zero Aircraft coupling"

key-files:
  created:
    - src/atc_sim/sim/procedure.py
  modified:
    - src/atc_sim/sim/aircraft.py
    - src/atc_sim/sim/interpolation.py
    - src/atc_sim/render/radar.py
    - tests/test_interpolation.py
    - tests/test_render_smoke.py

key-decisions:
  - "APPROACH does not call compute_target() at all -- a new _approach_targets() helper in aircraft.py targets the runway threshold directly (same atan2/true_to_magnetic convention) and uses glidepath_altitude_ft() for altitude, because by the time DESCENT->APPROACH fires, procedure_leg_index has already exhausted the STAR's legs, so indexing into aircraft.procedure.legs would raise IndexError. This also keeps procedure.py free of any ILS-adjacent logic per Task 2's explicit scope boundary."
  - "CLIMB->ENROUTE completion is tied to leg progress (procedure_leg_index >= 1), not an altitude threshold, per 03-RESEARCH.md's explicit instruction ('keep CLIMB->ENROUTE tied to leg progress') since the departure demo aircraft is removed from ENROUTE externally before ever reaching DESCENT"
  - "DESCENT->APPROACH completion (procedure_leg_index >= len(procedure.legs)) was added even though not explicitly named in Task 3's own threshold list, because 03-RESEARCH.md Pattern C requires it for a correct arrival lifecycle and leaving it unimplemented would silently strand every arrival in DESCENT forever (Rule 2: missing critical functionality)"
  - "advance_leg_if_reached() guards procedure_leg_index against the last leg (no-op once exhausted) so it is safe to call unconditionally from _step_airborne, including during APPROACH, without needing phase-specific call-site logic"
  - "ENROUTE has no auto-completion condition in _is_phase_complete (always returns False) -- consistent with phase.py's own docstring that removal-from-ENROUTE is an external list-membership concern owned by demo_traffic (03-05), never a Phase-FSM transition"
  - "Chose _TAXI_DURATION_SEC=18.0s, _ROTATION_SPEED_KT=150.0kt, _APPROACH_CAPTURE_DISTANCE_NM=0.1, _APPROACH_CAPTURE_ALTITUDE_FT=50.0 as named [ASSUMED] module-level constants, all within 03-RESEARCH.md Pattern C's suggested ranges"

requirements-completed: [PROC-01, PERF-02, PERF-03, PERF-04]

coverage:
  - id: D1
    description: "Aircraft evolved into the shared local-nm coordinate space with full altitude/phase/procedure/performance state, keeping validate_assignment=True; no is_departure field or stale spawn_default/CANVAS_WIDTH pixel-space code remains"
    requirement: "PERF-02"
    verification:
      - kind: unit
        ref: "tests/test_interpolation.py::test_aircraft_rejects_bad_fields, tests/test_interpolation.py::test_aircraft_validates_on_assignment"
        status: pass
      - kind: unit
        ref: "python -m pytest tests/test_boundary.py -q (aircraft.py/procedure.py/interpolation.py stay headless)"
        status: pass
    human_judgment: false
  - id: D2
    description: "compute_target() on the DET STAR's unrestricted LOFFO leg looks ahead to ABBOT's FL080 instead of holding level at FL170 (restriction look-ahead regression), and returns a true->magnetic-converted (exactly once) heading"
    requirement: "PROC-01"
    verification:
      - kind: unit
        ref: "tests/test_procedure_following.py::test_compute_target_looks_ahead_past_unrestricted_leg, tests/test_procedure_following.py::test_compute_target_heading_is_magnetic"
        status: pass
    human_judgment: false
  - id: D3
    description: "advance_leg_if_reached() increments procedure_leg_index only within the capture radius, and is a no-op once past the last leg"
    requirement: "PROC-01"
    verification:
      - kind: unit
        ref: "tests/test_procedure_following.py::test_advance_leg_if_reached_increments_leg_index_within_capture_radius"
        status: pass
      - kind: other
        ref: "manual python -c verification: aircraft placed 50nm outside the current leg's fix keeps procedure_leg_index unchanged after advance_leg_if_reached()"
        status: pass
    human_judgment: false
  - id: D4
    description: "sim_step() dispatches per-phase kinematics via small named helpers and transitions phases only via transition_to() when the completion condition is met, producing the exact departure ([TAXI_OUT, DEPARTURE_ROLL, CLIMB, ENROUTE]) and arrival ([DESCENT, APPROACH, LANDED, TAXI_IN]) phase sequences end-to-end"
    requirement: "PERF-03, PERF-04"
    verification:
      - kind: unit
        ref: "tests/test_interpolation.py (10 sim_step-dispatch tests: taxi freeze/timer, departure-roll acceleration/no-turn/rotation transition, airborne turn+descent+lookahead, leg advance, DESCENT->APPROACH, APPROACH->LANDED, LANDED->TAXI_IN, ENROUTE never auto-transitions)"
        status: pass
      - kind: other
        ref: "manual python harness stepping a full departure (TAXI_OUT spawn -> OLNEY_2B_SID exhausted) and full arrival (DESCENT at DET FL170 -> TAXI_IN) with no demo_traffic.py, confirming the exact phase sequences tests/test_departure_flow.py and tests/test_arrival_flow.py will assert once 03-05 lands"
        status: pass
    human_judgment: false

duration: 25min
completed: 2026-07-06
status: complete
---

# Phase 3 Plan 4: Autonomous Procedure-Following Core Summary

**Aircraft migrated to the shared local-nm coordinate system with full phase/procedure/performance state; new `procedure.py` compute_target() with restriction look-ahead and once-only true->magnetic conversion; `sim_step()` rewritten as a per-phase kinematics dispatcher — an aircraft now autonomously flies a real SID/STAR leg-by-leg toward its charted restrictions.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-07-06T17:40:00Z
- **Completed:** 2026-07-06T18:05:00Z
- **Tasks:** 3
- **Files modified:** 6 (1 created, 5 modified)

## Accomplishments
- `Aircraft` (src/atc_sim/sim/aircraft.py) evolved from the Phase-1 pixel-space placeholder (x/y pixels, speed_px_per_sec) into the shared local-nm tangent-plane coordinate system (x_nm/y_nm, same space as `navdata/geo.py`'s `project_to_local_xy_nm`), plus `altitude_ft`, `speed_kt`, magnetic `heading_deg`, `phase`, a single reusable `phase_elapsed_sec` timer, `procedure`, `procedure_leg_index`, and `performance` — `validate_assignment=True` preserved throughout; no `is_departure` field, `spawn_default()`/`CANVAS_WIDTH`/`CANVAS_HEIGHT` removed
- `src/atc_sim/sim/procedure.py` created: `Targets` frozen dataclass, `compute_target()` (restriction look-ahead across remaining legs so DET 2A STAR's unrestricted LOFFO leg targets ABBOT's FL080 instead of holding level at FL170 — the Pitfall 7 regression this phase specifically guards against), `advance_leg_if_reached()` (planar fly-by capture-radius sequencing, guarded past the last leg); imports `Aircraft` only under `TYPE_CHECKING` to avoid a circular import with `aircraft.py`
- `sim_step()` rewritten as a short dispatcher delegating to `_step_taxi`/`_step_departure_roll`/`_step_airborne`/`_step_landed`; phase transitions occur only via `transition_to()`, resetting `phase_elapsed_sec` to `0.0`; `_step_airborne` uses `compute_target()` (or a new `_approach_targets()` glidepath-to-threshold helper for APPROACH) plus `turn_rate_deg_per_sec`/`step_toward_heading`/`step_toward_value` for turn/climb-or-descend/speed-change/move kinematics
- `interpolation.py`'s `AircraftSnapshot`/`capture_state`/`interpolate` renamed to `x_nm`/`y_nm` in lockstep; `render/radar.py`'s `RenderState` Protocol and `draw_frame` renamed in lockstep so the render module keeps functioning against the renamed snapshot (a Rule 3 fix — see Deviations)
- Manually verified (no `demo_traffic.py` yet, so outside automated test scope) that a hand-built departure aircraft walks `[TAXI_OUT, DEPARTURE_ROLL, CLIMB, ENROUTE]` across the full OLNEY 2B SID and a hand-built arrival aircraft walks `[DESCENT, APPROACH, LANDED, TAXI_IN]` across the full DET 2A STAR — the exact sequences `tests/test_departure_flow.py`/`tests/test_arrival_flow.py` will assert once 03-05's `demo_traffic.py` lands
- Full suite green: 48 passed, 2 skipped (`test_departure_flow.py`/`test_arrival_flow.py`, correctly still pending `demo_traffic.py`); `test_boundary.py` confirms `aircraft.py`/`procedure.py`/`interpolation.py` stay headless; no circular-import error

## Task Commits

Each task was committed atomically (TDD RED -> GREEN pairs):

1. **Task 1: Evolve Aircraft into local-nm coordinate + procedure/performance/phase state; update interpolation lockstep**
   - `6d6e626` (test) — rewrote `tests/test_interpolation.py`/`tests/test_render_smoke.py` for the new field shapes (RED)
   - `7edaf41` (feat) — Aircraft model + interpolation.py + render/radar.py renamed in lockstep (GREEN)
2. **Task 2: procedure.py — compute_target with restriction look-ahead + magnetic heading + leg sequencing** — `befd9d9` (feat); activated the pre-existing `tests/test_procedure_following.py` (RED from 03-01, now GREEN)
3. **Task 3: sim_step per-phase kinematics dispatch** — `f172acc` (feat); activated the 10 sim_step-dispatch tests added in Task 1's RED commit

**Plan metadata:** (this commit, docs: complete plan)

## Files Created/Modified
- `src/atc_sim/sim/aircraft.py` - Evolved `Aircraft` model (nm-space, phase/procedure/performance state) + `sim_step()` per-phase dispatcher and helpers
- `src/atc_sim/sim/procedure.py` - `Targets`, `compute_target()`, `_next_altitude_restriction_ft()`, `_next_speed_restriction_kt()`, `advance_leg_if_reached()`
- `src/atc_sim/sim/interpolation.py` - `AircraftSnapshot`/`capture_state`/`interpolate` renamed x_nm/y_nm
- `src/atc_sim/render/radar.py` - `RenderState` Protocol + `draw_frame` renamed x_nm/y_nm in lockstep (deviation, see below)
- `tests/test_interpolation.py` - Rewritten for the new Aircraft/AircraftSnapshot shape; obsolete pixel-canvas tests retired; 10 new sim_step-dispatch tests added
- `tests/test_render_smoke.py` - `AircraftSnapshot` construction renamed x_nm/y_nm

## Decisions Made
See `key-decisions` in frontmatter for the full list. Highlights: APPROACH uses a dedicated `_approach_targets()` helper (never `compute_target()`) to avoid indexing past the STAR's exhausted legs; `CLIMB`->`ENROUTE` and `DESCENT`->`APPROACH` transitions are both tied to procedure-leg progress rather than altitude thresholds; `ENROUTE` has no auto-completion condition (removal is external, per `phase.py`'s own documented design).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Renamed render/radar.py's RenderState Protocol + draw_frame to x_nm/y_nm in lockstep**
- **Found during:** Task 1 (Aircraft/AircraftSnapshot coordinate rename)
- **Issue:** `render/radar.py` (not in this plan's `files_modified`) reads `render_state.x`/`render_state.y` via a structural `Protocol`, duck-typing against `AircraftSnapshot`. Renaming `AircraftSnapshot`'s fields to `x_nm`/`y_nm` without updating this consumer would leave `draw_frame()` raising `AttributeError` at runtime, and `tests/test_render_smoke.py` (which constructs an `AircraftSnapshot` directly and passes it to `draw_frame`) would fail — a direct, unavoidable consequence of the field rename, blocking the full-suite verification this plan requires.
- **Fix:** Renamed the `RenderState` Protocol's `x`/`y` fields and `draw_frame`'s attribute access to `x_nm`/`y_nm` — a pure field-name lockstep fix preserving current behavior exactly (values are still treated as raw screen-space pixels, not projected via `world_to_screen`). Real nm->pixel projection wiring remains explicitly deferred to plan 03-06, matching this plan's own stated boundary for `app.py`'s call site.
- **Files modified:** `src/atc_sim/render/radar.py`, `tests/test_render_smoke.py`
- **Verification:** `python -m pytest tests/test_render_smoke.py tests/ -q` — full suite green
- **Committed in:** `6d6e626` (test, RED) and `7edaf41` (feat, GREEN)

**2. [Rule 1 - Bug] Rewrote tests/test_interpolation.py's obsolete pixel-canvas tests**
- **Found during:** Task 1
- **Issue:** The pre-existing `test_interpolation.py` tested Phase-1/2 behavior (`AircraftSnapshot(x=..., y=...)`, `Aircraft(x=..., y=..., speed_px_per_sec=...)`, `sim_step`'s straight-line-only motion, `CANVAS_WIDTH` wrap-edge check) that this plan's field rename and `sim_step` rewrite make structurally impossible to construct — a direct, in-scope consequence of Task 1/3's own changes, not a pre-existing unrelated failure.
- **Fix:** Renamed `AircraftSnapshot` construction kwargs to `x_nm`/`y_nm`; rewrote `test_aircraft_rejects_bad_fields`/added `test_aircraft_validates_on_assignment` against the new full Aircraft shape (reusing real `navdata.eggw` procedures and `FLEET` performance profiles); removed the two obsolete pixel-canvas `sim_step` tests and replaced them with 10 new tests exercising the Task 3 per-phase dispatcher (taxi freeze/timer, departure-roll acceleration/no-turn/rotation-speed transition, airborne turn+descent+restriction-lookahead, leg-advance integration, DESCENT->APPROACH, APPROACH->LANDED capture, LANDED->TAXI_IN, ENROUTE never auto-transitioning).
- **Files modified:** `tests/test_interpolation.py`
- **Verification:** All 17 tests in the file pass after Task 3's implementation lands; the file correctly reported the new sim_step-dispatch tests as RED (via `NotImplementedError`) between Task 1 and Task 3
- **Committed in:** `6d6e626` (test, RED) and `f172acc` (feat, GREEN for the sim_step-dispatch subset)

**3. [Rule 2 - Missing Critical] Added DESCENT->APPROACH completion condition not explicitly named in Task 3's threshold list**
- **Found during:** Task 3
- **Issue:** Task 3's action text explicitly names TAXI_OUT/TAXI_IN, DEPARTURE_ROLL, CLIMB, and APPROACH completion conditions, but omits when an arrival should leave DESCENT. Leaving `_is_phase_complete` return `False` for DESCENT would strand every arrival there permanently, since 03-RESEARCH.md's Pattern C explicitly documents "once an arrival's leg_index exhausts DET_2A_STAR.legs ... transition DESCENT -> APPROACH" as required behavior for PERF-04's arrival lifecycle.
- **Fix:** Added `Phase.DESCENT: procedure_leg_index >= len(aircraft.procedure.legs)` to `_is_phase_complete`, matching 03-RESEARCH.md Pattern C exactly.
- **Files modified:** `src/atc_sim/sim/aircraft.py`
- **Verification:** `tests/test_interpolation.py::test_descent_transitions_to_approach_once_legs_exhausted` passes; manual full-arrival harness confirms `[DESCENT, APPROACH, LANDED, TAXI_IN]`
- **Committed in:** `f172acc` (Task 3 commit)

---

**Total deviations:** 3 auto-fixed (1 blocking render-layer lockstep fix, 1 bug fix to obsolete tests, 1 missing-critical-functionality addition)
**Impact on plan:** All three were necessary consequences of the plan's own coordinate-rename and dispatch-rewrite scope, or were required to prevent a documented, researched pitfall (stranded DESCENT). No architectural scope creep — `app.py`'s actual nm->pixel rewiring remains untouched, deferred to 03-06 exactly as the plan specifies.

## Issues Encountered
None beyond the deviations documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `src/atc_sim/sim/aircraft.py`, `src/atc_sim/sim/procedure.py`, and `src/atc_sim/sim/interpolation.py` now present a stable, test-verified interface for 03-05's `demo_traffic.py` (`spawn_departure`, `spawn_arrival`, `update_demo_traffic`) to consume — `Aircraft`'s full constructor shape, `sim_step()`'s dispatch behavior, and `procedure.py`'s `compute_target`/`advance_leg_if_reached` are all exercised and correct
- Manually confirmed (outside automated test scope, since `demo_traffic.py` doesn't exist yet) that a hand-built departure and arrival Aircraft walk the exact phase sequences `tests/test_departure_flow.py`/`tests/test_arrival_flow.py` already assert — 03-05 should be able to wire `demo_traffic.py` around this plan's `sim_step`/`compute_target` with no further rework to this plan's files
- `render/radar.py`/`app.py` remain intentionally unmigrated to real nm->pixel projection (deferred to 03-06 per this plan's explicit scope boundary) — the render module's field names were kept in lockstep only, not its projection logic; 03-06 must add a `world_to_screen()` call at the aircraft draw site
- No blockers

---
*Phase: 03-aircraft-performance-flight-phase-fsm-procedure-following*
*Completed: 2026-07-06*

## Self-Check: PASSED

All 6 created/modified files (aircraft.py, procedure.py, interpolation.py, radar.py, test_interpolation.py, test_render_smoke.py) verified present on disk; all 4 task commit hashes (6d6e626, 7edaf41, befd9d9, f172acc) verified present in git log.
