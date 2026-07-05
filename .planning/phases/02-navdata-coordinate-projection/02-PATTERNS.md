# Phase 2: Navdata & Coordinate Projection - Pattern Map

**Mapped:** 2026-07-05
**Files analyzed:** 8 (new: 5, modified: 3)
**Analogs found:** 8 / 8

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/atc_sim/navdata/models.py` (new) | model | CRUD (read-only reference data) | `src/atc_sim/sim/interpolation.py` (`AircraftSnapshot`, frozen Pydantic model) | role-match |
| `src/atc_sim/navdata/geo.py` (new) | utility | transform | `src/atc_sim/sim/aircraft.py` (`sim_step`, pure-math headless module) | role-match |
| `src/atc_sim/navdata/eggw.py` (new) | config (hand-authored data constants) | CRUD | `src/atc_sim/sim/aircraft.py::Aircraft.spawn_default()` (data-construction classmethod pattern) | partial-match |
| `src/atc_sim/navdata/__init__.py` (new) | config | — | `src/atc_sim/sim/__init__.py` | exact |
| `src/atc_sim/render/radar.py` (modified — add `_draw_runway`, `_draw_procedure`, `world_to_screen`, extend `build_static_background`) | component/render | request-response (per-frame draw) | `src/atc_sim/render/radar.py::build_static_background()` (itself — extend in place) | exact |
| `src/atc_sim/sim/interpolation.py` (modified — remove wrap-at-edge special case) | utility | transform | itself (existing `interpolate()`) | exact |
| `tests/test_projection.py` (new) | test | transform (pure-function assertions) | `tests/test_interpolation.py` | exact |
| `tests/test_navdata.py` (new, likely) | test | CRUD (model validation) | `tests/test_interpolation.py` (Pydantic `ValidationError` assertions) + `tests/test_boundary.py` (headless import-safety pattern) | role-match |

## Pattern Assignments

### `src/atc_sim/navdata/models.py` (model, CRUD)

**Analog:** `src/atc_sim/sim/interpolation.py` lines 1-26, and `src/atc_sim/sim/aircraft.py` lines 1-27

**Module docstring / pygame-free boundary declaration** (interpolation.py lines 1-14):
```python
"""...
This module MUST NOT import pygame — it stays headlessly testable via
pytest with no display, enforced by tests/test_boundary.py.
"""
```
Copy this exact framing into `navdata/models.py`'s docstring — note `tests/test_boundary.py` currently only scans `src/atc_sim/sim/`, NOT `src/atc_sim/navdata/`, per RESEARCH.md's "Pattern 2" — so if strict headless enforcement of `navdata/` is wanted, `test_boundary.py`'s `SIM_DIR` glob will need to be extended to also scan `src/atc_sim/navdata/` (flag this for the plan).

**Frozen Pydantic model pattern** (interpolation.py lines 21-26):
```python
class AircraftSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)
    x: float
    y: float
    heading_deg: float
```
Use identically for `Fix`, `AltitudeRestriction`, `SpeedRestriction`, `ProcedureLeg`, `Procedure`, `ILS`, `Runway` — all `model_config = ConfigDict(frozen=True)`, matching RESEARCH.md's Pydantic model design (already given verbatim in RESEARCH.md lines 238-294 — use that code directly).

**Field constraint pattern** (aircraft.py lines 24-27):
```python
x: float
y: float
heading_deg: float = Field(ge=0.0, lt=360.0)
speed_px_per_sec: float = Field(gt=0.0)
```
Same `Field(ge=..., lt=...)` bounds-validation convention applies to `lat`/`lon`/`course_deg_mag`/`altitude_ft`/`speed_kt` in the new navdata models — copy the `Field(...)` style, not raw type hints alone.

**Import style:** `from pydantic import BaseModel, ConfigDict, Field` — exact same import line as both analogs.

---

### `src/atc_sim/navdata/geo.py` (utility, transform)

**Analog:** `src/atc_sim/sim/aircraft.py` lines 1-19, 35-44 (pure-math, headless module)

**Module docstring / headless declaration pattern** (aircraft.py lines 1-11):
```python
"""...
This module MUST NOT import pygame — it stays headlessly testable via
pytest with no display, enforced by tests/test_boundary.py.
"""
```

**Pure trig/geometry function pattern** (aircraft.py lines 35-44, `sim_step`):
```python
def sim_step(aircraft: Aircraft, dt: float) -> None:
    """... Compass convention: heading_deg=0 is north/up, increasing clockwise."""
    rad = math.radians(aircraft.heading_deg)
    aircraft.x += math.sin(rad) * aircraft.speed_px_per_sec * dt
    aircraft.y -= math.cos(rad) * aircraft.speed_px_per_sec * dt
