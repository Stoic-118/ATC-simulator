"""Composition root: the only module that imports BOTH pygame and
atc_sim.sim.*.

Runs the fixed-timestep accumulator (SimClock) each frame, captures a
per-aircraft prev/curr sim-tick snapshot pair for every active aircraft,
interpolates between them for smooth 60fps rendering, and draws the
interpolated (never the live, mutable) Aircraft state. All position
mutation happens inside on_tick, called only from SimClock.advance() —
never in the render section using per-frame dt (CORE-01/CORE-02). Each
aircraft's trail deque is appended to once per sim tick, inside on_tick,
never once per render frame, so it represents true sim-tick history rather
than a dense cloud of near-duplicate interpolated positions.

Phase 3 (03-06): the single hardcoded placeholder aircraft
(Aircraft.spawn_default(), removed in 03-04) is replaced by
sim.demo_traffic's continuously looping departure/arrival pair
(spawn_departure/spawn_arrival/update_demo_traffic) — a call-site change
(D-02), not a new architecture. Per-aircraft state (a previous-tick
snapshot plus a trail deque) is tracked in dicts keyed by id(aircraft), so
a newly spawned aircraft gets fresh entries and a removed aircraft cleanly
drops its own, without leaking trail/snapshot state across the loop.
"""

import collections

import pygame

from atc_sim.navdata.eggw import DET_2A_STAR, EGGW_RUNWAY, OLNEY_2B_SID
from atc_sim.render.radar import TRAIL_MAX_LEN, build_static_background, draw_frame
from atc_sim.render.window import FPS_CAP, create_window
from atc_sim.sim import demo_traffic
from atc_sim.sim.aircraft import Aircraft
from atc_sim.sim.clock import SimClock
from atc_sim.sim.interpolation import AircraftSnapshot, capture_state, interpolate


def main() -> None:
    pygame.init()
    screen = create_window()
    pg_clock = pygame.time.Clock()
    sim_clock = SimClock()

    aircraft_list: list[Aircraft] = [demo_traffic.spawn_departure(), demo_traffic.spawn_arrival()]

    background = build_static_background(screen.get_size(), EGGW_RUNWAY, [OLNEY_2B_SID, DET_2A_STAR])

    # Per-aircraft state, keyed by id(aircraft). A key is created the first
    # time an aircraft is seen (initial spawn, or newly respawned by
    # update_demo_traffic) and dropped the tick an aircraft is removed, so
    # trails/snapshots never leak across the continuously looping demo.
    trails: dict[int, collections.deque[tuple[float, float]]] = {}
    prev_snapshots: dict[int, AircraftSnapshot] = {}

    def _ensure_tracked(aircraft: Aircraft) -> None:
        key = id(aircraft)
        if key not in trails:
            trails[key] = collections.deque(maxlen=TRAIL_MAX_LEN)
        if key not in prev_snapshots:
            # Newly spawned this tick: seed prev with curr so interpolation
            # has a valid previous frame instead of lerping from nowhere.
            prev_snapshots[key] = capture_state(aircraft)

    for aircraft in aircraft_list:
        _ensure_tracked(aircraft)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        real_dt = pg_clock.tick(FPS_CAP) / 1000.0

        def on_tick(dt: float) -> None:
            # Capture every currently-active aircraft's prev snapshot BEFORE
            # this tick mutates it (sim_step runs inside update_demo_traffic).
            for aircraft in aircraft_list:
                prev_snapshots[id(aircraft)] = capture_state(aircraft)

            demo_traffic.update_demo_traffic(aircraft_list, dt)

            # Drop tracking state for any aircraft removed this tick.
            live_keys = {id(aircraft) for aircraft in aircraft_list}
            for stale_key in set(trails) - live_keys:
                del trails[stale_key]
            for stale_key in set(prev_snapshots) - live_keys:
                del prev_snapshots[stale_key]

            for aircraft in aircraft_list:
                _ensure_tracked(aircraft)
                # Trail is appended once per sim tick (here), never once per
                # render frame — sim-tick history, not a dense render cloud.
                trails[id(aircraft)].append((aircraft.x_nm, aircraft.y_nm))

        alpha = sim_clock.advance(real_dt, on_tick)

        render_items = []
        for aircraft in aircraft_list:
            curr_state = capture_state(aircraft)
            prev_state = prev_snapshots.get(id(aircraft), curr_state)
            render_state = interpolate(prev_state, curr_state, alpha)
            render_items.append((render_state, trails[id(aircraft)]))

        draw_frame(screen, background, render_items)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
