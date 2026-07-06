"""Headless integration test for the autonomous demo departure flow
(PERF-03): spawn -> taxi-out -> departure roll -> climb -> enroute ->
removed once the OLNEY 2B SID's legs are exhausted. Guards its import of
the not-yet-existing atc_sim.sim.demo_traffic module so this file is
skipped until Phase 3's demo_traffic.py implementation plan lands.

Uses the shared `phase_recorder` fixture (tests/conftest.py) rather than
re-implementing tick-stepping.
"""

import pytest

pytest.importorskip("atc_sim.sim.demo_traffic")

from atc_sim.navdata.eggw import OLNEY_2B_SID
from atc_sim.sim import demo_traffic
from atc_sim.sim.phase import Phase

# Generous tick budget: ~2000 simulated seconds (33 min) at TICK_DT=0.5s is
# comfortably above the taxi-out timer + departure-roll acceleration +
# climb across the OLNEY 2B SID's ~43nm of legs (03-RESEARCH.md Pattern C
# timers + fleet terminal speeds). This is a hard cap, not a wait -- if the
# flow never completes, the sequence assertion below fails with a
# truncated/incomplete list rather than this test hanging.
N_TICKS = 4000
TICK_DT = 0.5


def test_departure_flow_visits_phases_in_order_and_is_removed(phase_recorder):
    active_traffic = []
    aircraft = demo_traffic.spawn_departure()
    active_traffic.append(aircraft)

    def step(_aircraft, dt):
        demo_traffic.update_demo_traffic(active_traffic, dt)

    sequence = phase_recorder(aircraft, step, N_TICKS, tick_dt=TICK_DT)

    assert sequence == [
        Phase.TAXI_OUT,
        Phase.DEPARTURE_ROLL,
        Phase.CLIMB,
        Phase.ENROUTE,
    ]
    assert aircraft.procedure_leg_index >= len(OLNEY_2B_SID.legs)
    assert aircraft not in active_traffic
