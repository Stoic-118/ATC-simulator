# Requirements: ATC Simulator

**Defined:** 2026-07-03
**Core Value:** The player can work a full session — launch an aircraft off a SID, land another off the ILS, entirely through their own instructions — and the sim never lies about separation.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Simulation Core

- [x] **CORE-01**: Simulation advances on a fixed-timestep clock (1-4Hz) fully decoupled from the 60fps render loop
- [x] **CORE-02**: Sim clock caps the maximum ticks processed per render frame, so a stall degrades gracefully instead of freezing or jumping ("spiral of death")
- [x] **CORE-03**: Render layer reads current aircraft state each frame without ever mutating it

### Radar Display

- [ ] **RADAR-01**: Player views a plan-view radar canvas with range rings and sector reference lines
- [ ] **RADAR-02**: Each aircraft renders as a datablock showing callsign, altitude, speed, and assigned instruction info
- [x] **RADAR-03**: Each aircraft shows a heading vector line and recent trail history dots
- [ ] **RADAR-04**: Radar canvas uses a cosine-corrected lat/lon-to-pixel projection shared with the separation-check math, so displayed positions never visually disagree with enforced separation

### Navdata

- [ ] **NAV-01**: Airport navdata models London Luton (EGGW), runway 26 only — threshold, heading, and ILS parameters (localizer course, 3.0° glideslope, CAT I decision height)
- [ ] **NAV-02**: One SID and one STAR for runway 26 are modeled with named fixes/waypoints and altitude/speed restrictions
- [ ] **NAV-03**: Navdata models distinguish heading/course/track/bearing as separate named fields and apply magnetic variation at exactly one defined boundary

### Aircraft Performance & State

- [ ] **PERF-01**: Each aircraft uses a simplified per-type performance profile (climb/descent rate, speed envelope, turn rate as a function of bank angle and groundspeed), drawn from a fleet of 3-5 aircraft types
- [ ] **PERF-02**: Aircraft flight phase is modeled as an explicit state machine (pushback/taxi, departure roll, climb, en-route, descent, approach, ILS capture, landed, taxi-in)
- [ ] **PERF-03**: Departure aircraft spawn at a stand, taxi via a timer abstraction (no ground pathfinding), then take off and climb via the SID
- [ ] **PERF-04**: Arrival aircraft spawn airborne at the STAR entry fix with realistic initial altitude/speed, descend toward the airport, and taxi in (abstracted) after landing

### Procedure Following

- [ ] **PROC-01**: Aircraft cleared via the SID/STAR follow procedure legs and restrictions automatically
- [ ] **PROC-02**: Vectoring instructions (heading/altitude/speed) override procedure-derived targets as a layer on top of procedure-following, not a separate movement code path
- [ ] **PROC-03**: Aircraft can capture the ILS (localizer then glideslope) from a vectored or procedural approach, with lateral guidance mode modeled as a single well-defined state rather than independent flags

### Instructions

- [ ] **INST-01**: Player can click an aircraft on the radar to select it
- [ ] **INST-02**: Player can issue heading, altitude/level, speed, direct-to-fix, cleared-approach, and cleared-for-takeoff/landing instructions via a command panel
- [ ] **INST-03**: Issued instructions take effect at the next sim tick boundary, never mid-tick

### Separation & Conflict Alerting

- [ ] **SEP-01**: Sim checks standard vertical (1000ft below FL290) and horizontal (5nm) separation minima between every aircraft pair each tick
- [ ] **SEP-02**: Sim surfaces separation violations as STCA-style visual (and optional audio) conflict alerts rather than blocking the instruction that caused them
- [ ] **SEP-03**: Separation checking reuses the same projection/geodesic math as the radar display

### Comms & Phraseology

- [ ] **COMM-01**: Player-issued instructions render as ICAO-style phraseology text in a comms/instruction log
- [ ] **COMM-02**: Each instruction is followed by a matching simulated pilot readback in the comms log

### Scenario Loading

- [ ] **SCEN-01**: Player can load a hand-authored scripted scenario file (aircraft, type, spawn time/point, flight plan) that drives all traffic for a session
- [ ] **SCEN-02**: Scenario file contents are validated against a Pydantic schema before a session starts

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Traffic & Airspace

- **VFR-01**: VFR traffic support (circuits, downwind/base/final, go-arounds, request-based rather than instruction-based behavior)
- **RWY-01**: Multiple runways/directions and wind-driven runway configuration switching
- **WAKE-01**: Wake turbulence / separation categories (Light/Medium/Heavy) affecting minimum spacing

### Simulation Depth

- **GND-01**: Real ground movement/taxiway simulation (pathfinding), replacing the timer-based taxi abstraction
- **TRAF-01**: Randomized/procedural traffic generator, multiple SIDs/STARs, broader fleet variety
- **APP-01**: Go-arounds/missed approaches
- **SEP-04**: Predictive/lookahead conflict alerting (trajectory-based STCA), beyond v1's current-instant checking

### Controller Interaction

- **INST-04**: Typed shorthand command entry alongside click+panel
- **INST-05**: Hold-short instructions and frequency handoff modelling

### Packaging

- **PKG-01**: PyInstaller packaging into a standalone Windows .exe

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Live/real AIRAC data ingestion | Hand-authored navdata is sufficient for a single fixed airport and avoids licensing/currency concerns |
| Multiplayer/pilot client | Pilot side is simulated AI by design — no networked pilot role planned |
| Voice recognition / real audio synthesis | Confirmed low realism payoff relative to complexity (Tower!3D reviews call required phrasing "clunky"); phraseology is text-rendered only |
| Multi-airport handoffs / en-route sectors beyond local airspace | One combined controller position at one airport is the entire scope of this project |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CORE-01 | Phase 1 | Complete |
| CORE-02 | Phase 1 | Complete |
| CORE-03 | Phase 1 | Complete |
| RADAR-01 | Phase 1 | Pending |
| RADAR-03 | Phase 1 | Complete |
| NAV-01 | Phase 2 | Pending |
| NAV-02 | Phase 2 | Pending |
| NAV-03 | Phase 2 | Pending |
| RADAR-04 | Phase 2 | Pending |
| PERF-01 | Phase 3 | Pending |
| PERF-02 | Phase 3 | Pending |
| PERF-03 | Phase 3 | Pending |
| PERF-04 | Phase 3 | Pending |
| PROC-01 | Phase 3 | Pending |
| INST-01 | Phase 4 | Pending |
| INST-02 | Phase 4 | Pending |
| INST-03 | Phase 4 | Pending |
| PROC-02 | Phase 4 | Pending |
| PROC-03 | Phase 4 | Pending |
| RADAR-02 | Phase 4 | Pending |
| SEP-01 | Phase 5 | Pending |
| SEP-02 | Phase 5 | Pending |
| SEP-03 | Phase 5 | Pending |
| SCEN-01 | Phase 6 | Pending |
| SCEN-02 | Phase 6 | Pending |
| COMM-01 | Phase 7 | Pending |
| COMM-02 | Phase 7 | Pending |

**Coverage:**

- v1 requirements: 27 total
- Mapped to phases: 27
- Unmapped: 0 ✓

---
*Requirements defined: 2026-07-03*
*Last updated: 2026-07-03 after roadmap creation (7 phases, full coverage)*
