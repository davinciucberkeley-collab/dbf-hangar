---
id: std-vtol-thrust-to-weight-paper
title: Design methodology for hybrid (VTOL + Fixed Wing) unmanned aerial vehicles
authors: Ashraf M Kamal, Alex Ramirez-Serrano (University of Calgary)
year: 2018
url: http://medcraveonline.com/AAOAJ/AAOAJ-02-00047.pdf
type: paper
retrieved: 2026-11-20
verified: true
---

## Summary
This is the paper linked in the ArduPilot thread (first post, Ben_Stanton) that the poster "Feibernaut" calls "the same paper". It is a preliminary sizing method for tiltrotor transitional aircraft, published in Aeronautics and Aerospace Open Access Journal 2(3):165-176, 2018, DOI 10.15406/aaoaj.2018.02.00047. In its literature review it mentions a hover thrust-to-weight range of 1.2 to 1.5, credited to Raymer's textbook (its ref. 16). The paper does not state a 1.05 minimum: "1.05" does not appear anywhere in its text. The forum's "floor 1.05" claim therefore traces back to Raymer, which was not opened in this run. Sources opened: https://discuss.ardupilot.org/t/recommended-thrust-to-weight-ratio-for-a-hybrid-vtol-uav/80510 and http://medcraveonline.com/AAOAJ/AAOAJ-02-00047.pdf.

## Usable rules / numbers
- [hover_thrust_to_weight_min] Hover thrust-to-weight 1.2 to 1.5 for VTOL. The paper reports this as a suggestion from "some references" (ref. 16: Raymer D., Aircraft Design: A Conceptual Approach, 5th ed., AIAA, 2012), which it says has been used for tail-sitter UAVs (ref. 19). This is a literature citation, not the paper's own result (Introduction, p. 166).
- [hover_thrust_to_weight_min] Minimum 1.05: not found in this paper. The forum attributes it to "the source given in the paper", which would be Raymer (ref. 16), and Raymer was not opened.
- [hover_thrust_to_weight_min] The paper also mentions a different method: historical power/thrust loading databases for manned VTOL aircraft (ref. 17: Keith JD, Hall DW, Rapid Sizing Methodologies for VTOL UAVs, 47th AIAA ASM, 2009). It gives no number for this (Introduction, p. 166-167).

## How we could use it
- Feeds `hover_thrust_to_weight_min` (D6 options). The 1.2 to 1.5 range comes from a textbook cited secondhand, so it supports 1.5 only as the top of that range. Nothing found here supports 2.0, and nothing found here supports the 1.05 floor.
- To confirm the 1.05 floor, open Raymer, Aircraft Design: A Conceptual Approach (VTOL chapter).
