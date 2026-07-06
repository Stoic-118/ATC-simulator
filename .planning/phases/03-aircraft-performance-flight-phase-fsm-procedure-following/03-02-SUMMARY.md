---
phase: 03-aircraft-performance-flight-phase-fsm-procedure-following
plan: 02
subsystem: sim
tags: [pydantic, kinematics, performance-model, fleet-data]

# Dependency graph
requires:
  - phase: 03-aircraft-performance-flight-phase-fsm-procedure-following
    provides: "03-01: tests/test_performance.py (PERF-01 assertions), Nyquist import-guard scaffold"
provides:
  - "src/atc_sim/sim/performance.py: frozen PerformanceProfile Pydantic model"
  - "FLEET dict of 4 hand-authored aircraft-type constants (Boeing 737-800, Embraer E175, ATR 72-600, Cessna Citation CJ2+)"
  - "turn_rate_deg_per_sec(bank_deg, speed_kt) — the one speed-coupled turn-rate formula"
  - "step_toward_value(current, target, max_delta) — generic non-overshooting scalar mover, for altitude and speed"
  - "step_toward_heading(current_deg, target_deg, max_turn_deg) — shortest-path, non-overshooting heading turn across the 0/360 wrap"
  - "glidepath_altitude_ft(distance_to_threshold_nm) — simplified 3-degree rule-of-three glidepath altitude"
