---
id: std-stanag-4703-annex-b-landing
title: STANAG 4703 / AEP-83 Edition A Version 1, Annex B "Landing conditions for conventional landing gear configurations (where applicable)"
authors: NATO Standardization Office
year: 2014
url: https://assets.publishing.service.gov.uk/media/5a7ec5c940f0b62305b83155/20140916-STANAG-4703_AEP-83_A__1_.pdf
type: standard
retrieved: 2026-11-20
verified: true
---

## Summary
Whole document read this time (113 PDF pages, ratification draft 1), including UL.6 ground loads and Annex B (PDF pages 67 to 68, sheets B-1 and I-2 to I-5). STANAG 4703 gives no fixed numeric landing load factor. UL.6.2 requires the worst combination of reasonably possible landing impact loads at maximum design weight and points to Annex B "as a reference" for conventional landing gear only; Annex B is adapted from manned-aircraft practice and says alternative designs may need case-by-case tailoring. Annex B computes the wheel load factor from drop height and shock absorber travel, then the limit landing factor as that value plus the 2/3 wing-lift term. Opened: the URL above only.

## Usable rules / numbers
- [landing_load_factor] No fixed landing load factor value in the whole document; landing loads are a calculated case (UL.6.2, PDF p.21; Annex B UL.GL.1, PDF p.67).
- [landing_load_factor] Wheel load factor nj = (h + d/3) / (ef x d); drop height h [in] = 3.6 x sqrt(W/S), W/S in lb/ft2, with h not less than 9 in; d = total shock travel [in] = d_tire + d_shock (Annex B 1.1, PDF p.68, sheet I-2).
- [landing_load_factor] Shock efficiency: ef x d = 0.5 x d for tire and rubber or spring shocks; = 0.5 x d_tire + 0.65 x d_shock for hydraulic shocks (Annex B 1.1, PDF p.68).
- [landing_load_factor] Limit landing load factor n = nj + 2/3, with assumed wing lift L = 2/3 of weight; fore-aft factor K = 0.25 in level landing; inclined reactions at 14 deg (Annex B table "Basic landing condition" notes and figure, PDF pp.67 to 68).
- [landing_load_factor] If nj > nmax - 0.67 (nmax from UL5.2, 3.8), concentrated masses must be substantiated for n = nj + 0.67 (Annex B 1.2, PDF p.68).
- [landing_load_factor] Ultimate factor 1.5 applies to the landing condition unless a drop test from reserve energy height hr = 1.44 h shows a lower factor; for fast energy-absorbing shocks, ultimate = limit x 1.2 reserve energy factor (Annex B 1.3, PDF p.68).

## How we could use it
- Feeds `landing_load_factor`: STANAG 4703 does not support a fixed 3.0 or 3.8; it supports computing n = nj + 2/3 from wing loading and gear travel (Annex B 1.1), with 3.8 (UL5.2) relevant only as the threshold in Annex B 1.2.
- Feeds the structure tier landing load case: a calculated value from the design's W/S and gear travel, ultimate factor 1.5.
