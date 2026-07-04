# Phase 1: Walking Skeleton — Sim Clock & Radar Render Loop - Pattern Map

**Mapped:** 2026-07-04
**Files analyzed:** 11 (new)
**Analogs found:** 0 / 11 — greenfield project, no source code exists yet

## Greenfield Notice

`git -C /home/toby/ATC-simulator ls-files` confirms the only tracked files are `.claude/CLAUDE.md`, `.planning/**` (planning docs, research cache, requirements, roadmap), and `README.md`. There is **no `src/`, no `tests/`, no `pyproject.toml`, no existing Python code anywhere in the repository.**

Because there is nothing to find an analog in, this PATTERNS.md does not attempt to point the planner at existing codebase files. Instead, it treats **RESEARCH.md's Code Examples section as the canonical pattern source** for this phase — these are the first patterns the project establishes, and every later phase's `sim/`, `render/`, and test-file patterns will be analogs of *these* Phase 1 files. The planner should copy the concrete code in RESEARCH.md directly (already phase-specific, already reconciled with CONTEXT.md's locked decisions D-01/D-02/D-03) rather than expect a codebase search to surface anything new.

## File Classification

| New File | Role | Data Flow | Closest Analog | Match Quality |
|----------|------|-----------|-----------------|---------------|
| `pyproject.toml` | config | — | none | no analog (greenfield) |
| `README.md` (installation section rewrite) | config/docs | — | none | no analog (greenfield) |
| `src/atc_sim/__init__.py` | config | — | none | no analog (greenfield) |
| `src/atc_sim/app.py` | controller (main loop / composition root) | event-driven (pygame event loop) + orchestration | none | no analog (greenfield) |
| `src/atc_sim/sim/clock.py` | service (sim core) | event-driven (accumulator/tick loop) | none | no analog (greenfield) |
| `src/atc_sim/sim/aircraft.py` | model | CRUD (mutate-in-place per tick) | none | no analog (greenfield) |
| `src/atc_sim/sim/interpolation.py` | utility (pure transform) | transform | none | no analog (greenfield) |
| `src/atc_sim/render/window.py` | config/provider (window + constants) | — | none | no analog (greenfield) |
| `src/atc_sim/render/radar.py` | component (pygame drawing) | request-response (draw-per-frame, reads state) | none | no analog (greenfield) |
| `tests/test_clock.py` | test | — | none | no analog (greenfield) |
| `tests/test_interpolation.py` | test | — | none | no analog (greenfield) |

## Pattern Assignments

All patterns below are sourced from `.planning/phases/01-walking-skeleton-sim-clock-radar-render-loop/01-RESEARCH.md` (project-authored research, not third-party code), since no in-repo analog exists. File paths/line ranges refer to RESEARCH.md itself.

### `src/atc_sim/sim/clock.py` (service, event-driven accumulator)

**Source:** RESEARCH.md lines 196-233 ("Pattern 1: Fixed-timestep accumulator with capped catch-up")

Copy this exactly as the starting point — it is the single riskiest piece of code in the phase (CORE-01/CORE-02):

```python
SIM_HZ = 2.0
TICK_DT = 1.0 / SIM_HZ          # 0.5 simulated seconds per tick
MAX_FRAME_TIME = 0.25           # clamp wall-clock dt fed into the accumulator
MAX_TICKS_PER_FRAME = 5         # hard cap on catch-up ticks drained in one frame


class SimClock:
    def __init__(self, tick_dt: float = TICK_DT) -> None:
        self.tick_dt = tick_dt
        self._accumulator = 0.0
        self.sim_time = 0.0
        self.dropped_tick_seconds = 0.0   # visibility counter, log/expose during dev

    def advance(self, real_dt: float, on_tick: Callable[[float], None]) -> float:
        frame_time = min(real_dt, MAX_FRAME_TIME)
        self._accumulator += frame_time

        ticks_run = 0
        while self._accumulator >= self.tick_dt and ticks_run < MAX_TICKS_PER_FRAME:
            self.sim_time += self.tick_dt
            on_tick(self.tick_dt)
            self._accumulator -= self.tick_dt
            ticks_run += 1

        if ticks_run == MAX_TICKS_PER_FRAME and self._accumulator >= self.tick_dt:
            self.dropped_tick_seconds += self._accumulator
            self._accumulator = 0.0

        return self._accumulator / self.tick_dt
```

**Constraint (hard boundary, enforce by convention + test):** this module must have **zero `import pygame`** anywhere — it must remain headlessly testable via pytest with no display. This is the single most important architectural rule for the whole project going forward (per `.planning/research/ARCHITECTURE.md`).

### `src/atc_sim/sim/aircraft.py` (model, CRUD/mutate-per-tick)

**Source:** RESEARCH.md lines 437-476

```python
class Aircraft(BaseModel):
    model_config = ConfigDict(validate_assignment=True)  # v2 style; catches bad mutations

    x: float
    y: float
    heading_deg: float = Field(ge=0.0, lt=360.0)
    speed_px_per_sec: float = Field(gt=0.0)

    @classmethod
    def spawn_default(cls) -> "Aircraft":
        return cls(x=0.0, y=CANVAS_HEIGHT / 2, heading_deg=90.0, speed_px_per_sec=60.0)


def sim_step(aircraft: Aircraft, dt: float) -> None:
    """Mutates the single authoritative Aircraft instance. Called only from
    SimClock.advance()'s on_tick callback — never from the render loop."""
    rad = math.radians(aircraft.heading_deg)
    aircraft.x += math.sin(rad) * aircraft.speed_px_per_sec * dt
    aircraft.y -= math.cos(rad) * aircraft.speed_px_per_sec * dt
    # wrap at canvas edge (D-02)
    ...
```

**Naming convention to lock in now:** use `heading_deg` (not bare `heading`) — later phases add `course_deg`/`bearing_to_fix_deg` and this avoids a rename (per project PITFALLS.md Pitfall 3). This model must also have zero pygame imports.

### `src/atc_sim/sim/interpolation.py` (utility, pure transform)

**Source:** RESEARCH.md lines 284-317 ("Pattern 2: State snapshot + interpolation")

```python
class AircraftSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)
    x: float
    y: float
    heading_deg: float


def capture_state(aircraft: Aircraft) -> AircraftSnapshot: ...

def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t

def _lerp_angle_deg(a: float, b: float, t: float) -> float:
    """Shortest-path interpolation across the 0/360 wrap boundary."""
    diff = ((b - a + 180) % 360) - 180
    return (a + diff * t) % 360

def interpolate(prev, curr, alpha) -> AircraftSnapshot: ...
```

**Edge case to build in from the start (Pitfall 3):** detect large position jumps between `prev`/`curr` (wrap-at-edge, D-02) and skip interpolation for that tick's render frames rather than lerping across the wrap — snap to `curr` instead. Threshold suggestion: `abs(curr.x - prev.x) > CANVAS_WIDTH / 2`.

### `src/atc_sim/app.py` (controller / composition root, event-driven main loop)

**Source:** RESEARCH.md lines 236-272

```python
def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((1280, 800))
    pg_clock = pygame.time.Clock()
    sim_clock = SimClock()
    aircraft = Aircraft.spawn_default()

    prev_state = capture_state(aircraft)
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        real_dt = pg_clock.tick(60) / 1000.0

        def on_tick(dt: float) -> None:
            nonlocal prev_state
            prev_state = capture_state(aircraft)
            sim_step(aircraft, dt)

        alpha = sim_clock.advance(real_dt, on_tick)
        curr_state = capture_state(aircraft)
        render_state = interpolate(prev_state, curr_state, alpha)

        draw_frame(screen, render_state)
        pygame.display.flip()

    pygame.quit()
```

This is the only file allowed to both import pygame AND drive the sim clock — it is the seam between the two halves of the architecture.

### `src/atc_sim/render/radar.py` (component, request-response draw-per-frame)

**Source:** RESEARCH.md lines 365-433 (two code blocks: static background, aircraft/trail/vector)

Key excerpts to copy:
- `build_static_background()` — pre-renders range rings + sector lines to a cached `Surface` once at startup, blitted (not redrawn) each frame.
- `draw_aircraft()` — draws trail dots (fading with age) → heading vector (`pygame.draw.aaline`) → aircraft dot on top, in that z-order.
- Color constants matching D-01 (dark grey/blue bg, cyan/white elements): `BG_COLOR = (18, 24, 32)`, `AIRCRAFT_COLOR = (0, 220, 220)`, `VECTOR_COLOR = (230, 240, 240)`.
- Trail data structure: `collections.deque(maxlen=TRAIL_MAX_LEN)`, appended **once per sim tick inside `on_tick`**, not once per render frame — this is a load-bearing distinction, not a style choice.

**Hard rule for this file (and any future `render/*`):** never import or call a mutator from `sim/aircraft.py`. `render/` reads interpolated snapshots only.

### `tests/test_clock.py` / `tests/test_interpolation.py` (test)

**Source:** RESEARCH.md "Validation Architecture" section, lines 556-589

Required test cases (drives CORE-01/02/03, RADAR-03):
- `test_tick_count_independent_of_call_frequency` — same total wall time, different frame-call patterns, same tick count.
- `test_stall_caps_ticks_per_frame` — single large `real_dt` (e.g. 3.0s) drains at most `MAX_TICKS_PER_FRAME` ticks, no exception, no infinite loop.
- `test_backlog_beyond_cap_is_dropped` — accumulator resets to 0 after a capped stall rather than retaining backlog.
- `test_interpolate_does_not_mutate_inputs` — both `AircraftSnapshot` inputs unchanged after `interpolate()` (relies on `frozen=True`).
- `test_heading_interpolation_shortest_path` — e.g. 350° → 10° interpolates through 0/360, not backward through 180°.

No pygame/display dependency needed for any of these — pure `SimClock`/`interpolation` unit tests.

## Shared Patterns

### Sim/render boundary (the one pattern everything else depends on)
**Source:** RESEARCH.md "System Architecture Diagram" + "Anti-Patterns to Avoid", lines 106-148, 321-325
**Apply to:** every file in `sim/` and `render/`
- `sim/*.py` — zero `import pygame`, ever. Enforceable later by a simple grep-based test.
- `render/*.py` — read-only access to interpolated/frozen state; never calls a `sim/aircraft.py` mutator (not even for debug convenience).
- All position mutation happens inside `on_tick`, called only from `SimClock.advance()` — never inside the render loop using frame `dt`.

### Pydantic v2 conventions
**Source:** `.claude/CLAUDE.md` "Pydantic modeling pattern" section + RESEARCH.md lines 445-477, 290-299
**Apply to:** `sim/aircraft.py`, `sim/interpolation.py`
- `model_config = ConfigDict(...)` (v2 style), never v1 `class Config:`.
- Live/mutable state (`Aircraft`) uses `validate_assignment=True`; per-tick snapshots (`AircraftSnapshot`) use `frozen=True`.
- Field-level bounds (`Field(ge=..., lt=...)`) at the one place state is constructed (`spawn_default`) — this project's only Phase 1 "input validation" boundary.

### Color/visual style (D-01, carries forward to later phases)
**Source:** RESEARCH.md lines 370-376
**Apply to:** all of `render/radar.py`, and referenced by future Phase 2/4/7 rendering work
```python
BG_COLOR = (18, 24, 32)          # dark grey/blue
RING_COLOR = (60, 90, 100)
SECTOR_COLOR = (40, 60, 68)
AIRCRAFT_COLOR = (0, 220, 220)   # cyan
TRAIL_COLOR = (0, 140, 140)
VECTOR_COLOR = (230, 240, 240)   # near-white
```

## No Analog Found

All 11 files — this is a greenfield repository. See Greenfield Notice above; RESEARCH.md Code Examples substitute for analogs for this phase only. From Phase 2 onward, these Phase 1 files (`sim/clock.py`, `sim/aircraft.py`, `sim/interpolation.py`, `render/radar.py`) become the real analogs for the pattern-mapper to point to.

## Metadata

**Analog search scope:** entire repository (`git ls-files`) — confirmed no `src/`, `tests/`, or `pyproject.toml` exist yet.
**Files scanned:** all tracked files (43, all planning docs / research cache / README / CLAUDE.md — no source).
**Pattern extraction date:** 2026-07-04
</content>
</invoke>
