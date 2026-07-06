---
phase: 02-navdata-coordinate-projection
verified: 2026-07-06T00:00:00Z
status: passed
score: 4/4 must-haves verified
behavior_unverified: 0
overrides_applied: 0
---

# Phase 2: Navdata & Coordinate Projection Verification Report

**Phase Goal:** The radar displays real EGGW navdata (runway 25, one SID, one STAR) through a cosine-corrected lat/lon-to-pixel projection shared with the future separation-check math, with heading/course/track/bearing modeled as distinct fields.
**Verified:** 2026-07-06T00:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Independent Verification Method

SUMMARY.md claims were not trusted at face value. All 6 phase-2 source files (`navdata/geo.py`, `navdata/models.py`, `navdata/eggw.py`, `render/radar.py`, `render/window.py`, `app.py`) and the modified Phase-1 files (`sim/aircraft.py`, `sim/interpolation.py`) were read in full and cross-checked line-by-line against the PLAN must_haves and 02-RESEARCH.md's sourced data. The full test suite was independently re-run (not the executor's reported output):

```
SDL_VIDEODRIVER=dummy python -m pytest -q
→ 25 passed in 0.18s
```

Beyond reading code, an independent headless script re-derived every SID/STAR fix's screen position directly from `navdata/eggw.py` + `navdata/geo.py` + `render/radar.py`'s own `project_to_local_xy_nm`/`world_to_screen`, to cross-check the projection math against 02-RESEARCH.md's predicted offsets without relying on the human checkpoint alone:

| Fix | Computed screen offset from center | 02-RESEARCH.md predicted offset |
|-----|-------------------------------------|----------------------------------|
| BNN | (-59, +72) px | (-54, +71) px |
| OLNEY | (-113, -121) px | (-109, -122) px |
| DET | (+286, +273) px | (+286, +274) px |

All within a few pixels (explained by the plan's own documented correction of BNN's rounded ~11.2nm to the precise geodesic ~11.6nm). All six fixes (BNN, HEN, OLNEY, DET, LOFFO, ABBOT) land within the 1280×800 canvas with no clipping. This independently corroborates both the projection math and the human-verified visual sign-off recorded in `02-05-SUMMARY.md`.

Git history was checked for every commit hash cited across all 5 SUMMARY.md files — all 15+ commits (`cf3636b`, `c8887c6`, `81d9a1f`, `20c42a9`, `b2588ab`, `cc687c5`, `46de8d0`, `91851fc`, `d3eac88`, `db0b826`, `d510211`, `e45242f`, etc.) exist in `git log`.

## Goal Achievement

### Observable Truths

