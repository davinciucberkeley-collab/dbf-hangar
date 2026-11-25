---
id: std-u171-p2-hamburg-empennage-sizing
title: Aircraft Design lecture 11, Empennage Sizing (HAW Hamburg lecture notes)
authors: HAW Hamburg aircraft design lecture series (author not stated in the text read)
year: unknown
url: https://www.fzt.haw-hamburg.de/pers/scholz/HOOU/AircraftDesign_11_EmpennageSizing.pdf
type: website
retrieved: 2026-11-25
verified: true
---

## Summary
University lecture notes on sizing the horizontal tailplane from stability and control requirements. They define the tail dynamic-pressure ratio and give its usual range and a typical mean. They also give the static-margin requirement for several airplane categories as a table of minimums.

## Usable rules / numbers
- [aft_surface_efficiency] Tail dynamic-pressure ratio eta_H "assumes values between 0.85 and 0.95. A typical mean value is 0.9" (section 11.1, parameter list after eq. 11.19, PDF p. 5). Typical range, with a stated mean.
- [aft_surface_efficiency] Definition eta_H = q_H / q (eq. 11.6, PDF p. 4). The notes say the ratio is below 1 because the wing's drag delays the flow at the tail (section 11.1, PDF p. 4). They give no interference or lift-slope term.
- [fw_static_margin_max] Table 11.1 "Required static margins" lists 10% MAC (homebuilts, single-engine propeller, twin-engine propeller, agricultural) and 5% MAC (military trainers, business jets, others). These are minimums; no maximum is stated (section 11.2, Table 11.1, PDF p. 11).

## How we could use it
- Feeds aero.aft_surface_efficiency as the dynamic-pressure term only; the notes give no lift-slope efficiency.
- Gives minimum static margins for context on fw_static_margin_max; it does not bound the maximum.
