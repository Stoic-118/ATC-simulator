---
phase: 01-walking-skeleton-sim-clock-radar-render-loop
plan: 05
subsystem: docs
tags: [readme, pip, venv, human-verify, walking-skeleton]

# Dependency graph
requires:
  - phase: 01-01
    provides: src-layout package skeleton, pyproject.toml [project.scripts] atc-sim entry point, pytest config
  - phase: 01-04
    provides: Complete render layer + app.py main loop wiring — the full walking skeleton this plan verifies end-to-end
provides:
  - README.md Installation section with real, verified venv/pip/ensurepip/install/launch/test instructions (no placeholder text remaining)
  - Human sign-off confirming the phase's visual/behavioral success criteria (smooth interpolated motion, no wrap-streak, FPS-independent speed, correct radar visuals) on a real display
  - Phase 01 (walking-skeleton-sim-clock-radar-render-loop) fully complete — all 5 plans done
affects: [02]

# Tech tracking
tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified:
    - README.md

key-decisions:
  - "Documented both the atc-sim console script and python -m atc_sim.app as an equivalent fallback launch path, matching pyproject.toml's [project.scripts] entry exactly"
  - "Kept the ensurepip fallback note as a conditional step (only needed if python -m pip --version fails) rather than a mandatory step, since most modern venvs bundle pip already"

requirements-completed: [CORE-01, RADAR-01, RADAR-03]

coverage:
  - id: D1
    description: "README Installation section documents venv creation, pip bootstrap (ensurepip fallback), editable dev install, and the atc-sim launch command — 'not available yet' placeholder fully removed"
    requirement: "RADAR-01"
    verification:
      - kind: unit
        ref: "python -c \"t=open('README.md').read().lower(); assert 'not available' not in t and 'coming soon' not in t; assert '.venv' in t and 'pip install -e' in t and 'atc-sim' in t and 'pytest' in t\" (Task 1 verify block)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Following the README steps verbatim from a clean checkout launches the walking-skeleton window; range rings/sector lines render as a static background; the aircraft shows a cyan dot, heading vector, and trail"
    requirement: "RADAR-01"
    verification:
      - kind: manual_procedural
        ref: "Task 2 checkpoint — human ran the app on their own machine with a real display, followed the README steps verbatim"
        status: pass
    human_judgment: true
    rationale: "Visual rendering correctness (window opens, rings/sector-lines/dot/vector/trail render correctly) cannot be verified by an automated headless test — it requires a human viewing a real display. The 01-04 headless smoke test already proves the code path executes without raising; this checkpoint proves it looks and behaves correctly."
  - id: D3
    description: "Aircraft motion is smooth (no per-tick teleport hops) and does not streak across the canvas when it wraps at the edge — interpolation + wrap-skip working end-to-end"
    requirement: "CORE-01"
    verification:
      - kind: manual_procedural
        ref: "Task 2 checkpoint — human confirmed smooth gliding motion and no streak-across-canvas at the wrap edge"
        status: pass
    human_judgment: true
    rationale: "Smoothness and wrap-skip correctness are perceptual/visual qualities of motion over time; no automated test can substitute for a human watching the animation run."
  - id: D4
    description: "Changing the render FPS cap does not change the aircraft's on-screen speed, proving CORE-01 sim/render decoupling visually"
    requirement: "CORE-01"
    verification:
      - kind: manual_procedural
        ref: "Task 2 checkpoint — human tested multiple FPS_CAP values in render/window.py and confirmed constant wall-clock crossing time"
        status: pass
    human_judgment: true
    rationale: "FPS-independence is a timing/visual property that requires a human to relaunch at different FPS_CAP values and compare perceived speed; this is the core architectural claim of the phase and the reason for the human capstone checkpoint."
  - id: D5
    description: "Full pytest suite is green on the human's machine (not just the sandbox)"
    verification:
      - kind: unit
        ref: "python -m pytest -q (14 tests) — confirmed green both in the execution sandbox and reported by the human during the Task 2 checkpoint"
        status: pass
    human_judgment: false

