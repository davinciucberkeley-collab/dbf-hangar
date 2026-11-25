---
id: std-u171-p4-rchelicopterfun-lipo-batteries
title: LiPo Batteries (RC helicopter fun guide, John Salt)
authors: John Salt (rchelicopterfun.com)
year: unknown
url: https://rchelicopterfun.com/lipo-batteries.html
type: website
retrieved: 2026-11-25
verified: true
---

## Summary
Named RC-hobby reference by an individual author, with stated use conditions for each rule. It gives a usable-capacity rule of 80 percent for a healthy pack at full rated capacity, a stricter 70 percent for aggressive or high-current flying, and a per-cell low-voltage setting of 3.4 V under load. It gives no internal-resistance or sag values and no nominal voltage per cell.

## Usable rules / numbers
- [battery_usable_fraction] "you should never discharge a Li-Po pack down past 80% of its CAPACITY to be safe": maximum usable fraction 0.8 of rated capacity. Condition: healthy pack at full rated capacity. Place: section "Discharging: THE 80% LIPO BATTERY RULE".
- [battery_usable_fraction, aggressive use] "nothing past 70% discharged is much better for the pack": maximum usable fraction 0.7. Condition: aggressive 3D flying or consistently high-current models. Place: section "Discharging: 80% Rule Caveat For Aggressive Flying".
- [context] Author's LVC setting: 3.4 V per cell (recommended setting, condition not stated). Place: section "Discharging: Over Discharging LiPo's".
- [context] "never lower than 3 volts per cell while Under Load": minimum voltage under load. Place: section "Discharging: Over Discharging LiPo's".
- [context] Open-circuit check: about 3.74 V per cell at 80 percent discharge, measured right after flight. Place: section "Discharging: THE 80% LIPO BATTERY RULE".
- Nominal voltage per cell: not stated. Reserve for a flight as a percentage: not stated.

## How we could use it
- Feeds `battery_usable_fraction`: an RC-hobby source with a stated condition (healthy pack, full rated capacity) gives the 0.8 maximum; it is not a cell maker datasheet, so the packet table records the tier.
- Context for the energy-reserve discussion: no reserve fraction is given.
