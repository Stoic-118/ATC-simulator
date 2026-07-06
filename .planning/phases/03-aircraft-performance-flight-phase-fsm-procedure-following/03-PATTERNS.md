# Phase 3: Aircraft Performance, Flight-Phase FSM & Procedure Following - Pattern Map

**Mapped:** 2026-07-06
**Files analyzed:** 9 (5 new sim modules, 1 evolved model, 1 evolved interpolation, 1 evolved render/app integration, 1 evolved app.py)
**Analogs found:** 9 / 9 (all files have a same-repo analog since this phase entirely extends existing patterns; no external-pattern fallback needed)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|--------------------|------|-----------|-----------------|----------------|
| `src/atc_sim/sim/performance.py` | model + utility (frozen reference data + pure kinematics functions) | CRUD (static lookup) + transform (kinematics math) | `src/atc_sim/navdata/models.py` (frozen model conventions) + `src/atc_sim/navdata/geo.py` (module-level pure-function helpers) | exact (frozen-model half) / role-match (function half) |
| `src/atc_sim/navdata/eggw.py`-style fleet constants block (lives inside `performance.py`, not a separate file) | config/model instantiation | CRUD (static data) | `src/atc_sim/navdata/eggw.py` (hand-authored constant instances of a frozen model, with cited/tagged sourcing comments) | exact |
| `src/atc_sim/sim/phase.py` | model (enum) + service (transition function) | event-driven (state transition on completion condition) | none in-repo (first FSM in codebase) — closest analog is `navdata/models.py`'s `Literal` restriction-kind pattern for the enum-of-choices style, and `sim/clock.py` for "small pure function + module-level constant table" structure | role-match (no direct FSM analog exists; RESEARCH.md's own code example is the primary source here) |
| `src/atc_sim/sim/procedure.py` | service (compute_target) + utility (leg advance) | transform (derives Targets struct each tick) + CRUD (reads navdata, mutates leg_index) | `src/atc_sim/navdata/geo.py` (module-level pure geodesic helper functions, `@dataclass`-adjacent style, docstring-heavy "why," reuse-not-reinvent framing) | exact |
| `src/atc_sim/sim/demo_traffic.py` | service (spawn/removal/loop orchestration) | event-driven (per-tick condition checks) + CRUD (list membership) | `src/atc_sim/sim/aircraft.py::spawn_default()` classmethod pattern, and `app.py`'s per-tick `on_tick` closure style for orchestration | role-match |
| `src/atc_sim/sim/aircraft.py` (evolved) | model (Aircraft state) + service (`sim_step` dispatcher) | CRUD (mutable validated state) + event-driven (phase dispatch) | itself (Phase 1/2 version) — the file being evolved is its own best analog for conventions to preserve | exact (self) |
| `src/atc_sim/sim/interpolation.py` (evolved: add altitude/phase fields as needed) | model (frozen snapshot) + transform (lerp) | transform (interpolate two frozen states) | itself (Phase 1/2 version) | exact (self) |
| `src/atc_sim/render/radar.py` (evolved: `RenderState` Protocol, no new draw logic required per D-05) | component (render) | request-response (draw call per frame) | itself (Phase 1/2 version) — `RenderState` Protocol duck-typing pattern | exact (self) |
| `src/atc_sim/app.py` (evolved: replace single `Aircraft.spawn_default()` call with `demo_traffic` spawn/list/loop wiring) | config/composition-root | event-driven (main loop `on_tick`) | itself (Phase 1/2 version) | exact (self) |
| `tests/test_performance.py`, `tests/test_phase.py`, `tests/test_procedure.py`, `tests/test_demo_traffic.py` (new) | test | CRUD/transform/event-driven per module under test | `tests/test_navdata.py` (frozen-model + data-correctness test style), `tests/test_clock.py` (pure-function/state-machine-adjacent unit test style) | exact |
| `tests/test_boundary.py` (evolved: no new dirs to add — `sim/` already fully scanned; verify new modules stay inside `sim/`) | test (architectural guard) | N/A | itself | exact (self, likely unmodified) |

