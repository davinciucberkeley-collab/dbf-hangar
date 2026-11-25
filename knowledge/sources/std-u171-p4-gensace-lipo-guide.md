---
id: std-u171-p4-gensace-lipo-guide
title: LiPo Battery Guide (Gens Ace)
authors: Gens Ace (GensAce / Grepow group)
year: unknown
url: https://gensace.de/pages/lipo-battery-guide
type: website
retrieved: 2026-11-25
verified: true
---

## Summary
Maker guide page from the Gens Ace battery brand. It states the nominal voltage of one LiPo cell, a storage voltage range, and a per-cell discharge floor under load. It also gives a Tattu UAS cut-off figure, which applies to a sister brand and is not a Gens Ace figure. It gives no internal resistance, voltage-sag or depth-of-discharge values.

## Usable rules / numbers
- [lipo_nominal_cell_v] Nominal voltage of one LiPo cell: 3.7 V (definition). Place: sections "Battery Voltage" and "Cell Configuration".
- [battery_usable_fraction, context] "Never discharge battery to a level below 3V per cell under load" (minimum voltage, under load). Place: section "Discharging".
- [context, not a Gens Ace figure] Recommended cut-off for Tattu UAS batteries: 3.5 V per cell (minimum voltage). Place: section "Discharging".
- [context] Long-term storage range: 3.6 V to 3.9 V per cell (storage range, not a discharge limit). Place: section "Lipo Battery Storage".
- Depth of discharge, usable-capacity percentage, internal resistance and C-rating voltage sag: not stated on this page.

## How we could use it
- Feeds `lipo_nominal_cell_v`: confirms the 3.7 V per-cell nominal for standard LiPo cells.
- Context only for `battery_usable_fraction`: gives the per-cell voltage floor, not a usable-capacity fraction.
