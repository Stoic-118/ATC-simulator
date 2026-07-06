"""Procedure-following (PROC-01): compute_target() with restriction
look-ahead and once-only true->magnetic heading conversion, plus simplified
fly-by leg sequencing.

This module MUST NOT import pygame — it stays headlessly testable via
pytest with no display, enforced by tests/test_boundary.py.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from atc_sim.navdata.geo import project_to_local_xy_nm, true_to_magnetic

if TYPE_CHECKING:
    # Type-hint-only import: aircraft.py imports this module at runtime, so
    # importing Aircraft here at runtime would create a circular import.
    from atc_sim.sim.aircraft import Aircraft


@dataclass(frozen=True)
class Targets:
    """Recomputed every tick -- a plain dataclass, not Pydantic, matching
    the project's convention for hot-path per-tick structures."""

    heading_deg: float  # MAGNETIC — see compute_target()'s Pitfall 4 note
    altitude_ft: float
    speed_kt: float


def _next_altitude_restriction_ft(aircraft: "Aircraft") -> float:
    """Looks ahead from the CURRENT leg onward for the next altitude
    restriction (any kind); falls back to the aircraft's current altitude
    if none remain on the procedure. This is what makes DET STAR's
    unrestricted LOFFO leg produce a continuous descent toward ABBOT's
    FL080, rather than a level-then-snap profile (Pitfall 7)."""
    legs = aircraft.procedure.legs[aircraft.procedure_leg_index :]
    for leg in legs:
        if leg.altitude_restriction is not None:
            return float(leg.altitude_restriction.altitude_ft)
    return aircraft.altitude_ft  # no more restrictions ahead — hold


def _next_speed_restriction_kt(aircraft: "Aircraft") -> float:
    legs = aircraft.procedure.legs[aircraft.procedure_leg_index :]
    for leg in legs:
        if leg.speed_restriction is not None:
            return float(leg.speed_restriction.speed_kt)
    return aircraft.performance.terminal_speed_kt


def compute_target(aircraft: "Aircraft") -> Targets:
    """Computes the current leg's heading/altitude/speed targets. Reuses
    navdata/geo.py's project_to_local_xy_nm/true_to_magnetic — never
    reimplements bearing/distance math here."""
    leg = aircraft.procedure.legs[aircraft.procedure_leg_index]
    fix_x_nm, fix_y_nm = project_to_local_xy_nm(leg.fix.lat, leg.fix.lon)
    dx = fix_x_nm - aircraft.x_nm
    dy = fix_y_nm - aircraft.y_nm
    # sin=x/cos=y convention, matching aircraft.py/geo.py — 0deg = north,
    # increasing clockwise.
    true_bearing = math.degrees(math.atan2(dx, dy)) % 360.0
    heading_deg = true_to_magnetic(true_bearing)  # Pitfall 4: convert true->magnetic exactly once

    return Targets(
        heading_deg=heading_deg,
        altitude_ft=_next_altitude_restriction_ft(aircraft),
        speed_kt=_next_speed_restriction_kt(aircraft),
    )


def advance_leg_if_reached(aircraft: "Aircraft", capture_radius_nm: float = 1.0) -> None:
    """Fly-by-style simplified fix sequencing: once within capture_radius_nm
    of the current leg's fix, advance to the next leg. Uses simple planar
    distance in the shared local-nm coordinate system (both aircraft and
    fix are already in that space — no geodesic call needed per tick).
    [ASSUMED] simplification of real FMS fly-by/fly-over logic, acceptable
    for v1 (Pitfall 11: don't over-invest fidelity before the end-to-end
    loop works).

    No-ops once procedure_leg_index has already exhausted the procedure's
    legs (e.g. once an arrival has reached APPROACH) — index sequencing
    past the last leg is left to demo_traffic's removal check, not this
    function."""
    if aircraft.procedure_leg_index >= len(aircraft.procedure.legs):
        return
    leg = aircraft.procedure.legs[aircraft.procedure_leg_index]
    fix_x_nm, fix_y_nm = project_to_local_xy_nm(leg.fix.lat, leg.fix.lon)
    distance_nm = math.hypot(fix_x_nm - aircraft.x_nm, fix_y_nm - aircraft.y_nm)
    if distance_nm <= capture_radius_nm:
        aircraft.procedure_leg_index += 1