```
This is the exact `sin`/`cos` + compass-clockwise convention (`0=north, sin=x, -cos=y`) that RESEARCH.md's `project_to_local_xy_nm()` reuses — confirms the compass convention is already established project-wide; do not introduce a different angle convention in `geo.py`.

**Concrete implementation to use as-is** (from RESEARCH.md "Coordinate Projection" section, already vetted against this codebase's conventions):
```python
from geographiclib.geodesic import Geodesic

_GEOD = Geodesic.WGS84

ORIGIN_LAT = 51.877044
ORIGIN_LON = -0.354486
PX_PER_NM = 8.0

def true_bearing_and_distance_nm(lat1, lon1, lat2, lon2) -> tuple[float, float]:
    result = _GEOD.Inverse(lat1, lon1, lat2, lon2)
    return result["azi1"] % 360.0, result["s12"] / 1852.0

def project_to_local_xy_nm(lat: float, lon: float) -> tuple[float, float]:
    bearing_deg, distance_nm = true_bearing_and_distance_nm(ORIGIN_LAT, ORIGIN_LON, lat, lon)
    rad = math.radians(bearing_deg)
    return distance_nm * math.sin(rad), distance_nm * math.cos(rad)

MAGNETIC_VARIATION_DEG = 1.2

def true_to_magnetic(true_deg: float, variation_deg: float = MAGNETIC_VARIATION_DEG) -> float:
    return (true_deg - variation_deg) % 360.0

def magnetic_to_true(mag_deg: float, variation_deg: float = MAGNETIC_VARIATION_DEG) -> float:
    return (mag_deg + variation_deg) % 360.0
```
(Replace the `__import__("math")` calls in RESEARCH.md's draft with a normal top-level `import math` — the draft used inline imports only for brevity in the research doc; follow this codebase's normal top-of-file `import math` style, as seen in `aircraft.py` line 13 and `radar.py` line 16.)

---

### `src/atc_sim/navdata/eggw.py` (config/data, CRUD)

**Analog:** `src/atc_sim/sim/aircraft.py::Aircraft.spawn_default()` lines 29-32 (data-construction classmethod, comment-annotated with the decision it encodes)

```python
@classmethod
def spawn_default(cls) -> "Aircraft":
    # D-02: simplest possible motion — straight line, fixed heading, wraps at edge
    return cls(x=0.0, y=CANVAS_HEIGHT / 2, heading_deg=90.0, speed_px_per_sec=60.0)
```
Follow this same "inline comment cites the decision/source next to the literal value" convention for every hand-typed coordinate in `eggw.py` — per RESEARCH.md's own instruction, preserve the original DMS string as a comment beside each decimal value:
```python
# RWY 25 threshold, UK AIP eAIP EG-AD-2.EGGW, live fetch 2024-03-21 AIRAC:
# 51°52'37.36"N, 000°21'16.15"W
THRESHOLD_LAT = 51.877044
THRESHOLD_LON = -0.354486
```
Module docstring must explain the "26"-label-but-"25"-sourced discrepancy (RESEARCH.md Pitfall C) — no direct codebase analog for this specific narrative comment, but follow the same "docstring explains a non-obvious historical/decision reason before any code" style used in `sim/aircraft.py` lines 1-11 and `sim/interpolation.py` lines 1-14.

---

### `src/atc_sim/render/radar.py` (extend `build_static_background`, add runway/fix/procedure drawing + `world_to_screen`)

**Analog:** itself — `build_static_background()` (lines 52-69) and `draw_frame()` (lines 97-109)

**Existing cached-background pattern to extend, not replace** (lines 52-69):
```python
def build_static_background(size: tuple[int, int]) -> pygame.Surface:
    """Rendered once at startup and blitted each frame — range rings/sector
    lines never change, so don't redraw primitives every frame."""
    surface = pygame.Surface(size)
    surface.fill(BG_COLOR)

    for i in range(1, NUM_RINGS + 1):
        pygame.draw.circle(surface, RING_COLOR, CENTER, RING_STEP_PX * i, width=1)

    for i in range(NUM_SECTOR_LINES):
        angle = math.radians(360 / NUM_SECTOR_LINES * i)
        end = (
            CENTER[0] + math.sin(angle) * RING_STEP_PX * NUM_RINGS,
            CENTER[1] - math.cos(angle) * RING_STEP_PX * NUM_RINGS,
        )
        pygame.draw.aaline(surface, SECTOR_COLOR, CENTER, end)

    return surface
