---
id: "research-flight-control"
title: "Research findings: flight-control"
kind: "research"
morph_cells: ["vtol_method:lift-plus-cruise", "vtol_method:tailsitter", "vtol_method:tiltrotor", "vtol_method:tiltwing"]
source_repo: DBF-Combined @ a93f14d
source_files: ["redesign/config-study/research/flight-control/FINDINGS.md"]
created: 2026-11-21
verified: false
---

## Summary
A ranking of the layouts by control risk for a first-time team, lowest risk first, with a flight-controller recommendation and an avionics cost. The file calls itself a recovered summary, and its ranking is the summary's own judgement from autopilot documentation and forum reports. The layouts ranked cover lift-plus-cruise, tilt-tricopter and tilt-quad, tailsitters and tilt-wing.

## Key facts
- The ranking, lowest control risk first, is: lift-plus-cruise, tilt-tricopter, quad tailsitter, quad tiltrotor, dual vectored tailsitter, dual non-vectored tailsitter, tilt-wing. [FINDINGS.md, numbered ranking]
- Lift-plus-cruise is called the easiest to control in the PX4 documentation and is ArduPilot's default simulation frame. [FINDINGS.md, ranking item 1]
- The recommended flight controller is an H7 board (Matek H743-WING V3 at about $125, or Pixhawk 6C Mini at about $177), not an F405, which has 1 MB flash and no Lua. [FINDINGS.md, hardware paragraph]
- An airspeed sensor (about $47 to $75) and a GPS (about $48) are added, and the core avionics come to about $220 to $272. [FINDINGS.md, hardware paragraph]
- The file recommends ArduPilot Plane as the autopilot. [FINDINGS.md, closing line]

## Status in the study
none

## Open questions
- The file header says its claims are UNVERIFIED unless a card cites them. [FINDINGS.md, header note]
- The ranking scores are the summary's own, not a sourced figure. [FINDINGS.md, opening line]
