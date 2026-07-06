"""Headless render smoke test — the automated Nyquist guard for the
otherwise-visual RADAR-01/RADAR-03 (full visual correctness is the
human-verify capstone in plan 01-05).

SDL_VIDEODRIVER must be set to "dummy" BEFORE pygame is imported, so this
test can run in a display-less CI/sandbox environment.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from collections import deque  # noqa: E402

import pygame  # noqa: E402

from atc_sim.navdata.eggw import DET_2A_STAR, EGGW_RUNWAY, OLNEY_2B_SID  # noqa: E402
from atc_sim.render.radar import (  # noqa: E402
    TRAIL_MAX_LEN,
    build_static_background,
    draw_frame,
)
from atc_sim.sim.interpolation import AircraftSnapshot  # noqa: E402


def test_build_and_draw_frame_headless_does_not_raise():
    pygame.init()
    try:
        screen = pygame.display.set_mode((1280, 800))
        background = build_static_background(
            (1280, 800), EGGW_RUNWAY, [OLNEY_2B_SID, DET_2A_STAR]
        )
        snapshot = AircraftSnapshot(x_nm=640.0, y_nm=400.0, heading_deg=45.0)
        trail: deque[tuple[float, float]] = deque(
            [(600.0, 380.0), (620.0, 390.0)], maxlen=TRAIL_MAX_LEN
        )

        draw_frame(screen, background, snapshot, trail)
    finally:
        pygame.quit()
