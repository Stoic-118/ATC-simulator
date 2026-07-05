"""Shared geodesic math for both the radar projection (render/radar.py) and
future separation-check math (sim/separation.py).

Uses geographiclib.Geodesic.WGS84 for all bearing/distance calculations so
the display and the separation logic can never visually disagree
(RADAR-04 / Pitfall 5).

This module MUST NOT import pygame — it stays headlessly testable via
pytest with no display, enforced by tests/test_boundary.py.
"""

import math

from geographiclib.geodesic import Geodesic

_GEOD = Geodesic.WGS84

# EGGW runway 25 threshold — the project's projection origin. Real, current
# UK AIP RWY 25 data (see 02-RESEARCH.md "Critical Finding" for why the
# project's internal identifier is "25", matching the current chart label).
# Charted DMS: 51°52'37.36"N, 000°21'16.15"W [VERIFIED: UK AIP eAIP]
ORIGIN_LAT = 51.877044
ORIGIN_LON = -0.354486

# Nautical miles per pixel — see 02-RESEARCH.md "Scale & Range Selection".
# Chosen so RING_STEP_PX (80px, render/radar.py) represents exactly 10nm per
# ring, and the farthest selected real fix (DET, ~50nm) fits inside the
# existing 1280x800 canvas without clipping.
PX_PER_NM = 8.0

# EGGW magnetic variation, positive = East. This is the ONLY constant used
# to convert between true and magnetic anywhere in the codebase (NAV-03).
# See 02-RESEARCH.md "Magnetic Variation" for full sourcing.
MAGNETIC_VARIATION_DEG = 1.2


def true_bearing_and_distance_nm(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> tuple[float, float]:
    """Returns (true_bearing_deg, distance_nm) from point1 to point2.

    This is the ONE function both the radar projection and (later)
    separation.py should call for geodesic distance/bearing — never
    reimplement haversine or a flat-earth approximation elsewhere.
    """
    result = _GEOD.Inverse(lat1, lon1, lat2, lon2)
    bearing_deg = result["azi1"] % 360.0
    distance_nm = result["s12"] / 1852.0  # metres -> nautical miles
    return bearing_deg, distance_nm


def project_to_local_xy_nm(lat: float, lon: float) -> tuple[float, float]:
    """Local tangent-plane offset from ORIGIN, in nautical miles.
    x is east-positive, y is north-positive (screen conversion happens
    in the render layer, which flips y and applies PX_PER_NM).

    Cosine correction is implicit: because this is true geodesic azimuth/
    distance (not raw degree scaling), a point due east and a point due
    north at the same real distance always produce the same magnitude
    here — satisfying "range rings render as true circles" by
    construction, not by manually multiplying longitude by cos(lat).

    Compass convention matches sim/aircraft.py's sim_step: 0deg = north,
    increasing clockwise, sin=x, cos=y.
    """
    bearing_deg, distance_nm = true_bearing_and_distance_nm(
        ORIGIN_LAT, ORIGIN_LON, lat, lon
    )
    rad = math.radians(bearing_deg)
    x_nm = distance_nm * math.sin(rad)
    y_nm = distance_nm * math.cos(rad)
    return x_nm, y_nm


def true_to_magnetic(true_deg: float, variation_deg: float = MAGNETIC_VARIATION_DEG) -> float:
    """The ONE place a geographiclib-computed TRUE bearing becomes a
    magnetic value for comparison against/display alongside charted
    (already-magnetic) courses. Mnemonic: variation east, magnetic least
    (subtract); variation west, magnetic best (add) — implemented here as
    subtraction since EGGW's variation is East (positive)."""
    return (true_deg - variation_deg) % 360.0


def magnetic_to_true(mag_deg: float, variation_deg: float = MAGNETIC_VARIATION_DEG) -> float:
    return (mag_deg + variation_deg) % 360.0
