# Pitfalls Research

**Domain:** Single-airport ATC simulator — native Python + Pygame desktop app, fixed-timestep sim clock, real-world navdata (EGGW/26), alert-only separation
**Researched:** 2026-07-03
**Confidence:** MEDIUM (cross-checked web sources for game-loop, navigation-terminology, ILS, STCA, and UI-hit-target claims; HIGH-confidence domain synthesis for how these generic pitfalls manifest in this specific architecture)

## Critical Pitfalls

### Pitfall 1: Fixed-timestep accumulator without a step cap (spiral of death)

**What goes wrong:**
The sim clock (1-4Hz) is decoupled from the render loop (60fps) using an accumulator: each render frame adds elapsed wall time to a bucket and drains fixed-size sim ticks from it. If a sim tick ever takes longer, in wall-clock time, than the sim-time it advances (e.g. a slow separation check, a GC pause, a debugger breakpoint, or just too many aircraft), the accumulator doesn't drain fully before the next frame adds more time. The next frame must run *more* catch-up ticks to drain it, which takes even longer, which adds more backlog — the app appears to freeze or the sim clock appears to leap forward unpredictably.

**Why it happens:**
Developers implement "Fix Your Timestep"-style accumulator loops correctly for the steady-state case but skip the max-steps-per-frame clamp because it never triggers in early testing (few aircraft, fast machine). It only surfaces once traffic volume, separation-check cost, or a slow frame (window drag, OS hiccup, breakpoint) pushes tick cost above the tick interval.

**How to avoid:**
Clamp the number of sim ticks processed per render frame (e.g. max 4-8 ticks/frame) and/or clamp the accumulator itself to a max value. When the cap is hit, let the sim visibly run slow rather than trying to catch up — this is explicitly the industry-standard mitigation, not a workaround. Log/counter for "ticks dropped due to cap" so degradation is visible during dev, not silent.

**Warning signs:**
Sim appears to "jump" aircraft positions after any window-drag, breakpoint pause, or CPU spike; frame time occasionally spikes and the sim visibly free-runs to catch up; adding aircraft count increases stutter non-linearly rather than smoothly.

**Phase to address:**
The very first phase that establishes the game loop / sim clock architecture — this is a foundational primitive, not a later optimization. Verification: deliberately stall the render thread (e.g. `time.sleep`) mid-run and confirm the sim slows down instead of hanging or leaping.

---

### Pitfall 2: Frame-rate-dependent behavior creeping back in despite an explicit sim/render split

**What goes wrong:**
The architecture correctly separates a fixed-Hz sim tick from the 60fps render loop, but individual features are implemented against "the frame" instead of "the tick" — e.g., a UI animation timer, an alert-flash blink rate, an input-debounce counter, or interpolation math is written using `pygame.Clock.get_time()` / frame count directly rather than accumulated sim time. This reintroduces frame-rate coupling in a subsystem while the top-level architecture diagram looks correct.

**Why it happens:**
`clock.get_time()` returns milliseconds since the *last frame*, not total elapsed time, and it's tempting to use it inline for "just this one animation" without routing through the same delta-time/tick-count plumbing used by the sim. Because Pygame doesn't enforce this, mixed frame-based and tick-based logic compiles and runs fine on the dev machine's frame rate and only reveals itself when frame rate differs (different machine, unfocused window throttling, vsync toggling).

**How to avoid:**
Establish one authoritative time source (accumulated sim ticks, or accumulated wall-clock seconds) at the start of the loop-architecture phase, and route every time-dependent calculation through it — including "cosmetic" things like blink timers and readback-log auto-scroll. Treat any direct use of per-frame delta outside the render-interpolation layer as a code-review flag.

**Warning signs:**
Anything that "feels different speed" when the window loses focus, when other apps are busy, or when moving the window (Pygame often throttles frame delivery during a drag); blink/animation timers that visibly speed up or slow down under load while aircraft motion stays correct (proof the split is only half-applied).

**Phase to address:**
Foundational game-loop phase, then spot-check at every subsequent phase that adds a timer-driven UI element (alerts, readback log, blink states).

---

### Pitfall 3: Conflating bearing, course, track, and heading in the data model

