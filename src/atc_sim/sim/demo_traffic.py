"""Demo-harness spawn/removal/looping orchestration (D-02, D-03, PERF-03,
PERF-04): the two-hardcoded-aircraft stand-in for Phase 6's real scenario
loader. Isolating spawn/removal/loop logic in this one module means Phase 6
can replace only this module without touching sim_step/procedure/phase.

This module MUST NOT import pygame — it stays headlessly testable via
pytest with no display, enforced by tests/test_boundary.py.
"""

import math

from atc_sim.navdata.eggw import DET_2A_STAR, EGGW_RUNWAY, OLNEY_2B_SID
from atc_sim.navdata.geo import project_to_local_xy_nm, true_to_magnetic
from atc_sim.sim.aircraft import Aircraft, sim_step
from atc_sim.sim.performance import (
    ATR_72_600,
    BOEING_737_800,
    CESSNA_CJ2_PLUS,
    EMBRAER_E175,
    PerformanceProfile,
)
from atc_sim.sim.phase import Phase

# --- Fleet type-rotation (RESEARCH "3 distinct types visibly differentiated"
# pitfall) -- a fixed round-robin order, advanced independently per spawn
# slot (departure/arrival) so within 1-2 loop iterations all 4 fleet types
# have flown, rather than always spawning the same hardcoded pair. ---------
_FLEET_ROTATION: list[PerformanceProfile] = [
    BOEING_737_800,
    EMBRAER_E175,
    ATR_72_600,
    CESSNA_CJ2_PLUS,
]


class _RotationState:
    """Encapsulates the two independent round-robin indices (departure slot,
    arrival slot) so tests can reset rotation state deterministically via
    reset_fleet_rotation() rather than reaching into module globals."""

    def __init__(self) -> None:
        self.departure_index = 0
        self.arrival_index = 0


_rotation_state = _RotationState()


def reset_fleet_rotation() -> None:
    """Test-resettable hook: rewinds both rotation slots back to index 0."""
    _rotation_state.departure_index = 0
    _rotation_state.arrival_index = 0


def _next_departure_type() -> PerformanceProfile:
    profile = _FLEET_ROTATION[_rotation_state.departure_index % len(_FLEET_ROTATION)]
    _rotation_state.departure_index += 1
    return profile


def _next_arrival_type() -> PerformanceProfile:
    profile = _FLEET_ROTATION[_rotation_state.arrival_index % len(_FLEET_ROTATION)]
    _rotation_state.arrival_index += 1
    return profile


# --- Spawn-position constants (Claude's Discretion / RESEARCH Open Question
# 2 -- a plausible stand position, not sourced from a real published stand
# chart; a one-line constant expressed directly in the local-nm space
# already established by navdata/geo.py). [ASSUMED] ------------------------
_DEPARTURE_STAND_X_NM = 0.2  # [ASSUMED] short offset off the threshold origin
_DEPARTURE_STAND_Y_NM = -0.2  # [ASSUMED] short offset off the threshold origin
_TAXI_SPEED_KT = 15.0  # [ASSUMED] low, nonzero (Field(gt=0.0)) taxi speed

# Arrival removal: how long TAXI_IN must elapse before the arrival is
# removed from active traffic (D-03). Deliberately a demo_traffic-owned
# constant, not aircraft.py's internal TAXI_OUT->DEPARTURE_ROLL timer --
# TAXI_IN is a terminal Phase (LEGAL_TRANSITIONS[TAXI_IN] == set()), so its
# "is it done" question is answered here (list-membership), never by a
# Phase-FSM transition (RESEARCH "Removal is not a phase" pitfall).
_ARRIVAL_TAXI_IN_REMOVAL_SEC = 18.0  # [ASSUMED] matches the taxi-duration pacing


