---
id: std-u171-p6-spaircraft-lg-tipback
title: Landing Gear Model (spaircraft software documentation page, sections on tip-back and lateral overturn)
authors: not found (documentation site of the spaircraft model; cites Raymer 1992 and Chai 1996)
year: not found
url: https://spaircraft.readthedocs.io/en/docs/lg.html
type: website
retrieved: 2026-11-25
verified: true
---

## Summary
Opened the landing gear model documentation page. It gives a longitudinal tip-back angle of 15 degrees measured from the vertical and a lateral overturn angle of no more than 63 degrees, both attributed to Raymer (1992) with no edition, page or section. It defines the lateral angle through a geometry formula, which is not used here. This is a secondary summary of a textbook, not the textbook itself, and the page does not state a date.

## Usable rules / numbers
- [tip_angle_max_deg] Longitudinal tip-back angle 15 degrees, measured from vertical; the page says the tip-back line must be at least 15 degrees from vertical (section "Tip-back (longitudinal tip-over) angle", read 2026-11-25). Kind as stated by this page: minimum. The lecture source (std-u171-p6-gear-lecture-tipover) states the same 15 as a maximum; both are reported, not resolved.
- [tip_angle_max_deg] Lateral overturn angle psi no larger than 63 degrees (section "Lateral overturn", citing Raymer 1992 for the 63 degree limit). Different axis from the key; not compared. The lecture gives about 55 degrees for the same quantity, which differs and is reported.
- [tip_angle_max_deg] Lateral geometry given as tan psi = (z_CG + l_m) / (dx_n sin delta), with tan delta = y_m / B (same section). Not used.

## How we could use it
- Feeds `tip_angle_max_deg` as a second source for the 15 degree tip-back figure, with the stated kind differing from the lecture (minimum here, maximum there).
- Its 63 degree lateral figure differs from the lecture's 55 degrees; not used for the key.
