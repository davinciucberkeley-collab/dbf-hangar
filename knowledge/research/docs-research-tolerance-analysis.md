---
id: "docs-research-tolerance-analysis"
title: "Tolerance analysis: 3D-printed parts and every fit they take part in"
kind: "research"
morph_cells: []
source_repo: DBF-Combined @ a93f14d
source_files: ["docs/research/tolerance-analysis.md"]
created: 2026-11-23
verified: false
---

## Summary
A 2026-11-01 analysis of the dimensional fits of the printed hardware in the C0 aircraft, assuming a Prusa MK4S-class printer (the repo does not name the printer). It concludes the printed hardware as drawn will not assemble on the first try: six fits fail, five are borderline, and three tolerance stack-ups need corrective action. No morphological cell applies because the file is about manufacturing fits, not configuration.

## Key facts
- Carbon and aluminium tube tolerance is much coarser than machined fits: a nominal 25.4 mm tube spans 25.197 to 25.603 mm, which is a coarse IT13-class tolerance (330 micrometres) against 21 micrometres for a standard grade-7 fit at 22 mm. The real tube lots must be measured. [tolerance-analysis.md section 2]
- Clamp default of a 25.4 plus 0.2 mm CAD bore prints at 25.30 to 25.55 mm, so the clamp halves bottom out on the smallest tube; the fix is a bore of 25.0 mm (or measured diameter minus 0.22 mm) with the split plane up. [tolerance-analysis.md section 5, 7]
- Clamp preload: a 0.25 N m torque on an M3 bolt gives about 417 N and 13.7 MPa under the washer (21.9 MPa at 0.4 N m); printed PETG relaxes about 2 percent after 1 hour, 12 percent after 1 day, 30 percent after 1 week and 50 percent after 30 days (extrapolated beyond the 22 h tested). [tolerance-analysis.md section 5]
- A heat-set insert in printed PLA resists roughly 1400 N of pull-out; insert bores should be 4.0 to 4.2 mm, 7.5 mm deep. [tolerance-analysis.md sections 5, 7]
- CAD changes listed: ten items covering clamp bores, saddle hole, insert bores, nut pockets, motor-mount screw pockets, tail tab slot, elevator hinge gap, axle block, splice plug and placeholder patterns. [tolerance-analysis.md section 7]
- Calibration coupons are printed first in PETG (about 90 min, estimated), then on the real tubes, then repeated in carbon-nylon. [tolerance-analysis.md section 8]
- Sources cited by DBF-Combined, not opened by this import: Smith's dimensional-accuracy page, CNC Kitchen on heat-set insert data, a University of Florida makerspace tolerance guide, a PETG creep paper, and other items keyed S1 to S13. [tolerance-analysis.md section 9]

## Status in the study
none

## Open questions
- The printer is assumed, and process capability numbers are assumed values.
- Motor 19 mm square hole pattern and servo ear pitch are placeholders to measure before cutting.
- The creep time unit is assumed to be seconds (estimate).
- Measure each tube lot, the clamp free gap (below 0.15 mm does not grip), bolt torque after 24 h and 7 days (over 30 percent loss means moving to carbon-nylon clamps), and receipt dimensions for hubs and patterns.
