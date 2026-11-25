# Scout task spec U4.36: fixed-wing real parts for a 1-3 kg scale model (W31-S)

class: easy · role: `scout` (Haiku) · four scouts, one per lot below, run in parallel · plan: §7 U4.36 item (5) · launched by the conductor, one lot per scout.

## Target aircraft (sizes the parts)
Cessna 172 at 1/8 scale (`designs/c172-rc` stub, `knowledge/reference-aircraft/c172.md` section 7): span 1.375 m, MTOW 2.26 kg, power guide about 260 W, 4S (14.8 V) battery, one tractor motor, 3 or 4 servos (aileron x2, elevator, rudder; flaps optional), 9-11 inch 2-blade prop with a spinner. Parts must also suit a generic 1-3 kg, 1.2-1.8 m trainer or scale model.

## Rules for every scout (from `.claude/agents/scout.md`)
- Open each vendor page; cite only pages you opened in this run, with the date checked (use today's date). Unknown value -> `not found`; never guess a mass, a dimension, a URL or a part number.
- A part is written to the library only if the vendor page (or datasheet you opened) gives mass AND the three envelope dimensions. Otherwise list it in your table with `not found` and write no part.yaml.
- Do not download vendor CAD files (licence unknown). Record the CAD link and its licence text instead (below).
- A blocked site -> write `blocked: <site>` and continue.
- Do not recommend; list 2-3 candidates per category with facts only. The conductor chooses.
- Skip anything already in `knowledge/parts/` (run `plane parts list` first): tmotor-mn2212-v2-kv780, apc-9x4-5mr-prop, speedybee-bls-35a-mini-v2-esc, emax-es3054hv-servo, radiomaster-rp3-v2-elrs-rx, tattu-2300mah-4s-75c are present and are not what is asked here (they are multirotor/tailsitter picks).

## Output per part
1. A library record `knowledge/parts/<part-id>/part.yaml`, schema in `knowledge/parts/README.md` (copy the style of `knowledge/parts/tmotor-mn2212-v2-kv780/part.yaml`): `id` is a lower-case slug equal to the folder name (`^[a-z0-9][a-z0-9_-]*$`); `category` one of `motor|propeller|esc|servo|receiver|other` (spinner = `other`); `vendor`, `part_number` (as printed by the vendor), `url` (the page you opened), `mass_g` (number > 0, the part alone without leads unless the page says with leads: say which in `cad_source`), `dimensions_mm: [x, y, z]` envelope in the part frame (x = shaft/axial direction for motors, props and spinners), `verified: {by: <your scout id>, date: 'YYYY-MM-DD', method: browser}`.
   - `cad_status`: `vendor-cad` only when you opened a vendor page offering CAD (STEP/STL/SolidWorks) for exactly this part; else `representative-envelope`.
   - `cad_source`: when vendor CAD exists: `<CAD URL>; licence: <the exact licence or terms text on that page, or "none stated">; not downloaded`. Otherwise: where the envelope came from (e.g. "vendor drawing on <URL>, dimensions table row <n>").
   - `geometry`: round parts (motors, props, spinners): `{generator: tube, params: {axis: x, length: <x>, outer_d: <largest diameter>}}`; box parts (ESCs, servos, receivers): `{generator: plate, params: {plane: xy, size: [<x>, <y>], thickness: <z>}}` with x, y, z equal to `dimensions_mm`. (Both generators are registered; the loader requires only a generator name, and `plane generators show plate` is not yet available, so use exactly these params.)
2. One result table per scout, `plans/2026-11-20-standardization/u4.36/parts-found-<lot>.md` (the scout may write this one path): a markdown table with columns `part-id | category | vendor | part number | URL | mass g | envelope mm (x y z) | key spec | vendor CAD link | CAD licence | in library (yes/no, why not)`; one row per candidate including those not written (with `not found` cells).

## Lots
- **lot A (motor, ESC):** 3 brushless outrunner motors for a 1-3 kg propeller airplane (roughly 150-400 W, 4S, 9-11 inch prop; give kV and max current/power in `key spec`); 3 ESCs (30-50 A, 3-4S; BEC yes/no; give continuous and burst current).
- **lot B (servos, receiver):** 3 micro/mini servos for control surfaces of a 1-3 kg airplane (9-20 g class; give torque kg-cm at the stated voltage, speed, gear material); 2 receivers suited to a small airplane (ELRS or similar, 5-12 g; give the antenna type and channels).
- **lot C (propellers, spinner):** 3 two-blade propellers 9-11 inch for 4S electric (APC E / thin electric, or comparable; give diameter x pitch in inches and the shaft/adapter bore) and 2 spinners/prop adapters that fit them (aluminium or plastic, 30-45 mm cone diameter; give the cone diameter, length, the shaft size). For the prop envelope use `[axial_thickness, diameter, diameter]` with the axial thickness from the vendor drawing; if the vendor gives none, `not found` and no part.yaml.
- **lot D (airfoil coordinates):** write `knowledge/airfoils/clarky.dat` and `knowledge/airfoils/sd7037.dat` by copying, unchanged, the coordinate file from the UIUC airfoil coordinates database (the page https://m-selig.ae.illinois.edu/ads/coord_database.html lists them; files `clarky.dat`, `sd7037.dat`) after opening each; replace nothing; if the first line is not a title, insert a first line `<airfoil name> (UIUC <file URL>, checked <date>)` (the file `designs/concept-a-param/airfoils/s5010.dat` shows the layout). Parse check: `PYTHONPATH=core C:/ProgramData/miniforge3/python.exe -c "from hangar.geom.wing import read_airfoil; u,l = read_airfoil('knowledge/airfoils/clarky.dat'); print(len(u), len(l))"` prints two counts above 20. Table `parts-found-D.md` has columns `name | file | source URL | date checked | points upper/lower`. Lot D needs `knowledge/airfoils/` from brief U4.36-4 (merged first); until then write the files under `plans/2026-11-20-standardization/u4.36/airfoils/` and the conductor moves them.

## Pass check (mechanical; paste the output into your hand-back)
- Lots A-C: `PYTHONPATH=core C:/ProgramData/miniforge3/python.exe -m hangar.cli parts list` lists each new id, and `... parts show <id>` exits 0 for each (the library loader validates the schema; any message it prints must be fixed); `...-m hangar.cli parts list --category <category>` shows it under its category.
- Every table row has all 11 columns filled (`not found` allowed, empty cells not).
- Count: each lot reports how many of its candidates reached `knowledge/parts/` and why each other did not.

## Stop rule
- A vendor page needs a login or is blocked: record `blocked`, continue. - Mass or a dimension is not stated: no part.yaml, table row with `not found`. - A choice between near-identical candidates: do not choose; list both. - Stop after the lot's list; do not add categories.