```
Add `_draw_runway(surface, runway)` and `for proc in procedures: _draw_procedure(surface, proc)` calls inside this function body (per RESEARCH.md Pattern 1), changing the signature to accept `runway`/`procedures` params — mirrors how `draw_aircraft` composes several `pygame.draw.*` calls in a fixed z-order (see below).

**Z-order / layered-drawing convention** (`draw_aircraft`, lines 72-94): draws trail, then vector, then dot last "so the dot is never occluded." Apply the same ordering discipline for the new static elements: draw procedure track line first, then fix markers, then fix name text on top (so text is never occluded by the line/marker), and draw the runway threshold/centerline before rings-derived elements or after — pick one order and comment why, per this convention.

**Text rendering:** no existing analog in this codebase (Phase 1 draws no text) — CLAUDE.md/STACK.md specifies `pygame.font`/`pygame.freetype` (bundled with pygame-ce) for this; there is no prior in-repo font-rendering call to copy, so this is a **new pattern** (see "No Analog Found" below) — follow the general "load font once, cache it, `font.render()` into a positioned blit" idiom typical of pygame, matching the module's "compute once at startup, blit every frame" philosophy already used for `background`.

**Direct import of navdata types is architecturally fine here** (per RESEARCH.md Pattern 2): unlike `RenderState` (a `Protocol` used because `sim/interpolation.py`'s mutable-state boundary must not be imported directly), `atc_sim.navdata.models` types are frozen read-only reference data and `render/radar.py` may `import atc_sim.navdata.models` directly — do NOT build a second Protocol for navdata; the existing `RenderState` Protocol (lines 32-39) stays scoped to aircraft snapshot state only.

**`world_to_screen` helper** (new function, RESEARCH.md-supplied, mirrors radar.py's existing `CENTER`/pixel-space conventions at lines 42-43):
```python
def world_to_screen(x_nm: float, y_nm: float, center: tuple[int, int], px_per_nm: float) -> tuple[int, int]:
    screen_x = center[0] + x_nm * px_per_nm
    screen_y = center[1] - y_nm * px_per_nm  # north = up = smaller screen y
    return int(screen_x), int(screen_y)
```
This mirrors the exact `+sin`/`-cos`-style y-flip convention already used in `build_static_background`'s sector-line loop (line 65: `CENTER[1] - math.cos(angle) * ...`) and in `draw_aircraft`'s vector math (line 90) — consistent sign convention across the file.

**Import block convention** (lines 16-29):
```python
import math
from collections import deque
from typing import Protocol

import pygame

from atc_sim.render.window import (
    AIRCRAFT_COLOR,
    BG_COLOR,
    RING_COLOR,
    SECTOR_COLOR,
    TRAIL_COLOR,
    VECTOR_COLOR,
)
```
Add new color constants (see Shared Patterns below) to this same import block; add `from atc_sim.navdata.models import Fix, Procedure, Runway` (or similar) as a new import group beneath it.

---

### `src/atc_sim/render/window.py` (modified — add new color constants)

**Analog:** itself, lines 20-26 (existing D-01 palette block)

```python
# D-01 color palette
BG_COLOR = (18, 24, 32)          # dark grey/blue
RING_COLOR = (60, 90, 100)       # muted cyan-grey
SECTOR_COLOR = (40, 60, 68)
AIRCRAFT_COLOR = (0, 220, 220)   # cyan
TRAIL_COLOR = (0, 140, 140)
VECTOR_COLOR = (230, 240, 240)   # near-white
```
Add `RUNWAY_COLOR`, `FIX_COLOR`, `FIX_TEXT_COLOR`, `PROCEDURE_LINE_COLOR` to this same block, in the same `(R, G, B)` tuple style with an inline comment describing the visual role — per CONTEXT.md D-01/D-04 ("extend this same palette rather than introducing new ad-hoc colors" / "stay within the existing thin-line, low-clutter EFIS aesthetic").

---

### `src/atc_sim/sim/interpolation.py` (modified — remove Phase-1 wrap-at-edge special case)

**Analog:** itself, lines 42-56 (current `interpolate()`)

**Code to remove** (lines 43-50):
```python
    # D-02 wrap-skip edge case: a position jump greater than half the canvas
    # dimension between snapshots means the sim tick wrapped the aircraft at
    # the canvas edge. Lerping across that seam would draw a fast streak
    # across the whole canvas for one interpolation window, so snap straight
    # to curr instead. Phase-1-only special case — removed once Phase 2
    # replaces wrap-at-edge with real navdata paths; do not generalize.
    if abs(curr.x - prev.x) > CANVAS_WIDTH / 2 or abs(curr.y - prev.y) > CANVAS_HEIGHT / 2:
        return curr
