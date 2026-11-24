---
id: "docs-research-avionics-autopilot"
title: "Avionics, autopilot software, test gear, compliance costs"
kind: "research"
morph_cells: ["vtol_method:lift-plus-cruise"]
source_repo: DBF-Combined @ a93f14d
source_files: ["docs/research/avionics-autopilot.md"]
created: 2026-11-23
verified: false
---

## Summary
Parts research for a lift-plus-cruise quadplane (4 or 8 lift rotors stopped in cruise, one pusher, 8 to 15 kg, $2,000 budget). It compares ArduPilot Plane and PX4 VTOL parameters, flight controllers by output count, sensors, links, Remote ID modules, test gear and compliance fees. Items were checked live on 2026-10-13; search-engine snippets were not used for prices.

## Key facts
- Latest stable releases at the check date were ArduPilot Plane 4.7.1 and PX4 v1.17.0. ArduPilot documents octa and octa-quad frame classes and a lift-motor thrust-loss handler, so it is the better documented path for an 8-rotor build. [avionics-autopilot.md 1.1-1.3]
- In ArduPilot the forward transition completes when airspeed reaches the minimum airspeed parameter, then the lift motors taper over 5000 ms by default. PX4 defaults include transition airspeed 10 m/s, front-transition duration 5 s, transition timeout 15 s (which triggers a quad-chute) and back-transition deceleration 2 m/s2. [avionics-autopilot.md 1.2, 1.3]
- Output need is 13 to 14 PWM outputs for 8 lift motors, a pusher and 4 to 5 servos, or 10 for a quad. A Pixhawk 6C has 16 outputs ($199 bare) and is the pick; a 6C Mini and a Cube Orange+ have exactly 14. [avionics-autopilot.md section 2]
- A 200 A CAN power module ($83) is needed only if whole-pack hover current exceeds about 70 A; the cheaper 70 A module ($20.99) comes with a lead rated 30 A. [avionics-autopilot.md 3.3]
- Recommended avionics subtotal is $602.95 without the 200 A module and telemetry radio and $744.94 with them, before tax and shipping. [avionics-autopilot.md section 6]
- A DIY thrust stand (two 10 kg load cells and two amplifiers) costs $35.80 against $1,075 for a commercial 5 kgf stand. [avionics-autopilot.md 4.1]
- Compliance costs listed: FAA registration $5 for 3 years, TRUST test free, Part 107 knowledge test $175, AMA full membership $89 per year with $2.5 million liability, Berkeley sales tax 10.25 percent. [avionics-autopilot.md section 5]
- Sources cited by DBF-Combined, not opened by this import: ArduPilot Plane parameter and QuadPlane docs, PX4 parameter reference and VTOL configuration docs, Holybro product pages, RadioMaster, ExpressLRS MAVLink page, Dronetag, FAA registration and UAS declaration-of-compliance pages, Tyto Robotics, SparkFun, AMA membership pages, CDTFA rate table. [avionics-autopilot.md throughout]

## Status in the study
none

## Open questions
- Look up the Remote ID module serial number in the FAA declaration-of-compliance system before purchase; the source could not read that site.
- Confirm peak whole-pack hover current; above 70 A continuous rules out the cheap power module.
- Confirm the final output count; above 14 only the 6C works, above 16 needs an extra I/O board.
- Calibrate the thrust stand; error above about 2 percent of full scale (an estimate) makes motor data unusable for rotor sizing.
- Decide recreational versus Part 107 operation, which decides whether the $175 test is needed.
