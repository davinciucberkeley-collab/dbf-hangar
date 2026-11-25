---
id: std-u171-p6-14cfr-23-725-drop
title: 14 CFR 23.725 Limit drop tests (Part 23 airworthiness standards, 2016 edition), read with 14 CFR 23.726 from pilotfriend.com
authors: US Federal Aviation Administration (regulation text); pilotfriend.com (reprint of the amendment history for 23.725 and 23.726)
year: 2016
url: https://www.govinfo.gov/content/pkg/CFR-2016-title14-vol1/xml/CFR-2016-title14-vol1-sec23-725.xml
type: regulation
retrieved: 2026-11-25
verified: true
---

## Summary
Opened the 2016 Part 23 section 23.725 XML on govinfo and read paragraphs (a) and (b) through the fetch tool, which returned a summary rather than verbatim text. Paragraph (a) gives a free drop height from a formula in weight over wing area, bounded between 9.2 and 18.7 inches. Paragraph (b) gives the wing-lift variant with an effective weight, whose formula is an image and was not read. The section is written for Part 23 airplanes, not small UAS, and gives no rest-speed or duration criterion.

## Usable rules / numbers
- [drop_height_m] Free drop height h [in] = 3.6 x (W/S)^(1/2), with W/S in lb/ft2; h "may not be less than" 9.2 in and "need not be more than" 18.7 in (14 CFR 23.725(a), govinfo CFR-2016 sec23-725 XML, read 2026-11-25). Conversions with 25.4 mm per inch: 9.2 in = 0.23368 m; 18.7 in = 0.47498 m.
- [drop_height_m] Paragraph (a) applies when free drop tests show compliance with 23.723(a) on the complete airplane or on a wheel, tire and shock-absorber unit (same XML section, paragraph (a) lead-in; also pilotfriend.com/FARS/7/Sec. 23.725, read 2026-11-25).
- [drop_height_m] Not used for the key: paragraph (b) wing-lift effective weight, with wing lift ratio L "not more than 0.667" (same XML section, paragraph (b)).
- [drop_height_m] Not used for the key: 23.726(a) requires one drop test at 2.25 times the 23.725(a) height or a height that gives 1.5 times the limit load factor (pilotfriend.com/FARS/7/Sec. 23.726, read 2026-11-25; amendment 23-7 shown on the page).
- [rest_speed_max_mps] none: no settled-velocity criterion in 23.725(a) or (b).
- [duration_s] none: no simulated time stated in 23.725 or 23.726.

## How we could use it
- Feeds `drop_height_m` as a Part 23 minimum-height bound (9.2 to 18.7 in) for a gear drop; it is a crewed-airplane rule, not a UAS rule, so the bound is a comparison only.
- Gives no value for `rest_speed_max_mps` or `duration_s`.