**What goes wrong:**
These four aviation terms are related but distinct, and the domain gets it wrong in exactly the place it matters most — instruction handling and separation math. Heading is where the aircraft's nose points (what the player assigns with a "fly heading" instruction). Course is the intended/published direction of a procedure or route leg (e.g., a SID's initial course, or the ILS localizer course). Track is the aircraft's actual path over the ground. Bearing is the angle from one point to another (e.g., "bearing from aircraft to fix," used for direct-to guidance) and has nothing to do with the aircraft's own orientation. A model that stores one field called `heading` and reuses it for "course to fly direct-to-fix" or for "localizer bearing" will produce subtly wrong turn commands, especially when wind or drift is introduced later.

**Why it happens:**
In a no-wind, zero-drift simplified model (this project's v1 has no stated wind modeling), heading and track are numerically identical, so the distinction feels academic — until direct-to-fix logic needs the *bearing to the fix* (a great-circle bearing calculation) converted into a *turn instruction* (a heading), and localizer capture needs the *published course* compared against the aircraft's *current track*, not its instantaneous heading.

**How to avoid:**
Name fields explicitly and distinctly from day one: `heading_deg` (aircraft orientation), `course_deg` (procedure/leg-intended direction), `bearing_to_fix_deg` (computed per-tick from geographiclib inverse geodesic), even if `heading == track` for all of v1 because there's no wind model. This makes the eventual wind/drift addition (if ever added) a non-breaking change instead of a rename-everything refactor, and prevents "direct to fix" bugs where the aircraft is commanded to fly a bearing as if it were a heading, which is directionally correct only by lucky coincidence in a no-wind world.

**Warning signs:**
Any function whose signature or variable name is ambiguous between "assigned heading" and "computed bearing to a point"; "direct to fix" commands that only work correctly for fixes directly ahead of the aircraft.

**Phase to address:**
Navdata/aircraft-state data-model phase (Pydantic models) — this is a naming and schema decision, cheap to get right early, expensive to fix once instruction-handling and separation logic both depend on it.

---

### Pitfall 4: True vs. magnetic heading applied inconsistently across the data pipeline

**What goes wrong:**
Real-world procedures (SIDs, STARs, the ILS localizer course for runway 26 at EGGW) are published in **magnetic** degrees, matching how the runway is named (runway "26" is defined by its magnetic heading, ~260°) and how a controller would phrase an instruction ("fly heading 260"). But great-circle math (bearing/course between two lat/lon points, computed via geographiclib/pyproj) naturally produces **true** bearings. If magnetic variation (~1-2° W at EGGW currently) isn't applied at a single, well-defined boundary, the sim will show a plausible-looking but subtly wrong ILS course, a "fly heading" readback that doesn't match what the aircraft actually turns to, or an aircraft that intercepts the localizer at the wrong angle because computed-true and published-magnetic values were compared directly.

**Why it happens:**
This is a well-documented recurring bug class in real flight simulators (FlightGear and X-Plane forums both report exactly this: one display/subsystem uses true, another uses magnetic, and the two are shown or compared without reconciling variation). It's easy because the error is small (a couple of degrees at this latitude) and doesn't look obviously "broken" — it looks like slightly sloppy localizer tracking, which is easy to misattribute to the aircraft performance model instead of the heading convention.

**How to avoid:**
Decide explicitly, once: store navdata courses/headings in magnetic (matching real-world charts and controller phraseology, since this project intentionally mirrors real procedure naming), and apply magnetic variation exactly once — at the boundary where a true bearing comes out of the geodesic library and needs to be compared against or displayed alongside a published magnetic course. Since EGGW is a single fixed airport for all of v1, variation can be a single hardcoded constant for the region rather than a full magnetic-model — but it must not be silently omitted (treated as 0) without that being a documented, deliberate simplification.

**Warning signs:**
Aircraft consistently intercept the localizer a degree or two off-axis; assigned heading vs. displayed track never quite converge to the runway course number; unit tests for "fly runway heading" pass numerically but the localizer capture logic still reports non-zero cross-track error at the runway threshold.

**Phase to address:**
Navdata phase (define whether stored values are true or magnetic, and where variation is applied) and ILS/procedure-modeling phase (verify the localizer course comparison uses the same convention as the aircraft's course value).

---

### Pitfall 5: Naive lat/lon → screen-pixel projection without a local cosine correction

**What goes wrong:**
The radar canvas needs to convert EGGW-area lat/lon into screen x/y. The simplest approach — treat longitude degrees and latitude degrees as directly proportional to x and y pixels — silently stretches east-west distances relative to north-south distances, because a degree of longitude covers less ground distance than a degree of latitude at any latitude other than the equator (the ratio is cos(latitude)). At EGGW's latitude (~52°N), a degree of longitude is about 61% the distance of a degree of latitude. Left uncorrected, the radar display will show circles as ellipses, range rings as ovals, and — worse — the *visual* bearing between two aircraft or between an aircraft and a fix will not match the *actual* bearing used by the separation/navigation math, making the display actively misleading to the player.

**Why it happens:**
It's the simplest possible implementation and looks approximately right at first glance (a wide-area map doesn't reveal the distortion at a casual look), so it's easy to ship without noticing — especially for a solo developer who isn't cross-checking the display against a real chart.

**How to avoid:**
Use a local tangent-plane / equirectangular projection with an explicit cosine correction: pick a reference latitude (e.g., the airport reference point), and scale the x-axis (longitude-derived) distance by cos(reference_latitude) relative to the y-axis (latitude-derived) distance, so that 1 pixel represents the same ground distance in both axes. This is standard practice for small-area (single-TMA-scale) radar-style rendering and is accurate enough at this scale — a full map projection (Mercator etc.) is unnecessary and would add complexity without benefit for an area this small. Critically, use the *same* geodesic library (geographiclib/pyproj) for both the "real" separation math and the "visual" projection math so the two never disagree — a common bug is doing separation math on the sphere but the display on an uncorrected flat grid, producing a picture that looks inconsistent with the alerts it's showing (an aircraft pair the STCA flags as inside 5nm horizontal but that looks farther apart on the misprojected display, undermining player trust).

**Warning signs:**
Range rings render as ellipses instead of circles; two points that are the same real-world distance apart look like different distances on screen depending on their east-west vs. north-south offset; a separation alert fires for two aircraft that look visually far apart on the radar.

**Phase to address:**
Radar canvas rendering phase — establish the projection function once, alongside the great-circle math phase, and reuse it everywhere (aircraft position, fixes, range rings, trail dots) rather than each renderer inventing its own conversion.

---

### Pitfall 6: ILS/procedure state machine left ambiguous between "on vectors" and "on procedure"

**What goes wrong:**
An aircraft's lateral/vertical guidance state needs to be unambiguous at every tick: is it flying an assigned heading (vectors), flying direct-to-a-fix, following the SID/STAR procedure legs, or capturing/established on the localizer and glideslope? A common bug class is allowing two of these to be simultaneously "kind of true" — e.g., a heading instruction is issued to an aircraft that's already established on the localizer, and the code doesn't clearly decide whether the localizer capture should be dropped, or a "cleared approach" instruction is issued to an aircraft that's still outside the 30°-ish intercept-angle window real ILS systems require, and the aircraft is left oscillating between correcting toward the localizer and being "captured" without ever stabilizing.

**Why it happens:**
It's tempting to model this as a set of independent booleans (`has_assigned_heading`, `is_on_ils`, `is_direct_to_fix`) that get set by instruction handlers, rather than as a true finite-state machine with explicit transitions. Independent flags can end up in combinations the designer never intended (e.g., both "vectoring" and "localizer captured" true at once), and nothing forces a decision about which one wins.

**How to avoid:**
Model lateral guidance mode as a single enum/state (VECTORS, DIRECT_TO_FIX, PROCEDURE, LOC_ARMED, LOC_CAPTURED) with explicit transition rules, mirroring the real-world logic this domain already has good reference material for: localizer capture should only arm when within a bounded intercept angle of the published course (real-world ~30°) and should only transition from armed to captured once the deviation signal is stably within a threshold band, executing a single turn onto the centerline. A new heading instruction while LOC_CAPTURED must explicitly drop back to VECTORS (matching real-world "vectors for another approach" behavior) rather than leaving stale localizer state active in the background. Keep vertical (glideslope) and lateral (localizer) mode as related but separately-tracked state, since a real aircraft can be localizer-captured without yet being glideslope-captured.

**Warning signs:**
An aircraft under a heading instruction that still snaps back toward the localizer centerline; an aircraft "cleared for the approach" from a poor intercept angle that overshoots through the localizer and re-intercepts from the other side; glideslope deviation logic running before localizer capture has occurred.

**Phase to address:**
The approach/ILS modeling phase — design the guidance-mode state machine explicitly before writing capture-angle math, and write the "reassign heading while established" transition as an explicit test case, not an afterthought.

---

### Pitfall 7: Simplified performance profiles producing numerically-correct but experientially-wrong climb/descent/turn behavior

**What goes wrong:**
A simplified per-type performance profile (fixed climb rate, fixed descent rate, turn rate as a function of bank angle and groundspeed) can satisfy every stated numeric constraint and still "feel wrong" to anyone with real ATC/aviation familiarity, because real profiles aren't flat — climb rate decreases as altitude increases (thinner air, same thrust), descent rate/speed interact (an aircraft can't simultaneously descend fast, decelerate fast, and stay configured cleanly for approach — this is exactly the real "energy management" problem where excess altitude and excess speed can't both be bled off at once). A model that treats climb rate and speed and descent rate as independent knobs will let the player instruct physically-incoherent combinations (e.g., "descend to bleed excess speed" then "reduce speed" simultaneously) that a real jet-shaped energy model would refuse or would require the player to feel a lag from.

**Why it happens:**
Independent, decoupled per-parameter profiles (a scalar climb rate, a scalar descent rate, a scalar speed) are the natural first implementation and are explicitly what this project has chosen for v1 (not BADA-style tables). The risk isn't the simplification itself — it's simplifying past the point where the *coupling* between altitude, speed, and configuration disappears entirely, which is what real controllers rely on (e.g., knowing a descending aircraft can't also slow down quickly without extra track miles) to plan realistic sequencing and to judge whether an instruction is achievable.

**How to avoid:**
Even in a simplified model, keep at least a coarse coupling between the three axes that matters most for the v1 loop (arrival sequencing and speed control on approach): descent rate should have a mild inverse relationship with commanded deceleration (a descending, decelerating aircraft takes measurably longer to reach a target speed than a level, decelerating one), and climb rate should taper somewhat with altitude for departures so the SID doesn't feel like a rocket. This doesn't require BADA tables — a simple multiplier or two per aircraft type is enough to avoid "numerically correct, experientially broken" behavior. Explicitly decide and document what the model does NOT couple (e.g., no wind, no weight/fuel effects) so it's a conscious scope cut, not an unnoticed gap.

**Warning signs:**
Playtesting reveals aircraft that instantly snap to a new speed/altitude/rate regardless of their current energy state; an arrival can be told to "descend and slow down" and both happen at their independent max rates simultaneously with no visible tradeoff; departure climb-outs look identical regardless of altitude.

**Phase to address:**
Aircraft performance-model phase — decide the coupling rules before writing individual aircraft-type profile data, since retrofitting coupling after profiles are authored as independent scalars means re-deriving every type's numbers.

---

### Pitfall 8: Conflict/separation checks against current position only, not projected trajectory

**What goes wrong:**
The simplest separation check compares only the current instant positions/altitudes of every aircraft pair against the horizontal (5nm) and vertical (1000ft below FL290) minima. This produces both false negatives (two aircraft closing fast will violate separation one tick from now but show clear right now, so the alert fires only after the violation has already begun, too late for the controller to act preventively) and, if look-ahead is naively long-window straight-line, false positives (a turning aircraft that will clearly diverge gets a straight-line projection that says it's heading toward another aircraft, generating a nuisance alert). This directly undermines the stated design intent that "the sim never lies about separation" — a current-position-only check is not really implementing STCA, it's implementing after-the-fact detection.

**Why it happens:**
Current-position checking is far simpler to implement first and does technically satisfy "detect when 5nm/1000ft is violated," so it's an easy stopping point that looks complete in a demo (a scripted scenario with two aircraft slowly closing will visibly alert) without revealing the false-negative timing problem until a fast-closing scenario is tested.

**How to avoid:**
Implement short-look-ahead linear trajectory projection (project each aircraft's position forward using current heading/track and groundspeed for a bounded window, e.g. 60-120 seconds, matching real STCA's "predicted within a short look-ahead time" approach) in addition to current-instant checking, so alerts fire with enough lead time for the controller to act. Explicitly accept — and document — that linear (non-turn-aware) projection will produce some nuisance alerts for turning aircraft in the terminal area; this is a known, accepted real-world STCA tradeoff, not a bug to chase to zero. Do not attempt full turn-aware/multi-hypothesis prediction for v1 — that's a real-world STCA enhancement layered on top of the basic linear predictor, appropriate for a later milestone, not the core loop.

**Warning signs:**
Two fast-closing aircraft (e.g. one behind another on the same final descending quickly) show no alert until they're already inside minima; alerts fire and then immediately clear as the projection window recalculates every tick with no hysteresis, creating flicker.

**Phase to address:**
Separation/conflict-detection phase — decide "current-instant only" vs. "current-instant + short-linear-projection" explicitly as a scope decision before implementation, since this is the phase's core value proposition ("the sim never lies about separation") and current-instant-only quietly breaks that promise.

---

### Pitfall 9: Naive O(n²) pairwise separation checks treated as a non-issue because v1 traffic is small

**What goes wrong:**
Checking every aircraft pair against every other aircraft pair every sim tick is O(n²). For v1's small scripted-scenario traffic counts (a handful of aircraft) this is genuinely a non-issue performance-wise — but the pitfall isn't performance, it's architectural: if the pairwise check is written as deeply coupled, unstructured nested loops threaded through rendering and instruction-handling code (rather than as an isolated, swappable function), it becomes expensive to later add spatial partitioning, becomes hard to unit-test in isolation, and becomes a likely source of subtle double-counting bugs (checking pair (A,B) and (B,A) both, and firing duplicate alerts) even at small n.

**Why it happens:**
Because v1's real-world scale (single airport, scripted scenario, small fleet) genuinely doesn't need spatial partitioning, it's tempting to write the pairwise loop as a quick nested `for` loop directly in the sim-tick update function rather than as a clean, isolated, well-tested module — reasoning that "performance doesn't matter at this scale" while missing that the *structure* still matters for correctness and future extensibility.

**How to avoid:**
Isolate the pairwise separation check into its own pure function (list of aircraft states in, list of conflict pairs out) even though it's O(n²) — this makes it trivially unit-testable (feed known positions, assert expected conflict pairs) and trivially swappable for a spatial-grid broad-phase later if traffic volume ever grows (e.g., a future randomized-traffic-generator milestone). Explicitly dedupe pairs (iterate `i < j`, not all ordered pairs) to avoid double-alerting on the same conflict.

**Warning signs:**
Separation-alert unit tests are hard to write because the check logic is entangled with rendering or instruction state; the same conflict produces two log entries or two alert sounds.

**Phase to address:**
Separation/conflict-detection phase — architectural isolation matters immediately regardless of when (or whether) performance ever becomes a real constraint.

---

### Pitfall 10: Click-target hit-testing sized to the visual aircraft symbol instead of a larger invisible hit-region

**What goes wrong:**
Aircraft on a radar display are rendered as small symbols (often just a few pixels) with a nearby datablock. If the click-handling code hit-tests against the exact rendered symbol bounds, selecting a specific aircraft — especially among several close together near a hold or on final — becomes frustratingly imprecise, and misclicks either select the wrong aircraft or select nothing, which is especially costly in this project because a wrong-aircraft instruction has domain-real consequences (wrong readback, potential separation issue caused by the tool rather than the player's decision).

**Why it happens:**
Fitts's Law is well established (smaller targets take longer to acquire and produce more errors) and real-world radar/ATC-sim UIs universally give aircraft symbols an invisible hit-region larger than their visual footprint — but this is easy to skip in a first pass where hit-testing is implemented as "is the click inside the symbol's pixel bounds," matching the rendering code exactly because it's the path of least resistance.

**How to avoid:**
Give every aircraft symbol a fixed-radius circular (or padded-square) hit-region independent of its visual size — sized for comfortable mouse precision (tens of pixels, not the symbol's actual few-pixel footprint) — and resolve ambiguity when multiple hit-regions overlap by picking nearest-to-click-point rather than z-order/first-match. Treat datablock text (callsign) as an equally valid click target for selection, since it's often easier to click than the tiny symbol itself and real radar displays support this.

**Warning signs:**
Playtesting shows repeated mis-selects among aircraft that are close together on screen (e.g., two aircraft in a holding pattern, or one following another on final); users need multiple attempts to select a target during a busy moment, exactly when precision matters most for issuing timely instructions.

**Phase to address:**
Click+panel input/interaction phase — decide the hit-region strategy (padded circular region, nearest-match resolution) as part of the initial input-handling design, not as a later "polish" pass, since retrofitting it means revisiting every place symbol geometry and click geometry are computed together.

---

### Pitfall 11: Investing in fidelity (aircraft performance realism, procedure variety, visual polish) before the core instruction loop is end-to-end playable

**What goes wrong:**
This project's stated v1 bar is a single, narrow, fully-working loop: launch an aircraft off the one SID, land another off the one ILS, entirely through the player's own instructions, with honest separation alerting. The single biggest risk to a solo hobby "realistic simulator" project of this kind is investing early effort into fidelity dimensions that feel core to "realism" (a richer performance model, additional aircraft types, wind, extra procedures, visual detail on the radar) before that one thin end-to-end loop actually works, because those investments are frequently reworked or wasted once the working loop reveals what it actually needs from each subsystem (e.g., the performance-model coupling in Pitfall 7 is only discoverable by playing the real approach-to-landing sequence, not by tuning numbers in isolation).

**Why it happens:**
This project's own subject matter is unusually seductive for scope creep: SIDs/STARs/ILS/performance modeling are each individually deep, well-documented, satisfying rabbit holes for a developer who enjoys the domain (evidenced by the amount of real-world nuance already surfaced in this research). It is easy to justify "just get the ILS capture logic exactly right first" or "just add one more aircraft type" as prerequisite work, when the project's own stated priority ("prioritize building it right over building it fast," but with an explicit v1 bar) is a single thin vertical slice.

**How to avoid:**
Sequence the roadmap so the absolute thinnest version of every subsystem (one hardcoded performance profile shape, the one SID, the one STAR/ILS, current-instant-only separation before adding trajectory projection) is wired together end-to-end as early as possible — even before it's "good" — so that every subsequent fidelity investment (better performance coupling, trajectory-based conflict prediction, more polished radar rendering) is validated against a real, playable loop instead of built speculatively. Treat every one of the other ten pitfalls in this document as "fix once the thin loop exists," not "must be perfect before the loop exists" — with the explicit exception of Pitfall 1 (timestep architecture) and Pitfall 3/4 (heading/bearing/course naming), which are foundational enough that getting them wrong early is expensive to unwind later even in a thin slice.

**Warning signs:**
Multiple weeks pass tuning a subsystem (performance profiles, ILS capture angles, radar visual polish) that has never been exercised by an actual instruction-driven playthrough; the project has detailed navdata/procedure/performance data before the click-to-instruction-to-readback loop fires even once end-to-end.

**Phase to address:**
Roadmap-level sequencing decision, not a single phase — the roadmap should place a minimal end-to-end vertical slice (one departure via the SID, one arrival via the STAR/ILS, current-instant separation checking, one performance profile) as early as possible, ahead of any phase whose main value is fidelity/polish on a subsystem already covered by that thin slice.

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|-----------------|------------------|
| Treating heading == track == course (no wind model) | Simpler math, faster v1 | Renaming/refactoring everywhere if wind/drift is ever added | Acceptable for v1 as long as fields are named distinctly (Pitfall 3) so it's a config choice, not a hardcoded assumption |
| Hardcoded single magnetic-variation constant for EGGW | Avoids building a magnetic model | Wrong the moment a second airport/region is added | Fine for v1 (single fixed airport), never acceptable if multi-airport is added without revisiting |
| Current-instant-only separation checking | Fastest to implement, easy to demo | Undermines "sim never lies about separation" promise, false-negative timing risk | Never acceptable as the final v1 separation logic; acceptable only as an interim step before trajectory projection ships in the same phase |
| Unstructured nested-loop pairwise conflict check inline in tick update | Fast to write | Hard to unit test, hard to extend to spatial partitioning later, double-count risk | Acceptable only if isolated into its own testable function even while still O(n²) |
| Click hit-testing against exact rendered symbol bounds | Matches rendering code exactly, less code | Frustrating, error-prone selection, especially under time pressure | Never acceptable even in v1 — the fix (padded hit-region) is nearly as cheap as the shortcut |
| Independent (uncoupled) climb/descent/speed scalars per aircraft type | Fast to author aircraft profiles | Physically-incoherent instructions accepted, no real energy-management gameplay | Acceptable for a throwaway prototype only; needs at least coarse coupling before v1 ships since energy management is core to approach sequencing gameplay |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|-----------------|
| O(n²) pairwise separation checks | None at v1 scale (few aircraft) | Isolate into a pure, swappable function now; add spatial partitioning only if a future randomized/high-density traffic milestone needs it | Not a concern at v1's scripted-scenario scale; would matter in the tens-of-aircraft range if traffic generation is ever added |
| Uncapped catch-up ticks in the fixed-timestep accumulator | Occasional freeze/jump after a slow frame or window drag | Cap max ticks-per-frame (Pitfall 1) | Any slow frame, at any traffic scale — this is a correctness bug, not a scale threshold |
| Recomputing great-circle geodesics every render frame instead of every sim tick | Unnecessary CPU use in the render loop | Compute geodesic-derived quantities (bearing, distance) once per sim tick, not once per render frame at 60fps | Noticeable once aircraft count or geodesic-per-pair calculations (e.g. trajectory projection for every pair) scale up |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-------------------|
| Hit-testing exact symbol bounds for click selection | Frustrating mis-selects, wrong-aircraft instructions | Padded, nearest-match hit-regions (Pitfall 10) |
| Separation alerts with no hysteresis (flicker on/off every tick as projection recalculates) | Distracting, erodes trust in the alert system | Add a small time-based debounce/hysteresis so an alert doesn't flicker on borderline cases |
| Radar display and separation math disagreeing visually (Pitfall 5) | Undermines the "sim never lies about separation" trust the whole product depends on | Shared projection/geodesic code path between display and separation logic |
| No visible distinction between "vectors," "cleared direct," and "established on approach" state | Player can't tell what mode an aircraft is in, leading to conflicting instructions | Surface the guidance-mode state (Pitfall 6) in the datablock or selection panel, not just internally |

## "Looks Done But Isn't" Checklist

- [ ] **Fixed-timestep sim loop:** Often missing a max-ticks-per-frame cap — verify by deliberately stalling a frame and confirming the sim slows rather than freezes/jumps (Pitfall 1)
- [ ] **Great-circle navigation math:** Often missing a clear true-vs-magnetic convention — verify every published procedure course and every computed bearing is tagged with which convention it's in, and that variation is applied at exactly one point (Pitfall 3, 4)
- [ ] **Radar canvas projection:** Often missing latitude cosine correction — verify range rings render as circles, not ellipses, and that on-screen bearing between two points matches the great-circle bearing used in separation math (Pitfall 5)
- [ ] **ILS capture logic:** Often missing an intercept-angle bound and a clear armed/captured state — verify an aircraft vectored to intercept from a poor angle (e.g. >45°) behaves sensibly rather than oscillating, and that reassigning a heading while established drops localizer state cleanly (Pitfall 6)
- [ ] **Separation/conflict detection:** Often missing trajectory projection (current-instant only) — verify a fast-closing pair triggers an alert before minima are actually violated, with enough lead time to act (Pitfall 8)
- [ ] **Click selection:** Often missing a padded hit-region — verify selecting a specific aircraft among 2-3 closely spaced symbols is reliable, not a matter of pixel-precision luck (Pitfall 10)

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|-----------------|-------------------|
| Spiral of death (uncapped accumulator) | LOW | Add a max-ticks-per-frame clamp; no data model changes needed |
| Heading/course/bearing conflation | MEDIUM | Rename fields and thread the correct one through instruction-handling and navdata code; contained if caught before wind/drift modeling is added |
| Magnetic/true mismatch | LOW-MEDIUM | Add a single variation constant applied at the true→magnetic boundary; low cost if caught before multiple display paths each apply their own inconsistent correction |
| Uncorrected radar projection | LOW | Add the cosine-correction factor to the existing projection function; contained to the rendering module if geodesic math was kept separate |
| Ambiguous ILS/procedure state | MEDIUM-HIGH | Refactor independent booleans into a single guidance-mode enum with explicit transitions; cost grows with how many places directly read/write the old flags |
| Current-instant-only separation checking | MEDIUM | Add short-look-ahead linear projection to the existing pairwise check function; low-medium if the check was already isolated (Pitfall 9) |
| Unpadded click hit-testing | LOW | Add a fixed-radius hit-region check ahead of/instead of exact-bounds testing |
| Uncoupled performance model | MEDIUM | Add coupling multipliers between descent/speed/climb per type; requires re-tuning existing profile data but not a data-model rewrite |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|-------------------|-----------------|
| Spiral of death / accumulator cap | Game-loop / sim-clock foundation phase | Stall a frame deliberately; confirm slowdown not freeze/jump |
| Frame-rate leakage into "decoupled" subsystems | Game-loop foundation phase; re-checked at every timer-driven UI phase | Vary render frame rate (or throttle window focus) and confirm sim-tick-driven behavior is unaffected |
| Heading/course/track/bearing conflation | Navdata/aircraft-state data model phase | Code review of field names; direct-to-fix instruction test with a fix not directly ahead |
| True/magnetic inconsistency | Navdata phase + ILS/procedure phase | Verify computed bearing and published procedure course agree to within a fraction of a degree at the runway threshold |
| Uncorrected lat/lon-to-pixel projection | Radar canvas rendering phase | Visual check: range rings are circles; on-screen distances match nm-scale conversions in both axes |
| Ambiguous ILS/procedure state transitions | ILS/procedure modeling phase | Explicit test: reassign heading to an established aircraft; vector an aircraft to intercept from a poor angle |
| Numerically-correct-but-wrong performance coupling | Aircraft performance-model phase | Playtest a full descend-and-slow-down approach sequence, not just isolated parameter checks |
| Current-instant-only separation checking | Separation/conflict-detection phase | Scripted scenario with a fast-closing pair; confirm alert fires with lead time before minima violation |
| Unstructured O(n²) checks | Separation/conflict-detection phase | Unit tests against the isolated pairwise-check function with known position sets |
| Unpadded click hit-testing | Click+panel input phase | Manual test: select among 2-3 closely spaced aircraft symbols repeatedly |
| Fidelity-before-core-loop scope creep | Roadmap sequencing (cross-phase) | Roadmap places a thin end-to-end vertical slice (one departure, one arrival, current-instant separation, one performance profile) before any pure-fidelity phase |

## Sources

- [Fix Your Timestep! — Gaffer On Games](https://gafferongames.com/post/fix_your_timestep/)
- [thoughts on fix-your-timestep and the spiral of death — GameDev.net](https://www.gamedev.net/blogs/entry/2262574-thoughts-on-fix-your-timestep-and-the-spiral-of-death/)
- [pygame.time — pygame v2.6.0 documentation](https://www.pygame.org/docs/ref/time.html)
- [Heading, Track, Bearing, and Course Explained — airplaneacademy.com](https://airplaneacademy.com/heading-track-bearing-and-course-explained/)
- [Course (navigation) — Wikipedia](https://en.wikipedia.org/wiki/Course_(navigation))
- [FlightGear forum — Magnetic vs. True heading (autopilot vs. HUD), bug?](https://forum.flightgear.org/viewtopic.php?f=14&t=22019)
- [North: Magnetic vs True Headings — X-Plane.Org Forum](https://forums.x-plane.org/forums/topic/174424-north-magnetic-vs-true-headings/)
- [Equirectangular projection — Wikipedia](https://en.wikipedia.org/wiki/Equirectangular_projection)
- [Equirectangular projection/Maps and Distortion — Wikiversity](https://en.wikiversity.org/wiki/Equirectangular_projection/Maps_and_Distortion)
- [ILS Nuances — IFR Magazine](https://ifr-magazine.com/technique/ils-nuances/)
- [Intercepting the ILS — PPRuNe Forums](https://www.pprune.org/archive/index.php/t-362575.html)
- [Short Term Conflict Alert (STCA) — SKYbrary Aviation Safety](https://skybrary.aero/articles/short-term-conflict-alert-stca)
- [Short Term Conflict Alert (STCA) optimization for TMAs — SKYbrary](https://skybrary.aero/articles/short-term-conflict-alert-stca-optimization-tmas)
- [Short-term conflict alert — Wikipedia](https://en.wikipedia.org/wiki/Short-term_conflict_alert)
- [Broad Phase Collision Detection Using Spatial Partitioning — Build New Games](http://buildnewgames.com/broad-phase-collision-detection/)
- [Video Game Physics Tutorial Part II: Collision Detection for Solid Objects — Toptal](https://www.toptal.com/developers/game/video-game-physics-part-ii-collision-detection-for-solid-objects)
- [Touch Targets on Touchscreens — NN/g](https://www.nngroup.com/articles/touch-target-size/)
- [Understanding Success Criterion 2.5.8: Target Size (Minimum) — W3C WAI](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)
- [Energy Management During Approach — SKYbrary Aviation Safety](https://skybrary.aero/articles/energy-management-during-approach)
- [Time and Energy Management During Descent and Approach: Batch Simulation Study — Journal of Aircraft](https://arc.aiaa.org/doi/10.2514/1.C032668)

---
*Pitfalls research for: Single-airport ATC simulator (Python/Pygame, fixed-timestep sim, EGGW/26)*
*Researched: 2026-07-03*
