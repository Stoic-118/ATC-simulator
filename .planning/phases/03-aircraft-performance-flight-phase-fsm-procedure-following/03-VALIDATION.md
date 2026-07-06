---
phase: 3
slug: aircraft-performance-flight-phase-fsm-procedure-following
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-06
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (already configured, `pyproject.toml` `[tool.pytest.ini_options] testpaths = ["tests"]`) |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-TBD | TBD | TBD | PERF-01 | — | N/A | unit | `pytest tests/test_performance.py -x` | ❌ W0 | ⬜ pending |
| 03-TBD | TBD | TBD | PERF-02 | — | N/A | unit | `pytest tests/test_phase_fsm.py -x` | ❌ W0 | ⬜ pending |
| 03-TBD | TBD | TBD | PERF-03 | — | N/A | integration | `pytest tests/test_departure_flow.py -x` | ❌ W0 | ⬜ pending |
| 03-TBD | TBD | TBD | PERF-04 | — | N/A | integration | `pytest tests/test_arrival_flow.py -x` | ❌ W0 | ⬜ pending |
| 03-TBD | TBD | TBD | PROC-01 | — | N/A | unit | `pytest tests/test_procedure_following.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky — Task IDs/Plan/Wave columns are populated by the planner once PLAN.md files exist; the Req→Test mapping above is fixed by research.*

---

## Wave 0 Requirements

- [ ] `tests/test_performance.py` — stubs for PERF-01 (distinct climb/descent/terminal-speed/bank values per `FLEET` profile; `turn_rate_deg_per_sec()` varies by speed at fixed bank)
- [ ] `tests/test_phase_fsm.py` — stubs for PERF-02 (`LEGAL_TRANSITIONS` covers all 8 phases; `transition_to()` raises on illegal transitions; full linear TAXI_OUT→...→TAXI_IN walk succeeds)
- [ ] `tests/test_procedure_following.py` — stubs for PROC-01 (`compute_target()` on DET STAR's LOFFO leg descends toward ABBOT's FL080 rather than holding level; `advance_leg_if_reached()` increments `leg_index`)
- [ ] `tests/test_departure_flow.py` — stubs for PERF-03 (headless departure aircraft visits TAXI_OUT→DEPARTURE_ROLL→CLIMB→ENROUTE in order, removed once OLNEY 2B SID legs exhaust)
- [ ] `tests/test_arrival_flow.py` — stubs for PERF-04 (headless arrival aircraft spawns in DESCENT at FL170, visits DESCENT→APPROACH→LANDED→TAXI_IN in order, removed after TAXI_IN timer)
- [ ] `tests/conftest.py` shared fixture — a headless "step N sim ticks and record the phase sequence observed" test harness reused by both flow tests, to avoid duplication

*(Framework itself needs no new install — pytest 8.x already present, no config changes needed.)*

---

## Manual-Only Verifications

*All phase behaviors have automated verification per the Req→Test map above. The one genuinely visual criterion — success criterion #1's "visibly differentiated during flight" and #4's "observable, never-skipped phase transitions" — is additionally confirmed by running the app and watching the demo loop, per this project's `human_verify_mode: end-of-phase` config, but has an automated proxy (test_performance.py, test_phase_fsm.py) so it is not manual-only.*

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Full departure+arrival demo loop is visually continuous (taxi-visible per D-05, loops per D-03) | PERF-03, PERF-04 | End-of-phase human sign-off convention (`workflow.human_verify_mode: end-of-phase`) for whole-loop visual review, on top of automated flow tests | Run the app, watch one full departure and one full arrival cycle, confirm taxi dot visible and demo restarts automatically |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
