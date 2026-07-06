# Phase 4: Instruction Handling — Click, Panel, Vectoring & ILS Capture - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-06
**Phase:** 4-instruction-handling-click-panel-vectoring-ils-capture
**Areas discussed:** Click selection & feedback, Command panel design, ILS capture realism, Datablock content & format

---

## Click Selection & Feedback

| Option | Description | Selected |
|--------|-------------|----------|
| Highlight ring | Colored circle/ring around the aircraft dot | |
| Color change | Dot/datablock text changes color when selected | |
| Datablock box/border | Bordered box around the datablock text only | ✓ |

**User's choice:** Datablock box/border
**Notes:** Chosen to reserve dot coloring for future status/alert use (Phase 5 STCA).

| Option | Description | Selected |
|--------|-------------|----------|
| Single-select only | Clicking a new aircraft deselects the previous one | ✓ |
| Multi-select with shift-click | Shared instruction to multiple aircraft at once | |

**User's choice:** Single-select only

| Option | Description | Selected |
|--------|-------------|----------|
| Nearest-to-click wins | Pick whichever aircraft is closest to the click, within a hit radius | ✓ |
| Cycle on repeated clicks | Clicking the same spot cycles through overlapping aircraft | |
| Reject ambiguous clicks | Select nothing if more than one aircraft is within hit radius | |

**User's choice:** Nearest-to-click wins

| Option | Description | Selected |
|--------|-------------|----------|
| Deselect current aircraft | Empty-space click clears selection | ✓ |
| No-op, keep current selection | Empty-space clicks are ignored | |

**User's choice:** Deselect current aircraft

---

## Command Panel Design

| Option | Description | Selected |
|--------|-------------|----------|
| Text entry field | Type a number and press Enter/click a button | |
| Increment/decrement buttons | +/- buttons stepping by a fixed increment | |
| Dial/slider control | Circular heading dial and vertical altitude/speed sliders, drag to set | ✓ |

**User's choice:** Dial/slider control
**Notes:** More UI work than the alternatives, but chosen for authenticity to a real radar console.

| Option | Description | Selected |
|--------|-------------|----------|
| Buttons + fix list | Discrete clearance buttons plus a clickable list of procedure fix names | ✓ |
| Click fix directly on radar | Direct-to-fix issued by clicking the fix symbol on the radar canvas | |

**User's choice:** Buttons + fix list

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed side panel | Permanent vertical strip, greyed out when nothing selected | |
| Bottom bar | Permanent horizontal strip along the bottom | |
| Floating panel near selection | Panel appears next to the selected aircraft, moves around, disappears when empty | ✓ |

**User's choice:** Floating panel near selection

| Option | Description | Selected |
|--------|-------------|----------|
| Track continuously | Panel re-positions every frame as the aircraft moves | |
| Snap on selection, then fixed | Panel appears at selection position and stays fixed until reselected | ✓ |

**User's choice:** Snap on selection, then fixed
**Notes:** Prioritizes stable interaction with the dial/slider over continuous visual attachment to the aircraft.

---

## ILS Capture Realism

| Option | Description | Selected |
|--------|-------------|----------|
| Vector-to-intercept required | Cleared approach arms capture; aircraft must be within realistic intercept geometry before establishing | ✓ |
| Auto-intercept from anywhere | Cleared approach immediately computes a path onto the localizer/glideslope regardless of position | |

**User's choice:** Vector-to-intercept required

| Option | Description | Selected |
|--------|-------------|----------|
| Same intercept check for both | Procedural and vectored arrivals both pass through the same intercept-geometry check | ✓ |
| Procedural arrivals auto-capture | Procedural arrivals skip the geometry check; only vectored aircraft need it | |

**User's choice:** Same intercept check for both
**Notes:** Directly satisfies ROADMAP success criterion #5 ("one well-defined guidance state, never ambiguous").

| Option | Description | Selected |
|--------|-------------|----------|
| Vector breaks the capture | New heading instruction pulls an established aircraft back into ordinary vector guidance | ✓ |
| Established aircraft ignores new headings | Heading instructions to an established aircraft are ignored | |

**User's choice:** Vector breaks the capture

| Option | Description | Selected |
|--------|-------------|----------|
| ILS owns altitude once captured | Altitude instructions have no effect on an established aircraft's vertical path | ✓ |
| Altitude instructions still override | Assigned altitude can still pull the aircraft off the glidepath | |

**User's choice:** ILS owns altitude once captured
**Notes:** Keeps exactly one way (heading) to break an established capture, consistent with the prior answer.

---

## Datablock Content & Format

| Option | Description | Selected |
|--------|-------------|----------|
| Blank/omitted | No assigned-instruction line until the player issues something | ✓ |
| Shows 'PROC' or procedure name | Always shows a label even before any instruction | |

**User's choice:** Blank/omitted

| Option | Description | Selected |
|--------|-------------|----------|
| Compact codes | Real-radar-style abbreviations (H270, A050, S210, ILS, DCT BNN) | ✓ |
| Plain text | Spelled-out labels (HDG 270, ALT 5000, SPD 210, CLRD APP, DIRECT BNN) | |

**User's choice:** Compact codes

| Option | Description | Selected |
|--------|-------------|----------|
| Show all active, stacked | Every concurrently active instruction gets its own token | ✓ |
| Most recent only | Only the latest instruction issued is shown | |

**User's choice:** Show all active, stacked

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, distinct codes | Different code while armed/intercepting vs. once established | ✓ |
| No, single code throughout | Same code from clearance through landing | |

**User's choice:** Yes, distinct codes

---

## Claude's Discretion

- Exact hit-radius (pixels) for click selection and exact intercept angle/distance thresholds for ILS capture.
- Exact dial/slider visual design (colors, size, snap increments) and floating-panel screen-edge-clamping behavior.
- Exact shorthand code strings beyond the illustrative examples (e.g. codes for cleared-for-takeoff/landing).
- Whether the dial/slider and buttons/fix-list live in one combined floating panel or visually grouped sub-sections.

## Deferred Ideas

None — discussion stayed within phase scope.
