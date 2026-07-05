"""Headless tests for the frozen ILS/Runway navdata models and the real
EGGW runway 25 data (NAV-01), plus the OLNEY 2B SID / DET 2A STAR
procedure models and data (NAV-02/NAV-03). No pygame import anywhere in
this file or in the modules under test.
"""

import pytest
from pydantic import ValidationError

from atc_sim.navdata.eggw import DET_2A_STAR, EGGW_RUNWAY, OLNEY_2B_SID
from atc_sim.navdata.geo import magnetic_to_true, true_to_magnetic
from atc_sim.navdata.models import (
    AltitudeRestriction,
    Fix,
    ILS,
    Procedure,
    ProcedureLeg,
    Runway,
)


def test_runway_25_matches_sourced_data():
    assert EGGW_RUNWAY.identifier == "25"
    assert EGGW_RUNWAY.threshold_lat == pytest.approx(51.877044)
    assert EGGW_RUNWAY.threshold_lon == pytest.approx(-0.354486)
    assert EGGW_RUNWAY.heading_deg_mag == pytest.approx(254.4)
    assert EGGW_RUNWAY.ils.glideslope_deg == 3.0
    assert EGGW_RUNWAY.ils.course_deg_mag == pytest.approx(254.0)
    assert EGGW_RUNWAY.ils.category == "CAT I"
    assert EGGW_RUNWAY.ils.decision_height_ft == 200


def test_runway_model_rejects_bad_fields():
    valid_ils = ILS(course_deg_mag=254.0, glideslope_deg=3.0, decision_height_ft=200)

    with pytest.raises(ValidationError):
        Runway(
            identifier="25",
            threshold_lat=51.877044,
            threshold_lon=-0.354486,
            heading_deg_mag=400.0,
            ils=valid_ils,
        )

    with pytest.raises(ValidationError):
        ILS(course_deg_mag=254.0, glideslope_deg=0.0, decision_height_ft=200)


def test_runway_model_is_frozen():
    with pytest.raises(ValidationError):
        EGGW_RUNWAY.identifier = "07"


def test_olney_2b_sid_data():
    assert OLNEY_2B_SID.name == "OLNEY 2B"
    assert OLNEY_2B_SID.kind == "SID"
    assert OLNEY_2B_SID.runway == "25"

    fix_names = [leg.fix.name for leg in OLNEY_2B_SID.legs]
    assert fix_names == ["BNN", "HEN", "OLNEY"]

    bnn_leg, hen_leg, olney_leg = OLNEY_2B_SID.legs
    assert bnn_leg.fix.lat == pytest.approx(51.726111)
    assert bnn_leg.fix.lon == pytest.approx(-0.549722)
    assert olney_leg.fix.lat == pytest.approx(52.127778)
    assert olney_leg.fix.lon == pytest.approx(-0.734167)

    # BNN -> OLNEY final leg: collapsed stepped-DME climb, terminal value
    # only (02-RESEARCH.md "Simplification note") -- real data, not invented.
    assert olney_leg.altitude_restriction is not None
    assert olney_leg.altitude_restriction.kind == "at_or_above"
    assert olney_leg.altitude_restriction.altitude_ft == 6000

    # Pitfall B: HEN has NO charted altitude restriction -- must be None,
    # not a fabricated value just to have "a restriction per fix".
    assert hen_leg.altitude_restriction is None


def test_det_2a_star_data():
    assert DET_2A_STAR.name == "DET 2A"
    assert DET_2A_STAR.kind == "STAR"
    assert DET_2A_STAR.runway == "25"

    fix_names = [leg.fix.name for leg in DET_2A_STAR.legs]
    assert fix_names == ["DET", "LOFFO", "ABBOT"]

    det_leg, _loffo_leg, abbot_leg = DET_2A_STAR.legs
    assert det_leg.fix.lat == pytest.approx(51.304003)
    assert det_leg.fix.lon == pytest.approx(0.597275)
    assert abbot_leg.fix.lat == pytest.approx(52.016111)
    assert abbot_leg.fix.lon == pytest.approx(0.599581)

    assert det_leg.altitude_restriction is not None
    assert det_leg.altitude_restriction.kind == "at"
    assert det_leg.altitude_restriction.altitude_ft == 17000  # FL170

    assert abbot_leg.altitude_restriction is not None
    assert abbot_leg.altitude_restriction.altitude_ft == 8000  # FL080
    assert abbot_leg.speed_restriction is not None
    assert abbot_leg.speed_restriction.kind == "max"
    assert abbot_leg.speed_restriction.speed_kt == 220


def test_procedure_models_reject_bad_fields():
    with pytest.raises(ValidationError):
        Fix(name="BAD", lat=91.0, lon=0.0)

    with pytest.raises(ValidationError):
        AltitudeRestriction(kind="at", altitude_ft=-100)

    with pytest.raises(ValidationError):
        OLNEY_2B_SID.name = "RENAMED"


def test_charted_course_not_double_converted():
    """NAV-03 guard: a ProcedureLeg's course_deg_mag is the exact charted
    magnetic value from the chart, stored as-is -- never re-derived by
    running it through magnetic_to_true()/true_to_magnetic() (those
    functions exist for geographiclib's TRUE output, not for charted values
    that are already magnetic)."""
    hen_leg = OLNEY_2B_SID.legs[1]
    assert hen_leg.fix.name == "HEN"
    assert hen_leg.course_deg_mag == pytest.approx(256.0)

    # If someone incorrectly ran the charted value through the true<->
    # magnetic boundary a second time, it would no longer equal the
    # charted value (since MAGNETIC_VARIATION_DEG != 0).
    assert hen_leg.course_deg_mag != pytest.approx(magnetic_to_true(256.0))
    assert hen_leg.course_deg_mag != pytest.approx(true_to_magnetic(256.0))
