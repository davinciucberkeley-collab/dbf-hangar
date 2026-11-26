---
id: std-u171-p1-stratasys-fortus-450mc
title: Fortus 450mc 3D Printer (Stratasys product page, Compare Printers and specifications)
authors: Stratasys Ltd. (manufacturer)
year: unknown
url: https://www.stratasys.com/uk/3d-printers/printer-catalog/fdm-printers/fortus-450mc/
type: website
retrieved: 2026-11-25
verified: true   # opened and read the Accuracy row and the note below the comparison table in this run
---

## Summary
Manufacturer product page for the Fortus 450mc FDM printer. It states a part accuracy specification as a fixed floor in mm and inches, or a proportional value in mm/mm, whichever is greater, with a Z-axis addition and a note that accuracy is geometry dependent. The same figure is stated in the Stratasys datasheet (PSS FDM Fortus 450mc), which search returned but which I could not open (see packet file).

## Usable rules / numbers
- Part accuracy: +/-0.127 mm (+/-0.005 in) or +/-0.0015 mm/mm (+/-0.0015 in/in), "whichever is greater" (maximum deviation, printer-stated). Place: Accuracy row, Compare Printers table.
- Z axis: Z part accuracy includes an additional tolerance of -0.000 / +slice height (the slice height value is not given on the page). Place: note under the comparison table.
- Condition: accuracy is geometry dependent and derived from statistical data at 95 % dimensional yield. Place: same note.
- Build envelope 406 x 355 x 406 mm (16 x 14 x 16 in), listed on the same page (not used for a value in this packet).

## How we could use it
- attach_tolerance_mm (packet 1): comparison input for printed-part dimensional accuracy (kind: maximum, printer-stated).
- planform_match_tolerance_fraction (packet 1): relative accuracy input (0.0015 mm/mm) for a measured-to-declared span comparison.
- interference_max_mm3 and strip_gap_tolerance_mm (packet 1): tolerance input +/-0.127 mm for derivations.
