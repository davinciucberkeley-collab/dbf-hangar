---
id: schema-openvsp-api-geom
title: OpenVSP API documentation, Geom group
authors: NASA OpenVSP team
year: unknown
url: https://openvsp.org/api_docs/latest/group___geom.html
type: website
retrieved: 2026-11-24
verified: true   # true for the part read (first 100 000 of 162 800 characters)
---

## Summary
NASA's parametric aircraft geometry tool. Only the first 100 000 of 162 800 characters of the Geom group page were read; the openvsp.org wiki pages tried (aircraftmodeling, start) had no geometry content. Treat the list as partial.

## Usable rules / numbers
- Geometry types named: WING, FUSELAGE, POD, PROP, STACK, MDC_BOD, MDC_FIN, CLONE, mesh and point cloud (Geom group page, visible part).
- Wing sections are driven by three of aspect ratio, root chord, tip chord (SetDriverGroup).
- Fuselage is cross-sections (ellipse: width and height drivers; circle: one driver); pods are placed by XForm (X_Rel_Location) relative to a parent (same page).
- PROP can switch to an actuator disk driven by RPM, CT, CP (PropMode).

## How we could use it
- Supports the primitive set wing / fuselage loft / pod (nacelle) / propeller / clone (mirror) as the common vocabulary of aircraft geometry tools.
