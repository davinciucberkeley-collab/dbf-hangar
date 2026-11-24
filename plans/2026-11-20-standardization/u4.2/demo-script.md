# Dec 2 live demo script (U4.2 Step 2), 8 minutes, re-run 2026-11-23 (W14-T; first dry run 2026-11-22, W4-TE)

Re-run 2026-11-23 on a scratch `git clone` of origin/main at 39c7c58, never on `designs/`. Steps 2-5 and the Studio API of step 6 were run; step 9 was read from code and the three URLs were fetched (publish was not run this time). Wall times are from that machine (each plane call pays 3-5 s Python start-up). Changes since the 11-22 dry run (69d050f): step 2 and 3 are faster (2.6 s, 2.8 s), validate is faster (6.7 s), `design new` now rejects ids outside `^[a-z0-9][a-z0-9_-]*$` (T90, exit 2), the yaw row of `T3.control_authority` is a WARN that says `not judged` (T37), cold Studio start is slower (278 s, was 149 s); validate counts (62 PASS, 7 WARN, 1 FAIL), the static-margin numbers (15.5%, 15.0%, 14.5%) and the sweep numbers (+-19.95 deg) are unchanged; no new SKIPs for demo-wing.

Run plane with: `export PYTHONPATH=<repo>/core; C:/ProgramData/miniforge3/python.exe -m hangar.cli ...`. Below it is shortened to `plane ...` (needs the `plane` entry point on PATH; see Issue 6).

## Before the room (T-15 min)
1. `plane studio --no-browser --port 8765` in the repo root (not in the 8-minute budget). The real repo has a warm `.studio/cache.json`. A cold start (fresh clone, no cache) took 278 s on 11-23 before concept-a had its model and mechanisms (was 149 s on 11-22, quote 278 s; port answers after 11 s, concept-a is the fifth of seven queued checks, tiltwing-cakir last); never start cold in the room. While the checks run, API calls are slow.
2. Open `http://127.0.0.1:8765/#m=physics&d=concept-a` once so the page and three.js are loaded. three.js loads from cdn.jsdelivr.net (`viewer/README.md`), so the room needs internet. Fallback is the recorded video.
3. Have `designs/demo-wing` absent: `ls designs` must not list it.

