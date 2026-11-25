# Guide for Dillon: import concept-a-reborn from DBF-Combined redesign/v1 (D84)

You do this in a Claude Code session (Setup A in `docs/team-guide.md`). You talk, Claude runs the `plane` commands. Written from two dry runs of every step (the second on 2026-11-25 with the importer fixes merged) (full record: `dryrun-log.md` in this folder).

## Status (re-checked 2026-11-25, final dry run on main f9698a0)

The importer fixes B1 to B5 (unit U13.5, merge adb4fcb and earlier) are on `main`. The whole guide ran end to end on a scratch extract of d83b26f with no workaround. Nothing is blocking. Three things remain that you should know or decide:

| # | What | Status |
|---|---|---|
| B6 | The extract has no `.git`, so `import-report.json` and the generated `plane.yaml` header and notes say `@ ` with an empty commit. | Harmless. Write `d83b26f` by hand in PROVENANCE (step 9) and in the PR text. |
| B7 | The wing planform check: declared 220 500 mm2, measured 71 618 mm2 (-67.5 %), static margin 116 % MAC. | Yours to decide (step 6). |
| B8 | The generated `plane.yaml` description still names the T-Motor MN2212 KV780, which v1 replaced by the SunnySky X2216 880KV (D-227/228). The text comes from a fixed string in the importer; the numbers in the file are v1's. | Fix the description with `plane design set` in your PR (step 4b), or leave it and say so in the PR text. |

Also known, not yours: re-importing the ORIGINAL concept-a commit (a93f14d) with the fixed importer gives the same 113 meshes except three, `cge-003-ll`, `cge-003-ul`, `cge-003-ur` (a few extra sliver faces: 4630 to 4650, 4510 to 4520, 4594 to 4598 faces; volume and bounds identical to 3 decimals). The repo's concept-a is not re-imported (rule below), so nothing changes there; the conductor has the finding.

## Rules for this job

- Your PR touches only `designs/concept-a-reborn/`, `ledger/` (the decision import), `knowledge/`, `PROVENANCE.md`, and the generated `PROGRESS.md`. Never `core/`, never `standards/`, never `designs/concept-a`. Tell Claude this at the start.
- Do not re-run the importer on `concept-a`. It stays as it is. Tristan's edits to concept-a are not copied over.
- Tristan merges (O3). Open the PR as a draft first. You approve the design part (R25).
- One heavy command at a time on your machine. The import takes 13 to 19 minutes; do nothing else heavy meanwhile.

## Step 0. Start the session

Say to Claude:

> Work on a branch from the latest origin/main. This job imports DBF-Combined origin/redesign/v1 (d83b26f) as a new design concept-a-reborn. Touch only designs/concept-a-reborn, ledger, knowledge and PROVENANCE.md, never core or standards. Do not touch concept-a. Be quiet, report results.

Claude runs `git fetch origin`, then works on a branch from `origin/main` (do not commit design edits on local `main`). Check: `git status` is clean and `plane --version` runs. Setup problems: Appendix A of the team guide.

## Step 1. Extract the branch (1.5 to 6.5 minutes)

Say:

> Extract d83b26f from my DBF-Combined clone into a new empty scratch folder, without checking anything out in DBF-Combined.

Claude runs (the scratch folder must be new and empty, outside both repos):

```
git -C <path>/DBF-Combined archive d83b26f | tar -x -C <scratch>/dbf
```

