---
id: "docs-research-thermal"
title: "Heat dissipation: lift units, pod (battery, avionics) and pusher (C0 frozen design, 18 m/s cruise)"
kind: "research"
morph_cells: ["vtol_method:lift-plus-cruise"]
source_repo: DBF-Combined @ a93f14d
source_files: ["docs/research/thermal.md"]
created: 2026-11-23
verified: false
---

## Summary
A finite-element thermal study of the frozen C0 design (run of 2026-11-02, 18 m/s cruise) covering the four lift motors with their ESCs, the battery and flight-controller bays and the pusher motor in its printed cup. Film coefficients come from textbook correlations rather than CFD, and the loss fractions are estimates. At the 25 C design ambient every component passes, with the lift motor, pusher and pack setting that ceiling.

## Key facts
- Design ambient is 25 C, the full-mission ceiling of requirement R21; each temperature moves one-for-one with ambient, which means a 30 C day pushes the pusher 1 K past its limit. The three limiting components have margins of +5 K (lift motor), +4 K (pusher) and +7 K (pack). [thermal.md verdict]
- Lift unit in continuous hover from 25 C: motor can reaches 44, 59, 73 and 85 C at 30, 60, 90 and 120 s, crossing the estimated 80 C limit near 108 s. In the mission it reaches 59 C after the 60 s take-off hover and reaches 75 C by the finish of the 20 s transition. [thermal.md 6.1]
- Pod: the battery warms about 6.9 K in take-off hover and ends near 53 C at touchdown; the flight-controller board reaches 60 C under a sealed canopy, still rising at touchdown. Battery heat is 26.0 kJ over the mission, 6.9 percent of the pack energy drawn. [thermal.md 6.2, 2]
- Pusher: steady cruise settles near 77 C on the can, 76 C after 600 s, with a time constant of about 153 s; its 33.2 W loss is an estimate stacked on an estimate. [thermal.md 6.3]
- Recommendations: add ram-air inlet and exit slots for the battery bay (two openings of about 15 by 30 mm, estimated), accept packs only at or below 6.0 mohm per cell, keep hover to 60 s or less per rule, move each ESC to the boom side or top, vent the avionics bay, and keep carbon-nylon for motor mounts and the pusher cup (printed PETG mounts would pass their heat deflection point at about 82 s of hover). [thermal.md 6.4]
- Prop wash at the disc is 7.13 m/s induced velocity (thrust 18.23 N per unit, 17 in disc); air properties come from Incropera and DeWitt, 6th edition. [thermal.md section 3]
- Sources cited by DBF-Combined, not opened by this import: Incropera and DeWitt "Fundamentals of Heat and Mass Transfer" 6th ed., NOAA NCEI 1991-2020 climate normals (Berkeley), SOLIDWORKS Simulation 2025. [thermal.md sections 1, 3]

## Status in the study
none

## Open questions
- Loss fractions (lift motor 20 percent, ESC 4 percent, pusher 15 percent times 75 percent) are not from datasheets; every temperature rise scales linearly with them.
- Radiation, bay-air warming, solar load and simplified geometry are left out; results are optimistic for the sealed flight-controller bay.
- Planned test-plan measurements (motor and ESC heat, pack resistance, controller and connector temperatures, three 60 s hovers, pusher after cruise legs) are not yet done and close every estimate.