```
This comment itself explicitly says "removed once Phase 2 replaces wrap-at-edge with real navdata paths" — confirms this deletion is in-scope and expected. After removal, `interpolate()` reduces to a plain `_lerp`/`_lerp_angle_deg` call; keep those two helper functions (lines 32-39) unchanged — they remain correct for real navdata paths. Also drop the now-unused `CANVAS_WIDTH, CANVAS_HEIGHT` import from `atc_sim.sim.aircraft` at line 18 if nothing else in the file uses them (check `aircraft.py` too, since `CANVAS_WIDTH`/`CANVAS_HEIGHT` may still be needed there or become obsolete once `Aircraft` no longer wraps at edges — flag for planner).

---

### `tests/test_projection.py` (test, transform)

**Analog:** `tests/test_interpolation.py` (whole file — headless pytest module, no pygame import, `pytest.approx` for float assertions)

**Structure/imports pattern** (test_interpolation.py lines 1-13):
```python
"""Headless tests for ... No pygame import anywhere in this file or in the
modules under test.
"""
import pytest
from pydantic import ValidationError

from atc_sim.sim.aircraft import ...
from atc_sim.sim.interpolation import ...
```
Mirror exactly for `test_projection.py`, importing `from atc_sim.navdata.geo import project_to_local_xy_nm, true_bearing_and_distance_nm, true_to_magnetic, magnetic_to_true`.

**Float-tolerance assertion pattern** (test_interpolation.py line 42): `assert result.x == pytest.approx(50.0)` — use `pytest.approx` for all nm/pixel/degree comparisons in the new circle-not-ellipse test (RESEARCH.md's suggested test at RESEARCH.md lines 522-539) rather than exact `==` float comparison.

**Docstring-as-spec-reference convention** (test_interpolation.py lines 46-53, `test_heading_interpolation_shortest_path`): each test function has an inline comment explaining *why* the assertion matters (referencing the spec pitfall it guards against) — replicate for `test_projection_is_circular_not_elliptical`, explicitly referencing "RADAR-04 / Pitfall 5" in the comment, matching RESEARCH.md's own suggested docstring.

---

### `tests/test_navdata.py` (test, CRUD — model validation)

**Analog:** `tests/test_interpolation.py::test_aircraft_rejects_bad_fields` (lines 98-103) + `tests/test_boundary.py` (whole file, for the "headless, no pygame" scan style)

**Pydantic validation-rejection pattern** (test_interpolation.py lines 98-103):
```python
def test_aircraft_rejects_bad_fields():
    with pytest.raises(ValidationError):
        Aircraft(x=0.0, y=0.0, heading_deg=360.0, speed_px_per_sec=60.0)
