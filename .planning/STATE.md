---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
current_phase: 4
current_phase_name: Instruction Handling — Click, Panel, Vectoring & ILS Capture
status: ready_to_plan
stopped_at: Phase 3 complete (UAT passed), ready to plan Phase 4
last_updated: "2026-07-06T19:27:33.264Z"
last_activity: 2026-07-06
last_activity_desc: Phase 03 complete, transitioned to Phase 4
progress:
  total_phases: 7
  completed_phases: 3
  total_plans: 16
  completed_plans: 16
  percent: 43
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-07-06)

**Core value:** The player can work a full session — launch an aircraft off a SID, land another off the ILS, entirely through their own instructions — and the sim never lies about separation.
**Current focus:** Phase 04 — Instruction Handling — Click, Panel, Vectoring & ILS Capture

## Current Position

Phase: 4 — Instruction Handling — Click, Panel, Vectoring & ILS Capture
Plan: Not started
Status: Ready to plan
Last activity: 2026-07-06 — Phase 03 complete (UAT passed), transitioned to Phase 4

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**

- Total plans completed: 16
- Average duration: N/A
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 5 | - | - |
| 02 | 5 | - | - |
| 03 | 6 | - | - |

**Recent Trend:**

- Last 5 plans: N/A
- Trend: N/A

