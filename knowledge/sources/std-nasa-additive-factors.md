---
id: std-nasa-additive-factors
title: NASA-STD-6030 Additive Manufacturing Requirements for Spaceflight Systems (Baseline, 2021-04-21), with NASA-STD-5001B w/Change 3 re-checked
authors: NASA
year: 2021
url: https://standards.nasa.gov/sites/default/files/standards/NASA/Baseline/0/2021-04-21_nasa-std-6030-approveddocx.pdf
type: standard
retrieved: 2026-11-20
verified: true
---

## Summary
Opened: https://standards.nasa.gov/standard/nasa/nasa-std-6030 (landing page), https://standards.nasa.gov/sites/default/files/standards/NASA/Baseline/0/2021-04-21_nasa-std-6030-approveddocx.pdf (full text, 190 pages, searched for safety factor, allowable, design value, polymer, NASA-STD-5001), https://standards.nasa.gov/standard/nasa/nasa-std-5001 and https://standards.nasa.gov/sites/default/files/standards/NASA/B-w/CHANGE-3/3/2022-10-24-NASA-STD-5001B-w-Change-3-Approved.pdf (full text searched for additive, polymer, non-metallic). MSFC-STD-3716 not opened.
NASA-STD-6030 governs process control, part classification and qualification of AM spaceflight parts; it explicitly does not set or change factors of safety, which it leaves to structural standards such as NASA-STD-5001. It gives margin thresholds (on top of the required safety factor) that mark a polymer AM part as "low structural demand", and a default 1.2 proof factor for acceptance. NASA-STD-5001B w/Change 3 contains no additive-manufacturing factor and no factor for "not fully characterized" material (0 hits for "additive manufactur").

## Usable rules / numbers
- `ultimate_factor` (printed parts): no AM-specific ultimate factor of safety in NASA-STD-6030; it states the structural demand assessment "does not levy or alter any of the structural requirements, factors of safety" (section 4.3 commentary before Table 2, p. 40).
- Polymer AM, low structural demand (elongation at failure >= 3% in application environment): ultimate strength minimum margin 0.5, yield strength minimum margin 0.3, where margin = design/(operation x safety factor) - 1 (NASA-STD-6030 Table 3, p. 43).
- Polymer AM with elongation at failure < 3%: ultimate strength minimum margin 2.0, assessed against local maximum principal stress at stress concentrations (Table 3, p. 43; brittle-material rule also in 6.11.5.1.3, p. 124).
- Polymer AM fatigue, low structural demand: cyclic stress range <= 50% of applicable fatigue limit; no sustained stress / no predicted creep strain (Table 3, p. 43).
- Material extrusion of thermoplastic filament (FDM) is allowed only for Class C parts, not Class A or B (Table 1, p. 18).
- Proof test: absent other guidance, a proof factor of 1.2 on limit conditions is considered appropriate for AM part acceptance (section 4.16 commentary to [AMR-32], p. 74).
- Class B polymer parts must not operate through their glass transition temperature Tg ([AMR-85], section 6.11.5.1.4, p. 125).
- NASA-STD-5001B w/Change 3, for comparison only: metallic ultimate design factor 1.4 (Table 1, p. 18); composite/bonded ultimate design factor 1.4 prototype / 1.5 protoflight uniform material, 2.0 at discontinuity areas (Table 2, p. 19). No additive or "not fully characterized material" factor found.
- `fea_allowable_printed_petg_mpa`: not found (neither standard gives a PETG or other FDM material strength in MPa; NASA-STD-6030 requires allowables from the user's own statistical test data, section 6.11).

## How we could use it
- `ultimate_factor`: evidence that NASA gives no separate ultimate factor for printed parts; the 6030 Table 3 margins (0.5 ultimate, 2.0 for < 3% elongation) are a possible extra margin check on printed (3d-print-fdm) parts in the FEA tier, if the team chooses.
- `fea_allowable_printed_petg_mpa`: no value from these sources; stays on its existing UltiMaker TDS source.
