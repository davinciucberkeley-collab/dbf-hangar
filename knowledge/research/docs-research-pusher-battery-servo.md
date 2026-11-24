---
id: "docs-research-pusher-battery-servo"
title: "Pusher propulsion, flight batteries, charger, servos: parts research"
kind: "research"
morph_cells: ["vtol_method:lift-plus-cruise"]
source_repo: DBF-Combined @ a93f14d
source_files: ["docs/research/pusher-battery-servo.md"]
created: 2026-11-23
verified: false
---

## Summary
Parts research dated 2026-10-13 for the pusher motor, prop and ESC, flight batteries, charger and control-surface servos of an 8 to 15 kg lift-plus-cruise VTOL cruising at 18 to 22 m/s on a $2,000 budget. These parts alone take about 46 to 48 percent of the budget. Cruise power and hover current are estimates built on assumed efficiencies.

## Key facts
- Sizing: cruise thrust is weight over a lift-to-drag of 10 (0.8 to 1.5 kgf); cruise electrical power is about 470 W (assuming prop efficiency 0.6 and motor efficiency 0.85); hover battery current is about 68 A on 6S. [pusher-battery-servo.md section 0]
- Pitch-speed check: a 14 by 7 in prop at full static RPM gives only 26 m/s, barely above top cruise; a 14 by 8.5 in prop (31.5 m/s) is the safer pusher prop. [pusher-battery-servo.md section 0]
- Pusher pick is a 550 KV long-shaft motor ($79.99, 218 g, 4.1 kgf static, 44.3 A at full throttle on a 14 by 7 in prop) with a 60 A, 5 V 7 A ESC ($41.99), leaving about 35 percent current margin; the 14 by 8.5 prop draws more and its current is unpublished. [pusher-battery-servo.md section 1]
- Battery picks: a 6S3P high-drain Li-ion pack (324 Wh, about 1.35 kg, $378, pre-order) is about 640 g lighter than a 6S 16 Ah LiPo (355 Wh, 1.99 kg, $335.99) and stores 31 Wh less. A 12S pack means two 6S packs in series, about $756 for 648 Wh. [pusher-battery-servo.md section 2]
- Charger: a 6S pack at 10 A needs 252 W; a 200 W unit gives only 7.9 A and fails, while a 400 W unit with a 24 V supply charges at about 15 A; the chosen pair totals $213.98. [pusher-battery-servo.md section 3]
- Servos: the 5 V ESC regulators run high-voltage servos below rated torque, and the 10 to 25 kg-cm hinge-moment band from the brief has not been computed. [pusher-battery-servo.md section 4]
- Sources cited by DBF-Combined, not opened by this import: T-Motor store pages, APC prop pages, WREKD, Tattu and ReadyMadeRC listings, SunnySky, Hobbywing Skywalker ESC, NextFPV note on air shipping. [pusher-battery-servo.md sections 1-5]

## Status in the study
none

## Open questions
- All thrust data is static bench data on tractor props; thrust in flight at 20 m/s will be lower.
- Measure pusher static thrust and current (fails if under 1.5 kgf at 60 percent throttle or over 55 A) (source item M1).
- Weigh delivered packs; the custom Li-ion pack spec and product-data weights disagree by 10 to 15 percent (M2).
- Pack voltage under 68 A is unmeasured; sag below 3.2 V per cell lowers endurance (M3).
- Pack transport and storage was skipped because the regulator page returned an error.