*Updated after each plan completion*
| Phase 01 P01 | 15min | 3 tasks | 6 files |
| Phase 01 P01-02 | 10min | 2 tasks | 2 files |
| Phase 01 P03 | 10min | 2 tasks | 3 files |
| Phase 01 P04 | 20min | 3 tasks | 4 files |
| Phase 01 P05 | 15min | 2 tasks | 1 files |
| Phase 02 P01 | 5min | 2 tasks | 1 files |
| Phase 02 P04 | 10min | 2 tasks | 3 files |
| Phase 02 P02 | 10min | 3 tasks | 11 files |
| Phase 02 P03 | 11min | 2 tasks | 7 files |
| Phase 02 P05 | 5min | 1 tasks | 1 files |
| Phase 03 P01 | 6min | 2 tasks | 6 files |
| Phase 03 P02 | 15min | 2 tasks | 1 files |
| Phase 03 P03 | 3min | 1 tasks | 1 files |
| Phase 03 P04 | 25min | 3 tasks | 6 files |
| Phase 03 P05 | 20min | 1 tasks | 2 files |
| Phase 03 P06 | 20min | 3 tasks | 3 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Roadmap: Walking-Skeleton build order adopted from research — sim clock/render decoupling and procedure-vs-vector reconciliation front-loaded; phraseology/log placed last as purely observational
- Roadmap: PROC-02/PROC-03 (vectoring override, ILS capture state) grouped into Phase 4 with instruction handling rather than Phase 3, so their success criteria are observable through the actual player-facing panel rather than a dev harness
- Roadmap: RADAR-02 (datablock assigned-instruction info) grouped into Phase 4 since instructions must exist before "assigned info" is meaningful
- [Phase 01]: Used version ranges (pygame-ce>=2.5,<3.0, pydantic>=2.13,<3.0, pytest>=8.0) rather than exact pins so pip resolves the true current release
- [Phase 01]: Bootstrapped pip via the official PyPA get-pip.py script (with python -m venv --without-pip) rather than sudo apt install python3.14-venv, since the sandbox has no non-interactive sudo
- [Phase 01-02]: Rescaled MAX_FRAME_TIME from researched 0.25 to 5.0 - at 2Hz TICK_DT=0.5 the literal value made the ticks-per-frame cap unreachable, contradicting CORE-02's required stall-drop behavior
- [Phase ?]: [Phase 01-03]: Copied RESEARCH.md's Aircraft/interpolation reference code verbatim after confirming no unit/scale mismatch existed (unlike 01-02's MAX_FRAME_TIME rescale)
- [Phase 01]: [Phase 01-04]: Replaced render/radar.py's AircraftSnapshot type-hint import with a local typing.Protocol (RenderState) so app.py stays the sole module importing both pygame and atc_sim.sim.*
- [Phase ?]: [Phase 01-05]: Documented both the atc-sim console script and python -m atc_sim.app as equivalent launch paths in README, matching pyproject.toml's [project.scripts] entry
- [Phase ?]: [Phase 02-01]: geographiclib legitimacy human-confirmed on pypi.org (long-established, MIT, official SourceForge link, exact name match) before install - SUS audit flag was a sandbox unknown-downloads false-positive
- [Phase ?]: [Phase 02-04]: Kept CANVAS_WIDTH/CANVAS_HEIGHT constants in aircraft.py (used only by spawn_default now); interpolate() wrap-skip and sim_step wrap removed together per Pitfall A to avoid regressing the teleport-streak the wrap-skip existed to hide
- [Phase ?]: [Phase 02-02]: Corrected test_true_bearing_and_distance_nm's BNN distance expectation from RESEARCH.md's rounded ~11.2nm to the precise geodesic value ~11.6nm, verified directly against geographiclib.Inverse()
- [Phase ?]: [Phase 02-02]: render/radar.py imports atc_sim.navdata.* directly (no Protocol) since navdata is frozen read-only reference data, unlike the mutable sim-state RenderState Protocol boundary
- [Phase ?]: [Phase 02-03]: Collapsed OLNEY 2B's stepped-DME climb restriction (4000/D6, 5000/D9, 6000/D15) into a single at-or-above 6000ft restriction on the final BNN->OLNEY leg, per 02-RESEARCH.md's recommended simplification
- [Phase ?]: [Phase 02-03]: Left HEN leg's altitude_restriction explicitly None (Pitfall B) rather than fabricating a value
- [Phase ?]: [Phase 02-03]: Used pygame.font.Font(None, 14) (bundled default font) rather than SysFont for fix-name text rendering, for portability under the SDL dummy driver
- [Phase 02-05]: Human sign-off completed for Phase 2 capstone: real EGGW runway 25, all 6 SID/STAR fixes with tracks, true-circle range rings, non-wrapping aircraft motion, all confirmed correct
- [Phase 03-01]: Used 'not all equal' fleet-distinctness assertions rather than strict pairwise-distinct, since 03-RESEARCH.md's own recommended fleet values intentionally repeat some numbers across types
- [Phase 03-01]: Named the demo per-tick orchestration entry point update_demo_traffic(aircraft_list, dt), matching 03-PATTERNS.md's suggested name
- [Phase ?]: [Phase 03-02]: Grouped turn_rate_deg_per_sec into Task 1's commit instead of Task 2's, since the test file's single combined import statement requires the function to exist for Task 1's own verification to pass, matching 03-RESEARCH.md Pattern A's grouping
- [Phase ?]: [Phase 03-03]: Copied RESEARCH.md's Pattern B FSM example (Phase enum, LEGAL_TRANSITIONS, transition_to guard) verbatim with no rescaling needed
- [Phase ?]: [Phase 03-04]: APPROACH targets the runway threshold directly via a new _approach_targets() helper (never compute_target()) since procedure_leg_index exhausts the STAR's legs before DESCENT->APPROACH fires, avoiding an out-of-range leg index while keeping procedure.py free of ILS-adjacent logic
- [Phase ?]: [Phase 03-04]: CLIMB->ENROUTE and DESCENT->APPROACH completions are tied to procedure-leg progress, not altitude, matching 03-RESEARCH.md Pattern C
- [Phase ?]: [Phase 03-04]: Renamed render/radar.py's RenderState Protocol + draw_frame from x/y to x_nm/y_nm in lockstep with the AircraftSnapshot rename (Rule 3 fix); real nm->pixel projection remains deferred to plan 03-06
- [Phase ?]: [Phase 03-05]: spawn_departure/spawn_arrival take an optional performance parameter (defaulting to next rotated fleet type) rather than a required one, matching the actual test contract in tests/test_departure_flow.py and tests/test_arrival_flow.py which call both with zero arguments
- [Phase ?]: [Phase 03-05]: Fixed a latent Rule-1 bug in aircraft.py's _is_phase_complete -- TAXI_IN is terminal (no legal transitions) so it must never auto-fire transition_to(), which previously raised StopIteration once an arrival's TAXI_IN timer elapsed; removal of TAXI_IN aircraft is now purely demo_traffic.py's list-membership concern
- [Phase 03-06]: draw_frame changed to accept an iterable of (render_state, trail) pairs so any number of demo_traffic aircraft render in one call, with no phase-aware branching or new per-type symbol added to radar.py (D-04 held)
- [Phase 03-06]: app.py tracks per-aircraft prev-snapshot/trail state in dicts keyed by id(aircraft) rather than adding a tracking-id field to the Aircraft model
- [Phase 03-06]: Task 3's end-of-phase human-check was satisfied via a headless equivalent-verification harness (20,000 real sim ticks through the actual demo_traffic/draw_frame/interpolation call path) since this session has no interactive display; genuine visual sign-off on the project owner's own machine remains the recommended final step

### Pending Todos

None yet.

### Blockers/Concerns

- [Phase 3 resolved]: ILS localizer/glideslope capture-angle logic was correctly scoped out of Phase 3 (8-state Phase enum has no ILS sub-states; PROC-03 owns it) — remains a `--research-phase` candidate for Phase 4, along with Phase 4's own click hit-region sizing/ambiguity resolution — see .planning/research/SUMMARY.md Research Flags section
- Magnetic variation constant for EGGW is a deliberate hardcoded simplification for v1 (Phase 2) — re-confirm against current EGGW charts at implementation time
- Literal on-screen visual sign-off of Phase 3's demo loop was verified via a headless equivalent-verification harness (no display in the execution sandbox) rather than a real screen-watch — recommended to actually launch `atc-sim` once on a machine with a display to eyeball it, though UAT already passed on the data-level evidence

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| *(none)* | | | |

## Session Continuity

Last session: 2026-07-06T19:30:19.000Z
Stopped at: Phase 3 complete, ready to plan Phase 4
Resume file: None
