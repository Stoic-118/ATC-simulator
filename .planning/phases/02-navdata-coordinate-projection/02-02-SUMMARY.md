---
phase: 02-navdata-coordinate-projection
plan: 02
subsystem: navdata
tags: [geographiclib, pydantic, pygame, projection, geodesy, magnetic-variation]

# Dependency graph
requires:
  - phase: 02-01
    provides: geographiclib>=2.1,<3.0 installed and importable in the venv
  - phase: 02-04
    provides: sim/aircraft.py spawn_default repositioned to the radar center (the runway-threshold projection origin), non-wrapping motion
provides:
  - navdata/geo.py — shared cosine-corrected geodesic projection (project_to_local_xy_nm, true_bearing_and_distance_nm) and the single true<->magnetic boundary (true_to_magnetic/magnetic_to_true), headless
  - navdata/models.py — frozen Pydantic v2 ILS and Runway models with Field range bounds
  - navdata/eggw.py — EGGW_RUNWAY, the real sourced RWY 25 threshold/heading/ILS data
  - render/radar.py world_to_screen() + _draw_runway() extending build_static_background() to draw the runway threshold + extended centerline
  - app.py wiring EGGW_RUNWAY into the cached static background
affects: [02-navdata-coordinate-projection plan 03+ (SID/STAR procedures will reuse project_to_local_xy_nm/world_to_screen and the Runway/ILS model patterns), future sim/separation.py (RADAR-04 shared projection)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "navdata/ is sim-core reference data: headless (no pygame import), frozen Pydantic models, guarded by tests/test_boundary.py exactly like sim/"
    - "Single geodesic projection function (project_to_local_xy_nm, built on geographiclib.Geodesic.WGS84.Inverse) reused unchanged by render and future separation math — satisfies RADAR-04 by construction, not convention"
    - "Single true<->magnetic conversion boundary (true_to_magnetic/magnetic_to_true in navdata/geo.py) — charted magnetic values (course_deg_mag, heading_deg_mag) are stored as-is and never re-converted"
    - "render/radar.py imports atc_sim.navdata.* directly (no Protocol) since navdata is frozen read-only reference data, unlike the mutable sim-state RenderState Protocol boundary"

key-files:
  created:
    - src/atc_sim/navdata/__init__.py
    - src/atc_sim/navdata/geo.py
    - src/atc_sim/navdata/models.py
    - src/atc_sim/navdata/eggw.py
    - tests/test_projection.py
    - tests/test_navdata.py
  modified:
    - tests/test_boundary.py
    - src/atc_sim/render/window.py
    - src/atc_sim/render/radar.py
    - src/atc_sim/app.py
    - tests/test_render_smoke.py

key-decisions:
  - "Corrected test_true_bearing_and_distance_nm's expected BNN distance from 02-RESEARCH.md's rounded '~11.2nm' to the precise geodesic value ~11.6nm, cross-checked directly against geographiclib.Geodesic.WGS84.Inverse() — the implementation is correct, the research figure was an approximation"
  - "Runway extended centerline length set to 10nm (RUNWAY_CENTERLINE_LENGTH_NM), Claude's discretion per plan — comfortably visible without clipping the 1280x800 canvas since the threshold sits at the canvas center"
  - "Centerline direction computed directly from heading_deg_mag treated as a screen compass angle (same convention already used for aircraft heading), not converted via magnetic_to_true first — the project's single geographic north-up screen convention doesn't distinguish true/magnetic for static line orientation, and the plan's action text specifies converting heading_deg_mag directly to a screen direction"
  - "Extended tests/test_boundary.py's headless guard to also scan src/atc_sim/navdata/, per the plan's explicit stricter-than-required instruction (02-PATTERNS.md flags this as deliberate)"

patterns-established:
  - "TDD RED/GREEN commit pairs for pure sim-core logic (geo.py, models.py+eggw.py): failing test committed first (ModuleNotFoundError), then the minimal implementation that makes it pass"

requirements-completed: [RADAR-04, NAV-01, NAV-03]

coverage:
  - id: D1
    description: "navdata/geo.py provides project_to_local_xy_nm() and true_bearing_and_distance_nm(), both built on geographiclib.Geodesic.WGS84 — proven circular (not elliptical) by test, headless (no pygame import) by the extended boundary guard"
    requirement: "RADAR-04"
    verification:
      - kind: unit
        ref: "tests/test_projection.py::test_projection_is_circular_not_elliptical"
        status: pass
      - kind: unit
        ref: "tests/test_projection.py::test_true_bearing_and_distance_nm"
        status: pass
      - kind: unit
        ref: "tests/test_boundary.py::test_navdata_package_never_imports_pygame"
        status: pass
    human_judgment: false
  - id: D2
    description: "navdata/models.py (frozen ILS, Runway) and navdata/eggw.py (EGGW_RUNWAY) model the real EGGW runway 25 threshold, heading, and ILS parameters (localizer course, 3.0 glideslope, CAT I decision height)"
    requirement: "NAV-01"
    verification:
      - kind: unit
        ref: "tests/test_navdata.py::test_runway_25_matches_sourced_data"
        status: pass
      - kind: unit
        ref: "tests/test_navdata.py::test_runway_model_rejects_bad_fields"
        status: pass
      - kind: unit
        ref: "tests/test_navdata.py::test_runway_model_is_frozen"
        status: pass
    human_judgment: false
  - id: D3
    description: "true_to_magnetic()/magnetic_to_true() in navdata/geo.py is the single defined true<->magnetic conversion boundary; charted magnetic values are never re-converted"
    requirement: "NAV-03"
    verification:
      - kind: unit
        ref: "tests/test_projection.py::test_magnetic_variation_boundary"
        status: pass
    human_judgment: false
  - id: D4
    description: "The real EGGW runway 25 threshold and extended centerline render on the radar canvas, positioned by lat/lon through the shared projection, as part of the cached static background"
    requirement: "RADAR-04"
    verification:
      - kind: unit
        ref: "tests/test_render_smoke.py::test_build_and_draw_frame_headless_does_not_raise"
        status: pass
      - kind: manual_procedural
        ref: "Launch atc-sim and visually confirm the runway threshold + centerline appear at a lat/lon-correct position"
        status: unknown
    human_judgment: true
    rationale: "Full visual correctness sign-off is explicitly deferred to Plan 05 per this plan's own <verification> section; the headless smoke test proves _draw_runway executes without error but cannot confirm visual placement."

# Metrics
duration: ~10min
completed: 2026-07-05
status: complete
---

# Phase 2 Plan 2: Shared Projection, Runway/ILS Models, and Radar Runway Rendering Summary

**Built the shared cosine-corrected geodesic projection and single magnetic-variation boundary in navdata/geo.py, modeled the real EGGW runway 25 + CAT I ILS as frozen Pydantic data in navdata/models.py + navdata/eggw.py, and rendered the runway threshold + extended centerline on the radar canvas via a new world_to_screen()/_draw_runway() extension to build_static_background().**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-07-05T20:43Z
- **Completed:** 2026-07-05T20:51Z
- **Tasks:** 3 (2 TDD, 1 auto)
- **Files modified:** 11 (6 created, 5 modified)

## Accomplishments

- `navdata/geo.py`: `ORIGIN_LAT`/`ORIGIN_LON` (RWY 25 threshold), `PX_PER_NM = 8.0`, `MAGNETIC_VARIATION_DEG = 1.2`, `true_bearing_and_distance_nm()`, `project_to_local_xy_nm()` (the ONE cosine-corrected projection, reusable unchanged by future separation math), `true_to_magnetic()`/`magnetic_to_true()` (the single true<->magnetic boundary, NAV-03) — headless, verified against `geographiclib` directly
- `navdata/models.py`: frozen Pydantic v2 `ILS` and `Runway` models with `Field(ge=..., lt=...)` range bounds on course/glideslope/heading
- `navdata/eggw.py`: `EGGW_RUNWAY` with real sourced RWY 25 data — threshold (51.877044, -0.354486), heading 254.4 QFU, ILS (course 254.0, glideslope 3.0, CAT I, DH 200ft) — identifier `"25"` throughout, with the historical 08/26→07/25 redesignation documented in the module docstring
- `tests/test_boundary.py` extended to also scan `src/atc_sim/navdata/` for pygame imports (deliberately stricter than required, per 02-PATTERNS.md)
- `render/window.py`: `RUNWAY_COLOR` added to the D-01 palette
- `render/radar.py`: `world_to_screen()` (nm → pixel + y-flip helper) and `_draw_runway()` (threshold dot + extended approach centerline along the reciprocal of `heading_deg_mag`); `build_static_background()` now takes a `Runway` and draws it into the cached static surface
- `app.py`: imports `EGGW_RUNWAY` and passes it into `build_static_background`, so the runway is part of the cached static layer
- Full test suite green (21 tests, up from 14 at the start of this phase)

## Task Commits

Each task was committed atomically (TDD tasks show test → feat commit pairs):

1. **Task 1: Shared projection + magnetic-variation boundary + boundary guard extension**
   - `c8887c6` (test) — RED: failing test_projection.py + extended test_boundary.py
   - `81d9a1f` (feat) — GREEN: navdata/geo.py implementation
2. **Task 2: Real runway 25 + ILS Pydantic models and EGGW data**
   - `20c42a9` (test) — RED: failing test_navdata.py
   - `b2588ab` (feat) — GREEN: navdata/models.py + navdata/eggw.py
3. **Task 3: Render the runway threshold + extended centerline on the radar** - `cc687c5` (feat)

**Plan metadata:** commit pending (this SUMMARY.md + STATE.md + ROADMAP.md commit, created next)

## Files Created/Modified

- `src/atc_sim/navdata/__init__.py` - empty package marker
- `src/atc_sim/navdata/geo.py` - shared geodesic projection + magnetic boundary
- `src/atc_sim/navdata/models.py` - frozen `ILS`, `Runway` Pydantic models
- `src/atc_sim/navdata/eggw.py` - real EGGW `EGGW_RUNWAY` data
- `tests/test_projection.py` - projection circularity, magnetic round-trip, geodesic bearing/distance tests
- `tests/test_navdata.py` - Runway/ILS sourced-data, Field-rejection, frozen-immutability tests
- `tests/test_boundary.py` - extended to scan `src/atc_sim/navdata/` for pygame imports
- `src/atc_sim/render/window.py` - added `RUNWAY_COLOR`
- `src/atc_sim/render/radar.py` - added `world_to_screen()`, `_draw_runway()`; `build_static_background()` signature changed to `(size, runway)`
- `src/atc_sim/app.py` - imports `EGGW_RUNWAY`, wires it into `build_static_background`
- `tests/test_render_smoke.py` - passes `EGGW_RUNWAY` through the new `build_static_background` signature

## Decisions Made

- Corrected `test_true_bearing_and_distance_nm`'s BNN distance expectation from 02-RESEARCH.md's rounded "~11.2nm" to the precise geodesic value (~11.6nm), cross-checked directly against `geographiclib.Geodesic.WGS84.Inverse()` before writing the assertion — the projection code is correct; the research figure was a rounded estimate, not a bug
- Chose `RUNWAY_CENTERLINE_LENGTH_NM = 10.0` for the extended centerline's visible length (Claude's discretion per plan) — comfortably visible on the 1280x800 canvas without clipping, since the runway threshold sits exactly at the canvas center (the origin and threshold are the same point by design)
- Computed the centerline direction directly from `heading_deg_mag` treated as a screen compass angle (matching the existing aircraft-heading-vector convention), not first converted via `magnetic_to_true()` — the plan's action text specifies "converting heading_deg_mag to a screen direction" directly, and the project's screen convention doesn't distinguish true/magnetic north for static line orientation at this fidelity level
- Extended `tests/test_boundary.py`'s headless guard to also scan `src/atc_sim/navdata/`, taking the plan's offered stricter-than-required option since navdata is sim-core reference data usable by future separation math

