---
phase: 03-aircraft-performance-flight-phase-fsm-procedure-following
plan: 01
subsystem: testing
tags: [pytest, nyquist, tdd-scaffold, fsm, pydantic]

# Dependency graph
requires:
  - phase: 02-navdata-coordinate-projection
    provides: EGGW navdata (OLNEY_2B_SID, DET_2A_STAR, EGGW_RUNWAY), navdata/geo.py projection + bearing helpers
provides:
  - "tests/conftest.py: phase_recorder fixture / record_phases() headless tick-stepping helper, zero import dependency on atc_sim.sim.* or pygame"
  - "Five import-guarded requirement test files (test_performance.py, test_phase_fsm.py, test_procedure_following.py, test_departure_flow.py, test_arrival_flow.py), one per Phase 3 requirement, each pytest.importorskip-guarded until its sim module lands"
  - "Implicit interface contract for later Phase 3 plans: sim/performance.py (PerformanceProfile, FLEET, turn_rate_deg_per_sec), sim/phase.py (Phase enum, LEGAL_TRANSITIONS, transition_to), sim/procedure.py (Targets, compute_target, advance_leg_if_reached), sim/aircraft.py (evolved Aircraft with x_nm/y_nm/altitude_ft/phase/procedure/procedure_leg_index/performance fields), sim/demo_traffic.py (spawn_departure, spawn_arrival, update_demo_traffic)"
