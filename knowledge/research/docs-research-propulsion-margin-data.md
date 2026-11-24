---
id: "docs-research-propulsion-margin-data"
title: "Propulsion margin data (R13 hover thrust-to-weight)"
kind: "research"
morph_cells: ["vtol_method:lift-plus-cruise"]
source_repo: DBF-Combined @ a93f14d
source_files: ["docs/research/propulsion-margin-data.md"]
created: 2026-11-23
verified: false
---

## Summary
A data note dated 2026-11-01 that tests whether the chosen lift motor, pack and connectors can meet requirement R13 (hover thrust-to-weight of at least 1.6) at about 6.95 kg MTOW. It reads the maker thrust tables for a 400 KV motor, looks for independent pack test data, and checks connector, ESC and landing-descent facts. Rows labelled EST are the note's own arithmetic.

## Key facts
- Each of four motors must give 2780 gf at 6.95 kg MTOW for T/W 1.6. From the maker tables on 6S (22.2 V), full-throttle T/W is 1.69 with a 16 in prop, 1.80 with 17 in and 1.90 with 18 in; at 25 V it is 2.07 to 2.14. [propulsion-margin-data.md section 1]
- At the R13 point the pack must supply about 82 to 98 A, above the 60 A continuous the project assumed for its LiPo. Thrust at sagging terminal voltage is not published. [propulsion-margin-data.md section 1]
- No independent voltage-under-load, internal-resistance or temperature data was found for the chosen 6500 mAh 100C pack, so its sag at the R13 current has to come from the team's own bench test. [propulsion-margin-data.md section 2]
- A 6S2P high-drain Li-ion option would have about 38 mohm of cell resistance (about 3.5 V sag at 90 A), 216 Wh and 852 g of cells. [propulsion-margin-data.md section 3]
- Connectors: an XT90 is rated 45 A continuous and 90 A for a minute on 10 AWG, so 82 to 98 A is beyond it; an XT60H at hover current is at 93 percent of its 30 A rating, and full-thrust current of 64 A exceeds its one-minute limit. [propulsion-margin-data.md section 4 and follow-up]
- The 45 A ESC (55 A for 10 s) runs at about half rating at 20 to 24 A per motor; its 18 AWG leads are the item to check. [propulsion-margin-data.md section 5]
- ArduPilot hover value 0.5 corresponds to T/W 2.0, and 0.3 to 0.6 to 1.7 to 3.3. [propulsion-margin-data.md section 6]
- Sources cited by DBF-Combined, not opened by this import: SunnySky maker tables, Ovonic shop page, Molicel data sheets, Amass connector datasheet, Holybro connector rating page, Horizon Hobby EC5 pages, an Amazon ESC listing. [propulsion-margin-data.md sections 1-5]

## Status in the study
none

## Open questions
- Published tables contain defects (an out-of-sequence row, identical rows for two prop sizes), so low-thrust rows for the 18 in prop are low confidence.
- Requiring hover thrust-to-weight at storage voltage is the project's own stricter choice for R13; none of the cited sources sets it that way.
- No in-stock 18 in prop of the required pitch was found and no maker table exists for an 18 by 5.5 in prop.