## Pattern Assignments

### `src/atc_sim/sim/performance.py` (model + utility, CRUD + transform)

**Analogs:** `src/atc_sim/navdata/models.py` (frozen model shape) and `src/atc_sim/navdata/geo.py` (pure function + module docstring style)

**Frozen-model pattern** (from `navdata/models.py` lines 16-25):
```python
class ILS(BaseModel):
    model_config = ConfigDict(frozen=True)

    identifier: str | None = None
    frequency_mhz: float | None = None
    course_deg_mag: float = Field(ge=0.0, lt=360.0)
    glideslope_deg: float = Field(gt=0.0, lt=10.0)
    category: Literal["CAT I"] = "CAT I"
    decision_height_ft: int = Field(gt=0)
```
Apply the same shape to `PerformanceProfile`: `model_config = ConfigDict(frozen=True)`, `Field(gt=0.0)` bounds on every numeric, `str`/`Literal` for name/category. RESEARCH.md's own sketch (03-RESEARCH.md lines 202-258) already follows this exactly — use it directly.

**Hand-authored constant-instance pattern with sourcing comments** (from `navdata/eggw.py` lines 27-58):
```python
# RWY 25 localizer — course is calibrated to the extended runway centerline
# ...
# identifier="ILJ", frequency_mhz=109.15 [CITED: flightplandatabase.com,
#   low confidence — not independently confirmed ...]
_EGGW_ILS = ILS(
    identifier="ILJ",
    frequency_mhz=109.15,
    course_deg_mag=254.0,
    ...
)
```
Apply the same `[VERIFIED]`/`[CITED]`/`[ASSUMED]` sourcing-tag comment convention immediately above each `PerformanceProfile(...)` fleet constant (`BOEING_737_800`, `EMBRAER_E175`, `ATR_72_600`, `CESSNA_CJ2_PLUS` — values already given in RESEARCH.md Pattern A), and above the `FLEET: dict[str, PerformanceProfile]` aggregate, mirroring how `eggw.py` documents each real value's confidence.

**Module-level pure-function pattern with "why reuse this" docstring** (from `navdata/geo.py` lines 37-49):
```python
def true_bearing_and_distance_nm(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> tuple[float, float]:
    """Returns (true_bearing_deg, distance_nm) from point1 to point2.

    This is the ONE function both the radar projection and (later)
    separation.py should call for geodesic distance/bearing — never
    reimplement haversine or a flat-earth approximation elsewhere.
    """
    result = _GEOD.Inverse(lat1, lon1, lat2, lon2)
    ...
```
Apply this shape to `turn_rate_deg_per_sec(bank_deg, speed_kt)` and any climb/descend/accelerate-toward-target helpers: plain module-level functions taking primitives/profile+state+target, single-purpose docstring naming the ONE place this logic should live.

**Module header pattern** (must appear at top, matching every other sim-core file):
```python
"""...
This module MUST NOT import pygame — it stays headlessly testable via
pytest with no display, enforced by tests/test_boundary.py.
"""
```
Copy verbatim (adjusted first paragraph) from `sim/aircraft.py` lines 13-15 / `navdata/geo.py` lines 8-10 / `navdata/models.py` lines 7-9 — every sim-core and navdata module in this project has this exact sentence.

---

### `src/atc_sim/sim/phase.py` (model + service, event-driven)

**No direct in-repo FSM analog exists** — this is the first state machine in the codebase. Use RESEARCH.md's own worked example directly (03-RESEARCH.md lines 268-304) as the primary source, since it was authored specifically to match `ARCHITECTURE.md` Pattern 2 and this project's conventions:

