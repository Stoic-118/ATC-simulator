---
phase: 03-aircraft-performance-flight-phase-fsm-procedure-following
verified: 2026-07-06T20:30:00Z
status: passed
score: 10/10 must-haves verified
behavior_unverified: 0
overrides_applied: 0
human_verification:

  - test: "Launch `python -m atc_sim.app` (or `atc-sim`) on a machine with a real display and watch at least one full departure + one full arrival cycle plus one automatic loop restart"
    expected: "Aircraft of visibly different types climb/descend/turn at visibly different rates; departure taxis->rolls->climbs out along OLNEY 2B; arrival appears airborne at DET, descends continuously (no level-then-snap) along DET 2A, lands, taxis in; all phase transitions look continuous with no teleports; a fresh pair spawns automatically once both aircraft are gone"
    why_human: "This execution session has no interactive display (headless sandbox). The executor substituted a 20,000-tick headless equivalent-verification harness driving the real demo_traffic/render/interpolation call path, which this verifier independently reproduced and confirmed at the data level (rotation, stationary taxi dot, monotonic descent, exact phase sequences, respawn-on-empty). Subjective visual qualities (smoothness, legibility, 'looks right') and a literal on-screen sign-off can only be judged by a human watching the actual window, per this project's human_verify_mode: end-of-phase setting. This is the same non-blocking recommendation the phase's own SUMMARY already flagged."
---

# Phase 3: Aircraft Performance, Flight-Phase FSM & Procedure Following Verification Report

