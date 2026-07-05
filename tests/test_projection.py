"""Headless tests for the shared cosine-corrected geodesic projection and
the single true<->magnetic boundary in atc_sim.navdata.geo.

No pygame import anywhere in this file or in the module under test.
"""

import math

import pytest
from geographiclib.geodesic import Geodesic

from atc_sim.navdata.geo import (
    ORIGIN_LAT,
    ORIGIN_LON,
    PX_PER_NM,
    magnetic_to_true,
    project_to_local_xy_nm,
    true_bearing_and_distance_nm,
    true_to_magnetic,
)


def test_projection_is_circular_not_elliptical():
    """RADAR-04 / Pitfall 5: a point 10nm due north of ORIGIN and a point
    10nm due east of ORIGIN (ground truth derived independently via
    Geodesic.WGS84.Direct) must both produce a pixel-space magnitude within
    tolerance of 10 * PX_PER_NM — equal magnitude in both bearings proves
    range rings render as circles, not ellipses."""
    north = Geodesic.WGS84.Direct(ORIGIN_LAT, ORIGIN_LON, 0.0, 10 * 1852)
    east = Geodesic.WGS84.Direct(ORIGIN_LAT, ORIGIN_LON, 90.0, 10 * 1852)

    north_x_nm, north_y_nm = project_to_local_xy_nm(north["lat2"], north["lon2"])
    east_x_nm, east_y_nm = project_to_local_xy_nm(east["lat2"], east["lon2"])

    north_mag_px = math.hypot(north_x_nm, north_y_nm) * PX_PER_NM
    east_mag_px = math.hypot(east_x_nm, east_y_nm) * PX_PER_NM

    assert north_mag_px == pytest.approx(10 * PX_PER_NM, abs=0.01)
    assert east_mag_px == pytest.approx(10 * PX_PER_NM, abs=0.01)


def test_magnetic_variation_boundary():
    # Round-trip across several angles, including near the 0/360 wrap.
    for true_deg in (0.0, 0.5, 90.0, 180.0, 270.0, 359.9, 254.4):
        assert magnetic_to_true(true_to_magnetic(true_deg)) == pytest.approx(true_deg, abs=1e-6)

    # EGGW's variation is +1.2 East -> magnetic = true - variation.
    assert true_to_magnetic(254.4) == pytest.approx(253.2, abs=1e-6)


def test_true_bearing_and_distance_nm():
    _, distance_to_self_nm = true_bearing_and_distance_nm(ORIGIN_LAT, ORIGIN_LON, ORIGIN_LAT, ORIGIN_LON)
    assert distance_to_self_nm == pytest.approx(0.0, abs=1e-6)

    # BNN (Bovingdon VOR/DME) — ~11.2nm from the RWY 25 threshold origin,
    # per 02-RESEARCH.md "Scale & Range Selection".
    bnn_lat, bnn_lon = 51.726111, -0.549722
    _, distance_to_bnn_nm = true_bearing_and_distance_nm(ORIGIN_LAT, ORIGIN_LON, bnn_lat, bnn_lon)
    assert distance_to_bnn_nm == pytest.approx(11.2, abs=0.1)
