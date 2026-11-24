---
id: "docs-research-benchmarks"
title: "Benchmarks: C0 against published aircraft and the literature"
kind: "research"
morph_cells: ["vtol_method:lift-plus-cruise"]
source_repo: DBF-Combined @ a93f14d
source_files: ["docs/research/benchmarks.md"]
created: 2026-11-23
verified: false
---

## Summary
A check of the C0 design against 22 published small VTOL aircraft (16 lift-plus-cruise, 6 tilt-rotor or tailsitter) and 37 literature values, done on 2026-10-26. The modelling assumptions came out mostly typical or conservative, and the study led to one design change, a lower cruise speed.

## Key facts
- C0 wing loading is 9.6 kg/m2 (published range 6.9 to 15.9), disk loading 110 N/m2 (published 126 to 315) and battery energy 22 Wh per kg of MTOW (published 51 to 98); the low battery figures follow from a 12 minute mission against published endurances of 1 to 4 hours. [benchmarks.md section 2]
- Adopted decision: the cruise speed drops from 20 to 18 m/s. Cruise power falls from 338 W to 264 W and available cruise time rises from 12.3 to 15.7 min against the 10 min requirement R10; the wing is sized by stall, so geometry is unchanged. [benchmarks.md section 4 item 1]
- C0's own polar puts best lift-to-drag speed at 12.6 m/s with a maximum L/D of 10.9, so even 18 m/s is well above it. [benchmarks.md section 3]
- Kept as conservative: propeller efficiency 0.60, hover figure of merit times efficiency 0.516, and a 64 kJ transition energy (literature scaling gives about 29 kJ, an estimate). [benchmarks.md sections 3-4]
- Static margin is 11.5 percent with payload and 4.9 percent empty against a literature band of 5 to 15 percent; a 0.5 kg ballast rule restores the loaded value. Tail volumes 0.35 and 0.03 sit inside the UAV range. [benchmarks.md sections 3-4]
- Published stopped-rotor data show a braked two-blade rotor across the flow adds 25 to 30 percent drag over one aligned with it, so the stopped-rotor test also records parking orientation. [benchmarks.md section 3]
- Sources named by the file, cited by DBF-Combined, not opened by this import: Pollet et al. (ICAS 2022-0383), Mathur and Atkins (arXiv 2301.12316 and 2411.08661), Brandt and Selig (AIAA 2011-1255), Russell et al. (NASA 2016), Drela's MIT 16.unified design rules, DeltaQuad Evo specifications, Wingcopter 178 data, NASA NPR 7123.1D. [benchmarks.md section 5]

## Status in the study
none

## Open questions
- Endurance figures for the published aircraft are maker claims; battery energy is published by only three makers and the rest assume 3.7 V per cell.
- Published W times V over P values assume 90 to 100 percent pack use and are upper bounds.
- Whether the tail needs more fin is left to flight-test pitch and yaw doublets.