```python
from enum import Enum, auto


class Phase(Enum):
    TAXI_OUT = auto()
    DEPARTURE_ROLL = auto()
    CLIMB = auto()
    ENROUTE = auto()
    DESCENT = auto()
    APPROACH = auto()
    LANDED = auto()
    TAXI_IN = auto()


LEGAL_TRANSITIONS: dict[Phase, set[Phase]] = {
    Phase.TAXI_OUT: {Phase.DEPARTURE_ROLL},
    Phase.DEPARTURE_ROLL: {Phase.CLIMB},
    Phase.CLIMB: {Phase.ENROUTE},
    Phase.ENROUTE: {Phase.DESCENT},
    Phase.DESCENT: {Phase.APPROACH},
    Phase.APPROACH: {Phase.LANDED},
    Phase.LANDED: {Phase.TAXI_IN},
    Phase.TAXI_IN: set(),
}


def transition_to(current: Phase, new: Phase) -> Phase:
    if new not in LEGAL_TRANSITIONS[current]:
        raise ValueError(f"Illegal transition {current} -> {new}")
    return new
```

**Adjacent in-repo convention to borrow:** `navdata/models.py`'s `RestrictionKind = Literal["at", "at_or_above", "at_or_below"]` (line 37) shows this project's taste for a small closed set of named states declared as a module-level constant right above the models that use it — `phase.py`'s `LEGAL_TRANSITIONS` dict should be placed the same way: directly below the `Phase` enum, at module level, all-caps, with a comment block explaining forward-compatible-but-currently-unreached transitions (RESEARCH.md lines 283-287 already supplies this comment).

**Module header:** same "MUST NOT import pygame" sentence as above.

**Testing pattern to copy** (from `tests/test_clock.py` lines 1-9, 11-29): headless pure-function tests, no Aircraft construction needed —
```python
"""Headless tests for the fixed-timestep accumulator sim clock.
...
No pygame import anywhere in this file or in the module under test.
"""

from atc_sim.sim.clock import SimClock, TICK_DT, MAX_TICKS_PER_FRAME


def test_tick_count_independent_of_call_frequency():
    ...
```
Apply directly: `tests/test_phase.py` should import only `Phase`, `LEGAL_TRANSITIONS`, `transition_to` and assert legal/illegal transitions raise `ValueError` — zero `Aircraft` construction, matching RESEARCH.md's stated rationale for splitting `phase.py` out (independently unit-testable with zero `Aircraft` construction overhead).

---

### `src/atc_sim/sim/procedure.py` (service, transform)

**Analog:** `src/atc_sim/navdata/geo.py` (module-level pure functions over frozen inputs, heavy "why" docstrings, explicit "this is the ONE place" framing)

**Imports pattern** (from `navdata/geo.py` lines 12-16, adapted per RESEARCH.md lines 341-343):
```python
import math

from atc_sim.navdata.geo import project_to_local_xy_nm, true_to_magnetic
```

**Core transform pattern — reuse existing geo helpers, never reimplement bearing math** (from `navdata/geo.py` lines 52-72, `project_to_local_xy_nm`):
```python
def project_to_local_xy_nm(lat: float, lon: float) -> tuple[float, float]:
    bearing_deg, distance_nm = true_bearing_and_distance_nm(ORIGIN_LAT, ORIGIN_LON, lat, lon)
    rad = math.radians(bearing_deg)
    x_nm = distance_nm * math.sin(rad)
    y_nm = distance_nm * math.cos(rad)
    return x_nm, y_nm
```
`compute_target()` must call this exact function (never reimplement geodesic math) to get each leg's fix into the same local-nm space as `Aircraft.x_nm`/`y_nm`, per RESEARCH.md's Pattern D and the "Don't Hand-Roll" table entry ("Great-circle bearing/distance math... Use Instead: the existing `navdata/geo.py`").

