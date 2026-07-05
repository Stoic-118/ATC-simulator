---
phase: 01-walking-skeleton-sim-clock-radar-render-loop
plan: 03
subsystem: sim
tags: [pydantic, pytest, tdd, interpolation, motion]

# Dependency graph
requires:
  - phase: 01-01
    provides: src-layout package skeleton (src/atc_sim/sim/), pytest config, sim/render boundary guard test
provides:
  - Aircraft state model with D-02 straight-line-then-wrap motion (src/atc_sim/sim/aircraft.py)
  - Read-only snapshot/interpolation seam for smooth 60fps render from 2Hz sim state (src/atc_sim/sim/interpolation.py)
  - Headless test suite (tests/test_interpolation.py) proving no-mutate interpolation, shortest-path heading lerp, and wrap-skip snap
affects: [01-04-render-loop, 01-05-app-entrypoint]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Snapshot/interpolate seam: frozen AircraftSnapshot in, frozen AircraftSnapshot out, never mutates the live Aircraft — the concrete mechanism satisfying CORE-03's 'render reads state, never mutates it'"
    - "Shortest-path angle lerp via diff = ((b - a + 180) % 360) - 180; return (a + diff * t) % 360 — single reusable function, not scattered inline branches"
    - "D-02 wrap-skip guard: a position jump > half a canvas dimension between snapshots snaps the whole returned snapshot to curr instead of lerping across the wrap seam (Phase-1-only special case)"

key-files:
  created:
    - src/atc_sim/sim/aircraft.py
    - src/atc_sim/sim/interpolation.py
    - tests/test_interpolation.py
  modified: []

key-decisions:
  - "Followed RESEARCH.md/PATTERNS.md reference code for aircraft.py and interpolation.py as-written (unlike 01-02's clock, no rescaling was needed here — sanity-checked against the same RESEARCH.md source per STATE.md's carried-forward caution but found no analogous unit-mismatch)"
  - "Wrap-skip guard snaps the entire returned AircraftSnapshot to curr (not just the jumped axis) when either x or y crosses the half-canvas threshold, matching RESEARCH.md's 'snap directly to the post-wrap position' guidance rather than a per-field patch"

requirements-completed: [CORE-03, RADAR-03]

coverage:
  - id: D1
    description: "interpolate() leaves both input AircraftSnapshot instances unchanged (frozen=True enforced); returns a distinct third instance"
    requirement: "CORE-03"
    verification:
      - kind: unit
        ref: "tests/test_interpolation.py#test_interpolate_does_not_mutate_inputs"
        status: pass
    human_judgment: false
  - id: D2
    description: "Position lerp produces the arithmetic midpoint at alpha=0.5"
    verification:
      - kind: unit
        ref: "tests/test_interpolation.py#test_position_lerp_midpoint"
        status: pass
    human_judgment: false
  - id: D3
    description: "Heading interpolation takes the shortest path across the 0/360 boundary in both directions, and behaves as a plain lerp away from the boundary"
    requirement: "RADAR-03"
    verification:
      - kind: unit
        ref: "tests/test_interpolation.py#test_heading_interpolation_shortest_path"
        status: pass
    human_judgment: false
  - id: D4
    description: "A position jump greater than half a canvas dimension between snapshots snaps to curr instead of lerping across the D-02 wrap seam"
    verification:
      - kind: unit
        ref: "tests/test_interpolation.py#test_wrap_skip_snaps_to_current"
        status: pass
    human_judgment: false
  - id: D5
    description: "sim_step advances the aircraft along heading_deg using compass convention (0deg=north/up, clockwise) and wraps position at canvas edges"
    requirement: "CORE-03"
    verification:
      - kind: unit
        ref: "tests/test_interpolation.py#test_sim_step_moves_along_heading, tests/test_interpolation.py#test_sim_step_wraps_at_edge"
        status: pass
    human_judgment: false
  - id: D6
    description: "Aircraft rejects an out-of-range heading (>=360) and a non-positive speed at construction"
    verification:
      - kind: unit
        ref: "tests/test_interpolation.py#test_aircraft_rejects_bad_fields"
        status: pass
    human_judgment: false
  - id: D7
    description: "sim/aircraft.py and sim/interpolation.py stay headlessly testable — no pygame import"
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

# Phase 01 Plan 03: Aircraft Motion and Interpolation Summary

**Aircraft pydantic model with D-02 straight-line-then-wrap motion (`sim/aircraft.py`) and the frozen-snapshot interpolation seam (`sim/interpolation.py`) that lets 2Hz sim state render smoothly at 60fps, with shortest-path heading lerp and a wrap-skip snap guard — proven by seven headless pytest cases.**

## Performance

