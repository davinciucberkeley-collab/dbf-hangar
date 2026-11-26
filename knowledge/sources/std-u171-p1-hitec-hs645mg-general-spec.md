---
id: std-u171-p1-hitec-hs645mg-general-spec
title: HS-645MG General Specification (standard deluxe high torque servo)
authors: Hitec RCD (manufacturer), copy hosted by Digi-Key
year: unknown
url: https://media.digikey.com/pdf/Data%20Sheets/Hi-Tech/HS-645MG.pdf
type: website
retrieved: 2026-11-25
verified: true
---

## Summary
Manufacturer general specification sheet for the Hitec HS-645MG analog metal-gear servo, opened as a PDF copy hosted by Digi-Key on 2026-11-25 and read through its text layer. The table lists dead band width for both test voltages and the operating travel with the pulse width that covers it. No resolution or linearity figure is printed on the sheet.

## Usable rules / numbers
- Dead band width 8 usec at 4.8 V and 8 usec at 6.0 V. Kind: typical range (single printed value per voltage; no bound stated). Place: spec table, row "Dead band width" (page 1 of the copy).
- Operating travel 45 degrees for a one-side pulse traveling 400 usec. Exact derivation: 45 / 400 = 0.1125 deg per usec. Kind: typical range (the sheet states the pair, not a tolerance). Place: spec table, row "Operating travel".
- The sheet gives no resolution, linearity or repeatability figure for this servo. Place: whole spec table checked.

## How we could use it
- mechanism_abs_tol_deg (standards key): gives the same-servo dead band (8 usec) and the same-servo degree per usec (0.1125 deg/usec from 45 deg per 400 usec) as derivation inputs for a dead-band floor. Not a bound on the mechanism.
- mechanism_ratio_tol and mechanism_contact_step_deg: no fraction and no resolution figure on this sheet, so no value for those keys.
