---
id: "docs-research-lift-propulsion"
title: "Lift propulsion: motor, prop and ESC candidates"
kind: "research"
morph_cells: ["vtol_method:lift-plus-cruise"]
source_repo: DBF-Combined @ a93f14d
source_files: ["docs/research/lift-propulsion.md"]
created: 2026-11-23
verified: false
---

## Summary
A survey of lift motor, prop and ESC candidates for a lift-plus-cruise VTOL of 8 to 15 kg and a $2,000 budget, with prices and thrust tables read on live pages on 2026-10-13. It sizes 4-lift and 8-lift layouts against a 1.6 thrust-to-weight rule and compares estimated hover electrical power at a 12 kg reference.

## Key facts
- Sizing targets: 4-lift needs 4.0 to 6.0 kgf maximum thrust per motor (MTOW times 1.6 over 4); 8-lift needs 2.0 to 3.0 kgf; hover load is 2.5 to 3.75 kg per motor (4-lift) or 1.25 to 1.9 kg (8-lift). [lift-propulsion.md scope]
- Candidates compared include integrated Hobbywing motor-ESC units, T-Motor Navigator and V-type motors and SunnySky motors, with thrust per watt read from published tables near hover (for example 8.5 g/W at about 3.1 kg for a 6S 22 in folding-prop unit, and 10.2 g/W for a 12S 24 in unit). [lift-propulsion.md tables A and B]
- Estimated hover electrical power at the 12 kg reference runs from about 1.17 kW (12S, 24 in props, 4-lift) to about 2.06 kW (12S, 15 in props, 8-lift); the best 8-lift options are near 1.28 to 1.33 kW. [lift-propulsion.md hover-power comparison]
- Published tables are usually measured at 23 to 25 V and 9 to 25 C, with prop lock or park alignment not provided by most ESCs; one integrated unit uses folding props. [lift-propulsion.md tables A and B]
- Sources cited by DBF-Combined, not opened by this import: Hobbywing product page, T-Motor and LigPower store pages, BuddyRC SunnySky page, with stock and ship-from noted per row. [lift-propulsion.md thrust-table excerpts]

## Status in the study
none

## Open questions
- Hover power figures are estimates interpolated from the maker tables, not measured.
- Several rows lack a listed price or stock status because pages did not show them.
- Prop park alignment in cruise is not solved by any ESC listed.