- **Duration:** ~10 min active execution (RED test authoring, GREEN implementation)
- **Started:** 2026-07-05 (Task 1 commit)
- **Completed:** 2026-07-05 (Task 2 commit)
- **Tasks:** 2 (RED, GREEN)
- **Files modified:** 3 (tests/test_interpolation.py, src/atc_sim/sim/aircraft.py, src/atc_sim/sim/interpolation.py)

## Accomplishments

- Wrote seven failing tests (`tests/test_interpolation.py`) fully specifying `Aircraft` field validation, `sim_step`'s compass-convention motion and wrap-at-edge behavior, and `interpolate()`'s no-mutate/shortest-path-heading/wrap-skip contract before either sim module existed (confirmed RED via `ModuleNotFoundError`)
- Implemented `Aircraft` in `src/atc_sim/sim/aircraft.py`: `validate_assignment=True` pydantic model with `heading_deg` (`Field(ge=0.0, lt=360.0)`) and `speed_px_per_sec` (`Field(gt=0.0)`) bounds, `spawn_default()`, and `sim_step()` mutating position along heading then wrapping at `CANVAS_WIDTH`/`CANVAS_HEIGHT` (D-02)
- Implemented `AircraftSnapshot`/`capture_state`/`interpolate` in `src/atc_sim/sim/interpolation.py`: `frozen=True` snapshot model, `_lerp`/`_lerp_angle_deg` pure helpers (shortest-path formula), and the D-02 wrap-skip guard that snaps to `curr` when a position jump exceeds half a canvas dimension
- Sanity-checked the RESEARCH.md/PATTERNS.md reference constants against this project's actual values (per 01-02's carried-forward caution about blindly copying timing constants) — no analogous mismatch found here; all constants (`CANVAS_WIDTH=1280`, `CANVAS_HEIGHT=800`, `spawn_default()` values) copied as researched and verified correct by the test suite
- All seven interpolation tests, the five pre-existing clock tests, and the sim/render boundary guard pass green (13 total)

## Task Commits

Each task was committed atomically:

1. **Task 1: RED — failing tests for interpolation math and wrap-skip** - `6b128a5` (test)
2. **Task 2: GREEN — implement Aircraft and interpolation to pass the tests** - `32eae4e` (feat)

**Plan metadata:** commit pending (this SUMMARY.md + STATE.md + ROADMAP.md commit, created next)

## Files Created/Modified

- `tests/test_interpolation.py` - Seven pytest cases: no-mutate interpolation, position lerp midpoint, shortest-path heading (both directions + a non-boundary case), wrap-skip snap (x and y), compass-convention sim_step motion, sim_step wrap-at-edge, Aircraft field-bounds rejection
- `src/atc_sim/sim/aircraft.py` - `Aircraft` pydantic model, module constants `CANVAS_WIDTH`/`CANVAS_HEIGHT`, `spawn_default()`, `sim_step(aircraft, dt)`
- `src/atc_sim/sim/interpolation.py` - `AircraftSnapshot` (frozen), `capture_state()`, `_lerp()`, `_lerp_angle_deg()`, `interpolate()` with wrap-skip guard

## Decisions Made

- Copied RESEARCH.md's reference implementation for both modules essentially verbatim after confirming (per STATE.md's carried-forward note from 01-02's `MAX_FRAME_TIME` rescale) that no unit/scale mismatch exists here — `CANVAS_WIDTH`/`CANVAS_HEIGHT` and the wrap-skip threshold (`> CANVAS_WIDTH/2` etc.) are self-consistent constants with no cross-module rate dependency like `TICK_DT` had
- The wrap-skip guard snaps the entire returned snapshot to `curr` (not a per-axis patch) whenever either the x or y jump exceeds its half-canvas threshold, matching RESEARCH.md's "snap directly to the post-wrap position" guidance

## Deviations from Plan

None - plan executed exactly as written. The RESEARCH.md/PATTERNS.md reference code for `aircraft.py` and `interpolation.py` passed all seven RED tests on first implementation with no constant rescaling needed (unlike 01-02's `SimClock`, where `MAX_FRAME_TIME` required correction).

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `Aircraft`, `sim_step`, `AircraftSnapshot`, `capture_state`, and `interpolate` are implemented, tested, and headlessly pygame-free — ready for `01-04` (render loop) to consume `capture_state()`/`interpolate()` for drawing and for `01-05` (app entrypoint) to wire `sim_step` into `SimClock.advance()`'s `on_tick` callback
- `tests/test_boundary.py` continues to pass, confirming neither new sim module introduces pygame coupling
- No blockers for plan 01-04

---
*Phase: 01-walking-skeleton-sim-clock-radar-render-loop*
*Completed: 2026-07-05*

## Self-Check: PASSED

All claimed files found on disk (src/atc_sim/sim/aircraft.py, src/atc_sim/sim/interpolation.py, tests/test_interpolation.py, this SUMMARY.md) and all claimed commits found in git history (6b128a5, 32eae4e).
