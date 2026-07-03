# Architecture Research

**Domain:** Single-airport ATC / flight simulator (native Python + Pygame desktop app)
**Researched:** 2026-07-03
**Confidence:** MEDIUM (general game-loop/FSM/STCA patterns are well-established, HIGH-confidence knowledge; ATC-simulator-specific structure is synthesized from general flight-sim domain knowledge plus LOW-confidence web sources — no direct source-code read of a reference ATC sim was possible in this session)

## Standard Architecture

### System Overview

```
┌───────────────────────────────────────────────────────────────────────┐
│                         INPUT / INSTRUCTION LAYER                     │
│  ┌──────────────┐   ┌───────────────────┐   ┌──────────────────────┐  │
│  │ Mouse picking │   │ Command panel     │   │ Instruction validator│  │
│  │ (select a/c)  │   │ (heading/alt/spd) │   │ (legal state check)  │  │
│  └──────┬───────┘   └─────────┬─────────┘   └──────────┬───────────┘  │
├─────────┴─────────────────────┴─────────────────────────┴─────────────┤
│                         SIM CORE (fixed-tick, no rendering)            │
│  ┌────────────┐  ┌──────────────┐  ┌───────────────┐  ┌────────────┐  │
│  │ Sim clock  │→ │ Aircraft     │→ │ Navdata /      │  │ Separation │  │
│  │ (1-4Hz     │  │ state model  │↔ │ procedure store│  │ / conflict │  │
│  │ accumulator│  │ (FSM + kine- │  │ (fixes, SID,   │  │ detector   │  │
│  │ pattern)   │  │ matics)      │  │ STAR, ILS)     │  │ (per tick) │  │
│  └────────────┘  └──────┬───────┘  └────────────────┘  └─────┬──────┘  │
│                         │                                     │        │
│                         ▼                                     ▼        │
│                  ┌───────────────┐                    ┌───────────────┐│
│                  │ Phraseology / │                    │ Alert/STCA    ││
│                  │ readback gen  │                    │ state (flag   ││
│                  └───────────────┘                    │ on aircraft)  ││
├─────────────────────────────────────────────────────────────────────┤
│                     PRESENTATION LAYER (variable-rate, 60fps)         │
│  ┌──────────────┐  ┌────────────────┐  ┌───────────────────────────┐ │
│  │ Radar canvas │  │ Datablock /    │  │ Comms/phraseology log,    │ │
│  │ (rings, a/c, │  │ trail renderer │  │ conflict alert banner     │ │
│  │ vectors)     │  │                │  │                           │ │
│  └──────────────┘  └────────────────┘  └───────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────┘
```

