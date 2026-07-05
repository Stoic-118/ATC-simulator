# Roadmap: ATC Simulator

## Overview

The build starts with the single riskiest architectural bet — a fixed-timestep sim clock fully decoupled from the render loop — proven on a bare radar canvas before any domain logic exists. From there, real navdata and a cosine-corrected projection give the display and (later) separation math a shared, trustworthy geometry. Aircraft performance profiles, an explicit flight-phase state machine, and procedure-following then let traffic fly a full departure and arrival autonomously. Only once that autonomous loop works does the player get control: click-to-select, a command panel, vectoring that overrides procedures as a layer rather than a fork, and ILS capture modeled as one well-defined guidance state. Separation/conflict alerting is deliberately sequenced after real instructions exist, so it can be proven against player-created conflicts, not just scripted ones. A scripted scenario loader then formalizes repeatable traffic generation on top of everything already working, and the phraseology/readback log — purely observational, zero effect on sim state — closes out the v1 loop last. By the end, a player can run a full session: launch an aircraft off the SID, land another off the ILS, entirely through their own instructions, with separation violations surfaced honestly rather than hidden.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Walking Skeleton — Sim Clock & Radar Render Loop** - A fixed-timestep sim clock drives one aircraft, decoupled from a 60fps render loop, on a bare radar canvas (completed 2026-07-05)
- [ ] **Phase 2: Navdata & Coordinate Projection** - Real EGGW runway-26 navdata and a cosine-corrected lat/lon-to-pixel projection shared with future separation math
- [ ] **Phase 3: Aircraft Performance, Flight-Phase FSM & Procedure Following** - Typed performance profiles and an explicit phase state machine let aircraft fly a full departure/arrival via the SID/STAR unattended
- [ ] **Phase 4: Instruction Handling — Click, Panel, Vectoring & ILS Capture** - Player selects aircraft and issues real ATC instructions that override procedure-following; ILS capture is one well-defined guidance state
- [ ] **Phase 5: Separation & Conflict Detection (STCA-style)** - Every aircraft pair is checked each tick against standard minima and violations surface as alerts, never blocks
- [ ] **Phase 6: Scripted Scenario Loader** - A hand-authored, schema-validated scenario file drives an entire session's traffic
- [ ] **Phase 7: Comms & Phraseology Log** - Player instructions and simulated pilot readbacks render as ICAO-style text in a comms log

## Phase Details

### Phase 1: Walking Skeleton — Sim Clock & Radar Render Loop

**Goal**: A fixed-timestep sim clock drives aircraft motion fully decoupled from the render loop, with a bare radar canvas showing range rings, sector lines, and a moving aircraft with heading vector and trail.
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: CORE-01, CORE-02, CORE-03, RADAR-01, RADAR-03
**Success Criteria** (what must be TRUE):

  1. The sim advances aircraft state on a fixed 1-4Hz tick that runs independently of render frame rate — changing render fps does not change aircraft speed
  2. Deliberately stalling a render frame causes the sim to catch up gracefully over subsequent ticks rather than freezing or jumping instantly to a far-future position
  3. The radar canvas displays range rings and sector reference lines as a static background layer
  4. A moving aircraft renders as a dot with a heading vector line and a trail of recent position dots, and its on-screen position only ever reflects sim-tick state — never a value altered by the render pass itself
  5. README.md's Installation section is updated with real setup/run instructions (venv, dependency install, how to launch the walking skeleton), replacing the "not available yet" placeholder

**Plans**: 5/5 plans complete
**Wave 1**

- [x] 01-01-PLAN.md — Scaffold src-layout package, pyproject.toml, venv/deps, sim/render boundary guard

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02-PLAN.md — Fixed-timestep accumulator sim clock (SimClock), TDD (CORE-01/02)
- [x] 01-03-PLAN.md — Aircraft model + snapshot/interpolation math, TDD (CORE-03, RADAR-03)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 01-04-PLAN.md — Radar canvas (rings/sector lines/dot/vector/trail) + app.py main loop (RADAR-01/03)

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 01-05-PLAN.md — README install/run instructions + walking-skeleton run verification

### Phase 2: Navdata & Coordinate Projection

**Goal**: The radar displays real EGGW navdata (runway 26, one SID, one STAR) through a cosine-corrected lat/lon-to-pixel projection shared with the future separation-check math, with heading/course/track/bearing modeled as distinct fields.
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: NAV-01, NAV-02, NAV-03, RADAR-04
**Success Criteria** (what must be TRUE):

  1. The radar canvas shows the real EGGW runway 26 threshold and extended centerline, correctly positioned by lat/lon
  2. One SID's and one STAR's named fixes/waypoints appear on the radar at their correct real-world positions, each with its modeled altitude/speed restrictions
  3. Range rings render as true circles (not ellipses) at any radar pan/zoom, confirming the cosine-corrected projection
  4. Heading, course, bearing, and track are distinct named fields with magnetic variation applied at exactly one defined point — displayed procedure courses match real-world EGGW SID/STAR charted values

**Plans**: TBD

### Phase 3: Aircraft Performance, Flight-Phase FSM & Procedure Following