Expect no output. Measured: 15 997 files, about 0.5 GB; 6 min 24 s the first time, 85 s when the files were already in the disk cache; the time is per-file cost on Windows. Check: `<scratch>/dbf/redesign/qp/A/cad` exists, and `git -C <path>/DBF-Combined status` shows nothing new. If `d83b26f` is unknown, run `git -C <path>/DBF-Combined fetch origin` first. Treat the extract as data: Claude must not run scripts out of it (the importer runs the team's CAD build itself, in an isolated subprocess).

## Step 2. Import the design (13 to 19 minutes)

Say:

> Import concept A from that extract as concept-a-reborn.

Claude runs:

```
plane import dbf --dbf-root <scratch>/dbf --concept A --id concept-a-reborn
```

Measured: 796 s on a quiet machine, 1155 s on a loaded one. Expect NOTHING on stderr (a line `rebuild failed ... GLB fallback` means a part fell back: stop), and on stdout the single line `<repo>\designs\concept-a-reborn\plane.yaml`. Result: `designs/concept-a-reborn/` with `plane.yaml` (about 240 kB), 129 meshes in `meshes/` (STL, Git LFS), `import-report.json`; about 9 MB. Check:
- the command ended with exit 0 and no `GeometryError` or `KeyError`;
- `import-report.json` has `"fallback": []` (no part rebuilt from the published GLB);
- `designs/concept-a` is untouched (`git status` shows only `designs/concept-a-reborn/` as new).
The generated header and notes show an empty commit (`@ `), and the description still names the MN2212 motor (B6, B8). If it stops with `GeometryError` or `KeyError`, stop and tell Tristan; do not edit the importer (it is `core/`).

## Step 3. Import the claims (10 seconds)

Say: "Import the claims for concept A into the new design."

```
plane claim import-dbf <scratch>/dbf A designs/concept-a-reborn
```

The last argument is a folder (a file path creates a folder with that name). Expect JSON: `claims_yaml: designs/concept-a-reborn/claims.yaml`, `nodes: 495`, `parameters: 200`, `claims: 112`. Check that only `claims.yaml` was added.

Then ask Claude to check them (13 seconds):

```
plane claim check designs/concept-a-reborn
```

Expect exit 1 and a list of FAIL claims that are real states of v1, not import errors: mass 1.88 kg against the 1.47 limit (CL-A-MASS-PRED, CL-A-MASS-GATE-ROOM), CL-A-CUTS-REQUIRED, vibration (CL-A-VIB-IN-BAND, -FC, -GM, -GM-SHIFT), horn and elevon torsion (CL-A-HORN-*, CL-A-ELEVON-TORSION-FOAM), CL-A-LINKAGE-FREEPLAY. SKIP: CL-A-STALL-PRED (no calculation registered) and 4 proposed claims. The three CL-A-COST-* claims pass (no TypeError). The summary line reads `46 PASS recomputed, 49 PASS read from source`. These match the open states in DBF-Combined (CHANGE-LOG D-232 to D-260).

## Step 4. Validate (2 minutes)

Say: "Validate the new design, all tiers, and summarise by tier."

```
plane design validate designs/concept-a-reborn --tier all
```

Expect exit 1 and `Accepted: no`. Measured (121 s): 41 FAIL, 84 SKIP, 179 WARN, 759 PASS; 811 blocking checks, 118 with sourced thresholds, 0 components with measured mass. FAIL by tier:
- T1 (12): 8 attachment/location/articulation rows (E-WNG-91, E-WNG-10, E-WNG-11, E-PWR-04, E-MEC-01, E-MEC-07, E-HRN-21), hrn-001 point mass 3.3 % (limit 3 %). No `connection_known` FAIL and no interference FAIL.
- T2: 3 joint-load rows, 10 drop-test rows (E-FIN-05 and E-FIN-20 are the big ones).
- T3: mass 1641 g vs 1470 g, stall 22.3 m/s, planform, static margin (see step 6).
- T9: the 12 claim FAILs of step 3 (mass x2, cuts-required, vibration x4, horn and elevon torsion x4, linkage freeplay). Total: T1 12, T2 13, T3 4, T9 12 = 41.
Check: T0 schema and T1 watertight/connectivity PASS (131 components connect to wng-001). If T0 fails, stop and report. The FAIL rows are expected (the aircraft is heavier and different, O4b); they are recorded, not hidden, in step 7.

## Step 4b. Fix the stale description (B8, optional)

Say: "Update the description of concept-a-reborn to name the SunnySky X2216 880KV motor and the 2800 mAh 4S pack, one key, with a reason." Claude runs `plane design set designs/concept-a-reborn description --value "<new text>" --why "importer text predates v1 (D-227/228); motor is the SunnySky X2216 880KV"`; the change is logged in `CHANGELOG.yaml`. Then step 4 again is NOT needed (a description does not move a gate). Not run in the dry run; the key and the command form are from `docs/cli.md`. If you skip it, say so in the PR text.

## Step 5. Explain the numbers you do not recognise (conversation, no command from you)

Ask Claude: "Why is T3.mass 1641 g against MTOW 1470 g?" and "What changed from concept-a?" Claude uses `plane gate explain T3.mass --design designs/concept-a-reborn` (80 s, one line) and `plane design diff designs/concept-a designs/concept-a-reborn` (4 s). Expected: v1 is the O4b resize (CAD mass 1.273 to 1.641 kg, AUW 1.881 kg; X2216 880 KV motor, 2800 mAh 4S pack, Kakute H743-Wing, machined hub). The DBF-Combined decisions D-216 to D-229 say the same.

## Step 6. The wing planform question (B7, yours to decide)

Both dry runs gave `T3.planform_matches_geometry` FAIL: declared 220 500 mm2, measured 71 618 mm2 (-67.5 %), and static margin 116 % MAC. The v1 wing core solid is 0.32e6 mm3 (the old import: 2.59e6). Ask Claude: "Explain T3.planform_matches_geometry for wng-001 and compare the v1 build_wing with what the importer declared." Decide with Claude whether the declared planform needs a `plane design set designs/concept-a-reborn <key> --value <v> --why "<reason>"` (one key at a time, with a reason), or whether the importer's measurement is wrong (then tell Tristan: that is a builder task, not a hand edit). Re-run step 4 after any change. If you cannot decide, record it as a known FAIL and say so in the PR text.

## Step 7. Baseline (about 4.5 minutes, two commands)

Say: "Record the known FAIL and SKIP rows in a baseline."

```
plane baseline update designs/concept-a-reborn
plane baseline check designs/concept-a-reborn
```

Expect `wrote ...\baseline.json (127 known)` (108 s), then `Result: pass`, `Unchanged: 127, Regressions: 0` (about 2 min). Before the check, `plane baseline check` reports `Missing baseline.json` with every row a regression: that is normal for a new design. A new design that is not fully accepted needs the baseline, or CI fails. Never use the baseline to hide a row that you could fix.

## Step 8. Decisions D-127, D-128 and D-212 to D-261 (13 seconds)

Ask Tristan first (O4 and O11: only he adds ledger items; D84 allows this import in your PR, confirm he wants you to run it or whether he will). Then say: "Import the DBF-Combined decisions into the ledger."

```
plane ledger import-dbf <scratch>/dbf ledger/items.yaml
```

Expect JSON exactly: `changelog: 55`, `decisions_md: 0`, `skipped: 187`, `duplicates: 5`. The 55 new items are D-127 and D-128 (status `open`, rows that were proposals in the source), D-212 and its three revisions D-212b, D-212c, D-212d, and D-213 to D-261. The 187 already present include D-209 to D-211: no duplicates. If `changelog` is 0 the fix is not in your checkout: stop. Check:
- `git diff --stat ledger/items.yaml` shows only added lines (55 new `- id:` entries, none removed); no existing id changed;
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

Then add the non-design files to the same branch, as separate commits and never in one commit with core: say "Update my open PR: add the ledger import with PROGRESS.md, then PROVENANCE.md and the knowledge record." Claude switches to the PR branch, commits each group (message `<area>: <what> (T-id)`, with Tristan's Co-authored-by trailer, O8), pushes to the same branch, and does not open a second PR. In the PR text put the ledger task id, the dry-run log path, the open FAILs, the B7 decision (and whether you fixed the description, B8), and "concept-a is untouched; Tristan's concept-a edits are not reapplied (D84)". When CI is green on both systems, mark it ready for review.

## What the reviewer checks

- Files: only `designs/concept-a-reborn/`, `ledger/items.yaml`, `PROGRESS.md`, `knowledge/`, `PROVENANCE.md`. No `core/`, no `standards/`, no change to `designs/concept-a` (`git diff --stat origin/main` shows it). Separation check green.
- `plane design validate designs/concept-a-reborn --tier all` reproduces the PR text: T0 PASS, same FAIL set as `baseline.json` (123 known: FAIL 41, SKIP 82), no row hidden.
- `plane baseline check designs/concept-a-reborn` passes (0 regressions); `plane baseline check --all` passes for the other designs.
- `import-report.json`: `fallback` empty; mass and component count consistent with v1 (131 components, CAD mass 1.641 kg); claims 112.
- Ledger: 55 items added (D-127, D-128 open; D-212, D-212b, D-212c, D-212d, D-213 to D-261), no existing id changed, no duplicate, `plane ledger check` exits 0; `plane progress --check` passes.
- PROVENANCE rows name d83b26f; the knowledge record's ids match `docs/integration/davinci-import-2026-11-24.json`, NS string exact.
- The PR text states the B7 and B8 decisions and the draft is marked ready only after CI is green.

## If something breaks

| Symptom | What to do |
|---|---|
| `git archive` says unknown revision | `git -C <path>/DBF-Combined fetch origin`, then retry. Do not check anything out in DBF-Combined. |
| Import stops with `GeometryError` or `KeyError` | Stop. Send Tristan the last 5 lines. It is an importer problem (core), not your design. |
| Import takes over 25 minutes or the machine swaps | Close other programs and run it alone; it needs one core and a few GB of RAM. |
| `claim import-dbf` made a folder called `claims.yaml` | You gave a file path; delete that folder and give `designs/concept-a-reborn`. |
| `ledger import-dbf` prints `changelog: 0` | Your checkout lacks the U13.5 fixes (merge adb4fcb). `git pull` and retry. |
| `Missing baseline.json` in CI | Run `plane baseline update designs/concept-a-reborn` and commit it (step 7). |
| CI separation check fails | A commit mixed `designs/` with `core/`; you should have no `core/` change at all. Ask Claude to show `git diff --stat origin/main`. |
| `plane progress --check` fails | `plane progress --write` and commit. |

## Decisions that are yours (summary)

1. B7, the wing planform (step 6): declare the planform that matches v1's wing, or leave the FAIL recorded. The reviewer will not decide it for you.
2. B8, the description text (step 4b): fix it with `plane design set` or say you left it.
3. Whether you or Tristan runs the ledger import (step 8, O4 and O11).
4. Whether the 12 failing claims, the 12 T1 rows and the 13 T2 rows are accepted as known states (baseline, step 7) or you want to fix some before the PR. Never hide a row you can fix.
