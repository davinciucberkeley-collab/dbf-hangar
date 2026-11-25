---
id: dbf-combined-davinci-research
title: DBF-Combined: DaVinci research (capabilities, connector, pricing) docs/integration/davinci-research.md
authors: DBF-Combined project (author not stated)
year: 2026
url: origin/redesign/v1:docs/integration/davinci-research.md
type: website
retrieved: 2026-11-24
verified: true
---

## Summary
Research notes read 2026-11-23 from DaVinci's public docs and the Celedon pricing page. Covers agent toolboxes, physics types, Python code objects, the absence of an MCP server and plan prices. The DaVinci docs were not re-opened for this entry.

## Usable rules / numbers
- Physics certified: steady thermal, linear statics, thermo-elastic. Gate-validated: modal, harmonic, random vibration, shock, transient thermal and structural, laminar flow, optics. System: multibody, networks, controls, contact dynamics (section 3).
- Aerodynamics: none beyond laminar CFD; flight dynamics: none documented (section 3).
- Tools named: Core, Parts and Components, Geometries (MeasureModel), Simulation (SetupSimulation, RunSimulation and others), Requirements, Constraints and Verification, Attributes and Analysis. The API has no list-tools route (section 3).
- No DaVinci MCP server found; DaVinci connects outward to MCP servers only (section 4).
- Plans: Individual Free $0 (100 MB, 2 projects); Core $20 per month (1 GB, 5 projects); Max $200 per month (10 GB); Group $40 per user per month (10 GB); Enterprise custom (section 5).
- Python code objects run in the browser via Pyodide per the research note; REST execution of a created Code object not tested (section 3).

## How we could use it
Source for the analysis-tool list and plan prices in davinci-api-facts. Those DaVinci pages were not re-opened by W32-S; treat as secondary.
