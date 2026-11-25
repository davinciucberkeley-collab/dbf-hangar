---
id: std-u171-p5-ac43-13-1b-ch11-wiring
title: FAA AC 43.13-1B Chapter 11, Aircraft Electrical Systems (wire routing, clearance and current tables)
authors: Federal Aviation Administration
year: 1998
url: https://www.faasafety.gov/files/events/SO/SO35/2020/SO35100907/AC_43.13_Chapter_11_Electrical.pdf
type: standard
retrieved: 2026-11-25
verified: true
---

## Summary
The FAA advisory circular chapter gives minimum separations for wiring: a protective grommet clearance from structure at penetrations, a separation from movable controls, and a separation from flammable fluid lines. Current-carrying values are given as tables and curves, and the derating factors are curves that the text layer did not give as numbers. I opened the chapter PDF in this run (the FAA copy as hosted on faasafety.gov) and read the text layer for pages 11-23, 11-25, 11-51, and 11-53 to 11-54.

## Usable rules / numbers
- [wire clearance, structure] Protective grommets: at least 3/8 inch (9.525 mm, exact 3/8 x 25.4) clearance from structure at penetrations, where wires cannot be clamped. Kind: minimum. Place: par. 11-115, p. 11-51.
- [wire clearance, movable controls] Minimum separation between wiring and movable controls: at least 1/2 inch (12.7 mm) when the bundle is displaced by light hand pressure. Kind: minimum. Place: par. 11-125, p. 11-53.
- [wire clearance, flammable fluid lines] Route wiring above oxygen, oil, fuel, hydraulic fluid or alcohol lines with 6 inches (152.4 mm) separation whenever possible; otherwise at least 2 inches (50.8 mm), unless positively clamped to keep at least 1/2 inch (12.7 mm). Kind: minimum. Place: par. 11-126, pp. 11-53 to 11-54.
- [bundle derating] Bundle derating factors are given as curves (Figure 11-5, par. 11-69 and 11-67); the text layer gave no numeric factor. Place: par. 11-67, p. 11-25.
- [connector limit] Par. 11-67 states that the contact rating can govern the maximum current in a wire, not the wire rating. Place: par. 11-67, p. 11-25 (text, no number).
- [current table, pointer only] Table 11-9 (continuous duty current, copper, bundled, 70 C ambient) is on p. 11-23. Values are not copied here; ampacity is covered by std-wire-ampacity.

## How we could use it
- `wire_clearance_mm` (gate-thresholds.yaml): the three minimum separations above (9.525 mm, 12.7 mm, 50.8 mm or 12.7 mm when clamped) are the only numeric minima in this chapter; each applies to a different route component.
- `electrical_rating_min_ratio` (operations.yaml): the chapter gives no numeric minimum ratio; derating is curve-only in the text layer, so the ratio stays pending.