The critical structural rule: **the sim core never imports Pygame, and the rendering layer never mutates aircraft state.** Data flows one direction into rendering (state → pixels) and one direction into the sim (instructions → state changes applied at the next tick, not immediately). This boundary is what lets you build/test separation logic and navdata with zero graphics code running (e.g. in a `pytest` suite that runs the sim clock headless).

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| Sim clock / tick engine | Owns simulated time; advances world state at a fixed rate independent of frame rate | Accumulator pattern: real elapsed time is banked each frame, fixed-size sim steps are drained from the bank (`while accumulator >= dt: step(); accumulator -= dt`). Simulated seconds-per-tick can run faster/slower than wall-clock (time acceleration is trivial — just scale what you deposit into the accumulator) |
| Aircraft state/behavior model | Owns each aircraft's authoritative state: position (lat/lon or local xy), altitude, heading, IAS/groundspeed, assigned instructions, flight-phase, on-procedure vs vectored flag | A dataclass/Pydantic model holding state + a small FSM (phase) + a kinematics update method called once per tick by the sim clock. Not "smart" — it exposes `assign_heading()`, `assign_altitude()`, etc. that just set target values; the kinematics step moves current values toward targets each tick (turn rate, climb rate limits applied here) |
| Navdata/procedure store | Owns static reference data: airport, runway, fixes, SID/STAR definitions, ILS parameters | Loaded once at startup from hand-authored data files (YAML/JSON/Python dict) into Pydantic models; treated as read-only during a session. Aircraft reference it by ID/name, never copy or mutate it |
| Radar rendering layer | Reads aircraft state + navdata each render frame and draws pixels; owns screen/world coordinate transform | Pure read-only consumer. Runs at display refresh rate (60fps), completely decoupled from sim tick rate. Converts lat/lon or local nm coordinates to screen pixels via a projection function; draws range rings, sector lines, aircraft symbol + datablock + vector line + trail dots from a rolling position history |
| Input/instruction handling | Translates mouse/panel events into validated instruction objects applied to the targeted aircraft | Two-stage: (1) UI event → "intent" (e.g. `HeadingInstruction(aircraft_id, 270)`), (2) intent validated against current aircraft state/phase (can't assign a landing runway to an aircraft mid-climb) and queued; applied at the start of the next sim tick, not mid-frame |
| Separation/conflict detector (STCA) | Each tick, checks all aircraft pairs for horizontal/vertical separation infringement (current and optionally short-horizon predicted) | A standalone function called once per sim tick (not per render frame): naive O(n²) pairwise loop over aircraft, computing great-circle/planar distance + altitude delta; sets an `alert=True` flag + which aircraft are involved. At this project's scale (single digits of aircraft) this is computationally free — no spatial partitioning needed |
| Phraseology/readback generator | Converts an issued instruction + aircraft state into controller phrasing text and a simulated pilot readback string | A templating function keyed on instruction type: `"{callsign}, turn left heading {hdg}"` → simulated readback `"{turn} left heading {hdg}, {callsign}"`. Purely textual, has no effect on state — it observes the instruction that was just applied |
| Scenario loader | Reads a scripted scenario file and spawns aircraft into the sim at the right sim-time with the right initial state/flight plan | Parsed once at load time into a sorted list of "spawn events" keyed by sim-time; the sim clock checks this queue each tick and instantiates aircraft when their spawn time arrives |

## Recommended Project Structure

```
src/atc_sim/
├── sim/                    # Sim core — no pygame import allowed here
│   ├── clock.py            # Fixed-tick accumulator, sim-time, time acceleration
│   ├── aircraft.py         # Aircraft state model + kinematics update + flight-phase FSM
│   ├── performance.py      # Per-type performance profiles (climb/descent rate, speed envelope, turn rate)
│   ├── separation.py       # STCA-style pairwise conflict detector
│   ├── instructions.py     # Instruction dataclasses + validation + application to aircraft
│   ├── phraseology.py      # Instruction -> controller/pilot text generation
│   └── scenario.py         # Scenario file parsing + spawn-event queue
├── navdata/                # Static reference data + loader — no pygame import
│   ├── models.py           # Pydantic models: Runway, Fix, Procedure (SID/STAR), ILS
│   ├── eggw.py (or .yaml)  # Hand-authored EGGW navdata: runway 26, fixes, one SID, one STAR
│   └── geo.py              # geographiclib/pyproj wrappers: distance, bearing, projection
├── render/                 # Pygame-only layer — reads sim/navdata, never mutates them
│   ├── window.py           # Pygame window setup, render-loop (variable rate)
│   ├── radar.py            # Range rings, sector lines, coordinate projection
│   ├── datablock.py        # Aircraft symbol, datablock, vector line, trail
│   └── ui_panels.py        # Command panel, comms log, alert banner (pygame_gui or hand-rolled)
├── input/                  # Translates pygame events into instruction intents
│   └── controller_input.py # Mouse picking (hit-test aircraft), panel event -> Instruction
└── app.py                  # Wires clock, aircraft list, navdata, renderer, input together
```

### Structure Rationale

- **`sim/` has zero Pygame imports.** This is the single most important boundary in this codebase: it lets you write and run separation-logic and flight-phase tests with plain `pytest`, at full sim-tick speed, with no window open. Given the project's stated bar ("the sim never lies about separation"), separation logic needs to be testable in isolation from day one.
- **`navdata/` is also Pygame-free and read-only at runtime.** Splitting it from `sim/` reflects the real distinction between "facts about the world" (fixes, procedures, ILS geometry — loaded once, never mutated) and "state of the world" (aircraft positions — mutated every tick). Procedures reference fixes by name/ID; aircraft reference procedures by name/ID. Nothing owns a deep copy.
- **`render/` only reads.** No file under `render/` should ever call `aircraft.assign_heading()` or similar. If the renderer needs derived data (e.g. "is this aircraft in conflict"), it reads a flag that `separation.py` already set on the aircraft object during the last sim tick — it does not recompute conflict state itself.
- **`input/` is the only place instruction intents are created**, and they are queued, not applied synchronously — this avoids the classic "instruction mutated state mid-frame while renderer was iterating aircraft" bug class.

## Architectural Patterns

### Pattern 1: Fixed-timestep sim clock decoupled from render loop (accumulator pattern)

**What:** The render loop runs as fast as Pygame/the display allows (typically capped at 60fps via `clock.tick(60)`); the sim update runs at a fixed rate (e.g. 1–4Hz, i.e. every 0.25–1.0 simulated seconds per tick) regardless of render framerate. A time accumulator bridges the two: each render frame, real elapsed time (`dt`) is added to the accumulator; while the accumulator holds at least one sim-tick's worth of time, a sim step is executed and that amount is subtracted.

**When to use:** Always, for this project — it's the standard fix for the two failure modes of naively updating physics in the render loop: (1) frame-rate-dependent behavior (aircraft move faster on a faster machine), and (2) instability from large/variable `dt` values feeding into kinematics integration. It's also what makes time acceleration (a common ATC-sim feature — speeding up quiet periods) trivial to add later: just scale what's deposited into the accumulator per frame.

**Trade-offs:** Slight added complexity (an accumulator plus a "how many steps to run this frame" loop) versus updating aircraft directly each render frame. Worth it immediately — retrofitting this after aircraft kinematics exist is more painful than starting with it.

**Example:**
```python
# sim/clock.py
class SimClock:
    def __init__(self, tick_hz: float = 2.0):
        self.tick_dt = 1.0 / tick_hz   # simulated seconds per sim step
        self._accumulator = 0.0
        self.sim_time = 0.0
        self.time_scale = 1.0          # >1.0 for time acceleration

    def advance(self, real_dt: float, on_tick):
        """real_dt: wall-clock seconds since last render frame."""
        self._accumulator += real_dt * self.time_scale
        while self._accumulator >= self.tick_dt:
            self.sim_time += self.tick_dt
            on_tick(self.tick_dt)      # runs one sim step: aircraft update, separation check
            self._accumulator -= self.tick_dt

# app.py main loop
pg_clock = pygame.time.Clock()
while running:
    real_dt = pg_clock.tick(60) / 1000.0   # render at up to 60fps
    sim_clock.advance(real_dt, sim_step)   # 0, 1, or several sim ticks happen here
    render(aircraft_list, navdata)          # always renders current state, every frame
```

### Pattern 2: Explicit finite-state machine for flight phase, hand-rolled or `transitions`-backed

**What:** Model each aircraft's flight phase (`PUSHBACK`, `TAXI_OUT`, `DEPARTURE_ROLL`, `CLIMB`, `ENROUTE`, `DESCENT`, `APPROACH`, `LOCALIZER_CAPTURED`, `GLIDESLOPE_CAPTURED`, `LANDED`, `TAXI_IN`) as an explicit enum-driven state machine with defined legal transitions, rather than inferring phase from raw altitude/speed thresholds scattered through the code.

**When to use:** Immediately — flight phase gates almost everything else (which instructions are legal, how kinematics behave, what the renderer's datablock shows, what phraseology applies). This project's phase list is short and mostly linear (no go-arounds, no VFR pattern branches in scope), which makes it a good fit for a *simple hand-rolled* FSM rather than pulling in `pytransitions/transitions` as a dependency.

**Trade-offs:** `transitions` (pytransitions) is the standard, well-maintained Python FSM library — lightweight, adds `on_enter_<state>`/`on_exit_<state>` callback hooks automatically, and is a reasonable choice if the state graph grows (e.g. when VFR/go-arounds are added in v2). For v1's short, mostly-linear phase list, a hand-rolled `Enum` + a `dict[Phase, set[Phase]]` legal-transitions table plus a plain `transition_to()` method is fewer moving parts, has zero dependency risk, and is trivial to unit test. Recommendation: **start hand-rolled**, migrate to `transitions` only if/when the VFR milestone introduces branching states (circuit legs, go-around recovery) that make a hand-rolled table unwieldy.

**Example:**
```python
# sim/aircraft.py
class Phase(Enum):
    PUSHBACK = auto(); TAXI_OUT = auto(); DEPARTURE_ROLL = auto()
    CLIMB = auto(); ENROUTE = auto(); DESCENT = auto()
    APPROACH = auto(); LOC_CAPTURED = auto(); GS_CAPTURED = auto()
    LANDED = auto(); TAXI_IN = auto()

LEGAL_TRANSITIONS: dict[Phase, set[Phase]] = {
    Phase.PUSHBACK: {Phase.TAXI_OUT},
    Phase.TAXI_OUT: {Phase.DEPARTURE_ROLL},
    Phase.DEPARTURE_ROLL: {Phase.CLIMB},
    Phase.CLIMB: {Phase.ENROUTE},
    Phase.ENROUTE: {Phase.DESCENT},
    Phase.DESCENT: {Phase.APPROACH},
    Phase.APPROACH: {Phase.LOC_CAPTURED},
    Phase.LOC_CAPTURED: {Phase.GS_CAPTURED},
    Phase.GS_CAPTURED: {Phase.LANDED},
    Phase.LANDED: {Phase.TAXI_IN},
}

class Aircraft:
    def transition_to(self, new_phase: Phase):
        if new_phase not in LEGAL_TRANSITIONS[self.phase]:
            raise ValueError(f"Illegal transition {self.phase} -> {new_phase}")
        self.phase = new_phase
```

### Pattern 3: Procedure-following with a vectoring override layer (not a replacement)

**What:** An aircraft on a SID/STAR tracks a `procedure_leg_index` pointing at its next fix in an ordered `Procedure.legs` list, and its kinematics target (desired heading/altitude/speed) is normally *derived* from "fly direct to `legs[leg_index].fix`, obey its restrictions." When the controller issues a vector (heading/altitude/speed instruction), it sets an explicit override that *replaces* the derived target until the controller clears it (e.g. "direct to fix" or "resume own navigation" re-engages procedure following).

**When to use:** This is the standard way flight-sim/ATC-sim software reconciles "fly the SID" with "vectors" without two incompatible code paths: procedure-following and vectoring both ultimately just produce the same three numbers (target heading, target altitude, target speed) that the kinematics step consumes every tick. The kinematics/turn-rate/climb-rate code is completely agnostic to *where* the target came from.

**Trade-offs:** Requires a small piece of state per aircraft (`on_procedure: bool`, `procedure_leg_index: int`, `vector_override: VectorOverride | None`) but avoids duplicating movement logic between "vectored" and "on procedure" aircraft — a common source of divergent bugs in naive implementations that hard-code separate movement branches per mode.

**Example:**
```python
def compute_target(aircraft: Aircraft) -> Targets:
    if aircraft.vector_override is not None:
        return aircraft.vector_override.as_targets()   # heading/alt/speed set by controller
    leg = aircraft.procedure.legs[aircraft.procedure_leg_index]
    return Targets(
        heading=bearing_to(aircraft.position, leg.fix.position),
        altitude=leg.altitude_restriction or aircraft.altitude,  # hold last if none
        speed=leg.speed_restriction or aircraft.speed,
    )
```

## Data Flow

### Instruction → State → Render Flow

```
[Mouse click on aircraft symbol]  [Panel: "Heading 270" button]
              │                              │
              ▼                              ▼
      input/controller_input.py  →  Instruction(aircraft_id, HEADING, 270)
              │
              ▼
      sim/instructions.py  →  validate against aircraft.phase (queued for next tick)
              │
              ▼  (at next sim tick, sim clock calls sim_step())
      Instruction applied → aircraft.vector_override = HeadingOverride(270)
              │                                             │
              ▼                                             ▼
      sim/phraseology.py generates readback text     sim/aircraft.py kinematics step:
              │                                       turns aircraft toward 270 at its
              ▼                                       type's turn-rate limit, this tick
      Comms log panel (render layer, read-only)             │
                                                              ▼
                                                    aircraft.heading, .position updated
                                                              │
                                                              ▼
                                        sim/separation.py checks all pairs this tick,
                                        sets aircraft.conflict_flag if minima infringed
                                                              │
                                                              ▼
                              render/radar.py (next render frame, reads current state)
                              draws aircraft at new position/heading, red datablock if
                              conflict_flag is set, alert banner if any conflict exists
```

### Key Data Flows

1. **Instruction application is tick-gated, not immediate.** An instruction issued between sim ticks is queued and applied atomically at the start of the next tick. This guarantees the renderer never observes a half-applied instruction mid-frame, and guarantees separation checks always see fully-consistent, post-instruction state.
2. **Rendering is a pure function of current state, run every frame regardless of whether a sim tick occurred that frame.** Because sim ticks (1-4Hz) are slower than render frames (60fps), most render frames redraw the same state — this is fine and expected. (Optional later polish: interpolate aircraft position between the last two sim ticks for smoother motion at low tick rates; not needed for v1.)
3. **Separation checking runs once per sim tick, after all aircraft kinematics for that tick have been applied**, never per render frame — it's a sim-core concern, invisible to the renderer except via the flag it sets.
4. **Navdata flows one direction: loaded once at startup, read by both the sim core (for procedure-following) and the renderer (for drawing fixes/procedures), never written to during a session.**

## Scaling Considerations

Given the project's explicit scope (single airport, one runway direction, a handful of concurrent aircraft, scripted deterministic scenarios), classic "scaling" concerns (thousands of entities, distributed simulation) do not apply. The relevant scaling axis here is "aircraft count per session," not "users."

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1-10 aircraft (v1 scope) | Naive O(n²) pairwise separation check every tick; single-threaded sim + render in one process. This is computationally free at 1-4Hz tick rate — no optimization needed |
| 10-30 aircraft (plausible v2/busy-scenario ceiling) | Still fine with O(n²) pairwise checks at this tick rate (a few hundred comparisons per tick, at most a few Hz) — do not add spatial partitioning pre-emptively |
| 30+ aircraft (unlikely in this project's scope) | Only then would a spatial grid/bucket (partition airspace into cells, only compare aircraft in nearby cells) be worth the added complexity — real-world ATC systems use R-trees/octrees at this scale, but that's solving a problem this project does not have |

### Scaling Priorities

1. **There is no first bottleneck at this project's scope.** The realistic risk is not performance but *complexity creep in the separation/procedure logic itself* (e.g. handling every edge case of vectoring-vs-procedure state cleanly). Optimize for code clarity and testability, not throughput.
2. If a future milestone (VFR traffic, multiple runways) meaningfully increases aircraft count, revisit the separation detector first — but the fix is a spatial bucket on top of the same pairwise check function, not a rewrite.

## Anti-Patterns

### Anti-Pattern 1: Coupling sim update to render frame rate

**What people do:** Update aircraft position/kinematics directly inside the Pygame render loop using the render frame's `dt`, without a fixed-tick sim clock.
**Why it's wrong:** Aircraft behavior becomes frame-rate-dependent (turns faster on a faster machine), separation logic becomes nondeterministic run-to-run (breaks the project's explicit goal of debuggable, repeatable scripted scenarios), and adding time-acceleration later requires a rewrite.
**Do this instead:** Fixed-timestep accumulator pattern (Pattern 1 above) from day one, even in the walking-skeleton phase.

### Anti-Pattern 2: Encoding flight phase implicitly via altitude/speed thresholds scattered through the codebase

**What people do:** Instead of an explicit `Phase` field, infer "is this aircraft climbing/descending/on approach" ad hoc from `if altitude < 3000 and distance_to_runway < 10: ...` checks duplicated in the renderer, the instruction validator, and the kinematics step.
**Why it's wrong:** These conditions drift out of sync across the codebase as the project grows; it becomes unclear what instructions are legal in what state, and debugging "why did this aircraft not respond to my instruction" requires re-deriving phase from raw numbers.
**Do this instead:** One explicit `Phase` enum field per aircraft (Pattern 2), transitioned through an explicit legal-transitions table, read everywhere else that needs to know phase.

### Anti-Pattern 3: Renderer reaching into and mutating sim state ("just this once")

**What people do:** For convenience, have a render/UI function directly set `aircraft.heading = clicked_value` instead of going through the instruction queue, especially for quick debug/dev shortcuts.
**Why it's wrong:** Breaks the tick-gating guarantee (Key Data Flow #1), makes separation-logic bugs hard to reproduce (state changed at an arbitrary point in the frame, not atomically at tick boundaries), and erodes the sim-core/render boundary that makes headless testing possible.
**Do this instead:** Every state mutation goes through `sim/instructions.py`, even ones triggered directly by a debug key — keep exactly one path into aircraft state changes.

### Anti-Pattern 4: Premature spatial-partitioning for separation checks

**What people do:** Reach for a k-d tree, R-tree, or spatial hash grid for conflict detection because "that's what real ATC systems use."
**Why it's wrong:** At this project's scale (single digits to low tens of aircraft, 1-4Hz tick rate), a naive O(n²) pairwise loop is a handful of microseconds of work per tick. Spatial partitioning adds real implementation and maintenance complexity (cell sizing, edge cases at cell boundaries) to solve a performance problem that does not exist here.
**Do this instead:** Naive pairwise separation check (see Pattern in `sim/separation.py` responsibility above); revisit only if profiling ever shows it as a bottleneck, which is very unlikely to happen at this project's scope.

## Integration Points

### External Services

None. This is an entirely offline, native desktop application with hand-authored navdata (explicitly out of scope: live AIRAC ingestion, multiplayer, voice). There is no network integration surface in v1.

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `input/` → `sim/instructions.py` | Instruction dataclasses, queued | Input layer never mutates aircraft directly; it only ever produces validated-or-rejected instruction intents |
| `sim/instructions.py` → `sim/aircraft.py` | Direct method calls at tick boundary (`aircraft.assign_heading(...)`) | Applied exactly once per sim tick, at tick start, before kinematics/separation run for that tick |
| `sim/aircraft.py` ↔ `navdata/models.py` | Read-only reference (aircraft holds a reference to its assigned `Procedure`/`Runway`/`ILS` objects) | Navdata objects are never copied or mutated by aircraft; procedure-following reads restrictions off shared navdata objects |
| `sim/aircraft.py` → `sim/separation.py` | Separation detector reads a list of live aircraft state each tick | One-way read; writes back only a `conflict_flag`/`conflict_with` field onto the aircraft objects it checked |
| `sim/*` → `render/*` | Render layer reads aircraft list + navdata each frame | Strictly read-only from render's side; this is the boundary that must never be violated (see Anti-Pattern 3) |
| `sim/scenario.py` → `sim/clock.py` | Scenario loader's spawn-event queue is checked each tick by the sim clock, which instantiates new `Aircraft` objects | Scenario file is parsed once at load; spawn events are consumed in sim-time order, not real-time order (so time acceleration doesn't skip spawns) |

## Suggested Build Order (Walking Skeleton → Full System)

Rationale drawn from Alistair Cockburn's Walking Skeleton pattern: build the thinnest end-to-end slice through every layer first, then grow via vertical slices, tackling the riskiest/most foundational integration earliest rather than last.

1. **Walking skeleton: sim clock + one hardcoded aircraft + radar canvas.** A single `Aircraft` with a fixed straight-line path (no real navdata, no kinematics beyond linear motion), driven by the fixed-tick sim clock, rendered on a bare radar canvas (just a dot, maybe a heading vector). This proves the hardest structural risk first — the sim-clock/render-loop decoupling and the "state flows one way into rendering" boundary — before any domain complexity exists. Rendering absolutely can and should be stubbed here; it does not need real navdata, real aircraft performance, or real coordinates (a flat local x/y plane is fine).
2. **Real navdata + coordinate projection.** Introduce `navdata/` (EGGW runway 26, fixes, lat/lon → screen projection via geographiclib/pyproj) and re-point the skeleton's aircraft path at real fixes. This is a natural next step because the renderer already exists and now just needs real geometry to draw; it doesn't yet need procedures or performance modeling.
3. **Aircraft performance model + flight-phase FSM.** Replace the placeholder linear motion with per-type performance profiles (climb/descent rate, speed envelope, turn rate) and the explicit `Phase` state machine. At this point aircraft can plausibly taxi/depart/climb/descend/land along a hardcoded procedure, still with no player input.
4. **Procedure-following (SID/STAR) with restrictions.** Wire the one SID and one STAR into the performance model via the "derive target from procedure leg" pattern (Pattern 3). This is naturally sequenced after step 3 because procedure-following needs a working kinematics/phase model to act on.
5. **Instruction handling (click + panel) with the vectoring override layer.** Only now does the player get control: heading/altitude/speed/direct-to/cleared-approach/cleared-for-takeoff-landing instructions, applied via the tick-gated instruction queue, overriding procedure-following per Pattern 3. This is sequenced after procedures because vectoring is defined as an override *on top of* procedure state — building it first would mean revisiting it once procedures exist anyway.
6. **Separation detection (STCA-style alerting).** Add the pairwise conflict detector once there are at least two independently-controllable aircraft to conflict with each other (requires steps 3-5 to produce two aircraft whose paths can plausibly cross). This is deliberately sequenced after instruction handling, not before, since testing separation logic is far more meaningful once a human can actually create a conflict via instructions rather than only via the scenario file.
7. **Scenario loader (scripted multi-aircraft spawns).** Formalize scenario authoring last among the core systems, once single-aircraft behavior, instructions, and separation are all proven — the scenario file is "just" a way to spawn more of what already works, in a controlled/repeatable time-ordered sequence.
8. **Phraseology/readback generation.** Layer the text log on top of the already-working instruction-application pipeline; it is purely observational (Key Data Flow, step: "Instruction applied" branch) and has zero effect on simulation state, so it is safe and low-risk to add last among the functional pieces.
9. **Polish**: datablocks, trails, alert banner styling, UI panel layout refinement — cosmetic/UX layer on top of an already-functioning sim core.

This order front-loads the two riskiest architectural bets (fixed-tick/render decoupling, and the procedure-vs-vector override reconciliation) exactly as the Walking Skeleton pattern recommends, and defers the lowest-risk, most "additive" pieces (phraseology text, visual polish) to the end.

## Sources

- [Fix Your Timestep! — Gaffer On Games](https://gafferongames.com/post/fix_your_timestep/) — MEDIUM (well-known, widely cited canonical reference for the accumulator pattern; corroborated by pygame wiki)
- [ConstantGameSpeed — pygame wiki](https://www.pygame.org/wiki/ConstantGameSpeed) — MEDIUM (official pygame community wiki)
- [Game Loop — Game Programming Patterns](https://gameprogrammingpatterns.com/game-loop.html) — MEDIUM (widely-used reference text on game architecture patterns)
- [pytransitions/transitions — GitHub](https://github.com/pytransitions/transitions) — MEDIUM (official repo for the standard Python FSM library)
- [Short-term conflict alert — Wikipedia](https://en.wikipedia.org/wiki/Short-term_conflict_alert) — LOW-MEDIUM (general encyclopedic source, cross-referenced conceptually with SKYbrary)
- [Short Term Conflict Alert (STCA) — SKYbrary Aviation Safety](https://skybrary.aero/articles/short-term-conflict-alert-stca) — MEDIUM (SKYbrary is an aviation-safety industry reference maintained by EUROCONTROL/industry partners)
- [Instrument landing system localizer — Wikipedia](https://en.wikipedia.org/wiki/Instrument_landing_system_localizer) — LOW-MEDIUM (general reference, standard ILS capture description consistent with pilot-training sources)
- [openScope — GitHub](https://github.com/openscope/openscope) — LOW (fetch did not expose internal file-tree/class detail; treated directionally only, not as a verified architectural reference)
- [Creating a Walking Skeleton — InfoQ / Alistair Cockburn's Walking Skeleton pattern](https://www.infoq.com/presentations/Walking-Skeleton/) — MEDIUM (standard, widely-cited software architecture pattern)
- [entity-component-system topic — GitHub](https://github.com/topics/entity-component-system?l=python) — LOW (general ecosystem survey, used only to justify *not* adopting full ECS for this project's scale)
- General domain knowledge of ATC-simulator and flight-simulator architecture (openScope, VATSIM/EuroScope-style ATC clients, X-Plane/MSFS-style autopilot capture logic) — used to synthesize patterns where direct web sourcing was LOW-confidence or unavailable; flagged inline above wherever a claim rests primarily on this rather than a citable source.

**Confidence caveat:** No MCP research providers (context7/exa) were available in this session; all findings were gathered via the built-in WebSearch/WebFetch tools, which the confidence-classification seam rates LOW by default. The general software-architecture patterns here (fixed timestep, FSM, walking skeleton, STCA concept, ILS capture sequencing) are well-established and cross-referenced across multiple independent sources, raising practical confidence to MEDIUM despite the LOW per-source tier. ATC-simulator-specific internal code structure (e.g. openScope's actual class design) could not be verified at source-code level and should be treated as directional inspiration, not a confirmed reference implementation.

---
*Architecture research for: single-airport ATC/flight simulator (Python + Pygame)*
*Researched: 2026-07-03*
