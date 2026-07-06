---
status: testing
phase: 03-aircraft-performance-flight-phase-fsm-procedure-following
source: [03-VERIFICATION.md]
started: 2026-07-06T19:21:01Z
updated: 2026-07-06T19:21:01Z
---

## Current Test

number: 1
name: Literal on-screen visual sign-off of the full demo loop
expected: |
  Launch `python -m atc_sim.app` (or the installed `atc-sim` entry point) on a machine
  with a real display; watch at least one full departure cycle, one full arrival cycle,
  and one automatic loop restart.

  All five ROADMAP success criteria are visually confirmed:
  - Type-differentiated climb/descent/turn behavior across aircraft
  - Departure: taxi-dot -> departure roll -> climb-out along the OLNEY 2B SID
  - Arrival: airborne-at-DET -> continuous descent (no level-then-snap) along the
    DET 2A STAR -> land -> taxi-in
  - Legal/continuous phase transitions with no teleports
  - Automatic respawn of a fresh departure+arrival pair once both aircraft are gone
awaiting: user response

## Tests

### 1. Literal on-screen visual sign-off of the full demo loop
expected: See above — full departure + arrival + auto-loop-restart cycle, all 5 ROADMAP success criteria visually confirmed
result: [pending]

## Summary

total: 1
passed: 0
issues: 0
pending: 1
skipped: 0
blocked: 0

## Gaps