## Steps (one command or click each)
| # | Min | Do | Expected (trimmed) | Wall | If it fails live |
|---|---|---|---|---|---|
| 1 | 0:00-0:45 | Say: "15 interfaces, rules forgotten, code edits per design; now one CLI and one app." | none | 0:45 | n/a |
| 2 | 0:45-1:30 | `plane design new demo-wing` | prints `...\designs\demo-wing\plane.yaml`, exit 0; folder has only `plane.yaml`. Template is `example-tailsitter-wing` (default; `--template` to change). An id like `Bad_ID` exits 2 (`plane: invalid id 'Bad_ID': must match ^[a-z0-9][a-z0-9_-]*$`), so type `demo-wing` exactly | 2.6 s | `cp -r designs/example-tailsitter-wing designs/demo-wing` and edit `id:`; or recorded video |
| 3 | 1:30-2:15 | `plane design set designs/demo-wing "components[wing].mass_g" --value 150 --why "demo: lighter wing foam"` | `components[wing].mass_g: 180 -> 150`, exit 0; `designs/demo-wing/CHANGELOG.yaml` gains one entry (old 180, new 150, kind modify) | 2.8 s | `plane design get designs/demo-wing --key "components[wing].mass_g"`, then edit by hand (say so) |
| 4 | 2:15-3:15 | `plane design validate designs/demo-wing` | scorecard table, `**Accepted:** no`, exit 1; 62 PASS, 7 WARN, 0 SKIP, 1 FAIL: `T3.static_margin FAIL: 15.5% MAC (NP x=194 mm, CG x=163 mm; target 5%-15%; ...)`; the 7 WARNs are report-only until 2026-12-08 (`T2.joint_rf`, `T3.control_authority` pitch and yaw, `T3.transition_margin`, `T3.endurance`, `T7.electrical_rating`, `T8.program.budget`); the yaw row says `not judged` (T37); last line `Fidelity: 5 of 61 blocking checks use sourced thresholds; 0 components have measured mass.` | 6.7 s | `plane design validate designs/demo-wing --tier 1` (3.3 s, 0 of 17 blocking checks sourced) or recorded video |
| 5 | 3:15-3:45 | Fix it live: `plane design set designs/demo-wing "components[wing].mass_g" --value 170 --why "demo: back inside the static-margin band"`, then `plane design validate designs/demo-wing` | `150 -> 170`; validate `**Accepted:** yes`, exit 0, `T3.static_margin PASS: 14.5% MAC` (CG x=165 mm; 160 g still FAILs at 15.0%, measured 7.7 s) | 5.2 s + 5.4 s | skip; the story works with step 4 alone |
| 6 | 3:45-5:15 | Studio Physics (click path below): design `concept-a`, mechanism `elevon-r`, then `elevon-l`, press Play | slider runs 0 to 30 (31 steps), input -15 to +15 deg; follower `E-WNG-10` reads -19.95 deg at +15 (ratio -1.33); `elevon-l` gives +19.95 for `E-WNG-11` (re-checked 11-23 through the Studio API: both sweeps, 31 steps, -15 to +15, E-WNG-10 +19.95 at -15 and -19.95 at +15, E-WNG-11 the reverse; GLB 2.3 MB, HTTP 200) | 1.5 min | drag the slider by hand; else recorded video |
| 7 | 5:15-6:15 | Decided (D46): no live propose. Open PR #3 (merged e2504d2, concept-a elevons) and say "this is what `plane design propose` makes" | PR page, designs/ only | 0:30 | `plane design propose --help` |
| 8 | 6:15-6:45 | Click the PR link: files changed (designs/ only, no core/) and CI | GitHub PR page | 0:30 | show PR #3 |
| 9 | 6:45-7:30 | `plane update publish 2026-11-30` (D46: the 11-30 week; its `updates/` entry must be merged to main first, else the URL is HTTP 404, Issue 4) | prints only `https://davinciucberkeley-collab.github.io/dbf-hangar/updates/2026-11-30/` (`core/hangar/ops/update.py:97-116`: writes `viewer/updates/<week>/index.html` and the index, gitignored, then returns the URL), exit 0. Without `plane update new 2026-11-30` first it exits 2 with `run plane update new first`; with no entries, `no entries to publish`. URL today: HTTP 404 (not yet on main) | 3.0 s (11-22) | open the URL directly after merge; fallback: week 2026-11-16 (HTTP 200 checked 2026-11-23) |
| 10 | 7:30-8:00 | Open the one link `https://davinciucberkeley-collab.github.io/dbf-hangar/` | HTTP 200 (checked 2026-11-23); same app, read-only | 0:30 | recorded video |

Step 9 uses the 11-30 week (D46). Dry run used the existing week 2026-11-16; a new week (`update new`, `update add`, `update publish`) works (4.7 s, then 3 s) but its URL returns 404 until the `updates/` file is merged to main and the Pages workflow has run (Issue 4).

