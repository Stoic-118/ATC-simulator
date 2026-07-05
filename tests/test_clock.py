"""Headless tests for the fixed-timestep accumulator sim clock.

Covers CORE-01 (frame-rate-independent motion) and CORE-02 (capped
catch-up / spiral-of-death prevention). No pygame import anywhere in
this file or in the module under test.
"""

from atc_sim.sim.clock import SimClock, TICK_DT, MAX_TICKS_PER_FRAME


def test_tick_count_independent_of_call_frequency():
    """Same total simulated wall time, split across different frame
    rates (30fps vs 120fps), must drain the same total tick count."""
    total_time = 5.0

    def run(fps: float) -> int:
        dt = 1.0 / fps
        clock = SimClock()
        ticks = []
        elapsed = 0.0
        while elapsed < total_time:
            clock.advance(dt, lambda tick_dt: ticks.append(tick_dt))
            elapsed += dt
        return len(ticks)

    ticks_30fps = run(30.0)
    ticks_120fps = run(120.0)

    assert ticks_30fps == ticks_120fps
    # Sanity: total sim time drained should match floor(total_time / TICK_DT)
    assert ticks_30fps == int(total_time / TICK_DT)


def test_stall_caps_ticks_per_frame():
    """A single large real_dt must drain at most MAX_TICKS_PER_FRAME
    ticks, invoke on_tick at most that many times, return a float,
    and not hang."""
    clock = SimClock()
    ticks = []

    alpha = clock.advance(3.0, lambda tick_dt: ticks.append(tick_dt))

    assert len(ticks) <= MAX_TICKS_PER_FRAME
    assert len(ticks) == MAX_TICKS_PER_FRAME
    assert isinstance(alpha, float)


def test_backlog_beyond_cap_is_dropped():
    """After a capped stall, the accumulator backlog is dropped (not
    retained to burst later) and dropped_tick_seconds is recorded."""
    clock = SimClock()
    ticks = []

    clock.advance(3.0, lambda tick_dt: ticks.append(tick_dt))

    assert clock.dropped_tick_seconds > 0.0

    # No retained backlog: a follow-up advance(0.0) drains zero ticks.
    further_ticks = []
    clock.advance(0.0, lambda tick_dt: further_ticks.append(tick_dt))
    assert len(further_ticks) == 0


def test_advance_returns_alpha_in_range():
    """advance() return value must always be in [0.0, 1.0)."""
    clock = SimClock()

    for real_dt in (0.0, 0.1, 0.25, 0.5, 1.0, 3.0):
        alpha = clock.advance(real_dt, lambda tick_dt: None)
        assert 0.0 <= alpha < 1.0


def test_on_tick_receives_tick_dt():
    """on_tick is invoked with tick_dt (0.5 at 2Hz) as its argument."""
    clock = SimClock()
    received = []

    clock.advance(TICK_DT, lambda tick_dt: received.append(tick_dt))

    assert received == [TICK_DT]
