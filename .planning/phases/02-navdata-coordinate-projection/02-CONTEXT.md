# Phase 2: Navdata & Coordinate Projection - Context

**Gathered:** 2026-07-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace Phase 1's throwaway straight-line-and-wrap test aircraft path with real EGGW runway-25 geography: a real runway threshold/extended centerline, one real published SID, one real published STAR, all rendered through a cosine-corrected lat/lon-to-pixel projection that will be shared with the future separation-check math. Heading/course/track/bearing become distinct named fields with magnetic variation applied at exactly one defined point. No performance modeling or flight-phase FSM (Phase 3), no procedure-following logic that actually flies the SID/STAR (Phase 3/4), no instruction handling (Phase 4). Requirements covered: NAV-01, NAV-02, NAV-03, RADAR-04.

**Runway identifier note:** EGGW's runway was redesignated from 08/26 to 07/25 in a May 2020 magnetic-drift realignment — same physical runway/threshold/ILS, relabeled identifier. This phase (and the project going forward) uses "25," matching current real-world charts. All docs (PROJECT.md, ROADMAP.md, REQUIREMENTS.md, CLAUDE.md) were updated accordingly during this discussion.

</domain>

<decisions>
## Implementation Decisions

### Waypoint/Fix Visual Style
- **D-01:** Named SID/STAR fixes render as a small marker plus the fix's 5-letter name in text next to it — matches real radar scopes/charts and makes it easy to visually confirm each fix is in the correct position. Follows the existing Phase 1 dark-flat modern-EFIS palette (D-01 from Phase 1 CONTEXT.md) for marker/text color rather than introducing a new visual language.

### Navdata Fidelity
- **D-02:** The one SID and one STAR use real published EGGW runway-25 fix names and coordinates, hand-typed from public chart sources — not invented/simplified placeholders. This is still hand-authored (not a live AIRAC feed), consistent with the project's existing "no live navdata ingestion" constraint (see PROJECT.md Out of Scope), but extends the project's real-EGGW commitment down to procedure-level detail.
- **D-03:** Which specific SID and STAR to model is left to the Phase 2 researcher to pick during research — the user does not have a specific procedure name locked in. The researcher should choose one well-documented, representative real EGGW runway-25 SID and one real EGGW runway-25 STAR from public sources.

### Procedure Path Rendering
- **D-04:** SID/STAR fixes are connected by a thin line in sequence (a visible procedure track), not just isolated markers. Gives Phase 3's procedure-following logic a visual anchor and makes the departure/arrival path readable at a glance. Line style should stay within the existing thin-line, low-clutter EFIS aesthetic established in Phase 1's rings/sector lines.

### Restriction Display Timing
- **D-05:** Altitude/speed restrictions at each fix (e.g. "cross BPK at or below 5000ft") are modeled as data (Pydantic fields on the fix/waypoint model) in this phase, but are **NOT** rendered as visible text on the radar canvas yet. Rendering restriction info as on-canvas text is intentionally deferred to Phase 4, which owns datablock-style instruction/info display (RADAR-02). **Important interpretation note for planner/verifier:** ROADMAP.md's Phase 2 success criterion #2 ("...each with its modeled altitude/speed restrictions") is satisfied by the restrictions existing as correct, tested data on the fix models — it does NOT require on-screen restriction text in this phase. Do not treat "not rendered visually" as a gap against that criterion.

