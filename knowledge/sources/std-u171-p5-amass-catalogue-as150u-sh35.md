---
id: std-u171-p5-amass-catalogue-as150u-sh35
title: Changzhou Amass connector catalogue, AS150U and SH3.5 / SH4.0U specification tables (distributor-hosted PDF)
authors: Changzhou Amass Electronics Co. Ltd. (distributor copy hosted at rcscomponents.kiev.ua)
year: unknown
url: https://www.rcscomponents.kiev.ua/datasheets/Amas-cat1.pdf
type: website
retrieved: 2026-11-25
verified: true
---

## Summary
The Amass catalogue PDF gives a per-model "Specifications" table with a current rating printed as "MAX" with a wire gauge and a temperature condition. I opened the PDF in this run and read the text layer for PDF pages 20 (SH3.5 and SH4.0U) and 28 (AS150U). The catalogue does not label any of these ratings as continuous or peak. The copy is distributor-hosted, not the Amass site.

## Usable rules / numbers
- [AS150U] Rated current 75 A, printed "75A MAX(8AWG/<85)", rated voltage 500 V DC, operating temperature -20 to 120 (printed range). The "<85" has no unit in the text layer. Place: PDF p. 28 (printed page 28), "Specifications" table, AS150U column. Label is MAX; not labelled continuous or peak.
- [SH3.5 bullet, 3.5 mm] Rated current 30 A, printed "30A MAX(14AWG/<85)", rated voltage 500 V DC, IP40. Place: PDF p. 20 (printed page 20), "Specifications" table, SH3.5 column. Label is MAX.
- [SH4.0U bullet, 4.0 mm] Rated current 45 A, printed "45A MAX(12AWG/<85)", 500 V DC. Place: PDF p. 20 (printed page 20), SH4.0U column. Label is MAX.
- Not found in this catalogue: a 2 mm bullet rating, any solder-joint rating, any JR/Futaba servo connector rating.

## How we could use it
- `standards/connection-types.yaml` key CT-AS150U: the 75 A MAX printed value (8 AWG, rise <85) is the maker figure opened here; the continuous label in the library is not printed in this catalogue.
- `CT-BULLET-3` (motor phases, size per E1): the 3.5 mm (SH3.5, 30 A MAX, 14 AWG) and 4.0 mm (SH4.0U, 45 A MAX, 12 AWG) rows; the size is for the builder to pick from E1.
