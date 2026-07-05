---
phase: 01-walking-skeleton-sim-clock-radar-render-loop
plan: 02
subsystem: sim
tags: [fixed-timestep, accumulator, pytest, tdd]

# Dependency graph
requires:
  - phase: 01-01
    provides: src-layout package skeleton (src/atc_sim/sim/), pytest config, sim/render boundary guard test
provides:
  - SimClock fixed-timestep accumulator (src/atc_sim/sim/clock.py) satisfying CORE-01 and CORE-02
  - Headless test suite (tests/test_clock.py) proving frame-rate independence and capped catch-up
affects: [01-03-aircraft-interpolation, 01-04-render-loop, 01-05-app-entrypoint]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Fixed-timestep accumulator with dual-layer catch-up cap: frame-time clamp (MAX_FRAME_TIME) bounds a single slow frame's backlog, ticks-per-frame cap (MAX_TICKS_PER_FRAME) bounds catch-up work per advance() call; excess backlog beyond the cap is dropped and tracked in dropped_tick_seconds rather than retained to burst later"

key-files:
  created:
    - src/atc_sim/sim/clock.py
    - tests/test_clock.py
  modified: []

key-decisions:
  - "Rescaled MAX_FRAME_TIME from RESEARCH.md's literal 0.25 to 5.0: at this project's 2.0Hz sim rate (TICK_DT=0.5), a 0.25s clamp is smaller than a single tick, making the MAX_TICKS_PER_FRAME cap mathematically unreachable in a single advance() call and dropped_tick_seconds permanently stuck at 0 — this directly contradicted the plan's own required CORE-02 test (a single 3.0s stall must hit the tick cap and record dropped backlog). 5.0 stays comfortably above MAX_TICKS_PER_FRAME * TICK_DT (2.5s) so the tick-per-frame cap is the operative bound for realistic multi-second stalls, while still acting as an outer backstop against pathological real_dt values."

patterns-established:
  - "SimClock.advance(real_dt, on_tick) -> float: pure function of wall-clock dt and a tick callback, no pygame import, returns interpolation alpha in [0.0, 1.0) for the render layer"

requirements-completed: [CORE-01, CORE-02]

coverage:
  - id: D1
    description: "Tick count is identical regardless of render-frame-rate split of the same total simulated wall time (frame-rate-independent motion)"
    requirement: "CORE-01"
    verification:
      - kind: unit
        ref: "tests/test_clock.py#test_tick_count_independent_of_call_frequency"
        status: pass
    human_judgment: false
  - id: D2
    description: "A single large real_dt (simulated stall) drains at most MAX_TICKS_PER_FRAME ticks in one advance() call, with no exception and no unbounded loop"
    requirement: "CORE-02"
    verification:
      - kind: unit
        ref: "tests/test_clock.py#test_stall_caps_ticks_per_frame"
        status: pass
    human_judgment: false
  - id: D3
    description: "Backlog beyond the cap is dropped (accumulator reset to 0, dropped_tick_seconds recorded) rather than retained to burst on a later frame — spiral-of-death prevention"
    requirement: "CORE-02"
    verification:
      - kind: unit
        ref: "tests/test_clock.py#test_backlog_beyond_cap_is_dropped"
        status: pass
    human_judgment: false
  - id: D4
    description: "advance() always returns alpha in [0.0, 1.0) for render-side interpolation"
    verification:
      - kind: unit
        ref: "tests/test_clock.py#test_advance_returns_alpha_in_range"
        status: pass
    human_judgment: false
  - id: D5
    description: "on_tick is invoked with tick_dt (0.5 at 2Hz) as its argument, once per drained tick"
    verification:
      - kind: unit
        ref: "tests/test_clock.py#test_on_tick_receives_tick_dt"
        status: pass
    human_judgment: false
  - id: D6
    description: "sim/clock.py stays headlessly testable — no pygame import"
    requirement: "CORE-03"
    verification:
      - kind: unit
        ref: "tests/test_boundary.py#test_sim_package_never_imports_pygame"
        status: pass
    human_judgment: false

# Metrics
duration: ~10min
completed: 2026-07-05
status: complete
---

# Phase 01 Plan 02: Fixed-Timestep Sim Clock Summary

**SimClock accumulator (`src/atc_sim/sim/clock.py`) implementing 2Hz fixed-timestep ticks decoupled from render frame rate, with a dual-layer capped catch-up (frame-time clamp + ticks-per-frame cap) that drops excess backlog instead of spiraling — proven by five headless pytest cases.**

## Performance

- **Duration:** ~10 min active execution (RED test authoring + investigation, GREEN implementation + constant fix)
- **Started:** 2026-07-05T11:13:29+01:00 (Task 1 commit)
- **Completed:** 2026-07-05T11:18:45+01:00 (Task 2 commit)
- **Tasks:** 2 (RED, GREEN)
- **Files modified:** 2 (tests/test_clock.py, src/atc_sim/sim/clock.py)

