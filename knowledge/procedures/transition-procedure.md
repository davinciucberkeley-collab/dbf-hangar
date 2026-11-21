---
id: transition-procedure
title: Transition Procedure
topic: transition-procedure
source_repo: DBF-Combined @ a93f14d
source_rows: [F4#60, F5#39, F5#41]
created: 2026-11-21
verified: false
---

## Purpose
Setting up the switch and pitch-over for the transition from hover to cruise. Run before each transition and after any RC3 change.

## Steps
1. Calibrate RC3 at stick low and at stick high [F5#41]
2. Set the flight-mode pulse bands to the ArduPilot control_in mode thresholds [F5#39]
3. Pitch over at 12 deg/s during the transition [F4#60]

## Checks and stop conditions
- Keep the pitch-over at this rate until the logs show a peak at or below 0.7 [F4#60]

## Notes
- (K09-L value) RC3 low 988 +/- 2 us and high 2012 +/- 2 us; re-run the table if RC3 changes [F5#41]
- (K09-L value) Mode pulse bands 1231 / 1361 / 1491 / 1621 / 1750 us; slot pulses 1167 / 1295 / 1423 / 1556 / 1684 / 1817 us [F5#39]
- The 0.7 peak value is still open in the change requests (CR-F4-10; CR-B1-12 rev 3) [F4#60]
