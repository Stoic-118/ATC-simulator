"""Authoritative Aircraft state model and its per-phase motion.

Phase 3 (03-04): Aircraft moved from the Phase-1 placeholder pixel-space
model (x/y pixels, heading_deg, speed_px_per_sec) into the shared local-nm
tangent-plane coordinate system already used by every navdata projection
(navdata/geo.py's project_to_local_xy_nm) and by procedure tracking, plus
full altitude/phase/procedure/performance state. `sim_step` mutates the
one authoritative Aircraft instance per tick and must only ever be called
from SimClock.advance()'s on_tick callback — never from the render loop.

This module MUST NOT import pygame — it stays headlessly testable via
pytest with no display, enforced by tests/test_boundary.py.
"""

import math

from pydantic import BaseModel, ConfigDict, Field

from atc_sim.navdata.eggw import EGGW_RUNWAY
from atc_sim.navdata.geo import project_to_local_xy_nm, true_to_magnetic
from atc_sim.navdata.models import Procedure
from atc_sim.sim.performance import (
    PerformanceProfile,
    glidepath_altitude_ft,
    step_toward_heading,
    step_toward_value,
    turn_rate_deg_per_sec,
)
from atc_sim.sim.phase import LEGAL_TRANSITIONS, Phase, transition_to
from atc_sim.sim.procedure import Targets, advance_leg_if_reached, compute_target


class Aircraft(BaseModel):
    model_config = ConfigDict(validate_assignment=True)  # v2 style; catches bad mutations

    x_nm: float
    y_nm: float
    altitude_ft: float = Field(ge=0.0)
    speed_kt: float = Field(gt=0.0)
    heading_deg: float = Field(ge=0.0, lt=360.0)  # Phase 3: MAGNETIC, matches every navdata heading field
    phase: Phase
    phase_elapsed_sec: float = 0.0  # single generic timer, reused across every timed phase; reset on transition
    procedure: Procedure
    procedure_leg_index: int = Field(default=0, ge=0)
    performance: PerformanceProfile

    # Phase 3 (D-02): spawn_default() removed -- the demo harness in plan
    # 03-05 owns spawn construction (round-robin fleet types, departure vs.
    # arrival flight kind). A stale pixel-based classmethod referencing
    # removed x/y/speed_px_per_sec fields would be dead code here.
    # NOTE: src/atc_sim/app.py still calls Aircraft.spawn_default() and
    # reads aircraft.x/aircraft.y -- that call site is rewired in plan
    # 03-06 alongside the render layer's nm->pixel projection; it is
    # intentionally left unmigrated until then (03-04-PLAN.md scope).


# --- Phase-completion thresholds (Claude's Discretion; [ASSUMED] per
# 03-RESEARCH.md Pattern C -- reasonable UX-pacing defaults, not sourced
# facts). Isolated as named module-level constants so they are easy to
# retune without touching dispatch logic. ---------------------------------
_TAXI_DURATION_SEC = 18.0  # [ASSUMED] ~15-20 sim seconds, RESEARCH Pattern C
_ROTATION_SPEED_KT = 150.0  # [ASSUMED] within RESEARCH's ~140-160kt range
_APPROACH_CAPTURE_DISTANCE_NM = 0.1  # [ASSUMED] RESEARCH Pattern C
_APPROACH_CAPTURE_ALTITUDE_FT = 50.0  # [ASSUMED] RESEARCH Pattern C


def sim_step(aircraft: Aircraft, dt: float) -> None:
    """Mutates the single authoritative Aircraft instance. Called only from
    SimClock.advance()'s on_tick callback — never from the render loop.

    Short dispatcher delegating to small, independently-testable per-phase
    helpers (Phase 3 (Pitfall "Per-phase kinematics dispatch scattered as
    inline conditionals")) rather than one long inline if/elif kinematics
    block. Phase transitions happen only via transition_to(), never by
    direct assignment elsewhere.
    """
    if aircraft.phase in (Phase.TAXI_OUT, Phase.TAXI_IN):
        _step_taxi(aircraft, dt)
    elif aircraft.phase == Phase.DEPARTURE_ROLL:
        _step_departure_roll(aircraft, dt)
    elif aircraft.phase == Phase.LANDED:
        _step_landed(aircraft, dt)
    else:  # CLIMB, ENROUTE, DESCENT, APPROACH
        _step_airborne(aircraft, dt)

    if _is_phase_complete(aircraft):
        aircraft.phase = transition_to(aircraft.phase, _next_phase(aircraft.phase))
        aircraft.phase_elapsed_sec = 0.0


def _next_phase(phase: Phase) -> Phase:
    """The linear chain has exactly one legal successor per non-terminal
    phase -- returns it directly rather than requiring the caller to know
    which one."""
    return next(iter(LEGAL_TRANSITIONS[phase]))


def _step_taxi(aircraft: Aircraft, dt: float) -> None:
    # Phase 3: TAXI_OUT/TAXI_IN are pure timers -- position is frozen
    # (D-05's "stationary dot"); only the shared phase_elapsed_sec advances.
    aircraft.phase_elapsed_sec += dt


def _step_departure_roll(aircraft: Aircraft, dt: float) -> None:
    # Phase 3: straight-line acceleration along the runway heading only --
    # no turning during the roll (RESEARCH Pattern C).
    max_speed_delta_kt = aircraft.performance.max_speed_change_kt_per_sec * dt
    aircraft.speed_kt = step_toward_value(aircraft.speed_kt, _ROTATION_SPEED_KT, max_speed_delta_kt)
    aircraft.heading_deg = EGGW_RUNWAY.heading_deg_mag  # held fixed; runway QFU, already magnetic
    _move_along_heading(aircraft, dt)


