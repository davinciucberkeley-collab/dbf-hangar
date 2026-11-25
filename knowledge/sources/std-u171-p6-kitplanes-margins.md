---
id: std-u171-p6-kitplanes-margins
title: Stressing Structure: Margins of Safety (Kitplanes magazine article by David Paule)
authors: David Paule
year: 2015
url: https://www.kitplanes.com/stressing-structure-2/
type: website
retrieved: 2026-11-25
verified: true
---

## Summary
Opened the magazine article on margins of safety for aircraft structure. The article says a margin is acceptable when it is zero or positive, with zero meaning the strength is adequate but has no reserve, and a negative margin meaning the part is not strong enough. The margin equation is an image on the page and was not read. The article also gives a suggested factor for yield, which is not a number for this key and is not used.

## Usable rules / numbers
- [joint_rf_min] A margin is acceptable when zero or positive; zero means strength is adequate with no reserve, a negative margin means not strong enough (article body, margin definition section, read 2026-11-25). Kind: definition; the boundary sits at zero margin.
- [joint_rf_min] The margin equation is shown only as an image; its symbols are not read.
- Not used: the author's suggested yield factor of 1.1 (article body, yield paragraph); a yield criterion, not the joint reserve factor.

## How we could use it
- Feeds `joint_rf_min` as a second definition that puts the acceptable boundary at zero margin, which corresponds to 1.0 in a ratio of strength to load.
- Agrees with the lecture notes on n = 1 as a boundary; differs from the lecture's margin wording, which is reported in that source file.
