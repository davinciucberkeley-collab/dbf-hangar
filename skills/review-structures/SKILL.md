---
name: review-structures
description: Use when reviewing a design for structures: loads, joints, modal separation, proof path and coupon records; each item is answered PASS, FAIL or N/A with the standards key it was judged against.
---

# Review structures

## Goal
The structures section of `reviews/<date>-<design-id>.md`: every item answered PASS, FAIL or N/A with the standards key it was judged against.

## Agents
| Step | Role | Model |
|---|---|---|
| Every item of this section, one reviewer reused via SendMessage | reviewer | Opus |
| Fix or explain a named item the reviewer cannot answer from the design | design-engineer | Sonnet |

Never start one reviewer per item.

## Steps
Answer each item from the design, its README and the cited extract row.
- **coupon-record**: Record the modulus and strength of each foam coupon, with no pass limit set in the plan (limit pending in standards/). (discipline-extract/H1.md#126)
- **modal**: Confirm first bending and torsion frequencies sit outside the once-per-revolution band, and flight controller vibration is within its limit (limit pending in standards/). (discipline-extract/A2.md#21)
- **modal**: Confirm the torsion-mode damping assumed for the gain and phase margin checks is stated and sourced. (discipline-extract/B3.md#70)
- **modal**: Confirm the once- and twice-per-revolution frequency bands for each hover rpm window stay clear of the structural modes (limit pending in standards/). (discipline-extract/H1.md#156)
- **modal**: Check the bare motor-tube first bending mode across the full modulus range stays clear of the once-per-revolution band (limit pending in standards/). (discipline-extract/J1.md#5)
- **post-impact-inspection**: Inspect shoe bonds, fin tips, wingtip caps, props, mounts, pod nose and block after any hard landing or tip-over. (discipline-extract/H3.md#38)
- **proof-inspection**: Inspect the wing after proof load for cracks, wrinkles, bond-line separation and core crush, by sight and tap. (discipline-extract/H1.md#81)
- **proof-path-decision**: Choose the shell proof path if face strain at the proof load exceeds the shell threshold (limit pending in standards/). (discipline-extract/H1.md#88)
- **proof-path-decision**: Conclude the strips are not clamped if measured strip strain falls below the clamp threshold (limit pending in standards/). (discipline-extract/H1.md#89)
- **proof-path-decision**: Select the three-dimensional proof path if pad deflection at proof load is within the geometric-mean limit (limit pending in standards/). (discipline-extract/H1.md#90)
- **tube-material-E**: Confirm the tube modulus used in the modal and stiffness checks lies within the sourced range for the tube type (limit pending in standards/). (discipline-extract/J1.md#24)

## Pass check
- [ ] Every item is answered PASS, FAIL or N/A with a one-line reason.
- [ ] Every PASS or FAIL cites a `standards/` key, or says pending.
- [ ] Every N/A says why the item does not apply.
- [ ] One reviewer was reused for the whole section.

## Stop rules
- The item needs a standards key that does not exist: say pending, and do not invent a key.
- The design has no structure to check: mark the section N/A and stop.
- The reviewer cannot answer an item from the design: send it to design-engineer once, then record it as pending.
