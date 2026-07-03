<!-- GSD:project-start source:PROJECT.md -->

## Project

**ATC Simulator**

A full-fidelity, single-airport air traffic control simulator: a native Python + Pygame desktop application (not a CLI, not a browser app) where the player works one combined Approach + Tower position. Aircraft are performance-modeled and rendered on a vector-style radar display; the player issues real ATC instructions and gets phraseology-accurate readbacks, with separation violations surfaced as alerts rather than silently blocked.

**Core Value:** The player can work a full session — launch an aircraft off a SID, land another off the ILS, entirely through their own instructions — and the sim never lies about separation.

### Constraints

- **Tech stack**: Python 3.12+, Pygame, pygame_gui/hand-rolled UI, asyncio/fixed-timestep sim clock, geographiclib or pyproj, Pydantic — Why: explicit user decision; must be a native desktop app with its own rendering loop, no browser/HTML anywhere in the stack
- **Scope**: single airport (EGGW), single runway direction (26), IFR only for v1 — Why: keeps procedure/ILS logic surface area small enough to validate the core instruction-and-separation loop before expanding
- **Fidelity**: simplified per-aircraft-type performance profiles, not BADA-style tables or full physics — Why: feels real without a heavy modeling lift blocking early phases
- **Traffic generation**: scripted scenario file, not a randomized generator, for v1 — Why: repeatable, deterministic runs are needed while separation/instruction logic is still being debugged
- **Separation enforcement**: alerts (STCA-style), not automatic blocking — Why: matches real-world ATC — the controller decides, the sim only warns

<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->

## Technology Stack

## Recommended Stack

### Core Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Python | 3.12+ | Language runtime | Already decided in PROJECT.md; modern typing (generics, `match`), good perf, wide library support. |
| pygame-ce | 2.5.7 (current line as of early 2026) | Window, 2D rendering, input, audio, event loop | The actively maintained community fork of pygame. Original `pygame` package has slow, largely stalled development (last stable 2.6.1, Sept 2024); pygame-ce ships frequent releases, SDL2-current fixes, and measurable performance improvements (e.g. ~2x faster import via lazy numpy loading, ~30% faster Vector2 construction). It is a drop-in API superset of `pygame` (`import pygame` still works), so there is no migration cost and no reason to start a new project on classic pygame in 2025-2026. |
| pygame_gui | 0.6.14 | Themed UI widgets (flight-strip bay, comms log, frequency box) layered over the pygame surface | Purpose-built to run inside a pygame main loop: feed it `pygame.event` objects, call `update(dt)` and `draw_ui(surface)` each frame. It has since moved to target pygame-ce directly for better SDL/perf. JSON theme files give a controllable "radar console" visual style without hand-rolling widget hit-testing, text entry, or scrollbars. |
| Pydantic | v2, ~2.13.x | Data modeling and validation for aircraft state, procedures (SID/STAR), navdata (runways, fixes, ILS params), and scenario files | v2's validation core is written in Rust (pydantic-core) — 4x-50x faster than v1 — so per-load validation cost is negligible even though the sim itself doesn't need to validate every tick. Gives free JSON (de)serialization for scenario files and clean nested-model composition for procedures/fixes. |
| geographiclib | 2.1 | Great-circle distance, bearing, direct/inverse geodesic problems for navdata math (fix-to-fix distance, radial/bearing from a VOR, ILS localizer geometry) | See dedicated comparison below — recommended over pyproj for this project. |

### Simulation / Rendering Architecture (pattern, not a library)

