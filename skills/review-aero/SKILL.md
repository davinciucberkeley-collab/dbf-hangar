---
name: review-aero
description: Use when reviewing a design for aerodynamics, mass and CG: prop normal force, cruise lift, pitot placement, tuft checks; each item is answered PASS, FAIL or N/A with the standards key it was judged against.
---

# Review aerodynamics, mass and CG

## Goal
The aerodynamics, mass and CG section of `reviews/<date>-<design-id>.md`: every item answered PASS, FAIL or N/A with the standards key it was judged against.

## Agents
| Step | Role | Model |
|---|---|---|
| Every item of this section, one reviewer reused via SendMessage | reviewer | Opus |
| Fix or explain a named item the reviewer cannot answer from the design | design-engineer | Sonnet |

Never start one reviewer per item.

## Steps
Answer each item from the design, its README and the cited extract row.
- **cruise-cl**: Record the cruise lift coefficient at the gate mass and speed, with the wing area used (no limit set in the plan). (discipline-extract/J1.md#11)
- **pitot-placement**: Confirm the pitot projects ahead of the nose by the stated clearance, is out of the propeller flow, and its cover is fitted before power-up. (discipline-extract/J1.md#37)
- **prop-normal-force**: Confirm the propeller plane sits ahead of the centre of gravity by the stated distance (limit pending in standards/). (discipline-extract/J1.md#4)
- **station-band-check**: Confirm every station reading falls within the stated band (limit pending in standards/). (discipline-extract/G4.md#39)
- **tuft-check**: Confirm no tuft on the strip is driven by the slipstream. (discipline-extract/H1.md#44)

## Pass check
- [ ] Every item is answered PASS, FAIL or N/A with a one-line reason.
- [ ] Every PASS or FAIL cites a `standards/` key, or says pending.
- [ ] Every N/A says why the item does not apply.
- [ ] One reviewer was reused for the whole section.

## Stop rules
- The item needs a standards key that does not exist: say pending, and do not invent a key.
- The design has no lifting surface or mass to check: mark the section N/A and stop.
- The reviewer cannot answer an item from the design: send it to design-engineer once, then record it as pending.