**Compass-convention consistency to copy exactly** (from `sim/aircraft.py` lines 48-52, `navdata/geo.py` lines 63-64, `render/radar.py` lines 79-87):
```python
# Compass convention matches sim/aircraft.py's sim_step: 0deg = north,
# increasing clockwise, sin=x, cos=y.
```
Every new trig call in `procedure.py` (`atan2`-derived bearings, kinematics moves in `aircraft.py`) MUST use this identical `sin=x, cos=y` (or its `-cos=y` screen-space mirror) convention — this is the single most load-bearing cross-cutting invariant in the codebase (three existing files already state it verbatim).

**True→magnetic conversion boundary** (from `navdata/geo.py` lines 75-81):
```python
def true_to_magnetic(true_deg: float, variation_deg: float = MAGNETIC_VARIATION_DEG) -> float:
    """The ONE place a geographiclib-computed TRUE bearing becomes a
    magnetic value for comparison against/display alongside charted
    (already-magnetic) courses."""
    return (true_deg - variation_deg) % 360.0
```
`compute_target()` must call `true_to_magnetic()` exactly once on any `atan2`-derived bearing before returning it as `Targets.heading_deg` (RESEARCH.md Pitfall "Heading stored as true bearing instead of magnetic" — this is a named, previously-documented pitfall in this exact codebase, PITFALLS.md Pitfall 4).

**Restriction look-ahead core logic:** use RESEARCH.md's `compute_target`/`_next_altitude_restriction_ft`/`_next_speed_restriction_kt`/`advance_leg_if_reached` code verbatim (03-RESEARCH.md lines 339-405) — this was purpose-built against this project's real `ProcedureLeg`/`AltitudeRestriction` shape and already avoids reproducing Pitfall 7.

**Frozen throwaway struct pattern** — use `dataclasses`, not Pydantic, per `CLAUDE.md`'s own stated convention ("lightweight internal-only structs... recomputed every frame where Pydantic's construction overhead isn't worth paying"):
```python
@dataclass(frozen=True)
class Targets:
    heading_deg: float
    altitude_ft: float
    speed_kt: float
```

---

### `src/atc_sim/sim/demo_traffic.py` (service, event-driven + CRUD)

**Analog:** `src/atc_sim/sim/aircraft.py::spawn_default()` classmethod (lines 33-41) for spawn-construction style, and `app.py`'s `on_tick` closure (lines 45-51) for "called once per sim tick, mutates shared list" orchestration style.

**Spawn-construction pattern to extend** (from `sim/aircraft.py` lines 33-41):
```python
@classmethod
def spawn_default(cls) -> "Aircraft":
    # Phase 2: spawn at the radar center ... within the real EGGW geography
    return cls(x=CANVAS_WIDTH / 2, y=CANVAS_HEIGHT / 2, heading_deg=90.0, speed_px_per_sec=60.0)
```
`demo_traffic.spawn_departure(performance_profile)` / `spawn_arrival(performance_profile)` should follow the same "one classmethod-or-module-function per spawn kind, comment explaining *why* this position/state was chosen" style — but per RESEARCH.md's structure recommendation these should be plain module-level functions in `demo_traffic.py`, not new classmethods on `Aircraft` (keeps `aircraft.py` from growing spawn-orchestration concerns it doesn't own).

**Per-tick orchestration pattern to extend** (from `app.py` lines 45-51):
```python
def on_tick(dt: float) -> None:
    nonlocal prev_state
    prev_state = capture_state(aircraft)
    sim_step(aircraft, dt)
    trail.append((aircraft.x, aircraft.y))
```
`demo_traffic.py` needs an equivalent per-tick entry point (e.g. `update_demo_traffic(aircraft_list, dt)`) called from `app.py`'s `on_tick`, which both calls `sim_step()` per aircraft AND performs the removal/respawn list-membership check — kept as a distinct function from `sim_step()` per RESEARCH.md's Architectural Responsibility Map ("Demo-harness spawn/removal/looping... is a distinct concern from aircraft state itself").

