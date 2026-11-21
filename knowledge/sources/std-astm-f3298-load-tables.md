---
id: std-astm-f3298-load-tables
title: ASTM F3298-24 Standard Specification for Design and Construction of Lightweight Unmanned Aircraft Systems (UAS) (store page); 14 CFR 23.473 Ground load conditions and assumptions (2016 edition, for comparison)
authors: ASTM International; US Federal Aviation Administration
year: 2024
url: https://store.astm.org/f3298-24.html
type: standard
retrieved: 2026-11-20
verified: false
---

## Summary
Opened: https://store.astm.org/f3298-24.html (F3298-24 store page; abstract and scope only, no body text or tables), https://www.govinfo.gov/content/pkg/CFR-2016-title14-vol1/xml/CFR-2016-title14-vol1-sec23-473.xml (14 CFR 23.473, 2016 edition). blocked: astm.org (https://www.astm.org/f3298-19.html returned HTTP 403). blocked: ecfr.gov (https://www.ecfr.gov/current/title-14/part-23 redirected to an unblock page). The third-party F3298-19 sample cited in `std-astm-f3298-lightweight-uas` (cdn.standards.iteh.ai) now returns HTTP 404, and no freely readable F3298-24 copy or preview was found by search. The F3298 landing and ground load tables were therefore not read; only the pre-2017 Part 23 landing rule was read, as a comparison point for crewed light aircraft.

## Usable rules / numbers
- [landing_load_factor] ASTM F3298-24 landing load factor: not found (store page gives only title, status "Active", scope; no load values) (store.astm.org/f3298-24.html, abstract and section 1.1).
- [landing_load_factor] ASTM F3298-24 ground load magnitudes / load tables: not found (body text not available in any opened source).
- [landing_load_factor] ASTM F3298-19 load tables: not found (sample copy URL now 404; astm.org page 403).
- [landing_load_factor] Part 23 comparison, not a UAS rule: limit inertia load factor for landing design "may not be less than 2.67"; limit ground reaction load factor not less than 2.0 at design maximum weight (14 CFR 23.473(g), 2016 edition).
- [landing_load_factor] Part 23 comparison: landing descent velocity V = 4.4 (W/S)^(1/4) ft/s, not more than 10 ft/s and not less than 7 ft/s (14 CFR 23.473(d), 2016 edition).
- [landing_load_factor] Part 23 comparison: wing lift up to two-thirds of airplane weight may be assumed during landing impact (14 CFR 23.473(e), 2016 edition).
- Sections 23.474 to 23.485 (2016 edition): not read.

## How we could use it
- Feeds `landing_load_factor`: no F3298 value was found, so the key stays pending; the only opened numeric anchor is the crewed Part 23 floor of 2.67 (inertia) / 2.0 (ground reaction), which is a comparison, not a UAS requirement.
- A paid or library copy of ASTM F3298-24 is still needed to check its landing and ground load tables.
