# Brief W4c: concept-a D21 data (battery, motor current, prop diameter, cruise L/D, battery harness) set with `plane design set`

class: easy · role: design-engineer · plan: §6l W4-C (ledger D38, D21; U3.6 brief "Design PR handoff") · rules: R-a (dry run done, results below), R-b

## Read first: decisions the conductor takes before launching this brief
The dry run (tactician, tmp copy of `designs/concept-a` at `2c6fdc3`) found five things that are not the engineer's to decide. The commands below are valid and green as written; the open points change only what is asked, not how.
1. **`tests/test_discipline_gates.py::test_concept_a_d21_on_disk` goes live and FAILS.** It skips today because `pwr-001` has no `battery` key; the first command below un-skips it. With the sourced data it fails at `T2.joint_rf` (first assertion: `no structural attachment declares a connection`) and would next fail at `T3.transition_margin` (`flight.transition_speed_mps missing`, a SKIP whose message lacks "pending"). Cause: no sourced value exists for those two fields (see Deferred). The engineer must not edit the test. The conductor either amends `_check_concept_a` in a separate `core`/tests commit (accept a SKIP that names a missing D21 field) or accepts a red test on main. Do not launch before this is decided.
2. **FEA results go stale for all 28 parts** (gap G1 below): `plane fea run designs/concept-a --all` must be re-run and its `fea/*.json` committed. Alternative: fix the hash first (core commit, below). Conductor chooses.
3. **A new FAIL row appears and is real:** `T7.electrical_rating` harness `hrn-bat`: 14 AWG 45 A x 0.8 = 36.0 A against a peak of 44.8 A (4 x 11.2 A). Report-only (WARN), so no baseline change. It is a design finding, not a data error: the source's own peak is 41 A (EDGES `current_a peak=41` in `cad/amodel/electrical.py`), also above 36 A.
4. **A second new row, `T7.wiring.hrn-bat` (existing wiring gate, WARN raw FAIL):** `segment pwr-001 to hrn-002 leaves the envelopes by 40 mm (> 5 mm); add exposed_ok with a reason or reroute`. The source says these leads are taped on the skin (E-HRN-13 route `tape on the skin`), so `exposed_ok` would be sourced, but whether exposure is acceptable is a design judgement (program key `exposed_wiring_minimised`). This brief does NOT set `exposed_ok`; Tristan decides.
5. **No PDL control-surface field exists** (U3.6 added none; schema 1.0 has no servo, hinge-moment or elevon-authority field). `params-A.json` has servo values (`servo.stall_72_nm` 0.397 N m, `servo.hinge_vd_nm` 0.151 N m, `sim.elevon_stop_deg` 20) with nowhere to put them. Out of this brief; needs a schema unit if wanted.

## Environment
- Windows 11 + Git Bash. Absolute paths only. Work in the main checkout `C:/Users/trist/dbf-hangar` on `main` (D30: no branch, no PR, no worktree). `git -C C:/Users/trist/dbf-hangar status --short` must print nothing before you start; if not, stop.
- Run plane as: `export PYTHONPATH=C:/Users/trist/dbf-hangar/core; C:/ProgramData/miniforge3/python.exe -m hangar.cli <args>` (called `plane` below; use `plane` itself only if it is on PATH). Each `design validate` and `baseline check` takes about 80 s: use a 400000 ms timeout.
- OpenCAE for the FEA step is already configured in `C:/Users/trist/dbf-hangar/opencae.local.json` (python `C:/Users/trist/.conda/envs/qt_test/python.exe`, root `C:/Users/trist/Documents/OpenCAE-Studio-0.1.0`). If your shell allows environment prefixes, `OPENCAE_PYTHON=C:/Users/trist/.conda/envs/qt_test/python.exe OPENCAE_ROOT=C:/Users/trist/Documents/OpenCAE-Studio-0.1.0` in front of the command gives the same result.
- `.gitattributes` forces LF; do not change line endings. Never `git add -A` or `git add .`; add only the paths in Commit.
- Never hand-edit `plane.yaml`; every change is a `plane design set`. Never touch `core/`, `schema/`, `standards/`, `tests/`, `skills/`.
- Logs (validate output) only under `C:/Users/trist/dbf-hangar/.logs/` (not tracked; do not add).

