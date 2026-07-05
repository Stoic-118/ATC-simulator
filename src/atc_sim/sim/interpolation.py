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

from atc_sim.sim.aircraft import CANVAS_HEIGHT, CANVAS_WIDTH, Aircraft


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
    # D-02 wrap-skip edge case: a position jump greater than half the canvas
    # dimension between snapshots means the sim tick wrapped the aircraft at
    # the canvas edge. Lerping across that seam would draw a fast streak
    # across the whole canvas for one interpolation window, so snap straight
    # to curr instead. Phase-1-only special case — removed once Phase 2
    # replaces wrap-at-edge with real navdata paths; do not generalize.
    if abs(curr.x - prev.x) > CANVAS_WIDTH / 2 or abs(curr.y - prev.y) > CANVAS_HEIGHT / 2:
        return curr

    return AircraftSnapshot(
        x=_lerp(prev.x, curr.x, alpha),
        y=_lerp(prev.y, curr.y, alpha),
        heading_deg=_lerp_angle_deg(prev.heading_deg, curr.heading_deg, alpha),
    )
