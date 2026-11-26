---
id: part-servodatabase-emax-es08ma
title: 'ServoDatabase: EMAX ES08MA 2 servo specifications'
authors: ServoDatabase (community database; page notes most data is from the manufacturer, some from community submissions and AI, accuracy not guaranteed)
year: unknown
url: https://servodatabase.com/servo/emax/es08ma
type: website
retrieved: 2026-11-26
verified: true   # page opened 2026-11-26 via WebFetch; values below read from that page
---

## Summary
ServoDatabase lists an EMAX micro analog servo under the name "ES08MA 2" (product number 0102003010), with metal gears, 15-tooth spline, about 12 g and 23 x 11.5 x 24 mm. Rotation and torque figures are given for 4.8 V and 6.0 V. The page does not say "ES08MA II" anywhere we saw.

## Model match
- Page model string: "ES08MA 2" (EMAX ES08MA 2). Page does not use the words "ES08MA II".
- Modelled part: knowledge/parts/emax-es08maii-metal/part.yaml (EMAX ES08MA II, EMX-SV-0275). Assumed to be the same product, but this page does not state that equivalence.
- Mismatch: none in the stated numbers (weight 12 g and dimensions 23 x 11.5 x 24 mm match part.yaml). The model-name equivalence "ES08MA 2" = "ES08MA II" is unconfirmed by this page.
- Original ES08MA vs ES08MA II: the page does not say which generation it describes beyond the "2" suffix.

## Usable rules / numbers
- Rotational Range: "Rotational Range" 95 deg (Control & Signal section). Usable travel for linkage design.
- Mechanical Limit: "Mechanical Limit" 360 deg (Control & Signal section). Not the usable range; continuous or mechanical stop value as listed.
- Torque (Performance section): 6.0 V 2.02 kg-cm (28.00 oz-in, 0.2 N-m); 4.8 V 1.50 kg-cm (20.83 oz-in, 0.1 N-m).
- Speed (Performance section): 6.0 V 0.10 sec/60 deg (600.0 deg/s, 100.0 RPM); 4.8 V 0.12 sec/60 deg (500.0 deg/s, 83.3 RPM).
- Operating voltage (Electrical & Environment section): 4.8 to 6 V.
- Weight (Physical section): 0.42 oz, 12.0 g.
- Dimensions (Physical section): L 23.0 mm, W 11.5 mm, H 24.0 mm (L 0.906 in, W 0.453 in, H 0.945 in).
- Gear type (Drivetrain section): "Metal" gears; 15 T spline.

## How we could use it
- Travel input for the servo-travel check in the linkage/deflection step: 95 deg rotational range is the value to compare against the design's commanded deflection (not the 360 deg mechanical limit).
- Cross-check for the part.yaml envelope (mass and dimensions agree); torque and speed can feed actuator sizing once the model match is confirmed.
