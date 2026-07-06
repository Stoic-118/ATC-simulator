"""Headless tests for Aircraft motion and read-only interpolation.

Covers CORE-03 (render layer never mutates sim state) and RADAR-03
(heading vector must be correct across the 0/360 boundary). No pygame
import anywhere in this file or in the modules under test.

Phase 3 (03-04): Aircraft moved into the shared local-nm coordinate space
(x_nm/y_nm replacing pixel x/y) with full procedure/performance/phase
state, and AircraftSnapshot was renamed in lockstep. The Phase-1/2
pixel-canvas motion tests (straight-line-only sim_step, CANVAS_WIDTH
wrap-edge check) are retired here since that motion model no longer
exists -- sim_step now dispatches per-phase kinematics (see the
"sim_step phase dispatch" section below, added alongside Task 3's
dispatcher implementation).
"""

import math

import pytest
from pydantic import ValidationError

from atc_sim.navdata.eggw import DET_2A_STAR, EGGW_RUNWAY, OLNEY_2B_SID
from atc_sim.navdata.geo import project_to_local_xy_nm, true_to_magnetic
from atc_sim.sim.aircraft import Aircraft, sim_step
from atc_sim.sim.interpolation import AircraftSnapshot, capture_state, interpolate
from atc_sim.sim.performance import FLEET
from atc_sim.sim.phase import Phase


def _angle_diff(a: float, b: float) -> float:
    """Smallest absolute distance between two angles in degrees, wrap-aware."""
    return abs(((a - b + 180) % 360) - 180)


def _valid_aircraft_kwargs(**overrides) -> dict:
    """A complete, valid set of Aircraft constructor kwargs (Phase 3 shape:
    x_nm/y_nm/altitude_ft/speed_kt/heading_deg/phase/phase_elapsed_sec/
    procedure/procedure_leg_index/performance), with individual fields
    overridable per-test so validation tests only vary the field under
    test."""
    kwargs = dict(
        x_nm=0.0,
        y_nm=0.0,
        altitude_ft=5000.0,
        speed_kt=200.0,
        heading_deg=90.0,
        phase=Phase.ENROUTE,
        procedure=OLNEY_2B_SID,
        procedure_leg_index=0,
        performance=next(iter(FLEET.values())),
    )
    kwargs.update(overrides)
    return kwargs


def test_interpolate_does_not_mutate_inputs():
    prev = AircraftSnapshot(x_nm=0.0, y_nm=200.0, heading_deg=90.0)
    curr = AircraftSnapshot(x_nm=100.0, y_nm=200.0, heading_deg=90.0)

    result = interpolate(prev, curr, 0.5)

    assert prev.x_nm == 0.0
    assert prev.y_nm == 200.0
    assert prev.heading_deg == 90.0
    assert curr.x_nm == 100.0
    assert curr.y_nm == 200.0
    assert curr.heading_deg == 90.0
    assert result is not prev
    assert result is not curr


def test_position_lerp_midpoint():
    prev = AircraftSnapshot(x_nm=0.0, y_nm=200.0, heading_deg=90.0)
    curr = AircraftSnapshot(x_nm=100.0, y_nm=200.0, heading_deg=90.0)

    result = interpolate(prev, curr, 0.5)

    assert result.x_nm == pytest.approx(50.0)
    assert result.y_nm == pytest.approx(200.0)


def test_heading_interpolation_shortest_path():
    # 350deg -> 10deg at alpha=0.5 must pass through 0/360, landing near 0,
    # NOT go the long way round through 180deg.
    prev = AircraftSnapshot(x_nm=0.0, y_nm=0.0, heading_deg=350.0)
    curr = AircraftSnapshot(x_nm=0.0, y_nm=0.0, heading_deg=10.0)
    result = interpolate(prev, curr, 0.5)
    assert _angle_diff(result.heading_deg, 0.0) < 1e-6
    assert _angle_diff(result.heading_deg, 180.0) > 90.0

    # 10deg -> 350deg goes backward through 0 (the shortest path the other way).
    prev2 = AircraftSnapshot(x_nm=0.0, y_nm=0.0, heading_deg=10.0)
    curr2 = AircraftSnapshot(x_nm=0.0, y_nm=0.0, heading_deg=350.0)
    result2 = interpolate(prev2, curr2, 0.5)
    assert _angle_diff(result2.heading_deg, 0.0) < 1e-6

    # A normal, non-boundary-crossing interpolation still behaves like a plain lerp.
    prev3 = AircraftSnapshot(x_nm=0.0, y_nm=0.0, heading_deg=90.0)
    curr3 = AircraftSnapshot(x_nm=0.0, y_nm=0.0, heading_deg=100.0)
    result3 = interpolate(prev3, curr3, 0.5)
    assert result3.heading_deg == pytest.approx(95.0)