# Metrics
duration: ~15min
completed: 2026-07-05
status: complete
---

# Phase 01 Plan 05: README Installation Rewrite + Walking-Skeleton Capstone Sign-off Summary

**Rewrote README.md's Installation section with real, verified venv/pip/ensurepip/install/launch/test steps, then obtained human sign-off that the assembled walking skeleton (fixed-timestep sim clock, interpolated render, radar canvas) runs correctly with smooth, FPS-independent, non-streaking aircraft motion — closing out Phase 01.**

## Performance

- **Duration:** ~15 min active execution (1 auto task + 1 human-verify checkpoint)
- **Started:** 2026-07-05T11:59:16+01:00 (Task 1 commit)
- **Completed:** 2026-07-05T12:09:56+01:00 (Task 1 commit); checkpoint approved in follow-up session
- **Tasks:** 2 (1 auto, 1 checkpoint:human-verify)
- **Files modified:** 1 (README.md)

## Accomplishments

- Rewrote README's Installation section: prerequisites (Python 3.12+), venv creation with both Unix/Windows activation forms, a conditional `ensurepip` bootstrap note, `pip install --upgrade pip` + `pip install -e ".[dev]"`, the `atc-sim` console-script launch command with `python -m atc_sim.app` documented as the equivalent fallback, and `python -m pytest` for running tests
- Removed all "not available yet"/"coming soon" placeholder text from the Installation section
- Added a one-line description of what the running skeleton shows (single aircraft gliding across a radar canvas with range rings, sector lines, heading vector, and trail)
- Obtained human sign-off (Task 2 checkpoint) on a real display, confirming: window opens correctly; static background (range rings + sector lines) renders; aircraft dot/heading-vector/trail render correctly; motion is smooth with no teleport hops; no streak-across-canvas at the wrap edge; aircraft speed is FPS-independent across multiple `FPS_CAP` values; `python -m pytest` is green on the human's machine
- This closes Phase 01 (walking-skeleton-sim-clock-radar-render-loop) — all 5 plans complete, all phase success criteria (CORE-01, CORE-02, CORE-03, RADAR-01, RADAR-03) satisfied

## Task Commits

Each task was committed atomically:

1. **Task 1: Rewrite README Installation section with real setup + run instructions** - `a738ede` (docs)
2. **Task 2 (checkpoint): Walking-skeleton run-through sign-off** - no code commit (human verification only, approved)

**Plan metadata:** commit pending (this SUMMARY.md + STATE.md + ROADMAP.md commit, created next)

## Files Created/Modified

- `README.md` - Installation section rewritten with venv creation, ensurepip fallback note, editable dev install, `atc-sim` launch command (+ `python -m atc_sim.app` fallback), and `python -m pytest` test command; placeholder text removed

## Decisions Made

- Documented both the `atc-sim` console script and `python -m atc_sim.app` as an equivalent fallback launch path, matching `pyproject.toml`'s `[project.scripts]` entry exactly
- Kept the `ensurepip` fallback note conditional (only run if `python -m pip --version` fails) rather than a mandatory step, since most modern venvs bundle pip already

## Deviations from Plan

None - plan executed exactly as written. Task 1 (README rewrite) was auto-verified against its literal acceptance criteria; Task 2 (checkpoint) was approved by the human without any reported issues (no teleporting, no wrap streak, no FPS-dependent speed change, all radar visuals correct).

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 01 (walking-skeleton-sim-clock-radar-render-loop) is fully complete: all 5 plans executed, all phase success criteria met and human-verified
- The walking skeleton (SimClock fixed-timestep accumulator, Aircraft model + sim_step, interpolation, radar canvas render layer, app.py composition root) is a proven, working foundation for Phase 02
- README now gives any future session (or the next phase's planner) a working, verified path to install and run the app from a clean checkout
- No blockers for Phase 02

---
*Phase: 01-walking-skeleton-sim-clock-radar-render-loop*
*Completed: 2026-07-05*

## Self-Check: PASSED

All claimed files found on disk (README.md, this SUMMARY.md) and the claimed Task 1 commit (a738ede) found in git history.
