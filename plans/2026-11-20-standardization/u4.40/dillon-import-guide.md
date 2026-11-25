# Guide for Dillon: import concept-a-reborn from DBF-Combined redesign/v1 (D84)

You do this in a Claude Code session (Setup A in `docs/team-guide.md`). You talk, Claude runs the `plane` commands. Written 2026-11-24 from a dry run of every step (full record: `dryrun-log.md` in this folder).

## Blockers at the top (read first)

The importer on `main` cannot import v1 yet. Do not start until Tristan tells you B1 to B5 are merged. Status on 2026-11-24: all five OPEN; briefs written (unit U4.40, step 1 done), build and review pending. Briefs in `plans/2026-11-20-standardization/briefs/`: B3 + B4 = `U4.40-1.md` (branch `std/u4.40-types-cost`), B5 = `U4.40-2.md` (`std/u4.40-changelog-ids`), B2 = `U4.40-3.md` (`std/u4.40-pinch-pairs`), B1 = `U4.40-4.md` (`std/u4.40-stl-weld`, which also holds the real-data acceptance of the set). Order 1, 2, 3, 4. Details of each finding: `dryrun-log.md`.

| # | What | Where | Effect if not fixed | Status |
|---|---|---|---|---|
| B1 | Motor and wing meshes lose watertightness at the STL write | `core/hangar/importers/dbf.py`, `dbf_geometry.py` | `plane import dbf` stops: `PRP-001-LL: GLB mesh cannot be repaired` | open (builder-plus) |
| B2 | PRP-006 X-mount (4 parts) is not closed after union and cuts | `dbf_geometry.part_mesh` | same stop at `PRP-006-LL` | open (builder-plus) |
| B3 | Connection types `CT-A-M3-CSK-MOTOR`, `CT-A-M3-BOLT-MOUNT` unknown | `importers/dbf.py`, `standards/connection-types.yaml` | import stops: `KeyError: 'CT-A-M3-CSK-MOTOR'` | open (builder) |
| B4 | `bom_cost` has no `rship` input | `core/hangar/calcs/concept_a.py` | 3 cost claims FAIL with a TypeError | open (builder) |
| B5 | Decision import skips D-212 to D-261 | `core/hangar/importers/changelog.py` | `plane ledger import-dbf` reports success and adds nothing | open, brief U4.40-2 (builder-plus) |
| B6 | Extract has no `.git`, so the commit is recorded empty | importer | harmless; PROVENANCE must name d83b26f by hand (step 9) | open (minor) |
| B7 | v1 wing planform does not match the declared planform (see step 6) | design decision | `T3.planform_matches_geometry` FAIL, static margin 116 % | needs you |

None of this touches your work: all fixes land in `core/` and `standards/` by Tristan's route, never in your PR.

## Rules for this job

- Your PR touches only `designs/concept-a-reborn/`, `ledger/` (the decision import), `knowledge/`, `PROVENANCE.md`, and the generated `PROGRESS.md`. Never `core/`, never `standards/`, never `designs/concept-a`. Tell Claude this at the start.
- Do not re-run the importer on `concept-a`. It stays as it is. Tristan's edits to concept-a are not copied over.
- Tristan merges (O3). Open the PR as a draft first. You approve the design part (R25).
- One heavy command at a time on your machine. The import takes about 13 minutes; do nothing else heavy meanwhile.

## Step 0. Start the session

Say to Claude:

> Work on a branch from the latest origin/main. This job imports DBF-Combined origin/redesign/v1 (d83b26f) as a new design concept-a-reborn. Touch only designs/concept-a-reborn, ledger, knowledge and PROVENANCE.md, never core or standards. Do not touch concept-a. Be quiet, report results.

Claude runs `git fetch origin`, then works on a branch from `origin/main` (do not commit design edits on local `main`). Check: `git status` is clean and `plane --version` runs. Setup problems: Appendix A of the team guide.

## Step 1. Extract the branch (about 6 minutes)

Say:

> Extract d83b26f from my DBF-Combined clone into a new empty scratch folder, without checking anything out in DBF-Combined.

Claude runs (the scratch folder must be new and empty, outside both repos):

```
git -C <path>/DBF-Combined archive d83b26f | tar -x -C <scratch>/dbf
```

