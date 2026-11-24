---
id: "docs-research-electrical-architecture"
title: "Electrical architecture (C0 lift + cruise)"
kind: "research"
morph_cells: ["vtol_method:lift-plus-cruise"]
source_repo: DBF-Combined @ a93f14d
source_files: ["docs/research/electrical-architecture.md"]
created: 2026-11-23
verified: false
---

## Summary
The wiring concept for the C0 lift-plus-cruise aircraft, dated 2026-10-19: power tree, signal tree, flight-controller output and serial map, power budget, wire and connector choices, arming and kill, harness segmentation, test plan and a landing-wheel proposal. Placements and wire lengths are estimates, and the file flags several unresolved risks rather than closing them.

## Key facts
- Power path: the 6S pack (nominal 22.2 V, 25.2 V when full) feeds through an anti-spark XT90S plug (the physical disconnect of requirement R20), the flight-controller power board with a 90 A continuous current sensor, then a star splice feeding five 12 AWG ESC branches. A separate regulator powers the Remote ID module so a servo brownout cannot silence it. [electrical-architecture.md sections 1, 7]
- Output map: lift motors on outputs 1 to 4 (DShot, ArduPilot functions 33 to 36), pusher on output 5 (function 70), servos on outputs 8 to 12 so analog servo timing never shares a timer group with DShot. [electrical-architecture.md section 3]
- Current budget: 37.5 A hover, 16.5 A pusher cruise, 74.4 A transition peak, and 110.8 to 133.2 A if all four lift motors run full throttle. The worst case is 1.48 times the 90 A sensor rating and each motor exceeds its 26 A, 30 s limit. [electrical-architecture.md section 4]
- Wire gauge: the 10 AWG trunk carries 74.4 A during transition and as much as 133.2 A with all lift motors at full throttle, beyond the 52 A tabulated for that gauge; the XT90S plug is rated 50 A continuous by one source and 90 A by another, so the transition current exceeds the lower figure by 1.49 times. [electrical-architecture.md sections 3 (risk R-D), 5]
- Landing wheels (3 in, about 124 g added) raise the ground line 0.048 m, increase pusher disc clearance from 36 to 84 mm and lower the tip-back angle from 57.9 to 52.6 degrees; the axle offset is an estimate. [electrical-architecture.md section 11]
- Harness is split into six joint boxes with plug pairs so the wing, booms and pod separate without cutting wire (requirement R4). [electrical-architecture.md section 8]
- Sources cited by DBF-Combined, not opened by this import: ArduPilot QuadPlane frame-setup and RC output mapping pages, the Engineering Toolbox AWG table, an esk8 connector wiki, a Maker Store XT90S listing, Oscar Liang's SpeedyBee F405 Wing page, Gator RC wheel listing. [electrical-architecture.md sections 3, 5, 6, 11]

## Status in the study
none

## Open questions
- Risk R-A: DShot on the pusher output rests on forum sources and must be bench-verified (fallback is PWM throttle with calibration).
- Risk R-B: output 12 conflicts with the LED function on the board; fallback is a Y-lead for both rudders.
- Risk R-C to R-F: board input voltage range, XT90S rating, servo supply pinout and small JR-connector contact heating are unresolved.
- Unknowns marked as not available: ESC dimensions and mass, motor lead gauge, GPS compass chip, receiver current, axle thread size.
