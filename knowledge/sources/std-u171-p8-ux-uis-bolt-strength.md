---
id: std-u171-p8-ux-uis-bolt-strength
title: Metric bolt strength (mechanical requirements for carbon steel externally-threaded metric fasteners, Table 2)
authors: not found (page hosted at ux.uis.no)
year: unknown
url: https://www.ux.uis.no/~hirpa/6KdB/ME/metric_bolt_strength.htm
type: website
retrieved: 2026-11-25
verified: true
---

## Summary
Opened on 2026-11-25. The page gives proof-stress and yield and ultimate stresses per property class (Table 2) and says loads are computed as stress times tensile stress area from a separate table that is not on the page. It has no M2.5 row, so it gives no M2.5 stress area or load.

## Usable rules / numbers
- Table 2 "Mechanical requirements for carbon steel externally-threaded metric fasteners": class 8.8, size range M16 to M72, proof stress 600 MPa (section Table 2, class 8.8 row).
- Table 2: class 12.9, size range M1.6 to M100, proof stress 970 MPa, tensile yield 1100 MPa minimum, tensile ultimate 1220 MPa minimum (section Table 2, class 12.9 row).
- Method note on the page: load = stress (MPa) times tensile stress area (mm2) divided by 1000 for kN; the stress-area table is referenced but not on the page.
- M2.5 tensile stress area or load: `not found` on this page.

## How we could use it
- Stress basis only. The page cannot give an M2.5 proof load, so CT-PROP-ADAPTER and CT-A-M25-SHCS-MOTOR stay pending from this source.
- The class 8.8 stress is size-dependent in this table (600 MPa for M16 and up), so it is not used for M2.5 to M6 values.
