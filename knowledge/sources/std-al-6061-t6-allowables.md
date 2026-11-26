---
id: std-al-6061-t6-allowables
title: Aluminum Standards and Data, Table 12.1 Mechanical Property Limits - Extruded Tube (6061-T6 rows, printed p. 12-4)
authors: The Aluminum Association
year: 2009
url: https://www.aluminum.org/sites/default/files/2022-12/Table_12.1.pdf
type: standard
retrieved: 2026-11-25
verified: true
---

## Summary
The Aluminum Association table gives specified minimum mechanical property limits for extruded tube by alloy, temper and wall thickness. For 6061-T6 it lists minimum ultimate and minimum yield strength in ksi and minimum elongation, banded by wall thickness. These are specified limits, not MMPDS basis A, B or S allowables, and the table does not label them as typical. The text layer was read in raw order because the default layout order mixed rows.

## Usable rules / numbers
6061-T6, T62, T6510 and T6511 rows, Table 12.1 (Extruded Tube), printed p. 12-4 (PDF p. 2):
- Wall up through 0.249 in, all areas: minimum ultimate tensile 38.0 ksi; minimum yield 35.0 ksi; minimum elongation 8% (Table 12.1, p. 12-4)
- Wall 0.250 in and over, all areas: minimum ultimate tensile 38.0 ksi; minimum yield 35.0 ksi; minimum elongation 10% (Table 12.1, p. 12-4)
- Basis: "specified" limits per the table header; MMPDS basis not stated (Table 12.1, p. 12-4)
- Conversion not applied: values are in ksi as printed.
- Applicability to c0-a1 (OnlineMetals 6061-T6 tube, 1.000 x 0.058 in): the 0.058 in wall falls in the "up through 0.249 in" band, so the 38.0 ksi / 35.0 ksi / 8% row applies (wall band from the table header, p. 12-4; footnote Q says the specimen thickness governs).
- Not found in this source: typical values for 6061-T6 tube, MMPDS basis A/B/S values, and any compressive or shear values.

## How we could use it
- Feeds U18.3 as minimum tensile and yield for 6061-T6 tube at the c0-a1 wall: Ftu 38.0 ksi and Fty 35.0 ksi minimum, elongation 8%, with basis not MMPDS.
- For design margins, use MMPDS-xx or MIL-HDBK-5J tables with basis A or B stated before the U18.3 gate closes.
- values still missing: MMPDS or MIL-HDBK-5J basis (A, B or S) value for 6061-T6 tube; typical values labelled as typical (not opened in this run).
