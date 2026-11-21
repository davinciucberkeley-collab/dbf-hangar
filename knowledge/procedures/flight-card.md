---
id: flight-card
title: Flight Card
topic: flight-card
source_repo: DBF-Combined @ a93f14d
source_rows: [A2#45, F4#56, F4#57, F4#58, F4#59, F5#29, F5#45, H3#35, H3#36, H3#37, H3#43, H3#48]
created: 2026-11-21
verified: false
---

## Purpose
The order of actions and checks for each flight, from power-up through transition, landing and turnaround. Run for every flight.

## Steps
1. Power up with the TX on before the pack is plugged in [F5#29]
2. Close the hatch no more than 2 min before take-off [H3#43]
3. Hover in QHOVER or QLOITER for at least 60 s before transition [F5#45]
4. Move to QSTABILIZE with the stick near mid, at or above 50 m AGL, to transition [F5#45] [A2#45]
5. Land with QLAND, or with RTL ending in QLAND, for the last 6 m [F4#57]
6. Hold full down stick in QHOVER or QLOITER to descend [F4#58]
7. Land with the final approach at 0.5 m/s and the wingtip into wind [F4#59]
8. Spin the props down at once after contact [H3#35]
9. Lay the aircraft flat between flights, with the pack out and on the mat, unless gusts are at or below 5 m/s [H3#36]
10. Check the foot groove after every landing [H3#37]

## Checks and stop conditions
- Do not land in QSTABILIZE except to recover [F4#56]
- Cut RC9 at contact, and RCOU minimum within 0.5 s after contact [F4#59]
- Go-around: climb to at least 10 m (EST) in QLOITER; one go-around only, then an alternate spot [H3#48]

## Notes
- (K09-L value) Transition at 50 m or more (transition_alt_min_m 50) [A2#45]
- (K09-L value) Current within +/-0.15, reference not given in the row [A2#45]
- (K09-L value) Q_LAND_FINAL_ALT 6 m [F4#57]
- (K09-L value) Q_PILOT_SPD_DN 1.0 m/s for full down stick [F4#58]
- (K09-L value) Q_WVANE_LAND 1 per R7; 3 in R4 [F4#59]
