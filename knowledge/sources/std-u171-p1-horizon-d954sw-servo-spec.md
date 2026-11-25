---
id: std-u171-p1-horizon-d954sw-servo-spec
title: D954SW Spec Sheet (Horizon Hobby servo)
authors: Horizon Hobby (manufacturer)
year: unknown
url: https://assets.horizonhobby.com/on/demandware.static/-/Sites-horizon-master/default/dwcd697d99/Manuals/D954SW%20Spec%20Sheet.pdf
type: website
retrieved: 2026-11-25
verified: true   # opened the manufacturer PDF; the text layer was only partly readable, so only the labelled values below were taken
---

## Summary
Manufacturer spec sheet for the D954SW servo. The PDF text layer was only partly readable in this run, so the values below are the labelled table entries that could be read, not the full table. It gives a dead band width of 1 microsecond in each voltage column, an operating travel stated as a one-side pulse of 400 microseconds, and no-load speeds. It gives no travel in degrees and no resolution or linearity figure that could be read.

## Usable rules / numbers
- Dead band width: 1 usec in each of the three voltage columns (typical spec label; voltages not confirmed from the readable text). Place: spec table, row "Dead band width".
- Operating travel: "one side pulse traveling 400 usec" (pulse width, not degrees). Place: spec table, row "Operating travel".
- No load speed: 0.19 s/60 deg (4.8 V), 0.15 s/60 deg (6.0 V), 0.12 s/60 deg (7.4 V). Place: spec table, row "No load speed".
- Pulse width range, neutral pulse width, operating angle in degrees, and resolution or linearity: not stated (in the readable text).

## How we could use it
- mechanism_abs_tol_deg (packet 1): deadband input in microseconds (kind: derivation input); conversion to degrees needs a travel in degrees for the same servo, which this sheet does not give.
- mechanism_contact_step_deg (packet 1): no resolution figure, so no direct input.
