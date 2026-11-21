---
name: review-controls
description: Use when reviewing a design for controls: stability, avionics, flight software, RC link and failsafes; each item is answered PASS, FAIL or N/A with the standards key it was judged against.
---

# Review controls

## Goal
The controls section of `reviews/<date>-<design-id>.md`, covering stability and control, avionics, flight software and the RC link: every item answered PASS, FAIL or N/A with the standards key it was judged against.

## Agents
| Step | Role | Model |
|---|---|---|
| Every item of this section, one reviewer reused via SendMessage | reviewer | Opus |
| Fix or explain a named item the reviewer cannot answer from the design | design-engineer | Sonnet |

Never start one reviewer per item.

## Steps
Answer each item from the design, its README and the cited extract row.
- **airspeed-calibration**: Confirm airspeed calibration from reciprocal legs at cruise speed on the racetrack, with error within the requirement (limit pending in standards/). (discipline-extract/H2.md#49)
- **airspeed-fallback**: Confirm the baseline minimum airspeed holds the largest gate-mass stall, above the tripped stall speed (limit pending in standards/). (discipline-extract/B2.md#23)
- **airspeed-fallback**: Confirm the second fallback maximum airspeed is at or below full-travel speed (limit pending in standards/). (discipline-extract/B2.md#24)
- **airspeed-fallback**: Confirm the section clmax ratio covered by the second fallback is at or below the trip ratio (limit pending in standards/). (discipline-extract/B2.md#25)
- **airspeed-sensor**: Confirm the airspeed sensor reading rises on a blow and falls on suction, if a sensor is fitted. (discipline-extract/G4.md#33)
- **airspeed-sensor**: Confirm the airspeed sensor type is set to none, and any sensor is used only in the fixed-wing mode, before purchase. (discipline-extract/H2.md#46)
- **arming-interlock**: Confirm arming is refused while the spin-cap script reports its fault (limit pending in standards/). (discipline-extract/F4.md#65)
- **bench-channels**: Confirm on the bench that the motor map, rotation directions and elevon channels are all correct against the wiring plan. (discipline-extract/H2.md#17)
- **failsafe-check**: Confirm no failsafe triggers during the range check (limit pending in standards/). (discipline-extract/H1.md#119)
- **failsafe-map**: Confirm RC loss maps to a land or return mode, and the geofence matches the flight-rules polygon with its altitude ceiling (limit pending in standards/). (discipline-extract/A2.md#29)
- **fbwa-trim**: Record the FBWA trim elevon deflection at cruise speed; no pass line is set in the plan (limit pending in standards/). (discipline-extract/H2.md#45)
- **fc-sku-check**: Confirm the flight controller SKU is the wing variant, the power board and capacitor are fitted, and the board check runs the same day. (discipline-extract/I1.md#33)
- **flex-loop-margin**: Confirm the hover pitch loop gain margin with the torsion mode stays at or above its minimum (limit pending in standards/). (discipline-extract/B3.md#55)
- **flex-loop-margin**: Confirm the hover yaw loop gain margin with the antisymmetric torsion mode stays at or above its minimum (limit pending in standards/). (discipline-extract/B3.md#56)
- **flex-loop-margin**: Confirm the flexible hover pitch and yaw phase margins each stay at or above the phase margin minimum (limit pending in standards/). (discipline-extract/B3.md#57)
- **fsw-params**: Check the tailsitter parameter file sets the enable flags, frame class, frame type and option bits the airframe needs. (discipline-extract/A2.md#27)
- **harmonic-notch**: Confirm the harmonic notch uses ESC rpm telemetry, with its harmonics centred on the once-per-revolution sweep range. (discipline-extract/J1.md#26)
- **loop-crossover**: Confirm the highest hover pitch crossover, at the stated gain and phase margins, stays at or above its minimum (limit pending in standards/). (discipline-extract/B3.md#58)
- **loop-crossover**: Confirm the highest hover yaw crossover stays at or above its minimum (limit pending in standards/). (discipline-extract/B3.md#59)
- **neutral-point**: Confirm the neutral point from elevon trim against lift coefficient has zero slope (limit pending in standards/). (discipline-extract/H2.md#23)
- **param-readback**: Run the flight software parameter check before flight and write the file hash to the flight row. (discipline-extract/H2.md#72)
- **param-update**: Set the per-motor thrust limit parameter to the measured peak, rounded up to the stated resolution (limit pending in standards/). (discipline-extract/H1.md#32)
- **rc-failsafe-mode**: Confirm the receiver failsafe mode is No Pulses, set and read back after a power cycle. (discipline-extract/F5.md#22)
- **rc-variant**: Confirm the radio is the regional variant for the operating region, not the other variant. (discipline-extract/I1.md#34)
- **rx-power-source**: Confirm the receiver is powered from the flight controller rail, not the servo or BEC rail, and check its rail voltage (limit pending in standards/). (discipline-extract/F5.md#28)
- **tailsitter-handover**: Confirm the tailsitter handover angle is set and sits above the horizon by the designed margin (limit pending in standards/). (discipline-extract/J1.md#27)
- **transition-mode**: Confirm no transition is commanded from hover modes, no automatic transition is allowed, and doubt aborts to hover. (discipline-extract/H2.md#53)
- **weathervane**: Confirm weathervane is enabled with its starting gain and minimum angle, and allowed only in hover, loiter, land and return modes (limit pending in standards/). (discipline-extract/J1.md#30)
- **yaw-damper**: Set the fixed-wing yaw damper gain from the builder convention range, with rudder-mix feedforward at zero (limit pending in standards/). (discipline-extract/J1.md#29)
- **yaw-doublet**: Confirm after a yaw doublet at test speed that heading and sideslip return within the stated time (limit pending in standards/). (discipline-extract/H2.md#26)

## Pass check
- [ ] Every item is answered PASS, FAIL or N/A with a one-line reason.
- [ ] Every PASS or FAIL cites a `standards/` key, or says pending.
- [ ] Every N/A says why the item does not apply.
- [ ] One reviewer was reused for the whole section.

## Stop rules
- The item needs a standards key that does not exist: say pending, and do not invent a key.
- The design has no flight controller or RC link to check: mark the section N/A and stop.
- The reviewer cannot answer an item from the design: send it to design-engineer once, then record it as pending.