def _step_landed(aircraft: Aircraft, dt: float) -> None:
    # Phase 3: LANDED is a near-instantaneous pass-through (RESEARCH
    # Pattern C) -- _is_phase_complete() unconditionally advances it to
    # TAXI_IN on the very next check, so no kinematics happen here.
    pass


def _step_airborne(aircraft: Aircraft, dt: float) -> None:
    # Phase 3: CLIMB/ENROUTE/DESCENT/APPROACH share the same
    # turn/climb-or-descend/speed-change/move kinematics; only the target
    # source differs for APPROACH (simplified glidepath-to-threshold,
    # never compute_target()'s leg restriction -- procedure.py Task 2's
    # explicit scope boundary, no ILS geometry here).
    targets = _approach_targets(aircraft) if aircraft.phase == Phase.APPROACH else compute_target(aircraft)

    max_turn_deg = turn_rate_deg_per_sec(aircraft.performance.max_bank_deg, aircraft.speed_kt) * dt
    aircraft.heading_deg = step_toward_heading(aircraft.heading_deg, targets.heading_deg, max_turn_deg)

    climbing = targets.altitude_ft > aircraft.altitude_ft
    rate_fpm = aircraft.performance.climb_rate_fpm if climbing else aircraft.performance.descent_rate_fpm
    max_altitude_delta_ft = rate_fpm / 60.0 * dt
    aircraft.altitude_ft = step_toward_value(aircraft.altitude_ft, targets.altitude_ft, max_altitude_delta_ft)

    max_speed_delta_kt = aircraft.performance.max_speed_change_kt_per_sec * dt
    aircraft.speed_kt = step_toward_value(aircraft.speed_kt, targets.speed_kt, max_speed_delta_kt)

    _move_along_heading(aircraft, dt)

    # No-op once procedure_leg_index has already exhausted the legs (i.e.
    # during APPROACH) -- advance_leg_if_reached guards that itself.
    advance_leg_if_reached(aircraft)


def _move_along_heading(aircraft: Aircraft, dt: float) -> None:
    """The one place x_nm/y_nm advance from current heading/speed, using
    the sin=x/cos=y convention shared with navdata/geo.py."""
    rad = math.radians(aircraft.heading_deg)
    distance_nm = (aircraft.speed_kt / 3600.0) * dt  # kt -> nm/sec
    aircraft.x_nm += math.sin(rad) * distance_nm
    aircraft.y_nm += math.cos(rad) * distance_nm


def _distance_to_threshold_nm(aircraft: Aircraft) -> float:
    threshold_x_nm, threshold_y_nm = project_to_local_xy_nm(
        EGGW_RUNWAY.threshold_lat, EGGW_RUNWAY.threshold_lon
    )
    return math.hypot(threshold_x_nm - aircraft.x_nm, threshold_y_nm - aircraft.y_nm)


def _approach_targets(aircraft: Aircraft) -> Targets:
    """APPROACH's simplified glidepath-to-threshold targeting (RESEARCH
    Pattern C): heading points directly at the runway threshold (same
    atan2/true_to_magnetic convention as compute_target(), but never
    calling into procedure.py -- by the time an aircraft reaches APPROACH,
    procedure_leg_index has exhausted the STAR's legs, so indexing into
    aircraft.procedure.legs would be out of range). Altitude comes from
    the simplified 3-degree glidepath rule, never real ILS geometry
    (explicit Phase 4/PROC-03 scope boundary)."""
    threshold_x_nm, threshold_y_nm = project_to_local_xy_nm(
        EGGW_RUNWAY.threshold_lat, EGGW_RUNWAY.threshold_lon
    )
    dx = threshold_x_nm - aircraft.x_nm
    dy = threshold_y_nm - aircraft.y_nm
    true_bearing = math.degrees(math.atan2(dx, dy)) % 360.0
    heading_deg = true_to_magnetic(true_bearing)  # Pitfall 4: convert true->magnetic exactly once
    distance_nm = math.hypot(dx, dy)
    return Targets(
        heading_deg=heading_deg,
        altitude_ft=glidepath_altitude_ft(distance_nm),
        speed_kt=aircraft.performance.approach_speed_kt,
    )


def _is_phase_complete(aircraft: Aircraft) -> bool:
    """Completion conditions read aircraft state, so they live here (not
    phase.py) to preserve phase.py as a pure leaf module with zero
    Aircraft coupling."""
    if aircraft.phase in (Phase.TAXI_OUT, Phase.TAXI_IN):
        return aircraft.phase_elapsed_sec >= _TAXI_DURATION_SEC
    if aircraft.phase == Phase.DEPARTURE_ROLL:
        return aircraft.speed_kt >= _ROTATION_SPEED_KT
    if aircraft.phase == Phase.CLIMB:
        # Tied to leg progress, not altitude (RESEARCH: "keep CLIMB->ENROUTE
        # tied to leg progress" since the departure demo is removed from
        # ENROUTE before ever reaching DESCENT): once the aircraft has
        # advanced past its first SID leg it has "begun tracking the
        # procedure".
        return aircraft.procedure_leg_index >= 1
    if aircraft.phase == Phase.DESCENT:
        # A full-flight arrival transitions to APPROACH once its STAR's
        # legs are exhausted (RESEARCH Pattern C).
        return aircraft.procedure_leg_index >= len(aircraft.procedure.legs)
    if aircraft.phase == Phase.APPROACH:
        return (
            _distance_to_threshold_nm(aircraft) < _APPROACH_CAPTURE_DISTANCE_NM
            and aircraft.altitude_ft < _APPROACH_CAPTURE_ALTITUDE_FT
        )
    if aircraft.phase == Phase.LANDED:
        return True  # near-instantaneous pass-through, RESEARCH Pattern C
    return False  # ENROUTE: no auto-transition; removal is external (demo_traffic, 03-05)
