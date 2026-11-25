# U18.1 study: OpenCAE CLI as hangar's physics backend (D89), W34-T3, 2026-11-25

Clone: `C:/Users/trist/OpenCAEModel-main` (OpenCAEModel main, head 620a11c / 8a1dc84; read-only, never pushed, no source copied; GPL-3.0, run only as an external program).
Scratch (project copies and outputs, nothing written into `designs/` or `core/`): `C:/Users/trist/AppData/Local/Temp/claude/56ffcdcd7ae967f7/44b963d0-55e7-40b4-ab48-7fb9b502ef73/scratchpad/` (`quad250/`, `u1314/`).
Recorded outputs that the briefs use as test fixtures: `plans/2026-11-20-standardization/u18.1/fixtures/`.

## 1. Which Python runs it, and what is missing

| env | Python | result |
|---|---|---|
| `C:/Users/trist/.conda/envs/opencae` | 3.15.2 | cannot run OpenCAE: no numpy, scipy, pyvista, vtk, gmsh, meshio, matplotlib, OCP (PySide6 only). It does hold `ccx.exe` (CalculiX 2.23, `Library/bin/ccx.exe`), which OpenCAE's doctor finds from any env. |
| `C:/Users/trist/.conda/envs/qt_test` | 3.12.16 | runs everything: PySide6 6.12.0, pyvista, vtk, gmsh 4.15.2, meshio, matplotlib, OCP, numpy, scipy. (trimesh is absent there; OpenCAE does not need it.) |

Nothing was installed. Nothing is missing for qt_test. For a clean machine the command would be (not run): `python -m pip install -r C:/Users/trist/OpenCAEModel-main/requirements.txt` into a Python 3.11+ env (PySide6 6.12.0, pyvista 0.49.1, pyvistaqt 0.13.1, vtk 9.6.2, gmsh 4.15.2, meshio 5.3.5, numpy 2.4.6, scipy 1.17.1, matplotlib 3.11.2, cadquery-ocp 8.0.1.1.0) plus CalculiX `ccx` (conda-forge `calculix`). Hangar's existing `opencae.local.json` python (qt_test) is therefore already the right interpreter; only the ROOT differs: the CLI needs the new clone (it has `opencae/cli.py`); the old `OpenCAE-Studio-0.1.0` has none.
Run form: `cd <clone root> && PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 <python> -m opencae <command>`. With `--json` stdout is exactly one JSON object and progress goes to stderr; exit 0 done, 1 an analysis ended in `error`, 2 bad input.

## 2. Commands run (each once) and timings

