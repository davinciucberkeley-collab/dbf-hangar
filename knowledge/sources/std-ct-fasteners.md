---
id: std-ct-fasteners
title: Small-screw, heat-set insert and metric bolt load data (CNC Kitchen tests; ISO 898-1 proof-load and ISO 898-7 breaking-torque tables)
authors: Stefan Hermann (CNC Kitchen); The Engineering ToolBox; TR Fastenings
year: unknown
url: https://www.cnckitchen.com/blog/threaded-inserts-for-3d-prints-cheap-vs-expensive
type: website
retrieved: 2026-11-20
verified: true
---

## Summary
Opened: https://www.cnckitchen.com/blog/threaded-inserts-for-3d-prints-cheap-vs-expensive ; https://www.cnckitchen.com/blog/are-our-heat-set-insert-datasheets-wrong ; https://www.cnckitchen.com/blog/helicoils-threaded-insets-and-embedded-nuts-in-3d-prints-strength-amp-strength-assessment ; https://www.cnckitchen.com/blog/tipps-amp-tricks-fr-gewindeeinstze-im-3d-druck-3awey (no numbers) ; https://www.engineeringtoolbox.com/metric-bolts-minimum-ultimate-tensile-proof-loads-d_2026.html ; https://www.trfastenings.com/knowledge-base/metric-screws/screws-and-bolts-mechanical-properties ; https://hackaday.com/tag/pull-out/ (summary, no numbers). blocked: sculpteo.com (HTTP 403). Prusa help-center heat-set insert article: not found (searches returned only prusa3d.com store pages, which give no loads).
CNC Kitchen's pull-out tests of M3 heat-set inserts in printed PLA and PETG give pull-out forces of roughly 1.1 to 1.8 kN for good inserts, with torque-out of a few Nm where the M3 screw itself failed first. The ISO 898-1 based tables give M3 and M4 bolt proof and ultimate loads for classes 8.8 and 12.9; M2 and M2.5 loads are not in the tables opened, only ISO 898-7 breaking torques.

## Usable rules / numbers
- CT-M3-SHCS-INSERT: M3 heat-set insert pull-out in Prusament PLA, Ruthex insert 181 kg, eBay insert 157 kg, cheap injection-molding insert 39 kg; direct screwing into a 2.7 mm hole 142 kg (cnckitchen "Threaded Inserts for 3D Prints - Cheap VS Expensive", section "Pull-out results").
- CT-M3-SHCS-INSERT: torque-out of M3 inserts in PLA about 3 to 4 Nm for all three insert types, "all tests for the inserts failed at around 3 to 4Nm"; direct screwing about 1 Nm (same post, section "Torque-out results").
- CT-M3-SHCS-INSERT: M3 inserts melted into as-printed PolySonic PLA, average pull-out about 1400 N at smaller hole diameters (3.6 to 4.6 mm tested, 3 pieces per diameter); 4.2 mm CAD hole keeps about 90% of maximum; packaging recommends 4.0 mm hole (cnckitchen "Are Our Heat-Set Insert Datasheets Wrong?", sections "Pull-out strength of the as-printed samples" and "Printing and drilling the test samples").
- CT-M3-SHCS-INSERT: M3 in PETG, average of 3 samples, heat-set insert 119 kg, direct screwing 118 kg, Helicoil 120 kg, side-pocket nut 86 kg, bottom-pocket nut about 166 kg (cnckitchen "Helicoils vs Threaded Inserts vs Embedded Nuts", section "Pull-out results").
- CT-M3-SHCS-NYLOC, CT-M3-SHCS-MOTOR, CT-M3-SHCS-INSERT: M3 coarse bolt, stress area 5.03 mm2, proof load 2920 N (class 8.8) and 4880 N (class 12.9); minimum ultimate tensile load 4020 N (8.8) and 6140 N (12.9) (engineeringtoolbox, tables "Metric Bolts - Coarse Threads - Proof Loads" and "... Minimum Ultimate Tensile Loads").
- CT-M4-SHCS-NYLOC: M4 coarse bolt, stress area 8.78 mm2, proof load 5100 N (8.8) and 8520 N (12.9); minimum ultimate tensile load 7020 N (8.8) and 10700 N (12.9) (same engineeringtoolbox tables).
- CT-M2-SCREW-PLASTIC: M2 screw minimum breaking torque 0.37 Nm (8.8), 0.5 Nm (12.9) (trfastenings, table "Breaking torque ISO 898-7 DIN 267 pt25"). M2 proof/tensile load and M2 pull-out in printed plastic: not found.
- CT-A-M25-SHCS-MOTOR: M2.5 screw minimum breaking torque 0.82 Nm (8.8), 1.1 Nm (12.9) (trfastenings, same table). M2.5 proof/tensile load: not found.
- M3 / M4 breaking torque 1.5 / 3.6 Nm (8.8) and 2.1 / 4.9 Nm (12.9) (trfastenings, same table).
- Nyloc nut prevailing-torque or stripping load: not found. CT-HW-SEATED, CT-PROP-ADAPTER, CT-PROP-NUT, CT-A-PROP-ADAPTER, CT-A-PROP-NUT ratings: not found.

## How we could use it
- Feeds connection-type ratings in standards/connection-types.yaml: CT-M3-SHCS-INSERT, CT-M3-SHCS-NYLOC, CT-M3-SHCS-MOTOR, CT-M4-SHCS-NYLOC (bolt loads); CT-M2-SCREW-PLASTIC and CT-A-M25-SHCS-MOTOR (torque only).
- Keys with no value found stay pending: CT-HW-SEATED, CT-PROP-ADAPTER, CT-PROP-NUT, CT-A-PROP-ADAPTER, CT-A-PROP-NUT.
- Insert test values are single-lab hobby tests in PLA/PETG; any rating built from them needs a design factor chosen elsewhere.
