---
id: std-wire-ampacity
title: Continuous current rating (ampacity) of copper wire, AWG 8-26, with silicone and other insulation classes (Multicable reference table, Standard Wire table, EngineeringToolbox AWG current ratings, Oscar Liang wire guide)
authors: Multicable; Standard Wire; EngineeringToolbox; Oscar Liang
year: unknown
url: https://www.multicable.com/resources/reference-data/current-carrying-capacity-of-copper-conductors/
type: website
retrieved: 2026-11-21
verified: true
---

## Summary
Four opened pages give AWG current ratings with different bases. Multicable and Standard Wire publish the same temperature-class table (silicone sits in the 200 C column); both state free air, 30 C ambient. EngineeringToolbox gives a PVC-insulated, 30 C ambient table with single-core and multicore columns. Oscar Liang's RC wire guide gives single values per AWG on a burst (full-throttle) basis, not continuous. Access date for all: 2026-11-21.
Blocked (HTTP 403/404, not read): hobbyking.com blog and product page (`blocked: hobbyking.com`), iewc.com wire-ampacity-chart (`blocked: iewc.com`), motionrc.com BenchCraft 14 AWG page (`blocked: motionrc.com`, 404), powerwerx.com silicone 12 AWG page (`blocked: powerwerx.com`). Cicoil "Current Rating Guide for Wire v11" PDF was fetched but its text was not decodable here (not read). No AS50881 or SAE J1292 table was opened (paywalled or not found). No silicone-specific RC datasheet with an AWG 8-26 table was found.

## Usable rules / numbers

