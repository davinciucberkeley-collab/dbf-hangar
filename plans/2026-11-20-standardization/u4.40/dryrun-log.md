# D84 dry run: import of DBF-Combined origin/redesign/v1 (d83b26f) as concept-a-reborn (W32-T, 2026-11-24)

Nothing pushed. DBF-Combined untouched (read only: `git archive`). Throwaway worktree `C:/Users/trist/wt/w32-reborn-dryrun` (branch `dry/reborn`, from origin/main e5fcec3). Machine: Windows 11, one heavy process at a time. `plane` was run as `python -c "from hangar.cli import cli; cli()"` with `PYTHONPATH=<worktree>/core` (the worktree has no venv of its own); the commands are the same as `plane ...`.

## Result in one paragraph

The importer as it stands on main CANNOT import v1: it stops at the first part (PRP-001-LL). Four importer/standards gaps and one ledger-importer gap were found (B1 to B5 below). To see what comes after, the dry run used throw-away stand-ins in a scratch wrapper outside the repo (probe P1/P2/P4; no file in `core/` was edited). With the stand-ins the import ran to the end, so the later steps (claims, validate, baseline, ledger) were exercised on a faithful, not hull-faked, model. Until B1 to B5 are built, Dillon cannot do the import.

## Commands, timings, outputs

| # | Command | Time | Result |
|---|---|---|---|
| 1 | `git -C C:/Users/trist/DBF-Combined archive d83b26f \| tar -x -C <scratch>/dbf` | 6 min 24 s | OK. 15 997 files, about 0.5 GB. Slow only because of the file count on Windows. No `.git` in the extract (see B6). |
| 2 | `git worktree add -b dry/reborn C:/Users/trist/wt/w32-reborn-dryrun origin/main` | under 1 min | OK (1 247 files). |
| 3 | `plane import dbf --dbf-root <scratch>/dbf --concept A --id concept-a-reborn` (importer as on main) | 49 s to fail | FAIL: `GeometryError: PRP-001-LL: GLB mesh cannot be repaired to a watertight solid` (B1). |
| 3b | same, with stand-in P1 only | 53 s to fail | FAIL: `PRP-006-LL: GLB mesh cannot be repaired...` (B2). |
| 3c | same, P1 + P2 | 65 s to fail | FAIL again at WNG-001 (B1 again: the P1 stand-in at that stage merged vertices, which was the wrong repair). |
| 3d | same, with a convex-hull stand-in for the failing parts | 820 s to fail | FAIL: `KeyError: 'CT-A-M3-CSK-MOTOR'` in `_write_yaml` (B3). Hull wing made the later validate run meaningless; discarded. |
| 3e | same, final stand-ins P1'' (separate coincident vertices), P2 (plain union for PRP-006), P4 (two connection types mapped to bolted) | 796 s (13 min 16 s) | OK. Wrote `designs/concept-a-reborn/` (plane.yaml 239 kB, 129 STL meshes, import-report.json), 9.2 MB. Prints the path of plane.yaml. |
| 4 | `plane claim import-dbf <scratch>/dbf A designs/concept-a-reborn` | 7 to 9 s | OK: `claims_yaml: designs/concept-a-reborn/claims.yaml`, 495 nodes, 200 parameters, 112 claims. NOTE `<out>` is a FOLDER, not a file (passing `.../claims.yaml` made a folder named claims.yaml). |
| 5 | `plane claim check designs/concept-a-reborn` | 8 s | exit 1. 43 PASS recomputed, 49 PASS read from source. FAIL: mass (1.881 kg vs 1.47), cuts-required, vib (IN-BAND, FC, GM, GM-SHIFT), horn/elevon torsion, freeplay, and the 3 cost claims (B4). SKIP: stall_pred (no calc registered), 4 proposed. |
| 6 | `plane design validate designs/concept-a-reborn --tier all` | 63 to 74 s | exit 1, Accepted: no. 45 FAIL, 84 SKIP, 182 WARN, 752 PASS. Breakdown below. |
| 7 | `plane baseline check designs/concept-a-reborn` (no baseline yet) | 85 s | exit 1: `Missing baseline.json`, 127 known results all counted as regressions. Expected. |
| 8 | `plane baseline update designs/concept-a-reborn` | 108 s | OK: wrote baseline.json (127 known: FAIL 45, SKIP 82). |
| 9 | `plane baseline check designs/concept-a-reborn` | 124 s | exit 0: `Result: pass`, unchanged 127, regressions 0. |
| 10 | `plane ledger import-dbf <scratch>/dbf <scratch copy of ledger/items.yaml>` | 7 s | exit 0 but imported NOTHING: `changelog 0, decisions_md 0, skipped 187, duplicates 4` (B5). No duplicate of D-209..D-211 (skipped as present). |
| 11 | `pytest -q -n 0 -m "" tests/test_baseline.py tests/test_pdl.py tests/test_yamlfast.py tests/test_cad_overlay_guard.py tests/test_separation.py` with designs/concept-a-reborn present | 20 min 38 s | 155 passed. The new design does not break the design-enumerating tests (CI shards run the whole suite; not run here). |
| 12 | `plane gate explain T3.mass --design designs/concept-a-reborn` | 80 s | prints one line (`T3.aero (tier 3, blocking): requirements.mtow_g`). |
| 13 | `plane design diff designs/concept-a designs/concept-a-reborn` | 4 s | OK, long list of changed keys. |
| 14 | `plane ledger check` | 5 s | exit 0 (unchanged ledger). |
| 15 | `git add designs/concept-a-reborn` + commit in the worktree (never pushed), `python harness/ci/check_separation.py --base HEAD~1 --labels ""` | under 1 min | 133 files, 129 STL stored as LFS (`git lfs ls-files -I`), separation check exit 0. Git warns CRLF will be replaced by LF in plane.yaml and import-report.json (harmless, `.gitattributes` normalises). |