| Pattern | Purpose | Why |
|---------|---------|-----|
| Fixed-timestep accumulator loop (Glenn Fiedler's "Fix Your Timestep!") | Decouple the 1-4Hz aircraft-state sim tick from the 60fps pygame render loop | This is the industry-standard pattern for exactly this problem, and it's a pattern, not a dependency — implement it directly in the main loop, don't reach for a framework. See Architecture Patterns below. |
| Single-threaded main loop (no `asyncio`, no `threading`) | Run sim update + render in one process, one thread | Python's GIL means `threading` buys no CPU-bound speedup here and only adds shared-state race-condition risk between a sim thread and a render thread reading the same aircraft objects. `asyncio` only pays off for concurrent I/O (network, disk) running alongside a loop — this project has no such I/O on the hot path in v1. A plain `while running:` loop with the accumulator is simpler, easier to debug, and the correct tool for a single-process real-time sim. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | current 8.x | Unit/integration tests for separation logic, performance model, procedure state machines | Use from day one — separation-checking and ILS-capture logic are exactly the kind of pure-function logic that benefits from fast, deterministic tests independent of the render loop. |
| `pygame.freetype` or `pygame.font` (bundled with pygame-ce) | n/a | Text rendering for datablocks, comms log, phraseology readbacks | No external dependency needed — pygame-ce ships SDL_ttf bindings; `freetype` module gives finer control over glyph metrics if datablock text needs precise alignment. |
| `dataclasses` (stdlib) | n/a | Lightweight internal-only structs that don't need validation (e.g. per-frame interpolation snapshots, render-side view models) | Use for hot-path, per-tick objects created and discarded every frame where Pydantic's (small but nonzero) construction overhead isn't worth paying; keep Pydantic for anything loaded from disk or crossing a validation boundary. |

## Alternatives Considered

| Category | Recommended | Alternative | Why Not (for this project) |
|----------|-------------|-------------|-----------------------------|
| 2D rendering engine | pygame-ce | classic `pygame` | Slower-moving upstream; no capability pygame-ce lacks; pygame-ce is what pygame_gui itself now targets. No reason to pick the un-forked original in 2025-2026. |
| 2D rendering engine | pygame-ce | Python `arcade` | Arcade's headline advantage — OpenGL/GPU-accelerated sprite batching — matters when drawing hundreds/thousands of textured sprites. A radar display is the opposite workload: a few dozen aircraft symbols plus thin vector primitives (lines, circles, dots, anti-aliased range rings) and text — exactly what pygame's CPU-side `draw.line`/`draw.circle`/`draw.aaline`/font rendering handles well within a 60fps budget. Arcade also nudges toward its own scene/sprite-list architecture that fights a hand-rolled radar-canvas + fixed-timestep sim design. Revisit only if profiling shows the render loop CPU-bound with a much larger aircraft/DrawCall count than v1's small fleet. |
| 2D rendering engine | pygame-ce | ModernGL + pygame (raw OpenGL) | Gives full GPU pipeline control but throws away pygame's biggest advantage for this project: `pygame.draw`/`pygame.font` primitives map almost directly onto radar-display elements (rings, vectors, datablocks) with no shader/VBO bookkeeping. Not justified unless/until profiling proves CPU-side 2D drawing is the bottleneck — unlikely at v1's traffic volumes. |
| UI panel library | pygame_gui | hand-rolled immediate-mode widgets | Hand-rolling buttons/dropdowns/scrollbars/text-entry for a flight-strip bay + comms log + frequency box is a meaningful amount of throwaway UI-toolkit code with no reuse value; pygame_gui already solves hit-testing, focus, theming, and text entry, and integrates at the "call `update`/`draw_ui` each frame" level pygame projects expect. Reach for hand-rolled UI only for the radar canvas itself (aircraft click-select, datablock hit-testing) where pygame_gui doesn't apply anyway. |
| UI panel library | pygame_gui | `imgui-bundle` (Dear ImGui Python binding) | imgui-bundle is faster/snappier for UI-heavy tool-style apps, but it does not integrate with pygame's SDL renderer directly — it wants its own GPU context (typically GLFW+ModernGL), meaning a second windowing/rendering pipeline running alongside pygame's surface-based one. For a modest widget count (strip bay, log, frequency box) that integration tax isn't worth paying. Reconsider only if the panel UI grows large/complex enough that pygame_gui's per-frame surface blitting becomes a measured bottleneck. |
| Sim/render decoupling | Single-threaded accumulator loop | `asyncio` event loop | `asyncio` doesn't parallelize CPU-bound work (still one thread, still the GIL) and only pays for itself when you have concurrent I/O to interleave. Nothing in v1's hot path (aircraft state update, collision/separation check, rendering) is I/O-bound. Keep `asyncio` in reserve for a hypothetical later phase (e.g. background scenario loading, network multiplayer) — don't build the core loop around it. |
| Sim/render decoupling | Single-threaded accumulator loop | Separate sim thread + render thread | Introduces shared mutable state (aircraft positions) accessed from two threads under the GIL, requiring locks or message-passing for no CPU-bound benefit in Python. Adds real complexity (thread-safety bugs in exactly the separation/collision logic that must be trustworthy) for zero speed gain. |
| Geodesy | geographiclib | pyproj | See dedicated section below. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|--------------|
| Classic `pygame` (PyPI package `pygame`, not `pygame-ce`) | Development has slowed to near-standstill relative to the community fork; missing fixes/perf work already in pygame-ce; `pygame_gui` itself has moved to target pygame-ce. | `pygame-ce` |
| `pyproj` as the primary navdata geodesy library | Wraps the PROJ C library and requires bundled data files (`proj.db`) plus compiled binary wheels; this is documented to cause real PyInstaller packaging failures (missing `proj.db`, `PROJ_LIB` env var issues, DLL load failures) requiring manual spec-file runtime hooks. This project has an explicit later PyInstaller-packaging phase — picking a geodesy library with zero native/data-file dependencies now avoids inheriting that pain later. pyproj's real strength (arbitrary CRS/datum/map-projection transforms) is not needed here: the project only needs WGS84 lat/lon distance, bearing, and direct/inverse geodesic math for navdata (fixes, runway thresholds, ILS localizer/glideslope geometry). | `geographiclib` |
| Threading for the sim/render split | GIL means no CPU-bound speedup; adds shared-state race risk in exactly the code (separation checks) that must never be subtly wrong. | Single-threaded fixed-timestep accumulator loop |
| `imgui-bundle` / `pyimgui` for the flight-strip/comms/frequency panels | Needs its own GPU rendering context (GLFW/ModernGL) rather than integrating with pygame's SDL surface pipeline — a second UI stack running alongside the radar canvas for no benefit at this widget count. | `pygame_gui` |
| Building the radar canvas as pygame `Sprite`/`Group` objects | Sprite/Group is optimized for large numbers of independently-blitted images with dirty-rect tracking; a radar display's elements (range rings, sector lines, datablocks, trail dots, vector lines) are better modeled as data drawn imperatively each frame from current (interpolated) aircraft state, not as persistent sprite objects with their own position/image state to keep in sync with the sim. | Plain `pygame.draw.*` / `pygame.font` calls driven directly from interpolated sim state each frame |

## Architecture Patterns Established by This Research

### Fixed-timestep accumulator (sim/render decoupling)

### Pydantic modeling pattern for aircraft/procedures/navdata

- Use `model_config = ConfigDict(...)` (v2 style), not the v1 `class Config:` pattern.
- Represent flight phase (departure/climb/cruise/approach/landed) as a discriminated union or enum-tagged sub-model rather than one flat mutable `Aircraft` model with many optional fields — keeps phase-specific fields (e.g. `localizer_course`, `glideslope_angle` only meaningful during approach) type-safe instead of `Optional[...]` soup.
- Use `@model_validator(mode="after")` for cross-field invariants (e.g. assigned altitude must be consistent with current clearance type).
- Validate at boundaries: scenario file load, navdata load, procedure load. Once an `Aircraft`/`Runway`/`Fix` object exists in memory for the sim loop, treat it as already valid — don't re-validate every tick if using `model_copy`/mutation in the hot path. Consider `frozen=True` immutable snapshots for the per-tick `capture_state()` structures used by the interpolation step above (this pairs naturally with the accumulator pattern's need for "previous state" and "current state" snapshots).

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|------------------|-------|
| `pygame_gui` 0.6.14 | `pygame-ce` (not classic `pygame`) | pygame_gui has moved to target pygame-ce; confirm pinned pygame-ce version against pygame_gui's declared dependency range at install time. |
| `geographiclib` 2.1 | Python >=3.7 | No conflict with Python 3.12+; pure Python, no compiled extension to break across platforms — this also simplifies PyInstaller packaging versus pyproj. |
| Pydantic v2 (~2.13.x) | Python 3.12+ | No known issues; v2's Rust core ships prebuilt wheels for common platforms. |

