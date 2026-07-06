"""Headless tests for the per-aircraft-type PerformanceProfile model and
FLEET data (PERF-01). Guards its import of the not-yet-existing
atc_sim.sim.performance module so this file is skipped until Phase 3's
performance.py implementation plan lands.
"""

import pytest

pytest.importorskip("atc_sim.sim.performance")

from pydantic import ValidationError

from atc_sim.sim.performance import FLEET, PerformanceProfile, turn_rate_deg_per_sec


def test_fleet_has_exactly_four_profiles():
    assert len(FLEET) == 4


def test_fleet_profiles_are_not_all_identical():
    """PERF-01: the fleet must have genuinely different climb/descent/
    terminal-speed/bank characteristics across types -- not four names
    sharing identical numbers. (Individual pairs may legitimately share a
    value in a simplified model -- e.g. two jets sharing a max_bank_deg --
    but no single field may collapse to one value across the whole fleet.)
    """
    climb_rates = {profile.climb_rate_fpm for profile in FLEET.values()}
    descent_rates = {profile.descent_rate_fpm for profile in FLEET.values()}
    terminal_speeds = {profile.terminal_speed_kt for profile in FLEET.values()}
    max_banks = {profile.max_bank_deg for profile in FLEET.values()}

    assert len(climb_rates) > 1
    assert len(descent_rates) > 1
    assert len(terminal_speeds) > 1
    assert len(max_banks) > 1


def test_performance_profile_rejects_non_positive_climb_rate():
    with pytest.raises(ValidationError):
        PerformanceProfile(
            name="Test Type",
            category="test",
            climb_rate_fpm=0.0,
            descent_rate_fpm=1000.0,
            terminal_speed_kt=200.0,
            approach_speed_kt=120.0,
            max_bank_deg=25.0,
            max_speed_change_kt_per_sec=1.5,
        )


def test_performance_profile_is_frozen():
    profile = next(iter(FLEET.values()))
    with pytest.raises(ValidationError):
        profile.climb_rate_fpm = 9999.0


def test_turn_rate_coupled_to_speed():
    """Turn rate is derived from bank angle + CURRENT groundspeed, not an
    independent per-type constant -- a faster aircraft turns slower at the
    same bank angle (03-RESEARCH.md Pitfall 7: coupling, not independent
    knobs)."""
    fast_turn_rate = turn_rate_deg_per_sec(bank_deg=25.0, speed_kt=250.0)
    slow_turn_rate = turn_rate_deg_per_sec(bank_deg=25.0, speed_kt=120.0)

    assert fast_turn_rate != pytest.approx(slow_turn_rate)
    assert slow_turn_rate > fast_turn_rate  # slower groundspeed -> tighter turn rate at same bank
