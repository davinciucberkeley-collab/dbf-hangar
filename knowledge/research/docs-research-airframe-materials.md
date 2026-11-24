---
id: "docs-research-airframe-materials"
title: "Airframe materials, hardware and reference airframes"
kind: "research"
morph_cells: ["vtol_method:lift-plus-cruise"]
source_repo: DBF-Combined @ a93f14d
source_files: ["docs/research/airframe-materials.md"]
created: 2026-11-23
verified: false
---

## Summary
A parts survey for a lift-plus-cruise VTOL of 8 to 15 kg and 2 to 3 m span that must break down to fit in a car. It prices carbon tubes, foam, glass cloth, epoxy, filament, plywood, clamps, wing bolts and landing gear, and compares published airframes for mass fractions. Pages were read live on 2026-10-13; vendor strength figures are reference only.

## Key facts
- Recommended boom tube is a roll-wrapped carbon tube of 25.3 mm outer and 22.2 mm inner diameter (1.5 mm wall, about 164 g/m, $123.45 per 1.83 m). The same tube doubles as a full-length wing joiner inside a 28.4 mm spar tube (about 193 g/m, $151.54), with about 0.005 in diametral clearance. [airframe-materials.md recommendation table]
- Lighter alternative with published laminate numbers is a 22.4 mm tube (0.9 mm wall, about 94 g/m, $94.99) with axial modulus 57.5 GPa and tensile strength 433 MPa from classical lamination theory; its diameter does not match the standard 22 or 25 mm clamps. [airframe-materials.md 1a]
- For twill roll-wrapped tubes the source says to design with 57 to 76 GPa axial modulus and 430 to 570 MPa tensile strength; the generic vendor figure of 117 GPa is a unidirectional best case and flatters stiffness. [airframe-materials.md 1c]
- Filaments: a pre-foamed lightweight PLA lists 0.9 g/cm3 on its data sheet, an actively foaming grade lists 0.40 to 0.48 g/cm3 once foamed, and carbon-filled nylon lists 1.17 g/cm3 with about 109 MPa tensile (XY, dry). [airframe-materials.md 2d]
- Reference airframes, empty mass over MTOW: DeltaQuad Evo 0.48 and Foxtech Baby Shark 260 0.46; the Evo battery fraction is about 0.40 with two packs. The derived band at 12 kg MTOW is about 5.6 kg empty, 4.8 kg battery, 2.6 kg bare structure (calculated from two data points). [airframe-materials.md section 4]
- No US-stocked metric 22 or 25 mm aluminium clamp with a live price was found; the cheapest stocked path is UK-sold Tarot mounts or printed carbon-nylon clamps. [airframe-materials.md 3a]
- Vendors read include Rock West Composites, Carbon Fiber Tube Shop, DragonPlate, Aircraft Spruce, US Composites, Fibre Glast, WEST SYSTEM, Polymaker, colorFabb, Flying Tech and Freefly (cited by DBF-Combined, not opened by this import). [airframe-materials.md sections 1-3]

## Status in the study
none

## Open questions
- Measure boom bending stiffness on an offcut; below 50 GPa means tip deflection and rotor-arm frequency need rechecking (source item M1).
- Check the joiner fit with a feeler gauge; a gap above 0.2 mm needs shimming (M2).
- Weigh every tube on arrival; more than 10 percent over listed mass means updating the mass roll-up (M3).
- Print a 50 mm cube in lightweight PLA to get the real density (M4).
- Several prices and stock levels could not be retrieved (some vendor pages returned errors) and are marked as not recorded in the source.
