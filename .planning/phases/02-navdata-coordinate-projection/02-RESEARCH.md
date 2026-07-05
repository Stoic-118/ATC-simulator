# Phase 2: Navdata & Coordinate Projection - Research

**Researched:** 2026-07-05
**Domain:** Real-world aviation navdata (UK AIP EGGW) + cosine-corrected geodesic projection (Python/geographiclib)
**Confidence:** MEDIUM-HIGH (runway/threshold/navaid coordinates and the current STAR are sourced directly from live UK AIP/NATS eAIP fetches this session — HIGH confidence; the chosen SID is sourced from a 2020 AIRAC chart that is structurally very likely still current but was not re-fetched at the very latest AIRAC cycle — MEDIUM-HIGH; the ILS frequency/identifier come from a lower-authority secondary source — MEDIUM-LOW, flagged)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01 (carried from Phase 1):** Named SID/STAR fixes render as a small marker plus the fix's 5-letter name in text next to it — matches real radar scopes/charts. Follows the existing Phase 1 dark-flat modern-EFIS palette for marker/text color rather than introducing a new visual language.
- **D-02:** The one SID and one STAR use real published EGGW runway-26 fix names and coordinates, hand-typed from public chart sources — not invented/simplified placeholders. Hand-authored (not a live AIRAC feed), consistent with the project's "no live navdata ingestion" constraint.
- **D-03:** Which specific SID and STAR to model is left to the Phase 2 researcher to pick during research — the user does not have a specific procedure name locked in. The researcher should choose one well-documented, representative real EGGW runway-26 SID and one real EGGW runway-26 STAR from public sources. **(This research selects OLNEY 2B as the SID and DET 2A as the STAR — see "Selected Procedures" below, with full sourcing and an explicit alternative noted.)**
- **D-04:** SID/STAR fixes are connected by a thin line in sequence (a visible procedure track), not just isolated markers. Line style stays within the existing thin-line, low-clutter EFIS aesthetic established in Phase 1's rings/sector lines.
- **D-05:** Altitude/speed restrictions at each fix are modeled as data (Pydantic fields) in this phase but are **NOT** rendered as visible text on the radar canvas yet (deferred to Phase 4 / RADAR-02). Restrictions existing as correct, tested data on the fix/leg models satisfies ROADMAP.md's success criterion #2 — no on-screen restriction text is required in this phase.

### Claude's Discretion

- Exact projection math implementation details (equirectangular vs. other cosine-corrected approach), the specific data structures for navdata storage/loading, and how the runway/procedure static elements integrate into the existing `build_static_background()` caching are left to research/planning. **(This research recommends a geographiclib-geodesic-inverse-based projection — see "Coordinate Projection" below — and extending `build_static_background()` directly.)**
- Magnetic variation is already decided at the project level as a single hardcoded constant for v1 — not re-litigated here. Re-confirm the exact EGGW magnetic variation value against current charts at implementation time. **(This research re-confirms it: recommend +1.2° E — see "Magnetic Variation" below.)**

### Deferred Ideas (OUT OF SCOPE)

- **On-canvas restriction text** (e.g. "5000A" next to a fix) — deferred to Phase 4 (RADAR-02/datablock display). Restrictions are still modeled as data in this phase; only the visual rendering is deferred.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| NAV-01 | Airport navdata models EGGW runway 26 only — threshold, heading, and ILS parameters (localizer course, 3.0° glideslope, CAT I decision height) | "Selected Runway & ILS Data" gives real, sourced threshold coordinates, magnetic heading, and ILS course/glideslope/DH values with confidence tags and a Pydantic `Runway`/`ILS` model design |
| NAV-02 | One SID and one STAR for runway 26 modeled with named fixes/waypoints and altitude/speed restrictions | "Selected Procedures" gives real fix names, real coordinates (converted DMS→decimal, shown with working), and real restriction values for OLNEY 2B (SID) and DET 2A (STAR), plus the `Procedure`/`ProcedureLeg`/`Fix` model design |
| NAV-03 | Navdata models distinguish heading/course/track/bearing as separate named fields and apply magnetic variation at exactly one defined boundary | "Heading/Course/Track/Bearing Field Design" gives concrete Pydantic field names and the exact function (`true_to_magnetic()`) where the single magnetic-variation constant is applied |
| RADAR-04 | Radar canvas uses a cosine-corrected lat/lon-to-pixel projection shared with the separation-check math | "Coordinate Projection" gives a geographiclib-based projection function usable unchanged by both `render/radar.py` and a future `sim/separation.py`, plus a worked scale/range selection that fits every selected real fix on the existing fixed 1280×800 canvas without clipping |

</phase_requirements>

## Summary

The single most important finding this research surfaced is **not** a library or pattern choice — it's a real-world fact that changes how "runway 26" should be sourced: **London Luton's runway was redesignated from 08/26 to 07/25 in May 2020** because the runway's magnetic heading drifted past the rounding threshold `[VERIFIED: NATS eAIP + WebSearch cross-check]`. The physical runway, its threshold, and every navaid/fix around it are unchanged — only the two-digit label changed. Today's UK AIP charts for the direction the project calls "runway 26" are filed under **"RWY 25"**. This research treats the project's "runway 26" as a fixed label (per already-locked REQUIREMENTS.md/ROADMAP.md/CONTEXT.md) attached to the **real, current data for RWY 25** — see "Critical Finding" below for the full reasoning and the recommendation to confirm this with the user before or during planning.

