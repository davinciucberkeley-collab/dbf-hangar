---
id: schema-aerosandbox-geometry
title: AeroSandbox geometry classes (airplane.py, wing.py, fuselage.py)
authors: Peter Sharpe et al. (AeroSandbox)
year: unknown
url: https://github.com/peterdsharpe/AeroSandbox/blob/master/aerosandbox/geometry/fuselage.py
type: website
retrieved: 2026-11-24
verified: true
---

## Summary
Open Python aircraft schema used for conceptual design. An Airplane holds wings, fuselages and propulsors; wings and fuselages are lists of cross-sections. Read from the GitHub pages (airplane.py, wing.py, fuselage.py); the WingXSec and Propulsor class bodies were not on the pages read.

## Usable rules / numbers
- Airplane: name, xyz_ref (moment reference, usually CG), wings, fuselages, propulsors, s_ref, c_ref, b_ref; references default from the first wing (airplane.py constructor).
- Wing: xsecs list plus `symmetric` mirror flag (wing.py constructor). WingXSec attributes seen in use: xyz_le, chord, twist, airfoil, control_surfaces (name, symmetric, deflection, hinge_point) (wing.py, inferred from usage, not the class body).
- Fuselage: list of FuselageXSec with xyz_c, xyz_normal, radius or (width, height), and `shape` superellipse exponent (2 circle, 1 diamond, large = square) (fuselage.py).

## How we could use it
- Confirms the minimum geometry schema: a wing is root-to-tip sections (LE position, chord, twist, airfoil); a fuselage is stations with width, height and a squareness exponent; our `fuselage_loft` has stations and ellipse/rect only, so a `shape` exponent would cover cabin-to-round sections.
