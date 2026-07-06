"""Per-aircraft-type performance profiles and the shared kinematics helpers
that move an aircraft toward a target at its type's limits (PERF-01).

`PerformanceProfile` is frozen reference data — "facts about an aircraft
type," not the state of any specific aircraft instance — mirroring the
navdata convention already established for runway/ILS/procedure data. A
small fleet of hand-authored constants spans a wide performance envelope
(narrowbody jet, regional jet, turboprop, light jet) so behavioral
differentiation between types (success criterion #1) falls directly out of
these numbers plus the speed-coupled turn-rate formula below — no new
visual symbol system is needed (D-04).

This module MUST NOT import pygame — it stays headlessly testable via
pytest with no display, enforced by tests/test_boundary.py.
"""

import math

from pydantic import BaseModel, ConfigDict, Field


class PerformanceProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    category: str
    climb_rate_fpm: float = Field(gt=0.0)
    descent_rate_fpm: float = Field(gt=0.0)  # nominal enroute/STAR descent, NOT final glidepath
    terminal_speed_kt: float = Field(gt=0.0)  # below-FL100 operating speed; NOT high-altitude cruise
    approach_speed_kt: float = Field(gt=0.0)  # Vref-equivalent, used once established on APPROACH
    max_bank_deg: float = Field(gt=0.0, lt=45.0)
    max_speed_change_kt_per_sec: float = Field(gt=0.0)


# Fleet of 4, spanning a wide performance envelope (03-RESEARCH.md "Standard
# Stack: Aircraft Fleet"). These are simplified in-sim terminal-area values,
# NOT the raw real-world Mach-cruise performance numbers for these types —
# see 03-RESEARCH.md's "Critical adaptation" note for why the real-world
# cruise figures would be meaningless inside this sim's terminal-area-only
# scope (single airport, IFR departures/arrivals, no enroute cruise phase).

# Boeing 737-800 [ASSUMED: simplified narrowbody-jet terminal-area values,
# adapted from published climb/descent/approach-speed performance figures —
# not a BADA-style lookup table, per the project's explicit fidelity
# constraint]
BOEING_737_800 = PerformanceProfile(
    name="Boeing 737-800",
    category="narrowbody_jet",
    climb_rate_fpm=1800,
    descent_rate_fpm=1500,
    terminal_speed_kt=250,
    approach_speed_kt=140,
    max_bank_deg=25.0,
    max_speed_change_kt_per_sec=1.5,
)

# Embraer E175 [ASSUMED: simplified regional-jet terminal-area values —
# faster climb/descent than the 737-800 reflects its lower operating
# weight, per 03-RESEARCH.md]
EMBRAER_E175 = PerformanceProfile(
    name="Embraer E175",
    category="regional_jet",
    climb_rate_fpm=2200,
    descent_rate_fpm=1800,
    terminal_speed_kt=250,
    approach_speed_kt=130,
    max_bank_deg=25.0,
    max_speed_change_kt_per_sec=1.8,
)

# ATR 72-600 [ASSUMED: simplified turboprop terminal-area values — the
# slowest and shallowest-climbing type in the fleet, distinguishing
# turboprop behavior from the three jet types]
ATR_72_600 = PerformanceProfile(
    name="ATR 72-600",
    category="turboprop",
    climb_rate_fpm=1350,
    descent_rate_fpm=1000,
    terminal_speed_kt=180,
    approach_speed_kt=110,
    max_bank_deg=22.0,
    max_speed_change_kt_per_sec=1.2,
)

# Cessna Citation CJ2+ [ASSUMED: simplified light-jet terminal-area values —
# the fastest-climbing, most agile (highest max bank) type in the fleet]
CESSNA_CJ2_PLUS = PerformanceProfile(
    name="Cessna Citation CJ2+",
    category="light_jet",
    climb_rate_fpm=3500,
    descent_rate_fpm=2000,
    terminal_speed_kt=220,
    approach_speed_kt=105,
    max_bank_deg=27.0,
    max_speed_change_kt_per_sec=2.0,
)

FLEET: dict[str, PerformanceProfile] = {
    p.name: p for p in (BOEING_737_800, EMBRAER_E175, ATR_72_600, CESSNA_CJ2_PLUS)
}


def turn_rate_deg_per_sec(bank_deg: float, speed_kt: float) -> float:
    """[CITED: SKYbrary "Rate Of Turn"] ROT = 1091 * tan(bank) / speed(kt).

    This is the ONE turn-rate formula in the codebase — call it with the
    aircraft's CURRENT groundspeed (not a fixed per-type constant) so
    per-type turn differences emerge naturally from differing terminal
    speeds, satisfying 03-RESEARCH.md Pitfall 7 (coupling, not independent
    knobs): a faster aircraft turns more slowly at the same bank angle.
    """
    return (1091.0 * math.tan(math.radians(bank_deg))) / speed_kt


def step_toward_value(current: float, target: float, max_delta: float) -> float:
    """The ONE place a scalar value (altitude, speed) moves toward a target
    by at most `max_delta` per tick, never overshooting. Reused for both
    altitude (max_delta = rate_fpm / 60 * dt) and speed
    (max_delta = max_speed_change_kt_per_sec * dt) — selecting climb_rate_fpm
    vs descent_rate_fpm (target above vs below current) is the CALLER's
    responsibility (done in aircraft.py's dispatch, plan 03-04)."""
    if current == target:
        return current
    if current < target:
        return min(current + max_delta, target)
    return max(current - max_delta, target)


def step_toward_heading(current_deg: float, target_deg: float, max_turn_deg: float) -> float:
    """Turns `current_deg` toward `target_deg` by at most `max_turn_deg`,
    along the shortest angular path across the 0/360 wrap, never
    overshooting. Mirrors the wrap logic in
    sim/interpolation.py::_lerp_angle_deg. Compass convention matches
    navdata/geo.py: 0deg = north, increasing clockwise, sin=x, cos=y — do
    not reinvent a different sign convention here."""
    diff = ((target_deg - current_deg + 180) % 360) - 180
    if diff > 0:
        turn = min(diff, max_turn_deg)
    else:
        turn = max(diff, -max_turn_deg)
    return (current_deg + turn) % 360


def glidepath_altitude_ft(distance_to_threshold_nm: float) -> float:
    """Simplified 3-degree "rule of three" glidepath altitude: 300ft per nm
    from the threshold, clamped to >= 0.0. This is NOT real
    localizer/glideslope geometry — it is used only by the APPROACH phase
    in a later plan, per 03-RESEARCH.md Pattern C."""
    return max(distance_to_threshold_nm * 300.0, 0.0)
