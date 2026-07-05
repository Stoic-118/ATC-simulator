"""Headless tests for the frozen ILS/Runway navdata models and the real
EGGW runway 25 data (NAV-01). No pygame import anywhere in this file or in
the modules under test.
"""

import pytest
from pydantic import ValidationError

from atc_sim.navdata.eggw import EGGW_RUNWAY
from atc_sim.navdata.models import ILS, Runway


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
