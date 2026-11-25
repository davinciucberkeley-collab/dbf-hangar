---
id: dbf-combined-davinci-step-parts-csv
title: DBF-Combined: STEP part list docs/integration/davinci-step-parts.csv
authors: DBF-Combined project (author not stated)
year: 2026
url: origin/redesign/v1:docs/integration/davinci-step-parts.csv
type: website
retrieved: 2026-11-24
verified: false
---

## Summary
Per-part table of STEP conversion results (triangles, faces, size, closed bodies, volume error, decimation flag). W32-S read the header, first three rows and the line count only.

## Usable rules / numbers
- 130 lines including the header (about 129 part rows) (wc -l).
- Columns: part, subsystem, triangles, faces, mb, bodies, closed_bodies, gmsh_volumes, bbox_err_mm, mesh_volume_mm3, step_volume_mm3, volume_err_pct, davinci_volume_mm3, davinci_vs_mesh_pct, decimation.
- Example row: AVN-002, avionics, 908 triangles, 126 faces, 0.07 MB, 2 bodies, decimation no.

## How we could use it
Input for sizing the STEP upload; the decimation column relates to the lite-STEP path in davinci-findings.