| command | wall time | result |
|---|---|---|
| `python -m opencae doctor --json` (qt_test) | 13.9 s (first start) | python 3.12.16 ok; ccx 2.23 found; openfoam `available:false`; gmsh 4.15.2; ocp; pyside6 6.12.0; free disk 134.7 GB. Fixture `doctor_no_openfoam.json`. Doctor has NO SU2 entry. |
| `opencae setup su2 --json` (no `--yes`) | 0.5 s | only prints: would download about 40 MB, `https://github.com/su2code/SU2/releases/download/v8.1.0/SU2-v8.1.0-win64.zip`, into `C:\Users\trist\.opencae\solvers\SU2-v8.1.0`, `confirmed:false`. `--yes` NOT run. |
| `opencae run <quad250 copy> --only mass,propulsion --json` | 1.4 s | exit 0. mass 472 g, CG x -5.8 mm; T/W 6.65; hover throttle 0.314; hover 15.75 min; margins motor 2.31, ESC 2.02, battery 2.06; checks `conditional` (all inputs are estimates). |
| `... --only mass,propulsion,structure --json` | 27.1 s | exit 0. structure `conditional`: weakest arm_fl SF 12.26 at 2 x thrust, p99 stress 48.9 MPa, 2.02 mm deflection; 4 arms x about 5 s CalculiX, about 10k elements each. Fixture `quad250_mass_propulsion_structure.json` (also holds the mass and propulsion results). |
| `... --only mass,propulsion,flight --json` | 1.9 s | `conditional`: levelled in 1.5 s, peak tilt 15 deg, drift 17 cm, throttle headroom 0.83. Fixture `quad250_mass_propulsion_flight.json`. |
| `... --only cfd --json` | 11 min 22 s (runtime_s 505.8: mesh 13.7 s, body boolean 2.9 s, SU2 solve 388.5 s; the rest was OpenCAE startup and a first wait on the fusing step) | exit 0. `cfd.solver: auto`, no OpenFOAM: fell back to SU2 (found through the machine's `SU2_RUN=C:/Program Files/bin`, which holds `SU2_CFD.exe`; doctor does not list SU2). Coarse 149,237 tetrahedra, 300 iterations, `converged:true` (residual criterion not met, force change last 10 % 4.1e-5), status `conditional`. Metrics cl -0.094, cd 1.011 (on the frontal area 0.0030 m2 of the CAD, no wing), ld -0.093, lift -0.04 N, drag 0.42 N at 15 m/s. OpenCAE says SU2 drag is indicative only. Fixture `quad250_cfd_su2.json` (also carries the earlier structure and flight results). |
| `plane design mass designs/concept-a-param` | 7.0 s | 1273.0 g, CG [21.35, -2.02, 6.62] mm |
| `plane design validate designs/concept-a-param --tier all` | about 10 s | rows quoted in section 4 |
| `plane design export designs/concept-a-param --format stl --out <scratch>/stl` and `--format json` | 9.4 s | 113 per-component STL files (115 components; hrd-001 26.08 g and hrn-001 22.5 g are point masses with no mesh) |
| `opencae run <scratch>/u1314 --only mass,propulsion --json` (hand-built drone.json plus one 32.7 MB ASCII STL of 113 named solids) | 6.0 s | exit 0, see section 4. Fixture `concept-a-param_mass_propulsion.json`; the hand-written input is `concept-a-param.drone.json`. |
| structure and cfd on concept-a-param | not run | structure needs wing material E, nu, yield (PDL has none: gap G6) and a 32 MB STL; cfd is a long run. |

## 3. Mapping hangar PDL to drone.json (concept-a-param, a tailsitter flying wing)

Geometry: hangar STL export is millimetres in the design frame (origin at the wing leading edge). The hangar nose is -x (forward thrust axis `[-1,0,0]`), so the project uses `geometry.forward:"-x"`, `up:"+z"`, `units:"mm"`. OpenCAE then works in x forward, y left, z up, which negates hangar x and y. Parts must be NAMED SOLIDS of one ASCII STL (a binary or unnamed STL becomes `part_1`, `part_2`, ...). Solid name = `<role>_<component id with non-alphanumerics as _>`; the battery is named `battery`. `roles` holds one glob per role.

| drone.json key | PDL source | evidence status |
|---|---|---|
| `format` | constant `"opencae-drone/1"` | n/a |
| `name` | `id` | n/a |
| `type` | `morphology.lift`/`vtol_method`: multirotor -> `multirotor`; vtol_method tailsitter -> `tailsitter`; other vtol_method -> `vtol`; none -> `fixed_wing` | n/a |
| `engine` | constant `"generic"` | n/a |
| `geometry.file/units/forward/up` | `airframe.stl`; `mm`; `-x`; `+z` | n/a |
| `roles` | component `type`: motor->motor, propeller->prop, battery->battery, wing->wing, tail_surface->fin, landing_gear->landing, boom->arm, structure->frame, flight_controller/receiver/esc/servo->electronics, other->other | n/a |
| `mass.parts.<solid>` (g) | `components[].mass_g`, or the generated mass (`plane design mass` per_component) | `provenance.mass_source`: measured->measured, datasheet->datasheet, cad->estimate, estimate->estimate, absent->estimate |
| `mass.payload_g` | 0 | user |
| `propulsion.rotors` | `"auto"` gives one rotor per `motor` part pointing forward/up by type and ignores cant. Canted motors (17 deg here) need an explicit list: position from the motor mesh centre, axis = `propulsion.axis` with x and y negated | n/a |
| `propulsion.motor.kv, r_ohm, i0_a` | NOT IN PDL (gap G1); only the text "KV780" in the description | sidecar value, else `null` |
| `propulsion.motor.i_max_a` | `components[motor].propulsion.max_current_a` | datasheet when the matching `bom[].verified.method` is datasheet, browser or webfetch; measured when in-hand; else estimate |
| `propulsion.motor.mass_g` | `components[motor].mass_g` | as mass |
| `propulsion.prop.diameter_in` | `propulsion.prop_diameter_mm / 25.4` | as i_max_a |
| `propulsion.prop.pitch_in, ct, cp` | NOT IN PDL (G2) | sidecar, else `null` |
| `propulsion.battery.cells` | `battery.cells_s` | as i_max_a |
| `propulsion.battery.capacity_mah` | `battery.capacity_mah` | as i_max_a |
| `propulsion.battery.c_rating` | `battery.max_discharge_c` | as i_max_a |
| `propulsion.battery.r_int_mohm_per_cell` | NOT IN PDL (G3) | sidecar, else `null` |
| `propulsion.battery.usable_fraction` | `standards/operations.yaml#battery_usable_fraction` | user |
| `propulsion.esc.i_cont_a` | NOT IN PDL as a number (G4; "35A" only in the description) | sidecar, else `null` |
| `propulsion.esc.efficiency` | NOT IN PDL (G5); `propulsive_efficiency` in operations.yaml is a different quantity, do not reuse | sidecar, else `null` |
| `aero.cruise_speed_ms` | `requirements.cruise_speed_mps` | user |
| `aero.alpha_deg` | 0 | estimate |
| `aero.ref_area_m2, ref_chord_m` | main-wing planform area and MAC from hangar (optional) | n/a |
| `mission.hover_s, cruise_s` | `operations.yaml#mission_hover_min`, `mission_cruise_min` x 60 | user |
| `environment.rho, g` | `flight.air_density_kgm3` (else 1.225); 9.80665 | user |
| `materials.<name>` density, E, nu, yield | `design.materials` has density only; no E, nu or yield (G6) | sidecar or sourced `standards/materials.yaml` value |
| `role_materials` | component `material` string -> materials key | n/a |
| `analyses.structure.load_factor` | `design-standards.yaml#ultimate_factor` | user |
| `analyses.cfd.enabled/preset/iterations/solver` | enabled only when a solver is found (section 6); `coarse`; `auto` | user |
| `analyses.flight.enabled` | true only for multirotor, vtol, tailsitter | user |
| `requirements[]` | not written; hangar judges the metrics itself and ignores OpenCAE's verdict | n/a |

Gaps G1-G6 are listed in the table: OpenCAE needs motor kv/R/i0, prop pitch/ct/cp, battery R_int, ESC rating and efficiency, and material E/nu/yield, and PDL holds none of them. Point masses (no mesh) drop out because OpenCAE needs a solid per part (hrd-001, hrn-001: 48.58 g). Proposal (conductor decides; `designs/` and `core/` cannot share a PR): a sidecar `designs/<id>/opencae-inputs.yaml` with `value/unit/status/source` per drone.json key, no PDL schema change. An absent key becomes `null`, so OpenCAE reports `not_evaluated` and names the key instead of guessing. The hand-written `concept-a-param.drone.json` used estimate placeholders (kv 780 from the description, r 0.12, i0 0.5, ct 0.11, cp 0.045, ESC 35 A, R_int 8 mohm); they are NOT sourced and no gate may rest on them.

Evidence status, hangar to OpenCAE: `provenance.mass_source` measured/datasheet/cad/estimate -> measured/datasheet/estimate/estimate; `bom[].verified.method` datasheet|browser|webfetch -> datasheet, in-hand -> measured; a value with only a `*_source` text -> estimate; values taken from `standards/*.yaml` or the mission (hover time, load factor, rho, cruise speed, usable fraction) -> user; `max_thrust_n: pending` -> `null`. An attachment's `rating_basis` (sourced/derived/placeholder) has no OpenCAE equivalent and is not exported. Back from OpenCAE each metric has `basis` (`estimate`, `datasheet`, `measured`, or empty) and an analysis status `ok|conditional|watch|fail|not_evaluated|error`.

## 4. concept-a-param: OpenCAE against hangar

| quantity | OpenCAE (`mass,propulsion`) | hangar | note |
|---|---|---|---|
| mass | 1224.4 g | 1273.0 g (`plane design mass`) | the 48.6 g difference is exactly the two point masses (26.08 + 22.5) that have no STL |
| CG x | -19.79 mm (nose frame) = +19.79 mm hangar | +21.35 mm | 1.6 mm, from the missing point masses |
| CG y | +2.12 mm (flipped) = -2.12 mm hangar | -2.02 mm | agrees |
| CG z | 6.61 mm | 6.62 mm | agrees |
| hover thrust to weight | tw_ratio 2.91 (4 rotors, no cant) | T3.hover_tw 2.70 (upward thrust 33.7 N of 35.2 N rated) | OpenCAE thrust 8.73 N per rotor comes from estimated kv/ct/cp; hangar uses the sourced 8.81 N. Use the explicit rotor list to include the cant |
| currents | full throttle 46.8 A; margins motor 1.008, ESC 3.15, battery 3.69 | T7.electrical_rating: pack 172.5 A vs peak 44.8 A (4 x 11.2 A), ratio 1.0 | OpenCAE derives current from kv/R/i0/ct/cp; hangar sums datasheet `max_current_a` |
| hover | throttle 0.518, 9.05 A, 131 W electrical, 12.2 min | T3.endurance: energy based (hover 5.01 Wh, usable 27.2 Wh, 20 % reserve), no current | OpenCAE hover power includes motor, ESC and battery losses; hangar's is actuator-disk power over `propulsive_efficiency`, so the two disagree by construction |

OpenCAE verdict `conditional` (all inputs are estimates); R-STR, R-LD and R-FLT `not_evaluated` because those analyses were not requested.

## 5. What each OpenCAE metric feeds in hangar

| OpenCAE result | hangar check | relation |
|---|---|---|
| `propulsion.tw_ratio`, `thrust_total_max_n`, `hover_throttle` | T3.hover_tw | alongside, new row `T2.opencae_hover_tw`; not a replacement (it needs electrical inputs PDL lacks) |
| `propulsion.motor_current_margin`, `esc_current_margin`, `battery_current_margin` | T7.electrical_rating | new row `T2.opencae_current_margin`, same `operations.yaml#electrical_rating_min_ratio`; adds motor and ESC ratings that T7 does not check |
| `propulsion.hover_endurance_min`, `hover_current_a`, `hover_power_w` | T3.endurance | new row `T2.opencae_endurance` against `mission_hover_min` x (1 + `energy_reserve_fraction`); the gap between the two models is a finding in itself |
| `structure.safety_factor`, `max_stress_mpa`, `max_disp_mm` (arms; wings for fixed wing) | T2.fea_strength (old runner, per printed part) | alongside; the old route stays; new row `T2.opencae_structure_sf` |
| `cfd.cl`, `cfd.cd`, `cfd.ld` | declared `flight.cruise_ld` | new row `T2.opencae_cfd_ld` compares computed with declared L/D; SU2 drag is "indicative only" per OpenCAE docs |
| `flight.max_tilt_deg`, `settle_time_s`, `position_error_m`, `throttle_margin` | T3.control_authority | new row `T2.opencae_flight`; thresholds pending |
| `mass.mass_kg`, `cg_mm` | `plane design mass` | cross-check row `T2.opencae_mass_cross` |

For U18.2-U18.4 (other tactician): U18.2 (calibration vs a real C172) can use OpenCAE `mass.cg_mm`, `mass.inertia_kgm2` and `cfd.cl/cd/ld` of a full-size drone.json as an independent computed number next to the published MTOW, wing area, L/D and cruise figures. U18.3 (beam-theory spar bending) is compared in a test against `structure.max_stress_mpa`, `safety_factor` and `max_disp_mm` on one wing. U18.4 (trim and stability) can take `mass.inertia_kgm2` and `cfd.cl/cd` as inputs; OpenCAE's `flight` is a hover model and "not available for a fixed wing", so trim and dynamic modes stay with AeroSandbox or AVL.

## 6. SKIP rules, CI, cache

- Rows read stored results only (like `fea.tier2_fea`); `plane validate` never launches OpenCAE. A missing, stale or unsolvable result gives `SKIP` with the reason and the fix command first. CI has no OpenCAE: its tests use the fixtures and `skipif` the live one.
- CLI found = a root with `opencae/cli.py` plus a Python for which `-m opencae doctor --json` exits 0. structure needs `doctor.ccx.available`. cfd needs `doctor.openfoam.available` OR an SU2 install; doctor does not list SU2, so hangar looks for `SU2_CFD(.exe)` on PATH, in `SU2_RUN`, `OPENCAE_SU2`, `C:/SU2**/bin`, `Program Files/**/bin` and `~/.opencae/solvers/**/bin` (the places OpenCAE's `find_su2` searches). Without a solver hangar must not run `--only cfd` (not tested here: on this machine SU2 exists through `SU2_RUN`). `setup su2 --yes` downloads about 40 MB from github.com/su2code/SU2 and is a human step.
- Hash (like `fea.part_hash`): first 16 hex of sha256 over canonical `drone.json` bytes, `airframe.stl` bytes, the sorted analysis list, the clone's `git rev-parse HEAD` (else the `pyproject.toml` version) and the `standards/` values the export reads (`ultimate_factor`, `battery_usable_fraction`, `mission_hover_min`, `mission_cruise_min`, `electrical_rating_min_ratio`, `energy_reserve_fraction`, `hover_thrust_to_weight_min`). Stored at `designs/<id>/opencae/results.json` with `design`, `hash`, `analyses`, `opencae_head`, `result` (the `--json` object). OpenCAE's own cache lives in a scratch project folder and every hangar run passes `--force`, so hangar's hash is the only staleness rule.
- Time budget: mass+propulsion 1-6 s; structure about 5 s per arm (27 s for quad250); flight 2 s; cfd: OpenFOAM coarse 5-20 min per OpenCAE docs; SU2 on quad250 took 11 min 22 s wall (mesh 14 s, solve 389 s) at the coarse preset.

## 7. Open points for the conductor

1. Sidecar `designs/<id>/opencae-inputs.yaml` for G1-G6 (assumed by the briefs) vs a PDL schema bump. Adding a sidecar to a real design is a later data PR, not in these briefs.
2. Row status policy: PASS/FAIL against existing standards keys, `; basis estimate` appended and `data.basis` set; a pass on estimates stays PASS (hangar has no conditional). Alternative: SKIP-with-would_be when basis is estimate.
3. New thresholds (`opencae_structure_sf_min`, `opencae_flight_settle_s_max`, `opencae_cfd_ld_tolerance_fraction`, `opencae_mass_cross_tolerance_g`) are added with `source: pending` (D88 sources them later), so those rows report with `would_be`.
4. New row ids `T2.opencae_*`: if `baseline.py` or applicability must list them, brief 2 stops and reports rather than guessing.
