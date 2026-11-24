---
id: "docs-research-budget-avionics"
title: "Budget avionics set: ArduPilot QuadPlane (cut from the ~$700 Pixhawk set)"
kind: "research"
morph_cells: ["vtol_method:lift-plus-cruise"]
source_repo: DBF-Combined @ a93f14d
source_files: ["docs/research/budget-avionics.md"]
created: 2026-11-23
verified: false
---

## Summary
A cheaper avionics selection for a lift-plus-cruise quadplane with 4 or 8 lift motors, one pusher and 4 servos, running ArduPilot Plane with QuadPlane enabled. Prices and stock were read live on 2026-10-13, with live pages overriding search snippets. It covers flight controller firmware limits, GPS, an optional airspeed sensor, Remote ID and current sensing.

## Key facts
- Output count needed is 9 for the 4-lift layout and 13 for the 8-lift layout (lift motors plus pusher plus 4 servos). Flying 8-lift without Y-leads needs a board with at least 13 outputs; the sole in-stock option was a 14-output H7 wing board at $105.00. [budget-avionics.md section 0 and 1.3]
- Boards with 1 MB flash include QuadPlane but drop coaxial octa-quad frames, Lua scripting, digital airspeed and OpenDroneID; separate-boom octa is kept. [budget-avionics.md section 0 caveat 1]
- A 4-lift pick is a 12-output F405 wing board at $67.26 with a 90 A current sensor and 8 A servo supply, but its firmware target exists only in the beta and latest Plane builds, not in stable 4.7.1. [budget-avionics.md section 0 caveat 2, 1.3]
- Estimated hover current at 12 kg is 53 to 91 A on 6S and 26 to 46 A on 12S. The onboard sensors accept only 2 to 6S or 3 to 8S, so a 12S lift pack needs a separate flight-controller supply and an external current sensor. [budget-avionics.md section 1.3]
- ArduPilot supports flying a QuadPlane without an airspeed sensor using a synthetic estimate; the assist-speed rule is 3 m/s below minimum airspeed, or 5 m/s below without a sensor. A downwind transition without a sensor can stall. [budget-avionics.md section 3]
- Remote ID: the two cheapest modules found on the FAA declaration list cost $36.99 and $39.99; ArduRemoteID-type boards were not listed as broadcast modules. GPS pick is a $20.49 M10 module. [budget-avionics.md sections 0 and 2]
- Sources cited by DBF-Combined, not opened by this import: ArduPilot firmware server feature lists, ArduPilot board and parameter docs (limited firmware, airspeed, QuadPlane transitions), vendor pages at ReadyMadeRC, RaceDayQuads, WREKD, ProgressiveRC, Holybro and Matek. [budget-avionics.md sections 1-3]

## Status in the study
none

## Open questions
- Holybro ships from China with the buyer paying duty; the duty amount is not stated.
- Hover current figures are estimates from the propulsion study, not measured.
- Whether the beta-only firmware target is acceptable for the 4-lift pick is not decided in the file.
