---
id: std-u171-p2-px4-vtol-transition
title: Generic Standard VTOL (QuadPlane) Configuration, transition airspeed section (PX4 documentation)
authors: PX4 development team
year: unknown
url: https://docs.px4.io/main/en/config_vtol/vtol_quad_configuration.html
type: website
retrieved: 2026-11-25
verified: true
---

## Summary
PX4 documentation of the standard VTOL configuration. For the transition airspeed (VT_ARSP_TRANS) it advises an airspeed comfortably above the airframe stall speed, checked against FW_AIRSPD_MIN. It states no numeric relation and no default value.

## Usable rules / numbers
- [transition_stall_ratio_min] No numeric ratio. The transition airspeed is to be set "comfortably above your airframes stall speed" (transition airspeed section). The page says this is "currently not checked".
- [transition_stall_ratio_min] No transition airspeed default is given on the page read.

## How we could use it
- Confirms the PX4 page gives no numeric transition-to-stall bound; does not support or change transition_stall_ratio_min.
