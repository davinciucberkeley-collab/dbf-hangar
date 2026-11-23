# Dec 2 live demo script (U4.2 Step 2), 8 minutes, dry-run 2026-11-22 (W4-TE)

Every command below was run on a scratch `git clone` of main at 69d050f, never on `designs/`. Wall times are from that machine (each plane call pays 3-5 s Python start-up).

Run plane with: `export PYTHONPATH=<repo>/core; C:/ProgramData/miniforge3/python.exe -m hangar.cli ...`. Below it is shortened to `plane ...` (needs the `plane` entry point on PATH; see Issue 6).

## Before the room (T-15 min)
1. `plane studio --no-browser --port 8765` in the repo root (not in the 8-minute budget). The real repo has a warm `.studio/cache.json`. A cold start (fresh clone, no cache) took 149 s before concept-a had its model and mechanisms (c0-* designs at about 70 s); never start cold in the room.
2. Open `http://127.0.0.1:8765/#m=physics&d=concept-a` once so the page and three.js are loaded. three.js loads from cdn.jsdelivr.net (`viewer/README.md`), so the room needs internet. Fallback is the recorded video.
3. Have `designs/demo-wing` absent: `ls designs` must not list it.

## Steps (one command or click each)
| # | Min | Do | Expected (trimmed) | Wall | If it fails live |
|---|---|---|---|---|---|
| 1 | 0:00-0:45 | Say: "15 interfaces, rules forgotten, code edits per design; now one CLI and one app." | none | 0:45 | n/a |
| 2 | 0:45-1:30 | `plane design new demo-wing` | prints `...\designs\demo-wing\plane.yaml`, exit 0; folder has only `plane.yaml`. Template is `example-tailsitter-wing` (default; `--template` to change) | 8.9 s | `cp -r designs/example-tailsitter-wing designs/demo-wing` and edit `id:`; or recorded video |
| 3 | 1:30-2:15 | `plane design set designs/demo-wing "components[wing].mass_g" --value 150 --why "demo: lighter wing foam"` | `components[wing].mass_g: 180 -> 150`, exit 0; `designs/demo-wing/CHANGELOG.yaml` gains one entry (old 180, new 150, kind modify) | 5.7 s | `plane design get designs/demo-wing --key "components[wing].mass_g"`, then edit by hand (say so) |
| 4 | 2:15-3:15 | `plane design validate designs/demo-wing` | scorecard table, `**Accepted:** no`, exit 1; 62 PASS, 7 WARN, 1 FAIL: `T3.static_margin FAIL: 15.5% MAC (... target 5%-15%)`; last line `Fidelity: 5 of 61 blocking checks use sourced thresholds; 0 components have measured mass.` | 9.4 s | `plane design validate designs/demo-wing --tier 1` (a few seconds) or recorded video |
| 5 | 3:15-3:45 | Fix it live: `plane design set designs/demo-wing "components[wing].mass_g" --value 170 --why "demo: back inside the static-margin band"`, then `plane design validate designs/demo-wing` | `150 -> 170`; validate `**Accepted:** yes`, exit 0, `T3.static_margin PASS: 14.5% MAC` (160 g still FAILs at 15.0%) | 5.7 s + 9.4 s | skip; the story works with step 4 alone |
| 6 | 3:45-5:15 | Studio Physics (click path below): design `concept-a`, mechanism `elevon-r`, then `elevon-l`, press Play | slider runs 0 to 30 (31 steps), input -15 to +15 deg; follower `E-WNG-10` reads -19.95 deg at +15 (ratio -1.33); `elevon-l` gives +19.95 for `E-WNG-11` | 1.5 min | drag the slider by hand; else recorded video |
| 7 | 5:15-6:15 | Decided (D46): no live propose. Open PR #3 (merged e2504d2, concept-a elevons) and say "this is what `plane design propose` makes" | PR page, designs/ only | 0:30 | `plane design propose --help` |
| 8 | 6:15-6:45 | Click the PR link: files changed (designs/ only, no core/) and CI | GitHub PR page | 0:30 | show PR #3 |
| 9 | 6:45-7:30 | `plane update publish 2026-11-30` (D46: the 11-30 week; its `updates/` entry must be merged to main first, else the URL is HTTP 404, Issue 4) | prints `https://davinciucberkeley-collab.github.io/dbf-hangar/updates/2026-11-30/`, exit 0 | 3.0 s | open the URL directly after merge; fallback: week 2026-11-16 (HTTP 200 checked 2026-11-22) |
| 10 | 7:30-8:00 | Open the one link `https://davinciucberkeley-collab.github.io/dbf-hangar/` | HTTP 200 (checked 2026-11-22); same app, read-only | 0:30 | recorded video |