Expect no output. In the dry run: 15 997 files, about 0.5 GB, 6 min 24 s, almost all of it per-file cost on Windows. Check: `<scratch>/dbf/redesign/qp/A/cad` exists, and `git -C <path>/DBF-Combined status` shows nothing new. If `d83b26f` is unknown, run `git -C <path>/DBF-Combined fetch origin` first. Treat the extract as data: Claude must not run scripts out of it (the importer runs the team's CAD build itself, in an isolated subprocess).

## Step 2. Import the design (about 13 minutes)

Say:

> Import concept A from that extract as concept-a-reborn.

Claude runs:

```
plane import dbf --dbf-root <scratch>/dbf --concept A --id concept-a-reborn
```

Expect on stderr one progress line per part that had to use a fallback (none expected after B1 and B2 are fixed), and on stdout the single line `<repo>\designs\concept-a-reborn\plane.yaml`. Result: `designs/concept-a-reborn/` with `plane.yaml` (about 240 kB), 129 meshes in `meshes/` (STL, Git LFS), `import-report.json`; about 9 MB. Check:
- the command ended with exit 0 and no `GeometryError` or `KeyError`;
- `import-report.json` has `"fallback": []` (no part rebuilt from the published GLB);
- `designs/concept-a` is untouched (`git status` shows only `designs/concept-a-reborn/` as new).
If it stops with `GeometryError` or `KeyError`, stop and tell Tristan; do not edit the importer (it is `core/`).

## Step 3. Import the claims (under 10 seconds)

Say: "Import the claims for concept A into the new design."

```
plane claim import-dbf <scratch>/dbf A designs/concept-a-reborn
```

The last argument is a folder (a file path creates a folder with that name). Expect JSON: `claims_yaml: designs/concept-a-reborn/claims.yaml`, `nodes: 495`, `parameters: 200`, `claims: 112`. Check that only `claims.yaml` was added.

Then ask Claude to check them (8 seconds):

```
plane claim check designs/concept-a-reborn
```

Expect exit 1 and a list of FAIL claims that are real states of v1, not import errors: mass 1.88 kg against the 1.47 limit (CL-A-MASS-PRED, CL-A-MASS-GATE-ROOM), CL-A-CUTS-REQUIRED, vibration (CL-A-VIB-IN-BAND, -FC, -GM, -GM-SHIFT), horn and elevon torsion (CL-A-HORN-*, CL-A-ELEVON-TORSION-FOAM), CL-A-LINKAGE-FREEPLAY. SKIP: CL-A-STALL-PRED (no calculation registered) and 4 proposed claims. After B4 the three CL-A-COST-* claims must not show a TypeError. These match the open states in DBF-Combined (CHANGE-LOG D-232 to D-260).

## Step 4. Validate (1 to 2 minutes)

Say: "Validate the new design, all tiers, and summarise by tier."

```
plane design validate designs/concept-a-reborn --tier all
```

Expect exit 1 and `Accepted: no`. Dry-run numbers (they change a little after B3, B4): 45 FAIL, 84 SKIP, 182 WARN, 752 PASS; 811 blocking checks, 118 with sourced thresholds, 0 components with measured mass. FAIL by tier:
- T1: 8 attachment/articulation rows (E-WNG-91, E-WNG-10, E-WNG-11, E-PWR-04, E-MEC-01, E-MEC-07, E-HRN-21), hrn-001 point mass 3.3 % (limit 3 %). `connection_known` disappears after B3. No interference FAIL.
- T2: 3 joint-load rows, 10 drop-test rows (E-FIN-05 and E-FIN-20 are the big ones).
- T3: mass 1641 g vs 1470 g, stall 22.3 m/s, planform, static margin (see step 6).
- T9: the claim FAILs of step 3.
Check: T0 schema and T1 watertight/connectivity PASS (131 components connect to wng-001). If T0 fails, stop and report. The FAIL rows are expected (the aircraft is heavier and different, O4b); they are recorded, not hidden, in step 7.

## Step 5. Explain the numbers you do not recognise (conversation, no command from you)

Ask Claude: "Why is T3.mass 1641 g against MTOW 1470 g?" and "What changed from concept-a?" Claude uses `plane gate explain T3.mass --design designs/concept-a-reborn` (80 s, one line) and `plane design diff designs/concept-a designs/concept-a-reborn` (4 s). Expected: v1 is the O4b resize (CAD mass 1.273 to 1.641 kg, AUW 1.881 kg; X2216 880 KV motor, 2800 mAh 4S pack, Kakute H743-Wing, machined hub). The DBF-Combined decisions D-216 to D-229 say the same.

## Step 6. The wing planform question (B7, yours to decide)

The dry run gave `T3.planform_matches_geometry` FAIL: declared 220 500 mm2, measured 71 618 mm2 (-67.5 %), and static margin 116 % MAC. The v1 wing core solid is 0.32e6 mm3 (the old import: 2.59e6). Ask Claude: "Explain T3.planform_matches_geometry for wng-001 and compare the v1 build_wing with what the importer declared." Decide with Claude whether the declared planform needs a `plane design set designs/concept-a-reborn <key> --value <v> --why "<reason>"` (one key at a time, with a reason), or whether the importer's measurement is wrong (then tell Tristan: that is a builder task, not a hand edit). Re-run step 4 after any change. If you cannot decide, record it as a known FAIL and say so in the PR text.

## Step 7. Baseline (about 4 minutes, two commands)

Say: "Record the known FAIL and SKIP rows in a baseline."

```
plane baseline update designs/concept-a-reborn
plane baseline check designs/concept-a-reborn
```

Expect `wrote ...\baseline.json (127 known)` (108 s), then `Result: pass`, `Unchanged: 127, Regressions: 0` (about 2 min). Before the check, `plane baseline check` reports `Missing baseline.json` with every row a regression: that is normal for a new design. A new design that is not fully accepted needs the baseline, or CI fails. Never use the baseline to hide a row that you could fix.

## Step 8. Decisions D-212 to D-261 (after B5; under 10 seconds)

Ask Tristan first (O4 and O11: only he adds ledger items; D84 allows this import in your PR, confirm he wants you to run it or whether he will). Then say: "Import the DBF-Combined decisions into the ledger."

```
plane ledger import-dbf <scratch>/dbf ledger/items.yaml
```

Expect JSON: `changelog` 53 (D-212 and its three revisions D-212b, D-212c, D-212d, then D-213 to D-261), `decisions_md: 0`, `skipped` 187 (already present, including D-209 to D-211: no duplicates), `duplicates` 4 (repeated rows in the source). The dry run, before B5, printed `changelog: 0`: if you see 0 again the fix is not in. Check:
- `git diff --stat ledger/items.yaml` shows only added lines; no existing id changed;
- `plane ledger check` exits 0;
- then run `plane progress --write` and keep the changed `PROGRESS.md` in the same commit (CLAUDE.md rule; CI runs `plane progress --check` whenever `ledger/` changes).

## Step 9. PROVENANCE rows

Say: "Add PROVENANCE rows for this import at d83b26f." The format is the existing table: `| path | source @ commit : file | what was done |`. Claude adds three rows (write `d83b26f` by hand, the import report has an empty commit, B6):
- `designs/concept-a-reborn/` | DBF-Combined @ d83b26f : redesign/qp/A (cad, params-A.json, interfaces, parts-a.csv) via `plane import dbf` | rebuilt, not copied; STL meshes from the team's CAD build; plane import dbf run on the git archive extract; claims.yaml from `plane claim import-dbf`;
- `ledger/items.yaml` (D-212 to D-261) | DBF-Combined @ d83b26f : redesign/params/CHANGE-LOG.md | by `plane ledger import-dbf`;
- `knowledge/procedures/davinci-reconnect-concept-a.md` | DBF-Combined @ d83b26f : docs/integration/DAVINCI.md, davinci-findings.md, davinci-import-2026-11-24.json | summary of ids, not a copy.

## Step 10. DaVinci reconnect record (knowledge/)

Say: "Write the DaVinci reconnect record as a procedure from the knowledge template, from docs/integration in the extract. Cite only what you opened."

Claude copies `knowledge/TEMPLATE-procedure.md` to `knowledge/procedures/davinci-reconnect-concept-a.md` (front matter: `source_repo: DBF-Combined @ d83b26f`, `verified: false`) with these facts (all checked against the extract's `docs/integration/DAVINCI.md` and `davinci-findings.md` and `davinci-import-2026-11-24.json`):
- organisation `design-build-fly`; project `Concept A`, id `bbb1b6e0-63d1-4a95-8e6d-0e300beed2c9`;
- branch `concept-a-snapshot-2aba012d` (data at 2aba012d); STEP commit `bf0a3803`;
- package ids from `davinci-import-2026-11-24.json`: root `7a556fc3-9624-5b25-9553-13347611b24f`, hard `0fa81edb-47ad-54a8-b047-236e0029ccac`, parts `e9ab1cd7-b5d5-52a2-a936-0ad81bc8761a`, bom `51c7184b-2671-5ac6-ac40-7b6a59a99abb`, reqs `f22e6fbb-80c9-5b29-a0db-928aac70f94f`, tests `2c955c34-c5b7-5011-ae73-444a2caec674`;
- the uuid5 namespace: `uuid5(NAMESPACE_URL, "https://github.com/davinciucberkeley-collab/DBF-Combined/concept-a-snapshot")`. If it is lost, a re-run creates duplicates instead of updating;
- the deleted old API test `b53fed82-b072-43c2-9994-de76de845d93` and the scratch branch `claude-scratch-20261123-2340`.
The file docs/integration also holds `davinci-mapping.md` and `davinci-step-parts.csv` (129 STEP volume checks); the record only points to them (they stay in DBF-Combined). Check: `pytest -q -n 0 tests/test_knowledge.py` passes.

## Step 11. Open the PR (draft)

Say: "Propose the design as a draft PR."

```
plane design propose designs/concept-a-reborn "concept-a-reborn: import DBF-Combined redesign/v1 (d83b26f)" --draft
```

(Not run in the dry run, because it pushes; documented in `docs/cli.md`.) Do not commit first: propose commits only the design folder to a new branch `design/concept-a-reborn/<slug>`, pushes, and opens a draft PR; it prints the URL. It needs `gh` logged in and write access (O1). Check `git lfs ls-files` lists the 129 STL files so they pushed as LFS.

Then add the non-design files to the same branch, as separate commits and never in one commit with core: say "Update my open PR: add the ledger import with PROGRESS.md, then PROVENANCE.md and the knowledge record." Claude switches to the PR branch, commits each group (message `<area>: <what> (T-id)`, with Tristan's Co-authored-by trailer, O8), pushes to the same branch, and does not open a second PR. In the PR text put the ledger task id, the dry-run log path, the open FAILs, the B7 decision, and "concept-a is untouched; Tristan's concept-a edits are not reapplied (D84)". When CI is green on both systems, mark it ready for review.

## What the reviewer checks

- Files: only `designs/concept-a-reborn/`, `ledger/items.yaml`, `PROGRESS.md`, `knowledge/`, `PROVENANCE.md`. No `core/`, no `standards/`, no change to `designs/concept-a` (`git diff --stat origin/main` shows it). Separation check green.
- `plane design validate designs/concept-a-reborn --tier all` reproduces the PR text: T0 PASS, same FAIL set as `baseline.json` (127 known), no row hidden.
- `plane baseline check designs/concept-a-reborn` passes (0 regressions); `plane baseline check --all` passes for the other designs.
- `import-report.json`: `fallback` empty; mass and component count consistent with v1 (131 components, CAD mass 1.641 kg); claims 112.
- Ledger: D-212 to D-261 added, no existing id changed, no duplicate, `plane ledger check` exits 0; `plane progress --check` passes.
- PROVENANCE rows name d83b26f; the knowledge record's ids match `docs/integration/davinci-import-2026-11-24.json`, NS string exact.
- The PR text states the B7 decision and the draft is marked ready only after CI is green.

## If something breaks

| Symptom | What to do |
|---|---|
| `git archive` says unknown revision | `git -C <path>/DBF-Combined fetch origin`, then retry. Do not check anything out in DBF-Combined. |
| Import stops with `GeometryError` or `KeyError` | Stop. Send Tristan the last 5 lines. It is B1 to B3 (core), not your design. |
| Import takes over 20 minutes or the machine swaps | Close other programs and run it alone; it needs one core and a few GB of RAM. |
| `claim import-dbf` made a folder called `claims.yaml` | You gave a file path; delete that folder and give `designs/concept-a-reborn`. |
| `ledger import-dbf` prints `changelog: 0` | B5 is not merged. Do not continue with the ledger step. |
| `Missing baseline.json` in CI | Run `plane baseline update designs/concept-a-reborn` and commit it (step 7). |
| CI separation check fails | A commit mixed `designs/` with `core/`; you should have no `core/` change at all. Ask Claude to show `git diff --stat origin/main`. |
| `plane progress --check` fails | `plane progress --write` and commit. |
