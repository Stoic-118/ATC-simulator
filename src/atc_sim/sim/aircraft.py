"""Authoritative Aircraft state model and its Phase-1 motion.

D-02: simplest possible motion for the walking skeleton — a single
aircraft flies a straight line at a fixed heading (no real navdata/lat-lon
yet). `sim_step` mutates the one authoritative Aircraft instance and must
only ever be called from SimClock.advance()'s on_tick callback — never
from the render loop.

Phase 2 (Pitfall A): the Phase-1 canvas-edge wrap-around was removed from
`sim_step` — real-world-scale navdata paths replace it, so the aircraft
now flies a straight, non-wrapping line.

This module MUST NOT import pygame — it stays headlessly testable via
pytest with no display, enforced by tests/test_boundary.py.
"""

import math

from pydantic import BaseModel, ConfigDict, Field

CANVAS_WIDTH = 1280   # D-03: fixed window size, no resize in Phase 1
CANVAS_HEIGHT = 800


class Aircraft(BaseModel):
    model_config = ConfigDict(validate_assignment=True)  # v2 style; catches bad mutations

    x: float
    y: float
    heading_deg: float = Field(ge=0.0, lt=360.0)
    speed_px_per_sec: float = Field(gt=0.0)

    @classmethod
    def spawn_default(cls) -> "Aircraft":
        # Phase 2: spawn at the radar center (CANVAS_WIDTH/2, CANVAS_HEIGHT/2 =
        # pixel (640, 400)), which is the runway-threshold projection origin
        # per navdata/geo.py's ORIGIN — so the placeholder aircraft starts
        # within the real EGGW geography instead of a canvas corner. Still
        # Phase-1-level placeholder motion (straight line, fixed heading,
        # no procedure following).
        return cls(x=CANVAS_WIDTH / 2, y=CANVAS_HEIGHT / 2, heading_deg=90.0, speed_px_per_sec=60.0)


def sim_step(aircraft: Aircraft, dt: float) -> None:
    """Mutates the single authoritative Aircraft instance. Called only from
    SimClock.advance()'s on_tick callback — never from the render loop.

    Compass convention: heading_deg=0 is north/up, increasing clockwise.
    """
    rad = math.radians(aircraft.heading_deg)
    aircraft.x += math.sin(rad) * aircraft.speed_px_per_sec * dt
    aircraft.y -= math.cos(rad) * aircraft.speed_px_per_sec * dt
    # Phase 2 (Pitfall A): the D-02 canvas-edge wrap-around was removed here —
    # real-world-scale navdata paths replace it, so motion is now a pure,
    # non-wrapping straight line.
