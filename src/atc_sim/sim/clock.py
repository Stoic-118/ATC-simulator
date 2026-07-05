"""Fixed-timestep accumulator sim clock.

Decouples the sim tick rate from the render loop's frame rate
(CORE-01: frame-rate-independent motion) and caps catch-up work when
a frame stalls, degrading gracefully into bounded slow-motion rather
than freezing or spiraling (CORE-02).

This module MUST NOT import pygame — it stays headlessly testable via
pytest with no display, enforced by tests/test_boundary.py.
"""

from collections.abc import Callable

SIM_HZ = 2.0
TICK_DT = 1.0 / SIM_HZ          # 0.5 simulated seconds per tick
# NOTE: RESEARCH.md's canonical example pairs MAX_FRAME_TIME=0.25 with a much
# smaller tick_dt (the classic Gaffer On Games ratio, ~15x a 60fps frame).
# At this project's deliberately low SIM_HZ=2.0 (TICK_DT=0.5), a 0.25s clamp
# is *smaller* than a single tick, which makes MAX_TICKS_PER_FRAME
# mathematically unreachable in one advance() call and dropped_tick_seconds
# permanently stuck at 0 — directly contradicting this plan's own required
# CORE-02 behavior (a single 3.0s stall must actually hit the per-frame tick
# cap and record dropped backlog). MAX_FRAME_TIME is rescaled here to stay
# comfortably above MAX_TICKS_PER_FRAME * TICK_DT (2.5s) so the tick-per-frame
# cap is the operative bound for realistic multi-second stalls, while still
# acting as an outer backstop against pathological real_dt values (e.g. a
# suspended process resuming after minutes).
MAX_FRAME_TIME = 5.0            # clamp wall-clock dt fed into the accumulator
MAX_TICKS_PER_FRAME = 5         # hard cap on catch-up ticks drained in one frame


class SimClock:
    def __init__(self, tick_dt: float = TICK_DT) -> None:
        self.tick_dt = tick_dt
        self._accumulator = 0.0
        self.sim_time = 0.0
        self.dropped_tick_seconds = 0.0   # visibility counter, log/expose during dev

    def advance(self, real_dt: float, on_tick: Callable[[float], None]) -> float:
        """Returns alpha in [0, 1): how far between the last two ticks we are,
        for the caller to interpolate render state."""
        frame_time = min(real_dt, MAX_FRAME_TIME)
        self._accumulator += frame_time

        ticks_run = 0
        while self._accumulator >= self.tick_dt and ticks_run < MAX_TICKS_PER_FRAME:
            self.sim_time += self.tick_dt
            on_tick(self.tick_dt)
            self._accumulator -= self.tick_dt
            ticks_run += 1

        if ticks_run == MAX_TICKS_PER_FRAME and self._accumulator >= self.tick_dt:
            # Backlog exceeds the cap this frame — deliberately drop it rather than
            # spiral; sim will simply run slow relative to wall clock until it recovers.
            self.dropped_tick_seconds += self._accumulator
            self._accumulator = 0.0

        return self._accumulator / self.tick_dt