## What to Re-Verify Before Implementation

## Sources

- pygame-ce vs pygame maintenance/governance: [Pygame vs. Pygame-CE API Differences (gist)](https://gist.github.com/davidpendergast/77e49f8028ce611ac478c38f77f9f72f), [pygame-ce GitHub](https://github.com/pygame-community/pygame-ce), [pygame-ce PyPI](https://pypi.org/project/pygame-ce/) — MEDIUM confidence (cross-checked across independent sources via WebSearch)
- pygame-ce release history/versions: [Releases · pygame-community/pygame-ce](https://github.com/pygame-community/pygame-ce/releases), [pygame-ce docs front page](https://pyga.me/docs/) — MEDIUM confidence
- Arcade vs pygame performance/architecture: [Arcade Performance Information](https://api.arcade.academy/en/2.5.7/arcade_vs_pygame_performance.html), [Pygame Comparison — Arcade docs](https://api.arcade.academy/en/2.6.0/pygame_comparison.html) — LOW-MEDIUM confidence (official Arcade docs are authoritative for Arcade's own claims, but comparison framing is Arcade's own)
- pygame_gui version/features/maintenance: [pygame-gui PyPI](https://pypi.org/project/pygame-gui/), [Pygame GUI docs change list](https://pygame-gui.readthedocs.io/en/latest/change_list.html) — MEDIUM confidence
- imgui-bundle vs pygame_gui integration tradeoffs: [UI: pygame-gui vs imgui_bundle — Mob City](https://mobcitygame.com/ui-pygame-gui-vs-imgui_bundle/), [Dear ImGui Bundle site](https://imgui-bundle.pages.dev/) — LOW confidence (single blog source for the head-to-head framing; general imgui-bundle architecture claims corroborated by its own docs)
- Fixed timestep accumulator pattern: [Fix Your Timestep! — Gaffer On Games](https://gafferongames.com/post/fix_your_timestep/), [Game Loop — Game Programming Patterns](https://gameprogrammingpatterns.com/game-loop.html) — MEDIUM confidence (canonical, widely-cited reference pattern)
- geographiclib vs pyproj accuracy/use: [geopy PR discussion](https://github.com/geopy/geopy/pull/144/files/db9f5478a609a38112fa931284e5342684ae6a48), [Computing Geodesic Distance with Python](https://www.cosmoscalibur.com/en/blog/2020/calcular-distancia-geodesica-con-python/) — MEDIUM confidence
- geographiclib version: [geographiclib PyPI](https://pypi.org/project/geographiclib/) — MEDIUM confidence
- pyproj version/API: [pyproj PyPI](https://pypi.org/project/pyproj/), [pyproj Geod docs](https://pyproj4.github.io/pyproj/stable/api/geod.html) — MEDIUM confidence
- pyproj + PyInstaller packaging issues: [pyinstaller/pyinstaller#8415](https://github.com/pyinstaller/pyinstaller/issues/8415), [pyproj4/pyproj discussion #1391](https://github.com/pyproj4/pyproj/discussions/1391), [pyproj4/pyproj#273](https://github.com/pyproj4/pyproj/issues/273) — MEDIUM confidence (direct GitHub issue/discussion reports)
- Pydantic v2 version/best practices: [Pydantic PyPI](https://pypi.org/project/pydantic/), [Pydantic v2 changelog](https://docs.pydantic.dev/latest/changelog/), [Pydantic validators docs](https://docs.pydantic.dev/latest/concepts/validators/) — MEDIUM confidence
- PyInstaller + pygame asset/onefile gotchas: [pyinstaller/pyinstaller#8997](https://github.com/pyinstaller/pyinstaller/issues/8997), [Bundling a Game with PyInstaller — Arcade docs](https://api.arcade.academy/en/stable/tutorials/bundling_with_pyinstaller/index.html), [Bundling data files with PyInstaller](https://www.iditect.com/faq/python/bundling-data-files-with-pyinstaller-onefile.html) — MEDIUM confidence
- asyncio vs threading vs single-threaded loop: [AsyncIO for the working PyGame programmer (parts I & II)](https://blubbervision.neocities.org/asyncio), [Asyncio Vs Threading in Python — GeeksforGeeks](https://www.geeksforgeeks.org/python/asyncio-vs-threading-in-python/), [Asyncio vs Threading — SuperFastPython](https://superfastpython.com/asyncio-vs-threading/) — MEDIUM confidence

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
