"""Headless tests for the flight-phase FSM (PERF-02): the 8-member Phase
enum and its legal-transitions table. Guards its import of the
not-yet-existing atc_sim.sim.phase module so this file is skipped until
Phase 3's phase.py implementation plan lands.
"""

import pytest

pytest.importorskip("atc_sim.sim.phase")

from atc_sim.sim.phase import LEGAL_TRANSITIONS, Phase, transition_to

EXPECTED_MEMBER_NAMES = {
    "TAXI_OUT",
    "DEPARTURE_ROLL",
    "CLIMB",
    "ENROUTE",
    "DESCENT",
    "APPROACH",
    "LANDED",
    "TAXI_IN",
}


def test_phase_has_exactly_eight_members():
    member_names = {member.name for member in Phase}
    assert member_names == EXPECTED_MEMBER_NAMES
    assert len(Phase) == 8


def test_no_ils_capture_or_removal_sub_states():
    """PERF-02 deliberately excludes Phase 4's ILS capture sub-states and
    any 'removed' terminal state -- removal-from-active-traffic is a list
    membership concern, not a Phase value (03-RESEARCH.md Pitfall
    'Removal-from-active-traffic treated as a phase-FSM transition')."""
    member_names = {member.name for member in Phase}
    for forbidden in ("LOC_CAPTURED", "GS_CAPTURED", "REMOVED"):
        assert forbidden not in member_names


def test_legal_transitions_covers_every_phase():
    assert set(LEGAL_TRANSITIONS.keys()) == set(Phase)


def test_transition_to_walks_full_linear_chain():
    """The full mostly-linear chain a full-flight aircraft would walk, even
    though this phase's own demo aircraft only ever traverse a subset of it
    (departures stop at ENROUTE; arrivals start at DESCENT)."""
    linear_chain = [
        Phase.TAXI_OUT,
        Phase.DEPARTURE_ROLL,
        Phase.CLIMB,
        Phase.ENROUTE,
        Phase.DESCENT,
        Phase.APPROACH,
        Phase.LANDED,
        Phase.TAXI_IN,
    ]

    current = linear_chain[0]
    for next_phase in linear_chain[1:]:
        current = transition_to(current, next_phase)
        assert current == next_phase


def test_transition_to_rejects_illegal_skip():
    with pytest.raises(ValueError):
        transition_to(Phase.TAXI_OUT, Phase.CLIMB)
