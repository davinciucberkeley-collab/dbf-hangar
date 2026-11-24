---
id: "docs-research-configurations"
title: "VTOL configuration survey and trade study"
kind: "research"
morph_cells: ["vtol_method:lift-plus-cruise", "vtol_method:tailsitter", "vtol_method:tiltrotor", "vtol_method:tiltwing", "lift:box-wing"]
source_repo: DBF-Combined @ a93f14d
source_files: ["docs/research/configurations.md"]
created: 2026-11-23
verified: false
---

## Summary
A literature survey plus a 29-variant scored trade study of small electric VTOL layouts, read on 2026-10-21 and re-run on v0.4 inputs on 2026-10-25. Lift-plus-cruise C0 stays the recommendation among layouts that keep stopped lift rotors, while a quad tailsitter scores higher but breaks that requirement. The cells listed are the layouts the file discusses; the box-wing cell is approximate because the file treats a box-wing quadplane only as one variant.

## Key facts
- Current v0.4 ranking of feasible lift-plus-cruise variants: C0-lean 6.04 out of 10, C0 with a 3.0 m span 6.01, C0 baseline 5.86. What moves forward is C0 as specified in v0.4, not the lean variant, because the lean variant leads mostly by omitting the airspeed sensor that stall tests and transition margins rely on. [configurations.md current results]
- Tailsitters rank higher (quad tailsitter 7.35, twin-motor 6.30) but break requirement R1 (stopped lift rotors), need about 30 degrees of tilt to hold position in an 8 m/s gust against 9 degrees for C0, and have no motor-out tolerance. [configurations.md verdict]
- All remaining alternatives (eight lift rotors, a coaxial X8, box and tandem wings, tilt-quad and bicopter layouts, tilt-wing, big packs) exceed the $2,000 cap; the tilt-tricopter is within it but fails the thrust-to-weight limit of 1.6 (it has 1.59). [configurations.md verdict, 2.3]
- Largest design lever found: stopped lift-propeller drag is about 40 percent of C0's parasite drag (0.0237 of 0.059, using an estimated drag area of 0.0034 m2 per rotor). At 1.5 times that value cruise falls to 10.1 min, and at 2 times to 8.8 min, which fails R10. [configurations.md verdict, 2.4]
- Folding props might cut that drag by half (an estimate) and raise cruise to 14.3 min but cost about $94 more before tax, fitting under the cap only with the lean bill of materials. [configurations.md verdict, 2.5 item 1]
- Span trade: 2.8 to 3.0 m costs nothing and adds 0.7 to 0.9 min of cruise but the joiner reserve factor, scaled from the baseline 1.85, falls to 1.61 and 1.51 respectively; at 3.0 m the wing halves reach the 1.5 m length limit. [configurations.md 2.5 item 2]
- Sources cited by DBF-Combined, not opened by this import: Brazinskas et al. (Aerospace 2016, overlapping rotors), UIUC Propeller Data Site, Silva et al. (NASA, AIAA 2018, VTOL concept vehicles), Fredericks et al. (GL-10), Kasliwal et al. (Nature Communications 2019), ArduPilot QuadPlane frame-setup and weathervaning pages, PX4 VTOL frames overview, BETA Technologies ALIA. [configurations.md section 8]

## Status in the study
none

## Open questions
- Stopped-prop drag is the least-known input; the source says to measure it before the pack and prop order is frozen.
- Tailsitter, tilt and box-wing performance factors are tagged EST (engineering estimates) in the source.
- Some tilt-rotor and tailsitter claims rest on search snippets marked unverified in the source.
- Whether to change requirement R1 is explicitly left undecided by the study.
