# Metrics slide (U4.2 Step 3): plan §2.1 with measured values, 2026-11-22 (W4-TE)

Sources: WB = `reviews/2026-11-22-whole-branch.md` (reviewer W4-R1, main at dea6f2a, verdict REJECT with six blocking items; main has moved to 69d050f). W4 = `reviews/2026-11-22-w4.md`. "ran" = command run by W4-TE on a scratch clone of main at 69d050f. Targets are not shown as results.

## A. The nine §2.1 metrics
| # | Measure | Today (plan) | Measured | Verdict | Source |
|---|---|---|---|---|---|
| M1 | Team tasks doable with no code edit | 3 of 12 | 12 of 12 scripts, each tested; `send_design.sh` only runs `design propose --help` and `run_stress.sh` is plan-only | PASS (two scripts weak) | WB:48 and WB:27; ran: `tests/test_team_tasks.py` + `tests/test_surfaces_in_sync.py` 29 passed, 160 s, with `plane` on PATH (12 failed without it) |
| M2 | One registry; CLI, MCP, Studio generated | 3 hand-written | 51 ops registered (ran `plane ops list`, 51 lines); not fully generated: 4 hand-written MCP tools, Studio-only routes, CLI-only commands (baseline, progress, build-index, import) | GAP | WB:49, WB:23; ran `plane ops list` |
| M3 | One app plus CLI | 5 interfaces | Plane Studio, 6 modes shipped (Designs, Compare, Physics, Stress, Updates, Ledger) plus an edit panel; §2.7 lists 11, 5 cut without a ledger record, Knowledge mode undecided; R11 "drag it around" not built (D43, v1.1) | PASS with caveat | WB:14, WB:50; `viewer/app.js:9` |
| M4 | Gates | tiers 0-5 | tiers 0-9 run; default `design validate` also runs 7 and 8; docs still say 0-5 (WB blocking 4) | PASS | WB:53, WB:16; ran: concept-a validate shows tiers 7, 8 |
| M5 | Blocking thresholds `source: pending` | 2 | 1: `landing_load_factor` (named, under D6) | PASS | WB:52, WB:9; ran `plane standards pending` first line `BLOCK landing_load_factor` |
| M6 | What a design can describe | geometry, joints, mass, flight | PDL 1.0 blocks exist; concept-a lacks bom, files, transport and assembly data | PASS (concept-a incomplete, see gap D33) | WB:54 |
| M7 | Agent rules enforced | advisory | roster plus hooks; 10 agent roles in `.claude/agents/` | PASS | WB:55; ran `ls .claude/agents` = 10 |
| M8 | Before-meeting status | memory | `plane ledger report` and `plane update publish` both work | PASS | WB:56; ran: ledger 359 items, 66 open, 0 overdue, 0 open prompts (live `plane ledger report`, 2026-11-22); publish 3.0 s |
| M9 | Iteration loop (set, then validate, no FEA) | edit YAML by hand | concept-a: 56.9 s quiet warm, 78.9 s cold, 113.5 s loaded machine; ran 83 s cold on a fresh clone (exit 1; on main 2026-11-23 the same command shows 10 FAIL rows). Template demo design: `design set` 5.7 s plus validate 9.4 s. Margin on the 60 s target is about 3 s warm | PASS (thin) | W4:94-108 (3 quiet runs each, median 120.9 s before, 56.9 s after, results byte-identical); WB:56, WB:7; ran 83 s |
| | §7 ticks have merge and review records | n/a | all except U2.5 Step 4 (no record that Dillon's BOM/claims check against the Explorer happened) | FAIL | WB:57, WB:15 |

Count: 9 metrics: 8 PASS (M3 and M9 with caveats, M6 with data gaps), 1 GAP (M2). Plus one process FAIL (the tick-record row). Whole-branch verdict at dea6f2a: REJECT; items B1 to B6 were not re-verified by W4-TE except B6, closed by `reviews/2026-11-22-concept-a-discipline.md` ACCEPT.

## B. Test and validation numbers (measured)
| Value | Number | Source |
|---|---|---|
| pytest at dea6f2a | 663 passed, 2 skipped, 1 failed (`tests/test_seed.py:9`, PATH) | WB:6 (full-suite CI run 45072187659) |
| concept-a `--tier all` | PASS 693, SKIP 73, WARN 146, FAIL 10 (all result rows, ran on main 5c229e7 after T28); fidelity 134 of 714 blocking checks sourced; 0 measured masses | ran 2026-11-23: 693 / 73 / 146 / 10, `Fidelity: 134 of 714` (WB:7 earlier tree: 531 / 102 / 9 / 4, 134 of 635) |
| Perf change | median 120.9 s to 56.9 s wall (CPU 129.0 to 66.1 s); frozen fixture 51.2 to 42.2 s | W4:98-102 |
| `plane tools doctor` | exit 0 at dea6f2a; opencae, aerosandbox, davinci missing, blender and sitl planned | WB:8 |
| Ledger | 359 items: 66 open, 52 done, 232 decided | live `plane ledger report`, 2026-11-22 |

## C. The ten known concept-a FAILs (state them; do not hide)
All from `plane design validate designs/concept-a --json` (ran 2026-11-23 on main 5c229e7, exit 1; WB:7 earlier tree listed four):
1. `T2.sim_drop_loads` E-WNG-20: peak 1.8 N in drop test exceeds rating 1.4 N
2. `T2.sim_drop_loads` E-WNG-21: peak 1.8 N in drop test exceeds rating 1.4 N
3. `T2.sim_drop_loads` E-MEC-05: peak 1.2 N in drop test exceeds rating 0.7 N
4. `T2.sim_drop_loads` E-MEC-10: peak 1.3 N in drop test exceeds rating 0.7 N
5. `T2.sim_rest` tipped over after drop: landing axis 81 deg from vertical (limit 30), speed 0.010 m/s; tailsitter cannot stand on its landing gear
6. `T2.fea_strength` cge-001 landing: 34.44 MPa peak away from the clamps vs 12.6 MPa allowable at 1.5x load (SF 0.37; 34.44 MPa at the clamp edges)
7. `T2.fea_strength` cge-001 thrust: 28.59 MPa peak away from the clamps vs 12.6 MPa allowable at 1.5x load (SF 0.44; 28.59 MPa at the clamp edges)
8. `T2.fea_strength` cge-006 landing: 15.22 MPa peak away from the clamps vs 12.6 MPa allowable at 1.5x load (SF 0.83; 15.22 MPa at the clamp edges)
9. `T2.fea_strength` cge-006 thrust: 17.45 MPa peak away from the clamps vs 12.6 MPa allowable at 1.5x load (SF 0.72; 17.45 MPa at the clamp edges)
10. `T3.static_margin` 16.4% MAC (NP x=59 mm, CG x=21 mm; target 5%-15%; fuselage effect not modelled) (mesh wing: chord measured at 41 stations)
Concept-a validated accepted: no. These sit behind pending thresholds and open model questions (T37), not behind a gate being skipped.

## D. Honest gaps (each is a named slide line, not a footnote)
| ID | What is not done | Slide wording | Source |
|---|---|---|---|
| D32 / T12 | No mass-gate number: 2.6 vs 2.7 kg standards conflict unresolved; keys stay `pending`; v1.1 | "No mass-gate number is quoted" | plan §3 row D32; ledger D32 |
| D33 / T24 | R1, R12, R14, R17, R31 are open gaps: concept-a re-import into PDL 1.0 (U2.5d) cannot land before the 11-30 freeze; v1.1. Ledger today: R1 open (concept-a still 0.4 in the ledger note; WB says it is schema 1.0 now, stale evidence), R12 open, R14 open, R17 open (WB:21 says probably met by PR #3 elevon mechanisms), R31 open | "Five requirements open until the concept-a re-import" | WB:21, WB:44; ledger R1, R12, R14, R17, R31 |
| D34 / T28 | Closed by D59 and D60: `read_value` registered; concept-a T9 is 93 PASS, 0 SKIP, 0 FAIL (was 53 PASS, 40 SKIP): 53 recomputed, 40 stored results read from source and checked against limits (analyses not re-run) | "93 PASS: 53 recomputed, 40 read from source and checked against limits" | ledger D34, T28, D59, D60 |
| T35 | PlaneBench 7 of 9 passes were reached by editing `mass_g` numbers only (mass-cut-10: Sonnet and Opus); fix-static-margin passes added mass without a real part change; Haiku's 0 on mass-cut-10 was declining to invent masses. Grader does not yet protect `designs/` (T54, v1.1) | Never "agents can cut mass"; never rank Haiku last on mass-cut-10 | `reviews/2026-11-21-w3.md:487`, `:593`, `:615`; `bench/results/2026-11-21.md`; ledger T35, T54 |
| R11 | "Drag the drone around" (interactive physics) not built; Physics mode replays analytic T6 sweeps | "Physics mode replays the mechanism sweep" | WB:14, WB:38; D43 |
| R29 | DaVinci full build superseded (D3); adapter is SKIP-with-reason | omit or "planned" | WB:46 |
| T57 | Windows viewer-test flake: backlog fix merged, cause still a hypothesis, task stays open | do not claim CI is flake-free | W4:`W4d viewer-flake` section |
| Open R-ids | R10, R23, R28, R34, R39, R40 open (U4.1, v1.1, process); R25 rests on D24; R33 met (56.9 s) but ledger-open until U4.1 closes. Ledger now shows R10 and R13 done (dc8902a) | list as "open" | WB:43-45; ledger |

## E. Discipline findings on concept-a (design problems found by the review skills, not gate bugs)
Source: `reviews/2026-11-22-concept-a-discipline.md` (ACCEPT of the review itself, at 7553ddd).
| Task | Finding | Owner, due |
|---|---|---|
| T60 | hrn-bat 14 AWG: 45 A x 0.8 derating = 36 A < 44.8 A peak pack current (`T7.electrical_rating` report-only FAIL); pick 12 AWG or lower the peak | conductor, 12-08 |
| T63 | 38 PETG parts routed to `jacobs-fdm`, whose standard lists PLA only (`standards/manufacturing.yaml:40-45`) | Dillon, 12-08 |
| T64 | CA (incl. foam-safe) declared on XPS fin fairings E-FIN-05..08 and 13..16 (`plane.yaml:1304-1337`) | Dillon, 12-08 |
| T65 | Torsion-mode damping behind CL-A-VIB-GM and VIB-GM-SHIFT unstated and unsourced (zeta 1% and 0.5% only in CALC-A-VIB-FC) | Dillon, 12-08 |
| T66 | FC power board and capacitor not modelled; RC receiver regional variant unstated; no Remote ID module | Dillon, 12-08 |
Also in the same review: FAIL on fc-sku-check, rc-variant, esc-listing and lab-access (not found in a BOM) and chemical-safety; most other items are "pending (no key)" or "N/A, nothing built yet" (`README.md:56`).

## F. Not measurable today (say so)
- A teammate-machine harness install (D31): evidence is the CI install test only.
- Browser click-through of Studio modes: CI Playwright tests only; not run by W4-TE.
- Mass accuracy: 0 components have measured mass (WB:7; ran: "0 components have measured mass").