## Deviations from Plan

None requiring a rule beyond normal test-value correction (not a deviation from scope, just fixing a test's expected value against verified ground truth — see Decisions Made above). Plan executed exactly as written otherwise.

**Note on acceptance-criteria greps:** Task 1's acceptance criterion `grep -c 'import pygame' src/atc_sim/navdata/geo.py returns 0` returns `1` in practice, because the module's mandated headless docstring itself contains the literal phrase "MUST NOT import pygame" (copied verbatim from the existing `sim/aircraft.py` pattern, which has the identical "violation" under the same literal grep). The actual headless guarantee is enforced correctly by `tests/test_boundary.py`'s regex-based scan (`PYGAME_IMPORT_RE`, anchored to `^\s*(import|from)`), which does not match prose docstring text and passes. This is a pre-existing quirk of the literal grep phrasing, not a real pygame import.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `navdata/geo.py`'s `project_to_local_xy_nm()` and `true_bearing_and_distance_nm()` are ready for reuse by Plan 03+'s SID/STAR fix rendering and by a future `sim/separation.py` — no further setup needed
- `render/radar.py`'s `world_to_screen()` helper and the `_draw_runway()` z-order convention (threshold dot after centerline line) are the pattern for the upcoming fix-marker/procedure-track drawing
- `EGGW_RUNWAY` is fully wired end-to-end (navdata → render → app) and covered by both headless unit tests and a headless render smoke test
- Full visual sign-off (runway appears at the lat/lon-correct position on a real launched window) is deferred to Plan 05 per this plan's own verification section — no blocker, just not yet human-verified
- No blockers for Plan 03 (SID/STAR procedures) or later phases

---
*Phase: 02-navdata-coordinate-projection*
*Completed: 2026-07-05*

## Self-Check: PASSED

- FOUND: src/atc_sim/navdata/__init__.py
- FOUND: src/atc_sim/navdata/geo.py
- FOUND: src/atc_sim/navdata/models.py
- FOUND: src/atc_sim/navdata/eggw.py
- FOUND: tests/test_projection.py
- FOUND: tests/test_navdata.py
- FOUND: tests/test_boundary.py
- FOUND: src/atc_sim/render/window.py
- FOUND: src/atc_sim/render/radar.py
- FOUND: src/atc_sim/app.py
- FOUND: tests/test_render_smoke.py
- FOUND commit: c8887c6
- FOUND commit: 81d9a1f
- FOUND commit: 20c42a9
- FOUND commit: b2588ab
- FOUND commit: cc687c5
