# Metrics slide (U4.2 Step 3): plan §2.1 with measured values, 2026-11-22 (W4-TE); sections B, C, E, G re-measured 2026-11-24 (W24-B4)

Sources: WB = `reviews/2026-11-22-whole-branch.md` (reviewer W4-R1, main at dea6f2a, verdict REJECT with six blocking items; main has moved to 69d050f). W4 = `reviews/2026-11-22-w4.md`. "ran" = command run by W4-TE on a scratch clone of main at 69d050f. The 11-24 re-measure (W24-B4) ran on a fresh clone of main at b7b50cb, marked "ran 11-24". Targets are not shown as results.

## A. The nine §2.1 metrics
| # | Measure | Today (plan) | Measured | Verdict | Source |
|---|---|---|---|---|---|
| M1 | Team tasks doable with no code edit | 3 of 12 | 12 of 12 scripts, each tested; `send_design.sh` only runs `design propose --help` and `run_stress.sh` is plan-only | PASS (two scripts weak) | WB:48 and WB:27; ran: `tests/test_team_tasks.py` + `tests/test_surfaces_in_sync.py` 29 passed, 160 s, with `plane` on PATH (12 failed without it) |
| M2 | One registry; CLI, MCP, Studio generated | 3 hand-written | 55 ops registered (ran `plane ops list` 11-24, 55 lines; 51 on 11-22); not fully generated: 4 hand-written MCP tools, Studio-only routes, CLI-only commands (baseline, progress, build-index, import) | GAP | WB:49, WB:23; ran `plane ops list` |
| M3 | One app plus CLI | 5 interfaces | Plane Studio, 6 modes shipped (Designs, Compare, Physics, Stress, Updates, Ledger) plus an edit panel; §2.7 lists 11, 5 cut without a ledger record, Knowledge mode undecided; R11 "drag it around" not built (D43, v1.1) | PASS with caveat | WB:14, WB:50; `viewer/app.js:9` |
| M4 | Gates | tiers 0-5 | tiers 0-9 run; default `design validate` also runs 7 and 8; docs still say 0-5 (WB blocking 4) | PASS | WB:53, WB:16; ran: concept-a validate shows tiers 7, 8 |
| M5 | Blocking thresholds `source: pending` | 2 | 1: `landing_load_factor` (named, under D6) | PASS | WB:52, WB:9; ran `plane standards pending` first line `BLOCK landing_load_factor` |
| M6 | What a design can describe | geometry, joints, mass, flight | PDL 1.0 blocks exist; concept-a lacks bom, files, transport and assembly data | PASS (concept-a incomplete, see gap D33) | WB:54 |
| M7 | Agent rules enforced | advisory | roster plus hooks; 10 agent roles in `.claude/agents/` | PASS | WB:55; ran `ls .claude/agents` = 10 |
| M8 | Before-meeting status | memory | `plane ledger report` and `plane update publish` both work | PASS | WB:56; ran: ledger 359 items, 66 open, 0 overdue, 0 open prompts (live `plane ledger report`, 2026-11-22); publish 3.0 s |
| M9 | Iteration loop (set, then validate, no FEA) | edit YAML by hand | concept-a: 56.9 s quiet warm, 78.9 s cold, 113.5 s loaded machine; ran 83 s cold on a fresh clone (exit 1; on main 2026-11-23 the same command shows 10 FAIL rows). Template demo design: `design set` 5.7 s plus validate 9.4 s. Margin on the 60 s target is about 3 s warm | PASS (thin) | W4:94-108 (3 quiet runs each, median 120.9 s before, 56.9 s after, results byte-identical); WB:56, WB:7; ran 83 s |
| | §7 ticks have merge and review records | n/a | all except U2.5 Step 4 (no record that Dillon's BOM/claims check against the Explorer happened) | FAIL | WB:57, WB:15 |

Count: 9 metrics: 8 PASS (M3 and M9 with caveats, M6 with data gaps), 1 GAP (M2). Plus one process FAIL (the tick-record row). Whole-branch verdict at dea6f2a: REJECT; items B1 to B6 were not re-verified by W4-TE except B6, closed by `reviews/2026-11-22-concept-a-discipline.md` ACCEPT.

## B. Test and validation numbers (measured; re-measured 2026-11-24 on main b7b50cb)
| Value | Number | Source |
|---|---|---|
| pytest at dea6f2a | 663 passed, 2 skipped, 1 failed (`tests/test_seed.py:9`, PATH) | WB:6 (full-suite CI run 45072187659) |
| concept-a `--tier all` | PASS 693, SKIP 73, WARN 146, FAIL 10 (all result rows, JSON run 11-24, exit 1); `Fidelity: 134 of 714` blocking checks sourced; 0 measured masses | ran 11-24: `plane design validate designs/concept-a --tier all --json` (status counts over all tier results) and the text run, last line `Fidelity: 134 of 714 blocking checks use sourced thresholds; 0 components have measured mass.` (11-23 values identical; 11-22 WB:7 earlier tree: 531 / 102 / 9 / 4, 134 of 635) |
| concept-a-param `--tier all` (900 mm, main state) | PASS 660, WARN 146, SKIP 73, FAIL 20; `Fidelity: 99 of 691` | ran 11-24 on main, `plane design validate designs/concept-a-param` (exit 1) |
| Perf change | median 120.9 s to 56.9 s wall (CPU 129.0 to 66.1 s); frozen fixture 51.2 to 42.2 s | W4:98-102 |
| `plane tools doctor` | exit 0 at dea6f2a; opencae, aerosandbox, davinci missing, blender and sitl planned | WB:8 |
| Ledger | 438 items: 61 open, 110 done, 2 dropped, 7 superseded, 258 decided (all kinds: 40 rulings, 123 tasks, 1 idea, 274 decisions); 0 overdue, 0 open prompts | ran 11-24: `plane ledger report`. (11-22: 359 items, 66 open, 52 done, 232 decided) |
| Tag v1.0.0 | commit 55fedae (annotated tag object 3635549) | ran 11-24: `git rev-parse --short v1.0.0^{commit}` = 55fedae; `git rev-parse --short v1.0.0` = 3635549; `git cat-file -t v1.0.0` = tag. (deck had 55fedae, which is the commit) |
| Claims tier | 93 PASS = 53 recomputed + 40 read from source | ran 11-24: `plane claim check designs/concept-a` summary line |
| Agent roles | 10 | ran 11-24: `ls .claude/agents` |
| Pending blocking thresholds | 1: `landing_load_factor` | ran 11-24: `plane standards pending` (lines starting BLOCK) |
| Op count | 55 | ran 11-24: `plane ops list` (55 lines) |
| Parametric demo, 940 mm | FAIL 19, PASS 661, WARN 146, SKIP 73; `Fidelity: 99 of 691` | ran 11-24: `plane design validate designs/concept-a-param`, see section G |

## C. The ten known concept-a FAILs (state them; do not hide)
All from `plane design validate designs/concept-a --tier all --json` (ran 2026-11-24 on main b7b50cb, exit 1; the same ten rows as 2026-11-23 on main 5c229e7; WB:7 earlier tree listed four). Ledger ids: rows 1-2 T74, rows 3-4 T73, row 5 T75, rows 6-9 T71, row 10 T76.
1. `T2.sim_drop_loads` E-WNG-20: peak 1.8 N in drop test exceeds rating 1.4 N (T74)
2. `T2.sim_drop_loads` E-WNG-21: peak 1.8 N in drop test exceeds rating 1.4 N (T74)
3. `T2.sim_drop_loads` E-MEC-05: peak 1.2 N in drop test exceeds rating 0.7 N (T73)
4. `T2.sim_drop_loads` E-MEC-10: peak 1.3 N in drop test exceeds rating 0.7 N (T73)
5. `T2.sim_rest` tipped over after drop: landing axis 81 deg from vertical (limit 30), speed 0.010 m/s; tailsitter cannot stand on its landing gear (T75)
6. `T2.fea_strength` cge-001 landing: 34.44 MPa peak away from the clamps vs 12.6 MPa allowable at 1.5x load (SF 0.37; 34.44 MPa at the clamp edges) (T71)
7. `T2.fea_strength` cge-001 thrust: 28.59 MPa peak away from the clamps vs 12.6 MPa allowable at 1.5x load (SF 0.44; 28.59 MPa at the clamp edges) (T71)
8. `T2.fea_strength` cge-006 landing: 15.22 MPa peak away from the clamps vs 12.6 MPa allowable at 1.5x load (SF 0.83; 15.22 MPa at the clamp edges) (T71)
9. `T2.fea_strength` cge-006 thrust: 17.45 MPa peak away from the clamps vs 12.6 MPa allowable at 1.5x load (SF 0.72; 17.45 MPa at the clamp edges) (T71)
10. `T3.static_margin` 16.4% MAC (NP x=59 mm, CG x=21 mm; target 5%-15%; fuselage effect not modelled) (mesh wing: chord measured at 41 stations) (T76)
Concept-a validated accepted: no. These sit behind pending thresholds and open model questions (T37), not behind a gate being skipped.

## D. Honest gaps (each is a named slide line, not a footnote)
| ID | What is not done | Slide wording | Source |
|---|---|---|---|
| D32 / T12 | No mass-gate number: 2.6 vs 2.7 kg standards conflict unresolved; keys stay `pending`; v1.1 | "No mass-gate number is quoted" | plan §3 row D32; ledger D32 |
| D33 / T24 (superseded by D72) | R1, R12, R14, R17, R31 closed by the concept-a re-import (merge d24b6df, W4-RD ACCEPT); T24 done. D33 premise (cannot land before the 11-30 freeze) was overtaken. Deck shows ledger truth | "R1, R12, R14, R17, R31 closed by the concept-a re-import (d24b6df)" | ledger R1, R12, R14, R17, R31, T24 (all done, 11-24); D72 |
| D34 / T28 | Closed by D59 and D60: `read_value` registered; concept-a claims tier is 93 PASS (`plane claim check` 11-24): 53 recomputed, 40 stored results read from source and checked against limits (analyses not re-run) | "93 PASS: 53 recomputed, 40 read from source and checked against limits" | ledger D34, T28, D59, D60; ran 11-24 |
| T35 | PlaneBench 7 of 9 passes were reached by editing `mass_g` numbers only (mass-cut-10: Sonnet and Opus); fix-static-margin passes added mass without a real part change; Haiku's 0 on mass-cut-10 was declining to invent masses. Grader now replays logged commands and protects `designs/` (T54 done, 41aa2a8) | Never "agents can cut mass"; never rank Haiku last on mass-cut-10 | `reviews/2026-11-21-w3.md:487`, `:593`, `:615`; `bench/results/2026-11-21.md`; ledger T35, T54 |
| R11 | "Drag the drone around" (interactive physics) not built; Physics mode replays analytic T6 sweeps | "Physics mode replays the mechanism sweep" | WB:14, WB:38; D43 |
| R29 | DaVinci full build superseded (D3); adapter is SKIP-with-reason | omit or "planned" | WB:46 |
| T57 | Windows viewer-test flake: backlog fix merged, cause still a hypothesis, task stays open | do not claim CI is flake-free | W4:`W4d viewer-flake` section |
| Open R-ids | R10, R23, R28, R34, R39, R40 open (U4.1, v1.1, process); R25 rests on D24; R33 met (56.9 s) but ledger-open until U4.1 closes. Ledger now shows R10 and R13 done (dc8902a) | list as "open" | WB:43-45; ledger |

## E. Discipline findings on concept-a (design problems found by the review skills, not gate bugs)
Source: `reviews/2026-11-22-concept-a-discipline.md` (ACCEPT of the review itself, at 7553ddd); owners and due dates from the ledger, checked 11-24.
| Task | Finding | Owner, due, status |
|---|---|---|
| T60 | hrn-bat 14 AWG: 45 A x 0.8 derating = 36 A < 44.8 A peak pack current (`T7.electrical_rating` report-only FAIL); pick 12 AWG or lower the peak | conductor, 12-08, done |
| T94 | BOM spares double-counted: `importers/dbf_blocks.py:27` adds spares to a qty that already includes them; lines total $1323.39 instead of $1262.50 (+$60.89) | conductor, 12-08, done |
| T63 | 38 PETG parts routed to `jacobs-fdm`, whose standard lists PLA only (`standards/manufacturing.yaml:40-45`) | Dillon, 12-08, open |
| T64 | CA (incl. foam-safe) declared on XPS fin fairings E-FIN-05..08 and 13..16 (`plane.yaml:1304-1337`) | Dillon, 12-08, open |
| T65 | Torsion-mode damping behind CL-A-VIB-GM and VIB-GM-SHIFT unstated and unsourced (zeta 1% and 0.5% only in CALC-A-VIB-FC) | Dillon, 12-08, open |
| T66 | FC power board and capacitor not modelled; RC receiver regional variant unstated; no Remote ID module | Dillon, 12-08, open |
| T73 | Drop test: E-MEC-05 1.2 N and E-MEC-10 1.3 N peak vs 0.7 N rating (new after re-import) | Dillon, 12-08, open |
| T74 | Drop test: E-WNG-20 and E-WNG-21 1.8 N vs 1.4 N rating (pre-existing) | Dillon, 12-08, open |
| T75 | Tailsitter tips 81 deg on its gear (limit 30) | Dillon, 12-08, open |
| T76 | Static margin 16.4% MAC (CG x=21 mm) vs 5-15% target | Dillon, 12-08, open |
| T77 | Harnesses e-hrn-01 and e-hrn-14 have no gauge_awg (WARN) | Dillon, 12-08, open |
| T78 | 13 E-HRN harnesses leave their envelopes by 8-197 mm (worst e-hrn-11 197 mm) | Dillon, 12-08, open |
| T79 | 16 BOM lines not verified (`T8.bom.verified` WARN) | Dillon, 12-08, open |
| T80 | Packed airframe OBB exceeds the transport box by 38 mm (`T7.transport.packed-airframe` WARN) | Dillon, 12-08, open |
| T81 | wng-010-r/l added at assembly step 14 touching nothing assembled (`T7.assembly.touch` WARN) | Dillon, 12-08, open |
| T96 | All four motor cants turn the same way: about 1.06 N*m untrimmed yaw vs about 0.27 N*m reaction torque | Dillon, 12-08, open |
Also in the same review: FAIL on fc-sku-check, rc-variant, esc-listing and lab-access (not found in a BOM) and chemical-safety; most other items are "pending (no key)" or "N/A, nothing built yet" (`README.md:56`).

## F. Not measurable today (say so)
- A teammate-machine harness install (D31): evidence is the CI install test only.
- Browser click-through of Studio modes: CI Playwright tests only; not run by W4-TE or W24-B4.
- Mass accuracy: 0 components have measured mass (WB:7; ran 11-24: "0 components have measured mass").

## G. Parametric demonstration (U4.22 concept-a-param; U4.23 step 6; ran 11-24 on a clone of main b7b50cb)
| Value | Number | Source |
|---|---|---|
| `parameters.span_mm` | 900 (main) -> 940 (demo set) | `designs/concept-a-param/plane.yaml`; `plane design set ... --value 940` (11-24) |
| Mass | 1272.99 g at 900 mm -> 1279.79 g at 940 mm (+6.80 g: core +4.6, spar +2.2) | ran 11-24: `plane design mass designs/concept-a-param` (`mass_g`); README line 45 for the split |
| CG | x 21.35 -> 21.65 mm; y -2.02 -> -2.01; z 6.62 -> 6.58 | ran 11-24: `plane design mass` (`cg_mm`) |
| Static margin | 15.7% MAC (900) -> 15.6% MAC (940), both FAIL; concept-a 16.4% | ran 11-24: validate T3.static_margin rows of concept-a-param and concept-a |
| Stall | 11.7 -> 11.5 m/s | README line 47 only (not re-measured 11-24) |
| FAIL rows | 20 at 900 mm (main); 19 at 940 mm (demo) | ran 11-24: `plane design validate designs/concept-a-param` (exit 1 both) |
| Neutral-pose pocket FAILs | 14 new rows (12 T1 interference and attachment-overlap rows at poses and sweeps, 2 T6 mechanism collisions at -15 deg); 4 concept-a cge stress rows absent because `fea/` is not copied | ran 11-24 (rows listed by check id); `designs/concept-a-param/README.md` lines 24-36 |
| Net extra vs concept-a | 10 FAIL at 900 mm (20 vs 10); at 940 mm 5 of the 19 FAILs are concept-a's own (drop tests, tip, static margin) and 14 are pockets | ran 11-24; ledger T121 |
| Fidelity | 99 of 691 blocking checks sourced (900 and 940 mm); 0 components have measured mass | ran 11-24 |
| Tier 1 at 940 mm | PASS 161, FAIL 12, SKIP 8, WARN 0; `Fidelity: 0 of 181`; partial run (no Accepted line) | ran 11-24: `plane design validate designs/concept-a-param --tier 1` |
| Open item | Pose-aware cut pockets make the copy match concept-a's FAIL set (U4.25, not merged 11-24) | ledger T121, D70 |