**Type-rotation for fleet coverage** — RESEARCH.md's Pitfall "3 distinct types visibly differentiated is not automatically satisfied" (lines 429-434) flags this as a real requirement-satisfaction risk; implement a fixed round-robin index over `FLEET`'s 4 types, advanced once per loop-restart per slot (departure/arrival independently), not a hardcoded always-737 spawn.

---

### `src/atc_sim/sim/aircraft.py` (evolved model + dispatcher)

**Analog:** itself (Phase 1/2 version) — preserve every existing convention while adding fields.

**Model conventions to preserve exactly** (lines 25-31):
```python
class Aircraft(BaseModel):
    model_config = ConfigDict(validate_assignment=True)  # v2 style; catches bad mutations

    x: float
    y: float
    heading_deg: float = Field(ge=0.0, lt=360.0)
    speed_px_per_sec: float = Field(gt=0.0)
```
New fields (per RESEARCH.md: `x_nm`/`y_nm` replacing pixel coords, `altitude_ft`, `phase: Phase`, `phase_elapsed_sec: float = 0.0`, `procedure: Procedure`, `procedure_leg_index: int = 0`, `performance: PerformanceProfile`) must keep `validate_assignment=True` and `Field(...)` bounds identically — this is the one existing convention every downstream summary/insight explicitly calls out to preserve ("preserving the existing Pydantic v2 conventions").

**Dispatcher pattern to introduce (new, but must avoid the "scattered inline conditionals" pitfall):** use RESEARCH.md's Code Examples section verbatim (03-RESEARCH.md lines 466-493) as the concrete `sim_step()` shape — small dispatch to `_step_taxi`/`_step_departure_roll`/`_step_airborne`/`_step_landed` helpers, each independently testable, matching the existing single `sim_step(aircraft, dt)` top-level function signature convention already established (line 44 of the current file: `def sim_step(aircraft: Aircraft, dt: float) -> None:`).

**Module header and docstring-per-decision convention:** every change should get an inline comment tagged `# Phase 3 (...)：` mirroring the existing `# Phase 2 (Pitfall A): ...` comment style (lines 9-11, 53-55) — this project consistently documents *why* a change was made at the point of change, not just what changed.

---

### `src/atc_sim/sim/interpolation.py` (evolved snapshot)

**Analog:** itself — extend `AircraftSnapshot` only if a new field needs interpolation for rendering (RESEARCH.md explicitly says this is NOT required this phase since D-04 defers a datablock: "extend AircraftSnapshot with altitude_ft if the renderer... needs it; not required this phase").

**Frozen snapshot + lerp pattern to preserve** (lines 21-30, 42-51):
```python
class AircraftSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)
    x: float
    y: float
    heading_deg: float


def capture_state(aircraft: Aircraft) -> AircraftSnapshot:
    return AircraftSnapshot(x=aircraft.x, y=aircraft.y, heading_deg=aircraft.heading_deg)
```
If `x`/`y` become `x_nm`/`y_nm` in `Aircraft`, this snapshot and `interpolate()`'s field names must be renamed in lockstep — do not let `Aircraft` and `AircraftSnapshot` diverge in field naming (the existing 1:1 field mirroring is itself the convention to preserve).

---

### `src/atc_sim/render/radar.py` (evolved, D-05 taxi-visible dot)

**Analog:** itself — `RenderState` Protocol (lines 38-46).

**Duck-typed render-state seam to extend if needed:**
```python
class RenderState(Protocol):
    """Structural type for a frozen AircraftSnapshot — avoids a runtime
    import of atc_sim.sim.interpolation..."""
    x: float
    y: float
    heading_deg: float
```
Per RESEARCH.md's Architectural Responsibility Map, D-05's stationary-taxi-dot requires **zero new render logic** — `TAXI_OUT`/`TAXI_IN` simply hold `x_nm`/`y_nm` constant in the sim core; `draw_aircraft()` (lines 164-186) keeps drawing the dot at whatever `x`/`y` it's given, unchanged. Do not add phase-aware branching into `radar.py` this phase (only extend the `RenderState` Protocol with a `phase` field if/when Phase 4's datablock needs it — not now).

