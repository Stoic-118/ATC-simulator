# Phase 3: Aircraft Performance, Flight-Phase FSM & Procedure Following - Research

**Researched:** 2026-07-06
**Domain:** Simplified aircraft performance modeling, hand-rolled flight-phase state machine, SID/STAR procedure-following (Python/Pydantic, headless sim core)
**Confidence:** MEDIUM (architecture/FSM/procedure-following design is HIGH-confidence synthesis of already-established project patterns; per-aircraft-type numeric performance values are LOW-MEDIUM confidence web-sourced approximations, explicitly simplified/adapted for this project, not authoritative BADA-grade data)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01 (Aircraft Fleet):** Which 3-5 real aircraft types to model is left to the Phase 3 researcher to pick during research — the user does not have specific types locked in. The researcher should choose a realistic, well-documented mix with clear performance-envelope spread (e.g. narrowbody jet vs. turboprop/GA), sourcing simplified (not BADA-table) climb/descent rate, speed envelope, and turn-rate data for each. **(This research fulfills D-01 — see "Standard Stack: Aircraft Fleet" below.)**
- **D-02 (Demo Harness):** This phase's autonomous departure/arrival loop is demonstrated by two hardcoded aircraft spawned when the app starts — one departure aircraft (spawns at a stand, taxis, takes off, climbs out via the OLNEY 2B SID's legs/restrictions) and one arrival aircraft (spawns airborne at the DET 2A STAR entry fix with a realistic initial altitude/speed, flies the STAR's legs/restrictions toward the airport). This replaces Phase 1/2's single placeholder aircraft entirely — it is not additive to it.
- **D-03 (Removal & Looping):** Once the departure aircraft passes the SID's final/exit fix, it is removed from active traffic (mirrors the arrival's removal after landing + taxi-in, per success criterion #5). Once both the departure and arrival aircraft have been removed, the demo loops — a fresh departure/arrival pair spawns automatically — so the app keeps demonstrating the full loop without needing a restart.
- **D-04 (Visual Differentiation):** Aircraft types are differentiated by behavior only (visibly different climb/descent rate, speed, and turn rate during flight) — no new visual symbol system this phase.
- **D-05 (Taxi Visibility):** During the abstracted timer-based taxi (pushback/taxi-out before departure roll, and taxi-in after landing), the aircraft renders as a stationary dot at a stand/gate position — it does not disappear or stay hidden during taxi.

### Claude's Discretion

- Exact stand/gate coordinate(s) used for the taxi-visible departure spawn and arrival taxi-in position — pick a plausible position near the apron/terminal area relative to the runway 25 threshold; does not need to be sourced from a real published stand chart.
- Exact numeric performance profile values (climb rate, descent rate, speed envelope, turn rate per bank angle/groundspeed) for each chosen aircraft type — per PITFALLS.md Pitfall 7 guidance (avoid decoupling that produces numerically-correct-but-experientially-wrong behavior; some coupling between altitude/speed/configuration should exist even in a simplified v1 model).
- Flight-Phase enum exact membership and legal-transitions table — per ARCHITECTURE.md Pattern 2 (hand-rolled `Enum` + legal-transitions `dict`, not the `transitions` library).
- Procedure-following mechanism (leg-index tracking, restriction application) — per ARCHITECTURE.md's Pattern 3, building the `compute_target()` seam now even though the vectoring-override side doesn't exist until Phase 4.
- Timer duration(s) for the taxi abstraction are an implementation detail, not a user vision decision.

### Deferred Ideas (OUT OF SCOPE)

- **Distinct visual symbols per aircraft type** (different dot size/shape on radar) — explicitly deferred; behavioral differentiation is sufficient this phase.
- **Scripted, file-driven traffic** — the two-hardcoded-aircraft demo harness (D-02) is a stand-in for the real scenario loader (Phase 6, SCEN-01/02). No scenario-file work happens in this phase.
- **ILS localizer/glideslope capture logic, vectoring override, click/panel instructions** — all explicitly Phase 4 (PROC-02, PROC-03, INST-01/02/03). This phase must not build real localizer/glideslope capture-angle math; see Common Pitfalls below for how APPROACH should be simplified instead.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PERF-01 | Each aircraft uses a simplified per-type performance profile (climb/descent rate, speed envelope, turn rate as f(bank, groundspeed)), drawn from a fleet of 3-5 types | "Standard Stack: Aircraft Fleet" gives 4 sourced/simplified types with a shared turn-rate formula; "Architecture Patterns: Pattern A" gives the `PerformanceProfile` model + kinematics design |
| PERF-02 | Aircraft flight phase modeled as an explicit state machine | "Architecture Patterns: Pattern B" gives the exact 8-state enum + legal-transitions table matching the roadmap's success-criterion wording |
| PERF-03 | Departure aircraft spawn at a stand, taxi via timer abstraction, take off, climb via the SID | "Architecture Patterns: Pattern C" (taxi/departure-roll/landing/taxi-in abstractions) + "Code Examples" |
| PERF-04 | Arrival aircraft spawn airborne at STAR entry fix with realistic initial altitude/speed, descend, taxi in after landing | "Standard Stack" (DET fix's real FL170 restriction as spawn altitude) + "Architecture Patterns: Pattern C" |
| PROC-01 | Aircraft cleared via SID/STAR follow procedure legs and restrictions automatically | "Architecture Patterns: Pattern D" (`compute_target()` seam, leg-sequencing, restriction look-ahead) |

</phase_requirements>

## Summary

This phase has no new external dependencies — it is pure Python/Pydantic domain logic layered onto the existing `atc_sim.sim` and `atc_sim.navdata` packages built in Phases 1-2. The three technical problems (performance modeling, flight-phase FSM, procedure-following) are all already scoped architecturally by the project's own prior research (`ARCHITECTURE.md` Patterns 2-3, `PITFALLS.md` Pitfall 7) — this research fills in the concrete gaps CONTEXT.md left to the researcher: which aircraft types to model, what numeric values to give them, and how the FSM/procedure-following/taxi-abstraction code should be structured and split across modules.

Four aircraft types are recommended (within the 3-5 range): **Boeing 737-800** (narrowbody jet), **Embraer E175** (regional jet), **ATR 72-600** (turboprop), and **Cessna Citation CJ2+** (light business jet) — all real, well-documented, and plausible traffic at a London Luton-scale airport (Luton has substantial narrowbody, regional, and business-jet traffic; turboprops are less common at LTN specifically but are included deliberately for envelope spread, matching CONTEXT.md's own suggestion). Their real-world climb/cruise/approach numbers were web-sourced (LOW-MEDIUM confidence, cross-checked across multiple sources per type) and then *adapted* for in-sim use: because this phase's aircraft never leave the terminal area (departures are removed at the SID's exit fix, arrivals spawn at only FL170), each type's *terminal-area operating speed* (capped near the real 250kt low-altitude speed limit already coded into the DET STAR's restrictions) is the number that matters — not its high-altitude Mach cruise speed, which is largely irrelevant to this phase and should not be hardcoded as `cruise_speed_kt`.

The flight-phase FSM should use exactly the 8 phases the roadmap's success criterion #4 already names (`TAXI_OUT`, `DEPARTURE_ROLL`, `CLIMB`, `ENROUTE`, `DESCENT`, `APPROACH`, `LANDED`, `TAXI_IN`) — deliberately *not* including `LOC_CAPTURED`/`GS_CAPTURED` sub-states from `ARCHITECTURE.md`'s original 11-state sketch, since ILS capture logic is explicitly Phase 4 scope (PROC-03). `APPROACH` in this phase should be a simplified "fly direct to the runway threshold on a fixed nominal glidepath" behavior, not real localizer/glideslope geometry — this keeps Phase 3 from accidentally building Phase 4's work early (Pitfall 11) while still satisfying "descend toward the airport" and "land" end-to-end.

Procedure-following extends `ARCHITECTURE.md` Pattern 3's `compute_target()` sketch with two necessary refinements this project's real navdata requires: (1) **restriction look-ahead** — because DET 2A STAR's middle leg (LOFFO) carries no altitude restriction, the target altitude must be derived from the *next known* restriction ahead, not just the current leg, or the aircraft will "hold" at FL170 past LOFFO and then snap down at ABBOT, which is exactly the "numerically correct but experientially wrong" behavior Pitfall 7 warns about; and (2) **magnetic heading conversion** — any bearing-to-fix computed from geometry is inherently a true bearing and must be passed through the project's existing `geo.true_to_magnetic()` exactly once before being stored as the aircraft's `heading_deg`, to keep the aircraft's heading convention consistent with every navdata field (`course_deg_mag`, `heading_deg_mag`) it will eventually be compared against or instructed via (Phase 4).

**Primary recommendation:** Split the new logic into four focused `sim/` modules (`performance.py`, `phase.py`, `procedure.py`, `demo_traffic.py`) rather than growing `aircraft.py` into a monolith; give each aircraft type its own frozen `PerformanceProfile`; drive phase transitions off explicit, testable completion-conditions (timers elapsed, leg-index exhausted, distance/altitude thresholds) rather than scattered inline checks; and rotate which aircraft type spawns into the departure/arrival "slot" each time the D-03 demo loop restarts, so that success criterion #1 ("at least 3 distinct aircraft types are visibly differentiated... during flight") is actually satisfied across loop iterations, not just in a single static snapshot.

## Architectural Responsibility Map

> This project is a single-process native desktop app, not a multi-tier web app — the standard Browser/API/CDN/Database tiers don't apply. Tiers below are the project's own established architecture (`ARCHITECTURE.md`): **Sim Core** (headless, pygame-free, authoritative state — equivalent role to a backend/API tier), **Render Layer** (pygame-only, read-only presentation — equivalent role to a client/browser tier), **App Composition Root** (`app.py`, wires the two together, the only module allowed to import both).

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Per-type performance profiles (climb/descent/speed/turn) | Sim Core (`sim/performance.py`) | — | Facts + kinematics math about aircraft behavior; must be pygame-free to stay unit-testable per project's established boundary |
| Flight-phase FSM (states, legal transitions) | Sim Core (`sim/phase.py`) | — | Gates instruction legality (future Phase 4) and kinematics dispatch; must be independently unit-testable |
| Procedure-following (`compute_target()`, leg sequencing, restrictions) | Sim Core (`sim/procedure.py`) | Navdata (reads `Procedure`/`ProcedureLeg` read-only) | Derives kinematic targets from static navdata each tick; navdata is read-only reference data, never mutated |
| Demo-harness spawn/removal/looping (D-02/D-03) | Sim Core (`sim/demo_traffic.py`) | App Composition Root (`app.py` calls it each tick) | Spawn/removal orchestration is a distinct concern from aircraft state itself — isolating it here means Phase 6's real scenario loader can replace only this module |
| Taxi-visible stationary rendering (D-05) | Render Layer (`render/radar.py`, reads `aircraft.phase`) | Sim Core (phase field itself) | Renderer needs zero new logic — it already draws the aircraft dot at its current `x`/`y` every frame; TAXI_OUT/TAXI_IN phases simply hold position constant in the sim core, the renderer doesn't need to know phase to render correctly (though it may want to for future datablock work) |
| Removal-from-active-traffic condition checks | Sim Core (`sim/demo_traffic.py`, called from `app.py`'s `on_tick`) | — | Reads `aircraft.phase` + `aircraft.procedure_leg_index` / timer state; not itself a phase-FSM transition (see Pitfall "Removal is not a phase" below) |

## Standard Stack

### Core

No new third-party libraries are required for this phase. All work extends `pydantic` (already a dependency) with new frozen/mutable models, plus pure-Python math (`math.sin`/`cos`/`atan2`/`tan`) for kinematics — matching the project's own explicit constraint ("simplified per-aircraft-type performance profiles, not BADA-style tables or full physics") and its established "pattern, not a library" approach to the sim/render architecture (`CLAUDE.md`).

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pydantic | 2.13.4 (confirmed installed, `pyproject.toml` pins `>=2.13,<3.0`) [VERIFIED: local venv `python3 -c "import pydantic; print(pydantic.VERSION)"`] | `PerformanceProfile` (frozen, like navdata), `Aircraft` model extensions (`validate_assignment=True`, matches existing convention) | Already the project's sole data-modeling library; no reason to introduce a second one for this phase's new models |
| stdlib `enum` | n/a (stdlib) | `Phase` enum | Matches `ARCHITECTURE.md` Pattern 2's explicit recommendation: hand-rolled `Enum` + `dict[Phase, set[Phase]]`, not the `transitions` package, for v1's short mostly-linear phase list |
| stdlib `dataclasses` | n/a (stdlib) | `Targets` struct returned by `compute_target()` (heading/altitude/speed) | Per `CLAUDE.md`'s own stated convention: "lightweight internal-only structs... recomputed every frame where Pydantic's construction overhead isn't worth paying" — `Targets` is recomputed once per aircraft per sim tick, exactly this category |

### Supporting

None — no new supporting libraries needed. `geographiclib` (already a dependency) is reused via the existing `navdata/geo.py` helpers (`project_to_local_xy_nm`, `true_to_magnetic`) rather than being called directly again from new modules.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Hand-rolled `Enum` + transitions `dict` for `Phase` | `pytransitions/transitions` package | Already rejected by the project's own prior research (`ARCHITECTURE.md` Pattern 2) for v1's short linear phase list — reconsider only if VFR/go-around branching states are added in v2 |
| Simplified flat/coarse-coupled performance profiles | BADA (Base of Aircraft Data) performance tables | Explicitly out of scope per `PROJECT.md` constraints ("not BADA-style tables or full physics") — BADA requires a licensed dataset and per-altitude/per-weight table lookups, disproportionate to this project's fidelity target |
| `dataclass` for `Targets` | Frozen Pydantic model for `Targets` | Pydantic validation cost is unnecessary for a value recomputed every tick from already-validated inputs; use Pydantic only at true data boundaries (navdata load, scenario load — not here) |

**Installation:** None — no new dependencies to add to `pyproject.toml`.

### Aircraft Fleet (fulfills D-01)

**Recommended 4 types** (narrowbody jet, regional jet, turboprop, light jet — deliberately spans the full spread CONTEXT.md asked for, and all four are real, well-documented, plausible traffic for a London-area airport):

| Type | Category | Real-world climb rate | Real-world cruise/high-alt speed | Real-world approach/Vref speed | Sourcing |
|------|----------|------------------------|-----------------------------------|-------------------------------|----------|
| Boeing 737-800 | Narrowbody jet | ~1800 fpm (sea-level/typical ops) | ~Mach 0.789 (~450-490kt TAS at altitude); V2 ~162kt | ~130-145kt (VREF 30-flap, weight-dependent; not directly returned by search, standard-knowledge range) | [CITED: planephd.com, b737.org.uk, aircraftinvestigation.info] LOW-MEDIUM — aggregated across several enthusiast/spec sites, not a single authoritative source |
| Embraer E175 | Regional jet | ~1900-2500 fpm (18min to FL350 implies ~1900fpm average; commonly cited initial climb 2000-2500fpm) | Mach 0.78-0.82 (~450-490kt) | ~125-135kt (inferred from ~4130ft landing field length; not directly stated) | [CITED: embraer.com official E175 spec PDF, globalair.com, flightschoolusa.com] LOW-MEDIUM |
| ATR 72-600 | Turboprop | 1355 fpm (sea level, MTOW, ISA) [CITED: atr-aircraft.com official factsheet PDF, aerocorner.com] | 275 KTAS max cruise | 113 KIAS (VREF/landing reference) | [CITED: atr-aircraft.com official factsheet PDF] LOW-MEDIUM |
| Cessna Citation CJ2+ | Light business jet | ~3800 fpm two-engine (sea level) | High-speed cruise 407kt; long-range cruise 352kt | ~100-110kt (Vref ≈ 1.3×Vs per type's published approach-speed methodology; not directly stated) | [CITED: jetav.com, code7700.com] LOW-MEDIUM |
| Turn rate (all types, shared formula) | — | Rate of Turn (deg/sec) = `1091 × tan(bank_deg) / speed_kt` | Standard/Rate-1 turn = 3°/sec; bank-for-rate-1 ≈ `(speed_kt/10) + 7`, valid to ~250-300kt | — | [CITED: SKYbrary Aviation Safety "Rate of Turn", CFI Library] MEDIUM (cross-checked across 2 independent aviation-reference sources) |
| 3° glidepath descent rate (used for final APPROACH targeting) | — | `descent_fpm ≈ groundspeed_kt × 5` (e.g. 120kt→600fpm, 100kt→530fpm, 90kt→450fpm) | "Rule of three": 3nm horizontal per 1000ft descended | — | [CITED: multiple independent aviation web sources agreeing on the same ~5× multiplier] LOW-MEDIUM |

**Why these four, and why plausible at Luton:** London Luton (EGGW) has heavy narrowbody scheduled traffic (easyJet/Wizz Air-style 737/A320-class jets — 737-800 represents this segment), a meaningful regional-jet segment, and is one of the UK's largest general/business-aviation hubs (multiple based FBOs/operators), making a light business jet like the Citation CJ2+ genuinely representative rather than arbitrary. A turboprop is less typical at LTN specifically but is included deliberately, per CONTEXT.md's own suggestion, purely for envelope spread (it is the type most likely to visibly demonstrate slower climb/descent/turn behavior against the three jets).

**Critical adaptation for in-sim use — do not hardcode the researched cruise speeds as-is:** every departure aircraft this phase is removed once it passes the SID's exit fix (well below any real cruise altitude), and every arrival spawns at only FL170 and never climbs. The researched high-altitude Mach-cruise numbers (450-490kt) are **not** what should end up in the `PerformanceProfile.cruise_speed_kt` field — they are cited above only to establish real-world differentiation context and to justify the fleet selection. In-sim, `cruise_speed_kt` should represent each type's *terminal-area/below-FL100 operating speed*, which is naturally bounded near 250kt by real airspace speed limits (already reflected in the coded DET 2A STAR restrictions: 250kt at LOFFO, 220kt at ABBOT). See "Code Examples" for a recommended profile table already adapted to this constraint.

### Package Legitimacy Audit

No new external packages are introduced by this phase. All new code is pure Python (`enum`, `dataclasses`, `math`) plus the already-vetted `pydantic` dependency. The Package Legitimacy Gate does not apply — nothing to audit.

## Architecture Patterns

### System Architecture Diagram

```
                         SIM CORE (headless, no pygame import)
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                           │
│  sim/demo_traffic.py                                                     │
│  ┌──────────────────┐   spawn_departure()/spawn_arrival()                │
│  │ Demo spawn/loop/  │──────────────┐                                    │
│  │ removal orchestr. │              ▼                                    │
│  └────────┬──────────┘   ┌────────────────────┐                          │
│           │ each tick,    │   Aircraft (state)  │◄──── navdata/eggw.py    │
│           │ checks phase  │  x_nm, y_nm, alt,   │      (OLNEY_2B_SID,     │
│           │ + leg_index / │  speed, heading,    │       DET_2A_STAR,      │
│           │ timers for    │  phase, procedure   │       EGGW_RUNWAY)      │
│           │ removal       │  ref + leg_index,   │      read-only          │
│           │               │  performance ref,   │                        │
│           │               │  phase_timer        │                        │
│           │               └──────┬──────┬───────┘                        │
│           │                      │      │                                │
│           │        sim_step()    │      │  compute_target()              │
│           │        (aircraft.py) │      │  (procedure.py)                │
│           │                      ▼      ▼                                │
│           │           ┌─────────────────────┐   ┌─────────────────────┐ │
│           │           │  sim/phase.py        │   │  sim/procedure.py    │ │
│           │           │  - LEGAL_TRANSITIONS  │   │  - compute_target()  │ │
│           │           │  - transition_to()    │   │  - advance_leg_if_   │ │
│           │           │  - is_phase_complete()│   │    reached()         │ │
│           │           └───────────┬──────────┘   │  - restriction       │ │
│           │                       │               │    look-ahead        │ │
│           │                       ▼               └──────────┬──────────┘ │
│           │           ┌─────────────────────┐                │            │
│           └──────────►│  sim/performance.py  │◄───────────────┘            │
│                       │  - PerformanceProfile │                            │
│                       │  - FLEET (4 types)    │                            │
│                       │  - climb/descend/turn │                            │
│                       │    kinematics helpers │                            │
│                       └───────────────────────┘                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ every render frame reads current
                                    │ (interpolated) Aircraft state — never
                                    │ mutates it (CORE-03, unchanged)
                                    ▼
                       RENDER LAYER (pygame-only, read-only)
                  render/radar.py draws aircraft dot/vector/trail
                  exactly as it does today — no new logic required
                  for D-05 (TAXI_OUT/TAXI_IN aircraft simply have a
                  constant x/y that render code already knows how to draw)
```

A reader can trace the primary departure use case end to end: `demo_traffic.spawn_departure()` creates an `Aircraft` in `TAXI_OUT` referencing `OLNEY_2B_SID` → each sim tick, `aircraft.py`'s `sim_step()` checks `phase.is_phase_complete()` to decide whether to `phase.transition_to()` the next phase → once in `CLIMB`, `procedure.compute_target()` is called each tick to derive heading/altitude/speed from the current leg + look-ahead restrictions → `performance.py`'s kinematics helpers move the aircraft toward those targets at its type's climb/turn-rate limits → `procedure.advance_leg_if_reached()` increments `leg_index` when the aircraft reaches each fix → once `leg_index` exhausts `OLNEY_2B_SID.legs` while `phase == ENROUTE`, `demo_traffic.py`'s per-tick check removes the aircraft and (once the arrival is also gone) respawns a fresh pair.

### Recommended Project Structure

```
src/atc_sim/sim/
├── clock.py              # unchanged
├── interpolation.py       # unchanged (still only tracks x, y, heading_deg — extend
│                          #   AircraftSnapshot with altitude_ft if the renderer or a
│                          #   future datablock needs to interpolate it; not required
│                          #   this phase since D-04 defers a datablock)
├── aircraft.py            # Aircraft model (evolved) + sim_step() dispatcher
├── performance.py         # NEW: PerformanceProfile model, FLEET constants, kinematics helpers
├── phase.py               # NEW: Phase enum, LEGAL_TRANSITIONS, transition_to(), is_phase_complete()
├── procedure.py           # NEW: Targets dataclass, compute_target(), advance_leg_if_reached(),
│                          #   restriction look-ahead helpers
└── demo_traffic.py        # NEW: spawn_departure()/spawn_arrival(), type-rotation, removal checks,
                           #   loop-restart logic (D-02/D-03)
```

**Structure rationale:** `ARCHITECTURE.md`'s original sketch nested the `Phase` enum directly inside `aircraft.py`. This research recommends splitting it into its own `phase.py` module instead, because `aircraft.py` is about to grow substantially (performance/procedure references, altitude/speed/heading state, kinematics dispatch) and the FSM's legal-transitions table plus its completion-condition logic (`is_phase_complete()`) benefits from being independently unit-testable with zero `Aircraft` construction overhead (pure `Phase → Phase` transition tests). This is a deliberate, justified evolution of the prior research's sketch, not a contradiction of it — the "hand-rolled `Enum` + `dict`, not `transitions` library" recommendation from `ARCHITECTURE.md` Pattern 2 is fully preserved.

### Pattern A: Per-type frozen `PerformanceProfile` + shared kinematics functions

**What:** One frozen Pydantic model (mirrors the navdata convention already established — "facts about an aircraft type," not "state of a specific aircraft") holding each type's climb rate, descent rate, terminal-area operating speed, approach speed, max bank angle, and max speed-change rate. A small set of *shared* functions (not per-type methods) compute climb-toward-target, descend-toward-target, turn-toward-target, and accelerate/decelerate-toward-target, each taking the profile + current state + target as arguments.

**When to use:** Always for this phase's kinematics — this is what PERF-01 literally asks for ("simplified per-type performance profile... drawn from a fleet of 3-5 aircraft types").

**Example:**
```python
# sim/performance.py
from pydantic import BaseModel, ConfigDict, Field


class PerformanceProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str                          # "Boeing 737-800"
    category: str                      # "narrowbody_jet" | "regional_jet" | "turboprop" | "light_jet"
    climb_rate_fpm: float = Field(gt=0.0)
    descent_rate_fpm: float = Field(gt=0.0)     # nominal enroute/STAR descent, NOT final glidepath
    terminal_speed_kt: float = Field(gt=0.0)     # below-FL100 operating speed; NOT high-altitude cruise
    approach_speed_kt: float = Field(gt=0.0)     # Vref-equivalent, used once established on APPROACH
    max_bank_deg: float = Field(gt=0.0, lt=45.0)
    max_speed_change_kt_per_sec: float = Field(gt=0.0)


# Recommended fleet (see "Standard Stack: Aircraft Fleet" for sourcing/derivation notes;
# these are simplified in-sim values, NOT the raw real-world cruise numbers cited there)
BOEING_737_800 = PerformanceProfile(
    name="Boeing 737-800", category="narrowbody_jet",
    climb_rate_fpm=1800, descent_rate_fpm=1500,
    terminal_speed_kt=250, approach_speed_kt=140,
    max_bank_deg=25.0, max_speed_change_kt_per_sec=1.5,
)
EMBRAER_E175 = PerformanceProfile(
    name="Embraer E175", category="regional_jet",
    climb_rate_fpm=2200, descent_rate_fpm=1800,
    terminal_speed_kt=250, approach_speed_kt=130,
    max_bank_deg=25.0, max_speed_change_kt_per_sec=1.8,
)
ATR_72_600 = PerformanceProfile(
    name="ATR 72-600", category="turboprop",
    climb_rate_fpm=1350, descent_rate_fpm=1000,
    terminal_speed_kt=180, approach_speed_kt=110,
    max_bank_deg=22.0, max_speed_change_kt_per_sec=1.2,
)
CESSNA_CJ2_PLUS = PerformanceProfile(
    name="Cessna Citation CJ2+", category="light_jet",
    climb_rate_fpm=3500, descent_rate_fpm=2000,
    terminal_speed_kt=220, approach_speed_kt=105,
    max_bank_deg=27.0, max_speed_change_kt_per_sec=2.0,
)

FLEET: dict[str, PerformanceProfile] = {
    p.name: p for p in (BOEING_737_800, EMBRAER_E175, ATR_72_600, CESSNA_CJ2_PLUS)
}


def turn_rate_deg_per_sec(bank_deg: float, speed_kt: float) -> float:
    """[CITED: SKYbrary 'Rate of Turn'] ROT = 1091 * tan(bank) / speed(kt).
    Called with each type's max_bank_deg and the aircraft's CURRENT speed_kt —
    turn rate differences between types emerge naturally from their differing
    terminal speeds even before any bank-angle differentiation is applied."""
    import math
    return (1091.0 * math.tan(math.radians(bank_deg))) / speed_kt
```

**Trade-offs:** A single shared `turn_rate_deg_per_sec()` function fed each type's own current speed automatically differentiates turn behavior (satisfies success criterion #1) without needing separate per-type turn-rate constants — this is the "coupling, not independent knobs" guidance from Pitfall 7 applied directly: turn rate is *coupled* to groundspeed by construction, not an independent scalar.

### Pattern B: Explicit 8-state flight-phase FSM (fulfills PERF-02)

**What:** Exactly the 8 phases named in the roadmap's success criterion #4 — no more, no less. `LOC_CAPTURED`/`GS_CAPTURED` sub-states from `ARCHITECTURE.md`'s original 11-state sketch are deliberately **excluded** this phase (they are Phase 4/PROC-03 scope).

**Example:**
```python
# sim/phase.py
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


# Mostly-linear chain. ENROUTE -> DESCENT and DESCENT -> APPROACH are defined
# for forward-compatibility (a future full-flight scenario) even though this
# phase's departure demo aircraft is removed from ENROUTE before ever
# reaching DESCENT, and this phase's arrival demo aircraft spawns directly
# into DESCENT rather than transitioning through CLIMB/ENROUTE first.
LEGAL_TRANSITIONS: dict[Phase, set[Phase]] = {
    Phase.TAXI_OUT: {Phase.DEPARTURE_ROLL},
    Phase.DEPARTURE_ROLL: {Phase.CLIMB},
    Phase.CLIMB: {Phase.ENROUTE},
    Phase.ENROUTE: {Phase.DESCENT},
    Phase.DESCENT: {Phase.APPROACH},
    Phase.APPROACH: {Phase.LANDED},
    Phase.LANDED: {Phase.TAXI_IN},
    Phase.TAXI_IN: set(),  # terminal; removal happens externally, see Pitfall below
}


def transition_to(current: Phase, new: Phase) -> Phase:
    if new not in LEGAL_TRANSITIONS[current]:
        raise ValueError(f"Illegal transition {current} -> {new}")
    return new
```

**Spawn phase depends on flight kind, not a new field:** a departure `Aircraft` is constructed with `phase=Phase.TAXI_OUT`; an arrival `Aircraft` is constructed with `phase=Phase.DESCENT` directly (STARs are inherently a descending profile — modeling a redundant `ENROUTE` entry phase for arrivals adds no value this phase). No separate `is_departure: bool` field is needed — the initial `phase` value alone fully determines which half of the transition graph an aircraft will traverse; adding a redundant flag risks the two falling out of sync.

### Pattern C: Taxi / departure-roll / landing / taxi-in abstractions

**What:** `TAXI_OUT` and `TAXI_IN` are pure timers — the aircraft's position does not change at all during these phases (satisfies D-05's "stationary dot" requirement with zero extra rendering logic: the renderer just keeps drawing the same unchanged `x`/`y` every frame). `DEPARTURE_ROLL`, by contrast, is a **short real kinematic phase**: a straight-line acceleration from the stand/threshold position along the runway heading (`EGGW_RUNWAY.heading_deg_mag`) from 0kt to a rotation speed, giving visible motion that satisfies the "watch the full lifecycle happen" framing behind D-05 without requiring any new rendering machinery. `LANDED` is a near-instantaneous transition (touchdown detected, immediately becomes `TAXI_IN`); the aircraft's position is then snapped/teleported to a taxi-in stand position (ground movement/pathfinding is explicitly out of scope — GND-01 is v2).

**Recommended single-timer field, not one field per phase:**
```python
# sim/aircraft.py (excerpt) — reuse ONE generic timer field across every
# timed phase rather than taxi_timer/departure_roll_timer/taxi_in_timer as
# three separate fields (only one is ever active per aircraft at a time)
class Aircraft(BaseModel):
    ...
    phase: Phase
    phase_elapsed_sec: float = 0.0   # reset to 0.0 on every phase.transition_to() call
```

**Recommended default durations** (Claude's Discretion per CONTEXT.md — these are reasonable UX-pacing defaults, not sourced facts, tag `[ASSUMED]`):

| Phase | Duration | Notes |
|-------|----------|-------|
| TAXI_OUT | ~15-20 sim seconds | Long enough to be observable, short enough not to feel like a stall |
| DEPARTURE_ROLL | ~6-8 sim seconds | Accelerate 0 → rotation speed (~140-160kt-equivalent depending on type) over this window |
| TAXI_IN | ~15-20 sim seconds | Symmetric with TAXI_OUT |

**`APPROACH`'s simplified glidepath (critical scope boundary):** once an arrival's `leg_index` exhausts `DET_2A_STAR.legs` (i.e., past ABBOT), transition `DESCENT → APPROACH`. In `APPROACH`, `compute_target()` should target the runway threshold *directly* (bearing computed the same way as any other fix-following target) with altitude derived from the simplified 3°-glidepath rule (`descent_fpm ≈ groundspeed_kt × 5`, or equivalently target_altitude_ft ≈ distance_to_threshold_nm × 300, clamped to 0 at the threshold). Transition `APPROACH → LANDED` once distance-to-threshold and altitude both cross small thresholds (e.g. < 0.1nm and < 50ft). **Do not** build real localizer/glideslope intercept-angle or armed/captured sub-state logic here — that is Phase 4's PROC-03, and building it now both violates the phase boundary CONTEXT.md drew and risks wasted rework once Phase 4's real vectoring-override layer needs to plug into the same seam (Pitfall 11: don't invest in fidelity ahead of the thin end-to-end loop).

### Pattern D: `compute_target()` with restriction look-ahead (fulfills PROC-01, extends ARCHITECTURE.md Pattern 3)

**What:** `ARCHITECTURE.md`'s original `compute_target()` sketch derives target altitude/speed purely from the *current* leg's restriction, holding the aircraft's *current* value if the leg has none (`leg.altitude_restriction or aircraft.altitude`). Applied naively to the real DET 2A STAR, this produces exactly the "numerically correct, experientially wrong" bug Pitfall 7 warns about: the aircraft would hold flat at FL170 all the way to LOFFO (which has no altitude restriction), then have to snap down hard toward ABBOT's FL080/220kt restriction. The fix: look ahead across legs for the *next* restriction, not just the current one, so a continuous descent begins immediately, and hold the aircraft at/above the *most recently passed* restriction as a floor (for `at_or_above`) or below it as a ceiling (for `at_or_below`).

**Example:**
```python
# sim/procedure.py
from dataclasses import dataclass

from atc_sim.navdata.geo import project_to_local_xy_nm, true_to_magnetic
from atc_sim.sim.aircraft import Aircraft


@dataclass(frozen=True)
class Targets:
    heading_deg: float   # MAGNETIC — see "Common Pitfalls" below
    altitude_ft: float
    speed_kt: float


def _next_altitude_restriction_ft(aircraft: Aircraft) -> float:
    """Looks ahead from the CURRENT leg onward for the next altitude
    restriction (any kind); falls back to the aircraft's current target if
    none remain on the procedure. This is what makes DET STAR's unrestricted
    LOFFO leg produce a continuous descent toward ABBOT's FL080, rather than
    a level-then-snap profile (Pitfall 7)."""
    legs = aircraft.procedure.legs[aircraft.procedure_leg_index:]
    for leg in legs:
        if leg.altitude_restriction is not None:
            return float(leg.altitude_restriction.altitude_ft)
    return aircraft.target_altitude_ft  # no more restrictions ahead — hold


def _next_speed_restriction_kt(aircraft: Aircraft) -> float:
    legs = aircraft.procedure.legs[aircraft.procedure_leg_index:]
    for leg in legs:
        if leg.speed_restriction is not None:
            return float(leg.speed_restriction.speed_kt)
    return aircraft.performance.terminal_speed_kt


def compute_target(aircraft: Aircraft) -> Targets:
    leg = aircraft.procedure.legs[aircraft.procedure_leg_index]
    fix_x_nm, fix_y_nm = project_to_local_xy_nm(leg.fix.lat, leg.fix.lon)
    dx, dy = fix_x_nm - aircraft.x_nm, fix_y_nm - aircraft.y_nm
    import math
    true_bearing = math.degrees(math.atan2(dx, dy)) % 360.0   # same sin=x/cos=y convention as sim/aircraft.py
    heading_deg_mag = true_to_magnetic(true_bearing)           # Pitfall 4: convert true->magnetic exactly once

    return Targets(
        heading_deg=heading_deg_mag,
        altitude_ft=_next_altitude_restriction_ft(aircraft),
        speed_kt=_next_speed_restriction_kt(aircraft),
    )


def advance_leg_if_reached(aircraft: Aircraft, capture_radius_nm: float = 1.0) -> None:
    """Fly-by-style simplified fix sequencing: once within capture_radius_nm
    of the current leg's fix, advance to the next leg. Uses simple planar
    distance in the shared local-nm coordinate system (both aircraft and fix
    are already in that space — no geodesic call needed per tick, avoiding
    the "recomputing great-circle geodesics" performance trap). A
    simplification of real FMS fly-by/fly-over logic — acceptable for v1 per
    Pitfall 11 (don't over-invest fidelity before the end-to-end loop
    works). Tag: [ASSUMED]."""
    import math

    leg = aircraft.procedure.legs[aircraft.procedure_leg_index]
    fix_x_nm, fix_y_nm = project_to_local_xy_nm(leg.fix.lat, leg.fix.lon)
    distance_nm = math.hypot(fix_x_nm - aircraft.x_nm, fix_y_nm - aircraft.y_nm)
    if distance_nm <= capture_radius_nm:
        aircraft.procedure_leg_index += 1
```

**Why local-plane (`x_nm`/`y_nm`) coordinates for `Aircraft`, not lat/lon:** `navdata/geo.py`'s `project_to_local_xy_nm()` already converts every fix/runway lat/lon into the same local tangent-plane coordinate system used for rendering (`render/radar.py`'s `world_to_screen()` consumes exactly this). Storing `Aircraft.x_nm`/`y_nm` in that same coordinate system (rather than lat/lon, and rather than the current Phase-1 placeholder's raw pixels) means aircraft and every navdata element share one coordinate space, per-tick kinematics become simple planar trigonometry (no repeated `geographiclib.Inverse()` calls per aircraft per tick — avoiding the "recomputing great-circle geodesics" performance trap PITFALLS.md already flags), and the render layer's existing `world_to_screen()` conversion works unchanged for aircraft, fixes, and the runway alike.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Turn rate as a function of bank/speed | A custom per-type lookup table or arbitrary constant | The standard aviation `ROT = 1091 × tan(bank) / speed_kt` formula (Pattern A) | It's a well-established, single-line formula that naturally couples turn rate to speed — reinventing a table wastes effort and loses the natural per-type differentiation the formula gives for free |
| Great-circle bearing/distance math for procedure-following | A second geodesic implementation inside `sim/procedure.py` | The existing `navdata/geo.py` (`project_to_local_xy_nm`, `true_bearing_and_distance_nm`, `true_to_magnetic`) | This module already exists specifically so display and future separation math never disagree (RADAR-04) — reusing it for procedure-following extends that same guarantee to autonomous flight, and avoids a second, possibly-inconsistent bearing calculation |
| A general-purpose Python FSM library | `pytransitions/transitions` | Hand-rolled `Enum` + `dict[Phase, set[Phase]]` (Pattern B) | Already decided in `ARCHITECTURE.md` Pattern 2 for this project's short, linear v1 phase list; introducing a dependency for an 8-state linear chain is unjustified complexity |
| ILS localizer/glideslope capture math | Any bank-angle/intercept-angle logic during `APPROACH` | The simplified fixed-glidepath "fly direct to threshold" calc in Pattern C | This is explicitly Phase 4/PROC-03 scope — building it now duplicates work and risks needing rework once the real vectoring-override layer needs to plug into the same seam |

**Key insight:** every "don't hand-roll" item above already has an existing, correct answer somewhere in this project's own prior research or already-built modules (`navdata/geo.py`, `ARCHITECTURE.md`). This phase's job is to *reuse* those, not invent parallel versions — the biggest risk is quietly reimplementing bearing math or FSM machinery slightly differently inside the new `sim/procedure.py`/`sim/phase.py` modules.

## Common Pitfalls

### Pitfall: Removal-from-active-traffic treated as a phase-FSM transition

**What goes wrong:** It's tempting to add a `REMOVED`/`GONE` state to the `Phase` enum so "aircraft is done" fits neatly into the transition table.
**Why it happens:** The FSM already models the aircraft's lifecycle, so adding one more terminal state feels consistent.
**How to avoid:** Removal (D-03) is a *list membership* concern (`aircraft_list.remove(aircraft)`), decided externally by `demo_traffic.py` reading `phase == ENROUTE and procedure_leg_index >= len(procedure.legs)` (departure) or a `TAXI_IN` timer elapsing (arrival) — not a `Phase` value. Adding a `REMOVED` phase would need a transition into it from *both* `ENROUTE` and `TAXI_IN`, which muddies the otherwise-clean linear chain for no benefit, since nothing ever needs to query "is this aircraft in the REMOVED phase" — it simply isn't in the list anymore.
**Warning signs:** A `REMOVED` or `GONE` enum member with no `is_phase_complete()` logic driving *into* it from kinematics — a sign the state exists only to satisfy the type checker, not because a real phase-completion condition needs it.

### Pitfall: "3 distinct types visibly differentiated" is not automatically satisfied by a 2-aircraft demo harness

**What goes wrong:** D-02 specifies exactly one hardcoded departure aircraft and one hardcoded arrival aircraft per demo cycle. If those two are always the *same* two types, success criterion #1 ("at least 3 distinct aircraft types are visibly differentiated... during flight") is never actually demonstrated by the running app, even though 4 types exist in `FLEET`.
**Why it happens:** D-02's wording focuses on the departure/arrival *flow*, not fleet rotation; it's easy to read it as "always spawn the same demo pair" and satisfy PERF-01 only in the sense that the data exists, not that it's observably exercised.
**How to avoid:** Rotate which `FLEET` type spawns into each slot every time the D-03 loop restarts — e.g. a fixed round-robin sequence (`[BOEING_737_800, EMBRAER_E175, ATR_72_600, CESSNA_CJ2_PLUS]`, advancing one type per loop per slot) so that within 1-2 loop iterations, at least 3 (in practice all 4) types have visibly flown. This is not explicitly locked in CONTEXT.md — flag it to the planner as a requirement-satisfaction risk, not an optional nicety.
**Warning signs:** A hardcoded `spawn_departure()` that always constructs a `Boeing 737-800` `Aircraft` with no type parameter.

### Pitfall: Restriction look-ahead omitted, reproducing Pitfall 7 exactly

**What goes wrong:** Implementing `compute_target()` literally as `ARCHITECTURE.md`'s original one-leg-only sketch (`leg.altitude_restriction or aircraft.altitude`) against the *real* DET 2A STAR data produces a level flight at FL170 through LOFFO, then an instant snap toward FL080 at ABBOT — a direct real-world instance of the project's own already-documented Pitfall 7 ("numerically correct but experientially wrong... an arrival can be told to descend and both happen at their independent max rates simultaneously with no visible tradeoff").
**Why it happens:** The one-leg-only version is the simpler code to write and passes a shallow "does it read the restriction fields" test.
**How to avoid:** Implement the look-ahead version in Pattern D above; write a test that specifically exercises the DET STAR's LOFFO leg (no altitude restriction) and asserts the target altitude is already descending toward ABBOT's FL080, not held at FL170.
**Warning signs:** Playtesting shows the arrival aircraft flying dead level for a long visible stretch, then dropping sharply.

### Pitfall: Heading stored as true bearing instead of magnetic

**What goes wrong:** `compute_target()`'s bearing-to-fix calculation (`atan2`/`math.degrees`) produces a **true** bearing by construction (it's raw local-plane geometry). If this is assigned directly to `aircraft.heading_deg` without conversion, the aircraft's heading field becomes inconsistent with every other magnetic-convention field in the codebase (`Runway.heading_deg_mag`, `ProcedureLeg.course_deg_mag`), reproducing PITFALLS.md's own documented Pitfall 4 ("true vs. magnetic heading applied inconsistently").
**Why it happens:** In a no-wind model, true and magnetic values are numerically close (EGGW's variation is only ~1.2°), so the bug looks like acceptable rounding error rather than a convention violation, until Phase 4 needs to compare an assigned heading against a charted magnetic course or display it to the player.
**How to avoid:** Route every geometrically-computed bearing through `navdata/geo.py`'s existing `true_to_magnetic()` exactly once (Pattern D's example does this) before it is ever assigned to `Aircraft.heading_deg`. Decide and document explicitly that `Aircraft.heading_deg` is MAGNETIC, matching every navdata field it will be compared against.
**Warning signs:** A `compute_target()` or kinematics function that calls `math.atan2`/`math.degrees` and assigns the result straight to `heading_deg` with no `true_to_magnetic()` call in between.

### Pitfall: Building real ILS capture logic into `APPROACH` this phase

**What goes wrong:** Because `APPROACH` needs to get an arrival "toward the airport" and eventually to `LANDED`, it's tempting to start modeling localizer/glideslope intercept angles, armed/captured sub-states, or intercept-angle bounds — exactly PITFALLS.md's own Pitfall 6, which is explicitly scoped to Phase 4 (PROC-03) per this project's roadmap and CONTEXT.md's phase-boundary framing.
**Why it happens:** The domain is genuinely deep and satisfying to model correctly (PITFALLS.md's Pitfall 11 calls this out directly as this project's biggest scope-creep risk), and "descend toward the airport and land" feels incomplete without real ILS geometry.
**How to avoid:** Use Pattern C's simplified fixed-glidepath-to-threshold calculation for `APPROACH` in this phase. It fully satisfies this phase's success criteria (arrival flies the STAR, then lands, then taxis in) without touching localizer/glideslope math at all.
**Warning signs:** Any new field or state named `LOC_ARMED`/`LOC_CAPTURED`/`GS_CAPTURED` appearing in this phase's plans.

### Pitfall: Per-phase kinematics dispatch scattered as inline conditionals

**What goes wrong:** `sim_step()`'s kinematics differ meaningfully by phase (TAXI_OUT/TAXI_IN: frozen position, decrement timer only; DEPARTURE_ROLL: straight-line runway-heading acceleration only, no turning; CLIMB/ENROUTE/DESCENT/APPROACH: full `compute_target()`-driven turn/climb-or-descend/speed-change kinematics; LANDED: single-tick pass-through). Writing this as one large `if phase == X: ... elif phase == Y: ...` block inside `sim_step()` reproduces `ARCHITECTURE.md`'s Anti-Pattern 2 ("implicit phase via scattered thresholds") in spirit, even though an explicit `Phase` enum exists, because the *behavioral* logic per phase is still scattered rather than isolated.
**How to avoid:** Keep a small, explicit per-phase dispatch table or a handful of clearly-named helper functions (`_step_taxi`, `_step_departure_roll`, `_step_airborne`, `_step_landed`) called from one short `sim_step()`, each independently unit-testable.
**Warning signs:** A single `sim_step()` function longer than ~40-50 lines mixing timer logic, kinematics, and phase-transition checks inline.

## Code Examples

### Full-lifecycle kinematics dispatch sketch
```python
# sim/aircraft.py (excerpt)
from atc_sim.sim.phase import Phase, is_phase_complete, transition_to
from atc_sim.sim.procedure import advance_leg_if_reached, compute_target


def sim_step(aircraft: Aircraft, dt: float) -> None:
    if aircraft.phase in (Phase.TAXI_OUT, Phase.TAXI_IN):
        aircraft.phase_elapsed_sec += dt
    elif aircraft.phase == Phase.DEPARTURE_ROLL:
        _step_departure_roll(aircraft, dt)
    else:  # CLIMB, ENROUTE, DESCENT, APPROACH, LANDED
        _step_airborne(aircraft, dt)

    if is_phase_complete(aircraft):
        aircraft.phase = transition_to(aircraft.phase, _next_phase(aircraft.phase))
        aircraft.phase_elapsed_sec = 0.0


def _step_airborne(aircraft: Aircraft, dt: float) -> None:
    targets = compute_target(aircraft)
    # turn toward targets.heading_deg at performance.turn_rate_deg_per_sec(...)
    # climb/descend toward targets.altitude_ft at performance climb/descent rate
    # accelerate/decelerate toward targets.speed_kt at max_speed_change_kt_per_sec
    # move x_nm/y_nm using current heading/speed, same sin=x/-cos=y convention
    # as the existing sim/aircraft.py sim_step
    advance_leg_if_reached(aircraft)
```

### Restriction-kind semantics (already-modeled navdata, applied correctly)
```python
# "at_or_above" (e.g. OLNEY leg, 6000ft): a floor. A continuously-climbing
# departure naturally satisfies this without special-casing — just don't
# cap climb below it.
# "at_or_below" (e.g. a hypothetical STAR leg): a ceiling — don't climb
# above it once assigned as a target.
# "at" (e.g. DET fix FL170, ABBOT FL080): treat as an exact target — both
# floor and ceiling simultaneously, used directly as compute_target()'s
# returned altitude_ft when it's the nearest upcoming restriction.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| BADA (Base of Aircraft Data) full performance tables | Simplified coupled-parameter profiles for hobby/indie ATC sims | N/A — this project's own deliberate choice, not an industry shift | Full BADA tables require licensing and per-altitude/weight lookups disproportionate to this project's fidelity target; this was already decided at the project level (`PROJECT.md` constraints), this research only supplies the concrete numbers |
| Independent boolean flags for guidance mode | Single well-defined guidance-mode state | Established real-world ATC/flight-sim practice, already documented in this project's own `PITFALLS.md` Pitfall 6 | Directly informs why this phase's `Phase` enum must stay a single authoritative field, not a set of booleans |

**Deprecated/outdated:** Not applicable — this is new functionality in a project with no prior implementation of this domain to deprecate.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Exact in-sim numeric performance values (climb/descent rate, terminal speed, approach speed, max bank, max speed-change) for all 4 recommended aircraft types | Standard Stack: Aircraft Fleet; Pattern A | Low — CONTEXT.md already delegates exact values to discretion; if playtesting shows types feel too similar or too extreme, values are isolated in one `performance.py` module and easy to retune without touching FSM/procedure logic |
| A2 | Recommended taxi/departure-roll/taxi-in timer durations (15-20s / 6-8s / 15-20s) | Pattern C | Low — explicitly UX pacing, not a correctness concern; easy to retune |
| A3 | Simplified fixed-glidepath "direct to threshold" APPROACH targeting (not real ILS geometry) | Pattern C | Low-Medium — if a future Phase 4 reviewer expects Phase 3's APPROACH to already resemble localizer/glideslope behavior, this could read as underbuilt; mitigated by this being an explicit, documented phase-boundary decision already established in CONTEXT.md's domain framing |
| A4 | 1nm fly-by-style leg-capture radius for procedure fix sequencing | Pattern D (`advance_leg_if_reached`) | Low — a reasonable simplification of real FMS fly-by/fly-over logic; if it causes visibly cutting corners too sharply or overshooting, is a single tunable constant |
| A5 | Aircraft type-rotation strategy across demo loop iterations to satisfy "3 distinct types visibly differentiated" | Common Pitfalls: "3 distinct types..." | Medium — if the planner instead hardcodes a fixed departure/arrival type pair without rotation, success criterion #1 risks being only nominally satisfied (data exists) rather than observably satisfied (a human watching the app sees ≥3 types fly) |
| A6 | Embraer E175 and standard-rate-turn-formula findings that initially fell back to training knowledge before a successful retry with real web sources (see Sources) | Standard Stack: Aircraft Fleet | Low — both were subsequently re-verified with real citations (embraer.com official spec PDF; SKYbrary) in this same research session |

**If this table is empty:** N/A — see entries above; all are low-to-medium risk and isolated to a single module each, matching this phase's own "Claude's Discretion" framing in CONTEXT.md.

## Open Questions

1. **Should `AircraftSnapshot` (interpolation.py) be extended with `altitude_ft`?**
   - What we know: The current `AircraftSnapshot` only carries `x`, `y`, `heading_deg` — sufficient for Phase 1/2's rendering (position + heading vector only).
   - What's unclear: Whether Phase 3 needs altitude interpolated for any rendering purpose this phase (D-04 defers a datablock, so altitude isn't displayed yet).
   - Recommendation: Skip extending it this phase — altitude only needs to exist on the authoritative `Aircraft` model, not the render-interpolation snapshot, until a Phase 4 datablock needs to display it smoothly. Revisit in Phase 4.

2. **Exact stand/gate coordinates for TAXI_OUT/TAXI_IN (CONTEXT.md discretion item).**
   - What we know: CONTEXT.md explicitly leaves this to implementation discretion; it doesn't need to be sourced from a real chart.
   - What's unclear: The precise nm-offset from `EGGW_RUNWAY` threshold to use.
   - Recommendation: Derive it the same way every other static point in this codebase is derived — via `project_to_local_xy_nm` from a small made-up lat/lon a short distance off the runway centerline, OR simpler: a fixed local nm offset (e.g., 0.2nm perpendicular from the threshold) expressed directly in the already-established local coordinate system, avoiding inventing a new lat/lon. Either is fine; this is a one-line constant, not an architectural decision.

## Environment Availability

No new external dependencies. All three third-party libraries this phase's code touches (`pydantic`, and transitively `geographiclib` via existing `navdata/geo.py` helpers) are already installed and verified working in the project's `.venv` from Phase 1/2.

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| pydantic | `PerformanceProfile`, `Aircraft` model extensions | ✓ [VERIFIED: local venv import check] | 2.13.4 | — |
| geographiclib | Reused transitively via `navdata/geo.py` (no new direct calls needed — see Pattern D) | ✓ [VERIFIED: local venv import check] | (already pinned `>=2.1,<3.0`) | — |
| pygame-ce | Unaffected — render layer needs no new logic this phase | ✓ [VERIFIED: local venv import check] | 2.5.7 | — |

**Missing dependencies with no fallback:** None.
**Missing dependencies with fallback:** None.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.x (already configured, `pyproject.toml` `[tool.pytest.ini_options] testpaths = ["tests"]`) |
| Config file | `pyproject.toml` |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|---------------------|-------------|
| PERF-01 | Each of the 4 `FLEET` profiles has distinct climb/descent/terminal-speed/bank values; `turn_rate_deg_per_sec()` produces different rates for different speeds at the same bank | unit | `pytest tests/test_performance.py -x` | ❌ Wave 0 |
| PERF-02 | `LEGAL_TRANSITIONS` covers all 8 phases; `transition_to()` raises on any transition not in the table; a full linear TAXI_OUT→...→TAXI_IN walk succeeds | unit | `pytest tests/test_phase_fsm.py -x` | ❌ Wave 0 |
| PERF-03 | Headless-driven departure aircraft (spawned via `demo_traffic.spawn_departure()`) visits TAXI_OUT→DEPARTURE_ROLL→CLIMB→ENROUTE in that exact order with no skips, and is removed once `procedure_leg_index` exhausts `OLNEY_2B_SID.legs` | integration | `pytest tests/test_departure_flow.py -x` | ❌ Wave 0 |
| PERF-04 | Headless-driven arrival aircraft spawns in DESCENT at FL170 (matching DET fix's real `at 17000` restriction), visits DESCENT→APPROACH→LANDED→TAXI_IN in order, and is removed after the TAXI_IN timer elapses | integration | `pytest tests/test_arrival_flow.py -x` | ❌ Wave 0 |
| PROC-01 | `compute_target()` on the DET STAR's LOFFO leg (no altitude restriction) returns a target already descending toward ABBOT's FL080, not held at FL170; `advance_leg_if_reached()` increments `leg_index` on approach to a fix | unit | `pytest tests/test_procedure_following.py -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_performance.py` — covers PERF-01
- [ ] `tests/test_phase_fsm.py` — covers PERF-02
- [ ] `tests/test_procedure_following.py` — covers PROC-01
- [ ] `tests/test_departure_flow.py` — covers PERF-03
- [ ] `tests/test_arrival_flow.py` — covers PERF-04
- [ ] Shared fixture/helper: a headless "step N sim ticks and record the phase sequence observed" test harness (likely in a new `tests/conftest.py` fixture) — both flow tests need this and should not duplicate it

*(Framework itself needs no new install — pytest 8.x already present, no config changes needed.)*

## Security Domain

### Applicable ASVS Categories

This phase adds no new untrusted-input boundary: no network I/O, no file parsing, no user-supplied data (all navdata/performance/procedure data is hardcoded Python constants, exactly like Phase 1/2). The player cannot yet issue any instruction (Phase 4). Most ASVS categories are structurally not applicable to a single-player, offline, local-only desktop simulator with no persistence layer.

| ASVS Category | Applies | Standard Control |
|---------------|---------|-------------------|
| V2 Authentication | No | N/A — no authentication surface exists or is planned for this project |
| V3 Session Management | No | N/A — no sessions/network in a local single-player desktop app |
| V4 Access Control | No | N/A — no multi-user/permission model |
| V5 Input Validation | Yes (narrow) | Pydantic `Field` bounds on the new `PerformanceProfile`/`Aircraft` fields (e.g. `gt=0.0` on climb/descent/speed rates, `lt=45.0` on `max_bank_deg`) — this is defensive validation against internal logic bugs producing physically-impossible state, not a security boundary against an adversarial actor (there is none in this phase) |
| V6 Cryptography | No | N/A — no secrets, no data at rest requiring encryption |

### Known Threat Patterns for this stack

None apply — this phase introduces no new attack surface (no network, no file/user input parsing, no serialization of untrusted data). The only "input validation" relevant here is Pydantic's existing role of catching internal programming errors (e.g., accidentally constructing a `PerformanceProfile` with a negative climb rate), which is a correctness control, not a security control.

## Sources

### Primary (HIGH confidence)
- Existing project research and code, read directly this session: `.planning/research/ARCHITECTURE.md`, `.planning/research/PITFALLS.md`, `.planning/research/SUMMARY.md`, `.planning/phases/02-navdata-coordinate-projection/02-CONTEXT.md`, `src/atc_sim/sim/aircraft.py`, `src/atc_sim/sim/clock.py`, `src/atc_sim/sim/interpolation.py`, `src/atc_sim/navdata/{models,geo,eggw}.py`, `src/atc_sim/render/radar.py`, `src/atc_sim/app.py` — HIGH confidence, direct source reads of this project's own already-established, already-tested code and prior research

### Secondary (MEDIUM confidence)
- [SKYbrary Aviation Safety — "Rate of Turn"](https://skybrary.aero/articles/rate-turn) and [CFI Library — "Rate of Turn"](https://library.cfi.fyi/Library/Aerodynamics+and+Flight+Maneuvers/Rate+of+Turn) — cross-checked, agree on the `1091 × tan(bank) / speed` formula and the rate-1/bank-angle approximation — MEDIUM
- [Embraer official E175 spec PDF](https://www.embraer.com/media/o3sjzbwl/e175_spec.pdf) plus [globalair.com](https://www.globalair.com/aircraft-specifications/embraer/embraer-e-175-specifications/1364) and [flightschoolusa.com](https://www.flightschoolusa.com/the-emb-175-performance-and-features/) — cross-checked across an official manufacturer source and two secondary spec sites — LOW-MEDIUM
- [ATR official 72-600 factsheet PDF](https://www.atr-aircraft.com/wp-content/uploads/2020/07/Factsheets_-_ATR_72-600.pdf) plus [aerocorner.com](https://aerocorner.com/aircraft/atr-72-600/) — official manufacturer factsheet cross-checked against a secondary spec aggregator — LOW-MEDIUM

### Tertiary (LOW confidence)
- [planephd.com](https://planephd.com/wizard/details/1108/BOEING-737-800-specifications-performance-operating-cost-valuation), [b737.org.uk "Rules of Thumb"](http://www.b737.org.uk/rulesofthumb.htm), [aircraftinvestigation.info](https://www.aircraftinvestigation.info/airplanes/Boeing_737-800.html) — Boeing 737-800 performance figures, aggregated across enthusiast/spec-aggregator sites, no single authoritative primary source located this session — LOW
- [jetav.com](https://jetav.com/cessna-citation-cj2-performance-specs/), [code7700.com](https://code7700.com/case_study_cessna_cj2_n380cr.htm) — Cessna Citation CJ2 performance figures — LOW
- Multiple independent, unlinked-in-final-answer web sources on the "descent_fpm ≈ groundspeed_kt × 5" 3°-glidepath rule of thumb, and on typical taxi speeds (30kt max/20kt normal/10-15kt congested) — general aviation web consensus, no single authoritative citation — LOW
- Python hand-rolled FSM pattern and initial Embraer E170/E175 figures — first-pass web search calls returned "unavailable" and fell back to training-knowledge synthesis; the FSM pattern claim is fully superseded by this project's own already-established `ARCHITECTURE.md` Pattern 2 (no new information), and the Embraer figures were subsequently re-verified with a successful follow-up search (see Secondary above) — LOW for the initial fallback content specifically

## Metadata

**Confidence breakdown:**
- Standard stack (aircraft fleet numeric values): LOW-MEDIUM — no BADA-grade or manufacturer-flight-manual-grade source was available this session; values are aggregated from enthusiast/spec-aggregator sites and manufacturer marketing factsheets, then further adapted (terminal-speed capping) for in-sim use, which is itself an unsourced simplification decision. Explicitly acceptable per CONTEXT.md ("not BADA-table... simplified"), but the planner/implementer should treat the exact numbers as tunable defaults, not verified facts.
- Architecture (FSM, procedure-following, module structure): HIGH — directly extends this project's own already-established, already-implemented architecture (`ARCHITECTURE.md` Patterns 2-3, existing `navdata/geo.py` and `sim/` module conventions), verified by direct reads of the current codebase this session.
- Pitfalls: HIGH — every pitfall in this document is either a direct, sourced re-application of this project's own already-documented `PITFALLS.md` (Pitfall 4, 6, 7, 11) to this phase's specific real navdata, or a newly-identified risk (the "3 distinct types" demo-rotation gap, "removal is not a phase" gap) grounded in direct comparison of CONTEXT.md's decisions against the roadmap's literal success-criteria wording.

**Research date:** 2026-07-06
**Valid until:** Indefinite for architecture/FSM/pitfalls sections (stable, internally-sourced project patterns). ~90 days for the aircraft performance numeric values if re-sourcing against a more authoritative source (e.g. an actual flight manual or BADA-lite dataset) becomes worthwhile — unlikely to be needed given the project's explicit "simplified, not BADA" constraint.

---
*Phase: 3-aircraft-performance-flight-phase-fsm-procedure-following*
*Researched: 2026-07-06*
