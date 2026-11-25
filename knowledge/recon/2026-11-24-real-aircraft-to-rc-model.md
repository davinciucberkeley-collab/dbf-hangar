# Recon: turning any real aircraft into a scale-look RC design in PDL (U12.4, D77, D78)

Question: which fields must a reference-aircraft fact sheet carry, which RC-scale adjustments apply, and which generators cover the most configurations. Sources opened this run are in `knowledge/sources/` (ids below). Not opened, so not cited: Model Aviation J-3 Cub scaling example (search snippet only), OpenVSP wiki pages (no geometry content), Moiz et al. 2018 (PDF unreadable here).

## 1. Approaches

| Approach | Evidence (opened) | Effect | Needs from PDL / `plane` | Risk |
|---|---|---|---|---|
| A. Document-then-scale: photos, then a checked three-view, one scale factor s | scale-modelaviation-scale-three-views | Geometry from span/length/height ratios; confidence recorded per field | fact-sheet fields with source and confidence; generators take mm after multiplying by s | published drawings disagree; need 2 sources for span, length |
| B. Power-law scaling: lengths s, area s^2, mass and power s^3, wing loading s, speed sqrt(s); choose s from power available | scale-stefanv-scale-electric-design | Target mass, wing area, stall/cruise speed, power from full-size values | `requirements.mtow_g`, `flight.cruise_speed_mps`, `plane design mass` | scale mass is only a floor test, real parts weigh more; low Reynolds number at small s |
| C. Stability-based correction: keep or restore Vh 0.30-0.60, Vv 0.02-0.05, static margin 0.05-0.15 c, dihedral from spiral/roll criteria; enlarge tail only if needed | std-mit-unified-desrules; scale-rcu-tail-feathers-scale-size (opinion: kits enlarge 10-33%) | Tail area and CG set by number | tail areas and arms from the generators; a stability check | forum evidence is opinion; enlargement is a visible deviation |
| D. Parametric-tool schema: wing = sections (LE, chord, twist, airfoil) plus mirror flag; fuselage = stations (width, height, shape exponent); pods/propulsors placed relative to a parent | schema-aerosandbox-geometry; schema-openvsp-api-geom (verified for the part read) | Field vocabulary and primitive set | mirrors our `wing_panel` and `fuselage_loft`; adds nacelle, propeller | OpenVSP page only partly read |
| E. Dynamic scaling (match inertia, Froude number) | named in a search snippet only, not opened | not usable | none | no citable source; skipped |

Gaps: no opened source gives a tested tail enlargement factor, a wing-loading target for RC scale airliners, or a scale-RC dihedral rule. These stay estimates in the template.

## 2. Ranked recommendation

1. A + B as the pipeline: fact sheet in full-size units, then one scale factor s chosen from the transport box and available power; mass floor = full-size MTOW x s^3, cruise speed = full-size x sqrt(s). Cheapest test: fill the template for the Cessna 172, generate, run `plane design mass`, compare with s^3 x MTOW.
2. C as the correction layer: compute Vh and Vv from the generated tail; if outside the MIT range raise tail area (span first), record the enlargement; place CG at static margin 0.05-0.15 c. Cheapest test: `plane design sweep` of tail area against Vh.
3. D to fix the primitive set and keep the fields general (no per-aircraft code).

## 3. Field list
See `knowledge/TEMPLATE-reference-aircraft.md`. Every geometric field maps to a generator parameter.

## 4. Generators vs configurations

Existing (core/hangar/geom): `wing_panel` (airfoil loft, sweep, dihedral, twist, taper, elevon), `fin` (trapezoid plate), `plate`, `fuselage_loft` (stations [x, width, height], ellipse or rect), `tube`, `mesh_file`, `motor_mount`.

| Config | Covered today | Missing |
|---|---|---|
| High-wing single prop (C172) | wing_panel, fuselage_loft, fin | strut, landing_gear, propeller+spinner, cowl |
| High-wing four-turboprop transport (A400M) | wing_panel, fuselage_loft | nacelle x4, propeller (multi-blade), T-tail mount, gear sponson/fairing, upswept tail cone |
| Low-wing single/twin, biplane, flying wing, V-tail | wing_panel, fin (mirrored) | nacelle, gear, interplane strut |

Missing primitives ranked by reuse across configurations: (1) `nacelle` (revolved body; also cowls, pods, tip tanks, external stores); (2) `landing_gear` (strut + wheel; fixed, tricycle, taildragger); (3) `propeller` (n-blade disc, spinner); (4) `strut` (round or faired line between two points); (5) `fuselage_loft` extensions: squareness exponent (AeroSandbox `shape`), centre-line z offset per station (upswept cone). Tail layouts (conventional, T, V, H, cruciform) need no new generator if `fin` and `wing_panel` take a mount point and dihedral; high/mid/low wing is a placement z and the dihedral sign.

## 5. Open points
- `wing_panel` needs an airfoil .dat; the fact sheet carries only the designation, with a generic section substituted when the real one is not public.
- The s^3 mass is a floor test, not a target: for a large airliner the chosen s will come from real-parts mass and the transport box, not from scale law. State the ratio in the sheet.
