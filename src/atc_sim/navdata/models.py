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
