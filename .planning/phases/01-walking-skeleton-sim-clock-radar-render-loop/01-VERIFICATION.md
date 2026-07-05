---
phase: 01-walking-skeleton-sim-clock-radar-render-loop
verified: 2026-07-05T13:55:49Z
status: passed
score: 8/8 must-haves verified
behavior_unverified: 0
overrides_applied: 0
---

# Phase 1: Walking Skeleton — Sim Clock & Radar Render Loop Verification Report

**Phase Goal:** A fixed-timestep sim clock drives aircraft motion fully decoupled from the render loop, with a bare radar canvas showing range rings, sector lines, and a moving aircraft with heading vector and trail.
**Verified:** 2026-07-05T13:55:49Z
**Status:** passed
**Re-verification:** No — initial verification

## Note on MVP Mode Tag

ROADMAP.md marks this phase `Mode: mvp`, but the phase goal text is a technical/architectural outcome, not a `As a [role], I want [x], so that [y].` user story (confirmed programmatically: `gsd-tools query user-story.validate` returns `valid: false` for this goal string). This is expected for phase 1 — a foundational, non-player-facing infrastructure phase (sim clock + render loop decoupling) that precedes any player-facing feature; there is no sensible user-role framing for "the sim clock is decoupled from rendering." Rather than refuse verification (which would leave the phase with no verification signal at all), this report proceeds with standard goal-backward verification against the ROADMAP Success Criteria and PLAN must_haves, and flags the mode/goal-format mismatch here for human awareness. This is an **informational note, not a gap** — it does not affect the pass/fail determination below.

## Independent Re-Verification Method

SUMMARY.md claims were not trusted at face value. A fresh, independent venv was built from scratch in the sandbox (mirroring exactly what a new developer following the README would do), the package was editable-installed, and the full test suite was executed independently of anything the executor claimed:

```
python3 -m venv --without-pip <verify-venv>   # system Python 3.14 lacks ensurepip, same issue 01-01-SUMMARY documented
<verify-venv>/bin/python3 get-pip.py
<verify-venv>/bin/python3 -m pip install -e ".[dev]"
SDL_VIDEODRIVER=dummy <verify-venv>/bin/python3 -m pytest -q
→ 14 passed in 0.14s
```

