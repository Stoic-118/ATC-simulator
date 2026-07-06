---
phase: 03-aircraft-performance-flight-phase-fsm-procedure-following
plan: 05
subsystem: sim
tags: [demo-harness, spawn, fleet-rotation, lifecycle]

# Dependency graph
requires:
  - phase: 03-02
    provides: "sim/performance.py: FLEET, PerformanceProfile, BOEING_737_800/EMBRAER_E175/ATR_72_600/CESSNA_CJ2_PLUS"
  - phase: 03-04
    provides: "sim/aircraft.py: Aircraft (nm-space, phase/procedure/performance state), sim_step() per-phase dispatcher; sim/procedure.py: compute_target/advance_leg_if_reached"
provides:
  - "src/atc_sim/sim/demo_traffic.py: spawn_departure(), spawn_arrival(), update_demo_traffic(aircraft_list, dt)"
  - "Independent round-robin fleet-type rotation per spawn slot (departure/arrival), with reset_fleet_rotation() test hook"
  - "Full autonomous departure lifecycle (spawn at stand -> TAXI_OUT -> DEPARTURE_ROLL -> CLIMB -> ENROUTE -> removed) and arrival lifecycle (spawn at DET FL170 -> DESCENT -> APPROACH -> LANDED -> TAXI_IN -> removed), looping indefinitely"
