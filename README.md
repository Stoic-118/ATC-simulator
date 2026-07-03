# ATC Simulator

A full-fidelity, single-airport air traffic control simulator — a native Python + Pygame desktop application (not a CLI, not a browser app). The player works one combined Approach + Tower position over a single real airport, controlling performance-modeled aircraft on a vector-style radar display with real ATC phraseology and separation alerting.

## Core Value

The player can work a full session — launch an aircraft off a SID, land another off the ILS, entirely through their own instructions — and the sim never lies about separation.

## v1 Scope

- **Airport:** London Luton (EGGW), runway 26 only — one SID, one STAR, real ILS parameters (CAT I)
- **Traffic:** IFR only, driven by a hand-authored scripted scenario file
- **Aircraft:** Simplified per-type performance profiles (climb/descent rate, speed envelope, turn rate) across a small fleet of 3–5 types
- **Control:** Click-to-select + command panel (heading, altitude, speed, direct-to-fix, cleared approach, cleared for takeoff/landing)
- **Separation:** Standard vertical/horizontal minima checked every tick, surfaced as STCA-style alerts — never auto-enforced
- **Comms:** ICAO-style instruction and pilot-readback text log

See [`.planning/PROJECT.md`](.planning/PROJECT.md) for full context, decisions, and out-of-scope boundaries, and [`.planning/REQUIREMENTS.md`](.planning/REQUIREMENTS.md) for the complete requirements list.

## Stack

- Python 3.12+
- [pygame-ce](https://github.com/pygame-community/pygame-ce) for the window, rendering loop, and input
- [pygame_gui](https://pyga.me/) for UI panels (flight strip bay, comms log, frequency box)
- Fixed-timestep accumulator loop for the simulation clock, decoupled from the render loop
- [geographiclib](https://geographiclib.sourceforge.io/) for great-circle navigation math
- [Pydantic](https://docs.pydantic.dev/) for aircraft, procedure, and navdata models

See [`.planning/research/STACK.md`](.planning/research/STACK.md) for the full stack rationale.

## Installation

> **Not available yet.** This project is still in the planning stage — Phase 1 (the walking skeleton) hasn't been built, so there's no package, entry point, or dependency list to install yet.
>
> Once Phase 1 ships, this section will cover:
> - Cloning the repo and setting up a Python 3.12+ virtual environment
> - Installing dependencies (`pygame-ce`, `pygame_gui`, `pydantic`, `geographiclib`)
> - Running the simulator and loading a scenario
>
> Track progress in [`.planning/ROADMAP.md`](.planning/ROADMAP.md).

## Roadmap

Built as a vertical MVP slice across 7 phases, starting from a walking skeleton (sim clock + bare radar render loop) and building up through navdata, aircraft performance/procedures, instruction handling, separation detection, scenario loading, and the comms log.

See [`.planning/ROADMAP.md`](.planning/ROADMAP.md) for full phase details and progress.

## Status

Planning complete — implementation not yet started. This project is managed with [GSD](https://github.com/opengsd/gsd-core); see `.planning/` for all project artifacts.
