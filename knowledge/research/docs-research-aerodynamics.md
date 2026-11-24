---
id: "docs-research-aerodynamics"
title: "Aerodynamics: section polars, whole-aircraft VLM, drag build-up and 2-D RANS CFD (C0, v0.3.1 analysis, updated for v0.4)"
kind: "research"
morph_cells: ["lift:fixed-wing", "vtol_method:lift-plus-cruise", "tail:conventional"]
source_repo: DBF-Combined @ a93f14d
source_files: ["docs/research/aerodynamics.md"]
created: 2026-11-23
verified: false
---

## Summary
An aerodynamic study of the C0 baseline, a twin-boom quadplane with four lift rotors, a pusher and a NACA 2415 wing. It combines XFOIL and NeuralFoil section polars, an AVL whole-aircraft lattice model, a component drag build-up and a 2-D RANS cross-check. In the v0.3.1 geometry the bare round landing legs caused the drag and endurance miss (9.1 min against 10 min), while the stall miss (12.4 m/s against 12) came from a trimmed CL_max of 1.13 against the 1.2 assumed in sizing; the source rates stall as at risk rather than failed. The v0.4 redesign, with faired legs and a wing re-sized on the trimmed CL_max, closes both. The tail is a conventional twin-fin H-tail, so the tail cell is the closest fit.

## Key facts
- v0.3.1 (MTOW 6.182 kg, wing span 2.4 m, area 0.5728 m2): trimmed 3-D CL_max is 1.13 against 1.2 assumed in sizing, which gives a stall speed of 12.4 m/s against the 12 m/s limit of requirement R11. [aerodynamics.md verdict table, section 5]
- v0.3.1 total parasite drag coefficient is 0.081 against 0.059 assumed; the four bare round legs (25.4 mm tubes) alone add 0.036. Cruise at 20 m/s then needs 479 W and lasts 9.1 min, below the 10 min of R10; with faired legs (estimate) it is 299 W and 14.6 min. [aerodynamics.md sections 7-8]
- v0.4 values: wing area 0.682 m2, chord 284.2 mm, aspect ratio 8.45, MTOW 6.552 kg, trimmed CL_max 1.114, stall 11.75 m/s (2.1 % margin to 12), CD0 0.0411 with faired legs, cruise L/D 9.48 at 18 m/s, 239 W electrical, 17.3 min of cruise. [aerodynamics.md v0.4 update table]
- Neutral point with the pod is 41.1 % MAC in v0.3.1 (47.3 % without); the pod shifts it forward by 6.2 % MAC. Static margin is 13.1 % at the 28 % CG and 5.2 % at the no-payload CG of 36 %; v0.4 gives 11.8 % and 5.1 %. [aerodynamics.md section 4, v0.4 table]
- The adopted 2-D CL_max is 1.30 from published wind-tunnel data (XFOIL 1.36, NeuralFoil 1.28). The tail section NACA 0009 stalls near 8 degrees at Re 6e4 to 1e5, which limits elevator authority at 12 m/s. [aerodynamics.md section 3]
- The SU2 2-D RANS run is a cross-check only and feeds no sizing number: 28 of 29 cases usable, lift within about 3 to 9 % of XFOIL at 2 and 10 degrees, grid convergence index indicative only. [aerodynamics.md section 6]
- Measurements the team is told to take: watt-meter at 18 m/s (above 420 W fails R10; 10 min needs 436 W or less), stall test at MTOW (above 12.5 m/s fails R11), stopped-rotor drag with and without props, CG weighing, gear-fairing A/B test. [aerodynamics.md section 10]
- Sources cited by DBF-Combined, not opened by this import: XFOIL 6.99 and AVL 3.52 (MIT Drela pages), NeuralFoil and AeroSandbox (Sharpe, GitHub), SU2 8.5.0, gmsh 4.15.2, Genc, Lock and Kaynak (AIAA ATIO 2008), Genc, Karasu and Acikel (Exp. Thermal Fluid Sci. 2012), Raymer 5th ed., Hoerner "Fluid-Dynamic Drag" (1965), Nelson "Flight Stability and Automatic Control", Celik et al. (2008). [aerodynamics.md sections 1, 3, 7]

## Status in the study
none

## Open questions
- The drag count as a whole carries about plus or minus 20 % in the source, because of its estimated items (frontal areas of printed parts, stopped-propeller drag, leakage).
- Gear-fairing benefit is an estimate (drag coefficient 0.1 on frontal area); the source has no BOM line for it yet.
- The no-payload CG leaves only about 5 % static margin; the source recommends ballast and a flight check.
