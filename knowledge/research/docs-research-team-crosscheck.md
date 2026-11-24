---
id: "docs-research-team-crosscheck"
title: "Cross-check against the team's DBF-VTOL repository"
kind: "research"
morph_cells: ["vtol_method:lift-plus-cruise"]
source_repo: DBF-Combined @ a93f14d
source_files: ["docs/research/team-crosscheck.md"]
created: 2026-11-23
verified: false
---

## Summary
A 2026-11-03 comparison of findings in the team's separate DBF-VTOL repository (built on the older v0.3.1 design) with the current v0.4.0 design, re-sourcing every number. Four findings still apply, a fifth applies in part, six are already covered by a different fix and two team resources are linked rather than copied. The file records the CAD fix for the first finding in detail.

## Key facts
- X1, battery sealed in the pod: a 35 mm layer of solid foam covered the whole pack, between the top of its bay and the canopy pocket, and the bay was only 5 mm longer than the pack while the build manual trims CG by sliding it 30 mm. Fix: an access well, a 225 mm bay and a 220 mm tray; the pack then passes through the hatch with about 2.5 mm a side at the tight end. [team-crosscheck.md section 2.1]
- The rebuild changes CG by only about 0.12 mm forward against a plus or minus 3.3 mm window, and adds no new part interference. [team-crosscheck.md section 2.1a]
- X2, servo stall current: five servos stalling at once draw 12.5 A (2.5 A each at 6 V) against an 8 A continuous, 14 A peak servo supply; the wiring list had assumed 1.5 A each and was corrected; bench test passes under 8 A sustained and 14 A peak. [team-crosscheck.md section 2.2]
- X3, lift motor over rating: one motor at full throttle draws 27.7 A against a 26 A, 30 s rating, and the total-current cap does not protect individual motors; action is to find the throttle fraction at 26 A on the thrust stand and set the spin-max parameter to it if lower. [team-crosscheck.md section 2.3]
- X4, printed PETG clamp preload relaxing over days leads to a re-torque rule; X5, power trunk near the GPS compass leads to a compass-motor calibration step. [team-crosscheck.md verdict table]
- Sources cited by DBF-Combined, not opened by this import: the team's DBF-VTOL repository at commit 77913e9, a 3DXR servo product page, a ReadyMadeRC motor page. [team-crosscheck.md sections 1, 2.2, 2.3]

## Status in the study
none

## Open questions
- The sizing result frozen on 2026-11-01 was not re-run after the CAD change.
- Compass-interference field strength at the GPS position is estimated, not measured.
- A separate 6 V servo supply is needed if the servo stall bench test fails.