Source 1: Multicable, "Current Carrying Capacity of Copper Conductors" (https://www.multicable.com/resources/reference-data/current-carrying-capacity-of-copper-conductors/), opened 2026-11-21. Basis as stated: single insulated conductor in free air, 30 C ambient. Column headers as given: 80 C (polyethylene, neoprene, polyurethane, semi-rigid PVC); 90 C (polypropylene, HDPE); 105 C (PVC, irradiated PVC, nylon); 125 C (Kynar, crosslinked PE, thermoplastic elastomers); 200 C (Kapton, PTFE, FEP, PFA, silicone). Values in amperes (table on page).

| AWG | 80 C | 90 C | 105 C | 125 C | 200 C (silicone) |
|---|---|---|---|---|---|
| 8 | 65 | 70 | 75 | 90 | 100 |
| 10 | 47 | 55 | 58 | 70 | 75 |
| 12 | 36 | 40 | 45 | 50 | 55 |
| 14 | 27 | 30 | 33 | 40 | 45 |
| 16 | 19 | 22 | 24 | 26 | 32 |
| 18 | 15 | 17 | 18 | 20 | 24 |
| 20 | 10 | 12 | 13 | 14 | 17 |
| 22 | 8 | 9 | 10 | 11 | 13 |
| 24 | 6 | 7 | 7 | 8 | 10 |
| 26 | 4 | 5 | 5 | 6 | 7 |

- Bundling derating (same page, bundling section): 2-5 conductors 0.8; 6-15 conductors 0.7; 16-30 conductors 0.5.
- Page wording: tables "should only be used as a guide". No chassis-wiring vs power-transmission distinction stated. No insulation-temperature rise stated beyond the column class.

Source 2: Standard Wire, "Current Carying Capacity of Copper Conductors" (heading spelled as on page) (https://standard-wire.com/?p=651), opened 2026-11-21. Stated basis: "Single Conductor in Free Air 30 C Ambient Temperature". Columns: 80 C, 90 C, 105 C, 125 C, 200 C. Extracted text does not clearly map each material group to a column; silicone is listed among the materials. Values as shown:

| AWG | 80 C | 90 C | 105 C | 125 C | 200 C |
|---|---|---|---|---|---|
| 8 | 65 | 70 | 75 | 90 | 100 |
| 10 | 47 | 55 | 58 | 70 | 75 |
| 12 | 36 | 40 | 45 | 50 | 55 |
| 14 | 27 | 30 | 33 | 40 | 45 |
| 16 | 19 | 22 | 24 | 26 | 32 |
| 18 | 15 | 17 | 18 | 20 | 24 |
| 20 | 10 | 12 | 13 | 14 | 17 |
| 22 | 8 | 9 | 10 | 11 | 13 |
| 24 | 6 | 7 | 7 | 8 | 10 |
| 26 | 4 | 5 | 5 | 6 | 7 |

- Bundling derating (same section): 2-5 conductors 0.8; 6-15 0.7; 16-30 0.5.
- Notes: conduit, duct, trays or raceways reduce capacity; ventilation can partly offset; higher ambient reduces headroom. Page says tables "should only be used as a guide". Chassis vs power transmission: not addressed.

Source 3: EngineeringToolbox, "AWG - American Wire Gauge Current Ratings" (section "Amp ratings vs. US AWG wire gauge") (https://engineeringtoolbox.com/wire-gauges-d_419.html), opened 2026-11-21. Basis as stated in footnote 1: "Current ratings for up to 1000 V, PVC-insulated single and multicore wiring cables, ambient temperature up to 30 oC". Also: "The AWG table below is for a single, solid, round conductor." Insulation temperature class not given for the values. Values in amperes, copper, as extracted (26 AWG current not in extracted text):

| AWG | Single core | Up to 3 cores | 4-6 cores | 7-24 cores | 25-42 cores | 43+ cores |
|---|---|---|---|---|---|---|
| 8 | 75 | 40 | 32 | 28 | 24 | 20 |
| 10 | 52 | 30 | 24 | 21 | 18 | 15 |
| 12 | 34 | 20 | 16 | 14 | 12 | 10 |
| 14 | 24 | 15 | 12 | 10 | 9.0 | 7.5 |
| 16 | 15 | 10 | 8.0 | 7.0 | 6.0 | 5.0 |
| 18 | 9.5 | 7 | 5.6 | 4.9 | 4.2 | 3.5 |
| 20 | 6.0 | 5 | 4.0 | 3.5 | 3.0 | 2.5 |
| 22 | 5.0 | 3 | 2.4 | 2.1 | 1.8 | 1.5 |
| 24 | 3.5 | 2 | 1.6 | 1.4 | 1.2 | 1.0 |
| 26 | not found in extracted text | | | | | |

- Ambient correction above 30 C (same page): 31-40 C = 0.82; 41-45 C = 0.71; 45-50 C = 0.58.
- Page notes the load "depends on installation method" and heat removal. Page text is jumbled; the values above were matched to rows by diameter and area on the page.

Source 4: Oscar Liang, wire and connector guide, section "Current Rating Look-Up Table" (https://oscarliang.com/wires-connectors), opened 2026-11-21. Single value per AWG, in amperes, as written:
- 10 AWG: 250 A
- 12 AWG: 160 A
- 14 AWG: 110 A
- 16 AWG: 80 A
- 18 AWG: 50 A
- 20 AWG: 30 A
- 22 AWG: 24 A
- 24 AWG: 20 A
- 8 AWG and 26 AWG: not found on page.
- Basis as stated: "based on the burst current requirement (e.g. current draw at full throttle)". Page also says the rating "is normally a continuous current if not specified" (general statement) and that manufacturers may differ. Temperature, free-air vs bundled, insulation and material: not stated for this table.

Not found in opened sources: silicone-insulated RC wire datasheet with AWG 8-26 continuous ratings; SAE AS50881 / J1292 chassis-wiring table; NEC or UL table opened. Values for 18-22 AWG silicone were only in Multicable and Standard Wire (200 C column) and in EngineeringToolbox (PVC, single core).

## How we could use it
- Source 1 and 2 give the only AWG 8-26 silicone-class (200 C column) values opened; both state free-air 30 C ambient and bundling derates, so they can feed a continuous-current check for `CT-*` wire entries with the stated basis.
- Sources 3 and 4 are different bases (PVC-insulated, 30 C ambient, bundled columns; and RC burst basis) and should be recorded as such, not as continuous silicone ratings; Oscar Liang's values are burst, not usable as continuous limits.