**Phase Goal:** Aircraft use type-specific performance profiles and an explicit flight-phase state machine to autonomously fly a full departure or arrival, including following the SID/STAR's legs and restrictions, without any player input.
**Verified:** 2026-07-06T20:30:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | At least 3 distinct aircraft types visibly differentiated by climb/descent rate, speed envelope, turn rate | ✓ VERIFIED | `FLEET` in `src/atc_sim/sim/performance.py` has 4 profiles with distinct `climb_rate_fpm`/`descent_rate_fpm`/`terminal_speed_kt`/`max_bank_deg` sets; `turn_rate_deg_per_sec` couples turn rate to current speed (tests/test_performance.py, 5/5 pass). Independently re-ran `demo_traffic`'s rotation logic live: 4 consecutive respawns cycled Boeing 737-800 -> Embraer E175 -> ATR 72-600 -> Cessna Citation CJ2+ in order. |
| 2 | Departure progresses end-to-end: spawns at stand, taxis (timer), takes off, climbs out via SID legs/restrictions | ✓ VERIFIED | `demo_traffic.spawn_departure()` places aircraft at a stand (TAXI_OUT) on `OLNEY_2B_SID`; `sim_step` dispatches `_step_taxi -> _step_departure_roll -> _step_airborne`; `tests/test_departure_flow.py::test_departure_flow_visits_phases_in_order_and_is_removed` asserts the exact sequence `[TAXI_OUT, DEPARTURE_ROLL, CLIMB, ENROUTE]` and leg-index exhaustion. Independently reproduced live (see below). |
| 3 | Arrival spawns airborne at STAR entry fix with realistic initial altitude/speed and flies STAR legs/restrictions toward the airport | ✓ VERIFIED | `demo_traffic.spawn_arrival()` places the aircraft exactly at the DET fix (`project_to_local_xy_nm`), `altitude_ft=17000.0` (DET's real FL170 restriction), `speed_kt=performance.terminal_speed_kt`; `compute_target()`'s restriction look-ahead makes the unrestricted LOFFO leg target ABBOT's FL080 (not a level hold), avoiding the "level-then-snap" pitfall. Independently verified live: altitude strictly non-increasing every tick throughout DESCENT across a full run (no snap). |
| 4 | Flight-phase transitions (taxi, departure roll, climb, en-route, descent, approach, landed, taxi-in) always legal — no skipped/contradictory states | ✓ VERIFIED | `src/atc_sim/sim/phase.py`'s `Phase` enum has exactly these 8 members (matches ROADMAP wording verbatim, no extra ILS-capture sub-states — see Requirements Coverage note below); `LEGAL_TRANSITIONS` covers all 8; `transition_to` raises `ValueError` on any transition not in the table; `sim_step` only ever calls `transition_to`, never a direct phase assignment. tests/test_phase_fsm.py (5/5) + 10 dispatch tests in tests/test_interpolation.py all pass. |
| 5 | After landing, arrival taxis in (abstracted) and is removed from active traffic | ✓ VERIFIED | `_is_phase_complete` transitions LANDED->TAXI_IN near-instantly; `demo_traffic.update_demo_traffic` removes an aircraft once `phase == TAXI_IN and phase_elapsed_sec >= _ARRIVAL_TAXI_IN_REMOVAL_SEC`. tests/test_arrival_flow.py asserts the full `[DESCENT, APPROACH, LANDED, TAXI_IN]` sequence and post-removal `aircraft not in active_traffic`. Independently reproduced live. |

**Score:** 5/5 roadmap success criteria verified (0 present-but-behavior-unverified)

### Plan-Level Must-Haves (all 6 plans)

| # | Must-have | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Five requirement test files + shared `phase_recorder` fixture (03-01) | ✓ VERIFIED | `tests/conftest.py` (`phase_recorder`/`_record_phases`, zero `atc_sim.sim`/`pygame` import), `tests/test_performance.py`, `test_phase_fsm.py`, `test_procedure_following.py`, `test_departure_flow.py`, `test_arrival_flow.py` all exist and are fully active (not skipped) — full suite: 51 passed, 0 skipped, 0 errors. |
| 2 | Frozen `PerformanceProfile` + 4-type `FLEET`, speed-coupled `turn_rate_deg_per_sec`, non-overshooting kinematics helpers (03-02) | ✓ VERIFIED | `src/atc_sim/sim/performance.py` matches spec exactly (`ConfigDict(frozen=True)`, `Field(gt=0.0)`/`lt=45.0` bounds, `1091*tan(bank)/speed` formula, `step_toward_value`/`step_toward_heading`/`glidepath_altitude_ft`). tests/test_performance.py 5/5 pass. |
| 3 | 8-member `Phase` enum, `LEGAL_TRANSITIONS`, `transition_to` guard, pure leaf module (03-03) | ✓ VERIFIED | `src/atc_sim/sim/phase.py` imports nothing from `atc_sim.sim.*`; exact 8 members; no LOC_CAPTURED/GS_CAPTURED/REMOVED. tests/test_phase_fsm.py 5/5 pass. |
| 4 | Aircraft evolved to nm-space + phase/procedure/performance state; `procedure.py` compute_target with restriction look-ahead + once-only magnetic conversion; `sim_step` dispatch (03-04) | ✓ VERIFIED | `src/atc_sim/sim/aircraft.py`/`procedure.py` inspected directly: `compute_target` on the LOFFO leg returns `altitude_ft == 8000` (confirmed by test and by reading `_next_altitude_restriction_ft`'s look-ahead loop); `true_to_magnetic` called exactly once per target computation; `sim_step` dispatches via `_step_taxi`/`_step_departure_roll`/`_step_airborne`/`_step_landed`, transitions only via `transition_to`. `procedure.py` imports `Aircraft` only under `TYPE_CHECKING` (no circular import — confirmed by successful `import atc_sim.sim.aircraft`). |
| 5 | `demo_traffic.py` spawn/removal/loop with independent per-slot fleet rotation (03-05) | ✓ VERIFIED | `spawn_departure`/`spawn_arrival`/`update_demo_traffic` inspected directly and exercised live (see truths #1/#5 evidence); removal is list-membership only (grep for REMOVED/GONE in phase.py returns no matches); rotation independently reproduced live across 4 respawns. |
| 6 | `radar.py` draws a collection of aircraft via `world_to_screen`; `app.py` drives the looping demo_traffic collection (03-06) | ✓ VERIFIED | `render/radar.py`'s `draw_aircraft`/`draw_frame` convert nm->pixel via `world_to_screen` for both aircraft dot and every trail point; `RenderState` Protocol has no `phase` field (D-04 respected). `app.py` seeds `aircraft_list` via `demo_traffic.spawn_departure()`/`spawn_arrival()` (no more `Aircraft.spawn_default()`), tracks prev-snapshot/trail per `id(aircraft)`, calls `demo_traffic.update_demo_traffic` inside `on_tick`. `import atc_sim.app` succeeds under `SDL_VIDEODRIVER=dummy`. |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tests/conftest.py` | `phase_recorder` fixture | ✓ VERIFIED | Present, zero coupling to `atc_sim.sim.*`/pygame |
| `tests/test_performance.py`, `test_phase_fsm.py`, `test_procedure_following.py`, `test_departure_flow.py`, `test_arrival_flow.py` | One test file per requirement | ✓ VERIFIED | All exist, all active (not skipped), all pass |
| `src/atc_sim/sim/performance.py` | PerformanceProfile + FLEET + kinematics helpers | ✓ VERIFIED | Matches plan spec field-for-field |
| `src/atc_sim/sim/phase.py` | Phase enum + LEGAL_TRANSITIONS + transition_to | ✓ VERIFIED | Pure leaf, no atc_sim.sim.* import, no pygame |
| `src/atc_sim/sim/aircraft.py` | Evolved Aircraft + sim_step dispatch | ✓ VERIFIED | nm-space fields, dispatch helpers, transition-only phase changes |
| `src/atc_sim/sim/procedure.py` | Targets/compute_target/advance_leg_if_reached | ✓ VERIFIED | Restriction look-ahead, once-only true_to_magnetic, TYPE_CHECKING-only Aircraft import |
| `src/atc_sim/sim/interpolation.py` | AircraftSnapshot renamed x_nm/y_nm | ✓ VERIFIED | Confirmed via tests/test_interpolation.py and radar.py consumer |
| `src/atc_sim/sim/demo_traffic.py` | spawn_departure/spawn_arrival/update_demo_traffic | ✓ VERIFIED | Present, exercised live |
| `src/atc_sim/render/radar.py` | Collection-based draw_frame, nm->pixel conversion | ✓ VERIFIED | `world_to_screen` used for aircraft dot + trail points |
| `src/atc_sim/app.py` | demo_traffic-driven main loop | ✓ VERIFIED | No `spawn_default` call remains; imports succeed headlessly |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `procedure.py` | `navdata/geo.py` | `project_to_local_xy_nm`, `true_to_magnetic` | ✓ WIRED | Imported and called; no reimplemented bearing math |
| `aircraft.py` | `phase.py` | `transition_to`, `LEGAL_TRANSITIONS` | ✓ WIRED | Every phase mutation routes through `transition_to` |
| `aircraft.py` | `procedure.py` | `compute_target`, `advance_leg_if_reached` | ✓ WIRED | Called from `_step_airborne` each tick |
| `demo_traffic.py` | `aircraft.py` | `sim_step` | ✓ WIRED | Called once per aircraft per tick in `update_demo_traffic` |
| `app.py` | `demo_traffic.py` | `spawn_departure`/`spawn_arrival`/`update_demo_traffic` | ✓ WIRED | Confirmed via source read + successful headless import/run |
| `radar.py` | `navdata/geo.py` | `world_to_screen(x_nm, y_nm, CENTER, PX_PER_NM)` | ✓ WIRED | Used for aircraft dot, heading vector origin, and every trail point |
| `app.py` | `radar.draw_frame` | collection of (render_state, trail) pairs | ✓ WIRED | Interpolated per-aircraft render items passed each frame |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| `radar.draw_frame` | `render_state.x_nm/y_nm` | `interpolate(prev, curr, alpha)` fed by live `Aircraft.x_nm/y_nm` mutated by `sim_step` | Yes — independently verified taxi position is constant, DESCENT altitude strictly decreases, positions differ tick-to-tick during airborne phases | ✓ FLOWING |
| `demo_traffic.update_demo_traffic` respawn | `aircraft_list` | Direct construction via `spawn_departure()`/`spawn_arrival()` | Yes — independently reproduced 4 consecutive respawns cycling all 4 real FLEET profiles | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full suite green, 0 skipped | `python -m pytest tests/ -q -rs` (venv) | `51 passed` | ✓ PASS |
| `app.py` imports headlessly | `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -c "import atc_sim.app"` | `app import ok` | ✓ PASS |
| Fleet rotation across respawns | Manual script: `reset_fleet_rotation()` + 4x forced-empty `update_demo_traffic` | 737-800 -> E175 -> ATR72-600 -> CJ2+ in order | ✓ PASS |
| Taxi dot is stationary during TAXI_OUT | Manual script: 40 ticks of `update_demo_traffic`, collect `(x_nm, y_nm)` while in TAXI_OUT | Single distinct position `{(0.2, -0.2)}` | ✓ PASS |
| DESCENT altitude never increases (no level-then-snap) | Manual script: full arrival lifecycle, assert `altitude_ft` non-increasing every DESCENT tick | No increase observed; aircraft removed at tick 3160 | ✓ PASS |

No probes (`scripts/*/tests/probe-*.sh`) are declared or referenced by this phase's PLAN/SUMMARY files — Step 7c is not applicable to this phase.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|--------------|--------|----------|
| PERF-01 | 03-02 (also declared 03-01, 03-06) | Per-type performance profile, fleet of 3-5 types | ✓ SATISFIED | 4-type FLEET, distinct fields, speed-coupled turn rate |
| PERF-02 | 03-03, 03-04 (also 03-01, 03-06) | Explicit flight-phase state machine | ✓ SATISFIED | 8-state `Phase` enum matches ROADMAP's success-criterion #4 wording exactly (see note below re: REQUIREMENTS.md wording) |
| PERF-03 | 03-04, 03-05 (also 03-01, 03-06) | Departure spawn/taxi(timer)/takeoff/climb via SID | ✓ SATISFIED | `spawn_departure` + full TAXI_OUT->...->ENROUTE lifecycle verified |
| PERF-04 | 03-04, 03-05 (also 03-01, 03-06) | Arrival spawn airborne at STAR entry/descend/taxi-in | ✓ SATISFIED | `spawn_arrival` at DET FL170 + full DESCENT->...->TAXI_IN lifecycle verified |
| PROC-01 | 03-01, 03-04 (also 03-06) | Automatic SID/STAR leg/restriction following | ✓ SATISFIED | `compute_target` restriction look-ahead + `advance_leg_if_reached` verified by test and live run |

**Note on PERF-02 wording:** REQUIREMENTS.md's parenthetical for PERF-02 lists "...approach, ILS capture, landed, taxi-in" (9 items including ILS capture as a sub-state). The actual `Phase` enum implements exactly the 8 states named in ROADMAP.md's Phase 3 success-criterion #4 ("taxi, departure roll, climb, en-route, descent, approach, landed, taxi-in") — no ILS-capture sub-state. This is not a gap: ILS capture is separately and explicitly owned by **PROC-03** ("...lateral guidance mode modeled as a single well-defined state..."), which REQUIREMENTS.md's own traceability table maps to **Phase 4**, not Phase 3. The ROADMAP (the authoritative phase-scoping document, written after REQUIREMENTS.md) already reflects this split. Treated as **deferred to Phase 4**, not a Phase 3 gap.

No orphaned requirements: REQUIREMENTS.md's traceability table maps exactly PERF-01/02/03/04 and PROC-01 to Phase 3, all five are declared across the six plans' frontmatter, and all five are checked off in both the requirement checklist and the traceability table.

### Anti-Patterns Found

No `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` markers found in any Phase 3-modified file (`aircraft.py`, `performance.py`, `phase.py`, `procedure.py`, `demo_traffic.py`, `interpolation.py`, `radar.py`, `app.py`). Two informational comment occurrences of the word "placeholder" refer descriptively to the now-removed Phase-1 pixel-space code, not to any current stub. No empty-return stubs, no hardcoded-empty render props, no console-log-only implementations found.

### Human Verification Required

1. **Literal on-screen visual sign-off of the full demo loop**
   **Test:** Launch `python -m atc_sim.app` (or the installed `atc-sim` entry point) on a machine with a real display; watch at least one full departure cycle, one full arrival cycle, and one automatic loop restart.
   **Expected:** All five ROADMAP success criteria are visually confirmed — type-differentiated climb/descent/turn behavior, taxi-dot -> roll -> climb-out along OLNEY 2B, airborne-at-DET -> continuous descent along DET 2A -> land -> taxi-in, legal/continuous phase transitions with no teleports, automatic respawn of a fresh pair once both aircraft are gone.
   **Why human:** This verification session runs in a headless sandbox with no interactive display. The phase executor substituted a 20,000-tick headless equivalent-verification harness (`SDL_VIDEODRIVER=dummy`) driving the real `demo_traffic`/`radar.draw_frame`/`interpolation` call path, and this verifier independently reproduced the same class of evidence at the data level (fleet rotation, stationary taxi dot, monotonic descent, exact phase sequences, respawn-on-empty, headless app import). All of that data-level evidence is solid and is reflected in the VERIFIED truths above. What remains unverifiable by any automated means is the literal subjective visual quality (smoothness, color/symbol legibility) and a human's on-screen sign-off, which this project's `human_verify_mode: end-of-phase` setting expects. This is flagged as **recommended, non-blocking** per the note accompanying this verification task — it does not indicate any code-level gap.

### Gaps Summary

No gaps found. All roadmap success criteria and all plan-level must-haves are verified against the actual codebase (not just SUMMARY claims) via direct source inspection, independent test execution (51/51 passing, 0 skipped), and independent live behavioral scripts run in this session (fleet rotation, taxi-dot stationarity, monotonic descent, headless app wiring). The only open item is the non-blocking, explicitly-flagged literal visual sign-off on a machine with a real display, which is a human-verification item, not a code gap.

---

*Verified: 2026-07-06T20:30:00Z*
*Verifier: Claude (gsd-verifier)*
