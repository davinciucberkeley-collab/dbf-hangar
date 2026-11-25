---
id: std-u171-p9-pololu-1054-servo
title: High-Torque Servo with Metal Gears (Generic), Pololu product 1054 specs
authors: Pololu Corporation
year: unknown
url: https://pololu.com/product/1054/specs
type: website
retrieved: 2026-11-25
verified: true
---

## Summary
Manufacturer specification page for a generic high-torque hobby servo with an all-metal gear train. The page gives stall torque at two supply voltages. It gives no spline type, horn screw size or arm length, so it does not rate a servo arm retention.

## Usable rules / numbers
- Stall torque 140 oz·in at 6 V = 0.98862 N·m (1 oz·in = 0.0625 lbf × 0.0254 m × 4.44822 N/lbf = 0.00706155 N·m). Bound type not stated. Place: specs table, 6 V stall torque row.
- Stall torque 124 oz·in at 4.8 V = 0.87563 N·m (same factor). Bound type not stated. Place: specs table, 4.8 V stall torque row.
- The same page prints "140 oz-in (10.2 kg-cm)"; 140 oz·in is 10.08 kgf·cm at the exact factor (1 kgf·cm = 0.0980665 N·m), so the printed kg-cm figure differs by about 1 %. Place: specs description, 6 V torque line.
- Gear train described as all metal (paraphrase). Place: product description.
- Spline type and tooth count, horn screw size and arm length: not stated on this page.

## How we could use it
- Servo torque input only; it does not set the CT-SERVO-SPLINE retention value.
- Any arm-retention rating for CT-SERVO-SPLINE needs a source that states the spline, the M2 retaining screw and the arm length.
