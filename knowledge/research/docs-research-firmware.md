---
id: "docs-research-firmware"
title: "Flight software: sources, design decisions, and changes the review must take"
kind: "research"
morph_cells: ["vtol_method:lift-plus-cruise"]
source_repo: DBF-Combined @ a93f14d
source_files: ["docs/research/firmware.md"]
created: 2026-11-23
verified: false
---

## Summary
Flight-software research for the C0 lift-plus-cruise aircraft, checked 2026-10-21 with a revision on 2026-11-01. It confirms the board and ArduPilot firmware target, then records thirteen design decisions behind the parameter file, from frame and output map through ESC protocol, tuning, failsafes and telemetry. Simulator runs passed all seven scripted scenarios.

## Key facts
- The board maps to the ArduPilot target CoreWingF405WingV2, which the stable Plane 4.7.2 release includes, so the earlier "beta-only" risk is closed. The build has DShot on outputs 1 to 10 and no Lua scripting. [firmware.md section 1, D1]
- Frame is Quad X (class 1, type 1). Output map puts lift motors on outputs 5 to 8, the pusher on 9 and servos away from every DShot timer group, because DShot forces a whole group. [firmware.md D2, D3]
- ESC protocol is DShot150 for lift motors and pusher, chosen for long signal leads and because it needs no calibration. [firmware.md D5]
- Airspeed: revised on 2026-11-01 to a 4525-class sensor with airspeed type 1, whose probed addresses do not collide with the board barometer, so no address strap is needed. [firmware.md D4]
- Current limiting: the only in-build limiter cuts lift-motor throttle only, so a 60 A cap would remove lift during transition. The chosen value is 85 A as a fault guard, under the 90 A sensor rating, with transition current trimmed through the maximum takeoff throttle. [firmware.md D7]
- Two-stage battery failsafe: low stage at 30 percent (1950 mAh) or 21.0 V sag-compensated returns to home and lands vertically; critical stage at 20 percent (1300 mAh) or 19.8 V lands in place. Geofence is 110 m above home, 12 m under the 400 ft limit. [firmware.md D9, D10]
- No telemetry radio is budgeted; three zero-cost options are listed (CRSF telemetry, ExpressLRS MAVLink mode, a WiFi module on the ground), and a receiver cannot run CRSF and MAVLink at once. [firmware.md D12]
- Sources cited by DBF-Combined, not opened by this import: ArduPilot hwdef and firmware server, ArduPilot Plane docs (QuadPlane frame, transitions, tuning, DShot, failsafe, notch filtering), Holybro, RadioMaster, RaceDayQuads, ExpressLRS, Bluejay, Mission Planner. [firmware.md section 2]

## Status in the study
none

## Open questions
- Tuning values for 17 inch props are interpolated starting points and the first-flight tuning must confirm them.
- Cell voltages for the failsafe stages (3.5 V and 3.3 V) are estimates.
- Final current-limit numbers depend on the pack burst test named in the source's review.
- Whether the hover-phase overlay should land in place or return is a documented choice, not a verified one.
