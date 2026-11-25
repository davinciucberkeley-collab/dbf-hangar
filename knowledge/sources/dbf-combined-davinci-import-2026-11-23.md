---
id: dbf-combined-davinci-import-2026-11-23
title: DBF-Combined: DaVinci import of concept A, 2026-11-23 docs/integration/davinci-import-2026-11-23.md
authors: DBF-Combined project (author not stated)
year: 2026
url: origin/redesign/v1:docs/integration/davinci-import-2026-11-23.md
type: website
retrieved: 2026-11-24
verified: true
---

## Summary
Record of the first concept-A import into the API Test project (since deleted). Gives per-package object counts, the BOM total and the import method.

## Usable rules / numbers
- Counts: 6 hard-constraint requirements (each with 1 constraint), 6 parts, 53 BOM items, 45 requirements, 11 tests; 367 objects in total (Counts table).
- BOM total $1,939.17 (goods $1,382.41, tax $141.70, shipping plus FAA $63.12, crash reserve $346.94, margin $60.83) (Values).
- Equation constraints HC-1 "[BOM total] <= 2000" and HC-3 "[Aircraft mass] <= 25000" (g) were accepted at creation (Notes and refusals).
- Relationships (test verifies requirement) not created: no REST route found (Notes).
- Re-run is idempotent with uuid5 ids (Notes).
- GLB upload 2,495,644 bytes; viewer-data parts recorded as parts with Mass and CG attributes (Part 2).

## How we could use it
Source for the import counts. The project it describes is deleted, so these objects are not in Concept A.
