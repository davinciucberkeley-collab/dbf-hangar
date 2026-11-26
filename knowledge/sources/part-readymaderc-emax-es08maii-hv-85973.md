---
id: part-readymaderc-emax-es08maii-hv-85973
title: 85973 EMAX ES08MA II HV high voltage 12g metal gear servo (ReadyMadeRC listing)
authors: ReadyMadeRC (retailer product listing)
year: unknown
url: https://www.readymaderc.com/products/details/85973-emax-es08ma-ii-hv-high-voltage-12g-metal-gear-servo
type: website
retrieved: 2026-11-26
verified: true   # opened 2026-11-26 via WebFetch; spec fields read from the page
---

## Summary
Retailer listing for the HV variant of the EMAX ES08MA II 9g-class (12 g) metal-gear analog servo. It gives a stall torque per voltage and a spline tooth count. It gives no arm pull-off or arm-screw retention value.

## Usable rules / numbers
- Stall torque at 6.0 V: 1.4 kg·cm, listed as "Max" (product page, specification block).
- Stall torque at 8.4 V: 2.0 kg·cm, listed as "Max" (same block).
- Output gear spline: 15T (same block). Conflicts with the 23T that concept-a's comment on E-MEC-02 attributes to "readymaderc 85975"; that product ID returned "Product Not found" (see the 85975 check in the report).
- Gear type: metal. Weight: 12 ± 1 g (same block).
- Arm or horn retaining screw spec: not found.
- Arm pull-off or retention load: not found.

## How we could use it
- CT-SERVO-SPLINE: supplies the torque input only (servo property, not a joint rating); the spline count needs confirmation from a second source before any arm-retention check.
- Fit check against the concept-a note that cites 23T for the same servo family.
