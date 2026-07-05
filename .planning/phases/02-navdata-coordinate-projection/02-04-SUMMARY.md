---
phase: 02-navdata-coordinate-projection
plan: 04
subsystem: sim
tags: [pydantic, pytest, interpolation, motion, cleanup]

# Dependency graph
requires:
  - phase: 01-03
    provides: Aircraft state model with D-02 straight-line-then-wrap motion, snapshot/interpolate seam
provides:
  - sim/aircraft.py with the Phase-1 canvas-edge wrap-around removed from sim_step (pure straight-line motion)
  - sim/aircraft.py spawn_default repositioned to the radar center (CANVAS_WIDTH/2, CANVAS_HEIGHT/2), the runway-threshold projection origin
  - sim/interpolation.py with the Phase-1 wrap-skip snap-to-curr special case removed (interpolate() is now a plain lerp)
  - updated tests/test_interpolation.py proving non-wrapping motion and correct large-jump lerping
affects: [02-05-radar-render-real-geography, phase-3-lat-lon-aircraft-state]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pitfall A cleanup: Phase-1-only wrap-at-edge behavior (both sim_step's teleport-wrap and interpolate()'s wrap-skip snap) removed together in the same plan — removing only one would have regressed the other (interpolate()'s snap existed specifically to hide sim_step's wrap teleport streak)"

key-files:
  created: []
  modified:
    - src/atc_sim/sim/aircraft.py
    - src/atc_sim/sim/interpolation.py
    - tests/test_interpolation.py

key-decisions:
  - "Kept CANVAS_WIDTH/CANVAS_HEIGHT constants in aircraft.py — they still define the fixed canvas and are now used only by spawn_default, per the plan's explicit instruction not to remove them"
  - "spawn_default's comment references navdata/geo.py's ORIGIN as the runway-threshold projection origin even though that module isn't created by this plan (it's built in a sibling Phase 2 plan) — this is a forward-referencing doc comment, not a runtime import, so it introduces no dependency"

requirements-completed: [RADAR-04]

coverage:
  - id: D1
    description: "sim_step no longer teleport-wraps the aircraft at the canvas edge — motion is pure, non-wrapping straight-line flight along heading"
    requirement: "RADAR-04"
    verification:
      - kind: unit
        ref: "tests/test_interpolation.py#test_sim_step_does_not_wrap_at_edge"
        status: pass
    human_judgment: false
  - id: D2
    description: "spawn_default spawns the placeholder aircraft at the radar center (CANVAS_WIDTH/2, CANVAS_HEIGHT/2), the runway-threshold projection origin, instead of a canvas corner"
    requirement: "RADAR-04"
    verification:
      - kind: unit
        ref: "grep -n 'CANVAS_WIDTH / 2, y=CANVAS_HEIGHT / 2' src/atc_sim/sim/aircraft.py"
        status: pass
    human_judgment: false
  - id: D3
    description: "interpolate() no longer snaps to curr on a large position jump — it always returns a plain lerp, so real-world-scale coordinate jumps interpolate smoothly with no teleport/streak"
    requirement: "RADAR-04"
    verification:
      - kind: unit
        ref: "tests/test_interpolation.py#test_large_jump_now_lerps"
        status: pass
    human_judgment: false
  - id: D4
    description: "Existing no-mutate, position-lerp-midpoint, and shortest-path-heading interpolation behavior is unchanged by the wrap-skip removal"
    verification:
      - kind: unit
        ref: "tests/test_interpolation.py#test_interpolate_does_not_mutate_inputs, tests/test_interpolation.py#test_position_lerp_midpoint, tests/test_interpolation.py#test_heading_interpolation_shortest_path"
        status: pass
    human_judgment: false

# Metrics
duration: ~10min
completed: 2026-07-05
status: complete
---

# Phase 02 Plan 04: Remove Phase-1 Wrap-at-Edge Behavior Summary

**Removed the Phase-1-only canvas-edge teleport-wrap from `sim_step` and the matching wrap-skip snap-to-curr special case from `interpolate()`, and repositioned the placeholder test aircraft to spawn at the radar center (the runway-threshold projection origin) instead of a canvas corner.**

## Performance

- **Duration:** ~10 min active execution
- **Started:** 2026-07-05T19:31Z (Task 1 commit)
- **Completed:** 2026-07-05T19:35Z (Task 2 commit)
- **Tasks:** 2
- **Files modified:** 3 (src/atc_sim/sim/aircraft.py, src/atc_sim/sim/interpolation.py, tests/test_interpolation.py)

