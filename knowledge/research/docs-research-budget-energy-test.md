---
id: "docs-research-budget-energy-test"
title: "Budget energy, charging and test kit: live price sweep"
kind: "research"
morph_cells: []
source_repo: DBF-Combined @ a93f14d
source_files: ["docs/research/budget-energy-test.md"]
created: 2026-11-23
verified: false
---

## Summary
A 2026-10-13 price sweep for 6S flight packs, an AC charger, safe storage and a DIY thrust stand against the project mission of a short hover plus a 10 minute cruise. It picks the cheapest packs that cover the worst-case energy need and flags unreliable listing data. No morphological cell applies because the file is about purchasing, not configuration.

## Key facts
- Worst-case mission energy is about 120 Wh (hover 0.6 to 0.9 kW for 3 min plus cruise 300 to 450 W for 10 min). With an assumed 80 percent usable depth, a 144 Wh pack gives 115 Wh and falls short, while a 177.6 Wh pack gives 142 Wh and covers it. [budget-energy-test.md verdict, energy check]
- Cheapest pack that covers the worst case is a 6S 8000 mAh two-pack at $199.99 (177.6 Wh, 986 g, about 180 Wh/kg); a lighter 6S 6500 mAh two-pack is $138.99 (144.3 Wh, 820 g) but is below the worst-case energy. [budget-energy-test.md verdict]
- Hover current is 27 to 41 A at 6S nominal, so a pack sustaining 60 A continuous leaves about 1.5 times margin. Listed C ratings of 100C and above imply 650 to 1200 A, which the source calls not credible. [budget-energy-test.md energy check, section 1]
- Charger: a 150 W unit gives 5.95 A on 6S ($56.99); a 100 W unit gives only 3.97 A and fails the 5 A requirement. [budget-energy-test.md verdict, section 2]
- Cheapest safety and test kit (LiPo bag, ammo can, watt meter, IR thermometer, 20 kg load cell with amplifier, microcontroller board) is $68.92. Ammo-can gasket removal is common practice, not from the vendor page, and should be checked against university safety guidance. [budget-energy-test.md verdict, section 3]
- Several Amazon listings contain inconsistent data (a weight in kilograms that is really grams, an energy-density claim 40 percent above the computed figure, template-artifact charger specs). [budget-energy-test.md Amazon flags]
- Sources cited by DBF-Combined, not opened by this import: Amazon listings, RaceDayQuads, Pyrodrone, Zeee and CNHL shipping policies, Harbor Freight, SparkFun, iFlight and Lumenier pages. [budget-energy-test.md sections 1-4]

## Status in the study
none

## Open questions
- Sales tax was not included in this sweep.
- The 80 percent usable depth is an assumption; the source plans a discharge test (item M2).
- Pack sustained current is unverified; the source plans a 45 A, 3 minute stand test, failing below 3.5 V per cell or above 60 C surface (an estimated threshold) (M1).
- Charger output at 24 to 25 V must be measured; under 5.0 A fails the requirement (M3).
- SparkFun shipping and the ammo-can venting practice were not checked.
