---
phase: 02-navdata-coordinate-projection
plan: 03
subsystem: navdata
tags: [pydantic, pygame, procedures, sid-star, geodesy]

# Dependency graph
requires:
  - phase: 02-02
    provides: navdata/geo.py shared projection (project_to_local_xy_nm), navdata/models.py frozen ILS/Runway conventions, render/radar.py world_to_screen() + build_static_background() extension pattern
provides:
  - navdata/models.py — frozen Fix, AltitudeRestriction, SpeedRestriction, ProcedureLeg, Procedure models
  - navdata/eggw.py — OLNEY_2B_SID and DET_2A_STAR real procedure data (named fixes, real coordinates, real altitude/speed restrictions)
  - render/radar.py _draw_procedure() rendering fix markers, 5-letter names, and thin procedure track lines, sharing world_to_screen()/project_to_local_xy_nm() with the runway
  - render/window.py FIX_COLOR/FIX_TEXT_COLOR/PROCEDURE_LINE_COLOR palette additions
  - app.py wiring OLNEY_2B_SID and DET_2A_STAR into the cached static background
affects: [02-navdata-coordinate-projection plan 05 (visual sign-off), future Phase 3/4 procedure-following and datablock/restriction-text rendering]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Text rendering: module-level lazily-initialized pygame.font.Font cache (_get_fix_font/_FIX_FONT), created on first draw call rather than at import time, since pygame.font requires pygame.init() to have already run"
    - "Procedure track/fix drawing z-order: track line first, fix markers second, fix name text last, so text is never occluded (mirrors draw_aircraft's trail->vector->dot discipline)"
    - "Restriction data modeled on ProcedureLeg but never read by render/radar.py this phase (D-05) — render only touches leg.fix, never leg.altitude_restriction/leg.speed_restriction"

key-files:
  created: []
  modified:
    - src/atc_sim/navdata/models.py
    - src/atc_sim/navdata/eggw.py
    - src/atc_sim/render/window.py
    - src/atc_sim/render/radar.py
    - src/atc_sim/app.py
    - tests/test_navdata.py
    - tests/test_render_smoke.py

key-decisions:
  - "OLNEY 2B's charted stepped-DME climb (4000ft/D6, 5000ft/D9, 6000ft/D15) collapsed to a single at-or-above 6000ft restriction on the final BNN->OLNEY leg, per 02-RESEARCH.md's Simplification note — the real terminal value, not an invented one"
  - "HEN leg's altitude_restriction left explicitly None (Pitfall B) — the real chart does not restrict this intercept point"
  - "Set course_deg_mag on the OLNEY 2B HEN leg (256.0, charted NDB inbound QDM) and OLNEY leg (345.0, charted BNN radial) to give NAV-03's 'stored as-charted, never re-converted' guard a concrete non-null value to test against"
  - "Used pygame.font.Font(None, 14) (pygame's bundled default font) rather than SysFont, for portability under the SDL dummy driver used in headless tests"

patterns-established:
  - "TDD RED/GREEN commit pair for procedure models+data (navdata/models.py + navdata/eggw.py): failing test committed first (ImportError), then the minimal implementation that makes it pass"

requirements-completed: [NAV-02, NAV-03]