## Accomplishments

- Deleted `sim_step`'s four canvas-edge wrap branches (`aircraft.x/y > / <` add/subtract `CANVAS_WIDTH`/`CANVAS_HEIGHT`) — the `math.sin`/`-math.cos` compass-convention position update is unchanged, motion is now pure straight-line flight
- Repositioned `spawn_default` to `x=CANVAS_WIDTH / 2, y=CANVAS_HEIGHT / 2` (pixel 640, 400), the runway-threshold projection origin, with an inline comment documenting why and that this remains Phase-1-level placeholder motion
- Removed `interpolate()`'s wrap-skip special case (`if abs(curr.x - prev.x) > CANVAS_WIDTH / 2 ...: return curr`) — `interpolate()` is now always a plain `_lerp`/`_lerp_angle_deg` snapshot, with no snap-to-curr path
- Dropped the now-unused `CANVAS_WIDTH, CANVAS_HEIGHT` import from `interpolation.py` (now imports only `Aircraft`)
- Replaced `test_sim_step_wraps_at_edge` with `test_sim_step_does_not_wrap_at_edge` (asserts x keeps increasing past `CANVAS_WIDTH` instead of wrapping)
- Replaced `test_wrap_skip_snaps_to_current` with `test_large_jump_now_lerps` (asserts a large prev→curr jump now lerps to the midpoint instead of snapping to curr)
- Dropped the now-unused `CANVAS_HEIGHT` import from the test file (kept `CANVAS_WIDTH`, still used by the new wrap test)
- Full test suite (14 tests: interpolation + clock + boundary guard) passes green with no regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Remove sim_step canvas-edge wrap and reposition the test aircraft spawn** - `db0b826` (fix)
2. **Task 2: Remove interpolate() wrap-skip special case and drop the now-unused CANVAS import** - `d510211` (fix)

**Plan metadata:** commit pending (this SUMMARY.md + STATE.md + ROADMAP.md commit, created next)

## Files Created/Modified

- `src/atc_sim/sim/aircraft.py` - `sim_step` loses its wrap block (pure straight-line motion); `spawn_default` repositioned to the radar center/projection origin; D-02 wrap comments replaced with Phase 2/Pitfall A removal notes
- `src/atc_sim/sim/interpolation.py` - `interpolate()` loses the wrap-skip special case; `CANVAS_WIDTH, CANVAS_HEIGHT` import dropped (imports only `Aircraft` now)
- `tests/test_interpolation.py` - `test_sim_step_wraps_at_edge` → `test_sim_step_does_not_wrap_at_edge`; `test_wrap_skip_snaps_to_current` → `test_large_jump_now_lerps`; unused `CANVAS_HEIGHT` import dropped

## Decisions Made

- Kept the `CANVAS_WIDTH`/`CANVAS_HEIGHT` module constants in `aircraft.py` exactly as the plan specified — they still define the fixed canvas and are now used only by `spawn_default`, not removed as dead code
- Left the `math.sin`/`-math.cos` compass-convention position update in `sim_step` completely untouched — only the wrap branches after it were deleted, per the plan's explicit scope guard

## Deviations from Plan

None - plan executed exactly as written. Both tasks' acceptance criteria (grep checks for removed wrap logic, removed CANVAS import, correct spawn coordinates, new/retained passing tests) were verified and matched exactly.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `sim_step` and `interpolate()` are now fully wrap-free — real-world-scale navdata coordinates (from sibling Phase 2 plans building `navdata/geo.py` and the EGGW projection) will interpolate smoothly with no teleport or streak once wired onto the aircraft
- The placeholder aircraft spawns at the radar center, which will coincide with the runway-threshold projection origin once `navdata/geo.py`'s `ORIGIN` lands from a sibling plan — no further change needed here to align the two
- No blockers for 02-05 or later phases; this plan's scope guard held (no procedure-following, performance modeling, or lat/lon aircraft state was added — the aircraft still uses simple Phase-1 straight-line, fixed-heading, pixel-space motion)

---
*Phase: 02-navdata-coordinate-projection*
*Completed: 2026-07-05*

## Self-Check: PASSED

All claimed files found on disk (src/atc_sim/sim/aircraft.py, src/atc_sim/sim/interpolation.py, tests/test_interpolation.py, this SUMMARY.md) and all claimed commits found in git history (db0b826, d510211, 276f026).
