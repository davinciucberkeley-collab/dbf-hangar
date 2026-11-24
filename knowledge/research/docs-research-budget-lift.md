---
id: "docs-research-budget-lift"
title: "Budget lift propulsion: cheapest credible motor, ESC and prop"
kind: "research"
morph_cells: ["vtol_method:lift-plus-cruise"]
source_repo: DBF-Combined @ a93f14d
source_files: ["docs/research/budget-lift.md"]
created: 2026-11-23
verified: false
---

## Summary
A 2026-10-13 live price check for the lift rotors of a 5 to 7.5 kg quadplane, replacing a baseline station that cost $134.98 per lift motor, ESC and prop. It compares 4-lift and 8-lift sets by station cost, hover power and ESC headroom, and lists errors found in published thrust tables.

## Key facts
- Cheapest credible set is 4-lift with a 400 KV 3515-class motor at $254.88 for four stations, 53 percent below four of the baseline stations. It reaches thrust-to-weight 2.0 only up to about 6.7 kg MTOW (3.36 kgf per motor) and 1.79 at 7.5 kg. [budget-lift.md verdict]
- Eight-lift costs more than four-lift at these sizes. The best hover efficiency is an 8-lift 3508-class set at about 568 W hover at 6 kg (estimate) against 799 W for the 4-lift pick, but it costs $218 more. [budget-lift.md verdict]
- The cheapest 8-lift set uses 4S motors (1.58 kgf max, T/W 2.0 up to about 6.3 kg), which pushes the rest of the system to 4S and raises pack current about 1.5 times; at $310.56 it is $55.68 above the 6S 4-lift set. [budget-lift.md verdict, caveat 6]
- ESC rule used: a motor with published max current of 25 A or less gets a 35 A ESC ($7.13), otherwise a 45 A ESC ($10.00); hover draws at most 9 A on every candidate, though full-throttle transients reach 28.6 to 30 A on two motors. [budget-lift.md ESC rule, caveat 5]
- None of the BLHeli_S ESCs can park a two-blade prop in line with the flow, so expect extra cruise drag; folding props cost $14 to 16 more per station. [budget-lift.md caveat 4, props]
- Several published thrust tables contain apparent errors (power not equal to voltage times current, out-of-sequence rows, a Kv mismatch), and tested props differ from the priced props by a few percent. [budget-lift.md caveats 1-2]
- Sources cited by DBF-Combined, not opened by this import: SunnySky USA motor tables, Tarot and Flying Tech product pages, T-Motor, iFlight at RobotShop, GetFPV and Amazon listings, Eolo and APC props. [budget-lift.md tables A and B]

## Status in the study
none

## Open questions
- Measure one station's current at 1500 g thrust (4-lift) or 750 g (8-lift); above 230 W per motor for 4-lift (15 percent over the table) the hover endurance is at risk (item M1).
- Check full-throttle current and case temperature after 30 s (over 80 C fails) (M2).
- Measure stopped-prop drag to decide whether folding props are worth the extra cost (M3).
- Shipping, spares and prop hub compatibility for the disc-type motor were not stated.
