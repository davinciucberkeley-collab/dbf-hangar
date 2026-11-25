---
id: std-u171-p4-aiaa-2022-4020-apc-props
title: Performance Testing of APC Electric Fixed-Blade UAV Propellers (AIAA Paper 2022-4020)
authors: Dantsker, Caccamo, Deters, Selig (University of Illinois Urbana-Champaign)
year: 2022
url: https://m-selig.ae.illinois.edu/pubs/DantskerCaccamoDetersSelig-2022-AIAA-Paper-2022-4020-APCEPropTestsVol4.pdf
type: paper
retrieved: 2026-11-25
verified: true
---

## Summary
Conference paper that describes the wind-tunnel test of APC electric fixed-blade propellers behind which the UIUC volume 4 data files were measured. The paper defines the thrust coefficient, power coefficient, advance ratio and propeller efficiency, and gives the efficiency as a function of CT, CP and J. Opened and read on 2026-11-25 (text layer, pages 5 of 26 and the definitions around them).

## Usable rules / numbers
- Thrust coefficient CT = T / (n^2 D^4), with n the rotation rate and D the diameter. Definition. Place: section on performance coefficients, equation (3), page 5 of 26.
- Power coefficient CP = P / (n^3 D^5). Definition. Place: same section, equation (4), page 5 of 26.
- Advance ratio J = V / (n D). Definition. Place: equation (5), page 5 of 26.
- Propeller efficiency eta = (T V) / P, and in terms of the coefficients eta = (CT / CP) x J. Definition. Place: equations (6) and (7), page 5 of 26, under the heading on propeller efficiency.

## How we could use it
- propulsive_efficiency (standards key): supplies the definition of eta used by the UIUC volume 4 data files (eta = CT J / CP). It defines propeller efficiency only, not battery-to-thrust efficiency.
