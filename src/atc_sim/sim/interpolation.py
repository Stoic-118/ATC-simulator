"""Read-only snapshot/interpolation seam between the 2Hz sim tick and the
60fps render loop.

Capturing an immutable snapshot before and after each sim tick and
interpolating between them by alpha = accumulator / tick_dt produces
smooth apparent motion while the authoritative Aircraft state itself
still only changes at the sim's tick rate. `interpolate()` reads two
frozen snapshots and returns a third, throwaway snapshot — it never
mutates the live Aircraft object, which is exactly how CORE-03 ("render
reads state, never mutates it") is satisfied.

This module MUST NOT import pygame — it stays headlessly testable via
pytest with no display, enforced by tests/test_boundary.py.
"""

from pydantic import BaseModel, ConfigDict

from atc_sim.sim.aircraft import Aircraft


class AircraftSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)
    x: float
    y: float
    heading_deg: float


def capture_state(aircraft: Aircraft) -> AircraftSnapshot:
    return AircraftSnapshot(x=aircraft.x, y=aircraft.y, heading_deg=aircraft.heading_deg)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _lerp_angle_deg(a: float, b: float, t: float) -> float:
    """Shortest-path interpolation across the 0/360 wrap boundary."""
    diff = ((b - a + 180) % 360) - 180
    return (a + diff * t) % 360


def interpolate(prev: AircraftSnapshot, curr: AircraftSnapshot, alpha: float) -> AircraftSnapshot:
    # Phase 2 (Pitfall A): the D-02 wrap-skip special case was removed here —
    # sim_step no longer teleport-wraps the aircraft at the canvas edge, so
    # there is no wrap seam to snap across. interpolate() is now always a
    # plain lerp, which is what real-world-scale position jumps require.
    return AircraftSnapshot(
        x=_lerp(prev.x, curr.x, alpha),
        y=_lerp(prev.y, curr.y, alpha),
        heading_deg=_lerp_angle_deg(prev.heading_deg, curr.heading_deg, alpha),
    )
