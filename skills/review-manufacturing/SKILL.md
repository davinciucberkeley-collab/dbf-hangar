---
name: review-manufacturing
description: Use when reviewing a design for manufacturing: process, printing, composites and foam, assembly; each item is answered PASS, FAIL or N/A with the standards key it was judged against.
---

# Review manufacturing

## Goal
The manufacturing section of `reviews/<date>-<design-id>.md`, covering process, printing, composites, foam and assembly: every item answered PASS, FAIL or N/A with the standards key it was judged against.

## Agents
| Step | Role | Model |
|---|---|---|
| Every item of this section, one reviewer reused via SendMessage | reviewer | Opus |
| Fix or explain a named item the reviewer cannot answer from the design | design-engineer | Sonnet |

Never start one reviewer per item.

## Steps
Answer each item from the design, its README and the cited extract row.
- **assembly**: Confirm tubes are vertical and parallel at the tube alignment step. (discipline-extract/G4.md#15)
- **block-fit**: Confirm blocks and frames drop in with no corner contact. (discipline-extract/G2.md#18)
- **chemical-safety**: Confirm epoxy and cyanoacrylate work uses nitrile gloves and ventilation, and no cyanoacrylate or solvent glue touches foam. (discipline-extract/G1.md#38)
- **colour-coding**: Confirm one colour is printed and colour codes are marked with a paint pen, not a second filament colour. (discipline-extract/G3.md#16)
- **core-handling**: Confirm slotted cores are never lifted out of their bed. (discipline-extract/G2.md#20)
- **fillet-keepout**: Confirm no filler is in lead holes or elevon gaps, and no fillet is on the lower link-slot zone. (discipline-extract/G2.md#32)
- **hot-wire-safety**: Confirm the hot wire is never left powered unattended and runs at the lowest current that cuts cleanly. (discipline-extract/G1.md#36)
- **jig-material**: Confirm jigs and drill guides are printed in PLA, not PETG, and no flight load passes through them. (discipline-extract/G3.md#5)
- **lab-access**: Confirm lab equipment is used in the lab only, with no loans, and the hot-wire gear purchase is recorded. (discipline-extract/I1.md#45)
- **le-quality**: Confirm the leading edge has no wire step or ridge, checked by hand. (discipline-extract/G2.md#8)
- **material-grade**: Confirm cartridge stock is the grade named in the landing parts list, and the bill of materials records the offcut grade. (discipline-extract/G4.md#36)
- **pod-box-accept**: Confirm the pod has cured for its full time, the box is square, the tray is flat and the saddles seat the wing (limit pending in standards/). (discipline-extract/G2.md#39)
- **printer-access**: Confirm PETG printing is available at the lab, asking staff or using a team printer if it is not confirmed. (discipline-extract/G3.md#14)
- **printer-access**: Confirm PLA printing for jigs and shop aids is available at the lab at no charge. (discipline-extract/G3.md#15)
- **printer-class**: Confirm each part's material maps to the printer class it needs: enclosed for ASA, direct drive for TPU, standard for the rest. (discipline-extract/G3.md#4)
- **printing**: Confirm ASA is printed only on an enclosed printer, and the lab's open-use list is checked first. (discipline-extract/G1.md#35)

## Pass check
- [ ] Every item is answered PASS, FAIL or N/A with a one-line reason.
- [ ] Every PASS or FAIL cites a `standards/` key, or says pending.
- [ ] Every N/A says why the item does not apply.
- [ ] One reviewer was reused for the whole section.

## Stop rules
- The item needs a standards key that does not exist: say pending, and do not invent a key.
- The design has no printed or composite part to check: mark the section N/A and stop.
- The reviewer cannot answer an item from the design: send it to design-engineer once, then record it as pending.
