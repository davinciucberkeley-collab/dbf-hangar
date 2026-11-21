---
name: review-propulsion
description: Use when reviewing a design for propulsion: motors, props, power, energy, thermal and harness; each item is answered PASS, FAIL or N/A with the standards key it was judged against.
---

# Review propulsion

## Goal
The propulsion section of `reviews/<date>-<design-id>.md`, covering motors, propellers, power, energy, thermal and harness: every item answered PASS, FAIL or N/A with the standards key it was judged against.

## Agents
| Step | Role | Model |
|---|---|---|
| Every item of this section, one reviewer reused via SendMessage | reviewer | Opus |
| Fix or explain a named item the reviewer cannot answer from the design | design-engineer | Sonnet |

Never start one reviewer per item.

## Steps
Answer each item from the design, its README and the cited extract row.
- **esc-listing**: Confirm the ESC listing title, rated current, piece count and price before the order is placed. (discipline-extract/I1.md#35)
- **incoming-inspection**: Inspect each incoming motor for weight, winding pattern, hole depth, E-clip and phase resistance before fitting. (discipline-extract/G4.md#31)
- **motor-direction**: Confirm each motor turns in its stated direction, and every screw and nut carries a witness mark. (discipline-extract/G4.md#27)
- **motor-out-handling**: Confirm the motor-out handling rule is a throttle cut into a glide, as written in the flight card. (discipline-extract/F4.md#61)
- **pack-capacity**: Check pack capacity at 1C to the cell cut-off voltage meets the minimum fraction of rated capacity (limit pending in standards/). (discipline-extract/A2.md#14)
- **pack-spec**: Confirm the pack cell count, discharge rating and connector match the propulsion spec, and the wrong connector SKU is not ordered. (discipline-extract/I1.md#32)
- **prop-hand-check**: Hand-check each prop adapter nut tightens under prop torque, and left-hand threads are used where motor direction requires. (discipline-extract/H1.md#16)
- **prop-selection**: Check the hover pack power ratio of the chosen prop against the baseline prop at gate mass (limit pending in standards/). (discipline-extract/B4.md#7)
- **punch-test**: Confirm every punch sample passes clean, with none failed (count limit pending in standards/). (discipline-extract/H1.md#22)
- **thermal**: Check the hover winding temperature rise is within its limit at the rated speed (limit pending in standards/). (discipline-extract/E1.md#4)
- **thermal**: Check the pack temperature at landing on the worst morning is within its limit (limit pending in standards/). (discipline-extract/E2.md#8)
- **thermal**: Confirm the ESC pad clears the contracted slipstream with a non-negative radial margin (limit pending in standards/). (discipline-extract/E3.md#24)
- **thermal**: Confirm the measured CFD factor meets or exceeds the design value for hover and cruise (limit pending in standards/). (discipline-extract/E3.md#35)

## Pass check
- [ ] Every item is answered PASS, FAIL or N/A with a one-line reason.
- [ ] Every PASS or FAIL cites a `standards/` key, or says pending.
- [ ] Every N/A says why the item does not apply.
- [ ] One reviewer was reused for the whole section.

## Stop rules
- The item needs a standards key that does not exist: say pending, and do not invent a key.
- The design has no propulsion or energy system to check: mark the section N/A and stop.
- The reviewer cannot answer an item from the design: send it to design-engineer once, then record it as pending.
