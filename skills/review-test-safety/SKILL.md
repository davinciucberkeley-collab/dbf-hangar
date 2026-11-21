---
name: review-test-safety
description: Use when reviewing a design for test and safety: ground and flight test, safety, go/no-go; each item is answered PASS, FAIL or N/A with the standards key it was judged against.
---

# Review test and safety

## Goal
The test and safety section of `reviews/<date>-<design-id>.md`, covering ground test, flight test, safety and go/no-go: every item answered PASS, FAIL or N/A with the standards key it was judged against.

## Agents
| Step | Role | Model |
|---|---|---|
| Every item of this section, one reviewer reused via SendMessage | reviewer | Opus |
| Fix or explain a named item the reviewer cannot answer from the design | design-engineer | Sonnet |

Never start one reviewer per item.

## Steps
Answer each item from the design, its README and the cited extract row.
- **build-safety**: Confirm the build-safety callout marks LiPo, prop, hot-wire and solvent hazards as stop-level. (discipline-extract/J5.md#16)
- **compliance-check**: Confirm the registration marking is legible, securely attached and on an external surface. (discipline-extract/H3.md#75)
- **compliance-check**: Confirm Remote ID status, and any flight without it stays inside the FRIA boundary with aircraft and pilot inside it; verify on the FAA map. (discipline-extract/H3.md#76)
- **compliance-check**: Confirm each pilot holds a current TRUST certificate before flying. (discipline-extract/H3.md#77)
- **crew-roles**: Confirm the crew roles are pilot, spotter, logger and safety lead, with no one doubling the pilot role. (discipline-extract/H3.md#70)
- **fatigue-limit**: Confirm the flights-per-session and rest limits for each pilot are set in the card, not left blank (limit pending in standards/). (discipline-extract/H3.md#63)
- **fence-recovery**: Confirm the aircraft refuses a mode switch during fence recovery, as the flight card follow-up requires. (discipline-extract/F4.md#64)
- **first-hover-entry**: Confirm each first-hover entry gate is met: prior gates passed, simulator time logged, flight-rules request accepted, range check passed, card signed (limit pending in standards/). (discipline-extract/G4.md#43)
- **go-around-triggers**: Confirm go-around is called on drift beyond the stated distance, tilt beyond the stated angle, a spotter call, a link warning or a gust above the card (limit pending in standards/). (discipline-extract/H3.md#47)
- **hover-hold**: Confirm the aircraft holds the hover point for the stated duration at the stated thrust (limit pending in standards/). (discipline-extract/H1.md#23)
- **landing-site**: Confirm the landing mat is the required size and level within tolerance, with slope room for a calm landing (limit pending in standards/). (discipline-extract/C5.md#71)
- **lipo-retermination**: Confirm LiPo leads are re-terminated only below the cell voltage limit, one lead bare at a time, in the electronics lab (limit pending in standards/). (discipline-extract/G1.md#37)
- **post-contact-spin-down**: Confirm the spin-down starts at once after contact, and the tilt rule for the spin-down is met (limit pending in standards/). (discipline-extract/C5.md#74)
- **prearm-checks**: Confirm every pre-arm check passes on the assembled aircraft before arming. (discipline-extract/G4.md#32)
- **range-check**: Confirm no failsafe triggers during the range check (limit pending in standards/). (discipline-extract/F5.md#14)
- **range-check**: Confirm no witness mark has moved and the range check has passed before flight. (discipline-extract/G4.md#40)
- **site-approval**: Confirm the site approval covers only the stated flight-rules sub-fields, with aircraft and pilot inside the approved area and aircraft in sight. (discipline-extract/H3.md#7)
- **site-rules**: Confirm the flight rules are met: approved sub-fields, altitude ceiling, visual line-of-sight range and the card time window (limit pending in standards/). (discipline-extract/A2.md#41)
- **spin-test**: Confirm the spin test for motor direction is run at low throttle with props removed (limit pending in standards/). (discipline-extract/G4.md#28)
- **wind-check**: Confirm the flight-rules wind and the station wind agree across the required mornings, within the wind ratio limit (limit pending in standards/). (discipline-extract/A2.md#46)
- **wind-ratio**: Check the flight-rules wind against the station reading; if the ratio exceeds its limit, rescale the card or apply the stated reversal (limit pending in standards/). (discipline-extract/H3.md#3)
- **wind-ratio**: Confirm the station wind limit is rescaled by the wind ratio when the ratio is between the stated bounds (limit pending in standards/). (discipline-extract/H3.md#5)

## Pass check
- [ ] Every item is answered PASS, FAIL or N/A with a one-line reason.
- [ ] Every PASS or FAIL cites a `standards/` key, or says pending.
- [ ] Every N/A says why the item does not apply.
- [ ] One reviewer was reused for the whole section.

## Stop rules
- The item needs a standards key that does not exist: say pending, and do not invent a key.
- The flight or test plan is absent: mark the section N/A and stop.
- The reviewer cannot answer an item from the design: send it to design-engineer once, then record it as pending.