---

### `src/atc_sim/app.py` (evolved composition root)

**Analog:** itself.

**Call-site to replace** (lines 18-23, 31, 45-51):
```python
from atc_sim.sim.aircraft import Aircraft, sim_step
...
aircraft = Aircraft.spawn_default()
...
def on_tick(dt: float) -> None:
    nonlocal prev_state
    prev_state = capture_state(aircraft)
    sim_step(aircraft, dt)
    trail.append((aircraft.x, aircraft.y))
```
Per CONTEXT.md D-02 ("this is a call-site change, not just an addition"): replace the single `aircraft` variable with a list/collection populated by `demo_traffic.spawn_departure()`/`spawn_arrival()`, and replace the single `sim_step(aircraft, dt)` call with a loop over the collection plus a `demo_traffic.update_demo_traffic(...)` call for removal/respawn — preserving the exact "prev_state captured before mutation, inside on_tick, trail appended once per tick" discipline already documented in the module docstring (lines 1-12).

**Docstring convention to preserve:** app.py's header docstring explicitly states its own invariants ("only module that imports BOTH pygame and atc_sim.sim.*", "position mutation happens inside on_tick... never in the render section"). Update this docstring to mention the now-plural aircraft collection and demo-loop orchestration, keeping the same declarative-invariant style.

---

### Test files (new: `test_performance.py`, `test_phase.py`, `test_procedure.py`, `test_demo_traffic.py`)

**Analog:** `tests/test_navdata.py` (frozen-model validation + sourced-data-correctness assertions) and `tests/test_clock.py` (pure-function/deterministic-sequence assertions).

**Frozen-model rejection test pattern** (from `test_navdata.py` lines 33-46, 49-51):
```python
def test_runway_model_rejects_bad_fields():
    with pytest.raises(ValidationError):
        Runway(..., heading_deg_mag=400.0, ...)


def test_runway_model_is_frozen():
    with pytest.raises(ValidationError):
        EGGW_RUNWAY.identifier = "07"
```
Apply directly to `test_performance.py` for `PerformanceProfile` (bad climb rate ≤ 0, frozen-mutation rejection).

**Deterministic-sequence/pure-function test pattern** (from `test_clock.py` lines 11-31):
```python
def test_tick_count_independent_of_call_frequency():
    ...
    assert ticks_30fps == ticks_120fps
```
Apply to `test_phase.py` (legal/illegal transition table exhaustively checked) and `test_procedure.py` (the specific look-ahead regression test RESEARCH.md calls for: "a test that specifically exercises the DET STAR's LOFFO leg... asserts the target altitude is already descending toward ABBOT's FL080, not held at FL170" — RESEARCH.md line 440).

**Real-data-correctness test pattern** (from `test_navdata.py` lines 54-77, `test_det_2a_star_data`): `test_procedure.py` should assert `compute_target()` against the actual `OLNEY_2B_SID`/`DET_2A_STAR` fixtures imported from `navdata.eggw`, not synthetic procedures — matching this project's consistent "test against the real navdata, not a mock" convention.

## Shared Patterns

### "MUST NOT import pygame" headless module header
**Source:** `src/atc_sim/sim/aircraft.py` lines 13-15, `src/atc_sim/navdata/geo.py` lines 8-10, `src/atc_sim/navdata/models.py` lines 7-9, `src/atc_sim/sim/interpolation.py` lines 12-14
**Apply to:** all four new `sim/` modules (`performance.py`, `phase.py`, `procedure.py`, `demo_traffic.py`) — every existing sim-core/navdata module carries this exact sentence in its module docstring, and `tests/test_boundary.py` mechanically enforces it via `_iter_sim_python_files()`.
```python
"""...
This module MUST NOT import pygame — it stays headlessly testable via
pytest with no display, enforced by tests/test_boundary.py.
"""
```