With that resolved, this research locates and sources a complete, real, currently-published data set: runway 25 threshold coordinates and magnetic heading `[VERIFIED: UK AIP eAIP, live fetch]`, the **OLNEY 2B** SID (RWY 25) with its BNN/HEN/OLNEY fix chain and altitude restrictions `[VERIFIED: UK AIP AD 2-EGGW-6-5 chart, live PDF fetch]`, the **DET 2A** STAR with its DET/LOFFO/ABBOT fix chain and altitude/speed restrictions `[VERIFIED: UK AIP AD 2-EGGW-7-6 chart, live PDF fetch, effective 2 Dec 2025 — this is the current, in-force chart]`, and ILS glideslope/course data `[CITED/ASSUMED — see confidence caveats]`. It also gives a concrete, working coordinate-projection design built directly on `geographiclib.Geodesic.WGS84.Inverse()` (already the project's locked geodesy library) that is naturally cosine-corrected because it uses true geodesic azimuth/distance rather than a raw degree-scaling approximation, and that can be called identically from `render/radar.py` today and from a future `sim/separation.py` — satisfying RADAR-04's "shared with separation math" requirement by construction, not by convention.

**Primary recommendation:** Model the runway as identifier `"26"` (per project convention) using real RWY-25 AIP data; use OLNEY 2B as the SID and DET 2A as the STAR; build the projection as a thin wrapper over `Geodesic.WGS84.Inverse()` returning `(dx_px, dy_px)` from a single shared origin (the runway threshold), reused unchanged by rendering and (later) separation math; apply magnetic variation (+1.2° E) at exactly one function boundary (`true_to_magnetic()`); and delete the Phase-1-only wrap-at-edge special case in `interpolation.py` now that real navdata paths replace it.

## Critical Finding: "Runway 26" No Longer Exists as a Charted Identifier

**What was found:** EGGW's single runway was renumbered from **08/26 to 07/25 in May 2020**, the first renumbering since 1960, because the runway's true/magnetic heading (~254° magnetic today) had drifted enough that it now rounds to "25" rather than "26" `[VERIFIED: WebSearch cross-check of UK aviation press + direct confirmation on the current OLNEY SID chart itself: "CHANGE (6/20): RWY 26 REDESIGNATED 25. OLNEY 1B REDESIGNATED OLNEY 2B."]`. Every current UK AIP chart, NOTAM, and third-party database (SkyVector, OpenNav, flightplandatabase) files this runway under 07/25, not 08/26.

**Why this matters for planning:** REQUIREMENTS.md (NAV-01/02), ROADMAP.md (Phase 2 goal/success criteria), and 02-CONTEXT.md (D-02, D-03) all say "runway 26" repeatedly and explicitly demand *real* data, "not invented/simplified placeholders." Taken literally, a currently-charted "runway 26" does not exist to source data from.

**Recommendation (this research's approach, used throughout the rest of this document):** The physical runway, threshold, extended centerline, ILS siting, and every navaid/fix around it have **not** changed — only the two-digit label changed, and that change is purely a function of secular magnetic drift crossing a rounding boundary. Therefore:
- Keep the project's internal identifier as `"26"` (zero disruption to already-locked planning docs).
- Source all coordinates, headings, and procedure data from the **current, real RWY 25 charts** (this is the same physical direction — landing/departing to the west — that "26" always meant).
- Document this explicitly in the `Runway` model / navdata module docstring so a future reader isn't confused when they cross-reference a current chart and see "25" instead of "26."

This is a **label-only** discrepancy, not a data-accuracy risk — the underlying real-world facts (threshold position, ILS course, fix locations) are identical either way. It is called out in "Assumptions Log" (A1) and "Open Questions" (Q1) for the planner to confirm with the user before final lock, but it does not block planning: the data below is correct regardless of which two-digit label is ultimately chosen.

## Architectural Responsibility Map

This project has no web/API/CDN tiers — its two tiers are the headless **Sim Core** (`atc_sim.sim.*` / a new `atc_sim.navdata.*`, no pygame) and the **Render** layer (`atc_sim.render.*`, pygame-only, read-only). Mapped accordingly:

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Navdata storage (Runway/Fix/Procedure/ILS Pydantic models) | Sim Core (`navdata/models.py`) | — | Read-only reference data, must stay pygame-free so it's usable by future separation math and testable headlessly |
| Coordinate projection (lat/lon → local xy/pixels) | Sim Core (`navdata/geo.py`) | Render (`render/radar.py`, consumer) | RADAR-04 requires the *same* function be usable by separation math later; it must not live in a pygame-importing module even though its only caller today is the renderer |
| Magnetic variation conversion (`true_to_magnetic`) | Sim Core (`navdata/geo.py`) | — | Pure math, no rendering concern; must be the single point of application per NAV-03 |
| Runway/ILS static symbol rendering (threshold dot, extended centerline) | Render (`render/radar.py`, extends `build_static_background()`) | — | Pixel drawing, reads navdata + projection output only |
| Fix marker + name text rendering | Render (`render/radar.py`) | — | Pixel/text drawing, reads navdata + projection output only |
| Procedure track line rendering | Render (`render/radar.py`) | — | Pixel drawing, reads an ordered list of already-projected points |
| Altitude/speed restriction data (per D-05, not rendered this phase) | Sim Core (`navdata/models.py`) | — | Data-only this phase; Render must not read/display it yet (Phase 4 owns that) |

## Selected Runway & ILS Data

**Runway:** Project identifier `"26"` (see Critical Finding above); real-world current identifier "25"; physical runway 07/25, single hard-surface runway, 2162m × 46m `[CITED: flightplandatabase.com aggregation, cross-checked against AIP length figures]`.

| Field | Value | Confidence / Source |
|-------|-------|----------------------|
| Threshold (DMS, as charted) | 51°52'37.36"N, 000°21'16.15"W | `[VERIFIED: UK AIP eAIP EG-AD-2.EGGW, live fetch, 2024-03-21 AIRAC cycle]` |
| Threshold (decimal, converted this session) | 51.877044°N, -0.354486°W | Converted from the DMS value above — show your work if re-deriving: `51 + 52/60 + 37.36/3600 = 51.877044`; `-(0 + 21/60 + 16.15/3600) = -0.354486` |
| Magnetic heading / QFU | 254.40° magnetic | `[VERIFIED: UK AIP eAIP EG-AD-2.EGGW, live fetch]` — printed as "Runway 25 at 254.40°" |
| True bearing | 254.37°–254.40° (sources agree to within 0.03°) | `[VERIFIED: UK AIP]` + `[CITED: flightplandatabase.com]` cross-check |
| Reciprocal (RWY 07 threshold, for sanity-checking runway length/orientation) | 51°52'19.25"N, 000°23'00.91"W → decimal 51.872014°N, -0.383586°W | `[VERIFIED: UK AIP eAIP]` |
| ILS glideslope angle | 3.0° | Already locked in REQUIREMENTS.md NAV-01 text; corroborated as the standard/near-universal ILS glideslope angle and by `[CITED: flightplandatabase.com]` |
| ILS localizer course | 254° magnetic (round the runway QFU above; localizer course is calibrated to the extended runway centerline and is expected to match/nearly match it) | `[VERIFIED: UK AIP runway QFU]` used as the authoritative value; flightplandatabase's independently-reported 253.68° is a close cross-check (Δ0.7°, within normal siting-vs-charted-heading tolerance) |
| ILS category | CAT I (project scope; EGGW's runway is CAT II/III-capable in reality but NAV-01 explicitly scopes this project to CAT I only) | Per REQUIREMENTS.md NAV-01 (locked); real-world CAT II/III capability `[CITED: WebSearch, general aviation-press coverage]` is out of this project's stated scope |
| CAT I decision height (DH) | 200 ft AAL | `[ASSUMED]` — this is the ICAO Annex 6 / near-universal standard CAT I DH; a Luton-specific published DH was not located this session (see Open Questions Q2) |
| ILS frequency | 109.15 MHz | `[CITED: flightplandatabase.com]` — MEDIUM-LOW confidence, third-party aggregator, not independently confirmed against the primary AIP AD 2.19 table this session (that section could not be retrieved — see Open Questions Q2) |
| ILS identifier | "ILJ" (reported for RWY 25) / "ILTN" (reported for RWY 07) | `[CITED: flightplandatabase.com]` — MEDIUM-LOW confidence, same caveat as frequency |
| Airport Reference Point (ARP), for context only — **not** recommended as the projection origin | ~51°52'29"N, 000°22'06"W | `[CITED: OpenNav/SkyVector/Great Circle Mapper, cross-checked across 3 independent secondary sources, consistent to a few arc-seconds]` — recommend using the runway threshold (HIGH confidence, primary source) as the projection origin instead of this MEDIUM-confidence ARP |

**Recommendation on frequency/identifier:** These two fields are not required by NAV-01 (which only asks for localizer course, glideslope, and DH) — include them as optional `ILS` model fields for realism/future use, but tag them `[CITED: flightplandatabase.com]` in code comments and treat as non-blocking. If the planner wants HIGH confidence on these two specific values, add a `checkpoint:human-verify` task to cross-check against the primary UK AIP AD 2.19 table (the eAIP page is very large and this session's automated fetch truncated before reaching that subsection — a human with a browser can reach it directly).

## Selected Procedures

### SID: OLNEY 2B (RWY 25 / project's "runway 26")

`[VERIFIED: UK AIP AD 2-EGGW-6-5, chart effective 25 Feb 2020, fetched and read directly this session]`. This chart is the one that documents the 08/26→07/25 redesignation itself ("CHANGE (6/20): RWY 26 REDESIGNATED 25. OLNEY 1B REDESIGNATED OLNEY 2B"), so it is unambiguously the correct current successor to whatever "OLNEY SID runway 26" chart existed pre-2020. VOR/NDB stations and named fixes are extremely stable data (unlike runway numbers, which are a magnetic-heading artifact) — this structure is very likely still current, though it was not re-fetched at the very latest AIRAC cycle this session (see Open Questions Q3).

**Route:** Climb straight ahead to 500ft AAL, turn left to intercept BNN VOR radial 032. At BNN D7 (7nm DME), turn right onto HEN NDB inbound QDM 256°. At BNN VOR radial 004, turn right onto BNN VOR radial 345 direct to OLNEY.

| Fix | Type | DMS (charted) | Decimal (converted this session) | Restriction |
|-----|------|----------------|-----------------------------------|-------------|
| BNN (Bovingdon) | VOR/DME, 113.75 MHz (Ch 84Y), elev 500ft | 51°43'34"N, 000°32'59"W | 51.726111°N, -0.549722°W | Turn/intercept point, no altitude restriction |
| HEN (Henton) | NDB, 433.5 kHz | 51°45'35"N, 000°47'25"W | 51.759722°N, -0.790278°W | Intercept point (QDM 256° inbound), no altitude restriction |
| OLNEY | Fix, defined as BNN R344.5/D25.1 | 52°07'40"N, 000°44'03"W | 52.127778°N, -0.734167°W | Cross at or above 6000ft (chart shows stepped climb: BNN D6 at/above 4000, D9 at 5000, D15 at 6000; simplified to a single "at or above 6000 by OLNEY" restriction on the final leg — see note below) |

**Simplification note (flag for planner):** The real chart encodes a *stepped* climb keyed to DME distance from BNN (4000ft by D6, 5000ft by D9, 6000ft by D15), not one restriction per named fix. Since D-05 already establishes restrictions as data-only (not rendered) and this project explicitly wants hand-authored, not full-AIRAC-fidelity navdata, this research recommends collapsing that stepped profile into a single restriction on the final `ProcedureLeg` (BNN → OLNEY): `altitude_restriction = AT_OR_ABOVE, 6000ft`. This is a defensible simplification of real data, not an invented one — the underlying 6000ft figure is exactly what the chart specifies as the terminal value of the stepped climb. If the planner wants literal per-DME-step fidelity, model BNN-D6/D9/D15 as three additional synthetic leg-restrictions instead of named fixes; this research's recommendation is the simpler of the two and satisfies NAV-02 as written.

Speed: Maximum 250 KIAS below FL100 (general note, applies to all Luton non-airways SIDs) `[VERIFIED: same chart]`.

### STAR: DET 2A (recommended over LOGAN 2A — see "Scale & Range Selection" below)

`[VERIFIED: UK AIP AD 2-EGGW-7-6, "LOGAN 2A DET 2A" combined chart, AERO INFO DATE 02 DEC 2025 — this is the currently in-force chart, fetched live this session from the 2026-04-16 AIRAC graphics set]`. This is the single most current, highest-confidence data point in this entire research file.

**Route (DET 2A, via ATS route N57):** DET → LOFFO → ABBOT. Levels: FL170 at DET, FL080 at ABBOT.

| Fix | Type | DMS (charted) | Decimal (converted this session) | Restriction |
|-----|------|----------------|-----------------------------------|-------------|
| DET (Detling) | VOR, 117.30 MHz (Ch 120X), elev 645ft | 51°18'14.41"N, 000°35'50.19"E | 51.304003°N, 0.597275°E | At FL170 |
| LOFFO | RNAV waypoint | 51°50'12.00"N, 000°35'56.37"E | 51.836667°N, 0.598992°E | Max 250 KIAS |
| ABBOT | RNAV waypoint / holding fix | 52°00'58.00"N, 000°35'58.49"E | 52.016111°N, 0.599581°E | At FL080; holding pattern, max 220 KIAS below FL140 / max 240 KIAS at FL150+; **"Do not proceed beyond ABBOT without ATC clearance"** |

**Alternative considered:** LOGAN 2A (LOGAN → CLN → ABBOT, via route L608) is the sibling STAR on the same chart, equally real and well-documented, but LOGAN itself is ~74nm from the runway threshold — see "Scale & Range Selection" below for why this makes it a poor fit for the project's fixed 1280×800 canvas. DET 2A's farthest fix (DET, ~50nm) fits comfortably; LOGAN 2A's farthest fix does not, without either shrinking the display so much that runway/ILS detail becomes illegible, or clipping LOGAN off the visible canvas (which would fail success criterion #2, "fixes appear on the radar at their correct real-world positions"). **Recommend DET 2A as the primary pick.**

Both STARs terminate at the ABBOT hold, from which real-world ATC vectors arrivals to whichever runway direction is active (07 or 25) — STARs in this TMA are not runway-specific beyond that point. This matches D-03's framing ("one well-documented, representative real EGGW runway-26 STAR") since the project only operates one runway direction; treat DET 2A as "the STAR that feeds this project's single active runway."

## Coordinate Projection

**Design:** Do not implement a raw degree-scaling equirectangular formula from scratch. Instead, build the projection directly on `geographiclib.Geodesic.WGS84.Inverse()` — already the project's locked geodesy library (see STACK.md). This is simpler to get right than hand-rolling the `cos(latitude)` correction, and it is *automatically* the shared function RADAR-04 requires: a future `sim/separation.py` calling the exact same `Inverse()`/`Direct()` primitives for actual separation math cannot visually disagree with the radar display, because both consume the same geodesic azimuth/distance, not two independently-approximated flat-earth models.

```python
# atc_sim/navdata/geo.py
"""Shared geodesic math for both the radar projection (render/radar.py) and
future separation-check math (sim/separation.py). MUST NOT import pygame.

Uses geographiclib.Geodesic.WGS84 for all bearing/distance calculations so
the display and the separation logic can never visually disagree (Pitfall 5).
"""

from geographiclib.geodesic import Geodesic

_GEOD = Geodesic.WGS84

# EGGW runway threshold — the project's projection origin. Real, current
# UK AIP RWY 25 data (see 02-RESEARCH.md "Critical Finding" for why this is
# sourced under "25" while the project calls it "26").
ORIGIN_LAT = 51.877044
ORIGIN_LON = -0.354486

# Nautical miles per pixel — see 02-RESEARCH.md "Scale & Range Selection".
# Chosen so RING_STEP_PX (80px, from render/window.py-adjacent radar.py)
# represents exactly 10nm per ring, and the farthest selected real fix
# (DET, ~50nm) fits inside the existing 1280x800 canvas without clipping.
PX_PER_NM = 8.0


def true_bearing_and_distance_nm(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> tuple[float, float]:
    """Returns (true_bearing_deg, distance_nm) from point1 to point2.

    This is the ONE function both the radar projection and (later)
    separation.py should call for geodesic distance/bearing — never
    reimplement haversine or a flat-earth approximation elsewhere.
    """
    result = _GEOD.Inverse(lat1, lon1, lat2, lon2)
    bearing_deg = result["azi1"] % 360.0
    distance_nm = result["s12"] / 1852.0  # metres -> nautical miles
    return bearing_deg, distance_nm


def project_to_local_xy_nm(lat: float, lon: float) -> tuple[float, float]:
    """Local tangent-plane offset from ORIGIN, in nautical miles.
    x is east-positive, y is north-positive (screen conversion happens
    in the render layer, which flips y and applies PX_PER_NM).

    Cosine correction is implicit: because this is true geodesic azimuth/
    distance (not raw degree scaling), a point due east and a point due
    north at the same real distance always produce the same magnitude
    here — satisfying "range rings render as true circles" by
    construction, not by manually multiplying longitude by cos(lat).
    """
    bearing_deg, distance_nm = true_bearing_and_distance_nm(
        ORIGIN_LAT, ORIGIN_LON, lat, lon
    )
    rad = __import__("math").radians(bearing_deg)
    x_nm = distance_nm * __import__("math").sin(rad)
    y_nm = distance_nm * __import__("math").cos(rad)
    return x_nm, y_nm
```

```python
# atc_sim/render/radar.py (extension — this module already imports pygame,
# so it does the final nm -> pixel + y-flip conversion; navdata/geo.py stays
# pygame-free per the sim/render boundary rule)

def world_to_screen(x_nm: float, y_nm: float, center: tuple[int, int], px_per_nm: float) -> tuple[int, int]:
    screen_x = center[0] + x_nm * px_per_nm
    screen_y = center[1] - y_nm * px_per_nm  # north = up = smaller screen y
    return int(screen_x), int(screen_y)
```

**Verification strategy this design enables (for RADAR-04 / Pitfall 5's "circles not ellipses" check):** project two synthetic points 10nm due north and 10nm due east of the origin; assert both produce a pixel distance from center within floating-point tolerance of `10 * PX_PER_NM`. Because both go through the same `Inverse()` call, this test is really checking "did I wire PX_PER_NM and the y-flip correctly," not "did I get a cosine formula right" — the correctness of the cosine relationship is delegated entirely to geographiclib, which is the point of not hand-rolling it (see "Don't Hand-Roll" below).

### Scale & Range Selection

Real-world distance of every selected fix from the runway-threshold origin (computed this session using the projection formula above, with the sourced coordinates):

| Fix | Distance from origin | Fits at 8.0 px/nm on 1280×800 canvas (±640px x, ±400px y from center)? |
|-----|----------------------|--------------------------------------------------------------------------|
| BNN | ~11.2nm | Yes — screen offset ≈ (-54, +71)px from center |
| HEN | ~17.2nm | Yes |
| OLNEY | ~20.4nm | Yes — screen offset ≈ (-109, -122)px |
| DET | ~49.6nm | Yes, comfortably — screen offset ≈ (+286, +274)px |
| LOFFO | ~35.9nm | Yes |
| ABBOT | ~36.9nm | Yes |
| LOGAN (not selected) | ~74nm | **No** — would require either shrinking scale below usable runway/ILS detail, or clipping off-canvas |
| CLN (not selected) | ~56nm | Marginal at this scale, borderline off the right edge |

**Recommendation:** `PX_PER_NM = 8.0` (i.e., each of Phase 1's existing 4 range rings at `RING_STEP_PX = 80` represents 10nm, out to 40nm). This is a clean, round mapping that requires no change to Phase 1's ring geometry constants — only a new "this ring = Nnm" meaning needs to be attached to them. All fixes in the selected OLNEY 2B / DET 2A procedures fit within the canvas at this scale without clipping. Do not pick LOGAN 2A given this canvas size and scale constraint (see "Selected Procedures" alternative note).

## Heading/Course/Track/Bearing Field Design

Per PITFALLS.md Pitfall 3/4, name these four concepts distinctly from day one, even though `heading == track` for all of v1 (no wind model). Phase 2 establishes the navdata-side courses and the shared conversion function; Phase 3 will apply the same naming convention to the `Aircraft` model.

```python
# atc_sim/navdata/models.py (excerpt)
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

RestrictionKind = Literal["at", "at_or_above", "at_or_below"]


class Fix(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str  # e.g. "OLNEY", "BNN", "DET" — real charted identifier
    lat: float = Field(ge=-90.0, le=90.0)
    lon: float = Field(ge=-180.0, le=180.0)


class AltitudeRestriction(BaseModel):
    model_config = ConfigDict(frozen=True)
    kind: RestrictionKind
    altitude_ft: int = Field(gt=0)


class SpeedRestriction(BaseModel):
    model_config = ConfigDict(frozen=True)
    kind: Literal["max", "min"]
    speed_kt: int = Field(gt=0)


class ProcedureLeg(BaseModel):
    model_config = ConfigDict(frozen=True)
    fix: Fix
    # course_deg_mag: the PUBLISHED/CHARTED course to fly toward this leg's
    # fix, as printed on the AIP chart — already magnetic, stored as-is,
    # NEVER passed through true_to_magnetic() (it did not come from
    # geographiclib; it came from a real chart already in magnetic).
    course_deg_mag: float | None = Field(default=None, ge=0.0, lt=360.0)
    altitude_restriction: AltitudeRestriction | None = None
    speed_restriction: SpeedRestriction | None = None


class Procedure(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str  # "OLNEY 2B" or "DET 2A"
    kind: Literal["SID", "STAR"]
    runway: str  # "26" — project convention; see Critical Finding
    legs: list[ProcedureLeg]


class ILS(BaseModel):
    model_config = ConfigDict(frozen=True)
    identifier: str | None = None       # [CITED, low confidence] "ILJ"
    frequency_mhz: float | None = None  # [CITED, low confidence] 109.15
    course_deg_mag: float = Field(ge=0.0, lt=360.0)   # 254.0 — see sourcing above
    glideslope_deg: float = Field(gt=0.0, lt=10.0)    # 3.0
    category: Literal["CAT I"] = "CAT I"
    decision_height_ft: int = Field(gt=0)             # 200 — [ASSUMED], see Q2


class Runway(BaseModel):
    model_config = ConfigDict(frozen=True)
    identifier: str  # "26" — project convention
    threshold_lat: float = Field(ge=-90.0, le=90.0)
    threshold_lon: float = Field(ge=-180.0, le=180.0)
    heading_deg_mag: float = Field(ge=0.0, lt=360.0)  # 254.4 — QFU
    ils: ILS
```

**The single magnetic-variation boundary (NAV-03):**

```python
# atc_sim/navdata/geo.py (continued)

# EGGW magnetic variation, positive = East. See 02-RESEARCH.md "Magnetic
# Variation" for full sourcing. This is the ONLY constant used to convert
# between true and magnetic anywhere in the codebase.
MAGNETIC_VARIATION_DEG = 1.2


def true_to_magnetic(true_deg: float, variation_deg: float = MAGNETIC_VARIATION_DEG) -> float:
    """The ONE place a geographiclib-computed TRUE bearing becomes a
    magnetic value for comparison against/display alongside charted
    (already-magnetic) courses. Mnemonic: variation east, magnetic least
    (subtract); variation west, magnetic best (add) — implemented here as
    subtraction since EGGW's variation is East (positive)."""
    return (true_deg - variation_deg) % 360.0


def magnetic_to_true(mag_deg: float, variation_deg: float = MAGNETIC_VARIATION_DEG) -> float:
    return (mag_deg + variation_deg) % 360.0
```

**Field-naming convention for Phase 3's `Aircraft` model (establish now, apply later):**

| Field | Meaning | Convention | Where it comes from |
|-------|---------|------------|----------------------|
| `heading_deg` | Aircraft nose orientation | Magnetic | Controller-assigned or procedure-derived target |
| `track_deg` | Aircraft's actual path over the ground | Magnetic | `== heading_deg` for all of v1 (no wind model) but named distinctly per Pitfall 3 |
| `course_deg_mag` | Published/intended direction of a procedure leg or the ILS localizer | Magnetic, stored as-charted | Navdata (`ProcedureLeg.course_deg_mag`, `ILS.course_deg_mag`) — never derived from geodesic math |
| `bearing_to_fix_deg` | Computed, per-tick angle from aircraft to a target fix (e.g., "direct to" guidance) | Computed TRUE via `true_bearing_and_distance_nm()`, then converted via `true_to_magnetic()` before being compared to or displayed alongside a charted course | The only per-tick quantity that crosses the true→magnetic boundary |

Navdata charted values (`course_deg_mag`, `heading_deg_mag` on `Runway`, `ILS.course_deg_mag`) are stored directly as sourced from the AIP — they are magnetic by definition on the chart and must never be run through `magnetic_to_true()`/`true_to_magnetic()` a second time. Only geographiclib's raw output crosses that boundary, and only inside `true_to_magnetic()`.

## Magnetic Variation

Three independent sourcings this session, all pointing to the same trend (magnetic variation over southeast England moving from westerly to easterly through the mid-2010s to now):

| Source | Value | Confidence |
|--------|-------|------------|
| UK AIP eAIP EG-AD-2.EGGW, AD 2.2, live fetch (2026-03-19 AIRAC) | **1.23°E (2027), annual change +0.17°E** | `[VERIFIED: primary source, live fetch]` — HIGH |
| UK AIP eAIP EG-AD-2.EGGW, live fetch (2024-03-21 AIRAC, an earlier cycle) | 0.41°E (2022), annual change +0.20°E | `[VERIFIED: primary source, live fetch]` — HIGH, but older cycle |
| DET 2A / LOGAN 2A STAR chart (effective 2 Dec 2025) | VAR 1.2°E - 2027, annual rate +0.17°E | `[VERIFIED: primary source, live PDF fetch]` — matches the AD 2.2 value almost exactly |
| OLNEY 2B SID chart (effective 25 Feb 2020) | VAR 0.3°W - 2019, annual rate +0.15°E (west-side sub-area) | `[VERIFIED: primary source, live PDF fetch]` — older, and a different local sub-area than the runway itself |
| magnetic-declination.com (independent IGRF-based geomagnetic model for "Luton") | +0.85° (undated "current") | `[CITED: WebSearch]` — MEDIUM, independent cross-check, same order of magnitude |

**Recommendation: `MAGNETIC_VARIATION_DEG = 1.2` (positive = East).** This is the AIP's own most-current published value for the aerodrome itself (AD 2.2, corroborated independently by the STAR chart's regional variation note), consistent with the project's existing documented decision (STATE.md) to use a single hardcoded constant for v1. Document in code that this is a deliberate simplification (real variation is time-varying and location-varying) and that the value should be re-checked if the project's live time horizon (in-sim "today") ever needs to track real calendar time precisely — not a concern for v1's scripted-scenario scope.

## Standard Stack

### Core (new to this phase)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| geographiclib | 2.1 | WGS84 geodesic inverse/direct problems — bearing, distance, and (per this research) the basis of the cosine-corrected projection | `[VERIFIED: pip index versions geographiclib` run this session against the live PyPI registry — confirms 2.1 is current]`. Already the project's locked-in geodesy choice from Phase 1 research (STACK.md, CLAUDE.md) — pure Python, zero native deps, avoids the documented pyproj/PyInstaller packaging pitfalls this project must avoid given its later packaging phase. |

**Installation:**
```bash
pip install "geographiclib>=2.1,<3.0"
```
Add to `pyproject.toml` `[project.dependencies]` alongside the existing `pygame-ce`/`pydantic` pins.

### Carried over unchanged (no re-verification needed this phase)

| Library | Version | Purpose |
|---------|---------|---------|
| pydantic | 2.13.4 (installed, confirmed via `pip show` this session) | Navdata models (`Runway`, `Fix`, `Procedure`, `ILS`) — read-only, `frozen=True` |
| pygame-ce | 2.5.7 (installed, confirmed this session) | Rendering only — navdata/geo modules must never import it |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| geodesic-inverse-based projection (this research's recommendation) | Raw equirectangular formula (`x = Δlon * cos(lat0) * k`, `y = Δlat * k`) | Slightly cheaper per-call (no full geodesic solve), and is what PITFALLS.md's Pitfall 5 literally describes — a perfectly valid alternative at this project's small-area scale (differences from the geodesic-exact version are sub-metre over a 50nm TMA). Recommended here as the *simpler-to-explain fallback* if the planner prefers not to route every static navdata point through a full `Inverse()` call; functionally interchangeable at this scale. |

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|--------------|---------|-------------|
| geographiclib | PyPI | Long-standing (versions back to 1.14; latest 2.1 released 21 Aug 2025) | 16.7M/month `[CITED: WebSearch, PyPI stats aggregator]` — automated `gsd-tools package-legitimacy check` reported `unknown-downloads` because it could not reach the live download-stats API in this sandbox, not because downloads are actually low | https://geographiclib.sourceforge.io/Python/ | SUS (automated, see note) | **Approved with note** — the automated SUS verdict is driven entirely by a sandbox network limitation (`unknown-downloads`), not a real legitimacy signal. Cross-checked this session via `pip index versions geographiclib` (confirms real, long version history on the live PyPI registry) and via WebSearch (confirms 16.7M/month downloads, MIT license, single well-known maintainer, official SourceForge project — this is also the project's own already-locked geodesy choice from Phase 1 STACK.md/CLAUDE.md). Per protocol, still flag: **planner should add a lightweight `checkpoint:human-verify` before the `pip install` step**, purely to close out the automated SUS flag, not because there is genuine doubt about this package. |

**Packages removed due to `[SLOP]` verdict:** none.
**Packages flagged as suspicious `[SUS]`:** geographiclib (see note above — false-positive-driven, approved with a lightweight verification checkpoint).

## Architecture Patterns

### System Architecture Diagram

```
                         ┌─────────────────────────────────┐
                         │   navdata/eggw.py (hand-authored) │
                         │   real, sourced constants:        │
                         │   Runway("26"), ILS, OLNEY 2B SID, │
                         │   DET 2A STAR                      │
                         └────────────────┬───────────────────┘
                                          │ loaded once at startup
                                          ▼
                         ┌─────────────────────────────────┐
                         │   navdata/models.py (Pydantic)    │
                         │   Runway, Fix, ILS, Procedure,    │
                         │   ProcedureLeg — frozen, read-only │
                         └────────────────┬───────────────────┘
                                          │ read by
              ┌───────────────────────────┼───────────────────────────┐
              ▼                                                       ▼
┌───────────────────────────────┐                     ┌───────────────────────────────┐
│ navdata/geo.py (Sim Core,      │                     │ (FUTURE, Phase 5+)             │
│ NO pygame import)               │                     │ sim/separation.py               │
│ - true_bearing_and_distance_nm │◄────────────────────┤ calls the SAME functions for   │
│ - project_to_local_xy_nm        │   same functions,    │ pairwise conflict distance     │
│ - true_to_magnetic /            │   never diverges      │                                 │
│   magnetic_to_true              │                     │                                 │
└────────────────┬────────────────┘                     └───────────────────────────────┘
                 │ (x_nm, y_nm) offsets from runway threshold origin
                 ▼
┌───────────────────────────────────────────────────────────────────────┐
│ render/radar.py (pygame, reads navdata + geo output, never mutates)    │
│  build_static_background() extended to also draw:                      │
│    - runway threshold dot + extended centerline (from Runway data)     │
│    - SID/STAR fix markers + 5-letter names (from Procedure.legs)       │
│    - thin procedure track line connecting each leg's fix in sequence   │
│  world_to_screen(x_nm, y_nm) does the final nm -> pixel + y-flip step  │
└───────────────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure

```
src/atc_sim/
├── navdata/                 # NEW this phase — no pygame import allowed here
│   ├── __init__.py
│   ├── models.py            # Fix, AltitudeRestriction, SpeedRestriction,
│   │                         # ProcedureLeg, Procedure, ILS, Runway (Pydantic, frozen)
│   ├── geo.py                # geographiclib wrappers: true_bearing_and_distance_nm,
│   │                         # project_to_local_xy_nm, true_to_magnetic, magnetic_to_true
│   └── eggw.py                # Hand-authored real EGGW data: Runway("26"), ILS,
│                              # OLNEY 2B SID, DET 2A STAR — the sourced constants
│                              # from this RESEARCH.md, as typed Python literals
├── sim/                      # unchanged from Phase 1 (aircraft.py, clock.py, interpolation.py)
│   └── interpolation.py       # MUST be edited this phase: remove the Phase-1-only
│                              # wrap-at-edge special case (see Common Pitfalls below)
└── render/
    └── radar.py                # extend build_static_background() to draw runway/
                                # fixes/procedure line; add world_to_screen() helper
```

### Pattern 1: Extend the existing static-background cache, don't add a second one

**What:** `build_static_background()` in `render/radar.py` already renders range rings and sector lines once at startup into a cached `pygame.Surface`. Runway threshold/centerline, fix markers+names, and the procedure track line are all static (world-fixed, never move per-tick) — exactly the same category of content already cached there.

**When to use:** This phase. Add the new drawing calls inside `build_static_background()` (or a helper it calls), reusing the same `screen.blit(background, (0,0))` pattern `draw_frame()` already uses. Do not introduce a second cached surface or redraw these elements per-frame.

**Example:**
```python
# render/radar.py (extension)
def build_static_background(size, runway, procedures) -> pygame.Surface:
    surface = pygame.Surface(size)
    surface.fill(BG_COLOR)
    # ... existing rings/sector lines ...
    _draw_runway(surface, runway)          # NEW
    for proc in procedures:                 # NEW — OLNEY 2B, DET 2A
        _draw_procedure(surface, proc)
    return surface
```

### Pattern 2: `RenderState`-style structural typing for navdata, if render code needs typed access

**What:** Phase 1's 01-04 deviation introduced a `typing.Protocol` (`RenderState`) so `render/radar.py` never has to `import atc_sim.sim.*` directly, keeping `app.py` the sole dual-importer. If any new render function needs typed access to a `Fix`/`Runway`/`Procedure` object, prefer passing already-constructed plain tuples/floats (as `world_to_screen()` above does) over importing `atc_sim.navdata.models` types directly into `render/radar.py`, OR — since `navdata/` (unlike `sim/`) is not scanned by `tests/test_boundary.py` (only `src/atc_sim/sim/` is) — a direct import of `atc_sim.navdata.models` from `render/radar.py` is architecturally fine. Prefer it over duck-typed Protocols here, since `navdata` types are read-only reference data, not the mutable sim-state boundary the `RenderState` Protocol exists to protect. **Recommendation: import `atc_sim.navdata.models` types directly into `render/radar.py`.**

### Anti-Patterns to Avoid

- **Hand-rolling haversine/flat-earth trig instead of using geographiclib:** the project already made this call in Phase 1 research; Phase 2 is where it must actually get used for the first time. Reaching for a manual `math.sin`/`math.cos` haversine implementation "because it's simple" reintroduces exactly the divergent-math risk (Pitfall 5) geographiclib exists to prevent.
- **Treating DMS→decimal coordinate conversion as a one-off scratch calculation:** every coordinate in this document was hand-converted from a real chart's DMS string. Do this once, in the data file (`navdata/eggw.py`), with the original DMS string preserved as a comment next to the decimal value (as shown in the tables above) — never re-derive it ad hoc elsewhere, and never silently "fix" a coordinate without re-checking the source chart.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|--------------|-----|
| Great-circle bearing/distance between two lat/lon points | A manual haversine or flat-earth trig function | `geographiclib.Geodesic.WGS84.Inverse()` (wrapped in `navdata/geo.py`) | Already the project's locked choice; guarantees the display and future separation math can never silently diverge (Pitfall 5) |
| Cosine-corrected lat/lon-to-pixel projection | A hand-derived `x = Δlon * cos(lat0)` formula reimplemented per-caller | The `project_to_local_xy_nm()` wrapper above, called once, reused everywhere (rings' meaning, fixes, runway, future aircraft position) | Centralizes the one place cosine correction matters; a geodesic-inverse-based implementation gets this right by construction, not by a formula someone has to remember to apply consistently |
| DMS (degrees-minutes-seconds) to decimal-degree coordinate conversion | Ad hoc regex/string parsing scattered through data files | A single small, unit-tested helper (or, since this is a one-time hand-authoring task for ~11 fixed points, careful hand-conversion with the DMS source preserved as a comment, as done in this document) | Coordinate transcription errors are the single easiest way to silently corrupt "real" navdata that D-02 specifically requires to be accurate — cheap to get right once, expensive to debug later as "the fix looks slightly off on the radar" |

**Key insight:** every hand-rolled alternative in this table produces code that *looks* correct (compiles, runs, draws something plausible-looking on a radar canvas) while being subtly wrong in exactly the way PITFALLS.md Pitfall 5 describes — and the bug is nearly invisible until someone overlays the result on a real chart, which is precisely why this research went to the trouble of using and cross-checking real chart data rather than inventing plausible-looking numbers.

## Common Pitfalls

### Pitfall A: Leftover Phase-1 wrap-at-edge special case in `interpolation.py`

**What goes wrong:** `sim/interpolation.py`'s `interpolate()` function contains an explicit Phase-1-only special case (its own docstring says so): if the position jump between two snapshots exceeds half the canvas dimension, it assumes a wrap-at-edge event and snaps straight to `curr` instead of lerping. Real navdata paths (SID climb-out, STAR descent) never wrap at a canvas edge, but they *can* legitimately produce large jumps at low tick rates during, e.g., a big turn onto a new leg. If this special case is left in place unmodified, it will silently mask/mishandle any such legitimate large per-tick movement once Phase 2's real-world-scale coordinates are in play (a fast jet at a wide tick interval on a ~50nm-wide radar can easily move a large fraction of the canvas in one tick).

**Why it happens:** The code and its own docstring flag it as Phase-1-only, but nothing forces its removal — it will keep "working" (in the sense of not crashing) indefinitely, just silently doing the wrong thing.

**How to avoid:** Explicitly remove this special case as part of this phase's plan (even though it lives in `sim/`, not `navdata/`) — it directly regards this phase's stated replacement of "Phase 1's throwaway straight-line-and-wrap test aircraft path with real EGGW geography" (per 02-CONTEXT.md's own Phase Boundary section). Add this as an explicit task in the plan, not an incidental side-effect.

**Warning signs:** An aircraft's interpolated position occasionally "teleports" (snaps to `curr` with no visible motion) during a real turn or fast leg, especially at the project's low 1-4Hz tick rate.

### Pitfall B: Real chart restrictions are DME-distance-keyed, not fix-keyed — don't over-simplify silently

**What goes wrong:** As shown in "Selected Procedures," OLNEY 2B's climb restrictions are charted against DME distance from BNN (D6/D9/D15), not against the named fixes (BNN, HEN, OLNEY) themselves. A naive reading of NAV-02 ("named fixes ... with altitude/speed restrictions") could tempt someone to invent a restriction number for HEN (which the chart does not actually restrict) just to have "a restriction per fix," which would violate D-02's "not invented" requirement.

**How to avoid:** Attach the real restriction (6000ft at-or-above) to the correct real leg (BNN→OLNEY) as this research recommends, and leave `HEN`'s leg restriction as `None` — an explicitly absent restriction is real data; a fabricated non-zero restriction is not.

**Warning signs:** Every single fix in a modeled procedure has a non-null restriction — real SIDs/STARs almost always have unrestricted intermediate turn/intercept points.

### Pitfall C: Confusing the project's "runway 26" label with a literal current-chart lookup

**What goes wrong:** A future contributor (or the planner/verifier) searching UK AIP/SkyVector/NOTAMs for "EGGW runway 26" mid-implementation will find nothing under that label and may conclude the navdata is wrong or outdated, when in fact it's correctly sourced from the current "25" charts under the project's own retained "26" convention (see Critical Finding).

**How to avoid:** Document this explicitly and prominently in `navdata/eggw.py`'s module docstring (not just in this research file), so anyone reading the code — not just the plan — understands why "25" appears in every source citation while the code says `"26"`.

## Code Examples

### DMS to decimal conversion (worked example, matches the tables above)

```python
# Source: manual conversion of UK AIP-published DMS strings this session.
# Example: RWY 25 threshold "51°52'37.36\"N, 000°21'16.15\"W"
def dms_to_decimal(deg: int, minutes: int, seconds: float, hemisphere: str) -> float:
    value = deg + minutes / 60.0 + seconds / 3600.0
    return -value if hemisphere in ("S", "W") else value

threshold_lat = dms_to_decimal(51, 52, 37.36, "N")   # 51.877044
threshold_lon = dms_to_decimal(0, 21, 16.15, "W")    # -0.354486
```

### Range-ring circle test (verifies RADAR-04 / Pitfall 5 without needing a screenshot)

```python
# tests/test_projection.py (new this phase)
import math
from atc_sim.navdata.geo import project_to_local_xy_nm

def test_projection_is_circular_not_elliptical():
    """North and east points at the same real distance must produce the
    same pixel-space magnitude — this is what 'range rings are circles,
    not ellipses' actually verifies, without needing a screenshot."""
    # 10nm due north of the origin, and 10nm due east, computed via the
    # geodesic direct problem for the test's own ground truth would be
    # more rigorous; a simplified small-angle check against known deltas
    # is sufficient at v1 scale — see geographiclib's Direct() for the
    # rigorous version if the planner wants a tighter tolerance.
    ...
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|-------------------|---------------|--------|
| EGGW runway identifier "08/26" | EGGW runway identifier "07/25" | May 2020 (per UK AIP AMDT, confirmed on the OLNEY chart itself) | Any pre-2020 chart, forum post, or hobbyist database referencing "runway 26" is describing the same physical runway current sources call "25" — see Critical Finding |
| OLNEY 1B SID | OLNEY 2B SID | Same May 2020 AIRAC cycle, renamed alongside the runway redesignation | Same route/fixes, new procedure name |

**Deprecated/outdated:** Any chart, dataset, or third-party tool still labeling this runway "08/26" (several were found this session — e.g. the 2013 AIP charts, some hobbyist sites) reflects pre-2020 numbering; treat "07/25" as current ground truth.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|-----------------|
| A1 | The project's "runway 26" should be modeled using real current RWY 25 data (label-only discrepancy, not a data discrepancy) | Critical Finding | Low — if the user instead wants the project's identifier changed to "25" to match reality exactly, this is a pure rename with no data changes required; does not block implementation either way |
| A2 | ILS localizer course (254° magnetic) is close enough to the charted runway QFU (254.40°) to use directly | Selected Runway & ILS Data | Low — real ILS localizer courses are calibrated to the extended runway centerline and are expected to match/nearly match the runway heading; a 0.7° cross-check discrepancy against a third-party source is within normal tolerance |
| A3 | CAT I decision height = 200ft AAL | Selected Runway & ILS Data | Low — this is the ICAO/near-universal standard CAT I DH; a Luton-specific published value was not located this session (Q2) |
| A4 | ILS frequency 109.15 MHz / identifiers "ILJ"/"ILTN" | Selected Runway & ILS Data | Low — these fields are not required by NAV-01 and are supplementary; sourced from a third-party aggregator (flightplandatabase.com), not the primary AIP table (Q2) |
| A5 | OLNEY 2B SID structure (fixes/restrictions) is still current, though the specific chart fetched is from the Feb 2020 AIRAC cycle rather than the very latest | Selected Procedures | Low — VOR/NDB/fix locations are extremely stable data; even if a newer AIRAC amendment exists, the named fixes and their real-world coordinates are very unlikely to have changed (Q3) |
| A6 | Collapsing OLNEY 2B's DME-stepped climb restriction (4000/D6, 5000/D9, 6000/D15) into a single "at or above 6000 by OLNEY" leg restriction is an acceptable simplification of real data | Selected Procedures (Simplification note) | Low — this is explicitly flagged for the planner; if literal per-DME fidelity is wanted instead, the alternative (three synthetic leg-restrictions) is given |

## Open Questions

1. **Should the project's runway identifier be "26" (current convention, real data underneath) or updated to "25" (matches current reality exactly)?**
   - What we know: the physical runway/threshold/ILS/fixes are unchanged; only the two-digit label changed in 2020.
   - What's unclear: whether the user, on hearing this, would prefer to update REQUIREMENTS.md/ROADMAP.md/CONTEXT.md's "runway 26" language to "25" for strict accuracy, versus keeping "26" as an intentional project convention.
   - Recommendation: proceed with "26" as the code-level identifier (this research's approach) unless the user says otherwise during plan review — it is lower-disruption and the underlying data is correct either way.

2. **Exact ILS frequency/identifier and CAT I decision height for EGGW RWY 25.**
   - What we know: glideslope (3.0°, already locked in NAV-01) and localizer course (~254° magnetic, HIGH confidence via runway QFU) are solid. Frequency/identifier come from a single third-party aggregator; DH is an industry-standard assumption, not airport-specific-sourced.
   - What's unclear: the primary UK AIP AD 2.19 "Radio navigation and landing aids" table, which would give an authoritative answer, could not be retrieved this session (the eAIP page for EGGW is large enough that automated fetching truncated before reaching that subsection).
   - Recommendation: proceed with the values given (they are non-blocking per NAV-01's actual wording), and add a `checkpoint:human-verify` task if the planner wants a human to browse `https://www.aurora.nats.co.uk/htmlAIP/Publications/<latest-AIRAC>/html/eAIP/EG-AD-2.EGGW-en-GB.html` directly and confirm AD 2.19 before implementation.

3. **Is OLNEY 2B still the current SID, or has a newer AIRAC amendment superseded it?**
   - What we know: the fetched chart (effective 25 Feb 2020) is the one that documents the 08/26→07/25 redesignation and the OLNEY 1B→2B rename; VOR/NDB/fix coordinates are extremely stable data that essentially never change between AIRAC cycles.
   - What's unclear: whether a later AIRAC cycle renamed the SID again (e.g., to "OLNEY 3B") or altered a restriction value.
   - Recommendation: proceed with OLNEY 2B's data as sourced; low risk given fix-location stability, but flag as a `checkpoint:human-verify` opportunity if the planner wants to re-fetch the very latest AIRAC cycle's SID chart before locking the hand-authored data file.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python | Language runtime | ✓ | 3.14.4 (confirmed this session) | — |
| pip | Package install | ✓ | 26.1.2 (confirmed this session) | — |
| pydantic | Navdata models | ✓ (already installed) | 2.13.4 (confirmed this session) | — |
| pygame-ce | Rendering | ✓ (already installed) | 2.5.7 (confirmed this session) | — |
| geographiclib | Projection/geodesic math (NEW this phase) | ✗ (not yet installed — confirmed via `pip show` this session) | 2.1 available on PyPI (confirmed via `pip index versions` this session) | None needed — trivial `pip install`, no native/data-file dependencies to worry about (unlike the rejected pyproj alternative) |
| Network access (for the one-time AIP data lookup) | Sourcing real navdata (this research phase only, not runtime) | ✓ (used this session to fetch live UK AIP pages/PDFs) | — | Not a runtime dependency — the app itself has no network dependency (hand-authored navdata is committed as Python literals) |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none — `geographiclib` just needs a standard `pip install` before implementation begins.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.x (already configured, confirmed via `pyproject.toml` `[tool.pytest.ini_options]`) |
| Config file | `pyproject.toml` (`testpaths = ["tests"]`) |
| Quick run command | `pytest tests/test_navdata.py tests/test_projection.py -x` |
| Full suite command | `pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|---------------------|--------------|
| NAV-01 | `Runway`/`ILS` models load with correct real threshold/heading/glideslope/DH values | unit | `pytest tests/test_navdata.py::test_runway_26_matches_sourced_data -x` | ❌ Wave 0 |
| NAV-02 | OLNEY 2B SID and DET 2A STAR load with correct real fix names, coordinates, and restrictions | unit | `pytest tests/test_navdata.py::test_olney_2b_sid_data -x` and `::test_det_2a_star_data` | ❌ Wave 0 |
| NAV-03 | `true_to_magnetic`/`magnetic_to_true` round-trip correctly; charted (already-magnetic) course fields are never double-converted | unit | `pytest tests/test_navdata.py::test_magnetic_variation_boundary -x` | ❌ Wave 0 |
| RADAR-04 | Projected points at equal real-world distance in different bearings produce equal-magnitude pixel offsets (circle, not ellipse) | unit | `pytest tests/test_projection.py::test_projection_is_circular_not_elliptical -x` | ❌ Wave 0 |
| RADAR-04 | Every selected SID/STAR fix projects to an on-canvas pixel position (no clipping) at the recommended `PX_PER_NM` | unit | `pytest tests/test_projection.py::test_selected_fixes_fit_on_canvas -x` | ❌ Wave 0 |
| RADAR-01/RADAR-04 (visual regression guard) | Extended `build_static_background()` still builds and `draw_frame()` still runs headlessly with runway/fix/procedure-line drawing added | smoke | `pytest tests/test_render_smoke.py -x` (existing file, extend its assertions) | ✅ (extend existing) |

### Sampling Rate

- **Per task commit:** `pytest tests/test_navdata.py tests/test_projection.py -x`
- **Per wave merge:** `pytest`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_navdata.py` — covers NAV-01, NAV-02, NAV-03 (new file)
- [ ] `tests/test_projection.py` — covers RADAR-04 (new file)
- [ ] Extend `tests/test_render_smoke.py` — pass a real `Runway`/`Procedure` fixture through `build_static_background()` so the headless smoke test actually exercises the new drawing code, not just the Phase 1 rings/sector-lines path
- [ ] Framework install: `pip install "geographiclib>=2.1,<3.0"` — add to `pyproject.toml` and the dev venv before any navdata/geo.py test can import it

## Security Domain

### Applicable ASVS Categories

This phase adds zero user input, zero authentication, zero network I/O, and zero cryptography — it is entirely hardcoded reference data plus pure math and rendering. Most ASVS categories do not apply.

| ASVS Category | Applies | Standard Control |
|----------------|---------|--------------------|
| V2 Authentication | No | N/A — no auth surface anywhere in this project |
| V3 Session Management | No | N/A |
| V4 Access Control | No | N/A |
| V5 Input Validation | Minimal-yes | Pydantic `Field(ge=..., le=...)` constraints on lat/lon/heading/frequency ranges (already shown in the model designs above) — this guards against hand-transcription typos in the hardcoded navdata (e.g., a lat/lon swap, an out-of-range heading), not against adversarial input, since there is none |
| V6 Cryptography | No | N/A — no secrets, no network, no storage requiring encryption |

### Known Threat Patterns for this stack

Given the complete absence of user/network input in this phase, classic STRIDE categories (Spoofing, Tampering by an external actor, Information Disclosure, Elevation of Privilege) do not meaningfully apply to hardcoded, locally-loaded reference data in an offline desktop app. The one genuinely relevant quality/correctness risk — silent data corruption from hand-transcribing real coordinates incorrectly — is already covered above as a Pitfall (Don't Hand-Roll: DMS conversion) and an Assumptions Log risk, rather than a security threat in the ASVS/STRIDE sense.

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|------------------------|
| Hand-transcribed real-world coordinate/frequency data silently corrupted (typo in a hardcoded lat/lon) | Not a security threat (data-quality/correctness issue) | Pydantic range validation (catches gross errors like an out-of-range lat/lon) + a unit test per named fix asserting its exact sourced decimal value, so any future accidental edit is caught by CI, not by eyeballing a radar screenshot |

## Sources

### Primary (HIGH confidence)
- UK AIP eAIP EG-AD-2.EGGW-en-GB, live fetch, 2026-03-19 AIRAC cycle — runway threshold coordinates, magnetic heading, magnetic variation (1.23°E/2027)
- UK AIP eAIP EG-AD-2.EGGW-en-GB, live fetch, 2024-03-21 AIRAC cycle — cross-check runway threshold coordinates, older magnetic variation value
- UK AIP AD 2-EGGW-6-5 (OLNEY 2B SID, RWY 25), effective 25 Feb 2020, live PDF fetch and read — https://www.aurora.nats.co.uk/htmlAIP/Publications/2020-08-13-AIRAC/graphics/177501.pdf
- UK AIP AD 2-EGGW-7-6 (LOGAN 2A / DET 2A STAR), effective 2 Dec 2025, live PDF fetch and read — https://www.aurora.nats.co.uk/htmlAIP/Publications/2026-04-16-AIRAC/graphics/479483.pdf
- UK AIP AD 2-EGGW-6-7 (Non-Airway Departures RWY 26, historical/pre-2020) and AD 2-EGGW-6-5 (Detling SID RWY 26/08, historical/pre-2020) — used only to corroborate fix continuity (BNN, HEN, BPK, DET) across the 2020 redesignation, not as current-data sources

### Secondary (MEDIUM confidence)
- flightplandatabase.com airport page for EGGW — ILS frequency/identifier/course figures (cross-checked against, but lower-authority than, the primary AIP runway heading)
- OpenNav.com, SkyVector.com, Great Circle Mapper — Airport Reference Point coordinates (cross-checked across 3 independent sources, consistent to a few arc-seconds; not used as the projection origin in favor of the HIGH-confidence AIP threshold coordinate)
- magnetic-declination.com — independent IGRF-based cross-check of magnetic variation trend
- pip index versions geographiclib (live PyPI registry query, this session) — confirms current version 2.1
- WebSearch cross-checks on the 08/26→07/25 runway redesignation (UK aviation press, Infinite Flight community discussion, Wikipedia) — independently corroborate the redesignation confirmed directly on the OLNEY 2B chart itself

### Tertiary (LOW confidence)
- Historical/pre-2020 opennav.com chart PDFs and Jeppesen-sourced hobbyist chart mirrors — used only for cross-referencing fix-name continuity, not as a current-data source

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — geographiclib version verified live against PyPI this session; already the project's locked choice
- Real navdata (runway/SID): HIGH-MEDIUM — runway and STAR data verified live against current, in-force UK AIP charts this session; SID data verified against a 2020 AIRAC chart that is structurally very likely still current but not re-verified at the latest cycle
- ILS frequency/identifier/DH: LOW-MEDIUM — sourced from a third-party aggregator and an industry-standard assumption respectively; flagged for optional human verification, non-blocking per NAV-01's actual wording
- Architecture/projection design: HIGH — directly extends already-locked Phase 1 patterns and the project's already-decided geodesy library; the geodesic-inverse-based projection approach is a straightforward, low-risk application of `geographiclib`
- Pitfalls: HIGH — Pitfall A (interpolation wrap-case) and Pitfall C (runway label) are concrete, codebase-specific findings from this session's direct code/data reading, not generic domain pattern-matching

**Research date:** 2026-07-05
**Valid until:** Real-world navdata (runway/navaid/fix data) is stable for years — no urgency to re-verify before implementation. The specific ILS frequency/identifier/DH values flagged LOW-MEDIUM confidence should be re-checked if the planner wants HIGH confidence there specifically. Library version (geographiclib 2.1) should be re-confirmed if implementation is delayed more than ~90 days.
