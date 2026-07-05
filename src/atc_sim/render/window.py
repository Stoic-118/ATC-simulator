"""Render-side window setup and shared constants.

This module (and everything under src/atc_sim/render/) legitimately imports
pygame — the sim/render boundary guard (tests/test_boundary.py) only scans
src/atc_sim/sim/, which this package is not part of.

Color palette matches the D-01 "modern flat display, dark grey/blue
background, white/cyan elements" decision (see
.planning/phases/01-walking-skeleton-sim-clock-radar-render-loop/01-UI-SPEC.md
Color table) and RESEARCH.md's Code Examples section, so research, plan, and
implementation all reference the same numbers.
"""

import pygame

WINDOW_SIZE = (1280, 800)  # D-03: fixed window size, no resize in Phase 1
FPS_CAP = 60
WINDOW_CAPTION = "ATC Simulator — Walking Skeleton (Phase 1)"

# D-01 color palette
BG_COLOR = (18, 24, 32)          # dark grey/blue
RING_COLOR = (60, 90, 100)       # muted cyan-grey
SECTOR_COLOR = (40, 60, 68)
AIRCRAFT_COLOR = (0, 220, 220)   # cyan
TRAIL_COLOR = (0, 140, 140)
VECTOR_COLOR = (230, 240, 240)   # near-white
RUNWAY_COLOR = (180, 190, 195)   # muted white/grey, Phase 2 runway symbol


def create_window() -> pygame.Surface:
    """Creates the fixed-size application window and returns the screen surface."""
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption(WINDOW_CAPTION)
    return screen
