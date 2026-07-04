# Walking Skeleton — ATC Simulator

**Phase:** 1
**Generated:** 2026-07-04

## Capability Proven End-to-End

> One sentence: the smallest user-visible capability that exercises the full stack.

A single hardcoded aircraft glides smoothly across a bare radar canvas (range rings + sector lines) driven entirely by a fixed-timestep 2Hz sim clock whose motion is provably independent of the 60fps render loop — proving the project's single riskiest architectural bet (sim/render decoupling) before any domain logic exists.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Language / runtime | Python 3.12+ (3.14.4 on dev machine) | Locked in PROJECT.md/CLAUDE.md; modern typing + `match`. |
| Rendering / windowing | pygame-ce `>=2.5,<3.0` | Actively maintained fork; `pygame.draw.*`/`pygame.font` map directly onto radar primitives; `import pygame` superset. |
| Data modeling | Pydantic v2 `>=2.13,<3.0` | `Aircraft` state model + `frozen=True` `AircraftSnapshot` for interpolation; validation at boundaries only. |
| Sim/render decoupling | Single-threaded fixed-timestep accumulator loop (Gaffer On Games "Fix Your Timestep!"), **2Hz sim tick, 5 max ticks/frame, 0.25s frame-time clamp** | GIL makes threads/asyncio pointless for CPU-bound single-process sim; accumulator is the canonical pattern and a pattern (not a dependency). |
| Smooth rendering | Previous/current frozen-snapshot interpolation (`alpha = accumulator / tick_dt`); position lerp + shortest-path heading lerp | 2Hz tick = 30 render frames/tick at 60fps; without interpolation the dot visibly teleports every 500ms. |
| Test runner | pytest `>=8.0`, headless (no display) for CORE-01/02/03 + RADAR-03 heading math | Sim core is pure; accumulator + interpolation are fast, deterministic unit tests with zero window. |
| Directory layout | src-layout `src/atc_sim/` with a hard `sim/` (no pygame) vs `render/` (pygame-only) module boundary; `app.py` the only seam | `sim/` must stay headlessly testable forever — the single most important project-wide rule. |
| Packaging | `pyproject.toml` (PEP 621), `[project.scripts] atc-sim`, `[tool.setuptools.packages.find] where=["src"]` | No `setup.py`; editable install (`pip install -e ".[dev]"`) makes `import atc_sim` and the `atc-sim` launcher work. |
| Geodesy library | **Deferred** — not in Phase 1 | Phase 1 uses plain local x/y canvas coordinates (D-02, no real navdata). geographiclib arrives in Phase 2. |

## Stack Touched in Phase 1

- [x] Project scaffold (pyproject.toml, src-layout package, pytest config, venv + pip bootstrap)
- [x] "Routing" equivalent — the `atc-sim` entry point / `python -m atc_sim.app` launch path
- [x] "Data layer" equivalent — authoritative `Aircraft` Pydantic state mutated only inside a sim tick (one real read/write per tick)
- [x] UI — one interactive real-time canvas: radar rings/sector lines + a moving aircraft dot/heading vector/trail wired to the sim state
- [x] Deployment — documented local full-stack run command in README (venv → install → launch), replacing the placeholder

## Out of Scope (Deferred to Later Slices)

> Anything that is *not* in the skeleton. Be explicit — prevents future phases re-litigating Phase 1's minimalism.

- Real EGGW navdata, lat/lon projection, cosine correction (Phase 2 — NAV-*/RADAR-04)
- Heading/course/track/bearing as distinct fields, magnetic variation (Phase 2 — NAV-03; only `heading_deg` exists now)
- Aircraft performance profiles, flight-phase FSM, SID/STAR following (Phase 3 — PERF-*/PROC-01)
- Click-to-select, command panel, vectoring, ILS capture, datablocks (Phase 4 — INST-*/PROC-02/03/RADAR-02)
- Separation/conflict detection (Phase 5 — SEP-*)
- Scenario file loading + Pydantic schema validation of untrusted files (Phase 6 — SCEN-*)
- Comms/phraseology log (Phase 7 — COMM-*)
- Window resize/scaling (D-03 — fixed 1280×800 only)
- Multiple SIDs/STARs / multi-aircraft procedure selection (v2 backlog `TRAF-01`, per D-04)
- `pygame_gui` panel widgets (Phase 4), on-canvas text/fonts (Phase 4/7)

## Subsequent Slice Plan

Each later phase adds one vertical slice on top of this skeleton **without altering** its architectural decisions (the accumulator loop, the `sim/`↔`render/` boundary, the snapshot-interpolation seam, the D-01 color palette):

- Phase 2: Real EGGW runway-26 navdata + cosine-corrected lat/lon→pixel projection on the radar
- Phase 3: Per-type performance profiles + flight-phase FSM → aircraft fly a full departure/arrival via SID/STAR
- Phase 4: Click-select + command panel; vectoring overrides procedure as a layer; ILS capture as one state
- Phase 5: Per-tick pairwise separation checking → STCA-style alerts (reusing the display's projection math)
- Phase 6: Schema-validated scripted scenario file drives all traffic
- Phase 7: ICAO-style comms/phraseology log with simulated readbacks
