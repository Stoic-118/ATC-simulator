---
phase: 01-walking-skeleton-sim-clock-radar-render-loop
plan: 04
subsystem: render
tags: [pygame-ce, radar, main-loop, composition-root]

# Dependency graph
requires:
  - phase: 01-01
    provides: src-layout package skeleton (src/atc_sim/render/), pytest config, sim/render boundary guard test
  - phase: 01-02
    provides: SimClock fixed-timestep accumulator (src/atc_sim/sim/clock.py)
  - phase: 01-03
    provides: Aircraft model + sim_step (src/atc_sim/sim/aircraft.py), AircraftSnapshot/capture_state/interpolate (src/atc_sim/sim/interpolation.py)
provides:
  - Radar canvas render layer (src/atc_sim/render/window.py, src/atc_sim/render/radar.py) satisfying RADAR-01 (rings/sector lines) and RADAR-03 (dot/vector/trail)
  - app.py composition root wiring SimClock -> sim_step -> interpolate -> draw_frame into a running main loop (CORE-03 read-only render path)
  - Headless render smoke test (tests/test_render_smoke.py) as the automated Nyquist guard for the otherwise-visual RADAR-01/RADAR-03
affects: [01-05-app-entrypoint-human-verify-capstone]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "render/*.py never imports atc_sim.sim.* directly — draw_frame's render_state parameter is typed as a local structural typing.Protocol (RenderState) rather than importing AircraftSnapshot, so app.py stays the sole module importing BOTH pygame and atc_sim.sim.*"
    - "Trail deque is owned by app.py and appended to exactly once per sim tick, inside on_tick — never once per render frame — established as the standing convention for any future per-tick history buffer"

key-files:
  created:
    - src/atc_sim/render/window.py
    - src/atc_sim/render/radar.py
    - src/atc_sim/app.py
    - tests/test_render_smoke.py
  modified: []

key-decisions:
  - "Replaced render/radar.py's originally-planned `from atc_sim.sim.interpolation import AircraftSnapshot` type-hint import with a local typing.Protocol (RenderState) exposing x/y/heading_deg — satisfies Task 3's literal acceptance criterion ('app.py is the only module importing both pygame and atc_sim.sim.*') that a same-module import in a pygame-importing render file would have violated"

requirements-completed: [RADAR-01, RADAR-03, CORE-03]

coverage:
  - id: D1
    description: "Static radar background renders 4 concentric range rings + 8 sector lines at CENTER=(640,400), RING_STEP_PX=80, pre-rendered once to a cached Surface"
    requirement: "RADAR-01"
    verification:
      - kind: unit
        ref: "SDL_VIDEODRIVER=dummy python -c ... build_static_background((1280,800)); CENTER==(640,400); NUM_RINGS==4; NUM_SECTOR_LINES==8 (Task 1 verify block)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Aircraft renders as a cyan dot with heading vector and fading trail, z-order trail -> vector -> dot (dot last, never occluded)"
    requirement: "RADAR-03"
    verification:
      - kind: unit
        ref: "SDL_VIDEODRIVER=dummy python -c ... draw_frame(scr,bg,snap,t); AIRCRAFT_RADIUS_PX==5, VECTOR_LENGTH_PX==40, TRAIL_MAX_LEN==8 (Task 2 verify block)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Frozen AircraftSnapshot raises on mutation attempt; render functions read it only"
    requirement: "CORE-03"
    verification:
      - kind: unit
        ref: "manual check: AircraftSnapshot(...).x = 99.0 raises pydantic ValidationError (frozen=True)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Trail is appended once per sim tick inside on_tick, never once per render frame"
    verification:
      - kind: unit
        ref: "src/atc_sim/app.py on_tick() appends trail.append((aircraft.x, aircraft.y)) inside the tick callback; no trail mutation exists in the render section"
        status: pass
    human_judgment: false
  - id: D5
    description: "Headless render smoke test builds the static background and draws a full frame without raising under SDL_VIDEODRIVER=dummy"
    verification:
      - kind: unit
        ref: "tests/test_render_smoke.py#test_build_and_draw_frame_headless_does_not_raise"
        status: pass
    human_judgment: false
  - id: D6
    description: "Colors match D-01 palette exactly (bg (18,24,32), cyan (0,220,220), near-white (230,240,240))"
    verification:
      - kind: unit
        ref: "src/atc_sim/render/window.py BG_COLOR/AIRCRAFT_COLOR/VECTOR_COLOR constants, checked by inspection against UI-SPEC Color table"
        status: pass
    human_judgment: false
  - id: D7
    description: "app.py is the only module importing both pygame and atc_sim.sim.*; the boundary guard (sim/ never imports pygame) still passes"
    requirement: "CORE-03"
    verification:
      - kind: unit
        ref: "grep-based check: src/atc_sim/render/radar.py and window.py import pygame but zero atc_sim.sim.* imports; src/atc_sim/app.py imports both; tests/test_boundary.py#test_sim_package_never_imports_pygame passes"
        status: pass
    human_judgment: false