## Accomplishments
- Wrote five failing tests (`tests/test_clock.py`) fully specifying `SimClock`'s frame-rate-independence and capped-catch-up contract before any implementation existed (confirmed RED via ImportError)
- Implemented `SimClock` in `src/atc_sim/sim/clock.py`: `SIM_HZ`/`TICK_DT`/`MAX_FRAME_TIME`/`MAX_TICKS_PER_FRAME` module constants, `advance(real_dt, on_tick) -> float` draining ticks in a bounded loop, `dropped_tick_seconds` visibility counter for dropped backlog
- Discovered and fixed a real calibration bug in the researched reference constants during GREEN (see Deviations) — the literal `MAX_FRAME_TIME = 0.25` from RESEARCH.md/PATTERNS.md made the ticks-per-frame cap unreachable at this project's 2Hz tick rate, which would have silently broken CORE-02's stall-drop behavior
- All five clock tests plus the pre-existing sim/render boundary guard (`tests/test_boundary.py`) pass green

## Task Commits

Each task was committed atomically:

1. **Task 1: RED — failing tests for the accumulator clock** - `6cb5dcd` (test)
2. **Task 2: GREEN — implement SimClock to pass the tests** - `e361b2d` (feat)

**Plan metadata:** commit pending (this SUMMARY.md + STATE.md + ROADMAP.md commit, created next)

## Files Created/Modified
- `tests/test_clock.py` - Five pytest cases specifying tick-count frame-rate independence, per-frame tick cap, backlog-drop-on-stall, alpha return-range, and on_tick argument contract
- `src/atc_sim/sim/clock.py` - `SimClock` fixed-timestep accumulator with capped catch-up; module constants `SIM_HZ`, `TICK_DT`, `MAX_FRAME_TIME`, `MAX_TICKS_PER_FRAME`

## Decisions Made
- Rescaled `MAX_FRAME_TIME` from the researched literal `0.25` to `5.0` — see Deviations below for full rationale. `SIM_HZ=2.0`, `TICK_DT=0.5`, and `MAX_TICKS_PER_FRAME=5` were kept exactly as researched.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] MAX_FRAME_TIME=0.25 made the ticks-per-frame cap unreachable at this project's 2Hz sim rate**
- **Found during:** Task 2 (GREEN implementation) — running the RED tests against the literal RESEARCH.md/PATTERNS.md reference code
- **Issue:** RESEARCH.md's canonical example (copied verbatim per the plan's Task 2 action) pairs `MAX_FRAME_TIME = 0.25` with `TICK_DT = 0.5` (2Hz). Since `advance()` clamps `real_dt` to `MAX_FRAME_TIME` *before* adding it to the accumulator, a single `advance(3.0)` call only ever adds 0.25s to the accumulator — less than one tick (0.5s) — so the `while` loop never runs, `dropped_tick_seconds` stays permanently 0, and `test_stall_caps_ticks_per_frame`/`test_backlog_beyond_cap_is_dropped` fail. This directly contradicts the plan's own `must_haves.truths` ("a single 3.0s real_dt drains at most MAX_TICKS_PER_FRAME (5) ticks... after a capped stall the accumulator is reset... dropped_tick_seconds") and RESEARCH.md's own Validation Architecture table, which expects both tests to pass. The 0.25 value appears to be carried over from the classic Gaffer On Games example, which pairs it with a much smaller tick_dt (~1/60s) — a ratio never re-validated against this project's deliberately low 2Hz tick rate.
- **Fix:** Rescaled `MAX_FRAME_TIME` to `5.0` — comfortably above `MAX_TICKS_PER_FRAME * TICK_DT` (2.5s) so the ticks-per-frame cap is the operative bound for realistic multi-second stalls (matching the documented 1-3s stall scenario in RESEARCH.md), while still acting as an outer backstop against truly pathological real_dt values (e.g. a suspended process resuming after minutes). `SIM_HZ`, `TICK_DT`, and `MAX_TICKS_PER_FRAME` were left exactly as researched. Added an in-code comment explaining the rescale and why.
- **Files modified:** src/atc_sim/sim/clock.py
- **Verification:** `python -m pytest tests/test_clock.py tests/test_boundary.py -q` — 6 passed (all 5 clock tests + boundary guard)
- **Committed in:** e361b2d (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Necessary for CORE-02 to actually hold at this project's 2Hz tick rate; no scope creep, no new files, single-constant change with rationale documented in-code and here.

## Issues Encountered
- The literal RESEARCH.md reference code, if copied verbatim, would have compiled and imported cleanly but silently failed to satisfy CORE-02's stall-drop guarantee — only caught because Task 1's RED tests encoded the exact required behavior before implementation (the value of test-first here). Resolved via the constant rescale above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `SimClock` is implemented, tested, and headlessly pygame-free — ready for `01-03` (aircraft interpolation) and `01-04` (render loop) to consume `advance()`'s alpha return value and `on_tick` callback
- `tests/test_boundary.py` continues to pass, confirming `sim/clock.py` introduces no pygame coupling
- No blockers for plan 01-03

---
*Phase: 01-walking-skeleton-sim-clock-radar-render-loop*
*Completed: 2026-07-05*

## Self-Check: PASSED

All claimed files found on disk (src/atc_sim/sim/clock.py, tests/test_clock.py, this SUMMARY.md) and all claimed commits found in git history (6cb5dcd, e361b2d).
