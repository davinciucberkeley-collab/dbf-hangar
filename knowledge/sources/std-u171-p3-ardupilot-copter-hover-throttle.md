---
id: std-u171-p3-ardupilot-copter-hover-throttle
title: Setting Hover Throttle (ArduPilot Copter documentation)
authors: ArduPilot development team
year: unknown
url: https://ardupilot.org/copter/docs/ac_throttlemid.html
type: website
retrieved: 2026-11-25
verified: true
---

## Summary
Official ArduPilot Copter page on the hover throttle parameter (MOT_THST_HOVER) and its automatic learning. It gives a typical range for the learned value as a fraction of motor output at nominal battery voltage. It does not give a limit on hover thrust relative to a sagged-pack maximum, and it does not say where in the stick range hover should sit.

## Usable rules / numbers
- Typical hover throttle (MOT_THST_HOVER) is "usually between 0.2 and 0.6", a fraction of motor output; the page says it may be lower for copters with a very high power-to-weight ratio. Kind: typical range, not a limit. Condition: copter in steady hover, nominal battery. Place: page section "Numeric Range" under "Hover Throttle (MOT_THST_HOVER)".
- Learning moves the value toward the average motor output in steady hover in all non-manual modes (all except Stabilize and Acro). Place: section "Learning". No number.
- Setting MOT_HOVER_LEARN to 0 turns learning off. Place: section "Disabling Learning". No number.
- The page gives no statement of where in the stick range hover should be. Place: section "Stick Position".

## How we could use it
- Gives a typical hover fraction for copters on nominal battery only; not a sagged-pack maximum, so it cannot be used as a bound for the transition_thrust_fraction_max check.
- Context for the hover-fraction units (fraction of motor output), relevant to the packet 3 table.
