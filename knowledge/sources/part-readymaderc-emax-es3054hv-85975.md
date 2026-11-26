---
id: part-readymaderc-emax-es3054hv-85975
title: EMAX ES3054 HV High Voltage 17g Metal Gear Digital Servo (RMRC product 85975)
authors: ReadyMadeRC (retailer)
year: unknown
url: https://www.readymaderc.com/products/details/85975-emax-es3054-hv-high-voltage-17g-metal-gear-digital-servo
type: website
retrieved: 2026-11-26
verified: true   # page opened 2026-11-26; spec section read
---

## Summary
Retailer product page for the ES3054HV that is the URL on the part.yaml. Page title says 17g, while the spec table says 20.5 g, so the listed figures conflict. The spec table gives metal gears, 23T output spline, 240 mm lead and 90/180 degree travel. No numeric case dimensions on the page: they are only "See Drawing Below", and the drawing is not in the fetched text.

## Usable rules / numbers
- Weight: "20.5±0.5 g" (Mechanical Specification). Title says 17g: conflict.
- Overall dimensions: "See Drawing Below", no numeric L x W x H given (Mechanical Specification).
- Output gear spline: "23T" (Mechanical Specification).
- Gear type: "Metal" (Mechanical Specification).
- Connector wire: "JR" gauge type; wire length "240±8mm (W/O Connector)" (Mechanical Specification). Exit side not stated.
- Extreme angle: "360°" (Mechanical Specification).
- Operating travel: "90° ±8°" at 1000–2000 µs; maximum travel "180° ±10°" at 500–2500 µs (Control Specification).
- Stall torque: "3.4kg.cm Max" at 6.0 V; "4.7kg.cm Max" at 8.4 V (Electrical Specification).
- Speed (no load): "0.13 sec/60°" at 6.0 V; "0.09 sec/60°" at 8.4 V (Electrical Specification).
- Mounting ears and output horn: not mentioned.
- Page text refers to an "EMAX ES09MD HV" servo: model naming on the page is inconsistent.

## How we could use it
- Source for mass, spline count and travel in the ES3054HV part.yaml; not a source for frames or ports (no ear or spline position data).
- Mass conflict (17 g title vs 20.5 g spec) to be resolved by a measured weight before any standards use.