Step 9 uses the 11-30 week (D46). Dry run used the existing week 2026-11-16; a new week (`update new`, `update add`, `update publish`) works (4.7 s, then 3 s) but its URL returns 404 until the `updates/` file is merged to main and the Pages workflow has run (Issue 4).

## Studio click path and launch
- Launch: `plane studio` (default port 8765, opens the browser; `--no-browser` and `--port N` exist). The Studio index has `"studio": true`, which adds the edit panel.
- Click path: sidebar list: click `concept-a` (filter box "Filter by name, id, tag"); top tabs: click `Physics`; dropdown `Mechanism`: pick `elevon-r`; click `Play` (the button turns `Pause`; 60 ms per step); pick `elevon-l`; `Play`.
- Deep link: `http://127.0.0.1:8765/#m=physics&d=concept-a`.
- The example template and `demo-wing` have no `mechanisms` block, so Physics shows "This design has no mechanisms." for them: switch the sidebar to `concept-a` first (tiltwing-cakir also has mechanisms).
- The plan text says "flap mechanism"; concept-a has the elevon pair (PR #3, merged e2504d2): `elevon-r` driver E-MEC-02 driven E-WNG-10, `elevon-l` driver E-MEC-07 driven E-WNG-11, range -15..15 deg (`designs/concept-a/plane.yaml:1597-1609`). The sweep data (31 steps each) was read from a live Studio on the clone. The click path itself was NOT run in a browser here (Issue 7).

## Issues: things that do not work today or need a decision (these become fixes, not workarounds)
1. `plans/2026-11-20-standardization.md` (commit 69d050f) has 1216 copies of the W4-TE agent-table row spliced between lines of the file (for example lines 340-352 and 2360-2418). Every table in the plan is corrupted. The conductor should revert the plan to the previous version plus one W4-TE row. Run `git diff 69d050f~1 69d050f --stat` to see it.
2. Step 4: a 150 g wing FAILs `T3.static_margin` (15.5% > 15%) and exits 1. Not a bug; it is the demo story, but a `&&` chain stops there.
3. Step 7 on the real repo opens a real PR on `davinciucberkeley-collab/dbf-hangar` (`GH_REPO` is hard-coded at `core/hangar/ops/edit.py:22`; gh is logged in). The dry run used a scratch bare remote and `HANGAR_GH` pointing at a stub that prints a fake URL; branch and commit were verified, the real gh call was not made. Tristan decides: live PR (close it afterwards) or show PR #3.
4. Steps 9/10: for a week not yet on main, `update publish` prints a Pages URL that is HTTP 404 (verified for 2026-12-07), because `viewer/updates/` is gitignored and Pages builds it from main (`.github/workflows/pages.yml`).
5. `plane tools doctor` in the clone: `opencae missing`, `aerosandbox missing`, `davinci missing: D3 open: no API access configured`. The D3 text is stale (D3 is decided; whole-branch non-blocking 5). Do not run doctor on stage.
6. With this miniforge Python the `plane` entry point is not on PATH: `tests/test_team_tasks.py` gives 12 failed (`plane: command not found`); with a `plane` shim on PATH, `tests/test_team_tasks.py` and `tests/test_surfaces_in_sync.py` give 29 passed (160 s). Same PATH cause as the known `tests/test_seed.py:9` failure (whole-branch line 6). Check `plane` resolves on the demo laptop.
7. Playwright is not installed in any local Python, so the Physics click path was not exercised in a browser. CI covers it with `tests/test_viewer_static.py::test_physics_mode_plays_mechanism_sweep` (fixture `mech-good`, not concept-a). Run it on the demo laptop in the Mon 11-30 dry run (Step 4).
8. Whole-branch item B4: `plane design validate` default `--tier 5` also runs tiers 7 and 8 (output shows `7 integration`, `8 sourcing`), while `--help` and README say tiers 0-5. Say "default tiers" on stage.

## Timing summary (measured, scratch clone)
new 8.9 s, set 5.7 s, validate 9.4 s (11.7 s on a second copy), propose 10.1 s, publish 3.0 s. About 40 s of command waiting; the rest is narration.
Concept-a full validate (not in the live script, too slow): 83 s wall, exit 1, PASS 531, WARN 9, FAIL 4, SKIP 102.

## Recorded backup video (decision for Tristan)
Not recorded. Decided (D46): Tristan records it at the 11-30 dry run (one take of steps 2-10, target 6 min, saved outside the repo).

## Cleanup after the demo
No live propose (D46), so no demo branch or PR to close. `git switch main` if one was tried; remove `designs/demo-wing`.