### Claude's Discretion
- Exact projection math implementation details (equirectangular vs other cosine-corrected approach), the specific data structures for navdata storage/loading, and how the runway/procedure static elements integrate into the existing `build_static_background()` caching are left to research/planning, per the project's existing STACK.md and ARCHITECTURE.md research (which already recommends geographiclib + a cosine-corrected equirectangular-style projection shared between display and future separation math).
- Magnetic variation is already decided at the project level as a single hardcoded constant for v1 (see STATE.md Blockers/Concerns and research/SUMMARY.md) — not re-litigated here. Re-confirm the exact EGGW magnetic variation value against current charts at implementation time.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Scope & Decisions
- `.planning/PROJECT.md` — core value, v1 scope, constraints (esp. "no live AIRAC ingestion" — hand-authored navdata only)
- `.planning/REQUIREMENTS.md` — NAV-01/02/03, RADAR-04 (this phase's requirements)
- `.planning/ROADMAP.md` — Phase 2 goal, success criteria, and Phase 3/4 boundaries this phase must not cross

### Research
- `.planning/research/ARCHITECTURE.md` — navdata/procedure store design, sim-core-never-imports-pygame boundary (still applies: navdata module must stay in the headless sim core)
- `.planning/research/STACK.md` — geographiclib recommendation, Pydantic v2 modeling conventions for navdata
- `.planning/research/PITFALLS.md` — Pitfall 3 (heading/course/track/bearing field-naming conflation), Pitfall 4 (true/magnetic convention), Pitfall 5 (uncorrected radar projection rendering ellipses instead of circles) — all three are exactly what this phase must get right
- `.planning/research/SUMMARY.md` — Phase 2 delivery summary (§"Phase 2: Navdata + Coordinate Projection"), magnetic variation hardcoded-constant note

### Prior Phase Context
- `.planning/phases/01-walking-skeleton-sim-clock-radar-render-loop/01-CONTEXT.md` — D-01 (dark flat modern-EFIS palette), D-03 (fixed 1280x800 window) — both carry forward unchanged into this phase
- `.planning/phases/01-walking-skeleton-sim-clock-radar-render-loop/01-SUMMARY.md` through `01-05-SUMMARY.md` — what exists today: `src/atc_sim/render/radar.py` (`build_static_background()`, `draw_frame()`), `src/atc_sim/render/window.py` (color palette constants, `WINDOW_SIZE`), `src/atc_sim/sim/aircraft.py`/`interpolation.py`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/atc_sim/render/window.py` — existing color palette constants (`BG_COLOR`, `RING_COLOR`, `SECTOR_COLOR`, `AIRCRAFT_COLOR`, `TRAIL_COLOR`, `VECTOR_COLOR`) and `WINDOW_SIZE` — new runway/fix/procedure-line colors should extend this same palette rather than introducing new ad-hoc colors.
- `src/atc_sim/render/radar.py::build_static_background()` — currently draws range rings and sector lines as a cached static surface. The runway symbol, procedure fixes, and connecting lines are also static (don't move per-tick) and are natural candidates to extend this same cached background rather than redrawing every frame.
- `src/atc_sim/render/radar.py::RenderState` (a `typing.Protocol`) — established pattern (from the Phase 1 01-04 deviation) for giving render code type-safe access to sim state without importing sim modules directly. Follow this pattern if new render code needs typed access to navdata.

### Established Patterns
- Sim/render architectural boundary: only `app.py` may import both `pygame` and `atc_sim.sim.*` (enforced by `tests/test_boundary.py` and the Phase 1 01-04 Protocol pattern). Navdata models belong in the sim core (`atc_sim.sim.*` or a sibling `atc_sim.navdata` module that is also pygame-free) — this must hold for the same testability reasons as the rest of the sim core.
- Pydantic v2 conventions already locked in from Phase 1 research: `ConfigDict`, `validate_assignment=True` for live/mutable state, `frozen=True` for immutable per-tick snapshots. Navdata (runway/fix/procedure) is read-only reference data loaded once at startup — likely a good fit for frozen/immutable models.

### Integration Points
- Projection math (lat/lon → pixel) needs to be usable both by the render layer (drawing the runway/fixes) and, in a future phase, by the separation-check math — per RADAR-04 and the project's core "sim never lies about separation" value. Build it as a shared, sim-core utility from the start, not render-only code.

</code_context>

<specifics>
## Specific Ideas

- Fix markers should look like a real radar/chart waypoint symbol (small dot/triangle + name), not just a raw dot — this reflects the "modern EFIS/radar workstation" look established in Phase 1.
- The SID/STAR procedure line should read as a thin, low-clutter track — consistent with how range rings and sector lines were kept minimal in Phase 1, not a bold/thick line that competes visually with the aircraft symbol.

</specifics>

<deferred>
## Deferred Ideas

- **On-canvas restriction text (e.g. "5000A" next to a fix)** — raised and explicitly deferred to Phase 4, which owns datablock/instruction-info display (RADAR-02). Restrictions are still modeled as data in this phase (D-05); only the visual rendering is deferred.

[None else — discussion stayed within phase scope]

</deferred>

---

*Phase: 2-navdata-coordinate-projection*
*Context gathered: 2026-07-05*
