---
id: std-u171-p6-mst-margin-notes
title: Allowable Stresses and Loads (university lecture notes, sections "Margin of safety" and "Factor of safety, n")
authors: not found (page hosted under a course directory at web.mst.edu; no author named on the page read)
year: not found
url: https://web.mst.edu/jthomas/classes/2210/concepts/04/allowable/index.html
type: website
retrieved: 2026-11-25
verified: true
---

## Summary
Opened a university course lecture-notes page on allowable stresses and loads. It defines the margin of safety as (n - 1) x 100, where n is the factor of safety, and says a structure presumably fails when the margin is less than or equal to zero, and for n less than 1. The page does not use the term reserve factor. The wording on the boundary is not fully consistent (margin "less than or equal to zero" against n "less than 1"), which is reported in the values table.

## Usable rules / numbers
- [joint_rf_min] Margin of safety = (n - 1) x 100, usually given as a percent; n is the factor of safety (section "Margin of safety", read 2026-11-25). Kind: definition.
- [joint_rf_min] "Structure will presumably fail for margins of safety less than or equal to zero" (section "Margin of safety"): this reads as a boundary above 1.0 in n.
- [joint_rf_min] "Structure will presumably fail for n less than 1" (section "Factor of safety, n"): this reads as a boundary at 1.0 in n.
- [joint_rf_min] Limit and ultimate are not separated in the margin definition on this page (same section).

## How we could use it
- Feeds `joint_rf_min` as a definition of margin in terms of a factor of safety n; n is not named RF on this page, so the mapping to reserve factor is the reader's.
- The two boundary statements differ in whether n = 1.0 is acceptable; reported, not resolved.