## Where
You may change exactly these paths, all under `C:/Users/trist/dbf-hangar/designs/concept-a/`:
- `plane.yaml` and `CHANGELOG.yaml` (only through the commands below)
- `fea/*.json` (only through `plane fea run`; all 28 files are rewritten)
- `baseline.json` (only through `plane baseline update`, and only if Pass check 5 asks for it)

Part ids `wng-004-l` and `avn-001` must still exist afterwards (tests reference them). No mass, rating, threshold or standards change. Nothing in `designs/` other than `concept-a`.

## Known failures
- Before your first command, `plane baseline check designs/concept-a` prints `Result: pass`, `Regressions: 0` (verified on a pristine tmp copy at `2c6fdc3`: known results 106, unchanged 106).
- After the commands and before the FEA re-run it prints `Result: FAIL`, 1 regression `T2.fea_strength SKIP stress results out of date for 28 part(s)`. That is expected and is cleared by step 4.
- `plane design validate designs/concept-a --tier all` exits 1 before and after (tiers 2 and 3 FAIL, tier 1 and 9 SKIP). Exit 1 is not a failure of your work; compare rows, not the exit code.

## Plan coverage
| Item | Status |
|---|---|
| `components[pwr-001].battery` (capacity_mah, cells_s, max_discharge_c) | covered, command 1 |
| `propulsion.max_current_a` x4 motors | covered, command 2 (11.2 A each) |
| `propulsion.prop_diameter_mm` x4 motors | covered, command 3 (228.6 mm) |
| `flight.cruise_ld`, `flight.cruise_ld_source` | covered, command 4 |
| `wiring.harnesses[].gauge_awg` | covered, command 5 (one harness, battery to XT60 female) |
| `flight.transition_speed_mps`, `flight.transition_speed_source` | deferred: no source. MISSION.md l.17 says "Hover-to-cruise handover speed: `—` until the time-domain pitch-over (C3)"; `sitl/results.jsonl` has no `V_at_handover`; `A.param Q_TRANSITION_MS 11667` is a time in ms, not a speed. Never derive it from stall. |
| `attachments[].connection` | deferred: only `CT-M3-SHCS-INSERT` is both structural and rated (`rated_load_n` 1167) in `standards/connection-types.yaml`, and no concept-a attachment uses it (E-WNG-01 is `CT-EPOXY` in the source; the test's `CT-M3-SHCS-INSERT` is a test value). `CT-TIE` (the only other rated type) is `structural: false`, so it gives no `T2.joint_rf` row. Setting `CT-EPOXY` etc. would add SKIP rows "has no rated_load_n" and no verdict. |
| battery disconnect row (`CT-XT60` `rated_current_a` 30) | deferred: the source edge E-HRN-01 (PWR-001 to HRN-002, `CT-XT60`) is not an attachment in concept-a's tree (the pack hangs on `cge-008` and `pwr-002`); adding it is a structure change, not a D21 value |
| control-surface data | no PDL field exists (decision 5) |
| the other harness edges (E-HRN-12 `hrn-002` to `prp-003`, 14 AWG; phase leads 20 AWG) | not set: the gate reads only harnesses touching a battery |

## Gaps found by the dry run
- **G1 (affects step 4, does not block a field):** `core/hangar/fea.py:189` `FEA_COMPONENT_KEYS` hashes each motor's whole `propulsion` block into every part's D18 hash (`part_inputs_fingerprint`), but FEA reads only `axis` and `max_thrust_n` (`core/hangar/sim.py:357-361`). Adding `max_current_a` / `prop_diameter_mm` therefore stales all 28 results. Commands that show it: command 2 then `plane baseline check designs/concept-a` gives the regression above. Fix option (core commit, conductor's choice): hash only the keys FEA reads, written so the existing `{max_thrust_n, axis, role}` bytes stay identical (exclude just `max_current_a` and `prop_diameter_mm`); then the committed `fea/*.json` stay valid and step 4 is skipped. Ledger id to be assigned by the conductor.
- **G2 (no field blocked):** `plane design set ... --value "<text with ': '>"` is YAML-parsed as a mapping: `plane design set <d> flight.cruise_ld --value 7.19 --also "flight.cruise_ld_source=DBF-Combined a93f14d redesign/qp/A/MISSION.md l.17 (x): cruise L/D 7.19 ..."` fails with `value '...' is a mapping or list; give one scalar (number, text, true/false, null)` (exit 2). Worked around only by wording; the source text below has no colon followed by a space. Use it exactly. `--why` text may contain colons.
- **G3:** no PDL control-surface field (decision 5).

## Exact steps and outputs
All commands from `C:/Users/trist/dbf-hangar`. Order matters: command 5 needs `hrn-002` and `pwr-001`, which exist; commands 1 to 4 are independent. After each command expect exit 0 and the printed `old -> new` lines shown. Number formats are exact: plain decimals, no thousands separator, no exponent, no unit text.

### Step 1. Baseline of the rows (log before)
`plane design validate designs/concept-a --tier all --json > C:/Users/trist/dbf-hangar/.logs/w4c-before.json`
(create `.logs/` first with `mkdir -p`).

### Step 2. The five set commands
Source repo for every value: DBF-Combined `C:/Users/trist/DBF-Combined` at `a93f14d`, folder `redesign/qp/A/`.

1. Battery. Output: `components[pwr-001].battery.capacity_mah: None -> 2300`, `cells_s: None -> 4`, `max_discharge_c: None -> 75`.
```
plane design set designs/concept-a "components[pwr-001].battery.capacity_mah" --value 2300 --also "components[pwr-001].battery.cells_s=4" --also "components[pwr-001].battery.max_discharge_c=75" --kind add --why "BOM-A.csv W01 'Tattu 2300 mAh 4S 75C XT60 270 g'; params-A.json mission.pack_ah 2.3 Ah x 1000 = 2300 mAh (pack_v 14.8 V = 4S nominal)"
```
Units: mAh (2.3 Ah x 1000); `cells_s` an integer; `max_discharge_c` a C-rate (75), not amps.

2. Motor peak current, four motors. Output: four lines `components[prp-001-<ll|lr|ul|ur>].propulsion.max_current_a: None -> 11.2`.
```
plane design set designs/concept-a "components[prp-001-ll].propulsion.max_current_a" --value 11.2 --also "components[prp-001-lr].propulsion.max_current_a=11.2" --also "components[prp-001-ul].propulsion.max_current_a=11.2" --also "components[prp-001-ur].propulsion.max_current_a=11.2" --kind add --why "prop_a.py (DBF-Combined redesign/qp/A) output 'fresh 16.8 V duty 0.90: 11.2 A/motor, 898 gf x0.93', the state that gives max_thrust_n 8.81 in plane.yaml"
```
Unit: amps per motor at `max_thrust_n` (schema: "peak current at max_thrust_n"). It is not the 13 A motor rating (`params-A.json` req.motor_rating_a 13.0) and not the 35 A ESC rating (req.esc_rating_a); do not use those. Reproduce with `C:/ProgramData/miniforge3/python.exe -I C:/Users/trist/DBF-Combined/redesign/qp/A/prop_a.py` (stdlib, writes nothing; line 2 of its output).

3. Prop diameter, four motors. Output: four lines `...propulsion.prop_diameter_mm: None -> 228.6`.
```
plane design set designs/concept-a "components[prp-001-ll].propulsion.prop_diameter_mm" --value 228.6 --also "components[prp-001-lr].propulsion.prop_diameter_mm=228.6" --also "components[prp-001-ul].propulsion.prop_diameter_mm=228.6" --also "components[prp-001-ur].propulsion.prop_diameter_mm=228.6" --kind add --why "BOM-A.csv P02 APC 9x4.5MR (9 in); prop_a.py D = 9*0.0254 m = 0.2286 m = 228.6 mm"
```
Unit: millimetres (not the 0.2286 m of the script, not the 9 in of the part name).

4. Cruise L/D with its source text. Output: `flight.cruise_ld: None -> 7.19` and `flight.cruise_ld_source: None -> '...'`.
```
plane design set designs/concept-a flight.cruise_ld --value 7.19 --also "flight.cruise_ld_source=DBF-Combined a93f14d redesign/qp/A/MISSION.md l.17 cruise L/D 7.19 at 1.37 kg and 17 m/s (S5010 aero model, EST)" --kind add --why "MISSION.md l.17 'Cruise power, 1.37 kg: CL 0.352, L/D 7.19'; params-A.json mission.cruise_ms 17, mission.ref_mass_kg 1.37"
```
Note for the reviewer: 7.19 is at the 1.37 kg reference mass; `mission_gate_a.py` gives 7.41 at 1.472 kg. The lower, documented figure is used (conservative). Do not change it to 7.41.

5. Battery harness (creates the top-level `wiring` block as one flow line). Output: `wiring: None -> {'harnesses': [{'id': 'hrn-bat', 'from': 'pwr-001', 'to': 'hrn-002', 'gauge_awg': 14}]}`.
```
plane design set designs/concept-a wiring --kind add --value "{harnesses: [{id: hrn-bat, from: pwr-001, to: hrn-002, gauge_awg: 14}]}" --why "cad/amodel/electrical.py E-HRN-13: pack power leads, 14 AWG, PWR-001 to HRN-002 (XT60 male side); BOM-A.csv W05 14 AWG silicone"
```
The harness id must be exactly `hrn-bat` (the on-disk test looks for it in the `T7.electrical_rating` message). `gauge_awg` is an integer (14). Do NOT add `exposed_ok`, `route` or any other key (decision 4).

Expected diff of `plane.yaml` (check with `git diff --stat -- designs/concept-a/plane.yaml`): `1 file changed, 15 insertions(+), 4 deletions(-)` wait-free reading: 4 motor lines changed (4 deletions, 4 insertions), battery 4 inserted lines, `cruise_ld` and `cruise_ld_source` 2 inserted lines, `wiring:` 1 inserted line. Total 11 insertions, 4 deletions. If the counts differ, stop.

### Step 3. Rows after the commands
`plane design validate designs/concept-a --tier all --json > C:/Users/trist/dbf-hangar/.logs/w4c-after.json`
Expected change against `w4c-before.json` (tactician dry run: 644 rows before, 611 after). Tier statuses unchanged: 0 PASS, 1 SKIP, 2 FAIL, 3 FAIL, 4 PASS, 5 PASS, 6 WARN, 7 WARN, 8 WARN, 9 SKIP. The only row changes:
- gone: `T3.endurance` WARN `motor prp-001-ll: propulsion.prop_diameter_mm missing`
- gone: `T7.electrical_rating` WARN `motor prp-001-ll: propulsion.max_current_a missing`
- new: `T3.endurance` PASS `usable 27.2 Wh vs need 11.8 Wh (hover 4.94 Wh, cruise 4.87 Wh, +20% reserve); provisional: ...`
- new: `T7.electrical_rating` PASS `pack pwr-001: discharge rating 172.5 A vs peak 44.8 A x 1.0`
- new: `T7.electrical_rating` WARN (raw FAIL, report-only) `harness hrn-bat: 14 AWG 45 A x 0.8 = 36.0 A vs peak 44.8 A`
- new: `T7.wiring.hrn-bat` WARN (raw FAIL, report-only) `segment pwr-001 to hrn-002 leaves the envelopes by 40 mm (> 5 mm); add exposed_ok with a reason or reroute`
- replaced: the 28 `T2.fea_strength` result rows (27 PASS, 2 SKIP rows of `cge-001` included) by one SKIP `stress results out of date for 28 part(s) ... re-run plane fea` (cleared by step 4).
Unchanged (must stay as before): `T2.joint_rf` SKIP (no attachment declares a connection), `T3.control_authority` pitch PASS, roll PASS, yaw WARN raw FAIL (ratio 1.10 vs 1.5), `T3.transition_margin` speed-margin SKIP (`flight.transition_speed_mps missing`) and entry-thrust PASS (0.51 vs 0.8). Any other difference: stop and report.

### Step 4. FEA re-run (skip only if the conductor has fixed G1 and `plane baseline check` already prints `Regressions: 0`)
```
plane tools doctor
```
First line must start with `opencae      ok`; if not, stop.
```
plane fea run designs/concept-a --all
```
Do not pass `--part`; all 28 files in `designs/concept-a/fea/` are rewritten (expected: the same parts, `cge-001` still reports the coarse-mesh SKIP). This is slow (OpenCAE/CalculiX, 28 parts); use the maximum timeout, and run in the background if your shell allows it. Not run by the tactician (instructed).

### Step 5. Baseline
`plane baseline check designs/concept-a`
- Expected: `Result: pass`, `Regressions: 0`. If it lists only Improvements, run `plane baseline update designs/concept-a` and stage `designs/concept-a/baseline.json`. If it lists a Regression, stop and report (do not update).
- Re-run `plane design validate designs/concept-a --tier all --json > C:/Users/trist/dbf-hangar/.logs/w4c-final.json`; the row changes against `w4c-before.json` must now be exactly the Step 3 list minus the `T2.fea_strength` replacement (PASS values within the FEA solver's own noise; judge by the baseline check, not by digits).

## Pass check
1. Each of the five commands exited 0 and printed the `old -> new` lines above.
2. `git diff --stat -- designs/concept-a/plane.yaml` shows 11 insertions and 4 deletions (the numbers in Step 2).
3. `git diff -- designs/concept-a/plane.yaml | grep -c "wng-004-l\|avn-001"` prints `0` and `grep -c "id: wng-004-l\|id: avn-001" designs/concept-a/plane.yaml` prints `2` (ids untouched).
4. Step 3 and step 5 row lists match.
5. `plane baseline check designs/concept-a` exits 0.
6. `git status --short` lists only: `designs/concept-a/plane.yaml`, `designs/concept-a/CHANGELOG.yaml`, `designs/concept-a/fea/*.json` (28), and `designs/concept-a/baseline.json` only if updated. `git diff --name-only | grep -c "^core/\|^schema/\|^standards/\|^tests/"` prints `0`; `git ls-files --eol | grep -c "w/crlf"` prints `0`.
7. The conductor (not you) then runs `pytest -q -m "" tests/test_discipline_gates.py tests/test_fea_hash.py tests/test_fea.py tests/test_adapters.py tests/test_gates.py` and `plane progress --write`; `test_concept_a_d21_on_disk` is expected to fail until decision 1 is taken.

## Commit
If your Bash cannot run `git add` and `git commit`, stage nothing, stop after Pass check 6 and hand the file list to the conductor. Otherwise one commit on `main`, no push to any other branch, no PR (D30): stage exactly the paths of Pass check 6, message first line `design: concept-a D21 data (battery, motor current, prop diameter, cruise L/D, battery harness) (D38)`; body lines: `migration: none (data only; the schema fields exist since U3.6)` and `deferred: flight.transition_speed_mps (no source), attachments[].connection (no sourced rated structural type), control-surface data (no PDL field)`. Trailers, exactly: `Co-authored-by: Tristan Hottier <185231225+TristanHottier@users.noreply.github.com>` then the agent attribution line from your own system reminder. Do not run `plane progress --write`; do not edit the plan, `PROGRESS.md` or the ledger.

## Stop rule
Stop and report (command, exit code, first error line) instead of improvising when: the working tree is not clean at the start; a command exits non-zero or prints different `old -> new` lines; the diff counts in Pass check 2 differ; a Step 3 row appears or disappears that is not listed; `plane tools doctor` does not start with `opencae      ok`; `plane baseline check` shows a regression after step 4; you would need a value that is not in this brief (transition speed, connection ids, `exposed_ok`, servo data): leave it unset. Never edit a test, `core/`, `schema/` or `standards/`, never lower a threshold, never change a mass. Two failed attempts at the same step: stop and report to the conductor (it goes to `advisor`).
