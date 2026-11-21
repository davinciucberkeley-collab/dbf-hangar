---
id: print-sequence
title: Print Sequence
topic: print-sequence
source_repo: DBF-Combined @ a93f14d
source_rows: [G3#7]
created: 2026-11-21
verified: false
---

## Purpose
The order in which the 3D-printed parts are printed. Run at the start of each print run.

## Steps
1. Print the jigs first [G3#7]
2. Print FIN-003, FIN-004, FIN-008, FIN-010 and the WNG parts next [G3#7]
3. Print the rest of the parts [G3#7]
4. Print the held parts last [G3#7]

## Checks and stop conditions
- none

## Notes
- The source sorts parts by prefix with order keys 0, 1, 2 and 3 [G3#7]
