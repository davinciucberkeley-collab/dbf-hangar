---
id: std-u171-p6-stanag-annex-b-drop
title: STANAG 4703 / AEP-83 Edition A Version 1 Annex B, Landing conditions for conventional landing gear configurations (re-read of PDF pages 67 to 68 for drop height)
authors: NATO Standardization Office
year: 2014
url: https://assets.publishing.service.gov.uk/media/5a7ec5c940f0b62305b83155/20140916-STANAG-4703_AEP-83_A__1_.pdf
type: standard
retrieved: 2026-11-25
verified: true
---

## Summary
Downloaded the same ratification draft PDF as the existing source file std-stanag-4703-annex-b-landing and extracted text from PDF pages 67 and 68 (Annex B sheets B-1 and I-2) this run. Annex B gives the drop height formula and states a floor of 9 inches, and it gives the wheel load factor and reserve energy height used with it. It states no rest-speed or simulated duration. The annex says it reflects manned-aircraft practice and that alternative designs may need tailoring.

## Usable rules / numbers
- [drop_height_m] Drop height h [in] = 3.6 x (W/S)^(1/2), W/S in lb/ft2, "but h larger than 9 in." (Annex B 1.1, PDF p.68, sheet I-2). Conversion with 25.4 mm per inch: 9 in = 0.2286 m.
- [drop_height_m] Reserve energy height h_r = 1.44 h (Annex B 1.3, PDF p.68). Not used for the key.
- [rest_speed_max_mps] none (Annex B 1.1 to 1.3, PDF p.68; UL.GL.1 table and figure, PDF p.67 give loads only).
- [duration_s] none (Annex B 1.1 to 1.3, PDF pp.67 to 68).

## How we could use it
- Feeds `drop_height_m` as a second bound (h above 9 in, 0.2286 m) on the same formula as 14 CFR 23.725(a); a manned-aircraft annex, so a comparison only.
- No support for `rest_speed_max_mps` or `duration_s`.