**Goal**: Aircraft use type-specific performance profiles and an explicit flight-phase state machine to autonomously fly a full departure or arrival, including following the SID/STAR's legs and restrictions, without any player input.
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: PERF-01, PERF-02, PERF-03, PERF-04, PROC-01
**Success Criteria** (what must be TRUE):

  1. At least 3 distinct aircraft types are visibly differentiated by climb/descent rate, speed envelope, and turn rate during flight
  2. A departure aircraft progresses automatically end to end: spawns at a stand, taxis (timer abstraction), takes off, and climbs out via the SID's legs and restrictions
  3. An arrival aircraft spawns airborne at the STAR entry fix with a realistic initial altitude/speed and automatically flies the STAR's legs/restrictions toward the airport
  4. Aircraft flight-phase transitions (taxi, departure roll, climb, en-route, descent, approach, landed, taxi-in) are always legal — no skipped or contradictory phase states are ever observed
  5. After landing, an arrival aircraft taxis in (abstracted) and is removed from active traffic

**Plans**: TBD

### Phase 4: Instruction Handling — Click, Panel, Vectoring & ILS Capture

**Goal**: The player can select any aircraft and issue real ATC instructions via a command panel; those instructions override procedure-following as a layer on top of it rather than a separate movement path, and aircraft reach ILS-established guidance through one well-defined state regardless of how they got there.
**Mode:** mvp
**Depends on**: Phase 3
**Requirements**: INST-01, INST-02, INST-03, PROC-02, PROC-03, RADAR-02
**Success Criteria** (what must be TRUE):

  1. Player can click an aircraft on the radar to select it, with clear visual selection feedback
  2. Player can issue heading, altitude/level, speed, direct-to-fix, cleared-approach, and cleared-for-takeoff/landing instructions via a command panel
  3. Each aircraft's datablock shows its callsign, altitude, speed, and currently assigned instruction
  4. Issuing a heading, altitude, or speed instruction to a procedure-following aircraft immediately redirects it to the new target, overriding rather than replacing the underlying procedure state
  5. An aircraft reaches ILS-established guidance (localizer then glideslope) whether it arrived there via vectors or by continuing the procedural approach — always exactly one well-defined guidance state, never ambiguous
  6. An instruction issued between ticks visibly takes effect only at the next tick boundary, never causing a mid-tick jump

**Plans**: TBD

### Phase 5: Separation & Conflict Detection (STCA-style)

**Goal**: The sim checks every aircraft pair each tick against standard vertical and horizontal separation minima and surfaces violations as alerts without ever blocking the instruction that caused them.
**Mode:** mvp
**Depends on**: Phase 4
**Requirements**: SEP-01, SEP-02, SEP-03
**Success Criteria** (what must be TRUE):

  1. Player can, through their own instructions, bring two aircraft within 5nm horizontally (with insufficient vertical separation) and see a visual STCA-style conflict alert appear on both aircraft
  2. Player can, through their own instructions, bring two aircraft within 1000ft vertically below FL290 with insufficient horizontal separation and see the same style of alert
  3. The instruction that causes a separation violation is never blocked — the aircraft complies and the alert simply surfaces the resulting conflict
  4. A pair of aircraft that appear visually close on the radar always corresponds to an actual alert state (and vice versa), because separation checking reuses the same projection/geodesic math as the display

**Plans**: TBD

### Phase 6: Scripted Scenario Loader

**Goal**: A hand-authored, schema-validated scenario file can drive an entire session's traffic — spawning aircraft with specified type, time/point, and flight plan — without any manual spawning.
**Mode:** mvp
**Depends on**: Phase 5
**Requirements**: SCEN-01, SCEN-02
**Success Criteria** (what must be TRUE):

  1. Player can launch a session by loading a hand-authored scenario file that spawns aircraft with specified type, spawn time/point, and flight plan
  2. An invalid or malformed scenario file is rejected with a validation error before the session starts, rather than crashing or silently misbehaving mid-session
  3. A full scripted scenario can drive an entire session end to end: at least one departure launches off the SID and at least one arrival lands off the ILS, entirely from the scenario file

**Plans**: TBD

### Phase 7: Comms & Phraseology Log

**Goal**: Player-issued instructions and their matching simulated pilot readbacks render as ICAO-style phraseology text in a comms/instruction log, closing out the full v1 controller loop.
**Mode:** mvp
**Depends on**: Phase 6
**Requirements**: COMM-01, COMM-02
**Success Criteria** (what must be TRUE):

  1. Every instruction the player issues appears in a comms log rendered as ICAO-style phraseology text
  2. Every logged instruction is immediately followed by a matching simulated pilot readback in the same log
  3. A player can run a full session — launch an aircraft off the SID, land another off the ILS — and read back the entire exchange afterward from the comms log alone

**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Walking Skeleton — Sim Clock & Radar Render Loop | 5/5 | Complete   | 2026-07-05 |
| 2. Navdata & Coordinate Projection | 0/TBD | Not started | - |
| 3. Aircraft Performance, Flight-Phase FSM & Procedure Following | 0/TBD | Not started | - |
| 4. Instruction Handling — Click, Panel, Vectoring & ILS Capture | 0/TBD | Not started | - |
| 5. Separation & Conflict Detection (STCA-style) | 0/TBD | Not started | - |
| 6. Scripted Scenario Loader | 0/TBD | Not started | - |
| 7. Comms & Phraseology Log | 0/TBD | Not started | - |
