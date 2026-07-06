# ATC Simulator

## What This Is

A full-fidelity, single-airport air traffic control simulator: a native Python + Pygame desktop application (not a CLI, not a browser app) where the player works one combined Approach + Tower position. Aircraft are performance-modeled and rendered on a vector-style radar display; the player issues real ATC instructions and gets phraseology-accurate readbacks, with separation violations surfaced as alerts rather than silently blocked.

## Core Value

The player can work a full session — launch an aircraft off a SID, land another off the ILS, entirely through their own instructions — and the sim never lies about separation.

## Requirements

### Validated

- [x] Native Pygame window with its own rendering loop, decoupled from a fixed-timestep sim clock (sim tick 1–4Hz driving aircraft state; render loop at 60fps) — Validated in Phase 1: Walking Skeleton — Sim Clock & Radar Render Loop
- [x] Radar canvas: range rings, sector lines, heading vector line, trail dots — Validated in Phase 1: Walking Skeleton — Sim Clock & Radar Render Loop
- [x] Navdata for one real airport (London Luton, EGGW), one runway direction (25) only — no runway changes, no wind-driven configuration switching — Validated in Phase 2: Navdata & Coordinate Projection
- [x] One SID and one STAR, off/into runway 25, with realistic ILS parameters (localizer course, 3.0° glideslope, CAT I decision height) — Validated in Phase 2: Navdata & Coordinate Projection (procedure restrictions modeled as data; ILS localizer/glideslope parameters modeled — on-screen restriction display deferred to Phase 4)
- [x] geographiclib for great-circle distance/bearing and lat/lon math — Validated in Phase 2: Navdata & Coordinate Projection (shared cosine-corrected projection built directly on `geographiclib.Geodesic.WGS84.Inverse()`; pyproj not used)
- [x] Pydantic models for aircraft, procedure, and navdata — Validated (aircraft in Phase 1; procedure and navdata in Phase 2), all as frozen/validated Pydantic v2 models per the project's established conventions
- [x] Simplified per-aircraft-type performance profiles (climb/descent rate, speed envelope, turn rate as a function of bank angle and groundspeed) across a fleet of 4 aircraft types (Boeing 737-800, Embraer E175, ATR 72-600, Cessna Citation CJ2+) — Validated in Phase 3: Aircraft Performance, Flight-Phase FSM & Procedure Following
- [x] Explicit flight-phase state machine (taxi-out, departure roll, climb, en-route, descent, approach, landed, taxi-in) with a legal-transitions table rejecting any illegal state change — Validated in Phase 3 (ILS localizer/glideslope capture as a distinct guidance state is separately scoped to Phase 4, per the PROC-03 requirement)
- [x] Departure flow: spawn at stand → abstracted taxi (timer-based, no ground pathfinding) → takeoff → climb via the SID → autonomous removal from active traffic — Validated in Phase 3
- [x] Arrival flow (procedural): spawn airborne at the STAR entry fix with realistic initial altitude/speed → autonomous procedural descent following STAR legs/restrictions → landing → abstracted taxi-in → removal from active traffic — Validated in Phase 3 (vectored descent and ILS capture remain Phase 4 scope, per PROC-02/PROC-03)
- [x] Automatic SID/STAR leg and altitude/speed-restriction following, including restriction look-ahead so unrestricted legs target the next real restriction instead of holding level — Validated in Phase 3

### Active

- [ ] Radar canvas: aircraft datablocks (callsign/altitude/speed/assigned info) — deferred to Phase 4 (needs instructions to exist first for "assigned info" to be meaningful)
- [ ] IFR traffic only for v1 (VFR deferred to v2+)
- [ ] Vectoring instructions (heading/altitude/speed) that override procedure-following as a layer on top of it, plus ILS capture (localizer then glideslope) modeled as a single well-defined guidance state reachable via vectors or procedural continuation
- [ ] Core instruction set: heading, altitude/level, speed, direct-to-fix, cleared approach, cleared for takeoff/landing
- [ ] Click + command-panel input: click an aircraft to select it, issue instructions via panel controls (mouse-first, console-style)
- [ ] Separation checking: standard vertical (1000ft below FL290) and horizontal (5nm) minima, surfaced as STCA-style visual/audio conflict alerts — not auto-enforced
- [ ] Text-rendered phraseology log: controller-issued instructions and matching simulated pilot readbacks
- [ ] Scripted scenario file (hand-authored spawn list: aircraft, type, spawn time/point, flight plan) drives all v1 traffic — no randomized generator yet

### Out of Scope

- VFR traffic entirely (circuits, downwind/base/final, go-arounds, request-based behavior) — biggest single architectural addition (separate state machine + interaction model); deferred to v2+
- Multiple runways/directions and wind-driven runway selection — v1 proves the loop on one direction first
- Wake turbulence / separation categories (Light/Medium/Heavy) — adds spacing-rule complexity not needed to prove the core loop
- Real ground movement/taxiway simulation — taxi is a timer abstraction in v1, not a simulated ground graph
- Randomized/procedural traffic generator, multiple SIDs/STARs, broader fleet variety — v1 needs deterministic, repeatable runs for debugging separation logic
- Go-arounds/missed approaches — adds a recovery branch to the approach state machine not needed for the core loop
- Frequency handoff modelling and hold-short instructions — meaningless with one combined controller position
- PyInstaller packaging into a standalone .exe — later nice-to-have, not blocking early development ("my machine only" for now)
- Live/real AIRAC data ingestion — hand-authored navdata is sufficient and avoids licensing/currency concerns
- Multiplayer/pilot client, voice recognition, or real audio synthesis — pilot side is simulated AI; phraseology is text-rendered only
- Multi-airport handoffs or en-route sectors beyond this airport's local airspace

