---
id: std-u171-p4-grepow-lihv-battery
title: High Voltage battery (LiHv)
authors: Grepow (battery maker)
year: unknown
url: https://www.grepow.com/lihv-battery
type: website
retrieved: 2026-11-25
verified: true
---

## Summary
Maker page describing high-voltage LiPo (LiHV) cells. It gives the nominal voltage per cell for standard and HV cells and the top-of-charge voltages for HV cells. It states no discharge cut-off voltage per cell.

## Usable rules / numbers
- [lipo_nominal_cell_v] Standard LiPo nominal voltage per cell: 3.6 to 3.7 V (typical range, definition). Quote: "The nominal voltage of normal-voltage cells is at 3.6-3.7V". Place: page introduction, page title "High Voltage battery (LiHv)".
- [lipo_nominal_cell_v, HV case] HV (LiHV) nominal voltage per cell: 3.8 to 3.9 V (typical range, definition). Quote: "the nominal voltage of high-voltage (LiHv) cells is at 3.8V-3.9V". Place: same page.
- [context] Standard cell full-charge voltage 4.2 V; HV cell charge cut-off 4.35, 4.4, 4.45 or 4.48 V. Place: same page.
- Discharge cut-off voltage per cell: not stated.

## How we could use it
- Feeds `lipo_nominal_cell_v`: the current 3.7 V matches the standard-cell nominal. An HV pack would need 3.8 V; this page gives 3.8 to 3.9 V for HV cells, so the note in the packet brief applies only if the design uses HV cells.
