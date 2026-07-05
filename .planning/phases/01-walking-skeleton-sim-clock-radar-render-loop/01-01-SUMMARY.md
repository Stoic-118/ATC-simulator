---
phase: 01-walking-skeleton-sim-clock-radar-render-loop
plan: 01
subsystem: infra
tags: [pygame-ce, pydantic, pytest, venv, packaging, src-layout]

# Dependency graph
requires: []
provides:
  - src-layout package skeleton (src/atc_sim/, src/atc_sim/sim/, src/atc_sim/render/)
  - pyproject.toml with pinned dependency ranges, pytest config, and the atc-sim console-script entry point
  - working .venv with pygame-ce 2.5.7, pydantic 2.13.4, pytest 9.1.1 installed editable
  - sim/render architectural boundary guard (tests/test_boundary.py) enforcing CORE-03
affects: [01-02-sim-clock, 01-03-aircraft-interpolation, 01-04-render-loop, 01-05-app-entrypoint]

# Tech tracking
tech-stack:
  added: [pygame-ce 2.5.7, pydantic 2.13.4, pytest 9.1.1, setuptools src-layout]
  patterns:
    - "sim/render architectural boundary enforced by a standing pytest guard (tests/test_boundary.py), not just code review discipline"
    - "pip bootstrapped via official get-pip.py when the system Python lacks the ensurepip module entirely (deeper than the standard missing-pip case)"

key-files:
  created:
    - pyproject.toml
    - .gitignore
    - src/atc_sim/__init__.py
    - src/atc_sim/sim/__init__.py
    - src/atc_sim/render/__init__.py
    - tests/test_boundary.py
  modified: []

key-decisions:
  - "Used version ranges (pygame-ce>=2.5,<3.0, pydantic>=2.13,<3.0, pytest>=8.0) rather than exact pins so pip's resolver picks the true current release"
  - "Bootstrapped pip via the official PyPA get-pip.py script rather than requiring sudo apt install python3.14-venv, since the sandbox has no non-interactive sudo"

patterns-established:
  - "Boundary guard test: pure-Python text scan (no grep shellout) recursively checking src/atc_sim/sim/*.py for pygame import statements — cross-platform and fast (0.02s)"

requirements-completed: [CORE-03]

coverage:
  - id: D1
    description: "src-layout package skeleton and pyproject.toml with correct script entry point, package-find root, dependency ranges, and pytest config"
    verification:
      - kind: unit
        ref: "python -c 'import tomllib; ...' pyproject validation (Task 1 verify block)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Dependencies installed into venv (pygame-ce, pydantic, pytest) and package importable"
    requirement: "CORE-03"
    verification:
      - kind: unit
        ref: "python -m pip show pygame-ce pydantic pytest && python -c 'import atc_sim, pydantic, pygame'"
        status: pass
    human_judgment: false
  - id: D3
    description: "sim/render boundary guard test enforces CORE-03 (no module under src/atc_sim/sim/ imports pygame)"
    requirement: "CORE-03"
    verification:
      - kind: unit
        ref: "tests/test_boundary.py#test_sim_package_never_imports_pygame"
        status: pass
    human_judgment: false

# Metrics
duration: ~15min (active work; excludes checkpoint pause for human package sign-off)
completed: 2026-07-05
status: complete
---

# Phase 01 Plan 01: Project Scaffold, Dependency Install, Boundary Guard Summary

**src-layout `atc_sim` package with pinned pyproject.toml, a working venv running pygame-ce 2.5.7/pydantic 2.13.4/pytest 9.1.1, and a standing pytest guard enforcing that `src/atc_sim/sim/` never imports pygame.**

## Performance

- **Duration:** ~15 min active execution (Task 1 + checkpoint sign-off + Task 3), spread across a checkpoint pause for human dependency-legitimacy review
- **Started:** 2026-07-04T22:52:11+01:00 (Task 1 commit)
- **Completed:** 2026-07-05T10:23:40+01:00 (Task 3 commit)
- **Tasks:** 3 (2 auto tasks + 1 human-verify checkpoint)
- **Files modified:** 6 (pyproject.toml, .gitignore, 3x `__init__.py`, tests/test_boundary.py)

