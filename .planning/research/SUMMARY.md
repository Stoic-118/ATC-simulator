# Project Research Summary

**Project:** ATC Simulator (single-airport, EGGW runway 26, native Python/Pygame desktop app)
**Domain:** ATC / flight simulator — single-controller trainer-style desktop game
**Researched:** 2026-07-03
**Confidence:** MEDIUM

## Executive Summary

This is a single-airport, single-controller ATC simulator built as a native Python + Pygame desktop app, and the research converges strongly on one central architectural bet: a fixed-timestep sim clock (1-4Hz) fully decoupled from a 60fps render loop, with a hard rule that the sim core never imports Pygame and the render layer never mutates sim state. Every other recommendation — stack choice, feature scope, component structure, and the majority of the pitfalls — either supports or depends on this boundary being right from the very first phase. The stack (pygame-ce, pygame_gui, Pydantic v2, geographiclib) is well-matched to this architecture: geographiclib in particular is chosen specifically to avoid PyInstaller packaging pain later, and Pydantic is used for validated navdata/scenario boundaries while hot-path per-tick objects stay lightweight.

The recommended approach is a Walking Skeleton build order: get a fixed-tick sim clock driving one hardcoded aircraft on a bare radar canvas working end-to-end first, then layer in real navdata/projection, performance modeling + flight-phase FSM, procedure-following, instruction handling (click+panel), separation/conflict alerting, scenario loading, and phraseology — in that order — before any fidelity or visual polish work. Feature-wise, the v1 table stakes (radar canvas with datablocks/trail/rings/vector, click+panel instructions, instruction/readback log, current-state separation alerting, scripted scenarios) are validated as genuinely minimal against real ATC tools (EuroScope, openScope, Tower!3D) — nothing here is over-scoped, and the anti-features list (voice, multi-sector handoff, procedural traffic, live AIRAC) is confirmed as correctly excluded rather than merely deferred.

