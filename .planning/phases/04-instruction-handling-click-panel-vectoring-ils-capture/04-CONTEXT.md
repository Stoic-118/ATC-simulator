# Phase 4: Instruction Handling — Click, Panel, Vectoring & ILS Capture - Context

**Gathered:** 2026-07-06
**Status:** Ready for planning

<domain>
## Phase Boundary

The player can click any aircraft on the radar to select it, then issue real ATC instructions (heading, altitude/level, speed, direct-to-fix, cleared-approach, cleared-for-takeoff/landing) via a command panel. Instructions override procedure-following as a layer on top of it — not a separate movement path — and an aircraft reaches ILS-established guidance (localizer then glideslope) through exactly one well-defined state whether it got there via vectors or by continuing its SID/STAR procedurally. No separation/conflict checking yet (Phase 5), no scripted scenario loader yet (Phase 6 — traffic is still the Phase 3 demo harness), no phraseology/comms log yet (Phase 7 — no readback text). Requirements covered: INST-01, INST-02, INST-03, PROC-02, PROC-03, RADAR-02.

</domain>

<decisions>
## Implementation Decisions

### Click Selection & Feedback
- **D-01:** Selection feedback is a box/border drawn around the datablock text — not a ring or color change on the aircraft dot itself. Keeps the aircraft symbol itself reserved for future status/alert coloring (e.g. Phase 5's STCA conflicts) without visual collision with "selected" state.
- **D-02:** Single-select only. Clicking a new aircraft deselects whatever was previously selected — there is never more than one selected aircraft, and the command panel always reflects exactly one aircraft's state.
- **D-03:** Ambiguous/overlapping clicks resolve to nearest-dot-to-click-point within a fixed hit radius. No cycling, no rejection.
- **D-04:** Clicking empty radar space (no aircraft within hit radius) deselects the current aircraft and closes/hides the command panel.

### Command Panel Design
- **D-05:** Heading, altitude, and speed are entered via a dial/slider control (not text entry, not increment buttons) — the player drags to set the value. This is a genuinely new UI element with no existing precedent in the codebase (first real pygame_gui-or-hand-rolled interactive widget beyond static drawing).
- **D-06:** Direct-to-fix, cleared-approach, and cleared-for-takeoff/landing are issued via discrete buttons plus a clickable list of the current procedure's fix names — not by clicking fix symbols directly on the radar canvas. Keeps radar-canvas click handling scoped to aircraft selection only (D-01–D-04); the panel owns all non-selection clicks.
- **D-07:** The panel is a floating panel that appears near the selected aircraft, not a fixed side panel or bottom bar.
- **D-08:** The floating panel snaps to the aircraft's position at the moment of selection and then stays fixed at that screen location — it does NOT track the aircraft's continued movement. (Reselecting the same aircraft, or selecting a different one, repositions it.) This keeps the dial/slider stable to interact with while open.

### ILS Capture Realism
- **D-09:** "Cleared approach" arms the capture but does not teleport/auto-path the aircraft onto the localizer. The aircraft must actually be within a realistic intercept angle/distance of the localizer course (via vectoring or procedural track) before it transitions into the established guidance state. Until then, a cleared-but-not-yet-intercepting aircraft keeps flying whatever heading it currently has (vectored or procedural).
- **D-10:** The same intercept-geometry check applies uniformly to vectored AND procedural (STAR-following) arrivals — there is exactly one code path that produces the established state, never a separate "procedural auto-capture" shortcut. This directly satisfies ROADMAP success criterion #5's "always exactly one well-defined guidance state, never ambiguous."
- **D-11:** Issuing a new heading instruction to an aircraft that is already established on the ILS breaks the capture — it reverts to ordinary heading-vector guidance and must be re-cleared for approach (and re-intercept) to rejoin. This is the only way to break an established capture.
- **D-12:** Once glideslope is captured, the ILS owns altitude completely — an assigned-altitude instruction issued to an established aircraft has no effect on its vertical path (only a heading instruction can break the capture, per D-11). This keeps exactly one way to leave the guidance state.

### Datablock Content & Format
- **D-13:** An aircraft with no player instruction yet (pure procedure-following) shows no assigned-instruction line at all — the datablock is just callsign/altitude/speed until the player issues something.
- **D-14:** Once instructions exist, they render as compact ATC shorthand codes (e.g. `H270` heading, `A050` altitude, `S210` speed, `DCT BNN` direct-to-fix) rather than spelled-out plain text.
- **D-15:** All currently active instructions render simultaneously (stacked/concatenated), not just the most recently issued one — e.g. an aircraft with both an assigned heading and an assigned speed shows both codes at once.
- **D-16:** The ILS clearance code is distinct between "cleared, still intercepting" and "established" — e.g. `ILS` while armed/intercepting, switching to a different code (e.g. `LOC`/`GS` or an established indicator) once actual capture per D-09/D-10 occurs. Gives the player direct visual feedback on whether a heading instruction would currently break an established capture (D-11) or just adjust an intercepting vector.

### Claude's Discretion
- Exact hit-radius (pixels) for click selection (D-03) and exact intercept angle/distance thresholds for ILS capture (D-09/D-10) are implementation details for the researcher/planner to size against the existing radar scale and Phase 3's aircraft speeds — not user vision decisions.
- Exact dial/slider visual design (colors, size, snap increments) and exact floating-panel screen-edge-clamping behavior (D-07/D-08) when a selected aircraft is near the window edge.
- Exact shorthand code strings beyond the illustrative examples in D-14/D-16 (e.g. whether cleared-for-takeoff/landing get their own short codes) — pick conventions consistent with real radar datablock shorthand.
- Whether the dial/slider and buttons/list live in one combined floating panel or are visually grouped as sub-sections of it — a layout detail, not a vision decision.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Scope & Decisions
- `.planning/PROJECT.md` — core value, v1 scope; Active requirements section already lists "Click + command-panel input", "Core instruction set", "Vectoring + ILS capture" as this phase's targets
- `.planning/REQUIREMENTS.md` — INST-01/02/03, PROC-02/03, RADAR-02 (this phase's requirements)
- `.planning/ROADMAP.md` — Phase 4 goal, all 6 success criteria, and Phase 5/6/7 boundaries this phase must not cross (no separation checking, no scenario loader, no phraseology log yet)

### Prior Phase Context
- `.planning/phases/03-aircraft-performance-flight-phase-fsm-procedure-following/03-CONTEXT.md` and `03-RESEARCH.md` — the 8-state Phase enum (no ILS sub-states — this phase must decide how/where the established-ILS guidance state is represented), `compute_target()` procedure-following seam this phase's vectoring override layers on top of, the demo-traffic harness this phase's click/panel interacts with
- `.planning/phases/02-navdata-coordinate-projection/02-CONTEXT.md` — OLNEY 2B SID / DET 2A STAR fix data (names/coordinates) needed for the direct-to-fix button list (D-06)
- `.planning/phases/01-walking-skeleton-sim-clock-radar-render-loop/01-CONTEXT.md` — dark flat modern-EFIS radar palette this phase's selection border/panel/dial styling should match

### Research
- `.planning/research/ARCHITECTURE.md` — Pattern 3 (procedure-following-with-vectoring-override-layer, `compute_target()` seam) — this phase is what that seam was built for
- `.planning/research/SUMMARY.md` — original research-sketch notes for instruction handling and ILS capture, if present

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/atc_sim/sim/aircraft.py::Aircraft` — Pydantic v2 model with `validate_assignment=True`; this phase adds assigned-instruction fields (heading/altitude/speed/direct-to-fix targets, cleared-approach/takeoff/landing flags, established-guidance state) without breaking the existing phase/procedure/performance fields.
- `src/atc_sim/sim/procedure.py::compute_target()` — the existing seam that CLIMB/ENROUTE/DESCENT read for procedure-derived targets (`Targets` namedtuple/dataclass with heading_deg/altitude_ft/speed_kt). Vectoring override (D-09 through D-12) should intercept or wrap this seam rather than duplicating target computation.
- `src/atc_sim/sim/phase.py::Phase`, `LEGAL_TRANSITIONS`, `transition_to()` — the 8-state FSM has no ILS sub-states (per 03-CONTEXT.md decision); this phase must decide whether established-ILS guidance is a new Phase member, a flag/sub-state on APPROACH, or a separate guidance-mode field orthogonal to Phase. This is exactly the "single well-defined guidance state" (D-10) the roadmap requires — a research/planning decision, not decided here.
- `src/atc_sim/render/radar.py::RenderState` Protocol, `draw_frame()` — extend for datablock rendering (D-13–D-16) and selection border (D-01); currently only draws dot/vector/trail, no datablock text yet.
- `src/atc_sim/app.py` — currently only handles `pygame.QUIT`; this phase adds `pygame.MOUSEBUTTONDOWN` handling for click-to-select (D-01–D-04) and whatever event handling the dial/slider/buttons (D-05/D-06) require.

### Established Patterns
- Sim/render architectural boundary: only `app.py` imports both `pygame` and `atc_sim.sim.*` (enforced by `tests/test_boundary.py`). Instruction-assignment logic (what an instruction does to an Aircraft) belongs in `atc_sim.sim.*`, pygame-free and unit-testable; only the panel widgets/click-hit-testing themselves are pygame-side.
- `validate_assignment=True` + `Field` bounds convention for all live Aircraft state — new instruction fields should follow the same convention.

### Integration Points
- `demo_traffic.update_demo_traffic()` — instruction state must survive across ticks the same way phase/procedure state does; whatever field(s) represent an active instruction need to be read by `sim_step()`'s per-phase kinematics dispatch (`_step_airborne` etc. in `aircraft.py`) ahead of or in place of `compute_target()`.
- No pygame_gui usage exists anywhere in the codebase yet — if the dial/slider (D-05) is built with pygame_gui rather than hand-rolled, this phase introduces that dependency's first real usage (pygame_gui is already in the approved stack per CLAUDE.md's Technology Stack section).

</code_context>

<specifics>
## Specific Ideas

- The floating, snap-on-selection panel (D-07/D-08) was chosen specifically so the dial/slider doesn't drift under the player's cursor while they're dragging it — stability during interaction was prioritized over continuous visual attachment to the moving aircraft.
- The ILS realism decisions (D-09–D-12) consistently favor matching real-world ATC procedure (vector-to-intercept required, heading breaks capture, altitude instructions ignored once established) over simpler "just works" alternatives — this mirrors the project's stated core value that "the sim never lies."
- Compact shorthand datablock codes (D-14) were chosen to match authentic radar display conventions, consistent with the project's general preference for realism (real airport, real SID/STAR, real ILS parameters) established in Phases 1-3.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 4-instruction-handling-click-panel-vectoring-ils-capture*
*Context gathered: 2026-07-06*