# Metrics
duration: ~20min
completed: 2026-07-05
status: complete
---

# Phase 01 Plan 04: Render Layer + Main Loop Wiring Summary

**Radar canvas render layer (cached rings/sector-line background, aircraft dot/heading-vector/fading-trail) wired into `app.py`'s fixed-timestep-accumulator-driven main loop, producing the first visible walking skeleton — one aircraft gliding across a bare radar canvas, its motion driven only by sim-tick state and rendered through a read-only interpolation seam.**

## Performance

- **Duration:** ~20 min active execution (3 auto tasks, all verified headlessly)
- **Started:** 2026-07-05T11:40:32+01:00 (Task 1 commit)
- **Completed:** 2026-07-05T11:42:54+01:00 (Task 3 commit)
- **Tasks:** 3 (all auto)
- **Files modified:** 4 (render/window.py, render/radar.py, app.py, tests/test_render_smoke.py)

## Accomplishments

- Created `render/window.py`: window constants (`WINDOW_SIZE=(1280,800)`, `FPS_CAP=60`, `WINDOW_CAPTION`), the D-01 color palette, and `create_window()`
- Created `render/radar.py`: `build_static_background()` drawing 4 concentric range rings + 8 anti-aliased sector lines centered at `(640,400)`, pre-rendered once and blitted each frame (never redrawn as primitives per frame)
- Extended `render/radar.py` with `draw_aircraft()` (z-order: fading trail dots → heading vector → aircraft dot drawn last) and `draw_frame()` (blit background + draw aircraft from a frozen render_state)
- Created `app.py`, the composition root: runs `SimClock.advance()` each frame, captures prev/curr `AircraftSnapshot`s inside `on_tick`, interpolates for smooth 60fps motion between 2Hz sim ticks, and draws the interpolated (never live) state; the trail deque is appended to exactly once per sim tick inside `on_tick`
- Created `tests/test_render_smoke.py`: headless (`SDL_VIDEODRIVER=dummy`) automated proof that the background builds and a full frame draws without raising — the Nyquist guard for RADAR-01/RADAR-03's otherwise-visual criteria, ahead of plan 01-05's human-verify capstone
- Full suite (14 tests: 5 clock + 7 interpolation + 1 boundary + 1 render smoke) passes green; `atc_sim.app:main` (the registered `atc-sim` console script target) resolves and imports cleanly

## Task Commits

Each task was committed atomically:

1. **Task 1: Window setup + cached radar background (rings + sector lines)** - `9fdbafa` (feat)
2. **Task 2: Aircraft symbol — trail, heading vector, dot** - `48ac204` (feat)
3. **Task 3: Wire app.py main loop + headless render smoke test** - `1eb778f` (feat) — also includes the Task-2-file boundary fix described below

**Plan metadata:** commit pending (this SUMMARY.md + STATE.md + ROADMAP.md commit, created next)

## Files Created/Modified

