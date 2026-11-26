---
id: std-u171-p1-iso-2768-1-amesweb
title: ISO 2768 linear dimensions tolerances (permissible deviations for basic size ranges, ISO 2768-1)
authors: AMES (tolerance reference website; transcribes ISO 2768-1:1989)
year: 1989
url: https://amesweb.info/fits-tolerances/iso-2768-linear-dimensions-tolerances.aspx
type: website
retrieved: 2026-11-25
verified: true   # opened and read the table for the 0.5 up to 3 mm row in this run
---

## Summary
Public tolerance reference page that reproduces the ISO 2768-1 table of permissible deviations for linear dimensions without individual tolerance indications. The page gives one row per basic size range and one column per class (f, m, c, v). This is a secondary transcription of the ISO table, not the standard itself; the ISO PDF copies opened in this run were scanned images with no readable text.

## Usable rules / numbers
- Size range "over 0.5 up to 3" mm, class f (fine): +/-0.05 mm (permissible deviation, bound). Place: page table titled "Permissible deviations for basic size ranges - linear dimensions (ISO 2768-1)", row 0.5 up to 3.
- Same row, class m (medium): +/-0.1 mm (permissible deviation, bound). Same place.
- Same row, class c (coarse): +/-0.2 mm (permissible deviation, bound). Same place.
- Same row, class v (very coarse): no value shown on the page ("-"). Same place.
- The page states the deviations as +/- values in mm per size range. It states no value for joint distances or gaps between parts.

## How we could use it
- attach_tolerance_mm (packet 1): tolerance input for a printed-part dimension; does not bound a joint distance.
- interference_max_mm3 (packet 1): tolerance input for the derivation tolerance x contact area (kind: derivation input).
