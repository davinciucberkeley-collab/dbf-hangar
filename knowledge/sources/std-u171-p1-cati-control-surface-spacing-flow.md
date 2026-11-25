---
id: std-u171-p1-cati-control-surface-spacing-flow
title: Model Aircraft Control Surface Spacing and SOLIDWORKS Flow Simulation
authors: CATI (website article; author not shown in the page text read)
year: unknown
url: https://www.cati.com/?p=118659
type: website
retrieved: 2026-11-25
verified: true   # opened and read the test configuration and results text in this run
---

## Summary
Short engineering article that runs a flow simulation of a model wing with a control surface and compares hinge and gap configurations. It states the gap tested in its largest case and the hinge dimensions used. It gives no recommended maximum gap or tolerance; the conclusions call one gap "way too large" without a figure.

## Usable rules / numbers
- Model: 5.5 in main wing chord, 0.5 in of chord is control surface (wing and surface sizes; not a gap). Place: body text after the title.
- Largest tested gap: 0.25 in (= 6.35 mm, exact conversion 1 in = 25.4 mm) with CA hinge, upward deflected surface. Place: "Test configurations", Run Four.
- Run Three: 0.0625 in barrel hinge (hinge size, not a gap). Place: "Test configurations" and "Results", Run Three.
- Hinge spacing: "typically spaced evenly across the control surface" (no number). Place: hinge types text.
- No recommended or bound gap value is stated. Place: Conclusions.

## How we could use it
- strip_gap_tolerance_mm (packet 1): gap size input 6.35 mm from a flow test case (kind: derivation input; not a bound).