def test_large_jump_now_lerps():
    # Phase 2 (Pitfall A): the D-02 wrap-skip special case is gone — a large
    # position jump between snapshots (as real-world-scale coordinates can
    # produce) now interpolates to the midpoint instead of snapping to curr.
    prev = AircraftSnapshot(x_nm=1270.0, y_nm=200.0, heading_deg=90.0)
    curr = AircraftSnapshot(x_nm=5.0, y_nm=200.0, heading_deg=90.0)
    result = interpolate(prev, curr, 0.5)
    assert result.x_nm == pytest.approx(637.5)
    assert result.x_nm != curr.x_nm


def test_capture_state_reads_x_nm_y_nm():
    aircraft = Aircraft(**_valid_aircraft_kwargs(x_nm=12.5, y_nm=-3.25, heading_deg=45.0))
    snapshot = capture_state(aircraft)
    assert snapshot.x_nm == 12.5
    assert snapshot.y_nm == -3.25
    assert snapshot.heading_deg == 45.0


def test_aircraft_rejects_bad_fields():
    with pytest.raises(ValidationError):
        Aircraft(**_valid_aircraft_kwargs(heading_deg=360.0))

    with pytest.raises(ValidationError):
        Aircraft(**_valid_aircraft_kwargs(speed_kt=0.0))

    with pytest.raises(ValidationError):
        Aircraft(**_valid_aircraft_kwargs(altitude_ft=-1.0))


def test_aircraft_validates_on_assignment():
    aircraft = Aircraft(**_valid_aircraft_kwargs())
    with pytest.raises(ValidationError):
        aircraft.heading_deg = 400.0


# --- sim_step phase dispatch (Task 3) --------------------------------------
# Added alongside aircraft.py's per-phase kinematics dispatcher. Exercises
# the small named helpers directly where useful (white-box) as well as the
# top-level sim_step()/transition_to() integration.


def _arrival_aircraft_at_loffo() -> Aircraft:
    """Same fixture shape as tests/test_procedure_following.py's arrival
    scenario: positioned at DET, tracking the LOFFO leg (no altitude
    restriction) of the DET 2A STAR."""
    det_fix = DET_2A_STAR.legs[0].fix
    x_nm, y_nm = project_to_local_xy_nm(det_fix.lat, det_fix.lon)
    return Aircraft(
        x_nm=x_nm,
        y_nm=y_nm,
        altitude_ft=17000.0,
        heading_deg=180.0,
        speed_kt=250.0,
        phase=Phase.DESCENT,
        procedure=DET_2A_STAR,
        procedure_leg_index=1,
        performance=next(iter(FLEET.values())),
    )


def test_taxi_phase_freezes_position_and_accumulates_timer():
    aircraft = Aircraft(
        **_valid_aircraft_kwargs(phase=Phase.TAXI_OUT, x_nm=10.0, y_nm=-5.0, speed_kt=5.0)
    )
    sim_step(aircraft, dt=1.0)
    assert aircraft.x_nm == pytest.approx(10.0)
    assert aircraft.y_nm == pytest.approx(-5.0)
    assert aircraft.phase_elapsed_sec == pytest.approx(1.0)
    assert aircraft.phase == Phase.TAXI_OUT


def test_taxi_out_eventually_transitions_to_departure_roll():
    aircraft = Aircraft(
        **_valid_aircraft_kwargs(phase=Phase.TAXI_OUT, procedure=OLNEY_2B_SID, speed_kt=5.0)
    )
    for _ in range(200):
        sim_step(aircraft, dt=1.0)
        if aircraft.phase != Phase.TAXI_OUT:
            break
    assert aircraft.phase == Phase.DEPARTURE_ROLL
    assert aircraft.phase_elapsed_sec < 1.0  # reset to ~0.0 on the transitioning tick


def test_departure_roll_accelerates_straight_along_runway_heading():
    aircraft = Aircraft(
        **_valid_aircraft_kwargs(
            phase=Phase.DEPARTURE_ROLL,
            heading_deg=EGGW_RUNWAY.heading_deg_mag,
            speed_kt=10.0,
        )
    )
    x0, y0 = aircraft.x_nm, aircraft.y_nm
    sim_step(aircraft, dt=1.0)
    assert aircraft.speed_kt > 10.0  # accelerating
    assert aircraft.heading_deg == pytest.approx(EGGW_RUNWAY.heading_deg_mag)  # no turning
    rad = math.radians(EGGW_RUNWAY.heading_deg_mag)
    expected_distance_nm = (aircraft.speed_kt / 3600.0) * 1.0
    assert aircraft.x_nm == pytest.approx(x0 + math.sin(rad) * expected_distance_nm, abs=1e-6)
    assert aircraft.y_nm == pytest.approx(y0 + math.cos(rad) * expected_distance_nm, abs=1e-6)


