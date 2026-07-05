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

from atc_sim.navdata.models import (
    ILS,
    AltitudeRestriction,
    Fix,
    Procedure,
    ProcedureLeg,
    Runway,
    SpeedRestriction,
)

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

# --- OLNEY 2B SID (RWY 25) ------------------------------------------------
# [VERIFIED: UK AIP AD 2-EGGW-6-5, chart effective 25 Feb 2020, live PDF
# fetch]. Route: climb straight ahead to 500ft AAL, turn left to intercept
# BNN VOR radial 032; at BNN D7 (7nm DME) turn right onto HEN NDB inbound
# QDM 256; at BNN VOR radial 004 turn right onto BNN VOR radial 345 direct
# OLNEY.
#
# Simplification note (02-RESEARCH.md "Selected Procedures" / Simplification
# note): the chart's stepped DME climb (4000ft by BNN D6, 5000ft by D9,
# 6000ft by D15) is collapsed here to a single at-or-above 6000ft
# restriction on the final BNN -> OLNEY leg -- the real terminal value of
# that stepped profile, not an invented number.
#
# Pitfall B: HEN is a real, unrestricted intercept/turn point on this chart
# -- its altitude_restriction is deliberately left None, not fabricated.
_BNN = Fix(name="BNN", lat=51.726111, lon=-0.549722)  # 51°43'34"N, 000°32'59"W
_HEN = Fix(name="HEN", lat=51.759722, lon=-0.790278)  # 51°45'35"N, 000°47'25"W
_OLNEY_FIX = Fix(name="OLNEY", lat=52.127778, lon=-0.734167)  # 52°07'40"N, 000°44'03"W

OLNEY_2B_SID = Procedure(
    name="OLNEY 2B",
    kind="SID",
    runway="25",
    legs=[
        ProcedureLeg(fix=_BNN),
        ProcedureLeg(
            fix=_HEN,
            course_deg_mag=256.0,  # HEN NDB inbound QDM 256 [VERIFIED: chart]
            altitude_restriction=None,  # Pitfall B: no charted restriction at HEN
        ),
        ProcedureLeg(
            fix=_OLNEY_FIX,
            course_deg_mag=345.0,  # BNN VOR radial 345 direct OLNEY [VERIFIED: chart]
            altitude_restriction=AltitudeRestriction(kind="at_or_above", altitude_ft=6000),
        ),
    ],
)

# --- DET 2A STAR (RWY 25) --------------------------------------------------
# [VERIFIED: UK AIP AD 2-EGGW-7-6 "LOGAN 2A DET 2A" combined chart, AERO
# INFO DATE 02 DEC 2025, live PDF fetch -- the current, in-force chart].
# Route via ATS route N57: DET -> LOFFO -> ABBOT. Levels: FL170 at DET,
# FL080 at ABBOT.
_DET_FIX = Fix(name="DET", lat=51.304003, lon=0.597275)  # 51°18'14.41"N, 000°35'50.19"E
_LOFFO = Fix(name="LOFFO", lat=51.836667, lon=0.598992)  # 51°50'12.00"N, 000°35'56.37"E
_ABBOT = Fix(name="ABBOT", lat=52.016111, lon=0.599581)  # 52°00'58.00"N, 000°35'58.49"E

DET_2A_STAR = Procedure(
    name="DET 2A",
    kind="STAR",
    runway="25",
    legs=[
        ProcedureLeg(
            fix=_DET_FIX,
            altitude_restriction=AltitudeRestriction(kind="at", altitude_ft=17000),  # FL170
        ),
        ProcedureLeg(
            fix=_LOFFO,
            speed_restriction=SpeedRestriction(kind="max", speed_kt=250),
        ),
        ProcedureLeg(
            fix=_ABBOT,
            altitude_restriction=AltitudeRestriction(kind="at", altitude_ft=8000),  # FL080
            speed_restriction=SpeedRestriction(kind="max", speed_kt=220),
        ),
    ],
)