def spawn_departure(performance: PerformanceProfile | None = None) -> Aircraft:
    """Spawns a departure Aircraft at a stand, phase=TAXI_OUT, on the OLNEY
    2B SID. `performance` defaults to the next rotated fleet type when not
    given explicitly (update_demo_traffic's respawn call passes it
    explicitly; the flow tests call this with no arguments)."""
    if performance is None:
        performance = _next_departure_type()
    return Aircraft(
        x_nm=_DEPARTURE_STAND_X_NM,
        y_nm=_DEPARTURE_STAND_Y_NM,
        altitude_ft=0.0,
        speed_kt=_TAXI_SPEED_KT,
        heading_deg=EGGW_RUNWAY.heading_deg_mag,  # runway QFU, already magnetic
        phase=Phase.TAXI_OUT,
        procedure=OLNEY_2B_SID,
        procedure_leg_index=0,
        performance=performance,
    )


def spawn_arrival(performance: PerformanceProfile | None = None) -> Aircraft:
    """Spawns an arrival Aircraft airborne exactly at the DET 2A STAR entry
    fix, phase=DESCENT, altitude_ft=17000 (the DET fix's real charted FL170
    restriction -- see navdata/eggw.py DET_2A_STAR.legs[0]). `performance`
    defaults to the next rotated fleet type when not given explicitly."""
    if performance is None:
        performance = _next_arrival_type()
    det_fix = DET_2A_STAR.legs[0].fix
    x_nm, y_nm = project_to_local_xy_nm(det_fix.lat, det_fix.lon)

    # Initial heading points toward the STAR's next leg (LOFFO), computed via
    # the same atan2 + true_to_magnetic path used everywhere else in this
    # codebase (Pitfall 4: convert true->magnetic exactly once) -- advance_
    # leg_if_reached() will advance procedure_leg_index past DET on tick 1
    # anyway (spawn distance to DET is 0), so this only matters for the very
    # first frame's heading vector.
    next_fix = DET_2A_STAR.legs[1].fix
    next_x_nm, next_y_nm = project_to_local_xy_nm(next_fix.lat, next_fix.lon)
    true_bearing = math.degrees(math.atan2(next_x_nm - x_nm, next_y_nm - y_nm)) % 360.0
    heading_deg = true_to_magnetic(true_bearing)

    return Aircraft(
        x_nm=x_nm,
        y_nm=y_nm,
        altitude_ft=17000.0,  # DET fix FL170 restriction (PERF-04 realistic initial altitude)
        speed_kt=performance.terminal_speed_kt,  # realistic initial terminal-area speed
        heading_deg=heading_deg,
        phase=Phase.DESCENT,
        procedure=DET_2A_STAR,
        procedure_leg_index=0,
        performance=performance,
    )


def update_demo_traffic(aircraft_list: list[Aircraft], dt: float) -> None:
    """Per-tick orchestration entry point (called once per sim tick from
    app.py, 03-06): steps every aircraft, removes any aircraft whose
    terminal condition has been met, and respawns a fresh rotated pair once
    the list empties (D-03 looping). Mutates `aircraft_list` in place --
    app.py owns the list itself.

    Removal is list membership, never a Phase value (RESEARCH "Removal is
    not a phase" pitfall) -- no REMOVED/GONE Phase member exists.
    """
    for aircraft in aircraft_list:
        sim_step(aircraft, dt)

    for aircraft in list(aircraft_list):
        # Departure: ENROUTE with the OLNEY 2B SID's legs exhausted. Arrivals
        # never enter ENROUTE this phase (they spawn directly into DESCENT),
        # so this condition only ever matches a departure.
        if aircraft.phase == Phase.ENROUTE and aircraft.procedure_leg_index >= len(
            aircraft.procedure.legs
        ):
            aircraft_list.remove(aircraft)
        # Arrival: TAXI_IN's timer has elapsed. Departures never reach
        # TAXI_IN this phase (they are removed from ENROUTE first), so this
        # condition only ever matches an arrival.
        elif aircraft.phase == Phase.TAXI_IN and aircraft.phase_elapsed_sec >= _ARRIVAL_TAXI_IN_REMOVAL_SEC:
            aircraft_list.remove(aircraft)

    if not aircraft_list:
        aircraft_list.append(spawn_departure())
        aircraft_list.append(spawn_arrival())
