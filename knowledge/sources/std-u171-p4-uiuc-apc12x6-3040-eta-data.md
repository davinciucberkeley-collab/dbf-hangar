---
id: std-u171-p4-uiuc-apc12x6-3040-eta-data
title: UIUC Propeller Database Volume 4 - APC 12x6 Thin Electric, wind-tunnel data file at 3040 RPM (apce_12x6_0630od_3040.txt)
authors: Dantsker, Caccamo, Deters, Selig (UIUC Applied Aerodynamics Group), data site
year: 2022
url: https://m-selig.ae.illinois.edu/props/volume-4/data/apce_12x6_0630od_3040.txt
type: website
retrieved: 2026-11-25
verified: true
---

## Summary
Text data file from the UIUC propeller wind-tunnel database (Volume 4, APC electric 2-blade propellers), opened on 2026-11-25. The file lists advance ratio J, thrust coefficient CT, power coefficient CP and efficiency eta in four columns. The volume page states that the four-digit number in each file name is the run RPM, so this file is the 12x6 run at 3040 RPM. The efficiency is propeller-only, not battery-to-thrust.

## Usable rules / numbers
- APC 12x6 Thin Electric, wind-tunnel run at 3040 RPM: eta = 0.642 at J = 0.352 (file line 7: 0.351626, 0.043995, 0.024092, 0.642123). Kind: measured point, not a bound. Place: data file, columns J, CT, CP, eta, file line 7 (line 1 is the header); run label from the volume page "Data" list for 12x6.
- Same run: eta = 0.506 at J = 0.230 (file line 4), and eta = 0.671 at J = 0.428 (file line 9). Place: same file.
- The file lists eta falling to near zero and then negative as J rises above about 0.6. The file rows from J 0.52 to 0.55 show eta 0.54 and 0.42. Place: same file, last rows.
- Volume 4 page, "Notes": coefficients are based on the propeller true diameter, and the four-digit number in the data names is the run RPM. Place: section "Notes" on the volume 4 page (propDB-volume-4.html).

## How we could use it
- propulsive_efficiency (standards key): this is propeller efficiency only, measured at stated J and RPM. It is not a battery-to-thrust or hover-point number, so it can only be an input to an efficiency chain, not the key value by itself.