Resolved package versions matched the SUMMARY's claims exactly: `pygame-ce 2.5.7`, `pydantic 2.13.4`, `pytest 9.1.1`.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Sim advances on a fixed 1-4Hz tick independent of render frame rate (CORE-01) | ✓ VERIFIED | `src/atc_sim/sim/clock.py` — `SimClock.advance(real_dt, on_tick)` drains ticks from an accumulator at fixed `TICK_DT=0.5` (2Hz) regardless of `real_dt` granularity. Independently re-ran `tests/test_clock.py::test_tick_count_independent_of_call_frequency` — 30fps vs 120fps splits of the same 5.0s wall time drain identical tick counts (`10 == floor(5.0/0.5)`). No pygame/render coupling in this module (enforced by `test_boundary.py`, independently re-run and passing). |
| 2 | A stalled render frame causes bounded catch-up, not a freeze or an instant jump (CORE-02) | ✓ VERIFIED | `advance()` clamps `real_dt` to `MAX_FRAME_TIME=5.0`, drains at most `MAX_TICKS_PER_FRAME=5` ticks per call, and drops any remaining backlog into `dropped_tick_seconds` instead of retaining it. Independently re-ran `test_stall_caps_ticks_per_frame` (a single `advance(3.0)` drains exactly 5 ticks, doesn't hang) and `test_backlog_beyond_cap_is_dropped` (`dropped_tick_seconds > 0` after the capped call; a follow-up `advance(0.0)` drains zero further ticks — no retained-backlog burst) — both pass. Note: SUMMARY.md documents that the executor caught and fixed a real bug in the RESEARCH.md reference constants (`MAX_FRAME_TIME=0.25` at `TICK_DT=0.5` made the tick cap mathematically unreachable, `dropped_tick_seconds` stuck at 0) — this fix is visible in-code (`clock.py` lines 16-27 comment) and is exactly the kind of deviation independent re-verification is meant to catch; it was caught by the plan's own TDD loop, not glossed over. |
| 3 | Render layer reads current aircraft state each frame without ever mutating it (CORE-03) | ✓ VERIFIED | `sim/interpolation.py`'s `interpolate()` takes two `frozen=True` `AircraftSnapshot` pydantic models and returns a third, distinct instance — mutation of a frozen model raises `pydantic.ValidationError`. `render/radar.py`'s `draw_frame`/`draw_aircraft` only read `render_state.x/y/heading_deg`, never assign to them, and never import `atc_sim.sim.*` at all (uses a structural `typing.Protocol` instead) — `app.py` is confirmed the sole module importing both `pygame` and `atc_sim.sim.*` (grep-verified: `render/*.py` has zero `atc_sim.sim` imports). `tests/test_boundary.py` (independently re-run) confirms zero pygame imports anywhere under `src/atc_sim/sim/`. `test_interpolate_does_not_mutate_inputs` independently re-run and passing. |
| 4 | The radar canvas displays range rings and sector reference lines as a static background layer (RADAR-01) | ✓ VERIFIED | `render/radar.py::build_static_background()` draws `NUM_RINGS=4` concentric circles (`RING_STEP_PX=80`) and `NUM_SECTOR_LINES=8` anti-aliased lines radiating from `CENTER=(640,400)`, returning a pre-rendered `Surface` blitted once per frame in `app.py` (not redrawn as primitives every frame). Independently re-ran the Task-1 verify command headlessly (`SDL_VIDEODRIVER=dummy`) — background builds at the correct size with `CENTER==(640,400)`, `NUM_RINGS==4`, `NUM_SECTOR_LINES==8`. Visual correctness (does it look right on a real display) was human-verified during execution — see Truth 7. |
| 5 | A moving aircraft renders as a dot with a heading vector and a trail of recent positions, driven only by sim-tick state (RADAR-03) | ✓ VERIFIED | `draw_aircraft()` draws in z-order trail → heading-vector (`pygame.draw.aaline`, compass convention) → dot last (never occluded). `app.py`'s `on_tick` (called only from `SimClock.advance()`) appends `(aircraft.x, aircraft.y)` to the trail exactly once per sim tick — no trail mutation exists in the per-frame render section (grep/code-reviewed). Heading vector correctness across the 0/360 seam is proven by `_lerp_angle_deg` (shortest-path formula) and independently re-run `test_heading_interpolation_shortest_path` (350°→10° interpolates through 0, not backward through 180°). Independently re-ran the headless render smoke test — full frame draws without raising. |
| 6 | README Installation section documents real setup/run instructions, placeholder removed (success criterion #5) | ✓ VERIFIED | Read `README.md` directly: venv creation (both Unix/Windows forms), conditional `ensurepip` fallback, `pip install --upgrade pip` + `pip install -e ".[dev]"`, `atc-sim` launch command (matches `pyproject.toml`'s `[project.scripts]` entry exactly, confirmed via `tomllib` parse), `python -m atc_sim.app` fallback, and `python -m pytest`. No "not available"/"coming soon" text anywhere in the file. |
| 7 | Following the README launches a working app with smooth, non-streaking, FPS-independent motion (visual/behavioral criteria) | ✓ VERIFIED (human-verified, per task instruction) | Per the task's explicit instruction, this was already human-verified in-band during execution: `01-05-SUMMARY.md`'s Task 2 checkpoint records a human running the assembled app on their own machine with a real display, confirming smooth motion, no wrap-streak, and FPS-independent speed across multiple `FPS_CAP` values (coverage IDs D2/D3/D4, `human_judgment: true`). Cross-checked that claim against the actual code rather than accepting it blindly: the wrap-skip guard (`interpolate()` snaps to `curr` when `abs(curr.x - prev.x) > CANVAS_WIDTH/2`, i.e. exactly the D-02 wrap case) and the interpolation seam that produces smooth motion both genuinely exist and are wired into `app.py`'s main loop (`render_state = interpolate(prev_state, curr_state, alpha)`, drawn every frame; `FPS_CAP` only controls `pg_clock.tick()`, never touched by `sim_step`/`SimClock`). The code fully supports the human's claim — no evidence of a mismatch between what was reported and what exists. |
| 8 | The sim/render architectural boundary (CORE-03's core mechanism) is enforced, not just followed by convention | ✓ VERIFIED | `tests/test_boundary.py` recursively scans `src/atc_sim/sim/*.py` for pygame import statements. Independently re-run — passes. Manually grepped `src/atc_sim/sim/*.py` for `pygame` — zero matches. |

**Score:** 8/8 truths verified (0 present-but-behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pyproject.toml` | Package metadata, `atc-sim` script entry, dep ranges, pytest config | ✓ VERIFIED | Parses as valid TOML; `[project.scripts].atc-sim == "atc_sim.app:main"`; `[tool.setuptools.packages.find].where == ["src"]`; pygame-ce/pydantic/pytest ranges present |
| `src/atc_sim/sim/clock.py` | `SimClock` fixed-timestep accumulator | ✓ VERIFIED | Exists, substantive (59 lines, full implementation, not a stub), wired (imported by `app.py`), no pygame import |
| `src/atc_sim/sim/aircraft.py` | `Aircraft` model + `sim_step` | ✓ VERIFIED | Exists, substantive, wired (imported by `app.py` and `interpolation.py`), field validation confirmed via test |
| `src/atc_sim/sim/interpolation.py` | `AircraftSnapshot`, `capture_state`, `interpolate` | ✓ VERIFIED | Exists, substantive, wired (imported by `app.py`), wrap-skip guard present |
| `src/atc_sim/render/window.py` | Window constants, D-01 color palette, `create_window()` | ✓ VERIFIED | Exists, substantive, wired (imported by `app.py` and `radar.py`); colors match D-01 exactly |
| `src/atc_sim/render/radar.py` | `build_static_background`, `draw_aircraft`, `draw_frame` | ✓ VERIFIED | Exists, substantive, wired (imported by `app.py`); correct z-order confirmed by code read |
| `src/atc_sim/app.py` | Composition root / main loop | ✓ VERIFIED | Exists, substantive, wired (registered `atc-sim` console script resolves and imports cleanly); confirmed only module importing both pygame and `atc_sim.sim.*` |
| `tests/test_boundary.py` | CORE-03 headless guard | ✓ VERIFIED | Exists, substantive, independently re-run and passing |
| `tests/test_clock.py`, `tests/test_interpolation.py`, `tests/test_render_smoke.py` | Behavioral test suites | ✓ VERIFIED | Exist, substantive, independently re-run and passing (13 tests across all three + boundary = 14 total) |
| `README.md` | Installation instructions | ✓ VERIFIED | Modified, substantive, no placeholder text remains |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `app.py` | `sim/clock.py` | `SimClock().advance(real_dt, on_tick)` called every frame | WIRED | Confirmed by direct read of `app.py` |
| `app.py` `on_tick` | `sim/aircraft.py` | `sim_step(aircraft, dt)` called only inside `on_tick` | WIRED | Confirmed — no `sim_step` call exists in the per-frame render section |
| `app.py` | `sim/interpolation.py` | `capture_state`/`interpolate` called every frame to produce `render_state` | WIRED | Confirmed |
| `app.py` | `render/radar.py` | `draw_frame(screen, background, render_state, trail)` called every frame, then `pygame.display.flip()` | WIRED | Confirmed |
| `render/radar.py` | `render/window.py` | Imports color constants (`BG_COLOR`, `AIRCRAFT_COLOR`, etc.) | WIRED | Confirmed via import statement and constant usage |
| `pyproject.toml` `[project.scripts]` | `atc_sim.app:main` | Console-script entry point | WIRED | Confirmed: `python -c "from atc_sim.app import main"` succeeds in the independently-built venv |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full headless test suite passes (independent venv) | `SDL_VIDEODRIVER=dummy python -m pytest -q` | `14 passed in 0.14s` | ✓ PASS |
| CORE-01 frame-rate independence (named test) | `pytest tests/test_clock.py::test_tick_count_independent_of_call_frequency` | pass | ✓ PASS |
| CORE-02 capped catch-up + backlog drop (named test) | `pytest tests/test_clock.py::test_backlog_beyond_cap_is_dropped` | pass | ✓ PASS |
| Radar background builds headlessly at correct geometry | `SDL_VIDEODRIVER=dummy python -c "...build_static_background..."` | `background OK` | ✓ PASS |
| `atc-sim` console script target resolves | `python -c "from atc_sim.app import main"` | imports cleanly | ✓ PASS |
| Package versions match SUMMARY claims | `pip show pygame-ce pydantic pytest` | `2.5.7 / 2.13.4 / 9.1.1` — exact match | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan(s) | Description | Status | Evidence |
|-------------|-----------------|-------------|--------|----------|
| CORE-01 | 01-02, 01-05 | Fixed-timestep clock decoupled from render loop | ✓ SATISFIED | `SimClock`, independently re-run tests, human-verified visually |
| CORE-02 | 01-02 | Capped catch-up / spiral-of-death prevention | ✓ SATISFIED | `MAX_TICKS_PER_FRAME`/`MAX_FRAME_TIME`, independently re-run tests |
| CORE-03 | 01-01, 01-03, 01-04 | Render layer never mutates sim state | ✓ SATISFIED | Frozen snapshots, boundary guard test, code review of render layer |
| RADAR-01 | 01-04, 01-05 | Range rings + sector lines static background | ✓ SATISFIED | `build_static_background`, headless smoke test, human-verified visually |
| RADAR-03 | 01-03, 01-04, 01-05 | Aircraft dot + heading vector + trail | ✓ SATISFIED | `draw_aircraft`, shortest-path heading lerp, human-verified visually |

**No orphaned requirements:** REQUIREMENTS.md's traceability table maps exactly CORE-01/02/03, RADAR-01/03 to Phase 1, and the union of every plan's `requirements:` frontmatter field across 01-01 through 01-05 covers exactly this same set — no gaps, no extras.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | No `TODO`/`FIXME`/`XXX`/`HACK`/`PLACEHOLDER` markers found anywhere under `src/` or `tests/` | — | None — clean |
| — | — | No "not available"/"coming soon"/"not yet implemented" strings found in `src/`, `tests/`, or `README.md` | — | None — clean |
| `README.md` | 79 | "Status" section still reads "Planning complete — implementation not yet started." | ℹ️ INFO | Stale/inaccurate now that Phase 1 is implemented and complete. Outside the scope of this phase's must_haves (only the *Installation* section was in scope for the 01-05 README rewrite), so not a gap for this phase, but worth fixing in a future phase's docs pass. |
| `.planning/phases/.../01-VALIDATION.md` | whole file | Template placeholders (`{N}`, `{command}`, etc.) never filled in; `nyquist_compliant: false` | ℹ️ INFO | Planning artifact, not a phase deliverable; does not affect goal achievement. Noted for completeness since the file exists in the phase directory. |

No blocking anti-patterns found.

### Human Verification Required

None outstanding. The one behavior-dependent truth in this phase (smooth/non-streaking/FPS-independent motion on a real display) was already human-verified in-band during execution (01-05-SUMMARY.md, `human_judgment: true`), and this report independently confirmed the underlying code (`interpolate()`'s wrap-skip guard, the interpolation seam, `FPS_CAP` isolation from `sim_step`) genuinely exists and is wired to support that human's observation — it is not merely claimed.

### Gaps Summary

No gaps found. All 5 ROADMAP success criteria and all `must_haves.truths` across the 5 plans (01-01 through 01-05) are verified against the actual codebase, using an independently-built venv (not the executor's), fresh test runs (not trusted output), and direct code reads (not SUMMARY paraphrase). One informational note is raised: ROADMAP.md tags this phase `Mode: mvp` but its goal is not phrased as a user story — flagged for human awareness, not treated as a gap given this is a non-player-facing infrastructure phase.

---

*Verified: 2026-07-05T13:55:49Z*
*Verifier: Claude (gsd-verifier)*
