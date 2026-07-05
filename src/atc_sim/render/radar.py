"""Radar canvas drawing: static background (rings/sector lines).

src/atc_sim/render/ legitimately imports pygame — the sim/render boundary
guard (tests/test_boundary.py) only scans src/atc_sim/sim/.
"""

import math

import pygame

from atc_sim.render.window import BG_COLOR, RING_COLOR, SECTOR_COLOR

CENTER = (640, 400)              # canvas center, fixed 1280x800 window (D-03)
RING_STEP_PX = 80
NUM_RINGS = 4
NUM_SECTOR_LINES = 8             # every 45 degrees


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
