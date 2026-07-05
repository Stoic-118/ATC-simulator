"""Hand-authored real EGGW runway + ILS data.

Identifier note (Pitfall C): EGGW's single runway was redesignated from
08/26 to 07/25 in May 2020, after its magnetic heading drifted past the
rounding threshold (the runway's true/physical position, threshold, and
ILS siting are completely unchanged — only the two-digit label changed).
This module uses "25", the current, real-world charted identifier — do not
be confused if an older (pre-2020) chart, forum post, or hobbyist database
still says "26"; it is describing this exact same runway. See
.planning/phases/02-navdata-coordinate-projection/02-RESEARCH.md
"Critical Finding" for the full sourcing.

This module MUST NOT import pygame — it stays headlessly testable via
pytest with no display, enforced by tests/test_boundary.py.
"""

from atc_sim.navdata.models import ILS, Runway

# RWY 25 localizer — course is calibrated to the extended runway centerline
# and closely matches the charted runway QFU below (254.40).
# course_deg_mag: 254.0 [VERIFIED: runway QFU, UK AIP eAIP]
# identifier="ILJ", frequency_mhz=109.15 [CITED: flightplandatabase.com,
#   low confidence — not independently confirmed against the primary AIP
#   AD 2.19 table this session; supplementary fields, not required by NAV-01]
# glideslope_deg: 3.0 — standard ILS glideslope angle
# decision_height_ft: 200 [ASSUMED: ICAO Annex 6 / near-universal standard
#   CAT I DH — no Luton-specific published DH located; see 02-RESEARCH.md
#   Open Questions Q2]
_EGGW_ILS = ILS(
    identifier="ILJ",
    frequency_mhz=109.15,
    course_deg_mag=254.0,
    glideslope_deg=3.0,
    category="CAT I",
    decision_height_ft=200,
)

# RWY 25 threshold, UK AIP eAIP EG-AD-2.EGGW, live fetch, 2024-03-21 AIRAC
# cycle [VERIFIED]. Charted DMS: 51°52'37.36"N, 000°21'16.15"W.
# Decimal conversion (do not re-derive ad hoc — see 02-RESEARCH.md "Don't
# Hand-Roll"): 51 + 52/60 + 37.36/3600 = 51.877044;
#              -(0 + 21/60 + 16.15/3600) = -0.354486
# heading_deg_mag: 254.40 (QFU) [VERIFIED: UK AIP eAIP EG-AD-2.EGGW]
EGGW_RUNWAY = Runway(
    identifier="25",
    threshold_lat=51.877044,
    threshold_lon=-0.354486,
    heading_deg_mag=254.4,
    ils=_EGGW_ILS,
)
