---
id: std-u171-p1-servodatabase-emax-es9051
title: EMAX ES9051 servo specifications (ServoDatabase)
authors: ServoDatabase (third-party servo specification database)
year: unknown
url: https://servodatabase.com/servo/emax/es9051
type: website
retrieved: 2026-11-25
verified: true   # opened and read the specification list in this run
---

## Summary
Third-party servo database page for the EMAX ES9051. It lists a rotational range, a pulse width range, and speeds at several voltages. It does not list dead band or resolution. The rotational range and pulse range are for this servo only and are not for the D954SW servo in the Horizon sheet.

## Usable rules / numbers
- Rotational range: 120 deg. Place: specification list, label "Rotational Range".
- Pulse width: 1100 to 1900 usec (800 usec span). Place: specification list, label "Pulse Width".
- Speed: 0.06 s/60 deg (6.0 V), 0.08 s/60 deg (5.5 V), 0.07 s/60 deg (4.8 V), 0.10 s/60 deg (4.0 V). Place: specification list, label "Speed".
- Dead band: not stated. Resolution: not stated.

## How we could use it
- mechanism_abs_tol_deg (packet 1): degrees-per-microsecond input (120 deg over 800 usec) for a different model from the deadband source; a derivation across models is not one servo's value, so it is listed as an input only.
- mechanism_ratio_tol and mechanism_contact_step_deg (packet 1): no deadband or resolution figure.
