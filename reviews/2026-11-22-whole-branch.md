# U4.1 Step 1: whole-branch review (W4-R1, fresh Opus), main @ dea6f2a vs plan §1–§2 and standards/review-scorecard.md

**Summary:** The build holds together. All ticked §7 units have a reviewed merge and CI is green on both OSes at dea6f2a (run 45072187659). 9 of 10 §2.1 metrics pass (M2 partial). Six blocking items, each small.

### Automated checks (reviewer's worktree at dea6f2a)
- `pytest -q -x -n auto`: 663 passed, 2 skipped, 1 failed (`tests/test_seed.py:9`, PATH missing the venv Scripts; 4 passed with it). Full-suite evidence: CI run 45072187659.
- `plane design validate designs/concept-a --tier all`: 113.5 s on a loaded machine; PASS 531, SKIP 102, WARN 9, FAIL 4 (`T2.sim_drop_loads` E-WNG-20/21 2.2/2.1 N vs 1.4 N; `T2.sim_rest` 79° vs 30°; `T3.static_margin` 16.8% MAC). Fidelity 134/635 sourced; 0 measured masses.
- `plane tools doctor` exit 0 (opencae missing in that worktree, aerosandbox missing, blender/sitl planned, davinci missing).
- `plane ledger check` clean; `plane progress --check` up to date; `plane standards pending`: 1 blocking key (`landing_load_factor`, D6).
- Designs/core separation: only seed commit 6909134 touches both.

### Blocking
1. **U4.1 / R33:** R33 is met at afed52a (56.9 s quiet warm, 78.9 s cold) but the ledger says open. Conductor note: R33's unit is U4.1, so by the plan's rule it closes when U4.1 completes; evidence recorded then.
2. **U3.1 / R11:** R11 is `done`, but "drag it around" (interactive frictionless physics) was out of scope (`briefs/U3.1-studio.md:56`) and T6 is analytic (D15). The §6a row-4 cut of Build, BOM, Proofs and Morph modes has no ledger record; Knowledge mode has no decision. 6 of 11 §2.7 modes exist.
3. **U2.5 Step 4:** no record that Dillon's BOM/claims check against the Explorer happened (`briefs/U2.5c-designs.md:36`).
4. **U2.1:** tier docs contradict the CLI. `checks.py:1093` runs T0–T9 whenever `max_tier >= 5` (`--tier 5` returns tiers 0,1,2,3,4,5,7,8); `cli.py:68` "all = 5", `README.md:43` "T0 to T5 by default", `docs/mcp.md:13` "tiers 0-5"; `--tier` offers only 0–5 and all (`ops/design.py:65`).
5. **U0.1:** `.claude/agents/reviewer.md:13` and plan lines 331, 595, 1178 use `plane design validate --all --json`; no `--all` option exists.
6. **U3.4 (+ track C data):** no concept-a review answers the scorecard's Discipline sign-off (`standards/review-scorecard.md:57`) with the six `skills/review-*`.

### Non-blocking
1. Stale ledger evidence: R1 (concept-a is schema 1.0 now), R12 (hrn-bat exists), R17 (probably met by PR #3), R25 (live PRs exist; D24–D26 still ledger-open), R13 (add evidence), R34 (close at U4.1).
2. §2.4 lists `bom list`, `morph list`, `idea list`, `davinci push/pull`, none registered; settle before `docs/cli.md` is generated.
3. Behaviour outside ops: `ops/design.py:108` imports `new_design` from `cli.py:135`; import-dbf `id:` rewrite duplicated in `cli.py:283-285` and `studio.py:184-188`; Studio `_job_fea` bypasses the `fea.run` op; baseline/progress/build-index/import are CLI-only. M2 partial.
4. `docs/mcp.md` lists `fea_run` as hand-written (it is generated); MCP `save_design` writes plane.yaml without a CHANGELOG entry (bypasses R15).
5. davinci adapter message says "D3 open", §3 records D3 decided.
6. `gates/discipline.py:114` silently defaults a missing `ultimate_factor` to 1.0; a SKIP would be safer.
7. Weak team-task scripts: `send_design.sh` runs `design propose --help`; `run_stress.sh` is plan-only.
8. Importer: full re-import broken (T53); U2.5 bom/files manifest not delivered; U2.5d not yet in §7 (D33, due 11-25).
9. Perf margin thin; README is 85 lines and `docs/cli.md` doesn't exist (U4.1 Step 4).

### R-ids and metrics
| Item | Ledger | Verdict | Note |
|---|---|---|---|
| R2 R3 R4 R5 R8 R15 R16 R18 R19 R20 R21 R22 R24 R27 R30 R32 R35 R36 R38 | done | PASS | |
| R6 | done | PASS | 5 modes cut without a record (B2) |
| R7 | done | PASS | 12/12 scripts tested; send_design is `--help` |
| R9 | done | PASS | under D24; cge-001 NOT CHECKED (T31) |
| R11 | done | FAIL | drag not started; analytic T6 (B2) |
| R26 | done | PASS | |
| R33 | open | met, closes with U4.1 | (B1) |
| R17 | open | GAP | probably met by PR #3 |
| R25 | open | GAP | rests on D24 |
| R13 | open | GAP | waits for U2.2 Step 3a |
| R1 R12 R14 R31 | open | GAP | D33 / U2.5d |
| R10 R23 R28 R34 R39 R40 | open | GAP | U4.1 / v1.1 / process |
| R29 | superseded | GAP | D3 |
| R37 | dropped | PASS | §8 |
| M1 team tasks 12/12 | | PASS | |
| M2 one registry, surfaces generated | | GAP | 4 hand-written MCP tools, Studio-only routes, CLI-only commands |
| M3 one app + CLI | | PASS | 6 of 11 modes (B2) |
| M4 tiers 0–9 | | PASS | |
| M5 blocking pending = 0 or named | | PASS | `landing_load_factor` under D6 |
| M6 PDL blocks | | PASS | concept-a lacks bom, files, transport, assembly data |
| M7 hooks enforce rules | | PASS | |
| M8 ledger report + update publish | | PASS | |
| M9 iteration ≤ 60 s | | PASS | 56.9 s quiet warm; 78.9 s cold; 113.5 s loaded |
| §7 ticks have merge/review records | | FAIL | all except U2.5 Step 4 (B3) |

### Verdict: REJECT
