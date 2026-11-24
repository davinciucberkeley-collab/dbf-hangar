---
id: "docs-research-stall-margin"
title: "Stall-margin policy trade: C0 (v0.4)"
kind: "research"
morph_cells: ["vtol_method:lift-plus-cruise"]
source_repo: DBF-Combined @ a93f14d
source_files: ["docs/research/stall-margin.md"]
created: 2026-11-23
verified: false
---

## Summary
A trade study dated 2026-10-25 and adopted the same day that asks how much stall margin the C0 wing needs against requirement R11 (stall at or below 12 m/s). It found the baseline wing had no margin, compared design stall targets of 12.00, 11.75, 11.50 and 11.25 m/s with the pack re-picked by the sizing rule, and recommended 11.75 m/s. A note says the current adopted design has since grown to a larger wing and MTOW.

## Key facts
- The baseline wing predicts stall at exactly 12.00 m/s. If the true trimmed maximum lift coefficient is 5, 10 or 15 percent lower, stall becomes 12.31, 12.65 or 13.02 m/s and R11 fails in every case. [stall-margin.md verdict, section 3]
- Recommended: design stall target 11.75 m/s (4.1 percent lift-coefficient margin), at no cost, keeping the pack and the $103.21 reserve; it adds 88 g and shortens cruise from 12.92 min to 12.35 min, which stays over the 11.5 min floor. [stall-margin.md verdict]
- A 11.5 m/s target is possible but cruise falls to 11.75 min, a single foam sheet can no longer supply a spare set of panels, a printed plate no longer fits a 256 mm bed, and aileron hinge moment rises 26 percent. [stall-margin.md verdict]
- The 11.25 m/s target is ruled out: on the baseline pack cruise shrinks to 11.07 min, the picker moves to a larger pack and the reserve drops to $35.96, failing the $100 reserve rule. [stall-margin.md verdict]
- With a lift-coefficient shortfall of 5 percent or more the transition minimum airspeed needs to rise from 16 to 17 m/s (1.3 times stall), and the maximum should be at least 1.5 times the minimum. [stall-margin.md section 3]
- Uncertainty in the lift coefficient: the 2-D value 1.30 adopted from wind-tunnel data sits between XFOIL (+5 percent) and NeuralFoil (-1.5 percent); the adopted 3-D estimate 1.121 is the lower of two trimmed estimates. [stall-margin.md section 3]
- The study also tabulates wing area, chord, aspect ratio, hover and cruise power, static margin, joiner and boom reserve factors and foam fit for each target. [stall-margin.md section 2]

## Status in the study
none

## Open questions
- Structural reserve factors are scaled from earlier results and the finite-element analysis was not re-run.
- The neutral-point shift with the larger chord is assumed to follow the same trend as the lattice-model result and was not re-run.
- The source specifies a measured-stall rule as a backstop in its section 5, which this import did not summarise.
