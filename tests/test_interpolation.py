"""Headless tests for Aircraft motion and read-only interpolation.

Covers CORE-03 (render layer never mutates sim state) and RADAR-03
(heading vector must be correct across the 0/360 boundary). No pygame
import anywhere in this file or in the modules under test.
"""

import pytest
from pydantic import ValidationError

from atc_sim.sim.aircraft import CANVAS_HEIGHT, CANVAS_WIDTH, Aircraft, sim_step
from atc_sim.sim.interpolation import AircraftSnapshot, capture_state, interpolate


def _angle_diff(a: float, b: float) -> float:
    """Smallest absolute distance between two angles in degrees, wrap-aware."""
    return abs(((a - b + 180) % 360) - 180)


def test_interpolate_does_not_mutate_inputs():
    prev = AircraftSnapshot(x=0.0, y=200.0, heading_deg=90.0)
    curr = AircraftSnapshot(x=100.0, y=200.0, heading_deg=90.0)

    result = interpolate(prev, curr, 0.5)

    assert prev.x == 0.0
    assert prev.y == 200.0
    assert prev.heading_deg == 90.0
    assert curr.x == 100.0
    assert curr.y == 200.0
    assert curr.heading_deg == 90.0
    assert result is not prev
    assert result is not curr


def test_position_lerp_midpoint():
    prev = AircraftSnapshot(x=0.0, y=200.0, heading_deg=90.0)
    curr = AircraftSnapshot(x=100.0, y=200.0, heading_deg=90.0)

    result = interpolate(prev, curr, 0.5)

    assert result.x == pytest.approx(50.0)
    assert result.y == pytest.approx(200.0)


def test_heading_interpolation_shortest_path():
    # 350deg -> 10deg at alpha=0.5 must pass through 0/360, landing near 0,
    # NOT go the long way round through 180deg.
    prev = AircraftSnapshot(x=0.0, y=0.0, heading_deg=350.0)
    curr = AircraftSnapshot(x=0.0, y=0.0, heading_deg=10.0)
    result = interpolate(prev, curr, 0.5)
    assert _angle_diff(result.heading_deg, 0.0) < 1e-6
    assert _angle_diff(result.heading_deg, 180.0) > 90.0

    # 10deg -> 350deg goes backward through 0 (the shortest path the other way).
    prev2 = AircraftSnapshot(x=0.0, y=0.0, heading_deg=10.0)
    curr2 = AircraftSnapshot(x=0.0, y=0.0, heading_deg=350.0)
    result2 = interpolate(prev2, curr2, 0.5)
    assert _angle_diff(result2.heading_deg, 0.0) < 1e-6

    # A normal, non-boundary-crossing interpolation still behaves like a plain lerp.
    prev3 = AircraftSnapshot(x=0.0, y=0.0, heading_deg=90.0)
    curr3 = AircraftSnapshot(x=0.0, y=0.0, heading_deg=100.0)
    result3 = interpolate(prev3, curr3, 0.5)
    assert result3.heading_deg == pytest.approx(95.0)


def test_wrap_skip_snaps_to_current():
    # A position jump larger than half the canvas width simulates the D-02
    # wrap-at-edge; interpolate() must snap to curr, not lerp across the seam.
    prev = AircraftSnapshot(x=CANVAS_WIDTH - 10.0, y=200.0, heading_deg=90.0)
    curr = AircraftSnapshot(x=5.0, y=200.0, heading_deg=90.0)
    result = interpolate(prev, curr, 0.5)
    assert result.x == curr.x

    # Same behavior for a large y jump.
    prev_y = AircraftSnapshot(x=100.0, y=CANVAS_HEIGHT - 10.0, heading_deg=90.0)
    curr_y = AircraftSnapshot(x=100.0, y=5.0, heading_deg=90.0)
    result_y = interpolate(prev_y, curr_y, 0.5)
    assert result_y.y == curr_y.y


def test_sim_step_moves_along_heading():
    # heading_deg=90 (east): compass convention means x increases, y ~unchanged.
    aircraft = Aircraft(x=100.0, y=200.0, heading_deg=90.0, speed_px_per_sec=60.0)
    sim_step(aircraft, dt=0.5)
    assert aircraft.x > 100.0
    assert aircraft.y == pytest.approx(200.0, abs=1e-6)


def test_sim_step_wraps_at_edge():
    aircraft = Aircraft(x=CANVAS_WIDTH - 5.0, y=200.0, heading_deg=90.0, speed_px_per_sec=60.0)
    sim_step(aircraft, dt=0.5)
    assert 0.0 <= aircraft.x < CANVAS_WIDTH
    assert aircraft.x < 100.0


def test_aircraft_rejects_bad_fields():
    with pytest.raises(ValidationError):
        Aircraft(x=0.0, y=0.0, heading_deg=360.0, speed_px_per_sec=60.0)

    with pytest.raises(ValidationError):
        Aircraft(x=0.0, y=0.0, heading_deg=90.0, speed_px_per_sec=0.0)
