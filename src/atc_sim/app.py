"""Composition root: the only module that imports BOTH pygame and
atc_sim.sim.*.

Runs the fixed-timestep accumulator (SimClock) each frame, captures
prev/curr sim-tick snapshots, interpolates between them for smooth 60fps
rendering, and draws the interpolated (never the live, mutable) Aircraft
state. All position mutation happens inside on_tick, called only from
SimClock.advance() — never in the render section using per-frame dt
(CORE-01/CORE-02). The trail deque is appended to once per sim tick, inside
on_tick, never once per render frame, so it represents true sim-tick
history rather than a dense cloud of near-duplicate interpolated positions.
"""

import collections

import pygame

from atc_sim.render.radar import TRAIL_MAX_LEN, build_static_background, draw_frame
from atc_sim.render.window import FPS_CAP, create_window
from atc_sim.sim.aircraft import Aircraft, sim_step
from atc_sim.sim.clock import SimClock
from atc_sim.sim.interpolation import capture_state, interpolate


def main() -> None:
    pygame.init()
    screen = create_window()
    pg_clock = pygame.time.Clock()
    sim_clock = SimClock()
    aircraft = Aircraft.spawn_default()

    background = build_static_background(screen.get_size())
    trail: collections.deque[tuple[float, float]] = collections.deque(maxlen=TRAIL_MAX_LEN)

    prev_state = capture_state(aircraft)
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        real_dt = pg_clock.tick(FPS_CAP) / 1000.0

        def on_tick(dt: float) -> None:
            nonlocal prev_state
            prev_state = capture_state(aircraft)
            sim_step(aircraft, dt)
            # Trail is appended once per sim tick (here), never once per
            # render frame — a ~4s sim-tick history, not a dense render cloud.
            trail.append((aircraft.x, aircraft.y))

        alpha = sim_clock.advance(real_dt, on_tick)
        curr_state = capture_state(aircraft)
        render_state = interpolate(prev_state, curr_state, alpha)

        draw_frame(screen, background, render_state, trail)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
