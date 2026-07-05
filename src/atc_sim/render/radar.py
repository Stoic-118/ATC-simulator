"""Radar canvas drawing: static background (rings/sector lines) and the
live aircraft symbol (trail, heading vector, dot).

This module reads only a frozen render_state (an AircraftSnapshot-shaped
object produced by atc_sim.sim.interpolation, read via duck typing — this
module deliberately avoids importing atc_sim.sim.* at all, so app.py stays
the only module importing BOTH pygame and atc_sim.sim.*). It never imports
or calls a mutator from atc_sim.sim.aircraft (RADAR-03/CORE-03's read-only
render path). The trail deque is owned and appended-to by app.py once per
sim tick; this module only reads it.

src/atc_sim/render/ legitimately imports pygame — the sim/render boundary
guard (tests/test_boundary.py) only scans src/atc_sim/sim/.
"""

import math
from collections import deque
from typing import Protocol

import pygame

from atc_sim.render.window import (
    AIRCRAFT_COLOR,
    BG_COLOR,
    RING_COLOR,
    SECTOR_COLOR,
    TRAIL_COLOR,
    VECTOR_COLOR,
)


class RenderState(Protocol):
    """Structural type for a frozen AircraftSnapshot — avoids a runtime
    import of atc_sim.sim.interpolation so this pygame-importing module
    never also imports atc_sim.sim.* (app.py is the sole exception)."""

    x: float
    y: float
    heading_deg: float


CENTER = (640, 400)              # canvas center, fixed 1280x800 window (D-03)
RING_STEP_PX = 80
NUM_RINGS = 4
NUM_SECTOR_LINES = 8             # every 45 degrees

TRAIL_MAX_LEN = 8                # number of past sim-tick positions retained
AIRCRAFT_RADIUS_PX = 5
VECTOR_LENGTH_PX = 40


def build_static_background(size: tuple[int, int]) -> pygame.Surface:
    """Rendered once at startup and blitted each frame — range rings/sector
    lines never change, so don't redraw primitives every frame."""
    surface = pygame.Surface(size)
    surface.fill(BG_COLOR)

    for i in range(1, NUM_RINGS + 1):
        pygame.draw.circle(surface, RING_COLOR, CENTER, RING_STEP_PX * i, width=1)

    for i in range(NUM_SECTOR_LINES):
        angle = math.radians(360 / NUM_SECTOR_LINES * i)
        end = (
            CENTER[0] + math.sin(angle) * RING_STEP_PX * NUM_RINGS,
            CENTER[1] - math.cos(angle) * RING_STEP_PX * NUM_RINGS,
        )
        pygame.draw.aaline(surface, SECTOR_COLOR, CENTER, end)

    return surface


def draw_aircraft(
    surface: pygame.Surface,
    x: float,
    y: float,
    heading_deg: float,
    trail: deque[tuple[float, float]],
) -> None:
    """Draws in z-order trail -> heading vector -> dot, so the dot is never
    occluded by its own trail/vector."""
    # Trail: oldest points fainter/smaller — fixed-length deque handles aging out
    for age, (tx, ty) in enumerate(trail):
        fade = 1.0 - (age / max(len(trail), 1))
        radius = max(1, int(AIRCRAFT_RADIUS_PX * 0.4 * fade))
        pygame.draw.circle(surface, TRAIL_COLOR, (int(tx), int(ty)), radius)

    # Heading vector: from aircraft position, pointing along heading_deg
    # (0 deg = up/north, clockwise, matching the compass/radar convention)
    rad = math.radians(heading_deg)
    end = (x + math.sin(rad) * VECTOR_LENGTH_PX, y - math.cos(rad) * VECTOR_LENGTH_PX)
    pygame.draw.aaline(surface, VECTOR_COLOR, (x, y), end)

    # Aircraft dot, drawn last so it sits above its own trail/vector
    pygame.draw.circle(surface, AIRCRAFT_COLOR, (int(x), int(y)), AIRCRAFT_RADIUS_PX)


def draw_frame(
    screen: pygame.Surface,
    background: pygame.Surface,
    render_state: RenderState,
    trail: deque[tuple[float, float]],
) -> None:
    """Blits the cached background then draws the aircraft from a frozen
    AircraftSnapshot. render_state is read-only here — never assigned to
    (CORE-03); the trail deque is owned/updated by app.py, appended once
    per sim tick, not by this render layer."""
    screen.blit(background, (0, 0))
    draw_aircraft(screen, render_state.x, render_state.y, render_state.heading_deg, trail)
