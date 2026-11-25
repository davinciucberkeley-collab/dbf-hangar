---
id: std-u171-p2-ardupilot-assisted-flight
title: Assisted Fixed-Wing Flight (ArduPilot Plane documentation)
authors: ArduPilot development team
year: unknown
url: https://ardupilot.org/plane/docs/assisted_fixed_wing_flight.html
type: website
retrieved: 2026-11-25
verified: true
---

## Summary
ArduPilot documentation of Q_ASSIST_SPEED, the airspeed below which the lift motors assist a quadplane in fixed-wing flight. It advises setting the assist speed above the plane's stall speed. It gives no numeric multiple of stall speed or transition speed.

## Usable rules / numbers
- [transition_stall_ratio_min] No numeric multiple of stall speed for Q_ASSIST_SPEED. The page only advises a setting "above plane stall speed" after test flights with assistance disabled (section "Assisted Fixed-Wing Flight").
- [transition_stall_ratio_min] Transition airspeed is not mentioned on the page. Q_ASSIST_SPEED defaults to 0 (same section).

## How we could use it
- Confirms no numeric transition-to-stall bound on this page; does not support or change transition_stall_ratio_min.
