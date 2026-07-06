"""Explicit flight-phase state machine (PERF-02).

Exactly the 8 phases named in the roadmap's success criterion #4 -- no
more, no less. The `LOC_CAPTURED`/`GS_CAPTURED` ILS-capture sub-states
from ARCHITECTURE.md's original 11-state sketch are deliberately
excluded this phase (Phase 4 / PROC-03 scope), and removal-from-active
-traffic is a list-membership concern handled by the demo-traffic
orchestration layer, not a Phase value.

This module MUST NOT import pygame — it stays headlessly testable via
pytest with no display, enforced by tests/test_boundary.py.
"""

from enum import Enum, auto


class Phase(Enum):
    TAXI_OUT = auto()
    DEPARTURE_ROLL = auto()
    CLIMB = auto()
    ENROUTE = auto()
    DESCENT = auto()
    APPROACH = auto()
    LANDED = auto()
    TAXI_IN = auto()


# Mostly-linear chain. ENROUTE -> DESCENT and DESCENT -> APPROACH are defined
# for forward-compatibility (a future full-flight scenario) even though this
# phase's departure demo aircraft is removed from ENROUTE before ever
# reaching DESCENT, and this phase's arrival demo aircraft spawns directly
# into DESCENT rather than transitioning through CLIMB/ENROUTE first.
LEGAL_TRANSITIONS: dict[Phase, set[Phase]] = {
    Phase.TAXI_OUT: {Phase.DEPARTURE_ROLL},
    Phase.DEPARTURE_ROLL: {Phase.CLIMB},
    Phase.CLIMB: {Phase.ENROUTE},
    Phase.ENROUTE: {Phase.DESCENT},
    Phase.DESCENT: {Phase.APPROACH},
    Phase.APPROACH: {Phase.LANDED},
    Phase.LANDED: {Phase.TAXI_IN},
    Phase.TAXI_IN: set(),  # terminal; removal happens externally, see module docstring
}


def transition_to(current: Phase, new: Phase) -> Phase:
    if new not in LEGAL_TRANSITIONS[current]:
        raise ValueError(f"Illegal transition {current} -> {new}")
    return new
