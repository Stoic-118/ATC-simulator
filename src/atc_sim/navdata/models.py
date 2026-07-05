"""Frozen Pydantic v2 models for real-world runway/ILS navdata.

Read-only reference data — models are constructed once at startup
(navdata/eggw.py) and never mutated. Render code reads these fields but
must never assign to them (frozen=True enforces this).

This module MUST NOT import pygame — it stays headlessly testable via
pytest with no display, enforced by tests/test_boundary.py.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ILS(BaseModel):
    model_config = ConfigDict(frozen=True)

    identifier: str | None = None
    frequency_mhz: float | None = None
    course_deg_mag: float = Field(ge=0.0, lt=360.0)
    glideslope_deg: float = Field(gt=0.0, lt=10.0)
    category: Literal["CAT I"] = "CAT I"
    decision_height_ft: int = Field(gt=0)


class Runway(BaseModel):
    model_config = ConfigDict(frozen=True)

    identifier: str
    threshold_lat: float = Field(ge=-90.0, le=90.0)
    threshold_lon: float = Field(ge=-180.0, le=180.0)
    heading_deg_mag: float = Field(ge=0.0, lt=360.0)
    ils: ILS


RestrictionKind = Literal["at", "at_or_above", "at_or_below"]


class Fix(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str  # real charted identifier, e.g. "BNN", "OLNEY", "DET"
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
    # course_deg_mag: the PUBLISHED/CHARTED course to this leg's fix, as
    # printed on the AIP chart -- already magnetic, stored as-is, NEVER
    # passed through true_to_magnetic()/magnetic_to_true() (NAV-03: it did
    # not come from geographiclib; it came from a real chart already in
    # magnetic).
    course_deg_mag: float | None = Field(default=None, ge=0.0, lt=360.0)
    altitude_restriction: AltitudeRestriction | None = None
    speed_restriction: SpeedRestriction | None = None


class Procedure(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str  # "OLNEY 2B" or "DET 2A"
    kind: Literal["SID", "STAR"]
    runway: str  # "25" -- see navdata/eggw.py Pitfall C note
    legs: list[ProcedureLeg]
