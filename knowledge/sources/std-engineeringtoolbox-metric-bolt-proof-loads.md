---
id: std-engineeringtoolbox-metric-bolt-proof-loads
title: Metric Bolt Strength - Minimum, Ultimate Tensile and Proof Loads - Metric (EngineeringToolbox)
authors: EngineeringToolbox (reference website; states its values follow ISO 898-1)
year: unknown
url: https://www.engineeringtoolbox.com/metric-bolts-minimum-ultimate-tensile-proof-loads-d_2026.html
type: website
retrieved: 2026-11-26
verified: true   # opened 2026-11-26 via WebFetch; M3 row read from the tables
---

## Summary
Reference tables of nominal stress area, minimum ultimate tensile load and proof load for metric coarse-thread bolts by property class. The page gives the M3 row for classes 8.8 and 12.9. It gives no shear values. Values were read through a summarising fetch, not the ISO 898-1 text itself.

## Usable rules / numbers
- M3 coarse thread, pitch 0.50 mm, nominal stress area As,nom 5.03 mm² (tables, M3 row).
- M3 class 8.8: minimum ultimate tensile load Fm,min 4020 N; proof load Fp 2920 N (tables, M3 row).
- M3 class 12.9: minimum ultimate tensile load Fm,min 6140 N; proof load Fp 4880 N (tables, M3 row).
- Shear load or shear strength for M3 class 8.8 or 12.9: not found.
- M3 pull-out in birch plywood or PLA: not found (not in scope of the page).

## How we could use it
- CT-M3-SHCS-MOTOR and CT-M3-SHCS-NYLOC: tensile ceiling (Fm,min) and proof load for the screw itself; the joint rating still needs a separate pull-out or shear basis.
- CT-M3-SHCS-NYLOC shear: no shear value here; a shear source is still needed.
