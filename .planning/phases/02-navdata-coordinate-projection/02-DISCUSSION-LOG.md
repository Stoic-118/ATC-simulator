# Phase 2: Navdata & Coordinate Projection - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-05
**Phase:** 2-navdata-coordinate-projection
**Areas discussed:** Waypoint/fix visual style, Real vs simplified navdata, Procedure path rendering, Restriction display timing

---

## Waypoint/Fix Visual Style

| Option | Description | Selected |
|--------|-------------|----------|
| Dot + name label | Small marker plus the fix's 5-letter name next to it — matches real radar scopes/charts | ✓ |
| Dot only | Just a marker, no text label — simplest, harder to visually confirm which fix is which | |
| Dot + name + restrictions | Marker, name, and altitude/speed restriction annotated on canvas — most chart-realistic but more rendering work now | |

**User's choice:** Dot + name label
**Notes:** No further questions raised in this area.

---

## Real vs Simplified Navdata

| Option | Description | Selected |
|--------|-------------|----------|
| Real EGGW SID/STAR | Actual published EGGW runway-26 SID/STAR, real fix names/coordinates hand-typed from public charts | ✓ |
| Simplified/invented procedure | Plausible but not sourced from a real chart | |

**User's choice:** Real EGGW SID/STAR
**Notes:** Follow-up question asked whether the user had a specific SID/STAR in mind.

| Option | Description | Selected |
|--------|-------------|----------|
| Researcher picks | Phase 2 researcher looks up EGGW's published runway-26 charts and picks one well-documented SID and STAR | ✓ |
| I have one in mind | User names a specific procedure to lock in now | |

**User's choice:** Researcher picks

---

## Procedure Path Rendering

| Option | Description | Selected |
|--------|-------------|----------|
| Connecting line | Thin line linking the procedure's fixes in sequence | ✓ |
| Isolated fix markers only | Just dots + labels, no connecting line | |

**User's choice:** Connecting line
**Notes:** No further questions raised in this area.

---

## Restriction Display Timing

| Option | Description | Selected |
|--------|-------------|----------|
| Internal data only for now | Model restrictions as Pydantic fields, don't render as canvas text yet — defers to Phase 4's datablock display | ✓ |
| Show restriction text now | Render restriction values as canvas text immediately | |

**User's choice:** Internal data only for now
**Notes:** Flagged in CONTEXT.md that ROADMAP.md's success criterion #2 wording ("...each with its modeled altitude/speed restrictions") is satisfied by correct data modeling, not necessarily on-screen text — to prevent this being misread as an unmet criterion during planning/verification.

---

## Claude's Discretion

- Exact projection math implementation (equirectangular vs other cosine-corrected approach), navdata storage/loading structures, and how static navdata elements integrate into the existing `build_static_background()` caching.
- Magnetic variation value re-confirmation against current EGGW charts (the hardcoded-constant decision itself was already made at the project level, prior to this discussion).

## Deferred Ideas

- **On-canvas restriction text** (e.g. "5000A" next to a fix) — deferred to Phase 4, which owns datablock/instruction-info display (RADAR-02).
