# Feature Research

**Domain:** ATC simulator / trainer software (single-airport, single-controller scope)
**Researched:** 2026-07-03
**Confidence:** MEDIUM (cross-checked across official docs — EuroScope, openScope, FAA JO 7110.65, SKYbrary/EUROCONTROL — plus community/product sources of lower individual reliability)

## Feature Landscape

### Table Stakes (Users Expect These)

Features every credible ATC sim/trainer has. Missing these makes it not read as "an ATC sim" at all.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Radar/plan-view display with datablocks (callsign, altitude, speed, assigned instructions) | Every real ATC display (FAA STARS/ERAM) and every hobby client (EuroScope, VRC, openScope) shows this as the minimum unit of information per aircraft. FAA order 7110.65 specifies flight ID + altitude as the *minimum* datablock content. | MEDIUM | v1 scope already includes this (callsign/altitude/speed/assigned info per PROJECT.md). Match real convention: a "full" datablock (leader line, position symbol, velocity vector, full data) vs a stripped "limited" datablock is the standard distinction — v1 only needs full datablocks since there's one controller and no handoff-driven full/limited toggle. |
| History trail dots behind each target | Standard on every radar client (EuroScope: configurable dot count; real radar: dots represent past position samples, historically ~30s apart). Without it, turn rate and closure rate are unreadable and separation judgement becomes guesswork. | LOW | Already in v1 scope. Keep it simple: fixed N most-recent tick positions rendered as fading dots — no need to match real ATC's exact 30s sampling since the project's sim tick is faster. |
| Range rings / distance reference on the scope | Present in EuroScope (`.showantenna`), STARS, and every plan-view radar tool as a way to eyeball distance without measuring. Needed for the player to self-judge 5nm horizontal separation. | LOW | Already in v1 scope. Concentric rings from a fixed reference point (airport) at fixed nm intervals is sufficient; no need for movable/rotatable rings. |
| Heading vector / leading line on target | Real FDB symbology includes a velocity vector line; without it, a controller can't predict where an aircraft is heading next tick, which is essential for both instruction-giving and conflict anticipation. | LOW | Already in v1 scope as "heading vector line." Matches real full-data-block convention directly. |
| Text-rendered instruction + readback log | Every real ATC interaction is instruction → readback, and this is the *core value proposition* per PROJECT.md ("never lies about separation" implies instructions are auditable). ICAO Doc 4444 defines exactly which instruction types require a readback (route clearances, runway ops, altimeter, squawk, level/heading/speed changes, transition level). | MEDIUM | Already in v1 scope. Implementation detail worth adopting from ICAO structure: log entries should read as `CALLSIGN, INSTRUCTION` from controller and `INSTRUCTION READBACK, CALLSIGN` from pilot (real-world order swaps — pilots restate the instruction *then* identify themselves) — this single formatting detail is what makes the log "feel" authentic vs a generic message list. |
| Click-to-select + instruction-issuing UI (panel or command bar) | Universal across the space — every tool differs only in *how* instructions are entered (see Differentiators/comparison below), never *whether* a discrete select→instruct interaction model exists. | MEDIUM | Already in v1 scope (click+panel, mouse-first). This is a legitimate table-stakes interaction model, not a lesser substitute for typed shorthand — Tower!3D (the most commercial/polished product in the space) is mouse/console-first, not command-line-first. |
| Conflict/separation alerting when minima are breached or about to be | This is the entire mechanic that makes an ATC sim a *game* rather than a flight-path editor. EUROCONTROL/SKYbrary's STCA concept (visual cue + audible alarm, short lookahead, decision-support not auto-block) is the direct real-world analog to the "surfaced as alerts, not auto-enforced" v1 requirement. | HIGH | Already in v1 scope. See Differentiators section for depth options; v1 needs only current-state (not predictive lookahead) checking to be credible — see MVP Definition. |
| Standard vertical/horizontal separation minima logic (1000ft / 5nm en route-terminal analog) | This is the substance behind every alert — without correct minima, "the sim lies about separation," which PROJECT.md explicitly rules out as the one thing v1 must never do. | MEDIUM | Already in v1 scope. Real STCA implementations vary in their exact minima and lookahead by facility — the project's PROJECT.md-specified simplified minima (1000ft below FL290, 5nm) are a defensible fixed simplification, not an inaccuracy, as long as it's documented as terminal-airspace-style minima rather than claimed as universal. |
| Deterministic/scripted scenario definition (spawn list: aircraft, type, time, flight plan) | Every ATC trainer with a "scenario" concept (openScope's spawnPatterns, RAMS-style `.out` initial-condition files, academic ATC-training tools) treats a hand-authored or generated list of spawn events as the baseline unit of a session — there's no product in this space that doesn't have *some* form of this. | MEDIUM | Already in v1 scope, explicitly scripted-only (no procedural gen) for v1 — this matches real ATC-training practice too: professional trainers still author scenarios by hand/manually-translated briefing before any procedural tooling gets involved. |
| Aircraft symbol/target rendering distinct per state (airborne vs on ground, e.g.) | Baseline visual legibility requirement across all radar tools; EuroScope even differentiates symbol by transponder mode. | LOW | Not separately called out in PROJECT.md but implied by "vector-style radar display" — cheap to add, worth doing (e.g. different marker or dimming for ground/taxi phase vs airborne). |

### Differentiators (Competitive Advantage / Depth, appropriate for v2+)

Features that go beyond baseline and could set this project apart — but every one below is legitimately deferrable past v1 without the sim "feeling incomplete."

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Typed shorthand command language (in addition to click+panel) | EuroScope and openScope's power-user base overwhelmingly prefers typed shorthand (alias expansion, chainable per-callsign commands like `AAL123 fh 270 c 30 + 250`) because it's faster once memorized. PROJECT.md's Key Decisions table already flags this as "could be added later as an accelerator." | MEDIUM | Should be architected so instructions flow through one internal command object regardless of input surface (click+panel now, optional typed parser later) — this is a real dependency to flag for the roadmap: don't let the click+panel UI hard-couple instruction semantics to widget state. |
| Predictive/lookahead conflict prediction (true STCA, e.g. 2-minute trajectory projection) | Real STCA predicts *future* infringement from current trajectories, not just current-state violations — this is meaningfully harder (requires trajectory extrapolation, closest-point-of-approach math) and is the actual "STCA" as EUROCONTROL defines it, vs the v1 "alert once minima are already breached or about to be" simplification. | HIGH | Good v1.x/v2 add: once current-state separation checking (table stakes) is solid and tested, extending to velocity-vector-based trajectory prediction is a natural, isolated next step and a strong "feels like a real STCA" differentiator. |
| Digital flight-strip bay | Real-world controllers (and Tower!3D, vStrips/vNAS) use flight strips as a secondary, spatially-organized reference distinct from the radar picture — bays ordered by altitude (approach) or by ground/runway/air (tower). PROJECT.md's stack context even mentions a "flight strip bay" as a panel concept. | MEDIUM-HIGH | Adds real depth/authenticity but is a second parallel UI system on top of the radar+panel — reasonable to defer past the v1 "one launch, one landing" loop; correctly listed as future rather than core-loop-blocking. |
| Voice/speech command input | Tower!3D Pro's marquee differentiator, but its own reviews note the phrasing has to be unnaturally exact, undermining the realism it's meant to add. | HIGH | Confirmed appropriate to exclude — see Anti-Features/Out-of-Scope. High complexity for low realism payoff given PROJECT.md's explicit "text-rendered phraseology only" decision. |
| Wake turbulence / aircraft separation categories | Real controllers apply different minima by weight category (Light/Medium/Heavy/Super) — adds real depth to separation logic once the base 1000ft/5nm loop is proven. | MEDIUM | Explicitly deferred in PROJECT.md Out of Scope; correctly sequenced after the core separation-alert loop is validated, since it's an additive rule layer, not a new subsystem. |
| Multiple runway configurations / wind-driven runway selection | Adds real operational depth (a controller choosing configuration based on wind) but multiplies procedure/ILS surface area. | HIGH | Correctly deferred per PROJECT.md; natural v2 differentiator once one-direction ILS/SID/STAR logic is fully solid. |
| Procedural/randomized traffic generator | Real training tools are moving toward this (node-based event scenario editors in academic ATC-training research) as scenario authoring scales, but it fights the v1 need for deterministic, debuggable runs. | MEDIUM-HIGH | Correctly deferred; a good v2 differentiator once the scripted-scenario format (table stakes now) is stable enough to generate *into* programmatically — see Feature Dependencies. |
| Go-arounds / missed approaches | Adds a real recovery branch that every commercial ATC game and real-world controller deals with regularly. | MEDIUM | Correctly deferred; depends on the approach state machine being solid first (see dependency chain). |

### Anti-Features (Confirmed Safe Exclusions for v1 — matches PROJECT.md Out of Scope)

These are directly cross-checked against how existing ATC products actually implement (or over-invest in) them, confirming the project's Out of Scope list is well-reasoned, not just convenient.

| Feature | Why It Might Seem Necessary | Why Problematic for v1 | Alternative / Confirmation |
|---------|------------------------------|-------------------------|-----------------------------|
| Voice recognition / speech command input | Tower!3D Pro's headline feature — "feels like real ATC" | Confirmed by product reviews to require unnaturally exact phrasing, adding friction rather than realism; enormous complexity (speech-to-intent parsing) for a mouse-first project. PROJECT.md already commits to text-only phraseology. | Text-rendered phraseology log (already in v1 scope) delivers the "readback" mechanic without the recognition-accuracy problem. |
| Multi-sector handoffs / frequency transfer | Real ATC (and EuroScope/VATSIM, built around exactly this) revolves around handoff between positions/sectors | Confirmed meaningless with a single combined Approach+Tower position and one airport's local airspace — there is no second controller to hand off to. EuroScope's `.qx` handoff command and VATSIM's whole multi-position model exist to support a use case (network of controllers) this project doesn't have. | None needed for v1; if the project ever adds a second position (e.g., separate ground control) this would become a real, isolated future feature — not a v1 gap. |
| Full flight-strip bay system | Real controllers and commercial sims (Tower!3D, vStrips) use strips as a first-class tool | Adds a second parallel UI/interaction surface (strip creation, movement between bays, strip-state sync with aircraft state) before the core click+panel+radar loop is proven. | Datablock + instruction log already carries the same "what's been cleared" information for a single controller working one small session; revisit as a differentiator once core loop ships. |
| True predictive STCA (trajectory/closest-point-of-approach lookahead) | This is literally what "STCA" means in EUROCONTROL's own definition | Materially harder than current-state separation checking (requires trajectory extrapolation math); v1's bar is "the sim never lies about separation," which current-state checking already satisfies. | Ship current-state 1000ft/5nm checking for v1; layer in lookahead prediction later as a differentiator (see above). |
| Randomized/procedural traffic generation | Feels more "replayable" | Undermines the deterministic, debuggable runs the project needs while separation/instruction logic is still being validated — confirmed as the correct tradeoff by academic ATC-training practice, which still authors scenarios by hand even in professional trainer contexts. | Scripted scenario file (already in v1 scope). |
| Wake turbulence / separation categories | Real controllers apply this constantly | Adds a rule-layer (weight-category lookup + category-pair minima table) on top of unproven base separation logic | Fixed minima (1000ft/5nm) first; add category-based minima once the base checker is solid. |
| Real ground movement/taxi simulation | Feels more complete | No radar/ATC product in this research treats ground pathfinding as core to the *approach/tower radar* loop — it's a distinct subsystem (surface movement radar / ground radar plugins exist as *separate* EuroScope plugins, not core) | Timer-based taxi abstraction (already in v1 scope) is a legitimate, product-precedented simplification (even dedicated "ground radar" tooling in EuroScope is an add-on plugin, not baseline). |
| Live/real AIRAC navdata ingestion | Feels more "real" | Adds licensing/currency complexity with no gameplay-loop payoff; every hobby ATC tool (openScope, EuroScope sector files) ships with static/hand-maintained or infrequently-updated navdata, not live AIRAC feeds | Hand-authored, versioned navdata for one airport (already in v1 scope) matches how openScope and EuroScope sector files actually work in practice. |

## Feature Dependencies

```
Radar/plan-view rendering (datablocks, trail, range rings, heading vector)
    └──requires──> Aircraft state model (position, altitude, speed, heading per tick)
                       └──requires──> Sim clock (fixed-timestep tick loop)

Click+panel instruction input
    └──requires──> Aircraft selection (click hit-test on radar target)
    └──enhances──> Instruction/readback text log (every issued instruction is logged)

Instruction/readback text log
    └──requires──> Simulated pilot behavior (readback generation per instruction type)

Separation/conflict alerting (STCA-style)
    └──requires──> Aircraft state model (position/altitude per tick, pairwise)
    └──requires──> Separation minima logic (vertical 1000ft, horizontal 5nm)
    └──enhances──> Radar display (visual alert overlay) AND Instruction log (alert entries, optional)

Scripted scenario file
    └──requires──> Aircraft/procedure/navdata Pydantic models (to validate scenario entries against)
    └──enables──> Departure flow AND Arrival flow (scenario spawns feed both)

ILS approach clearance + capture (localizer/glideslope)
    └──requires──> SID/STAR + fix/navdata model
    └──requires──> Aircraft performance profile (descent rate, speed envelope)

Typed shorthand command language (v2 differentiator)
    └──requires──> Click+panel instruction model already decoupled into a shared "instruction" object (design for this now, build the parser later)

Predictive/trajectory-based STCA (v2 differentiator)
    └──requires──> Current-state separation checking (v1 table stakes) proven correct first

Procedural/randomized traffic generator (v2 differentiator)
    └──requires──> Scripted scenario file format (v1) — generator should emit into the same schema, not a parallel one

Wake turbulence / separation categories (v2 differentiator)
    └──requires──> Base separation minima logic (v1) — additive rule layer, not a rewrite

Digital flight-strip bay (v2 differentiator)
    └──enhances──> Instruction log / datablock (redundant "what's cleared" view, not a replacement)

Voice recognition (excluded) ──conflicts──> Text-rendered phraseology decision (PROJECT.md)
Multi-sector handoff (excluded) ──conflicts──> Single combined controller position (PROJECT.md)
```

### Dependency Notes

- **Radar rendering requires the sim clock/aircraft state model to exist first:** this confirms PROJECT.md's own phase-1 instinct (fixed-timestep sim clock driving aircraft state, decoupled from the 60fps render loop) — nothing on the radar display can be built meaningfully before there's a tick-driven aircraft state to render.
- **Separation alerting requires the same aircraft state model, pairwise, every tick:** this is the single most complexity-loaded table-stakes feature (HIGH complexity) — it should not be bundled into the same phase as basic radar rendering; it deserves its own phase once aircraft state and datablocks are working, per the project's "never lies about separation" bar.
- **Typed shorthand (v2) enhances but does not replace click+panel:** design the internal instruction representation (e.g., a single `Instruction` model with type + params) now so a text parser can target the same execution path later without refactoring the panel UI. This is a genuine now-vs-later architecture decision worth flagging to the roadmap, even though the typed parser itself is deferred.
- **Predictive STCA (v2) requires current-state checking (v1) to be validated first:** trajectory-based lookahead is a strict superset of complexity over current-state checking — building it before the simpler version is proven risks compounding two hard problems (physics prediction + alerting) at once.
- **Procedural traffic generation (v2) requires the scripted scenario schema (v1) to be stable:** a generator that emits directly into the same Pydantic scenario schema used for hand-authored files avoids a costly format migration later — worth noting in the scenario-file design even though generation itself is out of scope now.
- **Voice recognition and multi-sector handoff both conflict with explicit v1 architecture decisions** (text-only phraseology; single combined controller position) rather than merely being deferred — they're not just "later," they're incompatible with the stated v1 design unless those decisions are revisited.

## MVP Definition

### Launch With (v1)

Minimum viable product — matches PROJECT.md's Active requirements almost exactly; validated against ecosystem research as genuinely minimal, not arbitrarily cut.

- [ ] Radar canvas: range rings, sector lines, datablocks, heading vector, trail dots — the baseline "reads as ATC" visual (table stakes across every product researched)
- [ ] Click-to-select + command-panel instruction input (heading, altitude, speed, direct-to-fix, cleared approach, cleared takeoff/landing) — the only interaction model needed to prove the core loop; confirmed as a legitimate first-class model (Tower!3D precedent), not a lesser stand-in for typed shorthand
- [ ] Text-rendered instruction + pilot-readback log, formatted per ICAO's instruction-then-identify convention — this is the auditable "proof" that instructions happened and were understood
- [ ] Current-state separation checking (1000ft vertical / 5nm horizontal) with visual + (optional) audio alert — the STCA-inspired mechanic that makes this a controller *game*, simplified to current-state rather than predictive lookahead
- [ ] Scripted scenario file (hand-authored spawn list) — the only scenario-authoring approach mature ATC training tools actually rely on as a baseline, before any procedural layer

### Add After Validation (v1.x)

Features to add once the core "launch one, land one, never lie about separation" loop is working and stable.

- [ ] Predictive/lookahead conflict alerting (trajectory-based STCA) — trigger: once current-state alerting is proven correct across scripted test scenarios
- [ ] Typed shorthand command entry alongside click+panel — trigger: once the internal instruction model is stable enough that a parser can target it without UI rework
- [ ] Go-arounds/missed approaches — trigger: once the nominal approach state machine (capture→land) is solid

### Future Consideration (v2+)

Features to defer until the single-airport/single-runway/IFR-only core is fully validated.

- [ ] VFR traffic (circuits, request-based behavior) — why defer: PROJECT.md correctly identifies this as the single biggest scope addition (separate state machine + interaction model)
- [ ] Multiple runways/wind-driven configuration — why defer: multiplies ILS/procedure surface area before the one-direction case is proven
- [ ] Wake turbulence / separation categories — why defer: additive rule layer on top of unproven base separation logic
- [ ] Digital flight-strip bay — why defer: a second parallel UI system, valuable but not core-loop-blocking
- [ ] Procedural/randomized traffic generator — why defer: fights the deterministic-run requirement while core logic is still being debugged
- [ ] Voice recognition / real audio — why defer (permanently, per PROJECT.md): conflicts with the explicit text-only phraseology decision and adds high complexity for confirmed-low realism payoff (per Tower!3D reviews)
- [ ] Multi-sector handoffs / multiplayer — why defer (permanently, per PROJECT.md): meaningless with a single combined controller position and one airport's local airspace

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Radar canvas (datablocks/trail/rings/vector) | HIGH | MEDIUM | P1 |
| Click+panel instruction input | HIGH | MEDIUM | P1 |
| Instruction/readback text log | HIGH | MEDIUM | P1 |
| Current-state separation alerting | HIGH | HIGH | P1 |
| Scripted scenario file | HIGH | MEDIUM | P1 |
| Departure flow (spawn→SID→exit) | HIGH | MEDIUM | P1 |
| Arrival flow (STAR→vector/procedural descent→ILS→land) | HIGH | HIGH | P1 |
| Predictive/lookahead STCA | MEDIUM | HIGH | P2 |
| Typed shorthand command entry | MEDIUM | MEDIUM | P2 |
| Go-arounds/missed approaches | MEDIUM | MEDIUM | P2 |
| Digital flight-strip bay | MEDIUM | MEDIUM | P3 |
| Wake turbulence/separation categories | LOW-MEDIUM | MEDIUM | P3 |
| Multiple runways/wind config | LOW-MEDIUM | HIGH | P3 |
| Procedural traffic generator | LOW-MEDIUM | HIGH | P3 |
| VFR traffic | MEDIUM (v2 core value) | HIGH | P3 (v2 milestone) |
| Voice recognition | LOW (confirmed low realism payoff) | HIGH | Excluded |
| Multi-sector handoffs | N/A (no use case) | N/A | Excluded |

**Priority key:**
- P1: Must have for v1 launch (matches PROJECT.md Active requirements)
- P2: Should have, add once v1 core loop validated
- P3: Nice to have, v2+ milestone consideration
- Excluded: confirmed anti-feature for the project's stated scope

## Competitor Feature Analysis

| Feature | EuroScope / VATSIM clients | openScope | Tower!3D Pro | This Project's Approach |
|---------|------------------------------|-----------|---------------|--------------------------|
| Instruction input | Typed command-line + alias shorthand (power-user, keyboard-first) | Typed short-verb command bar, chainable per callsign | Mouse-driven command center + optional (clunky) voice | Click+panel (mouse-first), matching Tower!3D's proven console-style precedent; typed shorthand deferred as v1.x accelerator |
| Datablocks/trail/rings | Configurable dot count, extended datablocks, range rings via `.showantenna`, symbol varies by transponder mode | Text-based sim, minimal radar chrome (browser 2D canvas) | Full 3D + 2D radar screens, flight strips, ground+air views | Full datablock + trail dots + range rings + heading vector, matching real FDB convention (v1 scope) |
| Separation alerting | Not built into the client itself — VATSIM relies on controller judgement, no client-side STCA | No conflict alert system found in research (single-controller sandbox sim, no enforcement) | Not clearly documented as a distinct STCA feature (focus is on command interface/voice) | Explicit STCA-inspired current-state alert (v1), predictive lookahead (v2) — this is a genuine differentiator versus the surveyed hobby tools, most of which don't alert at all |
| Scenario authoring | Sector files + prefile flight plans (network-driven, not single-session scenario files) | JSON `spawnPatterns` per airport, method-based spawn timing (cyclic/random/surge/wave) | Built-in scenario/mission selection, not user-authorable in the same sense | Hand-authored scripted scenario file validated against Pydantic models — closer to openScope's structured-JSON approach than EuroScope's network-oriented sector files |
| Phraseology/readback | Manual typed chat between human controller and human pilot (VATSIM is human-to-human) | Not phraseology-driven — commands are direct, no simulated readback loop documented | Simulated pilot voice responses read back instructions | Text-rendered controller instruction + simulated pilot readback log — this fills a real gap: none of the surveyed hobby ATC tools implement a genuine ICAO-style two-party instruction/readback text log as their core mechanic |

## Sources

- [EuroScope Display Settings](https://www.euroscope.hu/wp/display-settings/) — MEDIUM confidence (official plugin/tool docs, cross-checked)
- [EuroScope Professional Radar Simulation](https://www.euroscope.hu/wp/professional-radar-simulation/) — MEDIUM confidence
- [EuroScope Command Line Reference](https://www.euroscope.hu/wp/command-line-reference/) — MEDIUM confidence (official docs)
- [VRC Command Reference](https://vrc.rosscarlson.dev/docs/command_reference.shtml) — LOW confidence (community tool docs, not independently cross-verified)
- [VATSIM Radar](https://vatsim-radar.com/) / [docs.vatsim-radar.com](https://docs.vatsim-radar.com/) — LOW confidence (community project)
- [Tower!3D Pro on Steam](https://store.steampowered.com/app/588190/Tower3D_Pro/) and [FSNews review](https://fsnews.eu/review-tower3d-pro/) — LOW confidence (marketing + single review synthesis)
- [Short-term conflict alert — SKYbrary](https://skybrary.aero/articles/short-term-conflict-alert-stca) — MEDIUM confidence (aviation safety knowledge base, industry-standard reference)
- [EUROCONTROL Guidelines for Short Term Conflict Alert](https://www.eurocontrol.int/sites/default/files/2019-09/eurocontrol-guidelines-159-part-i-1.0.pdf) — MEDIUM confidence (official regulator guidance document)
- [Short-term conflict alert — Wikipedia](https://en.wikipedia.org/wiki/Short-term_conflict_alert) — LOW confidence (tertiary, used for corroboration only)
- ICAO PANS-ATM (Doc 4444) readback requirements, via [AviationRef ATC Phraseology Guide](https://www.aviationref.com/atc-phraseology) and [SKYbrary ICAO Standard Phraseology Quick Reference](https://skybrary.aero/sites/default/files/bookshelf/115.pdf) — MEDIUM confidence (references trace to the ICAO standard itself)
- [openScope aircraft-commands.md](https://github.com/openscope/openscope/blob/develop/documentation/aircraft-commands.md) — MEDIUM confidence (official open-source project documentation)
- [openScope airport-format.md / spawnPatternReadme](https://github.com/openscope/openscope/blob/develop/documentation/airport-format.md) — MEDIUM confidence (official docs)
- FAA JO 7110.65 Air Traffic Control Order, [Section 3 Radar Identification](https://www.faa.gov/air_traffic/publications/atpubs/atc_html/chap5_section_3.html) and [full order PDF](https://www.faa.gov/documentlibrary/media/order/atc.pdf) — MEDIUM confidence (official FAA regulatory document)
- ["Moving Toward an Air Traffic Control Display Standard"](https://hf.tc.faa.gov/publications/2010-moving-toward-an-air-traffic-control-display-standard/full_text.pdf) — MEDIUM confidence (FAA human-factors research report)
- [Flight progress strip — Wikipedia](https://en.wikipedia.org/wiki/Flight_progress_strip) and [NATS ATC Explained: Flight Progress Strips](https://nats.aero/blog/2026/01/atc-explained-flight-progress-strips/) — MEDIUM confidence (national ANSP blog + tertiary corroboration)
- [FAA Electronic Flight Strips (TFDM)](https://www.faa.gov/air_traffic/technology/tfdm/efs) — MEDIUM confidence (official FAA program page)
- Academic ATC-training scenario research (ResearchGate: "Enhancing Scenario-Centric Air Traffic Control Training"; arXiv "A Virtual Simulation-Pilot Agent for Training of Air Traffic Controllers") — LOW confidence (research-paper abstracts synthesized via search snippets, not full-text verified)

---
*Feature research for: ATC simulator / trainer software, single-airport IFR-only v1 scope*
*Researched: 2026-07-03*
