---
id: "docs-research-hardware-spec"
title: "Hardware and tolerance specification: C0 (v0.3.1)"
kind: "research"
morph_cells: ["vtol_method:lift-plus-cruise"]
source_repo: DBF-Combined @ a93f14d
source_files: ["docs/research/hardware-spec.md"]
created: 2026-11-23
verified: false
---

## Summary
A draft hardware and tolerance specification for the C0 v0.3.1 CAD, dated 2026-10-21, covering every joint and attached component with fastener, hole geometry, stack-up, fit and torque, plus the CAD changes the joints imply. One thread size (M3) does almost everything, and the motor maker's drawing sets the critical numbers. It was later refined by the hardware schedule and tolerance analysis files.

## Key facts
- The design uses 103 M3 stainless screws in nine lengths, 67 heat-set inserts, 8 nylon-insert nuts and two M5 wing bolts, with M2 only at servos and horns; no tapped holes, so metal threads exist only inside the motors. [hardware-spec.md verdict]
- The lift-motor base allows a maximum thread depth of 3.3 mm, so an 8 mm M3 screw through a 4.5 mm plate floor and 0.5 mm washer engages about 3.0 mm (2.8 to 3.2 over tolerances). [hardware-spec.md verdict, joint J01]
- The purchased screw kit does not fit the design (button heads in four short lengths, no nylocks, no 25 to 40 mm screws); replacing it with a $22.38 fastener-supplier order, heat-set inserts and a threadlocker raises goods by $15.08 and leaves a reserve of $75.45, below the $100 target. [hardware-spec.md verdict]
- Six CAD changes are needed, the largest being a split motor mount (screws cannot reach the motor base past the boom) and a 60 mm overlap between the front boom and rear stub. [hardware-spec.md verdict]
- Tube tolerances from the vendors turn the 0.23 mm nominal joiner fit into a range of -0.08 to +0.53 mm, so the joiner can bind; measure on receipt. [hardware-spec.md verdict]
- Torque without a driver: hang a known mass from a hex key (0.6 N m at a 60 mm arm needs about 1.02 kg). Threadlocker is for metal-to-metal threads only and never on plastics, nylocks or carbon-nylon. [hardware-spec.md section 2d]
- Printing rules: holes printed vertically come out small (compensate roughly 0.2 mm on a 4 mm hole), horizontal cross-bolt holes are modelled as teardrops, and the iron for heat-set inserts runs about 20 C above print temperature. [hardware-spec.md section 2b, 2c]
- Sources cited by DBF-Combined, not opened by this import: SunnySky X4110S drawing, Bolt Depot product data, an Albany County Fasteners ISO 273 chart, pollen.am hole-design guide, JLC3DP and CNC Kitchen insert guidance, Loctite 242 and 243 data sheets. [hardware-spec.md sections 1-2]

## Status in the study
none

## Open questions
- Torque values are engineering estimates, and a torque driver is assumed to be unavailable.
- Hub thickness for the prop screws and the pusher prop torque are not published.
- Measure the joiner and spar tubes on receipt (source item M1) before relying on the fit.