coverage:
  - id: D1
    description: "OLNEY_2B_SID and DET_2A_STAR modeled as frozen Procedure/ProcedureLeg/Fix/AltitudeRestriction/SpeedRestriction data with real sourced coordinates and restrictions (HEN unrestricted, OLNEY at-or-above 6000ft, DET at FL170, ABBOT at FL080/max 220kt), both under runway '25'"
    requirement: "NAV-02"
    verification:
      - kind: unit
        ref: "tests/test_navdata.py::test_olney_2b_sid_data"
        status: pass
      - kind: unit
        ref: "tests/test_navdata.py::test_det_2a_star_data"
        status: pass
      - kind: unit
        ref: "tests/test_navdata.py::test_procedure_models_reject_bad_fields"
        status: pass
    human_judgment: false
  - id: D2
    description: "Each leg's charted (already-magnetic) course_deg_mag is stored as-is and never re-converted through the true<->magnetic boundary"
    requirement: "NAV-03"
    verification:
      - kind: unit
        ref: "tests/test_navdata.py::test_charted_course_not_double_converted"
        status: pass
    human_judgment: false
  - id: D3
    description: "OLNEY 2B and DET 2A fixes render on the radar as markers with 5-letter names, connected by thin procedure track lines, at correct real-world positions, sharing the runway's projection"
    requirement: "NAV-02"
    verification:
      - kind: unit
        ref: "tests/test_render_smoke.py::test_build_and_draw_frame_headless_does_not_raise"
        status: pass
      - kind: manual_procedural
        ref: "Launch atc-sim and visually confirm OLNEY 2B / DET 2A fixes, names, and tracks appear at lat/lon-correct positions"
        status: unknown
    human_judgment: true
    rationale: "Full visual correctness sign-off is explicitly deferred to Plan 05 per this plan's own <verification> section; the headless smoke test proves _draw_procedure (including font render) executes without error but cannot confirm on-screen visual placement."

# Metrics
duration: ~11min
completed: 2026-07-05
status: complete
---

# Phase 2 Plan 3: OLNEY 2B SID / DET 2A STAR Procedure Models and Radar Rendering Summary

**Modeled the real OLNEY 2B SID and DET 2A STAR as frozen Pydantic procedures with sourced fix coordinates and restriction data, and rendered their fixes (marker + 5-letter name) connected by thin procedure track lines through the shared runway projection.**

## Performance

- **Duration:** ~11 min
- **Started:** 2026-07-05T21:10:08Z
- **Completed:** 2026-07-05T21:21:17Z
- **Tasks:** 2 (1 TDD, 1 auto)
- **Files modified:** 7 (0 created, 7 modified)

## Accomplishments

