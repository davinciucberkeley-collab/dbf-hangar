---
id: std-u171-p5-rchelicopterfun-servo-connectors
title: RC Helicopter Fun, "RC servo connectors" article (author John Salt)
authors: John Salt
year: unknown
url: https://rchelicopterfun.com/rc-servo-connectors.html
type: website
retrieved: 2026-11-25
verified: true
---

## Summary
A hobby guide to RC servo connectors that states an observed current figure for servo connectors in general. I opened the page in this run. The page does not mention JR or Futaba by name for the current figure and gives no temperature condition. The figures are the author's own observations, not a maker datasheet.

## Usable rules / numbers
- [servo connector, general] Rated for a sustained 3 A load; up to about 6 A for short periods (author's statement). Kind: maximum (as stated), but not JR or Futaba specific. Place: main article text, "sustained" paragraph.
- [servo connector, heating] The author reports heating with a small voltage drop after a couple of minutes at 5 A or more. Place: main article text, heating paragraph. No temperature stated.
- [servo connector, peak] The author ran connectors over 12 A for a few seconds without much trouble. Place: main article text. Observation, not a rating.
- [wire size] The page covers 20 to 26 AWG wire and ties no current figure to a gauge. Recommends 20 or 22 AWG for high-current use. Place: main article text.
- Not stated: a JR or Futaba model rating, a temperature condition, a publication date.

## How we could use it
- `CT-SERVO-JR` (connection-types.yaml): the 3 A sustained figure is for servo connectors in general and does not name JR or Futaba; it is recorded as context, not as the connector's rating.
