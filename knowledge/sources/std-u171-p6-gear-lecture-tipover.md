---
id: std-u171-p6-gear-lecture-tipover
title: Landing gear design (lecture slides, slides "Tip-over criteria -- 1" and "Tip-over criteria -- 2")
authors: not found (slides cite Schaufele and Raymer; no author or course named on the pages read)
year: not found
url: https://webpage-a360a5.gitlab.io/pdf/7-LandingGear.pdf
type: website
retrieved: 2026-11-25
verified: true
---

## Summary
Opened the lecture PDF (pages 2 and 3 read as text) on landing gear layout. The slides give a typical maximum tip-back angle of about 15 degrees for tricycle gear and a lateral tip-over or overturn angle of no more than about 55 degrees with the CG at its most forward position. The degree sign is lost in text extraction, so the unit is taken from the slide wording "tip-back angle" and matches the second source for the 15 value. The slides also give nose-gear load shares and a wheel-contact distance, which are not angles and are not used.

## Usable rules / numbers
- [tip_angle_max_deg] Tricycle gear: "maximum tip-back angle" is typically approx. 15 degrees; the main gear contact point must lie aft of the rearmost CG when the aircraft is tipped back for landing (slide "Tip-over criteria -- 1", item 5, PDF p.2). Kind: maximum.
- [tip_angle_max_deg] Not compared (different axis): lateral tip-over or overturn angle "no more than approx. 55" with CG at its foremost location (slide "Tip-over criteria -- 1", item 7, PDF p.2).
- [tip_angle_max_deg] Tailwheel gear: the same tip-back and lateral considerations apply, with the tail wheel replacing the nose wheel (slide "Tip-over criteria -- 2", items 10 and 12, PDF p.3). No new number.
- Not used: nose-gear static share 8 to 25 percent (slide "Tip-over criteria -- 1", item 9, PDF p.2); main wheel contact about 15 forward of the foremost CG (item 11, PDF p.3), a distance, not an angle.
- [rest_speed_max_mps] none. [duration_s] none.

## How we could use it
- Feeds `tip_angle_max_deg` as a maximum tip-back of about 15 degrees for tricycle gear, with the lateral 55 degrees a different axis.
- No support for `rest_speed_max_mps` or `duration_s`; `joint_rf_min` is not covered here.