- `navdata/models.py`: added frozen `RestrictionKind`, `Fix`, `AltitudeRestriction`, `SpeedRestriction`, `ProcedureLeg`, `Procedure` models with `Field` range bounds, matching the existing `ILS`/`Runway` frozen-model convention
- `navdata/eggw.py`: added `OLNEY_2B_SID` (BNN → HEN → OLNEY, runway "25", HEN unrestricted per Pitfall B, OLNEY at-or-above 6000ft collapsed from the chart's stepped DME climb) and `DET_2A_STAR` (DET → LOFFO → ABBOT, runway "25", DET at FL170, LOFFO max 250kt, ABBOT at FL080/max 220kt) — every coordinate/restriction sourced with its DMS/chart comment preserved beside the decimal value
- `render/window.py`: `FIX_COLOR`, `FIX_TEXT_COLOR`, `PROCEDURE_LINE_COLOR` added to the D-01 palette block
- `render/radar.py`: new `_draw_procedure()` projecting each leg's fix through `project_to_local_xy_nm`/`world_to_screen`, drawing (in z-order) the thin track line, fix markers, then fix-name text via a lazily-cached module-level `pygame.font.Font`; `build_static_background()` signature extended to `(size, runway, procedures)`, looping `_draw_procedure` for each procedure — no restriction text rendered (D-05)
- `app.py`: imports `OLNEY_2B_SID`/`DET_2A_STAR` and passes `[OLNEY_2B_SID, DET_2A_STAR]` into `build_static_background`
- Full test suite green (25 tests, up from 21 at the start of this plan)

## Task Commits

Each task was committed atomically (Task 1 is TDD, shown as test → feat pair):

1. **Task 1: Procedure models + real OLNEY 2B SID / DET 2A STAR data**
   - `46de8d0` (test) — RED: failing tests in test_navdata.py (ImportError, models/data not yet defined)
   - `91851fc` (feat) — GREEN: navdata/models.py procedure models + navdata/eggw.py real procedure data
2. **Task 2: Render SID/STAR fixes and procedure track lines** - `d3eac88` (feat)

**Plan metadata:** commit pending (this SUMMARY.md + STATE.md + ROADMAP.md commit, created next)

## Files Created/Modified

- `src/atc_sim/navdata/models.py` - added `RestrictionKind`, `Fix`, `AltitudeRestriction`, `SpeedRestriction`, `ProcedureLeg`, `Procedure` frozen models
- `src/atc_sim/navdata/eggw.py` - added `OLNEY_2B_SID`, `DET_2A_STAR` real procedure data
- `src/atc_sim/render/window.py` - added `FIX_COLOR`, `FIX_TEXT_COLOR`, `PROCEDURE_LINE_COLOR`
- `src/atc_sim/render/radar.py` - added `_draw_procedure()`, module-level fix-label font cache (`_FIX_FONT`/`_get_fix_font()`); `build_static_background()` signature changed to `(size, runway, procedures)`
- `src/atc_sim/app.py` - imports `OLNEY_2B_SID`, `DET_2A_STAR`; passes `[OLNEY_2B_SID, DET_2A_STAR]` into `build_static_background`
- `tests/test_navdata.py` - added `test_olney_2b_sid_data`, `test_det_2a_star_data`, `test_procedure_models_reject_bad_fields`, `test_charted_course_not_double_converted`
- `tests/test_render_smoke.py` - passes `[OLNEY_2B_SID, DET_2A_STAR]` through the new `build_static_background` signature

## Decisions Made

- Collapsed OLNEY 2B's charted stepped-DME climb (4000ft by D6, 5000ft by D9, 6000ft by D15 from BNN) into a single at-or-above 6000ft restriction on the final BNN→OLNEY leg, per 02-RESEARCH.md's own recommended simplification — the real terminal value of the stepped profile, not an invented number
- Left HEN's leg `altitude_restriction` explicitly `None` (Pitfall B) rather than fabricating a value just to have "a restriction per fix"
- Set `course_deg_mag` on OLNEY 2B's HEN leg (256.0, the charted NDB inbound QDM) and OLNEY leg (345.0, the charted BNN radial) — gives the NAV-03 "charted course stored as-is" guard a concrete, sourced non-null value to assert against, rather than leaving every leg's course `None`
- Used `pygame.font.Font(None, 14)` (pygame's bundled default font, no external font file) rather than `pygame.font.SysFont`, since the project has no font-rendering precedent and `Font(None, ...)` is the more portable/deterministic choice under the SDL dummy driver used in headless tests

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `OLNEY_2B_SID` and `DET_2A_STAR` are fully wired end-to-end (navdata → render → app), covered by headless unit tests and a headless render smoke test
- `_draw_procedure()`'s z-order (track line → markers → text) and the lazily-cached `_FIX_FONT` pattern are ready for reuse if Phase 4 adds more procedures or text-based datablocks
- Restriction data (`AltitudeRestriction`/`SpeedRestriction`) exists as tested data on every leg but is deliberately not read by any render code this phase (D-05) — Phase 4/RADAR-02 is the intended consumer for on-canvas restriction text
- Full visual sign-off (fixes/names/tracks appear at lat/lon-correct positions on a real launched window) is deferred to Plan 05 per this plan's own verification section — no blocker, just not yet human-verified
- No blockers for Plan 05 or later phases

---
*Phase: 02-navdata-coordinate-projection*
*Completed: 2026-07-05*

## Self-Check: PASSED

- FOUND: src/atc_sim/navdata/models.py
- FOUND: src/atc_sim/navdata/eggw.py
- FOUND: src/atc_sim/render/window.py
- FOUND: src/atc_sim/render/radar.py
- FOUND: src/atc_sim/app.py
- FOUND: tests/test_navdata.py
- FOUND: tests/test_render_smoke.py
- FOUND commit: 46de8d0
- FOUND commit: 91851fc
- FOUND commit: d3eac88
- FOUND commit: 3bcfdda