The biggest risks are not stack or performance risks (at v1's traffic scale, naive O(n^2) separation checks are computationally free) — they are correctness and sequencing risks: getting the timestep accumulator's step-cap wrong (spiral of death), conflating heading/course/track/bearing or true/magnetic conventions in the data model, shipping a radar projection that visually disagrees with the separation math it's supposed to represent, leaving ILS/procedure guidance state ambiguous between vectors and captured, and — the meta-risk that subsumes many of the others — investing in fidelity/polish before the thin end-to-end instruction loop (one departure, one arrival, one performance profile, current-instant separation) is actually playable. All of these have concrete, cheap mitigations if addressed in the phase where the underlying data model or architecture is first established; several become expensive refactors if deferred.

## Key Findings

### Recommended Stack

Python 3.12+ with pygame-ce (not classic pygame) for rendering/input/audio, pygame_gui for themed panel widgets (flight-strip bay, comms log, frequency box), Pydantic v2 for validated aircraft/procedure/navdata/scenario models, and geographiclib for all great-circle geodesy. The sim/render split is implemented as a plain single-threaded fixed-timestep accumulator loop — no asyncio, no threading — since Python's GIL means threading buys no CPU-bound benefit and only adds race-condition risk to the exact code (separation checks) that must be trustworthy. geographiclib is explicitly preferred over pyproj because pyproj's native C dependency and bundled data files are a documented PyInstaller-packaging failure mode, and this project has an explicit later packaging phase.

**Core technologies:**
- pygame-ce 2.5.7 — window/rendering/input/audio — actively maintained fork, drop-in API superset of classic pygame, no reason to pick the stalled original
- pygame_gui 0.6.14 — themed UI widgets (strip bay, comms log, frequency box) — purpose-built for the pygame main-loop event/update/draw cycle, avoids a second UI/GPU stack (unlike imgui-bundle)
- Pydantic v2 (~2.13.x) — validated data models for aircraft, procedures, navdata, scenario files — Rust core is fast enough that per-load validation cost is irrelevant; validate at boundaries (load time), not every tick
- geographiclib 2.1 — great-circle distance/bearing/geodesic math — pure Python, zero native deps, avoids pyproj's PyInstaller packaging pitfalls
- Fixed-timestep accumulator pattern (Gaffer's "Fix Your Timestep!") — decouples 1-4Hz sim tick from 60fps render loop; this is a pattern to implement directly, not a library

### Expected Features

The v1 feature set matches PROJECT.md's active scope closely and is validated as genuinely minimal (not arbitrarily cut) against EuroScope, openScope, and Tower!3D precedent. The single genuine differentiator versus surveyed hobby tools is the two-party instruction/readback text log formatted per ICAO convention — none of the surveyed competitors implement this as a core mechanic.

**Must have (table stakes):**
- Radar/plan-view display: datablocks, history trail dots, range rings, heading vector line
- Click-to-select + command-panel instruction input (heading, altitude, speed, direct-to-fix, cleared approach/takeoff/landing)
- Text-rendered instruction + simulated pilot readback log (ICAO instruction-then-identify format)
- Current-state separation/conflict alerting (1000ft vertical / 5nm horizontal), visual + optional audio, not auto-enforced
- Scripted scenario file (hand-authored spawn list), validated against Pydantic models

**Should have (competitive, v1.x/v2):**
- Predictive/lookahead conflict alerting (true trajectory-based STCA) — build only after current-state checking is proven
- Typed shorthand command entry alongside click+panel — requires the instruction model to already be decoupled from the panel UI
- Go-arounds/missed approaches — requires a solid nominal approach state machine first

**Defer (v2+):**
- VFR traffic, multiple runways/wind-driven config, wake turbulence categories, digital flight-strip bay, procedural traffic generator
- Permanently excluded: voice recognition (confirmed low realism payoff per Tower!3D reviews), multi-sector handoff/multiplayer (no use case with one combined controller position)

### Architecture Approach

The system is layered into an input/instruction layer, a Pygame-free sim core (clock, aircraft state/FSM, navdata/procedure store, separation detector), and a Pygame-only presentation layer — with a strict one-way data flow: instructions are queued and applied atomically at tick boundaries, state flows one-way into rendering, and the renderer never mutates sim state. This boundary is what makes separation logic testable headless with pytest, which matters directly for the project's "never lies about separation" bar.

**Major components:**
1. Sim clock / tick engine — fixed-timestep accumulator, owns simulated time, enables trivial time acceleration later
2. Aircraft state model — Pydantic/dataclass + explicit `Phase` FSM + kinematics update, exposes `assign_heading()`-style setters only
3. Navdata/procedure store — read-only reference data (runway, fixes, SID/STAR, ILS) loaded once at startup
4. Separation/conflict detector (STCA) — standalone per-tick pairwise function, naive O(n^2) is fine at this scale, isolated for testability
5. Radar rendering + input layers — pure read-only render of current state at 60fps; input translates events into queued instruction intents, never mutates state directly

Recommended build order (Walking Skeleton): sim clock + one hardcoded aircraft + bare radar canvas -> real navdata/projection -> performance model + phase FSM -> procedure-following -> instruction handling with vectoring-override layer -> separation detection -> scenario loader -> phraseology/readback -> polish.

### Critical Pitfalls

1. **Uncapped fixed-timestep accumulator (spiral of death)** — clamp max sim ticks processed per render frame; verify by deliberately stalling a frame and confirming graceful slowdown, not freeze/jump. Must be right from the very first game-loop phase.
2. **Heading/course/track/bearing conflation, and true-vs-magnetic inconsistency** — name fields distinctly (`heading_deg`, `course_deg`, `bearing_to_fix_deg`) and apply magnetic variation at exactly one well-defined boundary, even though v1 has no wind model. Cheap to get right in the navdata/data-model phase, expensive to unwind once instruction-handling and separation logic both depend on ambiguous fields.
3. **Radar projection without cosine correction** — an uncorrected lat/lon-to-pixel projection renders range rings as ellipses and can visually disagree with the separation math, undermining the "sim never lies" trust the whole product depends on. Use the same geodesic library for both display projection and separation math.
4. **Ambiguous ILS/procedure guidance state (vectors vs. captured)** — model lateral guidance mode as a single enum with explicit transitions, not independent booleans, so a heading instruction issued while localizer-captured has a well-defined, tested outcome.
5. **Fidelity/polish investment before the thin end-to-end instruction loop works** — the biggest scope-creep risk given how deep and seductive the domain (SID/STAR/ILS/performance modeling) is; sequence a minimal one-departure/one-arrival/current-instant-separation vertical slice before any pure-fidelity phase.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Walking Skeleton (sim clock + render loop foundation)
**Rationale:** This is the single riskiest architectural bet (fixed-tick/render decoupling) and must be proven correct before any domain logic is built on top of it; retrofitting it later is far more expensive than starting with it.
**Delivers:** A fixed-timestep accumulator sim clock with a max-ticks-per-frame cap, driving one hardcoded aircraft with simple linear motion, rendered as a dot/vector on a bare Pygame canvas. No real navdata, no kinematics beyond linear motion.
**Addresses:** Foundational requirement underlying every table-stakes feature (radar canvas, everything downstream)
**Avoids:** Pitfall 1 (spiral of death) and Pitfall 2 (frame-rate leakage) — verify by deliberately stalling a frame and confirming graceful degradation

### Phase 2: Navdata + Coordinate Projection
**Rationale:** The renderer already exists from Phase 1 and now needs real geometry; this doesn't yet require procedures or performance modeling, keeping the phase narrowly scoped.
**Delivers:** EGGW navdata (runway 26, fixes, one SID, one STAR) as Pydantic models; lat/lon-to-screen projection with cosine correction, shared between display and (future) separation math.
**Uses:** geographiclib, Pydantic v2 (models.py)
**Implements:** navdata/ module, geo.py projection utilities
**Avoids:** Pitfall 3 (heading/course/bearing field naming), Pitfall 4 (true/magnetic convention), Pitfall 5 (uncorrected projection) — all three are cheapest to get right exactly here

### Phase 3: Aircraft Performance Model + Flight-Phase FSM
**Rationale:** Sequenced after real navdata exists so performance/phase logic has real geometry to act on; before procedure-following since procedures need a working kinematics/phase model.
**Delivers:** Per-type performance profiles (climb/descent/turn rate, with coarse coupling between descent rate and commanded deceleration) and an explicit `Phase` enum with a legal-transitions table.
**Addresses:** Foundation for departure/arrival flows (FEATURES.md P1)
**Avoids:** Pitfall 7 (numerically-correct-but-experientially-wrong performance coupling), Anti-Pattern 2 (implicit phase via scattered thresholds)

### Phase 4: Procedure-Following (SID/STAR)
**Rationale:** Needs the performance/phase model from Phase 3 to act on; introduces the "derive target from procedure leg" pattern that vectoring will later override rather than replace.
**Delivers:** Aircraft following the one SID/STAR via leg-index tracking and restriction-following.
**Implements:** Procedure-following-with-vectoring-override-layer pattern (Architecture Pattern 3)

### Phase 5: Instruction Handling (Click + Panel)
**Rationale:** Only now does the player get control — sequenced after procedures because vectoring is defined as an override on top of procedure state; building it earlier would mean revisiting it once procedures exist.
**Delivers:** Click-to-select with padded hit-regions, command panel (heading/altitude/speed/direct-to/cleared-approach/cleared-for-takeoff-landing), tick-gated instruction queue.
**Addresses:** Table-stakes click+panel instruction input (FEATURES.md P1)
**Avoids:** Pitfall 10 (unpadded click hit-testing), Anti-Pattern 3 (renderer mutating state directly)

### Phase 6: Separation/Conflict Detection (STCA-style)
**Rationale:** Deliberately sequenced after instruction handling — testing separation logic is far more meaningful once a human can create a conflict via real instructions, not only via the scenario file. This is the single most complexity-loaded table-stakes feature and deserves its own phase.
**Delivers:** Isolated, unit-testable pairwise separation-check function with current-instant + short-linear-trajectory lookahead, visual + optional audio alerting.
**Addresses:** Core "never lies about separation" mechanic (FEATURES.md P1, HIGH complexity)
**Avoids:** Pitfall 8 (current-instant-only checking undermines the trust promise), Pitfall 9 (unstructured inline pairwise loop)

### Phase 7: Scripted Scenario Loader
**Rationale:** Formalized last among core systems since it's "just" a controlled, repeatable way to spawn more of what already works — single-aircraft behavior, instructions, and separation must all be proven first.
**Delivers:** Scenario file format (Pydantic-validated), sim-time-ordered spawn-event queue consumed by the sim clock.
**Addresses:** Scripted scenario table stakes (FEATURES.md P1)

### Phase 8: Phraseology/Readback Log + Polish
**Rationale:** Purely observational, zero effect on simulation state — safe and low-risk to add last. Cosmetic/UX polish (datablocks, trails, alert banner styling) follows once the sim core is fully functional.
**Delivers:** ICAO-formatted instruction + pilot-readback text log; visual polish pass.
**Addresses:** Instruction/readback log table stakes (FEATURES.md P1)

### Phase Ordering Rationale

- Dependencies discovered in FEATURES.md and ARCHITECTURE.md agree exactly: radar rendering requires the sim clock/aircraft state model; separation alerting requires the same aircraft state model pairwise; procedure-following requires a working performance/phase model; vectoring is an override on procedures, so procedures must exist first.
- This ordering directly implements the Walking Skeleton pattern recommended in ARCHITECTURE.md: front-load the two riskiest bets (timestep/render decoupling, procedure-vs-vector reconciliation) and defer the lowest-risk additive pieces (phraseology text, visual polish) to the end.
- This ordering is also PITFALLS.md's own top recommendation (Pitfall 11): get a thin end-to-end loop (one departure, one arrival, current-instant separation, one performance profile) working before any fidelity/polish investment, rather than perfecting any one subsystem in isolation first.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 4 (Procedure-following) / Phase 6 (Separation detection):** ILS localizer/glideslope capture-angle logic and trajectory-projection lookahead windows are domain-specific enough (real-world STCA/ILS nuance) to warrant a `--research-phase` pass validating exact intercept-angle bounds and lookahead-window tuning against SKYbrary/FAA sources already surfaced in PITFALLS.md.
- **Phase 5 (Instruction handling):** Hit-region sizing and ambiguity resolution (nearest-match vs. z-order) benefit from a quick UX-pattern check against real radar-tool conventions before implementation.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Walking skeleton):** Fixed-timestep accumulator is a canonical, extremely well-documented game-loop pattern (Gaffer On Games) — implement directly from ARCHITECTURE.md's example.
- **Phase 2 (Navdata/projection), Phase 3 (Performance/FSM), Phase 7 (Scenario loader), Phase 8 (Phraseology/polish):** All have clear, well-established patterns already documented in this research (Pydantic modeling conventions, enum-driven FSM, cosine-corrected equirectangular projection, ICAO phraseology format) — no additional research needed before planning.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | Directional calls (pygame-ce over pygame, geographiclib over pyproj, single-threaded accumulator over asyncio/threading) are HIGH-confidence and cross-checked across independent sources; exact point-release version numbers are MEDIUM and should be re-verified against PyPI before pinning dependencies. |
| Features | MEDIUM | Cross-checked against official docs (EuroScope, openScope, FAA JO 7110.65, SKYbrary/EUROCONTROL) for table-stakes and STCA concepts; competitor comparisons (Tower!3D) rely on lower-reliability marketing/review sources. |
| Architecture | MEDIUM | General game-loop/FSM/STCA/Walking-Skeleton patterns are HIGH-confidence, well-established, and cross-referenced; ATC-simulator-specific internal structure (e.g., openScope's actual class design) could not be verified at source-code level and is directional inspiration, not a confirmed reference implementation. |
| Pitfalls | MEDIUM | Generic game-loop, navigation-terminology, ILS, STCA, and UI-hit-target claims are cross-checked across multiple web sources; domain-specific manifestation in this exact architecture is HIGH-confidence synthesis but not independently source-verified. |

**Overall confidence:** MEDIUM

### Gaps to Address

- Exact current PyPI version numbers for pygame-ce, pygame_gui, pydantic, and geographiclib were not verified against a live registry this session — re-check before pinning `requirements.txt`/`pyproject.toml`.
- No direct source-code read of a reference ATC simulator (e.g., openScope) was possible — internal architectural recommendations are synthesized from general domain knowledge and should be treated as a strong starting point, not a verified port of an existing implementation.
- Exact ILS intercept-angle bounds and trajectory-projection lookahead windows (60-120s suggested) are sourced from general aviation/STCA references (SKYbrary, EUROCONTROL guidelines) rather than validated against this project's specific EGGW/26 geometry — flag for a research pass during Phase 4/6 planning.
- Magnetic variation constant for EGGW is time-varying in reality (~1-2 degrees W currently); the research recommends a single hardcoded constant for v1, which is a deliberate, documented simplification rather than a gap, but should be re-confirmed against current EGGW charts at implementation time.

## Sources

### Primary (HIGH confidence)
- None (no Context7/MCP official-docs provider was available this research session — all sources below were gathered via WebSearch/WebFetch)

### Secondary (MEDIUM confidence)
- Fix Your Timestep! — Gaffer On Games (https://gafferongames.com/post/fix_your_timestep/) — canonical fixed-timestep accumulator pattern
- Short Term Conflict Alert (STCA) — SKYbrary Aviation Safety (https://skybrary.aero/articles/short-term-conflict-alert-stca) / EUROCONTROL STCA Guidelines (https://www.eurocontrol.int/sites/default/files/2019-09/eurocontrol-guidelines-159-part-i-1.0.pdf) — separation-alerting concept and real-world tradeoffs
- FAA JO 7110.65 Air Traffic Control Order (https://www.faa.gov/documentlibrary/media/order/atc.pdf) — datablock content, minima conventions
- EuroScope docs (https://www.euroscope.hu/wp/display-settings/), openScope docs (https://github.com/openscope/openscope/blob/develop/documentation/aircraft-commands.md) — competitor feature/UX conventions
- pygame-ce GitHub/PyPI (https://github.com/pygame-community/pygame-ce), pygame-gui PyPI (https://pypi.org/project/pygame-gui/), Pydantic changelog (https://docs.pydantic.dev/latest/changelog/), geographiclib PyPI (https://pypi.org/project/geographiclib/) — stack maintenance/version status
- pyinstaller/pyinstaller#8415 (https://github.com/pyinstaller/pyinstaller/issues/8415), pyproj4/pyproj discussion #1391 (https://github.com/pyproj4/pyproj/discussions/1391) — pyproj packaging pitfalls justifying geographiclib choice

### Tertiary (LOW confidence)
- Tower!3D Pro Steam page / FSNews review (https://fsnews.eu/review-tower3d-pro/) — competitor UX claims, single-review synthesis
- FlightGear/X-Plane forum threads on true vs. magnetic heading bugs (https://forum.flightgear.org/viewtopic.php?f=14&t=22019) — anecdotal but consistent cross-source corroboration of Pitfall 4
- Academic ATC-training scenario research abstracts (ResearchGate, arXiv) — synthesized from search snippets, not full-text verified

---
*Research completed: 2026-07-03*
*Ready for roadmap: yes*
