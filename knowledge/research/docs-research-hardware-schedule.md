---
id: "docs-research-hardware-schedule"
title: "Hardware schedule: every fastener and small mechanical part"
kind: "research"
morph_cells: ["vtol_method:lift-plus-cruise"]
source_repo: DBF-Combined @ a93f14d
source_files: ["docs/research/hardware-schedule.md"]
created: 2026-11-23
verified: false
---

## Summary
A joint-by-joint schedule of every fastener and small mechanical part of the C0 aircraft, dated 2026-11-01: 31 joints, 128 items and 563 pieces, with the tool for each joint, a transport and field assembly order, a motor-screw engagement check, linkage geometry, design findings and five new purchase lines. Dimensions that the CAD or vendor pages do not publish are marked as estimates.

## Key facts
- Coverage by source: 386 pieces from the purchased kit, 44 supplied with parts, 33 printed parts, 16 wheel items and 82 new pieces. By kind: 173 screws, 138 washers, 75 heat-set inserts, 52 nuts, 33 ties and 37 printed plates or blocks. [hardware-schedule.md section 1]
- Field assembly takes 26 hex-key fasteners plus 6 joint boxes, about 12 min (estimated, not timed) against the 15 min target of requirement R5; two pinch bolts per clamp instead of four would save about 2.7 min. Transport pieces stay within the 1.5 by 0.5 by 0.4 m envelope of R4 (largest piece 1.41 m). [hardware-schedule.md section 3]
- Motor screw engagement is only about 3.4 mm (about 1.1 screw diameters) for both the lift motors and the pusher, because screws enter from the bore side; the actual base thickness and thread depth are unpublished. [hardware-schedule.md section 4]
- Design findings: the wing bolt cannot retain the wing panels as drawn (it sits inside the saddle), the boom splice has 60 mm of overlap, the rear clamp is foam-only and carries about a 111 N couple per boom, and one servo drives a 0.855 m elevator with no torque rod. [hardware-schedule.md section 6]
- Linkage: aileron, elevator and rudder horn radii, rod lengths and servo throws are planar-solve estimates; surface throws are asymmetric because the rod is not perpendicular at neutral. [hardware-schedule.md section 5]
- Required new goods cost $13.62 ($15.02 with tax) before shipping, reducing the budget reserve from $44.26 to $29.24. [hardware-schedule.md section 7]

## Status in the study
none

## Open questions
- Screw lengths in the purchased kit are unknown because its page was closed to robots, so 20, 30 and 40 mm M3 lengths are bought as new lines.
- Servo ear spacing, arm length and the wheel axle head are estimates.
- The rudder servo body touches the boom and also pushes roughly 2.5 mm into the underside of the elevator; lowering it 3 mm or moving it aft 25 mm is suggested, not decided.
- Time the first build to replace the estimated assembly time.
