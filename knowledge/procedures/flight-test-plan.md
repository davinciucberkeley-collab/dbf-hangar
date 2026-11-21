---
id: flight-test-plan
title: Flight Test Plan
topic: flight-test-plan
source_repo: DBF-Combined @ a93f14d
source_rows: [H2#18, H2#41, H2#50, J1#42]
created: 2026-11-21
verified: false
---

## Purpose
The flight test gates in order: hanging yaw test, landings, and cruise polar legs. Also the planning figures for the learning curve. Run at each gate.

## Steps
1. Gate 1b: on the hanging yaw test, yaw the frame -x then +x with motors UR+LL, then UL+LR, at 15 % [H2#18]
2. Gate 4: land belly into wind, using QLAND for the last 6 m at 0.3 m/s, with RC9 cut at contact [H2#41]
3. Gate 5: fly 200 m straights, three laps at 14, 16 and 18 m/s [H2#50]

## Checks and stop conditions
- Gate 4: 20 touchdowns over at least 10 sorties, and no more than 2 per sortie [H2#41]

## Notes
- (K09-L value) Gate 5 calm leg times 14.3 / 12.5 / 11.1 s; far points 163.8 / 177.9 / 193.4 m (plan_checks.py) [H2#50]
- Planning figures, not limits: 3-6 weeks from first stable hover to first clean round trip; 30-40 flight-test hours [J1#42]
