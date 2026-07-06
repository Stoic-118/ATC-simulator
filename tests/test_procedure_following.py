"""Headless tests for procedure-following (PROC-01): compute_target()'s
restriction look-ahead + true->magnetic heading conversion, and
advance_leg_if_reached()'s fix-capture leg sequencing. Guards its imports
of the not-yet-existing atc_sim.sim.procedure / atc_sim.sim.aircraft
modules so this file is skipped until Phase 3's procedure.py/aircraft.py
implementation plans land.
"""

import math

import pytest

pytest.importorskip("atc_sim.sim.procedure")
pytest.importorskip("atc_sim.sim.aircraft")

from atc_sim.navdata.eggw import DET_2A_STAR
from atc_sim.navdata.geo import project_to_local_xy_nm, true_to_magnetic
from atc_sim.sim.aircraft import Aircraft
from atc_sim.sim.performance import FLEET
from atc_sim.sim.phase import Phase
from atc_sim.sim.procedure import advance_leg_if_reached, compute_target

_LOFFO_LEG_INDEX = 1  # DET_2A_STAR.legs: [DET, LOFFO, ABBOT] -- LOFFO has NO altitude_restriction


def _arrival_at_loffo_leg() -> Aircraft:
    """Build an arrival Aircraft positioned at the DET fix, on the DET 2A
    STAR, with procedure_leg_index already pointing at the LOFFO leg -- the
    leg that carries NO altitude restriction. This is the exact scenario
    03-RESEARCH.md's 'Restriction look-ahead omitted' pitfall requires a
    regression test for."""
    det_fix = DET_2A_STAR.legs[0].fix
    x_nm, y_nm = project_to_local_xy_nm(det_fix.lat, det_fix.lon)
    performance = next(iter(FLEET.values()))
    return Aircraft(
        x_nm=x_nm,
        y_nm=y_nm,
        altitude_ft=17000,
        heading_deg=180.0,
        speed_kt=250.0,
        phase=Phase.DESCENT,
        procedure=DET_2A_STAR,
        procedure_leg_index=_LOFFO_LEG_INDEX,
        performance=performance,
    )


def _expected_true_bearing_deg(aircraft: Aircraft, fix_lat: float, fix_lon: float) -> float:
    """Replicates compute_target()'s own local-plane bearing math (not a
    fresh geodesic call) so the expected value is computed the same way
    the implementation must compute it -- per the task's own instruction to
    derive expected geometric values from navdata.geo helpers, not magic
    numbers."""
    fix_x_nm, fix_y_nm = project_to_local_xy_nm(fix_lat, fix_lon)
    dx, dy = fix_x_nm - aircraft.x_nm, fix_y_nm - aircraft.y_nm
    return math.degrees(math.atan2(dx, dy)) % 360.0


def test_compute_target_looks_ahead_past_unrestricted_leg():
    """PROC-01 / Pitfall 7 regression: LOFFO carries no altitude
    restriction, so compute_target() must look ahead to ABBOT's FL080
    rather than holding the aircraft's current altitude (17000ft), which
    would produce a level-then-snap profile instead of a continuous
    descent."""
    aircraft = _arrival_at_loffo_leg()

    targets = compute_target(aircraft)

    assert targets.altitude_ft == 8000  # ABBOT FL080 look-ahead, NOT 17000 held level


def test_compute_target_heading_is_magnetic():
    """Any atan2-derived bearing must be passed through true_to_magnetic()
    exactly once before being returned as Targets.heading_deg (Pitfall 4)."""
    aircraft = _arrival_at_loffo_leg()

    targets = compute_target(aircraft)

    leg = aircraft.procedure.legs[aircraft.procedure_leg_index]
    expected_true_bearing_deg = _expected_true_bearing_deg(aircraft, leg.fix.lat, leg.fix.lon)
    expected_heading_deg = true_to_magnetic(expected_true_bearing_deg)

    assert targets.heading_deg == pytest.approx(expected_heading_deg, abs=0.5)


def test_advance_leg_if_reached_increments_leg_index_within_capture_radius():
    aircraft = _arrival_at_loffo_leg()
    leg = aircraft.procedure.legs[aircraft.procedure_leg_index]
    fix_x_nm, fix_y_nm = project_to_local_xy_nm(leg.fix.lat, leg.fix.lon)

    # Place the aircraft essentially on top of its current leg's fix.
    aircraft.x_nm = fix_x_nm
    aircraft.y_nm = fix_y_nm

    advance_leg_if_reached(aircraft)

    assert aircraft.procedure_leg_index == _LOFFO_LEG_INDEX + 1  # advanced LOFFO -> ABBOT