## Accomplishments
- Scaffolded the src-layout package skeleton (`src/atc_sim/`, `sim/`, `render/`) and `pyproject.toml` with the `atc-sim` console-script entry point, `where=["src"]` package-find root, pinned dependency ranges, and pytest config
- Human sign-off obtained and honored for the three `[SUS]`-flagged (tooling false-positive) dependencies — pygame-ce, pydantic, pytest — before install
- Created `.venv`, bootstrapped pip (system Python 3.14 was missing the `ensurepip` module entirely, not just an unbootstrapped pip — one layer deeper than RESEARCH.md's anticipated case), and editable-installed the package with dev extras
- Confirmed exact resolved versions at install time: pygame-ce 2.5.7, pydantic 2.13.4, pytest 9.1.1 — matching RESEARCH.md's WebSearch-sourced `[ASSUMED]` figures exactly, resolving Open Question #2
- Added `tests/test_boundary.py`, a pure-Python (no grep shellout) recursive scan that fails if any file under `src/atc_sim/sim/` imports pygame — the standing architectural guard for CORE-03 that every later sim module (clock.py, aircraft.py, interpolation.py) must pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Scaffold src-layout package and pyproject.toml** - `1638607` (feat)
2. **Task 2: Package legitimacy sign-off before install** - checkpoint, no commit (human approval only: "approved")
3. **Task 3: Create venv, verify pip, install dependencies, add sim/render boundary guard test** - `166035b` (feat)

**Plan metadata:** commit pending (this SUMMARY.md + STATE.md + ROADMAP.md commit, created next)

## Files Created/Modified
- `pyproject.toml` - Package metadata, pinned dependency ranges, atc-sim script entry point, pytest config
- `.gitignore` - Excludes .venv/, __pycache__/, *.pyc, .pytest_cache/, *.egg-info/, build/, dist/
- `src/atc_sim/__init__.py` - Package marker (empty)
- `src/atc_sim/sim/__init__.py` - Sim sub-package marker (empty) — the headless-boundary-protected package
- `src/atc_sim/render/__init__.py` - Render sub-package marker (empty)
- `tests/test_boundary.py` - CORE-03 boundary guard: fails if src/atc_sim/sim/ imports pygame

## Decisions Made
- Version ranges over exact pins for pygame-ce/pydantic/pytest, per RESEARCH.md Open Questions #2, so pip's resolver picks the current release rather than trusting point-in-time WebSearch figures
- Bootstrapped pip via the official `https://bootstrap.pypa.io/get-pip.py` script inside the venv (using `python -m venv --without-pip` to sidestep the missing `ensurepip` module), rather than requesting `sudo apt install python3.14-venv` — the sandbox has no non-interactive sudo, and get-pip.py is PyPA's own official bootstrap mechanism, not a third-party package

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] System Python lacked the `ensurepip` module entirely, not just an unbootstrapped pip**
- **Found during:** Task 3 (venv creation)
- **Issue:** RESEARCH.md's Open Questions #1 anticipated `python -m ensurepip --upgrade` as the fallback for a venv with pip missing. In this environment, `python3 -m venv .venv` failed outright with "ensurepip is not available" — the `ensurepip` stdlib module isn't installed on this system Python 3.14 at all (would normally require `apt install python3.14-venv`, which needs sudo and this sandbox has no non-interactive sudo access).
- **Fix:** Created the venv with `python3 -m venv --without-pip .venv` (skips the ensurepip bootstrap step), then bootstrapped pip inside the venv using the official PyPA `get-pip.py` script downloaded over HTTPS from `bootstrap.pypa.io`. This is PyPA's own documented bootstrap mechanism for exactly this situation, not a third-party or unverified package, so it does not trigger the package-install legitimacy exclusion in Rule 3.
- **Files modified:** none (environment-only change; `.venv/` is gitignored)
- **Verification:** `.venv/bin/python -m pip --version` succeeded after bootstrap; subsequent `pip install -e ".[dev]"` completed cleanly
- **Committed in:** N/A (no source files changed — venv is a local, gitignored artifact)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary to complete Task 3 at all in this sandboxed environment; no scope creep, no source files touched, environment-only.

## Issues Encountered
- Sandbox has no non-interactive `sudo`, ruling out the `apt install python3.14-venv` system-level fix — resolved via the `--without-pip` + `get-pip.py` approach documented above.

## User Setup Required
None - no external service configuration required. (The checkpoint's human sign-off on package legitimacy was the only manual step, and it was already completed per the continuation context: "approved".)

## Next Phase Readiness
- `.venv` is live with pygame-ce, pydantic, and pytest installed editable; `import atc_sim` works; `python -m pytest -q` runs clean (1 passed, the boundary guard)
- The sim/render boundary guard (`tests/test_boundary.py`) is in place and will fail fast the moment any future sim module (clock.py, aircraft.py, interpolation.py in plans 01-02/01-03) imports pygame — ready to catch CORE-03 regressions from day one
- `atc-sim` console script is registered (resolves once plan 01-05 creates `app.py:main`)
- No blockers for plan 01-02 (sim clock accumulator)

---
*Phase: 01-walking-skeleton-sim-clock-radar-render-loop*
*Completed: 2026-07-05*

## Self-Check: PASSED

All claimed files found on disk (pyproject.toml, .gitignore, src/atc_sim/__init__.py, src/atc_sim/sim/__init__.py, src/atc_sim/render/__init__.py, tests/test_boundary.py) and all claimed commits found in git history (1638607, 166035b).
