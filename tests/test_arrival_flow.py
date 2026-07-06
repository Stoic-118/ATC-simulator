"""Headless integration test for the autonomous demo arrival flow
(PERF-04): spawn airborne at the DET 2A STAR entry fix (FL170) ->
descent -> approach -> landed -> taxi-in -> removed. Guards its import of
the not-yet-existing atc_sim.sim.demo_traffic module so this file is
skipped until Phase 3's demo_traffic.py implementation plan lands.

Uses the shared `phase_recorder` fixture (tests/conftest.py) rather than
re-implementing tick-stepping.
"""

import pytest

pytest.importorskip("atc_sim.sim.demo_traffic")

from atc_sim.sim import demo_traffic
from atc_sim.sim.phase import Phase

# Generous tick budget: ~3000 simulated seconds (50 min) at TICK_DT=0.5s
# comfortably covers the ~43nm DET 2A STAR plus the simplified
# fly-direct-to-threshold approach leg (~36nm) and the TAXI_IN timer
# (03-RESEARCH.md Pattern C). This is a hard cap, not a wait.
N_TICKS = 6000
TICK_DT = 0.5


def test_arrival_spawns_airborne_at_det_fl170():
    aircraft = demo_traffic.spawn_arrival()

    assert aircraft.phase == Phase.DESCENT
    assert aircraft.altitude_ft == 17000  # DET fix FL170


def test_arrival_flow_visits_phases_in_order_and_is_removed(phase_recorder):
    active_traffic = []
    aircraft = demo_traffic.spawn_arrival()
    active_traffic.append(aircraft)

    def step(_aircraft, dt):
        demo_traffic.update_demo_traffic(active_traffic, dt)

    sequence = phase_recorder(aircraft, step, N_TICKS, tick_dt=TICK_DT)

    assert sequence == [
        Phase.DESCENT,
        Phase.APPROACH,
        Phase.LANDED,
        Phase.TAXI_IN,
    ]
    assert aircraft not in active_traffic