- `src/atc_sim/render/window.py` - Window constants, D-01 color palette, `create_window()`
- `src/atc_sim/render/radar.py` - `build_static_background()`, `draw_aircraft()`, `draw_frame()`, and the `RenderState` structural `Protocol` (see Deviations)
- `src/atc_sim/app.py` - `main()`: pygame init, SimClock-driven accumulator loop, prev/curr snapshot capture inside `on_tick`, trail append inside `on_tick`, interpolate + draw + flip each frame
- `tests/test_render_smoke.py` - Headless smoke test: builds background, constructs an `AircraftSnapshot`, calls `draw_frame` with a small trail, asserts no exception

## Decisions Made

- Kept `render/radar.py`'s aircraft-drawing constants (`TRAIL_MAX_LEN=8`, `AIRCRAFT_RADIUS_PX=5`, `VECTOR_LENGTH_PX=40`) exactly as specified in RESEARCH.md/UI-SPEC — no rescaling needed here (unlike 01-02's `MAX_FRAME_TIME`)
- Replaced the originally-planned `from atc_sim.sim.interpolation import AircraftSnapshot` type-hint import in `render/radar.py` with a local `typing.Protocol` (`RenderState`, exposing `x`/`y`/`heading_deg`) — see Deviations for why

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `render/radar.py`'s planned `AircraftSnapshot` type-hint import would have violated Task 3's own acceptance criterion**
- **Found during:** Task 3 (writing `app.py` and checking its acceptance criteria against the codebase)
- **Issue:** Task 2's action text described `draw_frame`'s `render_state` parameter as "a frozen `AircraftSnapshot`" and my initial implementation imported `AircraftSnapshot` from `atc_sim.sim.interpolation` directly into `render/radar.py` for the type hint. But Task 3's acceptance criteria explicitly require: "`app.py` is the only module importing both pygame and `atc_sim.sim.*`." Since `render/radar.py` already imports `pygame` (legitimately, for drawing), adding a same-module `atc_sim.sim.*` import would make `radar.py` a second module satisfying "imports both," directly contradicting the stated criterion — a real, if narrow, boundary regression versus the plan's own success bar (this project's core architectural rule per `.claude/CLAUDE.md`/RESEARCH.md is exactly this sim/render seam).
- **Fix:** Replaced the import with a local structural `typing.Protocol` (`RenderState`) declaring `x: float`, `y: float`, `heading_deg: float` — satisfied by any object with those attributes (including the real `AircraftSnapshot`) at zero runtime cost and zero import coupling. `draw_frame`'s signature and behavior are unchanged; only the type-hint mechanism changed.
- **Files modified:** `src/atc_sim/render/radar.py`
- **Verification:** Full suite (`SDL_VIDEODRIVER=dummy python -m pytest -q`) still 14/14 passing; grep-based check confirms `render/radar.py` and `render/window.py` have zero `atc_sim.sim.*` imports while `app.py` is the sole module importing both `pygame` and `atc_sim.sim.*`
- **Committed in:** `1eb778f` (Task 3 commit, bundled with the app.py/test creation since it was discovered while verifying Task 3's own acceptance criteria)

---

**Total deviations:** 1 auto-fixed (1 bug against a stated acceptance criterion)
**Impact on plan:** Narrow, single-file fix; no scope creep. Strengthens rather than weakens the sim/render architectural boundary this whole phase exists to establish.

## Issues Encountered

None beyond the deviation above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The full walking skeleton is now wired end-to-end: `SimClock` → `sim_step` → `capture_state`/`interpolate` → `draw_frame`, all inside `app.py`'s main loop
- `python -m pytest -q` (14 tests) and the sim/render boundary guard both pass green
- Visual correctness (does the aircraft actually look right on screen, does it glide smoothly, does the trail fade correctly) is deliberately deferred to plan 01-05's human-verify capstone, per this plan's own `<verification>` section — this plan only proves the app constructs and draws headlessly without error
- No blockers for plan 01-05

---
*Phase: 01-walking-skeleton-sim-clock-radar-render-loop*
*Completed: 2026-07-05*

## Self-Check: PASSED

All claimed files found on disk (src/atc_sim/render/window.py, src/atc_sim/render/radar.py, src/atc_sim/app.py, tests/test_render_smoke.py) and all claimed commits found in git history (9fdbafa, 48ac204, 1eb778f).