affects: [03-03, 03-04, 03-05, 03-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Frozen Pydantic reference-data model (ConfigDict(frozen=True) + Field(gt=0.0) bounds), matching navdata/models.py convention, applied to a sim/ module for the first time"
    - "Module-level pure kinematics functions (not model methods) taking profile fields + current state + target as plain arguments, matching navdata/geo.py's pure-function style"

key-files:
  created:
    - src/atc_sim/sim/performance.py
  modified: []

key-decisions:
  - "Included turn_rate_deg_per_sec in the Task 1 commit (not deferred to Task 2) because tests/test_performance.py imports FLEET, PerformanceProfile, and turn_rate_deg_per_sec in a single import statement — deferring it would have made the whole test file error at collection rather than fail individual assertions, and 03-RESEARCH.md's own Pattern A code block groups the model, fleet constants, and turn_rate_deg_per_sec together as one unit"
  - "step_toward_value's tie-break (current == target) returns current unchanged rather than falling into either branch, avoiding a redundant min()/max() call on an already-settled value"

requirements-completed: [PERF-01]

coverage:
  - id: D1
    description: "Frozen PerformanceProfile model with gt=0.0 (and bank lt=45.0) validation bounds, rejecting non-positive rates and rejecting post-construction mutation"
    requirement: "PERF-01"
    verification:
      - kind: unit
        ref: "tests/test_performance.py#test_performance_profile_rejects_non_positive_climb_rate"
        status: pass
      - kind: unit
        ref: "tests/test_performance.py#test_performance_profile_is_frozen"
        status: pass
    human_judgment: false
  - id: D2
    description: "FLEET contains exactly 4 profiles whose climb/descent/terminal-speed/bank fields are not all identical across the fleet"
    requirement: "PERF-01"
    verification:
      - kind: unit
        ref: "tests/test_performance.py#test_fleet_has_exactly_four_profiles"
        status: pass
      - kind: unit
        ref: "tests/test_performance.py#test_fleet_profiles_are_not_all_identical"
        status: pass
    human_judgment: false
  - id: D3
    description: "turn_rate_deg_per_sec is coupled to current groundspeed, not an independent per-type constant — a faster aircraft turns more slowly at the same bank angle"
    requirement: "PERF-01"
    verification:
      - kind: unit
        ref: "tests/test_performance.py#test_turn_rate_coupled_to_speed"
        status: pass
    human_judgment: false
  - id: D4
    description: "step_toward_value/step_toward_heading/glidepath_altitude_ft never overshoot their targets and satisfy the plan's exact acceptance-criteria values"
    requirement: "PERF-01"
    verification:
      - kind: unit
        ref: "manual python -c verification: step_toward_value(0,10,3)==3, step_toward_value(0,2,3)==2, step_toward_heading wrap cases, glidepath_altitude_ft(10)==3000.0, glidepath_altitude_ft(0)==0.0 — all asserted true"
        status: pass
    human_judgment: false

duration: 15min
completed: 2026-07-06
status: complete
---

# Phase 3 Plan 2: PerformanceProfile & Kinematics Helpers Summary

**Frozen PerformanceProfile Pydantic model, a 4-type FLEET (737-800/E175/ATR72-600/CJ2+) spanning climb/descent/speed/bank envelopes, plus speed-coupled turn_rate_deg_per_sec and three generic non-overshooting kinematics helpers (step_toward_value, step_toward_heading, glidepath_altitude_ft).**

## Performance

- **Duration:** 15 min
- **Started:** 2026-07-06T18:12:00+01:00
- **Completed:** 2026-07-06T18:27:25+01:00
- **Tasks:** 2
- **Files modified:** 1 (newly created)

## Accomplishments
- `PerformanceProfile` frozen Pydantic model (`ConfigDict(frozen=True)`, `Field(gt=0.0)` / `Field(gt=0.0, lt=45.0)` bounds) mirroring `navdata/models.py`'s frozen-model convention, applied to a `sim/` module for the first time
- `FLEET` dict of 4 hand-authored constants (`BOEING_737_800`, `EMBRAER_E175`, `ATR_72_600`, `CESSNA_CJ2_PLUS`) with `[ASSUMED]`-tagged sourcing comments noting these are simplified in-sim terminal-area values, not raw real-world cruise figures
- `turn_rate_deg_per_sec(bank_deg, speed_kt)` — the one `1091*tan(bank)/speed` formula, coupling turn rate to current groundspeed (Pitfall 7) rather than an independent per-type constant
- `step_toward_value`, `step_toward_heading`, `glidepath_altitude_ft` — pure module-level kinematics helpers reused across altitude, speed, and heading dispatch in later plans
- `tests/test_performance.py` fully activated: 5/5 tests passing (up from all-skipped in 03-01); `tests/test_boundary.py` still passes (no pygame import); full suite green (30 passed, 4 skipped)

## Task Commits

Each task was committed atomically:

1. **Task 1: PerformanceProfile model + FLEET constants** - `f67d143` (feat)
2. **Task 2: Shared kinematics helper functions** - `143bb5f` (feat)

**Plan metadata:** (this commit, docs: complete plan)

_Note: turn_rate_deg_per_sec was included in Task 1's commit rather than Task 2's, per the key-decision above._

## Files Created/Modified
- `src/atc_sim/sim/performance.py` - `PerformanceProfile` model, `FLEET` constants, `turn_rate_deg_per_sec`, `step_toward_value`, `step_toward_heading`, `glidepath_altitude_ft`

## Decisions Made
- Grouped `turn_rate_deg_per_sec` into Task 1's commit instead of Task 2's, since the test file's single combined import statement (`from atc_sim.sim.performance import FLEET, PerformanceProfile, turn_rate_deg_per_sec`) requires the function to exist for Task 1's own verification command (`pytest tests/test_performance.py -x -q`) to collect and pass at all — consistent with 03-RESEARCH.md's Pattern A code block, which presents the model, fleet constants, and this function as one unit
- `step_toward_value` returns `current` unchanged (no min/max call) when `current == target`, a minor clarity choice with no behavioral difference from falling into either branch

## Deviations from Plan

None - plan executed exactly as written. The only adjustment (moving `turn_rate_deg_per_sec` into the Task 1 commit) is a task-boundary/commit-grouping choice, not a functional deviation — all four kinematics functions and the model/fleet were delivered exactly as specified, with identical field names, formulas, and constant values.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `src/atc_sim/sim/performance.py` is now the fully-realized leaf module every later Phase 3 plan consumes: `sim/phase.py` (03-03), `sim/procedure.py`, and the evolved `sim/aircraft.py` (03-04) can import `PerformanceProfile`, `FLEET`, and all four kinematics helpers with a stable, test-verified interface
- `tests/test_performance.py` (PERF-01) is fully green; `tests/test_phase_fsm.py`, `tests/test_procedure_following.py`, `tests/test_departure_flow.py`, `tests/test_arrival_flow.py` remain correctly skipped pending their own implementation plans
- No blockers

---
*Phase: 03-aircraft-performance-flight-phase-fsm-procedure-following*
*Completed: 2026-07-06*

## Self-Check: PASSED

All created files verified present on disk (`src/atc_sim/sim/performance.py`, this SUMMARY.md); both task commit hashes (f67d143, 143bb5f) verified present in git log.