Validate (step 6) by tier, failing rows only:
- T1 geometry: `connection_known` for CT-A-M3-CSK-MOTOR and CT-A-M3-BOLT-MOUNT (B3); 8 `attachment_contact` / `attachment_location` / `articulation` rows (E-WNG-91 17.0 mm, E-WNG-10 6.8 mm, E-WNG-11, E-PWR-04, E-MEC-01/07, E-HRN-21); `point_mass_location` hrn-001 54 g is 3.3 % of 1641 g (limit 3 %).
- T2 physics: 3 `joint_load` (E-AVN-01, E-MEC-01/07) and 10 `sim_drop_loads` (E-FIN-05 and E-FIN-20 about 43 N against ratings under 2 N, E-WNG-83L/R, E-AVN-01, E-MEC-01/07 and others).
- T3 aero: mass 1641 g vs MTOW 1470 g; stall 22.3 m/s (CLmax 0.75) vs 13.85 required; `planform_matches_geometry`: declared 220 500 mm2, measured 71 618 mm2 (-67.5 %); static margin 116 % MAC. The last three need an expert look (B7).
- T9 claims: 14 FAIL as in step 5.
- Interference: 0 FAIL (the hull-wing run had 35, all artefacts).
- Fidelity line: 118 of 811 blocking checks use sourced thresholds; 0 components have measured mass.

## Failures, causes, and who fixes them (builder tasks for the conductor; core/ and standards/ are not Dillon's)

