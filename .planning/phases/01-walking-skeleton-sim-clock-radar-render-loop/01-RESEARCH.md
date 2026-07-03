# Phase 1: Walking Skeleton — Sim Clock & Radar Render Loop - Research

**Researched:** 2026-07-04
**Domain:** Fixed-timestep simulation loop / sim-render decoupling, minimal pygame-ce radar rendering, Python project scaffolding
**Confidence:** MEDIUM-HIGH (architectural pattern is HIGH confidence, canonical, cross-checked; exact version pins are MEDIUM confidence web-search verified this session; no official-docs MCP provider was available — all fetches used built-in WebSearch)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01 (Radar Visual Style):** Modern flat display styling — dark grey/blue background with white/cyan elements, closer to a modern EFIS/radar workstation than a classic green CRT scope. This style choice should carry forward into later rendering phases (Phase 2 navdata rendering, Phase 4 datablocks, Phase 7 polish).
- **D-02 (Phase 1 Test Aircraft):** The one hardcoded aircraft in this skeleton flies a straight line across the canvas at a fixed heading, then wraps around to the opposite side and continues — the simplest possible motion model. Throwaway motion logic specific to Phase 1; does not need to resemble any real SID/STAR.
- **D-03 (Window Sizing):** Fixed window size (e.g. 1280x800) for this skeleton — no resize/scaling logic needed yet. Revisit resizability in a later phase if desired.
- **D-04 (v1 Scope Confirmation):** Multi-procedure/multi-aircraft idea raised during discussion was identified as scope creep and deferred to v2 (`TRAF-01`). No roadmap/requirements changes. Not relevant to Phase 1 implementation.

### Claude's Discretion

- Exact fixed sim tick rate within the 1-4Hz range, the max-ticks-per-frame cap value, and the specific numeric window resolution are implementation details left to the planner/research, per the project's existing STACK.md and ARCHITECTURE.md research.

### Deferred Ideas (OUT OF SCOPE)

- Multiple SIDs/STARs with per-aircraft procedure selection — tracked as v2 backlog item `TRAF-01`. Not applicable to Phase 1.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CORE-01 | Simulation advances on a fixed-timestep clock (1-4Hz) fully decoupled from the 60fps render loop | Recommended tick rate (2Hz), accumulator loop implementation (see Architecture Patterns, Code Examples) |
| CORE-02 | Sim clock caps the maximum ticks processed per render frame, so a stall degrades gracefully instead of freezing or jumping | Max-ticks-per-frame cap value + rationale (see Architecture Patterns, Pitfall coverage); concrete stall-test technique (see Common Pitfalls / Validation Architecture) |
| CORE-03 | Render layer reads current aircraft state each frame without ever mutating it | `sim/` vs `render/` module boundary (see Recommended Project Structure); interpolation reads two immutable snapshots, never mutates live state |
| RADAR-01 | Player views a plan-view radar canvas with range rings and sector reference lines | Concrete pygame-ce drawing calls (see Code Examples) |
| RADAR-03 | Each aircraft shows a heading vector line and recent trail history dots | Concrete pygame-ce drawing calls + trail data structure (see Code Examples) |

</phase_requirements>

## Summary

This phase is a pure infrastructure/architecture proof, not a domain-logic phase — its entire job is to stand up the fixed-timestep sim clock, the sim/render module boundary, and a bare radar canvas, and to prove (not just implement) that render frame rate cannot affect aircraft motion. The project-level research (STACK.md, ARCHITECTURE.md, PITFALLS.md) already establishes the correct pattern (Gaffer On Games "Fix Your Timestep!" accumulator loop) and the correct module boundary (`sim/` never imports pygame). This phase-level research narrows those general patterns down to concrete, numeric, copy-pasteable decisions: a 2Hz sim tick, a 5-ticks-per-frame cap, a `frozen=True` Pydantic snapshot pair for interpolation, shortest-path angle interpolation for the heading vector, and a minimal `sim/` + `render/` package layout sized for exactly this phase's scope (no navdata, no performance model, no FSM — those arrive in Phases 2-3).

