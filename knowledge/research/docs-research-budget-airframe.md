---
id: "docs-research-budget-airframe"
title: "Budget airframe: booms, spar, joiner, skin, foam, hardware, filament"
kind: "research"
morph_cells: ["vtol_method:lift-plus-cruise"]
source_repo: DBF-Combined @ a93f14d
source_files: ["docs/research/budget-airframe.md"]
created: 2026-11-23
verified: false
---

## Summary
Parts research to cut the airframe cost from about $1,000 (carbon tube with glass and epoxy) to a low-cost build: a 2.4 m foam wing in two halves, twin booms, an H-tail and a plug-in joiner. It works the mass fractions at 5 to 7.5 kg MTOW, which the source notes is below the project's 8 to 15 kg target. Prices were read live on 2026-10-13.

## Key facts
- Cheapest credible tube set is all 6061-T6 aluminium from one vendor: two 1.000 by 0.035 in booms of 72 in ($52.40), a 1.000 by 0.058 in spar socket tube of 96 in cut in half ($53.97) and a 0.875 by 0.058 in joiner of 36 in ($18.45). Total $124.82 plus shipping, about 1.56 kg. [budget-airframe.md verdict table, 1d option A]
- That 1.56 kg is 21 to 31 percent of a 5 to 7.5 kg MTOW. The boom bending stiffness is 355 N m2 at 185 g/m, against 452 to 603 N m2 at 173 g/m for a wrapped carbon tube. A mixed set (aluminium booms, carbon spar sockets) is $152.33 and 1.04 kg. [budget-airframe.md verdict, 1d]
- Joiner fit: a 0.875 in joiner in a 1.000 by 0.058 in socket leaves 0.23 mm diametral clearance, a normal slip fit; it is far too loose (1.40 mm) in the thin-wall boom tube. [budget-airframe.md 1b]
- Skin: 6 rolls of heavy-duty packing tape cost $19.98 (about 2.5 m2 of skin is needed, estimated from an assumed 0.30 m chord); paper skin with glue and sealer costs $54.04, so it is not cheaper. [budget-airframe.md 2a]
- Foam: one 2 in by 4 by 8 ft extruded polystyrene sheet ($59.97) fits both 1.2 m wing halves laid end to end; a 50.8 mm core suits a 12 percent section up to about 0.42 m chord. [budget-airframe.md 2b]
- Minimum hardware kit is 13 lines for $124.01 ($136.72 with tax), $184.44 with spares; airframe materials plus minimum kit total $359.75 before tax, about 40 percent of the earlier airframe. [budget-airframe.md sections 3 and verdict]
- PETG has a heat deflection temperature of 68 C against 55 C for PLA, so it suits clamps and joiner saddles but is reasonable at motor mounts only if the case stays well below 68 C. [budget-airframe.md section 5]
- Sources cited by DBF-Combined, not opened by this import: OnlineMetals, Aircraft Spruce, Speedy Metals, Goodwinds, Gator-RC, Home Depot and Lowe's listings, Amazon search pages, Prusament PETG and PLA technical data sheets, CDTFA tax rates, the 6061 aluminium Wikipedia page. [budget-airframe.md sections 1-5]

## Status in the study
none

## Open questions
- Shipping for the metal order is priced only at checkout and is unknown.
- Motor case temperature in hover is not known; measure it, and above about 60 C avoid printed mounts (source item M3).
- Weigh delivered tubes; above 1.6 kg or 25 percent of MTOW the source says to move to carbon sockets (M1).
- Skin mass per area is not published; a taped test panel above about 150 g/m2 (assumed threshold) calls for a laminating-film comparison (M2).
- Joiner play above about 5 mm at the wingtip (assumed threshold) calls for a bushing or tape shim (M4).
