# Scout task spec U13.8: 3-5 g sub-micro servos for a 1:10 Cessna 172 wing (W31-S)

class: easy · role: `scout` (Haiku), launched by the conductor · plan: §7 U13.8 (rehearsal 4 gap 3, c172-rc) · brief: U13.8-5-scale-props-servo-scout

## Target (sizes the parts)
Cessna 172 at 1:10 (`knowledge/reference-aircraft/c172.md`): span 1.2-1.4 m, MTOW about 1 kg, wing about 14 mm thick at the root. Control-surface servos (aileron, flap) must lie flat inside that wing:
- body thickness (the axis perpendicular to the servo's mounting face) at most 10 mm, so the servo fits under the skin with its 3.7-5 g class mass;
- torque at least 1.5 kg-cm at 4.8-6 V.

Comparison: `knowledge/parts/emax-es08maii-metal/part.yaml` (11.5 x 23 x 24 mm, 12 g) is too thick for a 14 mm wing and is the reference row. Do not rewrite it.

## Rules for the scout (from `.claude/agents/scout.md`; same as the 11-24 spec)
- Open each vendor page; cite only pages you opened in this run, with the date checked (today's date). Unknown value -> `not found`; never guess a mass, a dimension, a URL or a part number.
- A part is written to `knowledge/parts/` only if the vendor page (or a datasheet you opened) gives a stated mass AND three dimensions. Otherwise a table row with `not found` and no part.yaml.
- Do not download vendor CAD files (licence unknown). Record the CAD link and its licence text instead.
- A blocked site -> write `blocked: <site>` and continue.
- Do not recommend; list facts only. The conductor chooses. Do not choose between near-identical candidates; list both.
- Stop after the candidate list; do not add other servo classes.

## Candidates wanted
3 to 5 sub-micro servos in the 3-5 g class from vendors that publish dimensions and mass. Search the vendors' own product pages: Spektrum, Hitec, Emax, KST, Hobbywing, Blue Arrow, Corona, GWS. Any other vendor that publishes mass, three dimensions, torque and voltage is also acceptable.

For each candidate record:
- vendor; part number as printed; URL (page opened);
- mass g (say whether with or without leads/horn);
- dimensions L x W x H in mm, with mounting tabs included and, if given, excluded;
- torque kg-cm and voltage (state the voltage for each torque);
- speed s/60 deg at the stated voltage;
- gear material; connector type;
- vendor CAD link and its licence text, or `none stated`.

## Output
1. Knowledge record `knowledge/parts/<part-id>/part.yaml` only for a candidate with a stated mass and three dimensions. Schema in `knowledge/parts/README.md`. `id` = folder name (`^[a-z0-9][a-z0-9_-]*$`); `category: servo`; `dimensions_mm: [x, y, z]` envelope in the part frame (y = servo width, z = height, x = length); `verified: {by: <your scout id>, date: 'YYYY-MM-DD', method: browser}`.
   - `cad_status: vendor-cad` only when you opened a vendor page offering CAD for exactly this part; otherwise `representative-envelope`.
   - `cad_source`: with vendor CAD: `<CAD URL>; licence: <exact licence or terms text, or "none stated">; not downloaded`. Otherwise: where the envelope came from (page and table row).
   - `geometry`: box parts use `{generator: plate, params: {plane: xy, size: [<x>, <y>], thickness: <z>}}` with x, y, z equal to `dimensions_mm`.
2. Result table `plans/2026-11-20-standardization/u13.8/parts-found-servo.md` with the same 11 columns as the 11-24 spec: `part-id | category | vendor | part number | URL | mass g | envelope mm (x y z) | key spec | vendor CAD link | CAD licence | in library (yes/no, why not)`. One row per candidate, plus the `emax-es08maii-metal` comparison row (11.5 mm thickness, 12 g). Every cell filled (`not found` allowed).

## Pass check (mechanical; paste the output into the hand-back)
- `$PY -m hangar.cli parts list` lists each new id.
- `$PY -m hangar.cli parts show <id>` exits 0 for each new id (any message the loader prints must be fixed in the record).
- Every table row has all 11 columns filled.
- Report how many candidates reached `knowledge/parts/` and why each other did not.

## Stop rule
- Site needs a login or is blocked: record `blocked`, continue.
- Mass or a dimension not stated: no part.yaml; table row with `not found`.
- Two near-identical candidates: list both, do not choose.
- A required field cannot be filled from an opened page: `not found`, not a guess.