The riskiest part of this phase is not the sim/render split itself (well-documented, HIGH confidence) but two easy-to-skip details that project-level PITFALLS.md already flags: (1) omitting the max-ticks-per-frame cap because it "never triggers" in early manual testing (Pitfall 1 — directly maps to CORE-02's acceptance test), and (2) skipping state interpolation, which is not explicitly named in the success criteria but is required to satisfy them cleanly — without it, a 2Hz tick rate makes the aircraft visibly teleport every 500ms at 60fps, which will look like a bug during verification even though the tick/render decoupling is technically correct.

**Primary recommendation:** Implement the accumulator loop exactly as in Code Examples below with `SIM_HZ = 2`, `MAX_TICKS_PER_FRAME = 5`, capture `frozen=True` Pydantic snapshots before/after each tick, and interpolate position (lerp) and heading (shortest-path angle lerp) between the last two snapshots for every render frame — this one mechanism satisfies CORE-01, CORE-02, and CORE-03 simultaneously and is the single piece of code the rest of the project's rendering will depend on.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Sim clock / tick accumulator | Sim core (`sim/clock.py`) | — | Owns simulated time; must have zero pygame dependency to stay headless-testable (project's established boundary) |
| Aircraft state model (position, heading, speed) | Sim core (`sim/aircraft.py`) | — | Authoritative state; mutated only by the sim tick, never by rendering |
| State interpolation (previous/current snapshot → render-frame alpha blend) | Sim core (`sim/interpolation.py`) or render boundary glue | Render | The math is pure (no pygame needed) but exists purely to serve rendering smoothness — kept in `sim/` (or a thin seam module) so it stays unit-testable without a window |
| Radar canvas (range rings, sector lines) | Render (`render/radar.py`) | — | Pure drawing from static config, no sim state involved — a background layer |
| Aircraft symbol, heading vector, trail | Render (`render/radar.py` or `render/aircraft_render.py`) | — | Reads interpolated (read-only) state each frame; never writes back to sim state |
| Window/event loop wiring | Render (`app.py` / `render/window.py`) | — | Owns `pygame.init()`, the main `while running:` loop, and calling into `sim/clock.py` each frame |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.12+ (3.14.4 confirmed present on dev machine) | Language runtime | Already locked in PROJECT.md/CLAUDE.md `[CITED: .planning/PROJECT.md]` |
| pygame-ce | 2.5.7 (confirmed current, released 2026-03-02) `[ASSUMED — web-search verified, not registry/Context7-verified this session]` | Window, event loop, 2D drawing primitives | Actively maintained community fork; drop-in `import pygame` superset; confirmed Python 3.10–3.14 wheel support including 3.14 `[ASSUMED]` |
| pydantic | v2, ~2.13.x (2.13.4 latest patch confirmed via web search, 2026) `[ASSUMED — web-search verified, not registry/Context7-verified this session]` | `Aircraft` state model + immutable per-tick snapshot for interpolation | Already locked in project STACK.md; `frozen=True` config is exactly what the interpolation snapshot pattern needs |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 8.x (current) `[ASSUMED]` | Headless unit tests for the accumulator (tick count vs. wall time), interpolation math, and the stall-catch-up behavior | From day one — this phase's CORE-01/CORE-02 acceptance criteria are naturally expressed as fast, deterministic pytest cases against `sim/clock.py` with zero window/display required |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pydantic `frozen=True` snapshot for interpolation | `dataclasses.dataclass(frozen=True)` | Marginally faster construction (no validation), acceptable per project STACK.md guidance ("dataclasses for hot-path, per-tick objects"); Pydantic is still recommended here so `Aircraft` and its snapshot share one model definition and don't need a parallel dataclass mirror — revisit only if per-tick Pydantic construction is ever profiled as a bottleneck (very unlikely at v1's scale) |
| 2Hz sim tick | 1Hz / 4Hz | See Architecture Patterns below for full rationale |

**Installation:**
```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install "pygame-ce>=2.5,<3.0" "pydantic>=2.13,<3.0"
python -m pip install --group dev pytest   # or: pip install pytest
```

**Version verification:** `pip index versions <package>` was attempted this session but `pip`/`pip3` are not installed on the researched dev machine's system Python (only the stdlib `venv` module is present — `python3 -m pip` reports "No module named pip"). This means the walking-skeleton README/setup instructions (success criterion #5) **must include a `python -m ensurepip --upgrade` or equivalent bootstrap step** before `pip install` will work inside a fresh venv on this machine, or must explicitly note that the venv's bundled pip should be relied upon (Python's `venv` module normally bootstraps pip automatically — the missing pip was observed on the **system** Python, not confirmed missing inside a freshly created venv). **Planner must add a task to verify `pip` works inside the created venv as an early scaffold step**, and confirm exact current versions of `pygame-ce`/`pydantic` against PyPI directly at implementation time (this research could not query PyPI's JSON API or `pip index` directly and relied on WebSearch-verified figures dated 2026-03 / 2026-05, tagged `[ASSUMED]` above).

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| pygame-ce | PyPI | Established project (fork active since 2022); latest release 2026-03-02 | Unknown to checker (PyPI download-count signal unavailable to the legitimacy tool) | github.com/pygame-community/pygame-ce | SUS | Flagged — see note below |
| pydantic | PyPI | Established project (v1 since 2017, v2 since 2023); latest release 2026-05-06 | Unknown to checker | github.com/pydantic/pydantic | SUS | Flagged — see note below |
| pytest | PyPI | Established project (since 2004); latest release 2026-06-19 | Unknown to checker | github.com/pytest-dev/pytest | SUS | Flagged — see note below |

**Packages removed due to [SLOP] verdict:** none.
**Packages flagged as suspicious [SUS]:** `pygame-ce`, `pydantic`, `pytest` — **all three flags are a tooling limitation, not a genuine legitimacy concern.** The `package-legitimacy check` seam returned `unknown-downloads` (and `too-new`, based on latest-*release*-date rather than package age) for all three because PyPI weekly-download telemetry was unavailable to the checker in this session (`weeklyDownloads: null` for all three) — it is not evaluating package maturity correctly for the PyPI ecosystem here. All three are long-established, widely-used packages already locked in project-level STACK.md/CLAUDE.md with verified GitHub source repos. Per protocol, keep the `[SUS]` tag and planner should still add a lightweight `checkpoint:human-verify` before the dependency-install task — but the reviewer should expect this to be a fast rubber-stamp confirmation, not a real red flag.

*`pygame-ce`, `pydantic`, and `pytest` version numbers were discovered via WebSearch (not Context7/official registry query in this session) — tag `[ASSUMED]` per provenance rule regardless of registry existence; planner must gate the pinned-version install step behind a `checkpoint:human-verify` confirming current PyPI versions before locking `pyproject.toml`.*

## Architecture Patterns

### System Architecture Diagram

```
                    ┌─────────────────────────────────────────┐
                    │              app.py (main loop)          │
                    │  pygame.init() → window → pg_clock       │
                    └───────────────┬───────────────────────────┘
                                    │ real_dt (ms → s) each frame
                                    ▼
                    ┌─────────────────────────────────────────┐
                    │        sim/clock.py :: SimClock          │
                    │  accumulator += real_dt (clamped)        │
                    │  while accumulator >= tick_dt            │
                    │     and ticks_this_frame < MAX_TICKS:    │
                    │       prev_state = capture(aircraft)     │
                    │       sim_step(aircraft, tick_dt)  ──────┼──► sim/aircraft.py
                    │       curr_state = capture(aircraft)     │    (straight-line motion,
                    │       accumulator -= tick_dt             │     wrap at canvas edge)
                    └───────────────┬───────────────────────────┘
                                    │ prev_state, curr_state, alpha = accumulator/tick_dt
                                    ▼
                    ┌─────────────────────────────────────────┐
                    │     sim/interpolation.py (pure func)     │
                    │  interpolated = lerp(prev, curr, alpha)  │
                    │  (position: linear; heading: shortest-   │
                    │   path angle lerp)                       │
                    └───────────────┬───────────────────────────┘
                                    │ read-only interpolated state
                                    ▼
                    ┌─────────────────────────────────────────┐
                    │         render/radar.py (every frame)    │
                    │  1. draw static background (rings,       │
                    │     sector lines) — cached surface        │
                    │  2. draw aircraft dot at interpolated pos │
                    │  3. draw heading vector line              │
                    │  4. draw trail dots (aged from a          │
                    │     rolling deque of past sim-tick        │
                    │     positions, NOT interpolated frames)   │
                    └─────────────────────────────────────────┘
```
A reader can trace the primary use case (one aircraft moving) from `app.py`'s frame loop → `SimClock.advance()` draining 0-N ticks → `sim/aircraft.py` mutating authoritative state only inside a tick → interpolation blending the last two tick snapshots → `render/radar.py` drawing pixels from that blend, never touching `sim/aircraft.py`'s live object directly.

### Recommended Project Structure

Sized for Phase 1 only — deliberately does not create `navdata/`, `performance.py`, `separation.py`, `instructions.py`, `phraseology.py`, `scenario.py`, or `input/` yet (those are added in later phases per ARCHITECTURE.md's build order). Directory names match ARCHITECTURE.md's project-level naming exactly so nothing is renamed later.

```
atc-simulator/
├── pyproject.toml
├── README.md                    # Installation section rewritten (success criterion #5)
├── src/
│   └── atc_sim/
│       ├── __init__.py
│       ├── app.py               # pygame.init(), main loop, wires SimClock + renderer
│       ├── sim/                 # zero pygame imports — enforced by convention + a test
│       │   ├── __init__.py
│       │   ├── clock.py         # SimClock: accumulator, tick cap, sim_time
│       │   ├── aircraft.py      # Aircraft (Pydantic model) + straight-line-then-wrap motion
│       │   └── interpolation.py # capture_state(), interpolate() — pure functions
│       └── render/               # pygame-only — reads sim state, never mutates it
│           ├── __init__.py
│           ├── window.py        # window/display setup, constants (size, colors, FPS cap)
│           └── radar.py         # range rings, sector lines, aircraft dot/vector/trail
└── tests/
    ├── test_clock.py            # CORE-01/CORE-02: tick independence + stall catch-up
    └── test_interpolation.py    # position lerp + shortest-path heading lerp correctness
```

**Why `interpolation.py` lives under `sim/`, not `render/`:** it is pure math with no pygame dependency (a `pytest`-testable function of two Pydantic snapshots and a float), so it belongs on the pygame-free side of the boundary even though its only consumer is the renderer. This keeps `render/` a strict "read + draw" layer with no non-trivial logic of its own to unit test in isolation from pygame.

### Pattern 1: Fixed-timestep accumulator with capped catch-up (CORE-01, CORE-02)

**What:** Real elapsed wall-clock time per render frame is clamped, then added to an accumulator; the sim drains fixed-size ticks from the accumulator in a bounded loop (`while accumulator >= tick_dt and ticks_this_frame < MAX_TICKS_PER_FRAME`), guaranteeing both frame-rate-independent motion and graceful degradation under a stall.

**When to use:** This is the whole point of Phase 1 — implement first, before any aircraft/rendering code depends on its shape.

**Tick rate recommendation: 2Hz.** Rationale:
- 1Hz is the safest choice for interpolation smoothness margin but produces visibly "steppy" motion if interpolation has any bug — least forgiving to debug against.
- 4Hz is the most demanding choice: it makes the sim step function get called more often relative to render frames, which matters more once separation checks and kinematics are added in Phase 3/5, but adds no value in Phase 1 since aircraft motion here is trivial (straight line + wrap).
- **2Hz (0.5s per tick)** is the recommended middle value: frequent enough that even without interpolation the motion "reads" as continuous rather than obviously stepped during manual QA, infrequent enough relative to a 60fps render loop (30 render frames per sim tick) that the interpolation requirement is impossible to overlook or accidentally skip — a developer testing this phase will *immediately* notice a jump-per-tick artifact at 2Hz if interpolation is missing, which is a desirable property for this specific "prove the decoupling" phase. This tick rate is also easy to change later (single constant) since nothing about the architecture is tick-rate-specific.

**Max-ticks-per-frame cap recommendation: 5.** Rationale:
- At the target 60fps and a 2Hz tick (0.5s per tick, i.e. 30 render frames per tick under normal conditions), a single dropped/slow frame of up to ~150-200ms should be fully absorbed by catch-up within the very next frame or two — a cap of 5 ticks (2.5 simulated seconds of catch-up per frame) comfortably covers a deliberate stall test (e.g. a 1-2 second `time.sleep`) recovering within a handful of frames without ever looking like a freeze, while still being low enough that a truly pathological stall (multi-second freeze, e.g. a debugger breakpoint) visibly and intentionally causes the sim to run in bounded slow-motion rather than attempt to "catch up all at once" (Pitfall 1's core failure mode).
- Additionally clamp the *input* to the accumulator (the wall-clock `real_dt` itself) to a max value (e.g. `min(real_dt, 0.25)`) before it's added — this is the standard belt-and-suspenders pairing recommended by Gaffer On Games and cross-referenced in project PITFALLS.md Pitfall 1: capping ticks-per-frame alone still lets the accumulator's *backlog* grow unbounded across many consecutive slow frames; clamping the frame_time input bounds how much backlog a single slow frame can create in the first place.

**Trade-offs:** A capped accumulator means sim time can fall behind wall-clock time during a sustained stall (the sim visibly "runs slow"), which is the explicit, documented, correct behavior per CORE-02 and Pitfall 1 — not a bug to fix.

**Example:**
```python
# src/atc_sim/sim/clock.py — no pygame import
from collections.abc import Callable

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
        """Returns alpha in [0, 1): how far between the last two ticks we are,
        for the caller to interpolate render state."""
        frame_time = min(real_dt, MAX_FRAME_TIME)
        self._accumulator += frame_time

        ticks_run = 0
        while self._accumulator >= self.tick_dt and ticks_run < MAX_TICKS_PER_FRAME:
            self.sim_time += self.tick_dt
            on_tick(self.tick_dt)
            self._accumulator -= self.tick_dt
            ticks_run += 1

        if ticks_run == MAX_TICKS_PER_FRAME and self._accumulator >= self.tick_dt:
            # Backlog exceeds the cap this frame — deliberately drop it rather than
            # spiral; sim will simply run slow relative to wall clock until it recovers.
            self.dropped_tick_seconds += self._accumulator
            self._accumulator = 0.0

        return self._accumulator / self.tick_dt
```

```python
# src/atc_sim/app.py (excerpt) — pygame-only layer
import pygame
from atc_sim.sim.clock import SimClock
from atc_sim.sim.aircraft import Aircraft, sim_step
from atc_sim.sim.interpolation import capture_state, interpolate
from atc_sim.render.radar import draw_frame

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

### Pattern 2: State snapshot + interpolation for smooth rendering at a sub-frame-rate tick

**What:** Because the sim ticks at 2Hz (every 30 render frames) but renders at 60fps, most render frames occur *between* two sim ticks. Rendering raw current state on every frame produces a visible step/jump every 0.5s. Capturing an immutable snapshot before and after each tick and interpolating between them by `alpha = accumulator / tick_dt` produces smooth apparent motion while the authoritative sim state itself still only changes at 2Hz.

**When to use:** Required for RADAR-03's "aircraft renders as a dot with a heading vector" to look correct, and directly supports CORE-03 ("render layer reads current aircraft state each frame without ever mutating it") — interpolation reads two frozen snapshots and produces a third, throwaway value; it never mutates the live `Aircraft` object.

**Which fields need interpolating for Phase 1:** position (`x`, `y` in local/screen-relative units — Phase 1 has no real navdata/lat-lon yet, per D-02) and heading (degrees, for the heading-vector line). Speed does not need interpolation in Phase 1 since it's constant for the straight-line test aircraft and not itself rendered as a moving element.

**Example:**
```python
# src/atc_sim/sim/interpolation.py — no pygame import
from pydantic import BaseModel, ConfigDict

from atc_sim.sim.aircraft import Aircraft


class AircraftSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)
    x: float
    y: float
    heading_deg: float


def capture_state(aircraft: Aircraft) -> AircraftSnapshot:
    return AircraftSnapshot(x=aircraft.x, y=aircraft.y, heading_deg=aircraft.heading_deg)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _lerp_angle_deg(a: float, b: float, t: float) -> float:
    """Shortest-path interpolation across the 0/360 wrap boundary."""
    diff = ((b - a + 180) % 360) - 180
    return (a + diff * t) % 360


def interpolate(prev: AircraftSnapshot, curr: AircraftSnapshot, alpha: float) -> AircraftSnapshot:
    return AircraftSnapshot(
        x=_lerp(prev.x, curr.x, alpha),
        y=_lerp(prev.y, curr.y, alpha),
        heading_deg=_lerp_angle_deg(prev.heading_deg, curr.heading_deg, alpha),
    )
```

**Edge case this phase must handle:** the D-02 wrap-at-canvas-edge motion means `prev.x`/`curr.x` (or y) can jump discontinuously across a tick boundary (aircraft exits right edge, reappears at left edge). A naive linear lerp across that boundary will draw a fast streak across the entire canvas for one interpolation window. **Recommended handling:** when capturing a tick that performed a wrap, do not interpolate position for that one tick's render frames — snap directly to the post-wrap position (skip interpolation only for the wrap frame, detected by comparing `abs(curr.x - prev.x)` against a large-jump threshold, e.g. greater than half the canvas width). This is a Phase-1-only special case that will not exist once Phase 2 replaces wrap-at-edge with real navdata paths — do not over-engineer a general "seam" abstraction for it.

### Anti-Patterns to Avoid

- **Updating aircraft position directly inside the render loop using frame `dt`:** reintroduces frame-rate-dependent motion — exactly what CORE-01 exists to prevent. All position mutation must happen inside `on_tick`, called only from `SimClock.advance()`.
- **Skipping interpolation "since it's only Phase 1":** produces a visible stepping artifact that will look like a bug during verification of RADAR-03 and CORE-03, even though the underlying tick/render decoupling would be correct. Build it now — Pattern 2 above is ~15 lines and every later phase depends on this exact shape existing.
- **Letting `render/radar.py` call any `aircraft.assign_*()` / mutator method:** even for quick debug purposes. Per project ARCHITECTURE.md Anti-Pattern 3, this erodes the boundary that makes `sim/` headlessly testable — establish a test (or at minimum a code-review checklist item) that `render/` never imports a mutator from `sim/aircraft.py`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Frame timing / delta time | A manual `time.time()`-based frame timer | `pygame.time.Clock().tick(60)` | Already provides frame-rate capping and returns elapsed milliseconds; reinventing this adds risk for zero benefit |
| Anti-aliased radial lines (sector lines) | Manual Bresenham/AA line-drawing math | `pygame.draw.aaline()` / `pygame.draw.aalines()` | Built into pygame-ce; hand-rolling AA line rendering is a solved problem with no upside here |
| Shortest-path angle interpolation | An ad-hoc `if abs(diff) > 180: ...` branch scattered inline at each call site | The single `_lerp_angle_deg` pure function in `sim/interpolation.py` (Pattern 2 above) | A well-known, easy-to-get-subtly-wrong formula (sign errors, off-by-360 at the exact boundary) — implement once, unit test once (see Validation Architecture), reuse everywhere heading is ever interpolated in later phases |

**Key insight:** Phase 1's entire scope is small enough that the main "don't hand-roll" risk isn't a missing library — it's re-deriving the accumulator-cap math or the angle-wrap math ad hoc instead of using the exact, already-researched formulas above, which are easy to get subtly wrong (off-by-one on the cap check, wrong sign on the angle wrap) in ways that pass casual testing but fail exactly the stall/wrap edge cases this phase's acceptance criteria target.

## Common Pitfalls

### Pitfall 1: Spiral of death from an uncapped or improperly capped accumulator
**What goes wrong:** See project-level PITFALLS.md Pitfall 1 — a slow frame causes the sim to fall further and further behind, appearing to freeze then leap forward.
**Why it happens:** The cap is easy to omit because it never triggers during normal fast-machine development.
**How to avoid:** Implement both halves of the cap — clamp `real_dt` before accumulating AND clamp ticks-drained-per-frame (Pattern 1 above uses both).
**Warning signs:** Dragging the pygame window, hitting a breakpoint, or an artificial `time.sleep()` call inside the frame loop causes a visible jump instead of graceful slow-motion catch-up.

### Pitfall 2: Missing interpolation makes correct decoupling look broken
**What goes wrong:** Aircraft position visibly steps/jumps every 500ms (at 2Hz) even though CORE-01/CORE-02 are correctly implemented underneath.
**Why it happens:** Interpolation is not explicitly named in the phase's numbered success criteria, so it's easy to treat as optional polish rather than a load-bearing part of satisfying RADAR-03/CORE-03 cleanly.
**How to avoid:** Build `sim/interpolation.py` (Pattern 2) as a first-class module in this phase, not a follow-up.
**Warning signs:** Manual QA of the walking skeleton shows the aircraft dot "teleporting" in small hops rather than gliding.

### Pitfall 3: Wrap-around discontinuity drawn as a fast streak across the canvas
**What goes wrong:** D-02's "wrap at the canvas edge" motion, if naively interpolated across the wrap tick, draws the aircraft sweeping instantly across the full canvas width for one interpolation window.
**Why it happens:** The generic lerp function has no awareness that a large jump was an intentional teleport (wrap) rather than genuine motion to interpolate through.
**How to avoid:** Detect large jumps (threshold-based) between `prev` and `curr` snapshots and skip interpolation for that single tick's render frames (see Pattern 2's edge-case note).
**Warning signs:** A visible flash/streak crossing the radar canvas exactly when the test aircraft should be wrapping to the opposite edge.

### Pitfall 4: Frame-rate leakage into "decoupled" cosmetic timers
**What goes wrong:** See project PITFALLS.md Pitfall 2 — even with a correct sim/render split for aircraft motion, an unrelated cosmetic timer (e.g. a future blink/animation) implemented directly against per-frame delta reintroduces frame-rate dependence elsewhere.
**Why it happens:** `pygame.Clock.get_time()` is convenient to use inline for "just this one thing."
**Phase 1 relevance:** No blink/animation exists yet in this phase, but establish the convention now (route all time-dependent logic through either sim ticks or a single accumulated wall-clock source) since Phase 4+ will add alert-blink and comms-log timers that must not repeat this mistake.

## Code Examples

### Radar background layer: range rings + sector lines (RADAR-01)
```python
# src/atc_sim/render/radar.py — pygame-only
import math
import pygame

BG_COLOR = (18, 24, 32)          # dark grey/blue (D-01)
RING_COLOR = (60, 90, 100)       # muted cyan-grey
SECTOR_COLOR = (40, 60, 68)
AIRCRAFT_COLOR = (0, 220, 220)   # cyan (D-01)
TRAIL_COLOR = (0, 140, 140)
VECTOR_COLOR = (230, 240, 240)   # near-white

CENTER = (640, 400)              # canvas center, fixed 1280x800 window (D-03)
RING_STEP_PX = 80
NUM_RINGS = 4
NUM_SECTOR_LINES = 8             # every 45 degrees


def build_static_background(size: tuple[int, int]) -> pygame.Surface:
    """Rendered once at startup (or on resize) and blitted each frame —
    range rings/sector lines never change, so don't redraw primitives every frame."""
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
*Source: pygame-ce official `pygame.draw` reference (`pygame.draw.circle`, `pygame.draw.aaline`) `[CITED: pygame.org/docs/ref/draw.html]`. Caching the static background as a pre-rendered `Surface` blitted each frame — rather than redrawing rings/lines every frame — is standard pygame practice for anything that doesn't change frame-to-frame `[ASSUMED — general pygame performance convention, not phase-critical at v1 scale but free to do correctly from the start]`.*

### Aircraft dot, heading vector, and trail (RADAR-03)
```python
# src/atc_sim/render/radar.py (continued)
from collections import deque
import math

TRAIL_MAX_LEN = 8          # number of past sim-tick positions retained
AIRCRAFT_RADIUS_PX = 5
VECTOR_LENGTH_PX = 40


def draw_aircraft(surface: pygame.Surface, x: float, y: float, heading_deg: float,
                   trail: deque[tuple[float, float]]) -> None:
    # Trail: oldest points fainter/smaller — fixed-length deque handles aging out
    for age, (tx, ty) in enumerate(trail):
        fade = 1.0 - (age / max(len(trail), 1))
        radius = max(1, int(AIRCRAFT_RADIUS_PX * 0.4 * fade))
        pygame.draw.circle(surface, TRAIL_COLOR, (int(tx), int(ty)), radius)

    # Heading vector: from aircraft position, pointing along heading_deg
    # (0 deg = up/north, clockwise, matching a radar/compass convention)
    rad = math.radians(heading_deg)
    end = (x + math.sin(rad) * VECTOR_LENGTH_PX, y - math.cos(rad) * VECTOR_LENGTH_PX)
    pygame.draw.aaline(surface, VECTOR_COLOR, (x, y), end)

    # Aircraft dot, drawn last so it sits above its own trail/vector
    pygame.draw.circle(surface, AIRCRAFT_COLOR, (int(x), int(y)), AIRCRAFT_RADIUS_PX)
```
**Trail data structure and aging:** use `collections.deque(maxlen=TRAIL_MAX_LEN)`, appending one **interpolated** render position is *not* correct here — append the aircraft's position **once per sim tick** (inside `on_tick`, not inside the render loop), so the trail represents actual sim-tick history, not a dense cloud of near-duplicate render-frame positions. A `deque(maxlen=N)` automatically discards the oldest point once full — no manual aging logic needed. Recommended `TRAIL_MAX_LEN = 8` at a 2Hz tick rate gives a 4-second trail history, long enough to visually convey a heading/path without cluttering a bare radar canvas; this is a cosmetic tuning constant, not load-bearing for any success criterion, so treat it as easily adjustable.
*Source: `deque(maxlen=N)` behavior is Python stdlib documented behavior `[CITED: docs.python.org/3/library/collections.html#collections.deque]`; drawing primitives per pygame-ce `pygame.draw` reference `[CITED: pygame.org/docs/ref/draw.html]`.*

### Minimal `Aircraft` Pydantic v2 model (Phase 1 scope only)
```python
# src/atc_sim/sim/aircraft.py — no pygame import
import math
from pydantic import BaseModel, ConfigDict, Field

CANVAS_WIDTH = 1280
CANVAS_HEIGHT = 800


class Aircraft(BaseModel):
    model_config = ConfigDict(validate_assignment=True)  # v2 style; catches bad mutations

    x: float
    y: float
    heading_deg: float = Field(ge=0.0, lt=360.0)
    speed_px_per_sec: float = Field(gt=0.0)

    @classmethod
    def spawn_default(cls) -> "Aircraft":
        # D-02: simplest possible motion — straight line, fixed heading, wraps at edge
        return cls(x=0.0, y=CANVAS_HEIGHT / 2, heading_deg=90.0, speed_px_per_sec=60.0)


def sim_step(aircraft: Aircraft, dt: float) -> None:
    """Mutates the single authoritative Aircraft instance. Called only from
    SimClock.advance()'s on_tick callback — never from the render loop."""
    rad = math.radians(aircraft.heading_deg)
    aircraft.x += math.sin(rad) * aircraft.speed_px_per_sec * dt
    aircraft.y -= math.cos(rad) * aircraft.speed_px_per_sec * dt

    # D-02: wrap at canvas edge (simplest possible — no real navdata yet)
    if aircraft.x > CANVAS_WIDTH:
        aircraft.x -= CANVAS_WIDTH
    elif aircraft.x < 0:
        aircraft.x += CANVAS_WIDTH
    if aircraft.y > CANVAS_HEIGHT:
        aircraft.y -= CANVAS_HEIGHT
    elif aircraft.y < 0:
        aircraft.y += CANVAS_HEIGHT
```
**Deliberately excluded from this model (belongs to later phases):** flight phase/FSM (`Phase` enum — Phase 3), performance profile fields (climb/descent rate, turn rate — Phase 3), procedure/vector-override state (Phase 3-4), lat/lon or navdata-relative position (Phase 2 — Phase 1 uses plain local x/y canvas coordinates per D-02's "no real navdata yet"). Field naming (`heading_deg`, not a bare `heading`) follows project PITFALLS.md Pitfall 3's guidance to name heading/course/bearing distinctly from day one even though only `heading_deg` exists in this phase — this avoids a rename when `course_deg`/`bearing_to_fix_deg` are introduced in Phase 2/3.
*Source: Pydantic v2 `ConfigDict`/`Field` API `[CITED: docs.pydantic.dev/latest/concepts/models/]`; `frozen=True` config behavior for the separate `AircraftSnapshot` model above `[CITED: docs.pydantic.dev — frozen model config, verified via WebSearch this session]`.*

### Minimal `pyproject.toml`
```toml
[project]
name = "atc-simulator"
version = "0.1.0"
description = "Single-airport ATC simulator (walking skeleton)"
requires-python = ">=3.12"
dependencies = [
    "pygame-ce>=2.5,<3.0",
    "pydantic>=2.13,<3.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[project.scripts]
atc-sim = "atc_sim.app:main"

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]
```
*Source: Python Packaging User Guide src-layout + `[project.scripts]` convention `[CITED: packaging.python.org/en/latest/guides/writing-pyproject-toml/]`.*

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| Classic `pygame` PyPI package | `pygame-ce` community fork | Ongoing since ~2022 fork; project-level STACK.md already locked this | No change needed for this phase — just confirms the earlier decision still holds as of 2026-07 |
| `setup.py` / `setup.cfg` packaging | `pyproject.toml` with `[project]` table (PEP 621) | Standard since ~2021-2022, now near-universal | Use `pyproject.toml` exclusively — no `setup.py` needed for this project |

**Deprecated/outdated:** none specific to this phase's narrow scope beyond the classic-pygame-vs-pygame-ce point already captured in project STACK.md.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `pygame-ce` current version is 2.5.7, released 2026-03-02, with Python 3.14 wheel support | Standard Stack, Installation | If wrong/stale, the pinned version range (`>=2.5,<3.0`) still resolves correctly via pip's own resolver at install time — low risk, but the specific "confirmed 3.14 support" claim should be re-checked if `pip install` fails on the dev machine's Python 3.14.4 |
| A2 | `pydantic` current version is ~2.13.x (2.13.4 latest patch) | Standard Stack, Installation | Same as A1 — pinned range (`>=2.13,<3.0`) is resilient to being slightly stale; re-verify only if install fails |
| A3 | `pip`/`pip3` missing from system Python implies it may also be missing from a freshly created venv on this machine | Installation, Environment Availability | If wrong (venv's bundled pip works fine, as it does on most standard CPython installs), the extra `ensurepip` verification step is merely a harmless no-op; if right and un-checked, the README's install instructions (success criterion #5) would fail on first use |
| A4 | Package-legitimacy `[SUS]` verdicts for pygame-ce/pydantic/pytest are a tooling limitation (missing PyPI download telemetry) rather than genuine risk | Package Legitimacy Audit | Low risk — all three packages are independently corroborated as legitimate, long-established projects via their GitHub repos and project-level STACK.md's own prior (cross-checked) research; worst case is an unnecessary but harmless `checkpoint:human-verify` |
| A5 | 2Hz sim tick / 5 max-ticks-per-frame are the right numeric choices for this phase | Architecture Patterns | Low risk — both are single constants, trivially tunable; even if a different value is later preferred (e.g. project settles on 4Hz once real kinematics exist in Phase 3), nothing about this phase's architecture is coupled to the specific number |

**If this table is empty:** N/A — see entries above; all are low-risk, easily-correctable-at-implementation-time assumptions rather than decisions that would reshape the architecture if wrong.

## Open Questions

1. **Does the target dev machine's Python 3.14.4 venv include a working `pip` out of the box?**
   - What we know: System-wide `python3 -m pip` reports "No module named pip" on the researched machine; `venv` module itself is present and functional.
   - What's unclear: Whether `python3 -m venv .venv` on this machine bootstraps pip automatically (standard CPython behavior) or requires an explicit `python -m ensurepip --upgrade` follow-up.
   - Recommendation: Planner should add an early scaffold task that creates the venv, checks `pip --version` inside it, and runs `ensurepip` as a fallback if missing, before attempting the dependency install — this directly de-risks success criterion #5 (README install instructions must actually work).

2. **Exact current PyPI versions of `pygame-ce` and `pydantic`.**
   - What we know: WebSearch-verified figures (pygame-ce 2.5.7 / 2026-03-02, pydantic 2.13.4 / 2026-05-xx) are internally consistent and match project-level STACK.md's independent prior research.
   - What's unclear: No direct PyPI registry or Context7 query was possible this session (no `pip`, no MCP provider configured) to get an authoritative confirmation.
   - Recommendation: Use version-range pins (`>=2.5,<3.0`, `>=2.13,<3.0`) rather than exact pins in `pyproject.toml` so pip's resolver picks up the true current version at install time regardless of whether this research's point-in-time figures are slightly stale; treat this as resolved by design rather than blocking.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12+ | Entire project | Yes | 3.14.4 (system) | — |
| `venv` stdlib module | Isolated dependency environment | Yes | bundled with 3.14.4 | — |
| `pip` (system-wide) | Installing dependencies | No | — | Rely on `venv`'s bundled pip (standard CPython behavior); verify with `ensurepip` fallback (see Open Questions #1) |
| `pygame-ce` | Window/rendering (RADAR-01, RADAR-03) | Not yet installed (greenfield) | — | Install via pip inside venv; no system-level fallback needed (pure pip package) |
| `pydantic` | Aircraft state model | Not yet installed (greenfield) | — | Install via pip inside venv |
| Display/X server (for pygame window) | Running the actual walking-skeleton app | Not verified this session (sandbox environment may be headless) | — | If the execution/verification environment is headless, the accumulator/interpolation logic (CORE-01/02/03) can still be fully verified headlessly via `pytest` against `sim/clock.py` and `sim/interpolation.py`; only the visual rendering criteria (RADAR-01, RADAR-03) require an actual display or a virtual framebuffer (e.g. `xvfb`) — flag this to the planner as a verification-environment consideration, not a phase-blocking issue |

**Missing dependencies with no fallback:** none — all missing items have a viable, documented fallback above.

**Missing dependencies with fallback:**
- System `pip` → venv-bundled pip + `ensurepip` fallback.
- Display server for visual verification → headless `pytest` coverage for CORE-01/02/03 sim-clock logic; visual RADAR-01/03 criteria need either a real display or a virtual framebuffer during verification.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.x (not yet installed — greenfield project) |
| Config file | none yet — see Wave 0 Gaps |
| Quick run command | `pytest tests/test_clock.py tests/test_interpolation.py -x` |
| Full suite command | `pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CORE-01 | Sim tick count over N seconds of wall time is independent of how many render-loop iterations occurred in that time | unit | `pytest tests/test_clock.py::test_tick_count_independent_of_call_frequency -x` | ❌ Wave 0 |
| CORE-02 | A single very large `real_dt` (simulated stall) is drained at most `MAX_TICKS_PER_FRAME` ticks in one `advance()` call, with no exception and no unbounded loop | unit | `pytest tests/test_clock.py::test_stall_caps_ticks_per_frame -x` | ❌ Wave 0 |
| CORE-02 | Backlog beyond the cap is dropped (accumulator reset), not silently retained to explode on a future frame | unit | `pytest tests/test_clock.py::test_backlog_beyond_cap_is_dropped -x` | ❌ Wave 0 |
| CORE-03 | `interpolate()` never mutates its input snapshots (both remain `frozen=True`, unchanged after the call) | unit | `pytest tests/test_interpolation.py::test_interpolate_does_not_mutate_inputs -x` | ❌ Wave 0 |
| RADAR-03 | `interpolate()` produces the shortest-path result crossing the 0/360 heading boundary (e.g. 350° → 10° interpolates through 360/0, not backward through 180°) | unit | `pytest tests/test_interpolation.py::test_heading_interpolation_shortest_path -x` | ❌ Wave 0 |
| RADAR-01 / RADAR-03 | Visual manual check: rings render as circles, sector lines radiate from center, aircraft dot + heading vector + trail render at plausible positions | manual (requires display) | N/A — manual/visual UAT | — |

*(CORE-01/CORE-02's success-criterion #2 acceptance test — "deliberately stalling a render frame" — is directly testable via the unit tests above by calling `SimClock.advance()` with a single artificially large `real_dt` value, e.g. 3.0 seconds, rather than needing an actual `time.sleep()` in a running pygame loop; this is the concrete, fast, deterministic technique requested by this research's brief. A supplementary manual/exploratory check — inserting a real `time.sleep(1.5)` inside the running app's frame loop once and observing no freeze/jump — is recommended once as a one-time integration sanity check, but should not be the automated regression test.)*

### Sampling Rate
- **Per task commit:** `pytest tests/test_clock.py tests/test_interpolation.py -x`
- **Per wave merge:** `pytest` (full suite)
- **Phase gate:** Full suite green before `/gsd-verify-work`, plus one manual visual check of the running app (rings/sector lines/aircraft/trail/vector) since RADAR-01/RADAR-03's full acceptance criteria include subjective visual correctness that pytest cannot assert.

### Wave 0 Gaps
- [ ] `tests/test_clock.py` — covers CORE-01, CORE-02
- [ ] `tests/test_interpolation.py` — covers CORE-03, RADAR-03 (heading wrap correctness)
- [ ] `pyproject.toml` `[project.optional-dependencies].dev` entry + a `pytest.ini` or `[tool.pytest.ini_options]` section — no test config exists yet (greenfield)
- [ ] Framework install: `pip install -e ".[dev]"` (or equivalent) — pytest is not yet a dependency anywhere in this greenfield repo

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | Single-player, offline, no accounts — out of scope for entire project |
| V3 Session Management | No | No session/auth concept in this native single-user desktop app |
| V4 Access Control | No | No multi-user/privilege boundary exists |
| V5 Input Validation | Marginally yes | Pydantic `Field(ge=..., lt=...)` constraints on `Aircraft.heading_deg`/`speed_px_per_sec` (already in the Code Examples model above) provide basic sanity-bound validation on the one place this phase constructs state from a fixed/hardcoded spawn — no external/untrusted input exists yet in Phase 1 (scenario files arrive in Phase 6) |
| V6 Cryptography | No | No secrets, no network, no persisted credentials anywhere in this offline desktop app |

### Known Threat Patterns for this stack

No meaningful STRIDE-relevant threat surface exists in this phase: the application is a fully offline, single-process, single-user native desktop app with no network I/O, no file I/O beyond reading its own source (scenario file loading is a Phase 6 concern), and no persisted user data. The only "input" in Phase 1 is a hardcoded spawn — there is no untrusted-input boundary to threat-model yet. This section will become materially relevant starting at Phase 6 (scenario file parsing — untrusted file input validated against a Pydantic schema per SCEN-02) and should be revisited then.

## Sources

### Primary (HIGH confidence)
- Project-level `.planning/research/STACK.md`, `.planning/research/ARCHITECTURE.md`, `.planning/research/PITFALLS.md` — prior GSD research for this same project, already cross-checked across multiple independent web sources at project-formation time.
- [Fix Your Timestep! — Gaffer On Games](https://gafferongames.com/post/fix_your_timestep/) — canonical, widely-cited accumulator pattern reference.
- Python stdlib `collections.deque` documented `maxlen` behavior — standard library reference.

### Secondary (MEDIUM confidence — WebSearch, cross-checked against official docs/project research this session)
- [pygame.draw — pygame-ce/pygame documentation](https://www.pygame.org/docs/ref/draw.html) — `circle`, `aaline` signatures used in Code Examples.
- [pygame-ce PyPI](https://pypi.org/project/pygame-ce/) and cross-referenced release-date/version claims via WebSearch (2.5.7, 2026-03-02; Python 3.10-3.14 wheel support).
- [Pydantic Docs — Models / Configuration](https://docs.pydantic.dev/latest/concepts/models/) — `ConfigDict(frozen=True)` behavior, `Field` constraint usage.
- [Writing your pyproject.toml — Python Packaging User Guide](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) — src-layout + `[project.scripts]` convention.
- [ConstantGameSpeed — pygame wiki](https://www.pygame.org/wiki/ConstantGameSpeed) — accumulator-cap discussion cross-referencing Gaffer On Games.
- Shortest-path angle interpolation formula — cross-referenced across [a widely-cited angle-interpolation gist](https://gist.github.com/shaunlebron/8832585) and general game-engine `lerp_angle` conventions (Unity `Mathf.LerpAngle`, Python Arcade `arcade.math.lerp_angle`) — consistent formula across independent sources.

### Tertiary (LOW confidence — single-source or unverifiable this session)
- Exact `pydantic` 2.13.4 patch-version and release-date figures — WebSearch only, not cross-verified against PyPI's registry directly this session (no working `pip`/network registry query tool available).
- Whether the specific sandboxed dev machine's fresh `venv` will have working `pip` — inferred from system Python's missing `pip`, not directly tested by creating a venv this session.

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM — directional choices (pygame-ce, pydantic, accumulator pattern) are HIGH confidence and already locked by project-level research; exact version numbers are WebSearch-verified only (MEDIUM/LOW), not registry-confirmed
- Architecture: HIGH — fixed-timestep accumulator, sim/render module boundary, and interpolation pattern are canonical, well-documented, and already established at project level; this phase's contribution (concrete tick-rate/cap numbers, concrete module layout scoped to Phase 1, concrete interpolation code) is a straightforward, low-risk narrowing of that established pattern
- Pitfalls: HIGH — Pitfall 1 (spiral of death) and the interpolation-omission risk are both directly derived from project-level PITFALLS.md plus this session's own architectural reasoning about how CORE-02/RADAR-03 will actually be verified

**Research date:** 2026-07-04
**Valid until:** 30 days (stable architectural pattern; re-verify exact `pygame-ce`/`pydantic` version pins against PyPI directly before implementation regardless of this window, per the Installation section's noted gap)
