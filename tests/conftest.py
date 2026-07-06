"""Shared headless test fixtures for Phase 3 (aircraft performance,
flight-phase FSM, procedure following).

This module exists so tests/test_departure_flow.py and
tests/test_arrival_flow.py do not each re-implement their own tick-stepping
loop -- both consume the `phase_recorder` fixture below instead.

Deliberately imports NOTHING from atc_sim.sim.* -- the aircraft object and
step function are supplied by the caller (dependency injection), so this
file has zero import dependency on code that does not exist yet and never
triggers a pytest collection error, even before Phase 3's sim/ modules
(performance.py, phase.py, procedure.py, demo_traffic.py) exist.

Does NOT import pygame.
"""

from collections.abc import Callable
from typing import Any

import pytest


def _record_phases(
    aircraft: Any,
    step_fn: Callable[[Any, float], None],
    n_ticks: int,
    tick_dt: float = 0.5,
) -> list[Any]:
    """Step `aircraft` via `step_fn(aircraft, tick_dt)` exactly `n_ticks`
    times, recording `aircraft.phase` after every tick. Returns the ordered
    list of observed phases with consecutive duplicates collapsed -- e.g. an
    aircraft that stays in CLIMB for 20 ticks contributes a single CLIMB
    entry to the returned sequence."""
    sequence: list[Any] = []
    for _ in range(n_ticks):
        step_fn(aircraft, tick_dt)
        current_phase = aircraft.phase
        if not sequence or sequence[-1] != current_phase:
            sequence.append(current_phase)
    return sequence


@pytest.fixture
def phase_recorder() -> Callable[..., list[Any]]:
    """Returns the record_phases(aircraft, step_fn, n_ticks, tick_dt=0.5)
    helper -- see _record_phases for behavior."""
    return _record_phases