affects: [03-02, 03-03, 03-04, 03-05, 03-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "pytest.importorskip() at test-module scope to keep the suite green while implementation modules don't exist yet (Nyquist scaffold pattern)"
    - "Shared conftest.py fixture (phase_recorder) injected via dependency-injected step_fn, avoiding any import coupling to unimplemented sim modules"

key-files:
  created:
    - tests/conftest.py
    - tests/test_performance.py
    - tests/test_phase_fsm.py
    - tests/test_procedure_following.py
    - tests/test_departure_flow.py
    - tests/test_arrival_flow.py
  modified: []

key-decisions:
  - "Used 'not all equal' (len(set) > 1) rather than strict pairwise-distinct assertions for PerformanceProfile fleet fields, since 03-RESEARCH.md's own recommended fleet values intentionally share some values across types (e.g. max_bank_deg 25/25/22/27, terminal_speed_kt 250/250/180/220) — a strict pairwise-distinct check would reject the very fleet data this phase's research already specified"
  - "Computed expected test_procedure_following.py bearing values via the same local-plane atan2 math compute_target() must use (via navdata.geo.project_to_local_xy_nm), not a fresh geodesic call, so projection distortion doesn't produce a false test failure"
  - "Named the demo per-tick orchestration entry point update_demo_traffic(aircraft_list, dt), matching 03-PATTERNS.md's own suggested name, so the flow tests' expectations are consistent with what the later demo_traffic.py plan is expected to implement"
  - "Departure/arrival flow tests use generous fixed tick budgets (4000/6000 ticks) as a hard cap rather than a wait condition, computed from real OLNEY 2B SID / DET 2A STAR leg distances, so a stalled implementation fails with a visibly incomplete phase sequence instead of hanging"

requirements-completed: [PERF-01, PERF-02, PERF-03, PERF-04, PROC-01]

coverage:
  - id: D1
    description: "Shared headless phase-recorder test fixture (tests/conftest.py) reused by both flow tests"
    verification:
      - kind: unit
        ref: "python -m pytest tests/ -q (conftest.py collects with zero errors; existing suite unaffected)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Five requirement test files exist as import-guarded specs, one per PERF-01/02/03/04 and PROC-01, and the full suite stays green (new tests reported as skipped) until each corresponding sim module is implemented"
    requirement: "PERF-01, PERF-02, PERF-03, PERF-04, PROC-01"
    verification:
      - kind: unit
        ref: "python -m pytest tests/ -q -rs (5 new files reported SKIPPED with correct importorskip reason, 25 pre-existing tests still pass)"
        status: pass
    human_judgment: false

duration: 6min
completed: 2026-07-06
status: complete
---

# Phase 3 Plan 1: Nyquist Test Scaffold Summary

**Five import-guarded requirement test files plus a shared headless phase-recorder fixture, giving every subsequent Phase 3 implementation plan an automated green/red signal from the moment its module lands.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-07-06T17:12:45Z
- **Completed:** 2026-07-06T17:18:15Z
- **Tasks:** 2
- **Files modified:** 6 (all newly created)

## Accomplishments
- Shared `phase_recorder` pytest fixture in `tests/conftest.py` — a dependency-free `record_phases(aircraft, step_fn, n_ticks, tick_dt)` helper that collapses consecutive duplicate phases into an ordered transition sequence, with zero import dependency on `atc_sim.sim.*` or `pygame`
- `tests/test_performance.py` (PERF-01): asserts `FLEET` has exactly 4 profiles, none of the four key numeric fields collapse to a single value across the fleet, `PerformanceProfile` rejects non-positive `climb_rate_fpm` and is frozen, and `turn_rate_deg_per_sec()` is coupled to groundspeed (not an independent per-type constant)
- `tests/test_phase_fsm.py` (PERF-02): asserts `Phase` has exactly the 8 roadmap-named members (no ILS-capture or `REMOVED` sub-states), `LEGAL_TRANSITIONS` covers every member, the full linear chain walks without error, and an illegal skip (`TAXI_OUT` -> `CLIMB`) raises `ValueError`
- `tests/test_procedure_following.py` (PROC-01): the load-bearing regression test for the "restriction look-ahead omitted" pitfall — asserts `compute_target()` on the DET 2A STAR's unrestricted LOFFO leg targets ABBOT's FL080 (not a level hold at FL170), asserts the returned heading is true->magnetic converted exactly once, and asserts `advance_leg_if_reached()` increments `procedure_leg_index` on fix capture
- `tests/test_departure_flow.py` / `tests/test_arrival_flow.py` (PERF-03/PERF-04): full-lifecycle headless integration tests using the shared `phase_recorder` fixture, asserting the exact expected phase sequences (`[TAXI_OUT, DEPARTURE_ROLL, CLIMB, ENROUTE]` and `[DESCENT, APPROACH, LANDED, TAXI_IN]`) and active-traffic-list removal
- Full suite verified green: 25 pre-existing tests pass, 5 new tests report as SKIPPED with the correct `pytest.importorskip` reason (module not found), zero collection errors

## Task Commits

Each task was committed atomically:

1. **Task 1: Shared headless phase-recorder fixture in tests/conftest.py** - `4cad223` (feat)
2. **Task 2: Five requirement test files (import-guarded stubs with real assertions)** - `c8633cf` (test)

**Plan metadata:** (this commit, docs: complete plan)

## Files Created/Modified
- `tests/conftest.py` - `phase_recorder` fixture / `record_phases()` tick-stepping + phase-sequence-collapsing helper
- `tests/test_performance.py` - PERF-01 stubs: FLEET distinctness, frozen/validated PerformanceProfile, speed-coupled turn rate
- `tests/test_phase_fsm.py` - PERF-02 stubs: 8-member Phase enum, LEGAL_TRANSITIONS coverage, linear chain walk, illegal-skip rejection
- `tests/test_procedure_following.py` - PROC-01 stubs: restriction look-ahead regression, true->magnetic heading, leg-capture advance
- `tests/test_departure_flow.py` - PERF-03 stub: full departure lifecycle phase sequence + active-traffic removal
- `tests/test_arrival_flow.py` - PERF-04 stub: full arrival lifecycle phase sequence + spawn altitude + active-traffic removal

## Decisions Made
- Used "not all equal" fleet-distinctness assertions instead of strict pairwise-distinct, since 03-RESEARCH.md's own recommended fleet values intentionally repeat some numbers across types (see key-decisions above for detail)
- Computed expected bearing values in `test_procedure_following.py` via the same local-plane `atan2` math `compute_target()` is specified to use, rather than a fresh geodesic call, avoiding a false failure from map-projection distortion
- Named the demo per-tick orchestration entry point `update_demo_traffic(aircraft_list, dt)`, matching 03-PATTERNS.md's suggested name, so this plan's test expectations are consistent with the interface the later `demo_traffic.py` implementation plan is expected to expose
- Chose generous, distance-derived fixed tick budgets (4000 ticks / 2000 sim-seconds for departure, 6000 ticks / 3000 sim-seconds for arrival) as hard caps rather than open-ended waits, so a future stalled implementation fails visibly rather than hanging the test suite

## Deviations from Plan

None - plan executed exactly as written. Both tasks matched their `<action>` specs; all `<acceptance_criteria>` were verified directly (file existence, no `atc_sim.sim`/`pygame` imports, full suite green with 5 new files skipped).

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- The Nyquist scaffold is in place: every remaining Phase 3 requirement (PERF-01 through PERF-04, PROC-01) now has an executable, currently-skipped test that will activate automatically the moment its corresponding `sim/` module is implemented in a later wave
- Later plans implementing `sim/performance.py`, `sim/phase.py`, `sim/procedure.py`, `sim/aircraft.py` (evolved), and `sim/demo_traffic.py` should conform to the exact names/shapes referenced by these tests (documented above and in 03-RESEARCH.md / 03-PATTERNS.md) to avoid re-deriving an interface that already has a test contract
- No blockers

---
*Phase: 03-aircraft-performance-flight-phase-fsm-procedure-following*
*Completed: 2026-07-06*
