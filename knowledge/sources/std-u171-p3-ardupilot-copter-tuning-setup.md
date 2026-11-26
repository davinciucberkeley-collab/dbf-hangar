---
id: std-u171-p3-ardupilot-copter-tuning-setup
title: Setting the Aircraft Up for Tuning (ArduPilot Copter documentation)
authors: ArduPilot development team
year: unknown
url: https://ardupilot.org/copter/docs/setting-up-for-tuning.html
type: website
retrieved: 2026-11-25
verified: true
---

## Summary
Official ArduPilot Copter page on preparing a copter for PID tuning. Its motor setup section gives a starting value for the hover thrust parameter (MOT_THST_HOVER) and says a lower value is safer. The value is a parameter setting for tuning, not a limit on the ratio of hover thrust to maximum thrust.

## Usable rules / numbers
- MOT_THST_HOVER should be set to 0.25 "or below the expected actual hover thrust percentage" (page wording, quoted in part); the page says lower is safe and gives no other margin. Kind: maximum, for the parameter setting during tuning only. Condition: tuning setup, copter. Place: section "Motors setup".

## How we could use it
- Does not bound hover thrust as a fraction of a sagged-pack maximum, so it does not feed transition_thrust_fraction_max. Recorded so the parameter is not confused with a thrust margin.