```
Use identically for `Fix(lat=91.0, ...)`, `AltitudeRestriction(altitude_ft=-100, ...)`, `Runway(heading_deg_mag=400.0, ...)`, etc.

**If extending the boundary guard to cover `navdata/`:** copy `tests/test_boundary.py`'s `SIM_DIR` + regex-scan approach (lines 17-44) but add a second directory constant (e.g. `NAVDATA_DIR`) and either extend the same test function or add a sibling `test_navdata_package_never_imports_pygame()` — flag this as a planner decision, since RESEARCH.md's Pattern 2 explicitly says `navdata/` is *not currently* scanned and that a direct `atc_sim.navdata.models` import from `render/radar.py` is architecturally fine specifically because it's unscanned; extending the guard would be a deliberate stricter-than-required choice.

## Shared Patterns

### Headless sim-core module docstring (pygame-free declaration)
**Source:** `src/atc_sim/sim/aircraft.py` lines 9-11, `src/atc_sim/sim/interpolation.py` lines 12-14
**Apply to:** `navdata/models.py`, `navdata/geo.py`, `navdata/eggw.py`, `navdata/__init__.py`
```python
"""...
This module MUST NOT import pygame — it stays headlessly testable via
pytest with no display, enforced by tests/test_boundary.py.
"""
```

### Frozen Pydantic v2 model convention
**Source:** `src/atc_sim/sim/interpolation.py` lines 21-26
**Apply to:** All new navdata models (`Fix`, `AltitudeRestriction`, `SpeedRestriction`, `ProcedureLeg`, `Procedure`, `ILS`, `Runway`)
```python
class SomeModel(BaseModel):
    model_config = ConfigDict(frozen=True)
    field: float = Field(ge=..., lt=...)
```

### Static-background caching (compute once, blit every frame)
**Source:** `src/atc_sim/render/radar.py::build_static_background()` lines 52-69, and its call site in `app.py` line 32 (`background = build_static_background(screen.get_size())`, called once before the loop) plus line 56 (`draw_frame` blits it every frame)
**Apply to:** Runway symbol, fix markers/names, procedure track lines — all extend the same cached surface, never redrawn per-tick.

### Color palette extension, not ad-hoc colors
**Source:** `src/atc_sim/render/window.py` lines 20-26
**Apply to:** Any new render/radar.py drawing code — pull new constants (`RUNWAY_COLOR`, `FIX_COLOR`, `FIX_TEXT_COLOR`, `PROCEDURE_LINE_COLOR`) from `window.py`, imported the same way existing colors are (`radar.py` lines 22-29).

### Compass/pixel angle convention (0=north/up, clockwise, sin=x, -cos=y)
**Source:** `src/atc_sim/sim/aircraft.py` lines 41-43, `src/atc_sim/render/radar.py` lines 62-66 and line 90
**Apply to:** `navdata/geo.py::project_to_local_xy_nm()` and `render/radar.py::world_to_screen()` — keep the same sign convention throughout so bearings/headings/screen positions never silently disagree in orientation.

### Sim/render pygame-import boundary
**Source:** `tests/test_boundary.py` (whole file), and the "only app.py imports both" rule stated in `render/radar.py` lines 6-13
**Apply to:** `navdata/geo.py` and `navdata/models.py` must never import pygame; `render/radar.py` may import `atc_sim.navdata.*` directly (unlike `atc_sim.sim.*`, which is Protocol-mediated).

## No Analog Found

| File/Concern | Role | Data Flow | Reason |
|---|---|---|---|
| Text rendering for fix names (D-01) | component/render | request-response | Phase 1 draws no text anywhere; no existing `pygame.font`/`pygame.freetype` call to copy in this codebase. Follow CLAUDE.md/STACK.md's guidance (load font once, cache, `font.render()` + blit) as a new pattern, consistent with the "compute once, reuse" philosophy of `build_static_background()`. |
| Waypoint marker glyph (dot/triangle) shape | component/render | request-response | No existing non-circle/non-line primitive drawn in `radar.py` (only `pygame.draw.circle`/`aaline` used so far for rings/aircraft). Use `pygame.draw.circle` for the dot variant (matches existing primitive usage) or `pygame.draw.polygon` for a triangle variant — both are standard pygame calls but neither has an in-repo precedent yet. |

## Metadata

**Analog search scope:** `src/atc_sim/` (sim/, render/, app.py), `tests/`
**Files scanned:** `src/atc_sim/render/radar.py`, `src/atc_sim/render/window.py`, `src/atc_sim/sim/aircraft.py`, `src/atc_sim/sim/interpolation.py`, `src/atc_sim/sim/clock.py`, `src/atc_sim/app.py`, `tests/test_boundary.py`, `tests/test_interpolation.py`, `tests/test_render_smoke.py`, `tests/test_clock.py`
**Pattern extraction date:** 2026-07-05