- B1 [hard, core]: `core/hangar/importers/dbf.py` (`_write_stl` / `_canonical`, `import_concept` round-trip check) and `dbf_geometry.py` (`_separate_pinches`). The rebuilt solid of PRP-001-LL (motor X2216) and WNG-001 (wing, 117 cuts) is watertight in memory but not after the float32 STL write and reload: after `_canonical`, 2 vertex pairs (wing) and 1 pair plus 2 zero-area faces (motor) sit at the same position, so the STL loader welds them and leaves 5 to 14 broken faces. Then the GLB fallback also fails. Stand-in that worked: after the float32 cast, move one vertex of each coincident pair 6e-4 mm along its face-neighbour direction (the same idea as `_separate_pinches`, which misses these pairs). Pass check: `plane import dbf` on the v1 extract reaches the end; every `meshes/*.stl` reloads with `is_watertight and is_volume`.
- B2 [hard, core]: `dbf_geometry.part_mesh`, PRP-006-LL/LR/UL/UR (new X-mount: 13 bodies, 4 countersink cuts). The union is closed, but `_clean(...)` after it (and the sequential cuts) re-opens it: `not watertight after union/cuts (bodies=13, cuts=4)`. Stand-in: the plain union without `_clean` and without the 4 cuts (loses the countersinks). Pass check: the 4 parts rebuild with their cuts and reload watertight.
- B3 [easy, core + standards]: v1 uses two connection types the importer and the standards do not know: `CT-A-M3-CSK-MOTOR` (4 x M3 countersunk, motor to X-mount) and `CT-A-M3-BOLT-MOUNT` (4 x M3x14 SHCS plus nyloc, X-mount to motor cup plate). Fix: add both to `CONN_METHOD` in `importers/dbf.py` (method bolted, as the other CT-A fasteners) and to `standards/connection-types.yaml` (source: v1 `redesign/interfaces/connection_types.json`). Without the second, validate fails `T1.interfaces.connection_known`.
- B4 [easy, core]: `core/hangar/calcs/concept_a.py:206 bom_cost(rows, tax, faa, ship, bump, tubes, budget)` has no `rship` input, but v1's `CALC-A-COST` passes `rship: P:cost.reserve_ship_usd`. The 3 cost claims (CL-A-COST-TOTAL, -MARGIN30, -BUDGET) FAIL with `TypeError ... unexpected keyword argument 'rship'`. Fix: accept `rship` (v1 `redesign/qp/A/cad/amodel/bom_a.py` has the formula), and check `tests/fixtures/concept-a-calcs/golden.json` still passes.
- B5 [hard, core]: `core/hangar/importers/changelog.py` `import_decisions` reads only rows whose first cell is a bare id (`^D-\d+[a-z]*$`). In v1 the rows D-212 to D-261 carry the title inside the first cell (`| **D-213 landing side-load limit ... (T-064, ...)** | ... |`), so all 50 are silently skipped and the command reports success with 0 imported. Four D-212 rows (first version, rev 2, rev 3, rev 3 minors) share one number, and a row about T-096 F-5 has no D-number (it belongs to D-246). Fix: take the id from the start of the first cell; give the D-212 rows distinct ids (for example D-212, D-212r2, D-212r3, D-212r3m); attach the unnumbered row to the previous decision or skip it with a message. Pass check: against a copy of `ledger/items.yaml` the command adds the ids D-212 to D-261 (about 53 rows) and nothing that already exists.
- B6 [easy, core, minor]: the extract has no `.git`, so `import-report.json` records `"commit": ""` and the plane.yaml comments say `rebuilt from DBF-Combined  ...` with an empty commit. A `--commit d83b26f` option (or reading a `COMMIT` file) would fix it; until then PROVENANCE rows must state d83b26f by hand. Ledger evidence strings from `ledger import-dbf` would read `@ unknown` for the same reason (the importer calls `git rev-parse` on the extract).
- B7 [question for the advisor and Dillon, no builder task yet]: v1 wing core WNG-001 rebuilds to 0.32e6 mm3 (2.59e6 in the old concept-a), measured planform 71 618 mm2 against the declared 220 500, static margin 116 percent. Either the declared planform in the importer (`amodel/common.py` C, B) no longer describes v1's wing, or the v1 core is modelled differently (D-226 skin WNG-011, cove strip WNG-012). Dillon decides whether to declare it or to fix the planform; it cannot be settled by the importer.

Not a failure but worth knowing: a `plane import dbf` run takes about 13 minutes on this machine; the progress lines go to stderr; the final line is the plane.yaml path.

## Mistake in the dry run, disclosed

One re-run (3e) was started with `PYTHONPATH` entries separated by `:`, which Python on Windows does not split, so it imported the editable install of the MAIN checkout and wrote its output into `C:/Users/trist/dbf-hangar/designs/concept-a-reborn` (untracked, the main checkout was otherwise untouched; the importer code is identical between e5fcec3 and main HEAD 3676609, only `core/hangar/geom/*` differs). The folder was moved into the dry-run worktree and the main checkout was left clean (`git status` empty). Nothing was committed or pushed from it.