| # | Truth (ROADMAP Success Criterion) | Status | Evidence |
|---|-------|--------|----------|
| 1 | The radar canvas shows the real EGGW runway 25 threshold and extended centerline, correctly positioned by lat/lon | ✓ VERIFIED | `navdata/eggw.py::EGGW_RUNWAY` holds the real UK AIP threshold (51.877044, -0.354486) and QFU (254.4°), sourced/commented with DMS + `[VERIFIED]` tags. `render/radar.py::_draw_runway()` projects it via the shared `project_to_local_xy_nm`→`world_to_screen` pipeline and draws a threshold dot + extended centerline along the reciprocal heading (074°, the real-world ILS approach corridor direction for RWY 25). Wired into `app.py`'s `build_static_background(screen.get_size(), EGGW_RUNWAY, [...])`. Independently confirmed the threshold lands exactly at canvas center (640,400) since it is the projection origin by design. Additionally human-verified in-band (`02-05-SUMMARY.md`, `human_judgment: true`) — code genuinely supports that claim, not merely asserted. Identifier is "25" everywhere in code; the only "26" occurrences in `eggw.py` are inside the historical 08/26→07/25 redesignation narrative, never a value. |
| 2 | One SID's and one STAR's named fixes/waypoints appear on the radar at their correct real-world positions, each with its modeled altitude/speed restrictions | ✓ VERIFIED | `OLNEY_2B_SID` (BNN→HEN→OLNEY) and `DET_2A_STAR` (DET→LOFFO→ABBOT) are frozen `Procedure` models in `navdata/eggw.py` with real sourced coordinates and restrictions (OLNEY at-or-above 6000ft, DET at FL170, ABBOT at FL080/max 220kt, HEN correctly left `None` per Pitfall B — no fabricated restriction). `render/radar.py::_draw_procedure()` renders fix markers + 5-letter names + a connecting thin track line, wired via `app.py`. Per 02-CONTEXT.md D-05 (explicitly confirmed acceptable per this verification's task instructions), restrictions exist as tested Pydantic DATA on the leg models but are deliberately NOT rendered as on-canvas text this phase (Phase 4/RADAR-02 owns that) — this does not fail the criterion. `tests/test_navdata.py::test_olney_2b_sid_data`/`test_det_2a_star_data` assert every exact sourced coordinate/restriction value, independently re-run and passing. Independent projection re-derivation (see method above) confirms all 6 fixes land at real-world-correct, non-clipped screen positions. |
| 3 | Range rings render as true circles (not ellipses) at any radar pan/zoom, confirming the cosine-corrected projection | ✓ VERIFIED | `tests/test_projection.py::test_projection_is_circular_not_elliptical` independently re-run and passing: a point 10nm due north and a point 10nm due east of the origin (ground-truth derived via `Geodesic.WGS84.Direct`, independent of the code under test) both project to a pixel magnitude within 0.01px of `10*PX_PER_NM`. The projection is geodesic-inverse-based (`geographiclib.Geodesic.WGS84.Inverse`), not a hand-rolled flat-earth formula — cosine correction is structural, not a formula someone could get subtly wrong. Human-verified in-band that displayed range rings are visually circular, not ellipses (`02-05-SUMMARY.md`). |
| 4 | Heading, course, bearing, and track are distinct named fields with magnetic variation applied at exactly one defined point — displayed procedure courses match real-world EGGW SID/STAR charted values | ✓ VERIFIED (see note) | `Runway.heading_deg_mag` and `ProcedureLeg.course_deg_mag`/`ILS.course_deg_mag` are distinct, separately named fields (grep-confirmed, never conflated). `true_bearing_and_distance_nm()` in `navdata/geo.py` is the single, distinctly-named function producing `bearing_deg`. `MAGNETIC_VARIATION_DEG = 1.2` is defined exactly once, and `true_to_magnetic()`/`magnetic_to_true()` in `navdata/geo.py` are the only two functions that touch it anywhere in the codebase (grep-confirmed zero other conversion sites). `tests/test_navdata.py::test_charted_course_not_double_converted` and `tests/test_projection.py::test_magnetic_variation_boundary` independently re-run and passing — charted magnetic values (e.g. HEN's 256.0° QDM) are proven to never be re-passed through the conversion functions. Charted course values (HEN 256°, OLNEY 345°) are the exact real chart values, tested. **Note:** a `track_deg` field does not yet exist anywhere in the running code (grep-confirmed) — only `heading_deg` (Aircraft/AircraftSnapshot) exists today. This is a defensible, documented deferral, not a silent omission: 02-RESEARCH.md's own "Field-naming convention for Phase 3's Aircraft model" section explicitly scopes `track_deg` to Phase 3 (heading == track for all of v1, no wind model), and 02-CONTEXT.md's Phase Boundary explicitly excludes aircraft lat/lon state/procedure-following from this phase. Track is inherently a moving-aircraft concept with no analog in Phase 2's static navdata models, so its absence does not create the field-conflation risk NAV-03 exists to prevent. Flagged here for visibility since the ROADMAP criterion's literal text lists "track" as a field that should exist by end of Phase 2, but this was not treated as a blocking gap given the reasoning above — see Gaps Summary. |

**Score:** 4/4 truths verified (0 present-but-behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/atc_sim/navdata/geo.py` | Shared cosine-corrected projection + single magnetic boundary, pygame-free | ✓ VERIFIED | Exists, substantive (86 lines), no pygame import (grep + `test_navdata_package_never_imports_pygame` independently re-run), wired into `render/radar.py` and `tests/test_navdata.py` |
| `src/atc_sim/navdata/models.py` | Frozen `ILS`, `Runway`, `Fix`, `AltitudeRestriction`, `SpeedRestriction`, `ProcedureLeg`, `Procedure` | ✓ VERIFIED | Exists, all 7 models present, all `ConfigDict(frozen=True)`, `Field()` range bounds present and tested |
| `src/atc_sim/navdata/eggw.py` | Real EGGW RWY 25 + ILS + OLNEY 2B SID + DET 2A STAR data | ✓ VERIFIED | Exists, every coordinate/restriction sourced with DMS/chart comments, identifier "25" throughout, HEN correctly unrestricted |
| `src/atc_sim/render/radar.py` | `world_to_screen`, `_draw_runway`, `_draw_procedure`, extended `build_static_background` | ✓ VERIFIED | Exists, all four present, wired into `app.py`, correct z-order (track→markers→text, mirrors `draw_aircraft`'s discipline) |
| `src/atc_sim/render/window.py` | `RUNWAY_COLOR`, `FIX_COLOR`, `FIX_TEXT_COLOR`, `PROCEDURE_LINE_COLOR` | ✓ VERIFIED | Exists, all 4 palette additions present, consistent with D-01 dark-flat EFIS palette |
| `src/atc_sim/app.py` | Wires `EGGW_RUNWAY`, `OLNEY_2B_SID`, `DET_2A_STAR` into `build_static_background` | ✓ VERIFIED | Confirmed exact call site `build_static_background(screen.get_size(), EGGW_RUNWAY, [OLNEY_2B_SID, DET_2A_STAR])` |
| `src/atc_sim/sim/aircraft.py` | Canvas-edge wrap removed, `spawn_default` repositioned to radar center | ✓ VERIFIED | `sim_step` has no wrap branches (grep-confirmed); `spawn_default` returns `x=CANVAS_WIDTH/2, y=CANVAS_HEIGHT/2` |
| `src/atc_sim/sim/interpolation.py` | Wrap-skip snap-to-curr special case removed | ✓ VERIFIED | No `return curr` path inside `interpolate()`; unused `CANVAS_WIDTH`/`CANVAS_HEIGHT` import dropped |
| `pyproject.toml` | `geographiclib>=2.1,<3.0` dependency | ✓ VERIFIED | Present in `[project.dependencies]`, alongside pygame-ce/pydantic |
| `tests/test_projection.py`, `tests/test_navdata.py`, `tests/test_boundary.py` (extended), `tests/test_interpolation.py` (updated), `tests/test_render_smoke.py` (updated) | RADAR-04/NAV-01/NAV-02/NAV-03 guards + Phase-1 regression tests | ✓ VERIFIED | All exist, substantive, independently re-run — 25/25 passing |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `render/radar.py` | `navdata/geo.py` | `project_to_local_xy_nm`/`PX_PER_NM` imported and called for every static element | WIRED | Confirmed by direct read: runway threshold, procedure fixes, and centerline all route through the same function |
| `app.py` | `navdata/eggw.py` | Imports `EGGW_RUNWAY`, `OLNEY_2B_SID`, `DET_2A_STAR` | WIRED | Confirmed exact import + call site |
| `render/radar.py` | `render/window.py` | Imports `RUNWAY_COLOR`/`FIX_COLOR`/`FIX_TEXT_COLOR`/`PROCEDURE_LINE_COLOR` | WIRED | Confirmed via import statement and usage in `_draw_runway`/`_draw_procedure` |
| `navdata/geo.py` | future `sim/separation.py` | Documented as the shared function, not yet consumed (Phase 5 does not exist yet) | ARCHITECTURALLY WIRED (forward-looking) | `navdata/geo.py` is pygame-free sim-core, `true_bearing_and_distance_nm`/`project_to_local_xy_nm` are the only geodesic functions in the codebase (no duplicate haversine/flat-earth code exists anywhere) — this satisfies RADAR-04's "shared with separation math" by construction; full proof is deferred by design to Phase 5 when `sim/separation.py` is written and must reuse these functions, not reimplement them |
| `sim/aircraft.py` | `sim/interpolation.py` | Wrap removed from both together (Pitfall A) | WIRED / CONSISTENT | Confirmed both removals happened in the same plan (02-04); `test_large_jump_now_lerps` and `test_sim_step_does_not_wrap_at_edge` both independently re-run and passing — no half-removed state |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| `render/radar.py::_draw_runway` | `runway.threshold_lat/lon`, `heading_deg_mag` | `navdata/eggw.py::EGGW_RUNWAY` | Real, sourced UK AIP values | ✓ FLOWING |
| `render/radar.py::_draw_procedure` | `leg.fix.lat/lon`, `leg.fix.name` | `navdata/eggw.py::OLNEY_2B_SID`/`DET_2A_STAR` | Real, sourced UK AIP chart values | ✓ FLOWING |
| Independent script re-derivation (see Method above) | Screen pixel offsets for all 6 fixes | `project_to_local_xy_nm` + `world_to_screen`, run outside the test suite | Matches 02-RESEARCH.md's independently-predicted offsets to within a few pixels | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full test suite passes (independent re-run) | `SDL_VIDEODRIVER=dummy python -m pytest -q` | `25 passed in 0.18s` | ✓ PASS |
| CORE-01/02/03 regression (named tests, no wave re-run) | `pytest tests/test_clock.py tests/test_boundary.py -v` | 7/7 passed | ✓ PASS |
| Projection circularity (named test) | `pytest tests/test_projection.py::test_projection_is_circular_not_elliptical` | pass | ✓ PASS |
| Magnetic-boundary round-trip (named test) | `pytest tests/test_projection.py::test_magnetic_variation_boundary` | pass | ✓ PASS |
| Wrap-removal regression (named tests) | `pytest tests/test_interpolation.py::test_sim_step_does_not_wrap_at_edge tests/test_interpolation.py::test_large_jump_now_lerps` | both pass | ✓ PASS |
| Independent headless projection re-derivation (not part of the test suite — extra adversarial check) | Custom script computing all 6 fix screen positions from real code | Matches 02-RESEARCH.md predictions within a few px; no clipping | ✓ PASS |
| `geographiclib` importable/functional | `pip show geographiclib` + `pyproject.toml` grep | 2.x pinned, present | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan(s) | Description | Status | Evidence |
|-------------|-----------------|-------------|--------|----------|
| NAV-01 | 02-02 | EGGW runway 25 threshold/heading/ILS (course, glideslope, DH) | ✓ SATISFIED | `EGGW_RUNWAY`, `test_runway_25_matches_sourced_data`, rendered + human-verified |
| NAV-02 | 02-03 | One SID + one STAR, named fixes, altitude/speed restrictions as data | ✓ SATISFIED | `OLNEY_2B_SID`/`DET_2A_STAR`, `test_olney_2b_sid_data`/`test_det_2a_star_data`, rendered + human-verified |
| NAV-03 | 02-02, 02-03 | Heading/course/track/bearing distinct fields, magnetic variation at one boundary | ✓ SATISFIED (with note) | `heading_deg_mag`/`course_deg_mag` distinct, `true_to_magnetic`/`magnetic_to_true` single boundary, tested; `track_deg` not yet instantiated in running code — see Truth #4 note and Gaps Summary |
| RADAR-04 | 02-01, 02-02, 02-04 | Shared cosine-corrected projection | ✓ SATISFIED | `navdata/geo.py`, geodesic-inverse-based, circularity-tested, pygame-free for future separation.py reuse |

**No orphaned requirements:** REQUIREMENTS.md's traceability table maps exactly NAV-01/02/03 and RADAR-04 to Phase 2, and the union of every plan's `requirements:` frontmatter field across 02-01 through 02-05 covers exactly this same set — no gaps, no extras.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | No `TODO`/`FIXME`/`XXX`/`HACK`/`TBD` markers found anywhere under `src/` or `tests/` | — | None — clean |
| `src/atc_sim/sim/aircraft.py` | 37, 39 | Word "placeholder" appears in a comment describing the still-Phase-1-level test aircraft motion | ℹ️ INFO | Accurate self-description of intentional, documented scope (Phase 3 replaces this with real procedure-following) — not a stub masquerading as done |
| ROADMAP.md Phase 2 goal / success criterion #4 | — | Literal text lists "track" as a field that should be modeled as distinct by end of Phase 2; no `track_deg` field exists anywhere in the codebase yet | ℹ️ INFO (not a blocker) | Defensible, documented deferral (02-RESEARCH.md explicitly scopes `track_deg` to Phase 3's Aircraft model; `heading == track` for all of v1 with no wind model; CONTEXT.md's Phase Boundary explicitly excludes aircraft lat/lon/procedure-following state this phase). No field-conflation risk exists (the actual hazard NAV-03 guards against) since track is simply absent, not confused with heading. Recommend Phase 3's plan explicitly re-confirm this convention is honored when the Aircraft model gains `track_deg`. |
| `.planning/phases/02-navdata-coordinate-projection/02-VALIDATION.md` | whole file | Template placeholders never filled in; `nyquist_compliant: false` | ℹ️ INFO | Planning artifact, not a phase deliverable; matches the same pattern already noted (and accepted) in Phase 1's verification report |

No blocking anti-patterns found.

### Human Verification Required

None outstanding. The behavior-dependent visual truths in this phase (runway/fix/track visual placement, true-circle rings, smooth non-wrapping motion) were already human-verified in-band during execution (`02-05-SUMMARY.md`, `human_judgment: true`, all 4 coverage items `status: pass`), per this task's explicit instruction to treat that as satisfied evidence. This report independently confirmed the underlying code (`_draw_runway`, `_draw_procedure`, `project_to_local_xy_nm`, the wrap removals) genuinely exists, is wired into `app.py`, and — via an independent screen-position re-derivation — produces geometrically correct output consistent with the human's observation. It is not merely claimed.

### Gaps Summary

No blocking gaps found. All 4 ROADMAP success criteria and all NAV-01/NAV-02/NAV-03/RADAR-04 requirements are verified against the actual codebase using independently re-run tests (not trusted executor output), direct code reads, git-history commit verification, and an independent re-derivation of projection math outside the test suite. The runway-redesignation ("25" not "26") requirement was checked project-wide — no stray "26" identifier values exist anywhere in code; all "26" occurrences are correctly confined to historical-redesignation narrative text. The Phase-1 wrap-at-edge removal (`sim/aircraft.py`, `sim/interpolation.py`) was verified clean and complete, with the full Phase-1 regression suite (CORE-01/02/03, 7 tests) still green.

One informational note is raised, not treated as a gap: the ROADMAP's Phase 2 goal/success-criterion #4 text names "track" as a field that should be modeled as distinct by phase end, but no `track_deg` field exists in the running codebase yet. This is a reasoned, documented deferral (02-RESEARCH.md explicitly scopes it to Phase 3's Aircraft model, consistent with 02-CONTEXT.md's Phase Boundary excluding aircraft lat/lon/procedure-following state this phase, and with the architectural fact that `heading == track` for all of v1 with no wind model). It creates no field-conflation risk and does not block the phase's core delivered value. Flagged here for visibility so Phase 3's plan can explicitly confirm the convention documented in 02-RESEARCH.md is honored when `track_deg` is finally instantiated.

---

*Verified: 2026-07-06T00:00:00Z*
*Verifier: Claude (gsd-verifier)*