### Frozen Pydantic v2 model for read-only reference data
**Source:** `src/atc_sim/navdata/models.py` (all classes), pattern also directly requested for `PerformanceProfile` in RESEARCH.md
**Apply to:** `performance.py::PerformanceProfile` and the `FLEET` dict of instances
```python
model_config = ConfigDict(frozen=True)
some_field: float = Field(gt=0.0)
```

### `validate_assignment=True` + `Field` bounds for live mutable state
**Source:** `src/atc_sim/sim/aircraft.py` line 26
**Apply to:** the evolved `Aircraft` model's new mutable fields (`phase`, `phase_elapsed_sec`, `altitude_ft`, `procedure_leg_index`, `speed_kt` if renamed from `speed_px_per_sec`)

### Compass convention: `heading_deg=0` is north, clockwise, `sin=x`/`cos=y`
**Source:** `src/atc_sim/sim/aircraft.py` line 48, `src/atc_sim/navdata/geo.py` lines 63-64, `src/atc_sim/render/radar.py` lines 79-87, 180-182
**Apply to:** every new kinematics/bearing computation in `procedure.py` and `aircraft.py` — this is the single most repeated invariant across the existing codebase and must not be reinvented with a different sign convention.

### True→magnetic conversion at exactly one boundary point
**Source:** `src/atc_sim/navdata/geo.py::true_to_magnetic()` lines 75-81
**Apply to:** `procedure.py::compute_target()` — any `atan2`-derived bearing must pass through this function exactly once before being stored as `Aircraft.heading_deg`. Previously-documented project pitfall (PITFALLS.md Pitfall 4); RESEARCH.md restates it as a named pitfall for this phase specifically.

### Reuse `navdata/geo.py` for all bearing/distance math — never reimplement
**Source:** `src/atc_sim/navdata/geo.py::true_bearing_and_distance_nm()`, `project_to_local_xy_nm()`
**Apply to:** `procedure.py` (fix bearing/distance for `compute_target()` and `advance_leg_if_reached()`) — do not add a second geodesic implementation.

### Dataclass (not Pydantic) for hot-path, recomputed-every-tick structs
**Source:** `.claude/CLAUDE.md` "Supporting Libraries" table (`dataclasses` row) — no existing in-repo dataclass yet, but this is an explicit, already-adopted project convention
**Apply to:** `procedure.py::Targets`

### Inline `# Phase N (reason): what changed and why` comment convention
**Source:** `src/atc_sim/sim/aircraft.py` lines 9-11, 53-55; `src/atc_sim/sim/interpolation.py` lines 43-46
**Apply to:** every modification to `aircraft.py`, `interpolation.py`, `app.py` this phase — document the change inline at the point of change, referencing the phase and specific pitfall/decision it addresses.

## No Analog Found

None — every file in this phase's scope has at least a role-match analog in the existing codebase or a complete worked example already supplied by RESEARCH.md's own code excerpts (which were themselves written to match this project's established conventions). The only genuinely novel *shape* (a hand-rolled FSM in `phase.py`) has no direct in-repo precedent but is fully specified by RESEARCH.md Pattern B and does not require external-pattern research.

## Metadata

**Analog search scope:** `src/atc_sim/sim/`, `src/atc_sim/navdata/`, `src/atc_sim/render/`, `src/atc_sim/app.py`, `tests/`
**Files scanned:** `aircraft.py`, `clock.py`, `interpolation.py`, `navdata/models.py`, `navdata/geo.py`, `navdata/eggw.py`, `render/radar.py`, `render/window.py` (not read in full — not relevant to this phase's new logic), `app.py`, `tests/test_navdata.py`, `tests/test_clock.py`, `tests/test_boundary.py`
**Pattern extraction date:** 2026-07-06
