# Reference aircraft fact sheet: <aircraft name and variant>

Rules: full-size values; lengths in metres, areas m2, masses kg, speeds m/s, angles degrees. The model scale factor is applied in section 7. Every row needs a value, a source (id or URL you opened) and a confidence (measured, drawing, photo, estimate). Write `unknown` rather than guess. Get two sources for span, length and wing area, and check drawings against photos (scale-modelaviation-scale-three-views). Save the filled sheet as `knowledge/reference-aircraft/<kebab-id>.md`.

Each table has columns: Field | Unit | Where to find it | Value | Source | Confidence. Only the first three are shown here; the last three are filled per aircraft. The last column of sections 1 to 5 names the PDL generator parameter the value feeds.

## 0. Identity
| Field | Unit | Where to find it |
|---|---|---|
| name, variant, year | text | maker data sheet, type certificate data sheet (TCDS) |
| configuration class | high-wing-single, high-wing-multi-turboprop, low-wing-twin, biplane, flying-wing, ... | photos |
| three-view and photo links | URL | maker, museum, Wikipedia three-view |

## 1. Wing
| Field | Unit | Where to find it | PDL parameter |
|---|---|---|---|
| span | m | data sheet | `wing_panel.span` |
| wing area | m2 | data sheet | cross-check span x mean chord |
| root chord, tip chord | m | three-view | `root_chord`, `tip_chord` |
| LE sweep (say if quarter-chord) | deg | three-view | `sweep_le_deg` |
| dihedral | deg | three-view, front photo | `dihedral_deg` |
| twist (washout) | deg | usually estimate | `twist_tip_deg` |
| airfoil root / tip designation | text | TCDS, airfoil databases | `airfoil_file` |
| wing position high/mid/low; root z relative to fuselage centre line | m | three-view side | component position z |
| root LE x from nose | m | three-view side | component position x |
| incidence at root | deg | estimate | component rotation |
| aileron/flap span and hinge fraction | m, fraction | three-view | `elevon_y`, `hinge_frac` |
| struts: count, attach points | m | photo | `strut` (planned U4.32) |

## 2. Fuselage
| Field | Unit | Where to find it | PDL parameter |
|---|---|---|---|
| overall length | m | data sheet | stations x range |
| overall height, ground to fin tip, gear down | m | data sheet | check |
| stations: x from nose, width, height, centre-line z | m | three-view, 8 to 15 stations incl. nose, cabin, tail-cone end | `fuselage_loft.stations`, `center_z` |
| section shape per station | ellipse, round-square, rect | cross-section photos | `shape` |
| nose shape, tail-cone upsweep angle | text, deg | photo | loft stations |

## 3. Tail
| Field | Unit | Where to find it | PDL parameter |
|---|---|---|---|
| layout | conventional, T, cruciform, V, H, twin boom | photo | placement of `fin`, `wing_panel` |
| horizontal tail: span, root/tip chord, sweep, dihedral, LE x, z | m, deg | three-view | `wing_panel` |
| vertical tail: height, root/tip chord, sweep, LE x | m, deg | three-view | `fin` |
| dorsal/ventral fin, strakes | text, size | photo | `fin` |
| elevator and rudder chord fraction | fraction | three-view | `hinge_frac` |

## 4. Propulsion
| Field | Unit | Where to find it | PDL parameter |
|---|---|---|---|
| engine type and count | text, int | data sheet | `morphology.propulsion_count` |
| prop plane position x, y, z per engine | m | three-view (front and top) | component position |
| thrust line down/right angle | deg | estimate | component rotation |
| nacelle or cowl: length, max width, max height | m | three-view | `nacelle` (planned U4.32) |
| prop diameter, blade count, spinner length/diameter, rotation direction | m, int, m, cw/ccw | data sheet, photo | `propeller` (planned U4.32) |
| rated power per engine | kW | data sheet | for scaling in section 7 |

## 5. Landing gear
| Field | Unit | Where to find it | PDL parameter |
|---|---|---|---|
| arrangement; fixed or retractable | tricycle, taildragger, bicycle, skids | photo | `landing_gear` (planned U4.32) |
| wheel positions x, y; z at ground | m | three-view | placement |
| wheel diameter, width | m | data sheet | wheel size |
| track, wheelbase | m | data sheet | check |
| strut type and length; sponson or fairing | text, m | photo | `landing_gear`, `nacelle` |

## 6. Mass and performance (full size)
| Field | Unit | Where to find it |
|---|---|---|
| MTOW, empty mass, max payload | kg | data sheet |
| wing loading (MTOW / wing area) | kg/m2 | computed |
| stall speed (flaps up, down), cruise speed | m/s | data sheet |
| CG range | % MAC | TCDS, flight manual |
| paint scheme, markings | text, photo links | photo (look only) |

## 7. RC-scale adjustments (fill after sections 1 to 6)
Sources: scale-stefanv-scale-electric-design (power laws), std-mit-unified-desrules (stability ranges), scale-rcu-tail-feathers-scale-size (forum opinion).
| Field | Rule | Value |
|---|---|---|
| scale factor s (model/full) | span x s must fit the transport box; check power: s = cube root of (power available / full-size power) is an upper bound | |
| model span, length, area | span x s, length x s, area x s^2 | |
| scale-law mass (floor test) | MTOW x s^3; if real-parts mass is far higher, s is too small | |
| target mass | real-parts mass; state the ratio to the s^3 mass | |
| wing loading | full-size x s; accept higher if the stall check passes | |
| stall, cruise speed | full-size x sqrt(s) | |
| power | full-size power x s^3 as a guide; thrust-to-weight not below the standards value (`standards/*.yaml`) | |
| horizontal tail volume Vh = Sh h / (S c) | 0.30 to 0.60 | |
| vertical tail volume Vv = Sv v / (S b) | 0.02 to 0.05 | |
| tail enlargement | area factor 1.0 to 1.33, only when Vh or Vv is below range (forum opinion, not tested) | |
| static margin | 0.05 to 0.15 of mean chord | |
| dihedral | keep the full-size value; add only to meet the spiral or roll criteria (MIT desrules, dihedral sizing) | |
| Reynolds number note | model below about 200 000, full size above 1 000 000: choose a thicker or higher-Cl section if the stall check fails | |

## 8. Gaps
List every field left `unknown` and what to read or measure next.