## Studio click path and launch
- Launch: `plane studio` (default port 8765, opens the browser; `--no-browser` and `--port N` exist). The Studio index has `"studio": true`, which adds the edit panel.
- Click path: sidebar list: click `concept-a` (filter box "Filter by name, id, tag"); top tabs: click `Physics`; dropdown `Mechanism`: pick `elevon-r`; click `Play` (the button turns `Pause`; 60 ms per step); pick `elevon-l`; `Play`.
- Deep link: `http://127.0.0.1:8765/#m=physics&d=concept-a`.
- The example template and `demo-wing` have no `mechanisms` block, so Physics shows "This design has no mechanisms." for them: switch the sidebar to `concept-a` first (tiltwing-cakir also has mechanisms).
- The plan text says "flap mechanism"; concept-a has the elevon pair (PR #3, merged e2504d2): `elevon-r` driver E-MEC-02 driven E-WNG-10, `elevon-l` driver E-MEC-07 driven E-WNG-11, range -15..15 deg (`designs/concept-a/plane.yaml:3115-3127`). The sweep data (31 steps each) was read from a live Studio on the clone on 11-22 and again on 11-23: viewer path is `GET /data/index.json` (concept-a entry `mechanisms` = `concept-a-dd56ba4c68e1.mechanisms.json`), then `GET /data/<that file>` (`viewer/modes/physics.js:18`). The click path itself was NOT run in a browser here (Issue 7).

## Issues: things that do not work today or need a decision (these become fixes, not workarounds)
1. Fixed in 852b114 (the plan's agent tables were repaired; `plans/2026-11-20-standardization.md` at 69d050f had the W4-TE row spliced between lines). Nothing to revert; no action.
2. Step 4: a 150 g wing FAILs `T3.static_margin` (15.5% > 15%) and exits 1. Not a bug; it is the demo story, but a `&&` chain stops there.
3. Decided by D46: no live propose; show PR #3 (merged e2504d2) at step 7. For the record, `plane design propose` on the real repo would open a real PR on `davinciucberkeley-collab/dbf-hangar` (`GH_REPO` is hard-coded at `core/hangar/ops/edit.py:22`; gh is logged in); the 11-22 dry run used a scratch bare remote and a `HANGAR_GH` stub, so the real gh call was never made. Nothing open.
4. Steps 9/10: for a week not yet on main, `update publish` prints a Pages URL that is HTTP 404 (verified for 2026-12-07), because `viewer/updates/` is gitignored and Pages builds it from main (`.github/workflows/pages.yml`).
5. Fixed in 541222a (the stale D3 text in `plane tools doctor` was removed). `opencae missing` and `aerosandbox missing` remain by design; doctor is still not part of the demo.
6. With this miniforge Python the `plane` entry point is not on PATH: `tests/test_team_tasks.py` gives 12 failed (`plane: command not found`); with a `plane` shim on PATH, `tests/test_team_tasks.py` and `tests/test_surfaces_in_sync.py` give 29 passed (160 s). Same PATH cause as the known `tests/test_seed.py:9` failure (whole-branch line 6). Check `plane` resolves on the demo laptop.
7. Playwright is not installed in any local Python, so the Physics click path was not exercised in a browser (still true 11-23). CI covers it with `tests/test_viewer_static.py::test_physics_mode_plays_mechanism_sweep` (fixture `mech-good`, not concept-a). Run it on the demo laptop in the Mon 11-30 dry run (Step 4).
8. Fixed in 5133fdc (B4): `plane design validate --tier N` now runs tiers 0..N and `all` runs 0-9, matching `--help` and README. No special wording needed on stage.
9. (11-23) Step 9: on 2026-11-30 the URL is HTTP 404 today and stays so until the `updates/` entry is on main and the Pages workflow has run; `update publish` itself still prints the URL and exits 0 once `update new` and `update add` were done, so it looks like success on stage. Merge the week's entry before the demo (the week-of-11-30 entry does not exist on main yet).
10. (11-23) Step 6: a cold Studio needs 278 s before concept-a's mechanisms exist. If Studio is restarted or `designs/` changes under it, the cache is invalidated for the changed design and its Physics tab shows no mechanisms until its check finishes. Start Studio before the room and do not touch `designs/` while it runs (step 2 adds `designs/demo-wing`; it only queues one new check).
11. (11-23) Items 6 and 7 were not re-checked in this run; read them as of 11-22. Step 7 (`design propose`) and `tools doctor` were not re-run.

## Timing summary (measured, scratch clone)
11-23: new 2.6 s, set 2.8-5.2 s, validate 5.4-6.7 s (7.7 s at 160 g, 3.3 s at `--tier 1`). 11-22 (not re-measured): propose 10.1 s, publish 3.0 s. About 25 s of command waiting; the rest is narration.
Concept-a full validate (not in the live script, too slow): 83 s wall (earlier tree), exit 1; current main, all result rows: PASS 693, WARN 146, FAIL 10, SKIP 73.

## Recorded backup video (decision for Tristan)
Not recorded. Decided (D46): Tristan records it at the 11-30 dry run (one take of steps 2-10, target 6 min, saved outside the repo).

## Cleanup after the demo
No live propose (D46), so no demo branch or PR to close. `git switch main` if one was tried; remove `designs/demo-wing`.
