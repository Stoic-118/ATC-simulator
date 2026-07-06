---
phase: 03-aircraft-performance-flight-phase-fsm-procedure-following
plan: 03
subsystem: sim
tags: [fsm, enum, phase-transitions]

# Dependency graph
requires:
  - phase: 03-01
    provides: "tests/test_phase_fsm.py (import-guarded PERF-02 spec asserting the exact 8-member enum, LEGAL_TRANSITIONS coverage, linear-chain walk, and illegal-skip rejection)"
provides:
  - "src/atc_sim/sim/phase.py: Phase enum (8 members), LEGAL_TRANSITIONS table, transition_to() guard"
affects: [03-04, 03-05, 03-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pure-leaf FSM module: no import of atc_sim.sim.* or pygame, independently unit-testable with zero Aircraft construction"
    - "Module-level ALL-CAPS constant table (LEGAL_TRANSITIONS) placed directly below the enum it governs, matching navdata/models.py's RestrictionKind convention"

key-files:
  created:
    - src/atc_sim/sim/phase.py
  modified: []

key-decisions:
  - "Copied RESEARCH.md's Pattern B example verbatim (enum members, LEGAL_TRANSITIONS shape, transition_to guard) with no rescaling needed, since the FSM has no unit/scale dimension to distort (unlike clock.py's MAX_FRAME_TIME)"

requirements-completed: [PERF-02]

coverage:
  - id: D1
    description: "8-member Phase enum (TAXI_OUT, DEPARTURE_ROLL, CLIMB, ENROUTE, DESCENT, APPROACH, LANDED, TAXI_IN), no ILS-capture or REMOVED sub-states"
    requirement: "PERF-02"
    verification:
      - kind: unit
        ref: "tests/test_phase_fsm.py::test_phase_has_exactly_eight_members, tests/test_phase_fsm.py::test_no_ils_capture_or_removal_sub_states"
        status: pass
    human_judgment: false
  - id: D2
    description: "LEGAL_TRANSITIONS covers every Phase member; transition_to() raises ValueError on illegal transitions and succeeds across the full linear TAXI_OUT->TAXI_IN chain"
    requirement: "PERF-02"
    verification:
      - kind: unit
        ref: "tests/test_phase_fsm.py::test_legal_transitions_covers_every_phase, tests/test_phase_fsm.py::test_transition_to_walks_full_linear_chain, tests/test_phase_fsm.py::test_transition_to_rejects_illegal_skip"
        status: pass
    human_judgment: false
  - id: D3
    description: "phase.py stays a pure, pygame-free leaf module (no atc_sim.sim.* imports), enforced by the architectural boundary test"
    requirement: "PERF-02"
    verification:
      - kind: unit
        ref: "python -m pytest tests/test_boundary.py -x -q"
        status: pass
    human_judgment: false

duration: 3min
completed: 2026-07-06
status: complete
---

# Phase 3 Plan 3: Flight-Phase FSM Summary

**Explicit 8-state flight-phase enum with a `LEGAL_TRANSITIONS` table and a `transition_to()` guard, implemented as a pure pygame-free leaf module.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-07-06T17:28:34Z
- **Completed:** 2026-07-06T17:31:19Z
- **Tasks:** 1
- **Files modified:** 1 (newly created)

## Accomplishments
- `src/atc_sim/sim/phase.py` created with the mandatory "MUST NOT import pygame" docstring sentence, no import of `atc_sim.sim.*`
- `Phase` enum with exactly the 8 roadmap-named members in the specified order; no `LOC_CAPTURED`/`GS_CAPTURED`/`REMOVED` sub-states (those are Phase 4 / list-membership scope)
- `LEGAL_TRANSITIONS: dict[Phase, set[Phase]]` covering all 8 members, `TAXI_IN` mapping to the empty set (terminal), with the forward-compatibility comment for `ENROUTE->DESCENT`/`DESCENT->APPROACH` preserved from RESEARCH.md
- `transition_to(current, new)` raises `ValueError` on any transition absent from `LEGAL_TRANSITIONS`, else returns `new`
- `tests/test_phase_fsm.py` activated from skipped and all 5 tests pass; `tests/test_boundary.py` confirms the module stays headless/pygame-free; full suite (`tests/ -q`) shows 35 passed, 3 skipped (remaining PERF-01/PERF-03/PERF-04 stubs still pending their own implementation plans), zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Phase enum, LEGAL_TRANSITIONS table, transition_to guard** - `d433d80` (feat)

**Plan metadata:** (this commit, docs: complete plan)

## Files Created/Modified
- `src/atc_sim/sim/phase.py` - `Phase` enum, `LEGAL_TRANSITIONS` table, `transition_to()` guard function

## Decisions Made
- Copied RESEARCH.md's Pattern B worked example verbatim (enum, table shape, guard function) since it required no rescaling or unit-mismatch correction, unlike prior plans' MAX_FRAME_TIME/bearing-value adjustments

## Deviations from Plan

None - plan executed exactly as written. The single task's `<action>` spec was followed directly; all `<acceptance_criteria>` were verified (file existence and docstring wording, exact 8-member enum with no forbidden members, `LEGAL_TRANSITIONS[Phase.TAXI_IN] == set()`, illegal-transition `ValueError`, full linear walk succeeding, `test_phase_fsm.py` and `test_boundary.py` both green).

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `sim/phase.py`'s `Phase`, `LEGAL_TRANSITIONS`, and `transition_to` are now available for 03-04 (aircraft.py evolution / phase dispatch), 03-05 (demo_traffic.py spawn/removal orchestration), and 03-06 to consume
- The module remains a pure leaf with zero `Aircraft` coupling, so completion-condition logic that decides *when* to call `transition_to` still belongs in `aircraft.py`'s dispatch, per the plan's explicit circular-import-avoidance rationale
- No blockers

## Self-Check: PASSED

Created file `src/atc_sim/sim/phase.py` verified present on disk; commit hash `d433d80` verified present in git log.