## Context

- **Motivation**: Personal deep-dive project. The goal is to build something ambitious and learn simulation/systems design along the way — not a product for external users (yet), so no Business Context section.
- **Stack decisions** (see Constraints): Python 3.12+, Pygame for window/rendering/input, pygame_gui or hand-rolled UI for panels (flight strip bay, comms/instruction log, frequency box), asyncio or fixed-timestep loop for the sim clock, geographiclib/pyproj for nav math, Pydantic for data models. No HTML/web rendering anywhere in the stack.
- **Airport**: London Luton (EGGW), runway 25 — real ILS CAT I approach, real fix/procedure naming conventions, simplified to one direction/one SID/one STAR for v1. Navdata is hand-authored, not sourced from live AIRAC. (Note: this runway was redesignated from "26" to "25" in a May 2020 magnetic-drift realignment — same physical runway/threshold/ILS, relabeled identifier. See Key Decisions.)
- **Platform**: Developed and run on the user's own machine for now. Cross-platform Pygame behavior is a bonus, not a driver; PyInstaller .exe packaging is an explicit later phase.
- **Timeline**: Open-ended — no external deadline. Prioritize building it right over building it fast.
- **v1 bar** (from questioning): a full session where an aircraft launches, flies the SID, and another lands off the ILS, entirely through the player's own instructions, without the sim lying about separation. Everything that doesn't serve proving that loop is deferred.

## Constraints

- **Tech stack**: Python 3.12+, Pygame, pygame_gui/hand-rolled UI, asyncio/fixed-timestep sim clock, geographiclib or pyproj, Pydantic — Why: explicit user decision; must be a native desktop app with its own rendering loop, no browser/HTML anywhere in the stack
- **Scope**: single airport (EGGW), single runway direction (25), IFR only for v1 — Why: keeps procedure/ILS logic surface area small enough to validate the core instruction-and-separation loop before expanding
- **Fidelity**: simplified per-aircraft-type performance profiles, not BADA-style tables or full physics — Why: feels real without a heavy modeling lift blocking early phases
- **Traffic generation**: scripted scenario file, not a randomized generator, for v1 — Why: repeatable, deterministic runs are needed while separation/instruction logic is still being debugged
- **Separation enforcement**: alerts (STCA-style), not automatic blocking — Why: matches real-world ATC — the controller decides, the sim only warns

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Click + command-panel input over typed shorthand | Mouse-first matches real radar consoles; typed shorthand could be added later as an accelerator | — Pending |
| Simplified performance profiles over BADA tables or full physics | Feels real without blocking v1 on heavy aircraft-performance modeling | Validated in Phase 3 (4-type FLEET, terminal-area speeds capped rather than each type's Mach cruise speed) |
| Scripted scenario file over randomized traffic generator (v1) | Debugging separation/instruction logic needs repeatable, deterministic runs | — Pending (Phase 3 used a 2-aircraft looping demo harness as an interim stand-in; real scenario file is Phase 6) |
| Real airport (London Luton, EGGW, runway 25) over fictional | Real-world-plausible navdata/ILS parameters without live AIRAC complexity | Validated in Phase 2 |
| One runway direction, one SID, one STAR for v1 | Minimizes procedure/ILS logic surface area to prove the core loop fast | Validated in Phase 2 (OLNEY 2B SID, DET 2A STAR); Phase 3 flew both procedures autonomously end-to-end |
| Runway identifier updated "26" → "25" (Phase 2 research) | EGGW's runway was redesignated 08/26 → 07/25 in a May 2020 magnetic-drift realignment — same physical runway/threshold/ILS, relabeled identifier. Renamed throughout for real-world accuracy rather than keeping the outdated label, consistent with "the sim never lies." | Validated in Phase 2 research |
| IFR-only for v1, VFR deferred to v2+ | VFR is a second state machine and interaction model — the single biggest cut to reach v1 faster | — Pending |
| Separation surfaced as alerts, not auto-enforced | A controller game with no separation consequence isn't an ATC game — but the controller must stay in control | — Pending |
| 8-state flight-phase enum with no ILS-capture sub-states in Phase 3 | Roadmap's Phase 3 success criteria name exactly 8 states (taxi through taxi-in); localizer/glideslope capture is a guidance-mode concern owned by PROC-03, explicitly deferred to Phase 4 so it can be built once against both vectored and procedural approach paths rather than twice | Validated in Phase 3 |
| Two-hardcoded-aircraft looping demo harness with fleet type-rotation, as a stand-in for the real scenario loader | Phase 6 owns the real scripted scenario file; Phase 3 needed *some* traffic source to prove autonomous flight, and rotation across all 4 fleet types was needed to satisfy "≥3 types visibly differentiated" with only 2 aircraft airborne at once | Validated in Phase 3 |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-07-06 after Phase 3 completion*