affects: [03-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Module-level round-robin rotation state encapsulated in a small _RotationState object with a reset_fleet_rotation() test hook, rather than bare module globals"
    - "Spawn functions take an optional PerformanceProfile parameter defaulting to the next rotated fleet type, so callers (tests) can invoke them with zero arguments while update_demo_traffic's respawn path still drives explicit rotation"

key-files:
  created:
    - src/atc_sim/sim/demo_traffic.py
  modified:
    - src/atc_sim/sim/aircraft.py

key-decisions:
  - "spawn_departure/spawn_arrival take an optional `performance: PerformanceProfile | None = None` parameter (defaulting to the next rotated fleet type) rather than the plan's literal `spawn_departure(performance) -> Aircraft` required-argument signature, because tests/test_departure_flow.py and tests/test_arrival_flow.py call both functions with zero arguments -- the test files are the actual contract and take precedence over the plan's prose signature"
  - "Departure/arrival removal conditions distinguish flight kind purely by Phase membership (ENROUTE only ever reached by departures; TAXI_IN only ever reached by arrivals, this phase), rather than adding a kind/is_departure field to Aircraft -- consistent with 03-04's decision to keep Aircraft free of a flight-kind field"
  - "Arrival TAXI_IN removal uses a demo_traffic-owned constant (_ARRIVAL_TAXI_IN_REMOVAL_SEC = 18.0), not aircraft.py's internal _TAXI_DURATION_SEC, since that constant only governs TAXI_OUT's own timer and TAXI_IN is now explicitly excluded from aircraft.py's auto-transition logic (see Rule 1 fix below)"
  - "_FLEET_ROTATION is an explicit list of the four named PerformanceProfile constants (matching the plan's literal example order), not derived from FLEET.values() insertion order -- decouples rotation order from performance.py's internal dict construction order"

requirements-completed: [PERF-03, PERF-04]

coverage:
  - id: D1
    description: "spawn_departure() returns an Aircraft at phase TAXI_OUT on OLNEY_2B_SID at a stand position; spawn_arrival() returns an Aircraft at phase DESCENT on DET_2A_STAR at altitude_ft == 17000.0 (the DET fix's real FL170 restriction)"
    requirement: "PERF-03, PERF-04"
    verification:
      - kind: unit
        ref: "tests/test_arrival_flow.py::test_arrival_spawns_airborne_at_det_fl170"
        status: pass
    human_judgment: false
  - id: D2
    description: "A full departure lifecycle (TAXI_OUT -> DEPARTURE_ROLL -> CLIMB -> ENROUTE) runs to completion headlessly and the aircraft is removed from active traffic once OLNEY_2B_SID's legs are exhausted while ENROUTE"
    requirement: "PERF-03"
    verification:
      - kind: integration
        ref: "tests/test_departure_flow.py::test_departure_flow_visits_phases_in_order_and_is_removed"
        status: pass
    human_judgment: false
  - id: D3
    description: "A full arrival lifecycle (DESCENT -> APPROACH -> LANDED -> TAXI_IN) runs to completion headlessly and the aircraft is removed from active traffic once its TAXI_IN timer elapses"
    requirement: "PERF-04"
    verification:
      - kind: integration
        ref: "tests/test_arrival_flow.py::test_arrival_flow_visits_phases_in_order_and_is_removed"
        status: pass
    human_judgment: false
  - id: D4
    description: "update_demo_traffic respawns a fresh departure+arrival pair once the active-traffic list empties, rotating fleet types independently per slot so >=3 distinct types fly within 1-2 loop iterations; no REMOVED/GONE Phase member was added (removal stays list membership)"
    requirement: "PERF-03, PERF-04"
    verification:
      - kind: other
        ref: "manual python harness: reset_fleet_rotation() then 6 consecutive spawn_departure()/spawn_arrival() calls each produced all 4 FLEET type names in round-robin order (Boeing 737-800, Embraer E175, ATR 72-600, Cessna Citation CJ2+, Boeing 737-800, Embraer E175); grep for REMOVED/GONE in sim/phase.py returned no matches"
        status: pass
    human_judgment: false

duration: 20min
completed: 2026-07-06
status: complete
---

# Phase 3 Plan 5: Demo Traffic Harness Summary

**`demo_traffic.py` spawn/removal/loop orchestration: `spawn_departure`/`spawn_arrival` build aircraft directly on the OLNEY 2B SID and DET 2A STAR, `update_demo_traffic` steps + removes + respawns with independent round-robin fleet-type rotation per slot, and fixed a latent StopIteration bug in `aircraft.py`'s TAXI_IN auto-transition that the arrival flow test's longer tick budget exposed.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-07-06T18:20:00Z
- **Completed:** 2026-07-06T18:40:00Z
- **Tasks:** 1
- **Files modified:** 2 (1 created, 1 modified)

## Accomplishments
- `src/atc_sim/sim/demo_traffic.py` created: `spawn_departure()`/`spawn_arrival()` construct aircraft directly on the real OLNEY 2B SID (stand position, TAXI_OUT) and DET 2A STAR (DET fix at FL170, DESCENT); `update_demo_traffic(aircraft_list, dt)` steps every aircraft via `sim_step`, removes departures once `ENROUTE` with the SID's legs exhausted and arrivals once `TAXI_IN`'s timer elapses (list membership, never a Phase value), and respawns a rotated pair once the list empties
- Independent round-robin fleet-type rotation for the departure slot and arrival slot, encapsulated in a small `_RotationState` object with a `reset_fleet_rotation()` test hook; manually verified all 4 `FLEET` types rotate through both slots within 1-2 loop iterations (RESEARCH "3 distinct types visibly differentiated" pitfall satisfied)
- Both previously-skipped flow tests now activate and pass: `tests/test_departure_flow.py` (full `[TAXI_OUT, DEPARTURE_ROLL, CLIMB, ENROUTE]` sequence, removed once `OLNEY_2B_SID` exhausts) and `tests/test_arrival_flow.py` (spawn-at-FL170 assertion plus full `[DESCENT, APPROACH, LANDED, TAXI_IN]` sequence, removed once `TAXI_IN`'s timer elapses)
- Full suite green: 51 passed (up from 48 passed / 2 skipped before this plan); `tests/test_boundary.py` confirms `demo_traffic.py` stays headless

## Task Commits

Each task was committed atomically:

1. **Task 1: spawn_departure / spawn_arrival + per-tick update with removal & looping** - `760d25a` (feat)

**Plan metadata:** (this commit, docs: complete plan)

## Files Created/Modified
- `src/atc_sim/sim/demo_traffic.py` - `spawn_departure`, `spawn_arrival`, `update_demo_traffic`, `_FLEET_ROTATION`, `_RotationState`, `reset_fleet_rotation`
- `src/atc_sim/sim/aircraft.py` - `_is_phase_complete` no longer auto-completes `TAXI_IN` (Rule 1 bug fix, see Deviations)

## Decisions Made
See `key-decisions` in frontmatter for the full list. Highlights: `spawn_departure`/`spawn_arrival` take an optional `performance` parameter (defaulting to the next rotated type) rather than a required one, matching the actual test contract; removal conditions distinguish departure vs. arrival by Phase membership alone (no new `Aircraft` field).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed StopIteration when an arrival's TAXI_IN timer elapsed**
- **Found during:** Task 1, while running `tests/test_arrival_flow.py`'s full lifecycle test (6000 ticks, comfortably exceeding `TAXI_IN`'s timer)
- **Issue:** `aircraft.py`'s `_is_phase_complete` treated `TAXI_OUT` and `TAXI_IN` identically (`phase_elapsed_sec >= _TAXI_DURATION_SEC`), but `Phase.TAXI_IN` is terminal (`LEGAL_TRANSITIONS[Phase.TAXI_IN] == set()`). Once an arrival's `TAXI_IN` timer elapsed, `sim_step()` called `transition_to(TAXI_IN, _next_phase(TAXI_IN))`, and `_next_phase()`'s `next(iter(LEGAL_TRANSITIONS[TAXI_IN]))` raised `StopIteration` trying to iterate an empty set — a hard crash that would have made every arrival flow test fail non-deterministically depending on tick budget. This was a latent bug in 03-04's code, invisible until this plan's flow test ran `TAXI_IN` long enough to hit it.
- **Fix:** Changed `_is_phase_complete`'s taxi-timer check to only fire for `Phase.TAXI_OUT`; added a comment explaining why `TAXI_IN`'s "is it done" question is answered externally by `demo_traffic.py`'s removal check instead (list membership, never a Phase-FSM transition — matching `phase.py`'s own documented design and this phase's "Removal is not a phase" pitfall).
- **Files modified:** `src/atc_sim/sim/aircraft.py`
- **Verification:** `python -m pytest tests/ -q` — 51 passed, including the full-length `test_arrival_flow_visits_phases_in_order_and_is_removed`
- **Committed in:** `760d25a` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix in a file outside this plan's `files_modified` list, but a direct, unavoidable consequence of exercising `TAXI_IN` to completion for the first time)
**Impact on plan:** Necessary to make the arrival flow test pass at all; no scope creep — the fix is a one-line completion-condition narrowing plus an explanatory comment, not a new feature.

## Issues Encountered
None beyond the deviation documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `src/atc_sim/sim/demo_traffic.py` presents a stable, test-verified interface (`spawn_departure`, `spawn_arrival`, `update_demo_traffic`) for 03-06's `app.py` rewiring: replace the single `Aircraft.spawn_default()` call with `demo_traffic.spawn_departure()`/`spawn_arrival()` seeding a list, and replace the single `sim_step(aircraft, dt)` call in `on_tick` with `demo_traffic.update_demo_traffic(active_traffic, dt)`
- PERF-03/PERF-04 (already marked Complete in REQUIREMENTS.md by 03-04's executor, ahead of this plan landing) are now genuinely and fully satisfied end-to-end: a departure literally spawns at a stand and taxis/climbs via the SID, an arrival literally spawns at the DET fix at FL170 and descends/lands/taxis-in, both verified headlessly by the now-passing flow tests
- `app.py` itself remains unmigrated (render layer still reads `aircraft.x`/`aircraft.y` pixel fields from the Phase-1 `Aircraft.spawn_default()` call) — this is 03-06's explicit scope, untouched by this plan
- No blockers

---
*Phase: 03-aircraft-performance-flight-phase-fsm-procedure-following*
*Completed: 2026-07-06*

## Self-Check: PASSED

Created file `src/atc_sim/sim/demo_traffic.py` and this SUMMARY.md verified present on disk; both commit hashes (`760d25a`, `9f0abeb`) verified present in git log.
