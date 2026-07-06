"""Authoritative Aircraft state model.

Phase 3 (03-04 Task 1): Aircraft moved from the Phase-1 placeholder
pixel-space model (x/y pixels, heading_deg, speed_px_per_sec) into the
shared local-nm tangent-plane coordinate system already used by every
navdata projection (navdata/geo.py's project_to_local_xy_nm) and by
procedure tracking, plus full altitude/phase/procedure/performance state.
`sim_step`'s real per-phase kinematics dispatch is added in Task 3 (it
needs sim/procedure.py's compute_target()/advance_leg_if_reached(), added
in Task 2) -- this module only evolves the Aircraft model itself.

This module MUST NOT import pygame — it stays headlessly testable via
pytest with no display, enforced by tests/test_boundary.py.
"""

from pydantic import BaseModel, ConfigDict, Field

from atc_sim.navdata.models import Procedure
from atc_sim.sim.performance import PerformanceProfile
from atc_sim.sim.phase import Phase


class Aircraft(BaseModel):
    model_config = ConfigDict(validate_assignment=True)  # v2 style; catches bad mutations

    x_nm: float
    y_nm: float
    altitude_ft: float = Field(ge=0.0)
    speed_kt: float = Field(gt=0.0)
    heading_deg: float = Field(ge=0.0, lt=360.0)  # Phase 3: MAGNETIC, matches every navdata heading field
    phase: Phase
    phase_elapsed_sec: float = 0.0  # single generic timer, reused across every timed phase; reset on transition
    procedure: Procedure
    procedure_leg_index: int = Field(default=0, ge=0)
    performance: PerformanceProfile

    # Phase 3 (D-02): spawn_default() removed -- the demo harness in plan
    # 03-05 owns spawn construction (round-robin fleet types, departure vs.
    # arrival flight kind). A stale pixel-based classmethod referencing
    # removed x/y/speed_px_per_sec fields would be dead code here.
    # NOTE: src/atc_sim/app.py still calls Aircraft.spawn_default() and
    # reads aircraft.x/aircraft.y -- that call site is rewired in plan
    # 03-06 alongside the render layer's nm->pixel projection; it is
    # intentionally left unmigrated until then (03-04-PLAN.md scope).


def sim_step(aircraft: Aircraft, dt: float) -> None:
    """Placeholder pending Task 3's full per-phase kinematics dispatch,
    which needs sim/procedure.py's compute_target()/advance_leg_if_reached()
    (added in Task 2). Task 1 only evolves the Aircraft model itself."""
    raise NotImplementedError("sim_step's per-phase dispatch lands in 03-04 Task 3")
