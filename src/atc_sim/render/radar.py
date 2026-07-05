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

from atc_sim.navdata.geo import PX_PER_NM, project_to_local_xy_nm
from atc_sim.navdata.models import Procedure, Runway
from atc_sim.render.window import (
    AIRCRAFT_COLOR,
    BG_COLOR,
    FIX_COLOR,
    FIX_TEXT_COLOR,
    PROCEDURE_LINE_COLOR,
    RING_COLOR,
    RUNWAY_COLOR,
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

RUNWAY_THRESHOLD_RADIUS_PX = 4
RUNWAY_CENTERLINE_LENGTH_NM = 10.0   # extended approach centerline, in nm

FIX_MARKER_RADIUS_PX = 3
FIX_LABEL_OFFSET_PX = 6           # blit offset so text doesn't overlap the dot
FIX_FONT_SIZE_PX = 14

# Module-level fix-label font cache -- lazily created on first use (text
# rendering is new to this codebase; pygame.font requires pygame.init() to
# have already run, so this must not be created at import time). Follows
# the same "compute once, reuse" philosophy as build_static_background's
# cached surface.
_FIX_FONT: pygame.font.Font | None = None


def _get_fix_font() -> pygame.font.Font:
    global _FIX_FONT
    if _FIX_FONT is None:
        _FIX_FONT = pygame.font.Font(None, FIX_FONT_SIZE_PX)
    return _FIX_FONT


def world_to_screen(
    x_nm: float, y_nm: float, center: tuple[int, int], px_per_nm: float
) -> tuple[int, int]:
    """Final nm -> pixel conversion (+y-flip: north = up = smaller screen
    y). Reused by every static navdata element (runway, fixes, procedures)
    on top of the shared navdata/geo.py projection."""
    screen_x = center[0] + x_nm * px_per_nm
    screen_y = center[1] - y_nm * px_per_nm
    return int(screen_x), int(screen_y)


def _draw_runway(surface: pygame.Surface, runway: Runway) -> None:
    """Draws the runway threshold as a dot and the extended approach
    centerline as a thin line from the threshold, along the reciprocal of
    the runway's magnetic heading (the direction approaching aircraft fly
    in from). Uses the same sin=x/-cos=y compass convention as
    draw_aircraft's heading vector and navdata/geo.py's projection."""
    threshold_x_nm, threshold_y_nm = project_to_local_xy_nm(
        runway.threshold_lat, runway.threshold_lon
    )
    threshold_px = world_to_screen(threshold_x_nm, threshold_y_nm, CENTER, PX_PER_NM)

    reciprocal_rad = math.radians((runway.heading_deg_mag + 180.0) % 360.0)
    centerline_end_x_nm = threshold_x_nm + math.sin(reciprocal_rad) * RUNWAY_CENTERLINE_LENGTH_NM
    centerline_end_y_nm = threshold_y_nm + math.cos(reciprocal_rad) * RUNWAY_CENTERLINE_LENGTH_NM
    centerline_end_px = world_to_screen(centerline_end_x_nm, centerline_end_y_nm, CENTER, PX_PER_NM)

    pygame.draw.aaline(surface, RUNWAY_COLOR, threshold_px, centerline_end_px)
    pygame.draw.circle(surface, RUNWAY_COLOR, threshold_px, RUNWAY_THRESHOLD_RADIUS_PX)


def _draw_procedure(surface: pygame.Surface, procedure: Procedure) -> None:
    """Draws a SID/STAR procedure's fixes and connecting track line.

    Z-order (mirrors draw_aircraft's discipline): (1) the thin procedure
    track line connecting consecutive fixes in leg order, (2) each fix
    marker, (3) each fix's 5-letter name text on top -- so text is never
    occluded by the line/marker. Does NOT render altitude/speed
    restriction text: D-05 defers on-canvas restriction display to Phase 4
    (RADAR-02); restrictions exist only as tested data on the leg models.
    """
    points_px = [
        world_to_screen(*project_to_local_xy_nm(leg.fix.lat, leg.fix.lon), CENTER, PX_PER_NM)
        for leg in procedure.legs
    ]

    if len(points_px) > 1:
        pygame.draw.lines(surface, PROCEDURE_LINE_COLOR, False, points_px, width=1)

    for point_px in points_px:
        pygame.draw.circle(surface, FIX_COLOR, point_px, FIX_MARKER_RADIUS_PX)

    font = _get_fix_font()
    for leg, point_px in zip(procedure.legs, points_px):
        label = font.render(leg.fix.name, True, FIX_TEXT_COLOR)
        surface.blit(label, (point_px[0] + FIX_LABEL_OFFSET_PX, point_px[1] - FIX_LABEL_OFFSET_PX))


def build_static_background(
    size: tuple[int, int], runway: Runway, procedures: list[Procedure]
) -> pygame.Surface:
    """Rendered once at startup and blitted each frame — range rings/sector
    lines/runway symbol/procedure fixes never change, so don't redraw
    primitives every frame."""
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

    _draw_runway(surface, runway)
    for proc in procedures:
        _draw_procedure(surface, proc)

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