def test_departure_roll_transitions_to_climb_at_rotation_speed():
    aircraft = Aircraft(
        **_valid_aircraft_kwargs(
            phase=Phase.DEPARTURE_ROLL,
            heading_deg=EGGW_RUNWAY.heading_deg_mag,
            speed_kt=149.0,
        )
    )
    sim_step(aircraft, dt=5.0)
    assert aircraft.phase == Phase.CLIMB
    assert aircraft.phase_elapsed_sec == pytest.approx(0.0)


def test_airborne_step_turns_toward_magnetic_bearing_and_descends_toward_lookahead():
    aircraft = _arrival_aircraft_at_loffo()
    h0 = aircraft.heading_deg
    a0 = aircraft.altitude_ft

    sim_step(aircraft, dt=1.0)

    leg = aircraft.procedure.legs[1]
    fix_x_nm, fix_y_nm = project_to_local_xy_nm(leg.fix.lat, leg.fix.lon)
    dx, dy = fix_x_nm - aircraft.x_nm, fix_y_nm - aircraft.y_nm
    expected_true_bearing = math.degrees(math.atan2(dx, dy)) % 360.0
    expected_heading = true_to_magnetic(expected_true_bearing)

    # Heading should have moved from its starting value toward the expected
    # magnetic bearing (not overshot it), and altitude should have begun
    # descending toward ABBOT's FL080 look-ahead target (not held at 17000).
    assert aircraft.heading_deg != pytest.approx(h0)
    assert _angle_diff(aircraft.heading_deg, expected_heading) < _angle_diff(h0, expected_heading)
    assert aircraft.altitude_ft < a0


def test_advance_leg_if_reached_is_invoked_from_airborne_step():
    aircraft = _arrival_aircraft_at_loffo()
    leg = aircraft.procedure.legs[aircraft.procedure_leg_index]
    fix_x_nm, fix_y_nm = project_to_local_xy_nm(leg.fix.lat, leg.fix.lon)
    aircraft.x_nm = fix_x_nm
    aircraft.y_nm = fix_y_nm

    sim_step(aircraft, dt=1.0)

    assert aircraft.procedure_leg_index == 2  # advanced LOFFO -> ABBOT


def test_descent_transitions_to_approach_once_legs_exhausted():
    abbot_fix = DET_2A_STAR.legs[-1].fix
    x_nm, y_nm = project_to_local_xy_nm(abbot_fix.lat, abbot_fix.lon)
    aircraft = Aircraft(
        x_nm=x_nm,
        y_nm=y_nm,
        altitude_ft=8000.0,
        heading_deg=180.0,
        speed_kt=220.0,
        phase=Phase.DESCENT,
        procedure=DET_2A_STAR,
        procedure_leg_index=len(DET_2A_STAR.legs) - 1,
        performance=next(iter(FLEET.values())),
    )
    sim_step(aircraft, dt=1.0)
    assert aircraft.procedure_leg_index == len(DET_2A_STAR.legs)
    assert aircraft.phase == Phase.APPROACH


def test_approach_targets_runway_threshold_directly_and_lands_when_close():
    threshold_x_nm, threshold_y_nm = project_to_local_xy_nm(
        EGGW_RUNWAY.threshold_lat, EGGW_RUNWAY.threshold_lon
    )
    aircraft = Aircraft(
        x_nm=threshold_x_nm,
        y_nm=threshold_y_nm - 0.01,
        altitude_ft=10.0,
        heading_deg=EGGW_RUNWAY.heading_deg_mag,
        speed_kt=110.0,
        phase=Phase.APPROACH,
        procedure=DET_2A_STAR,
        procedure_leg_index=len(DET_2A_STAR.legs),
        performance=next(iter(FLEET.values())),
    )
    sim_step(aircraft, dt=1.0)
    assert aircraft.phase == Phase.LANDED


def test_landed_transitions_to_taxi_in_immediately():
    aircraft = Aircraft(
        **_valid_aircraft_kwargs(phase=Phase.LANDED, procedure=DET_2A_STAR, speed_kt=5.0)
    )
    sim_step(aircraft, dt=1.0)
    assert aircraft.phase == Phase.TAXI_IN
    assert aircraft.phase_elapsed_sec == pytest.approx(0.0)


def test_enroute_never_auto_transitions():
    aircraft = Aircraft(**_valid_aircraft_kwargs(phase=Phase.ENROUTE, procedure=OLNEY_2B_SID))
    for _ in range(20):
        sim_step(aircraft, dt=10.0)
    assert aircraft.phase == Phase.ENROUTE
