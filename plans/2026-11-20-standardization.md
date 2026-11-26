# DBF Hangar v1.0 Implementation Plan (CLI, Plane Design Language, one surface)

Repo: [davinciucberkeley-collab/dbf-hangar](https://github.com/davinciucberkeley-collab/dbf-hangar). Owner of every unit: **Tristan**. Teammates (Dillon, James, Vaibhav) are users and acceptance testers; Douglas is the advisor.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan unit by unit. Steps use checkbox (`- [ ]`) syntax for tracking. Every unit is one branch and one PR. Agents come only from `.claude/agents/` (see §5).

**Goal:** By Wednesday 2026-12-02 (next team meeting; Tristan, 2026-11-21), one new repo (`dbf-hangar`) holds what the team's other repos do, rebuilt to one standard, and every team task (new design, design change, analysis, research, morphological chart, BOM check, assembly test, weekly update) can be done by an agent or a teammate through one `plane` CLI on one shared design language, without editing code, and the result is visible at one link.

**Architecture:** One operations layer (`core/hangar/ops/`) is the API. The `plane` CLI, the MCP server and Plane Studio are generated from it, so there is one way to do each thing. Designs are data in the Plane Design Language (PDL v1.0, `schema/plane.schema.json`); analyses are gates and adapters that read PDL and never require code edits to accept a new plane. A team harness (`.claude/agents/`, hooks, ledger) makes the agent rules part of the system instead of a file agents forget.

**Tech Stack:** Python 3.12, click, jsonschema, ruamel.yaml, trimesh/manifold3d, MuJoCo 3, mcp ≥1.2, pytest; OpenCAE Studio (CalculiX) via adapter; vanilla JS viewer on GitHub Pages; Claude Code agents, hooks and output styles.

**Spec:** §1–§4 of this file (the spec and the plan travel together, per the team's request for one file). Sources: DBF weekly check-in transcripts 2026-11-04, 2026-11-11, 2026-11-18 (team Drive folder "161 Design-Build-Fly"); repos `aircraft-platform` @ `f462468`, `DBF-Combined` @ `a93f14d` (itself a snapshot of DBF-VTOL, DillonVTOL, TiltWing and OpenCAEModel, see its `PROVENANCE.md`), `OpenCAEModel` @ `792f0ab`.

## Global Constraints

- Deadline: presentable v1.0 on **2026-12-02** (moved from 12-01 by Tristan, 2026-11-21). Feature freeze **2026-11-30 18:00 PT** (shifted one day with the deadline); after it only fixes from review.
- One schema, one CLI, one app. **No new interfaces** (advisor, 11-18): new capability lands as an op, a gate, an adapter or a Studio *mode*, never as a new app, page or script entry point.
- **New designs never need code edits** (advisor, 11-18). CI enforces: a PR that changes `designs/**` may not change `core/**` (U1.4).
- Thresholds live only in `standards/*.yaml`, each with `source:` or `source: pending` (existing CLAUDE.md rule, kept).
- Every op returns the `OpResult` JSON contract (U1.1) when called with `--json`; exit code 0 = ok, 1 = check failed, 2 = usage/input error.
- Python ≥ 3.11; CI on 3.12, Linux + Windows (team works on Windows/Miniforge).
- Old commands keep working until v1.1 (`plane validate`, `plane fea`, …) as aliases; schema 0.1–0.4 files migrate with `plane design migrate`.
- Agents: Haiku builds by default; "hard" work class bumps one tier (§5). Main sessions at medium effort; `plan-scheme` runs at max effort for planning only (advisor, 11-18).
- Agents are quiet: no narration over ~20 words unless answering a question (`.claude/output-styles/quiet.md`).
- **Adapt, don't copy** (Tristan, 11-20): nothing enters hangar as a folder dump. Each source piece is rebuilt as an op, a gate, an adapter, PDL data, a knowledge entry or a Studio mode (§1b), and `PROVENANCE.md` records the source repo, commit and path of everything imported.
- **No generated output is imported** (renders, films, sites, `out/` folders, team agent transcripts: about 1 GB of DBF-Combined). hangar regenerates what it needs through ops.
- OpenCAE Studio is GPL-3.0: hangar calls it as an external tool through its adapter and does not vendor its source.
- Meshes and CAD files go through Git LFS (`.gitattributes`: `*.stl *.step *.stp *.glb *.f3d *.SLDPRT`), D8.
- The package is `hangar` (`core/hangar/`); the CLI stays `plane`.

## Review Focus

1. **A teammate's design that the importer has never seen** (e.g. Dillon's next CAD revision with a new part type): expected to load, migrate and get a scorecard with SKIPs naming what is missing, never a traceback. Pinned by `tests/test_ops_contract.py::test_unknown_component_type_gives_skip_not_crash` (U1.1).
2. **Windows paths and line endings** in every op (`designs\concept-a`, CRLF YAML): expected identical results to Linux. Pinned by `tests/test_paths.py::test_backslash_and_crlf_roundtrip` (U1.4) and the Windows CI job.
3. **`design.set` on a path that does not exist, or a value of the wrong type**: expected exit 2 with the schema path and the allowed type, file untouched. Pinned by `tests/test_design_edit.py::test_set_rejects_bad_path_and_type_without_writing` (U1.4).
4. **An external tool missing** (OpenCAE not installed, DaVinci not connected, MuJoCo import fails on a laptop): expected SKIP with the fix command from `plane tools doctor`, and `accepted` stays false with a reason, never a silent PASS. Pinned by `tests/test_adapters.py::test_missing_tool_is_skip_with_fix` (U2.3).
5. **A ledger item closed as "dropped" vs "not done"** (advisor, 11-18: Claude marks decided-against items as overdue): expected `dropped` to require `decided_in:` and never appear in the overdue list. Pinned by `tests/test_ledger.py::test_dropped_needs_decision_and_is_not_overdue` (U0.3).

---

## 1. What was asked (traceability)

Every requirement has an id. The ledger (U0.3) is seeded from this table; a unit is not done until its R-ids are marked `done` with evidence (PR or file), or `dropped` with a decision reference. "A" = advisor (Douglas), "T" = team member.

| R | Who / when | Requirement (paraphrased from the transcript) | Unit(s) |
|---|---|---|---|
| R1 | A 11-11, 11-18 | A consistent file format for a plane ("schema"): if Tristan submits a plane to the system Dillon works in, it drops into the same bucket; CAD files go here, BOM goes here | U1.3, U2.5d (data, d24b6df) |
| R2 | A 11-11 | CLI **and** MCP so different agents interface with one app; `plane add …` instead of agents editing HTML per plane | U1.1, U1.2 |
| R3 | A 11-18 | API → CLI on top → simple natural-language layer on top of that (skills) | U1.1, U1.2, U3.2 |
| R4 | A 11-18 | Separate operations and data from code; don't edit code every time you run a simulation; saves tokens | U1.1, U1.4, U2.3 |
| R5 | A 11-18 | Bring in new plane designs without changing design-software code ("put a window in, don't remove bricks") | U1.4 (CI rule), U2.1 |
| R6 | A 11-18 | Lots of new things, **no new interfaces**; you have ~15, need ~3; one interface, different modes, one design language, one surface | U3.1 |
| R7 | A 11-18 | Stretch: every team task doable via CLI without editing code: sending designs, updating morphological chart, sending an idea, researching, consolidating, testing assembly, Dillon's tasks | U1.4, U2.4, U3.4 |
| R8 | A 11-18 (to Tristan) | CLI lets Claude test a design, change one parameter, re-test, see how it evolves, iterate fast | U1.4 (`design.set`, `design.sweep`) |
| R9 | A 11-18 (to Vaibhav) | OpenCAE behind a CLI: can an agent run a full simulation + design iteration without editing or crawling code? then can Dillon? | U2.3, U3.4 |
| R10 | A 11-11 | Success conditions close to the real goal, hard enough Claude can't meet them unless it works: full 3D physics sim where parts can't pass through each other; mechanism works there or it doesn't; NASA standards; lift ratio | U2.1, U2.2 |
| R11 | A 11-18 | Rigid-body physics (frictionless first) to check mechanisms: motor motions, flap movements, "if you pull this, does it pull that"; drop the drone in and drag it around | U2.1 (T6), U3.1 (Physics mode) |
| R12 | A 11-11 | Gates: transport by car (the box), no exposed wires and rules for how wiring works | U1.3, U2.1 (T7), U2.5d (data, d24b6df) |
| R13 | A 11-11 | Database of plane guidelines and standards every design is evaluated against; manufacturing methods; "does a tailsitter actually work?" evidence | U2.2 (builds on `knowledge/`, `standards/`) |
| R14 | T 11-11 (Dillon) | BOM: verify parts are real (Amazon blocks agents → use Claude in Chrome) | U1.3 (`bom`), U2.4 (`bom.verify`), U2.5d (data, d24b6df) |
| R15 | A 11-18 | Claude adds, rarely subtracts; fixes must consider add / subtract / modify / adjust and not add unless needed; weight is the constraint | U1.4 (change kind log), U3.2 (`design-iterate` skill), agent `design-engineer` |
| R16 | A 11-18 | Iterative research at every step: "wing too heavy → research how others fixed it without adding parts"; recon + benchmarking | U3.2 (`recon` skill), agent `recon` |
| R17 | A 11-18 | Hardest goal first: working, non-placeholder mechanisms before weight | §6 ordering, U2.1 T6 before T8, U2.5d (data, d24b6df) |
| R18 | A 11-18 | Agent roles by **type and level** of work, not domain; Haiku builds, Sonnet for hard; tactician Sonnet (hard → Opus); advisor Opus; one conductor decides; batch of ~10 units → fresh Opus reviewer | U0.1, §5 |
| R19 | A 11-18 | Embed rules in the system: hook on agent launch asking "did you follow the rules", role must be picked; roles + output styles in Claude Code; hooks and looping prompts | U0.1, U0.2 |
| R20 | A 11-18 | Every prompt logged; agent may not stop until each prompt is marked addressed; compaction re-loads the task file; tasks in files, not memory | U0.2, U0.3 |
| R21 | A 11-18 | Hourly "get it together" audit (cheap Haiku): rules broken, stuck agent, plan drift; a fix that fails twice means something is wrong → advisor | U0.2, U3.2, agent `auditor` |
| R22 | A 11-18 | Plan before executing (scheme): max effort for planning, waves by dependency, units ≈ one PR each, one agent per unit; broken unit is fixed in place, not patched with a new unit; surface unknown decisions and a permissions prompt up front | §4–§6, U3.2 (`plan-scheme`) |
| R23 | A 11-18 | Pointer files: AGENTS/CLAUDE.md point to rule files, not contain them; trim bloat (280 stale items) | U0.1, U4.1 |
| R24 | A 11-18 | Team harness repo + install script so every teammate's Claude gets the same roles | U0.2 (`harness/install.py`) |
| R25 | A 11-18 | Multiple PRs on the same plane from different people/agents; Dillon picks which to merge | U1.4 (`design.propose`), §4 |
| R26 | A 11-18 | Weekly updates: one artifact/page with each person's thing and link, sent before the meeting; drafted early in the week as a checklist; doc in Drive with links | U2.4 (`update.*`), U3.1 (Updates mode) |
| R27 | A 11-18 | Before each meeting, list every task/idea from transcripts and compare with what repos have; beware "not done" vs "decided not to" | U0.3 (`ledger.ingest`, `ledger.check`) |
| R28 | A 11-11 | One link for all the team's stuff; local copies push to the shared online version | U3.1 (Pages build), U4.1 |
| R29 | A 11-18 | Connect DaVinci API to Claude; do a full build in DaVinci | U2.3 (DaVinci adapter), D3 |
| R30 | A 11-11 | Skill-making skill: research → recon → synthesize best of existing skills → de-bloat pass; every analysis is a skill | U3.2 |
| R31 | A 11-11 | Animate every step of manufacturing assembly; if Claude can't animate it, something is broken (self-check) | U2.4 (`assembly.animate`), T7 |
| R32 | A 11-18 | Benchmarks: could we make a plane benchmark? | U3.3 (PlaneBench v0) |
| R33 | A 11-18 | Agents are good at making things faster: e.g. renderer 10 min → 3 min | U4.1 (perf budget) |
| R34 | A 11-18 | Use superpowers when building software like OpenCAE | §4 (whole process) |
| R35 | T 11-18 (James) | Standardize `standards/agents.md` for everyone, with hooks to enforce it | U0.1, U0.2 |
| R36 | T 11-18 (Tristan) | Finish CLI + plane format; CLI is for Claude, not humans | U1.1–U1.4 |
| R37 | A 11-18 | Surrogate models matter for families (tens–hundreds of variants), not one | §8 Not doing (v1.1), `design.sweep` output is surrogate-ready |
| R38 | A 11-11 | Morphological chart from literature, not reinvented; synthesize options | U2.4 (`morph.*`) |
| R39 | T 11-20 (Tristan) | One new repo, `dbf-hangar`, that adapts what the other repos have so everything fits the advisor's vision; Tristan owns all of it | §1b, U0.4, U1.5, U1.6, U2.5 |
| R40 | A 11-11 | At least one person threads the side quests into the main quest; one software tool everyone works on, not four personal ones; integrate before adding | §1b, U0.4, U2.5 |

## 1b. What each source repo contributes (R39, R40)

Inventory taken 2026-11-20. "Lands as" is the only form a piece may take in hangar.

| Source (repo @ commit : path) | What it is | Lands as | Unit |
|---|---|---|---|
| aircraft-platform @ `f462468` : `core/`, `schema/`, `standards/`, `tests/`, `designs/`, `knowledge/`, `skills/`, `viewer/` | schema v0.4, validator tiers 0–5, CLI, MCP, Studio, FEA bridge, baselines, 7 designs, knowledge base | the seed: `core/hangar/` (renamed package), the rest kept in place; then rebuilt by W1–W3 | U0.4 |
| DBF-Combined @ `a93f14d` : `redesign/proofs/` (`proofs/1` schema, `proofkit.py`, `build_graph.py`) + `redesign/qp/A/proofs/claims.*.json` | claims graph: requirement → claim → calculation → parameter → source/test, margins recomputed | PDL `claims` (per design `claims.yaml`) + `claims` engine + gate **T9 Claims** + Proofs mode | U1.5 |
| DBF-Combined : `redesign/interfaces/` (`dbf-interfaces/1`, `connection_types.json`, `seats.json`, `merge_check.py`) | part–connection graph with a shared connection-type library | `standards/connection-types.yaml` + PDL `attachments[].connection` + T1 "nothing floating" check | U1.6 |
| DBF-Combined : `redesign/qp/A/` (`params-A.json`, `A.param`, `BOM-A.csv`, `REQUIREMENTS-A.md`, `MISSION.md`, `MASS-GATE.md`, `cad/`) | concept A, the current design | `designs/concept-a/` in PDL 1.0 with params, BOM (verified stamps from `date_checked`), requirements, claims, interfaces, meshes (LFS) | U2.5 |
| DBF-Combined : `redesign/params/CHANGE-LOG.md` (D-1…D-200), `DECISIONS.md` | design decision log and open conflicts | ledger items `kind: decision` with `source: CHANGE-LOG#D-182` | U2.5 |
| DBF-Combined : `CLAUDE.md` hard constraints ($2,000, 2027-04-30, car trunk, < 25 kg, 3-D physics, CAD = real parts, limit exposed wiring) | the team's hard requirements | `standards/program.yaml` (program-level requirements every design inherits) + gates T6–T8 | U2.1, U2.5 |
| DBF-Combined : `redesign/collision/` (Blender 4.5 collision, `--transport`), `redesign/qp/A/cad/a_assembly*.py`, `a_build_steps.py` | interpenetration, transport-pose and build-step checks | `blender` adapter used by T6/T7 when Blender is installed; MuJoCo/trimesh path otherwise | U2.3 |
| DBF-Combined : `redesign/qp/A/sitl/` (ArduPilot SITL plant, batches), `firmware/` | flight-case simulation | `sitl` adapter, report-only in v1.0 (§8) | U2.3 |
| DBF-Combined : `redesign/site/` (Explorer: 3-D with vendor links, build guide, hub stress map, BOM, status, morph chart, proofs) | the team's best viewer | its features become Studio modes (Build, BOM, Proofs, Stress); the site itself is not imported | U3.1 |
| DBF-Combined : `redesign/config-study/` (43 concepts, judging), `docs/research/`, `redesign/inputs/` | trade study and research | `knowledge/` entries via templates; concept cards linked to morph chart cells | U2.2 |
| DBF-Combined : `redesign/TEAM.md` (45 discipline roles) | agent roles by discipline | not imported as agents: replaced by the 10 work-level roles (R18); its checklists land as gates, standards, skills, scorecard sections and knowledge per §1c | U3.5, U3.6, U2.2 |
| DBF-Combined : `analysis/`, `cad/` (SOLIDWORKS rev G), `inventory/`, `fusion/` (v0.3.1), `explorations/tiltwing/`, `sim/` | earlier design states (C0 lift+cruise, K09-L, tiltwing) | `status: retired` designs only where aircraft-platform already has them (`c0-*`, `tiltwing-cakir`); the rest stays in DBF-Combined, linked from `PROVENANCE.md` | U2.5 |
| OpenCAEModel @ `792f0ab` (= DBF-Combined `tools/opencae-studio/`) | CalculiX-based CAE app, GPL-3.0 | external dependency behind the `opencae` adapter; hangar pins the version | U2.3 |
| DBF-VTOL, DillonVTOL, TiltWing | already inside DBF-Combined (its `PROVENANCE.md`) | nothing extra | — |

## 1c. Discipline roles → checks, standards and skills (Tristan, 2026-11-21)

DBF-Combined `redesign/TEAM.md` @ `a93f14d` lists **45** discipline roles (A1–J6; 39 with a `team/<id>/` folder). None becomes an agent: the 10 work-level roles stay (R18; Douglas 11-18). Each role's checklist was extracted by scouts into `plans/2026-11-20-standardization/discipline-extract/<id>.md` (1,935 check rows, each citing its source file and line), and every row was given exactly one destination under the fixed rules in `discipline-extract/_RULES.md`. Leadership and integration roles (A1 chief engineer, A2 systems, A4 configuration, J2 proof chain, J6 review board) land on what already exists: the conductor and advisor (decisions), the ledger (change requests, traceability), the claims graph and T9 (verification), and `standards/review-scorecard.md` (review rules).

**Totals (rows, after the advisor's re-tag pass):** gate 259 · standards 376 (367 distinct keys, design-independent only) · skill 97 · scorecard 60 · knowledge 128 · dropped 1015 (k09l-instance 650, duplicate 271, covered 47, k09l-only 4, generated-output 38, out-of-scope 5); 1935 rows in all.

**Where the rows land**
- **Existing gates** take most gate rows (T1.interference, T1.interfaces, T2.fea_strength, T3.mass, T3.static_margin, T3.hover_tw, T7.*, T8.*, T9.claims): no new code, they become test fixtures and criteria text in U3.6.
- **New gates (5, U3.6, report-only until D7's 12-08 date; advisor DF-A cut 7 to 5):** `T2.joint_rf` (every attachment with a `connection`: reserve factor = connection-type rating / computed joint load >= `joint_rf_min`; extends T2.joint_load), `T3.control_authority` (pitch, roll and yaw separately: hover control moment with a sagged pack / wind moment from `operations.yaml` >= `hover_ctrl_factor`; yaw usually binds), `T3.transition_margin` (VTOL only: transition speed margin over stall and entry thrust fraction <= 0.8 with a sagged pack; a non-VTOL design gets SKIP "not applicable", never PASS), `T3.endurance` (power computed from PDL, not a declared number; usable energy >= mission energy + reserve), `T7.electrical_rating` (wire gauge and disconnect rating >= peak current). Every gate names the PDL paths and `standards/` keys it reads; a pending threshold or a declared value without a calculation or source gives SKIP, as T9 does. Cut: `T7.thermal` and `T2.modal_separation` (no adapter produces their data) become `review-propulsion` / `review-structures` items plus T9 claims (U2.5 imports the E1-E3 temperature claims); `T2.load_case_coverage` drew no rows. Load cases become `standards/load-cases.yaml`, read by T2.fea_strength.
- **Standards:** D19 limits import to keys a gate or skill reads, enforced by a test (every `standards/*.yaml` key is referenced by a gate or a skill), and only design-independent values (ratios, factors, process/material ratings, field conditions); a number sized for one K09-L part never becomes a standards default, not even as `pending` (DF-A re-tag pass, `_RULES.md` amendments). New files: `standards/load-cases.yaml`, `standards/operations.yaml` (wind/gust/flight-window limits, go/no-go). No `gate-thresholds.yaml`; other keys go to `design-standards.yaml` only if FEA does not read them (D13/D18).
- **Skills (6, U3.5, ≤ 120 lines each):** `review-structures` (C1–C6, D1–D3, D5; modal separation), `review-aero` (B1–B4, A3 mass and CG), `review-controls` (B3 stability, F3–F5 avionics, flight software, RC link), `review-propulsion` (E1–E3, F1–F2: motors, props, power, energy, thermal, harness; thermal limits), `review-manufacturing` (G1–G4, D6–D7), `review-test-safety` (H1–H3). `review-mass` and `review-interfaces` drew 1 and 0 rows and are merged/dropped (subtract). Read by `reviewer` and `design-engineer`.
- **Scorecard (U3.5):** two new sections in `standards/review-scorecard.md`: *Evidence and closure* (a fail closes only by a design change, a corrected model with a stated reason, or a deciding test; limits are never loosened; reviewer estimates are labelled; figures spot-checked against the claims graph) and *Discipline sign-off* (each relevant discipline skill read and its items answered).
- **Knowledge (U3.5):** procedures, not checks: ground-test plan, build sequence, flight card, flight-test plan, transition procedure, battery handling, procurement lead times and smaller entries (19 topics, 128 rows), via `knowledge/` templates.
- **Dropped (1,015):** K09-L part values (claims about the retired configuration, D9), inactive D4, generated output (J3 renders, J4 visual design → Studio/Pages), duplicates and rows already covered.

**Per role** (counts by destination; main destinations = the three most frequent codes):

| Role | Name | Status | Rows | GATE | STD | SKILL | SCORECARD | KNOW | DROP | Main destinations |
|---|---|---|---|---|---|---|---|---|---|---|
| A1 | Chief engineer / integrator | active | 28 | 18 | 4 | 0 | 0 | 0 | 6 | `GATE:T3.static_margin` 7, `GATE:T3.mass` 4, `STD:design-standards` 2 |
| A2 | Systems engineer | K09-L in part | 59 | 20 | 17 | 6 | 0 | 2 | 14 | `STD:operations` 8, `GATE:T3.control_authority` 3, `STD:design-standards` 3 |
| A3 | Mass-properties engineer | active | 33 | 15 | 0 | 0 | 0 | 0 | 18 | `GATE:T3.static_margin` 6, `GATE:T3.mass` 4, `GATE:T9.claims` 2 |
| A4 | Configuration / interface manager | K09-L in part | 32 | 17 | 0 | 0 | 1 | 0 | 14 | `GATE:T0.schema` 4, `GATE:T1.interference` 4, `GATE:T7.wiring` 3 |
| A5 | CAD lead | active | 25 | 6 | 2 | 0 | 0 | 0 | 17 | `GATE:T3.static_margin` 2, `GATE:T0.schema` 2, `GATE:T9.claims` 2 |
| B1 | Aero performance engineer | K09-L in part | 40 | 6 | 4 | 0 | 1 | 0 | 29 | `GATE:T3.transition_margin` 3, `STD:design-standards` 3, `GATE:T3.control_authority` 2 |
| B2 | Wing aero engineer | K09-L in part | 45 | 3 | 3 | 3 | 4 | 0 | 32 | `SCORECARD:evidence-and-closure` 4, `SKILL:review-controls` 3, `STD:design-standards` 3 |
| B3 | Stability and control engineer | K09-L-specific | 72 | 12 | 3 | 6 | 5 | 0 | 46 | `GATE:T3.transition_margin` 6, `SCORECARD:evidence-and-closure` 5, `GATE:T3.control_authority` 5 |
| B4 | Rotor / propeller aero engineer | active | 48 | 3 | 10 | 1 | 1 | 0 | 33 | `STD:design-standards` 7, `STD:program` 3, `SCORECARD:evidence-and-closure` 1 |
| C1 | Loads engineer | active | 23 | 2 | 10 | 0 | 1 | 0 | 10 | `STD:program` 4, `STD:load-cases` 4, `STD:operations` 1 |
| C2 | Wing structures engineer | active | 57 | 2 | 12 | 0 | 1 | 0 | 42 | `STD:manufacturing` 9, `STD:program` 3, `GATE:T2.fea_strength` 1 |
| C3 | Pod structures engineer | K09-L in part | 35 | 3 | 9 | 0 | 0 | 0 | 23 | `STD:manufacturing` 7, `STD:design-standards` 2, `GATE:T2.joint_rf` 1 |
| C4 | Fin and motor-tube structures engineer | K09-L in part | 54 | 2 | 5 | 0 | 1 | 0 | 46 | `STD:manufacturing` 4, `SCORECARD:evidence-and-closure` 1, `STD:program` 1 |
| C5 | Landing / impact engineer | K09-L in part | 79 | 2 | 16 | 2 | 1 | 3 | 55 | `STD:operations` 7, `STD:program` 6, `STD:design-standards` 2 |
| C6 | Joints and fasteners engineer | active | 67 | 4 | 7 | 0 | 0 | 1 | 55 | `STD:connection-types` 7, `GATE:T2.joint_rf` 1, `GATE:T1.interference` 1 |
| D1 | Wing designer | active | 21 | 2 | 6 | 0 | 0 | 0 | 13 | `STD:manufacturing` 4, `STD:design-standards` 2, `GATE:T3.mass` 1 |
| D2 | Pod designer | K09-L-specific | 38 | 7 | 0 | 0 | 0 | 4 | 27 | `KNOW:ground-test-plan` 4, `GATE:T1.interfaces` 1, `GATE:T3.static_margin` 1 |
| D3 | Fin and motor-tube designer | K09-L-specific | 23 | 6 | 0 | 0 | 0 | 5 | 12 | `KNOW:ground-test-plan` 4, `GATE:T2.joint_rf` 1, `GATE:T1.interference` 1 |
| D4 | Tail designer | inactive | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| D5 | Landing designer | K09-L-specific | 38 | 7 | 6 | 0 | 0 | 6 | 19 | `KNOW:ground-test-plan` 5, `STD:design-standards` 3, `STD:load-cases` 2 |
| D6 | Mechanisms designer | K09-L in part | 27 | 7 | 0 | 0 | 0 | 4 | 16 | `KNOW:ground-test-plan` 4, `GATE:T6.mechanism` 1, `GATE:T2.fea_strength` 1 |
| D7 | Transport and packaging designer | active | 29 | 3 | 4 | 0 | 0 | 5 | 17 | `KNOW:ground-test-plan` 5, `STD:design-standards` 2, `STD:load-cases` 1 |
| E1 | Propulsion engineer | K09-L in part | 52 | 9 | 1 | 1 | 0 | 4 | 37 | `KNOW:ground-test-plan` 4, `STD:design-standards` 1, `GATE:T7.electrical_rating` 1 |
| E2 | Battery / energy engineer | active | 30 | 4 | 4 | 1 | 1 | 4 | 16 | `KNOW:ground-test-plan` 4, `STD:design-standards` 2, `STD:operations` 2 |
| E3 | Thermal engineer | active | 38 | 4 | 16 | 2 | 0 | 1 | 15 | `STD:design-standards` 9, `STD:operations` 3, `STD:load-cases` 2 |
| F1 | Power distribution engineer | K09-L in part | 55 | 6 | 14 | 0 | 1 | 1 | 33 | `STD:design-standards` 14, `GATE:T7.electrical_rating` 4, `GATE:T7.wiring` 2 |
| F2 | Harness engineer | active | 22 | 3 | 4 | 0 | 0 | 0 | 15 | `STD:design-standards` 4, `GATE:T1.interference` 2, `GATE:T7.wiring` 1 |
| F3 | Avionics hardware engineer | K09-L in part | 38 | 3 | 9 | 0 | 0 | 2 | 24 | `STD:design-standards` 9, `KNOW:ground-test-plan` 2, `GATE:T1.interfaces` 1 |
| F4 | Flight-control software engineer | active | 65 | 21 | 20 | 3 | 0 | 6 | 15 | `STD:design-standards` 12, `GATE:T3.control_authority` 9, `STD:operations` 7 |
| F5 | RC link, telemetry and ground station engineer | active | 47 | 5 | 16 | 3 | 2 | 8 | 13 | `STD:operations` 9, `STD:design-standards` 7, `GATE:T3.transition_margin` 3 |
| G1 | Manufacturing engineer | active | 38 | 6 | 7 | 4 | 2 | 3 | 16 | `STD:manufacturing` 6, `KNOW:build-sequence` 3, `SKILL:review-manufacturing` 3 |
| G2 | Composites and foam specialist | active | 46 | 1 | 7 | 5 | 2 | 15 | 16 | `KNOW:build-sequence` 11, `STD:manufacturing` 6, `SKILL:review-manufacturing` 5 |
| G3 | 3D-printing specialist | active | 18 | 2 | 4 | 5 | 0 | 1 | 6 | `SKILL:review-manufacturing` 5, `STD:manufacturing` 2, `GATE:T8.bom` 1 |
| G4 | Assembly sequence engineer | active | 46 | 3 | 14 | 10 | 4 | 2 | 13 | `STD:program` 4, `STD:manufacturing` 4, `STD:design-standards` 4 |
| H1 | Ground test engineer | active | 162 | 9 | 52 | 12 | 0 | 28 | 61 | `KNOW:ground-test-plan` 28, `STD:design-standards` 27, `STD:connection-types` 12 |
| H2 | Flight test engineer | active | 80 | 6 | 38 | 8 | 3 | 3 | 22 | `STD:operations` 32, `SKILL:review-controls` 8, `STD:program` 3 |
| H3 | Safety officer | active | 80 | 3 | 28 | 10 | 1 | 12 | 26 | `STD:operations` 20, `SKILL:review-test-safety` 9, `KNOW:battery-procedure` 5 |
| I1 | Procurement / BOM engineer | active | 48 | 2 | 7 | 5 | 10 | 4 | 20 | `SCORECARD:discipline-sign-off` 8, `STD:program` 7, `KNOW:procurement-lead-times` 4 |
| I2 | Schedule planner | active | 29 | 8 | 1 | 0 | 2 | 1 | 17 | `GATE:T8.program` 7, `SCORECARD:discipline-sign-off` 2, `STD:program` 1 |
| J1 | Outside research analyst | active | 45 | 0 | 6 | 9 | 1 | 1 | 28 | `SKILL:review-controls` 4, `STD:design-standards` 3, `SKILL:review-aero` 3 |
| J2 | Verification / proof-chain engineer | active | 22 | 14 | 0 | 0 | 0 | 0 | 8 | `GATE:T9.claims` 9, `GATE:T0.schema` 5 |
| J3 | Technical illustrator | active | 24 | 1 | 0 | 0 | 0 | 0 | 23 | `GATE:T7.assembly` 1 |
| J4 | Visual designer | active | 22 | 0 | 0 | 0 | 3 | 0 | 19 | `SCORECARD:evidence-and-closure` 3 |
| J5 | Technical writer / documentation | active | 20 | 1 | 0 | 1 | 1 | 2 | 15 | `KNOW:build-sequence` 2, `SKILL:review-test-safety` 1, `SCORECARD:evidence-and-closure` 1 |
| J6 | Design review board | active | 35 | 1 | 10 | 0 | 11 | 0 | 13 | `SCORECARD:evidence-and-closure` 7, `STD:design-standards` 7, `SCORECARD:discipline-sign-off` 4 |

## 2. Spec: what v1.0 is

### 2.1 Today vs v1.0 ("100x" as measured targets)

| Measure | Today (`f462468`) | v1.0 target, checked on 2026-11-30 |
|---|---|---|
| Team tasks doable with no code edit (R7 list, 12 tasks) | 3 (validate, export, import) | 12 / 12, each with a test in `tests/test_team_tasks.py` |
| Ways to call one operation | 3 hand-written (CLI, MCP, Studio API), drift-prone | 1 registry; CLI, MCP, Studio generated (`tests/test_surfaces_in_sync.py`) |
| Interfaces a human opens | viewer, Studio, OpenCAE Studio, whiteboard, artifacts | 1 app (`plane studio`, also on Pages read-only) + CLI |
| Gates | tiers 0–5 | tiers 0–9 (adds mechanisms, integration, sourcing, claims) |
| Thresholds `source: pending` among blocking checks | 2 (`landing_load_factor`, `hover_thrust_to_weight_min`) | 0 blocking-pending, or each named as a decision for the team |
| What a design can describe | geometry, joints, mass, flight | + files manifest, BOM, wiring, mechanisms, transport, provenance |
| Agent rules | `standards/agents.md`, advisory | roster + hooks enforce role choice, prompt ledger, stop gate, compaction re-inject |
| Before-meeting status | memory | `plane ledger report` + `plane update publish` |
| Iteration loop (change one number → scorecard) | edit YAML by hand, rerun | `plane design set … && plane design validate --json`; target ≤ 60 s for tiers 0–5 on concept-a excluding FEA (measured in U4.1) |

### 2.2 Layers (R3)

```
 Natural language   skills/ (design-iterate, review-design, recon, plan-scheme, get-it-together, weekly-update, …)
        │ call
 Surfaces           plane CLI ── plane-mcp ── Plane Studio (/api/op/<name>)     ← all generated from the registry
        │ call
 Operations (API)   core/hangar/ops/   @op("design.set") → OpResult  ← the only place behaviour lives
        │ use
 Engines            gates/ (tiers 0–8)   adapters/ (OpenCAE, MuJoCo, AeroSandbox, DaVinci)   ledger/   bench/
        │ read/write
 Data               designs/<id>/plane.yaml (PDL 1.0) + files   standards/*.yaml   knowledge/   ledger/   updates/
```

### 2.3 Plane Design Language (PDL) v1.0 (R1, R12, R14)

PDL is `schema/plane.schema.json` plus its generated reference `docs/pdl/reference.md`. v1.0 keeps every v0.4 field and adds (all optional, so old files stay valid after `design migrate`):

| Block | Fields | Why |
|---|---|---|
| `files` | `cad: [{path, format: step\|f3d\|stl\|glb, role: source\|derived}]`, `drawings`, `photos` | "CAD files go here" |
| `bom` | `items: [{id, component_ids, part_number, supplier, url, qty, unit_cost_usd, mass_g, verified: {by, date, method: browser\|datasheet\|in-hand, evidence}}]` | real parts, cost gate |
| `wiring` | `harnesses: [{id, from, to, route: [component ids], gauge_awg, exposed_ok: {reason}}]` | no exposed wires |
| `mechanisms` | `[{id, driver: attachment id, driven: [attachment ids], input_range_deg, expect: [{attachment, ratio}]}]` | "pull this, does it pull that" |
| `transport` | `box_mm: [l,w,h]` in `requirements`; `disassembly: [{group, component_ids}]` | car transport |
| `assembly` | `sequence: [{step, add: [component ids], tool, note}]` | animated assembly self-check |
| `provenance` | per component `mass_source: measured\|cad\|datasheet\|estimate`, `geometry_source` | tells real numbers from plausible ones |
| `changelog` | `designs/<id>/CHANGELOG.yaml` (separate file): `{date, by, op, path, from, to, kind: add\|subtract\|modify, why}` | subtraction bias visible (R15) |

Naming: the language is called **PDL** in docs; the file stays `plane.yaml` (decision D1 can rename).

### 2.4 CLI command tree (R2, R7, R8)

`plane <group> <verb>`; every verb takes `--json`. Groups and the team task each one closes:

| Group | Verbs | Team task (R7) |
|---|---|---|
| `design` | `list, new, copy, get, set, diff, migrate, validate, mass, export, sweep, propose` | send a design, change one parameter, compare, propose a PR |
| `gate` | `list, explain <check_id>` | know why something failed |
| `standards` | `list, show <key>, pending` | the bar |
| `tools` | `doctor` | what's installed |
| `fea` | `plan, run` (adapter `opencae`) | stress check |
| `sim` | `drop, mechanism` (adapter `mujoco`) | physics |
| `bom` | `verify, cost` (`list`: v1.1, D45) | real parts |
| `assembly` | `animate` | assembly test |
| `morph` | `add-option, coverage` (`list`: v1.1, D45) | morphological chart |
| `idea` | `add` (`list`: v1.1, D45) | send an idea |
| `research` | `new, check` | research into templates |
| `ledger` | `add, ingest, set, check, report` | tasks from meetings |
| `update` | `new, add, publish` | weekly update |
| `bench` | `list, run, report` | PlaneBench |
| `claim` | `list, explain, check` | why a number is believed |
| `davinci` | `push, pull`: v1.1 (D3, D45) | DaVinci build (D3) |
| `ops` | `list` | agents discover what exists |

### 2.5 Gates (R10–R13, R17)

Gates are registered in `standards/gates.yaml` (`id, tier, blocking, needs: [adapter], criterion`) and implemented under `core/hangar/gates/`. New:

- **T6 Mechanisms** (MuJoCo, rigid, frictionless, gravity off): drive each `mechanisms[].driver` through `input_range_deg` in 1° steps; each `expect` follower must move by `ratio × input` within `mechanism_ratio_tol` ; no unattached contact beyond `geometry.interference_max_mm3`; every articulated joint not covered by a mechanism is a WARN "undriven joint".
- **T7 Integration**: wiring (each harness segment between consecutive `route` components must lie inside the union of their envelopes + `wire_clearance_mm`, else FAIL unless `exposed_ok`); transport (each `disassembly` group's OBB fits `requirements.transport_box_mm`); assembly (every component appears exactly once in `assembly.sequence`, each added part touches an already-placed part).
- **T8 Sourcing**: every component with `manufacturing.method: buy` has a BOM line; every line `verified` within `bom_verified_max_age_days`; `Σ qty × unit_cost_usd ≤ requirements.budget_usd`.
- **T9 Claims** (U1.5): every claim in `claims.yaml` recomputes from PDL values; negative margin = FAIL; a claim with no calculation stays PROPOSED (SKIP), so it can't be passed by assertion.
- **Program constraints** (`standards/program.yaml`): budget, mass cap, transport, schedule apply to every active design without being copied into it.
- **Fidelity line** on every scorecard: "N of M blocking checks use sourced thresholds; K components have measured mass." Not a gate; it shows how real the PASS is.

### 2.6 Harness (R18–R24, R35)

- `.claude/agents/` the 10-role roster (§5), each file names model, tools, inputs, outputs, stop rules.
- `.claude/settings.json` hooks → `sh harness/hooks/run.sh <hook>` (the launcher picks the first Python 3 on PATH: `python3`, `python` or `py`):
  - `UserPromptSubmit` → `log_prompt.py`: append prompt to `ledger/prompts.jsonl` with status `open`; tells Claude its id.
  - `PreToolUse` (matcher `Task|Agent`) → `agent_gate.py`: block (exit 2) unless `subagent_type` is in the roster **and** in an agent table (a table with a `Pass criterion` column) of the newest plan; builders also need a builder-ready brief. The message lists the roster.
  - `SessionStart` (every source) → `reinject.py`: always one pointer line; after `compact`/`resume`, open prompts + the plan's unfinished units.
  - `Stop` → `stop_gate.py`: block if any prompt in this session is still `open`. Claude closes each with `ledger.py addressed P-n --evidence …`, or `defer P-n --reason …` when it is waiting on the user. `HANGAR_ALLOW_STOP=1` overrides; after 3 blocks in a row the stop goes through and a `stop-forced` event is logged for the auditor.
  - All hooks read and write UTF-8 (Windows consoles default to cp1252) and never raise: a hook bug cannot block the user.
- `.claude/output-styles/quiet.md`: answers questions fully; otherwise only results, decisions needed and blockers, at most five lines at the end of a task.
- `harness/install.py --target <project folder>`: copies agents, hooks, output style, merges settings, adds the ledger files to `.gitignore`; idempotent; refuses the home folder (a user-level install would call scripts that other projects don't have). (R24, D4.)

### 2.7 One surface (R6, R11, R26, R28)

`plane studio` (local, editable) and the Pages build (read-only) are the same app with modes: **Designs** (3D + scorecard, vendor link per part), **Compare**, **Build** (assembly sequence, animated), **BOM**, **Proofs** (claim chains), **Physics** (MuJoCo replay of drop + mechanism sweep; drag parts frictionless), **Stress** (FEA results — replaces the separate OpenCAE dashboard), **Morph chart**, **Knowledge**, **Ledger**, **Updates** (this week's per-person links). `viewer/app.js` and `viewer/studio.js` merge into one bundle; the old viewer page is deleted.

## 3. Decisions the team must make (surface now, R22)

Each has a default the plan uses if nobody answers by the date. **Standing rule (Tristan, 2026-11-21): every decision takes its default at once; the conductor records it as decided and does not wait for approval. Tristan can overrule later.** Recorded with `plane ledger add --kind decision`.

| D | Question | Default if unanswered | Ask | By | Status |
|---|---|---|---|---|---|
| D1 | Name of the language: PDL? keep `plane.yaml`? | PDL, file stays `plane.yaml` | — | 11-21 | decided: default (Tristan, 2026-11-20) |
| D2 | Dec 2 meeting: who is the audience (Douglas only, Kosa, class?), live demo or recorded, length? | Douglas + Kosa, 10-min live demo + Slides deck, recorded backup | Douglas | 11-22 | decided: default (Tristan, 2026-11-20) |
| D3 | DaVinci API: who has access, which account, is a Claude connector set up? | adapter ships as SKIP-with-reason; full DaVinci build moves to after Dec 1 | Douglas / Chris (Slack) | 11-23 | decided: default (Tristan, 2026-11-20) |
| D4 | Harness in hangar (`harness/`) or its own repo? | in hangar; `harness/install.py` installs it on any teammate's machine | — | 11-21 | decided: default (Tristan, 2026-11-20) |
| D5 | Transport box size and wiring clearance | box from DBF-Combined's constraint (K09-L box about 1.25 × 0.55 × 0.45 m) marked `source: team constraint`; clearance `pending` | Dillon | 11-24 | decided: default (Tristan, 2026-11-20) |
| D6 | Hover T/W 1.5 vs 2.0, landing factor 3.0 vs STANAG 3.8 (both `pending`); concept A's claims use T/W ≥ 1.6 | one value per key, chosen from sources found in U2.2, recorded as a decision | Dillon | 11-25 | decided: default (Tristan, 2026-11-20) |
| D7 | Does accepted require T6–T9 for v1.0, or report-only first? | T6 and T9 blocking; T7/T8 report-only (WARN) until 12-08 | — | 11-24 | decided: default (Tristan, 2026-11-20) |
| D8 | Binary files: Git LFS in hangar, or meshes stay in DBF-Combined and hangar stores `{repo, commit, path, sha256}` references? | LFS for the meshes the gates need (concept A, about 130 STL); CAD sources referenced, not copied | — | 11-21 | decided: default (Tristan, 2026-11-20) |
| D9 | Which design states are active? | concept A active; K09-L, C0 rev G, v0.3.1, tiltwing `retired` | Dillon | 11-22 | decided: default (Tristan, 2026-11-20) |
| D10 | Archive DBF-Combined and aircraft-platform (read-only) once hangar v1.0 is out? | yes, on 12-05, with a README pointer to hangar | team | 12-05 | decided: default, takes effect 12-05 (Tristan, 2026-11-21) |
| D11 | Who turns an unknown component type into a SKIP instead of a T0.schema FAIL (Review Focus #1)? | U2.1 (gate registry); schema stays strict until then | Tristan | 11-21 | decided: U2.1 (Tristan, 2026-11-21) |
| D12 | Does U1.3 migrate the committed designs (§7 U1.3 step 3)? | no: a designs-only PR after U1.3 migrates the designs whose results don't hash plane.yaml; concept-a stays at 0.4 until its FEA is re-run (fea.py hashes plane.yaml) | Tristan | 11-21 | decided: default (Tristan, 2026-11-21) |
| D13 | FEA part hashes include all of `standards/design-standards.yaml`, so any standards edit (e.g. U2.2 closing a pending source) makes every FEA result stale | U2.3 narrows `fea.part_hash` to the standards keys FEA reads; existing results re-hashed once from unchanged inputs | Tristan | 11-21 | decided: default (Tristan, 2026-11-21) |
| D14 | May a design carry executable calcs (`designs/<id>/calcs.py`)? | no: calcs live only in `core/hangar/calcs/`; claims reference them by registered name; designs stay data | Tristan | 11-21 | decided: default (Tristan, 2026-11-21) |
| D15 | T6 mechanisms: MuJoCo simulation or analytic check? | analytic: follower angle = clamp(ratio × input, range_deg), trimesh interference, `needs: []` (same verdicts, no MuJoCo tuning) | Tristan | 11-21 | decided: default (Tristan, 2026-11-21) |
| D16 | Should concept-A's claims react to `plane design set`? | yes: U2.5b `PDL_MAP` maps params-A refs to PDL paths (unit scaling allowed, e.g. MTOW) | Tristan | 11-21 | decided: default (Tristan, 2026-11-21) |
| D17 | DBF-Combined DECISIONS.md items on import | DD-1, DD-13, DD-14 `superseded` (decided_in D9); the other 12 `open` for triage | Tristan | 11-21 | decided: default (Tristan, 2026-11-21) |
| D18 | FEA staleness when concept-A is edited (U3.4) | U2.3a hashes every input the load model reads (all masses, geometry, propulsion, attachments, root, VTOL method, all mesh bytes) instead of the whole plane.yaml; requirements, flight, description edits keep FEA fresh; physical edits correctly make it stale | Tristan | 11-21 | decided: default (Tristan, 2026-11-21) |
| D19 | §1c proposes 367 standards keys (after the re-tag pass) from the role checklists; how many become `standards/*.yaml` entries? | only keys a gate or a discipline skill reads, each with `source:` or `pending` (estimate ≤ 80); the rest stay in the extracts as evidence | Tristan | 11-24 | decided: default (standing rule, 2026-11-21) |
| D20 | Discipline gates: five (thermal and modal as skill items + T9 claims) or seven (those two SKIP-only)? | five, in U3.6, report-only until 12-08 (D7); cut first if W3 slips (§6a 0a) | Tristan | 11-24 | decided: default (standing rule, 2026-11-21) |
| D21 | May U3.6 add optional PDL fields the gates need (battery capacity, wire gauge, current ratings, control-surface data)? | yes: optional fields in a schema minor version, merged with a `migration:` commit line; concept-a's values set later with `plane design set` | Tristan | 11-24 | decided: default (standing rule, 2026-11-21) |
| D22 | After D7's 12-08 flip, does `T8.program.budget` SKIP ("no BOM") block acceptance of designs without a BOM? | no: the budget row stays report-only until a design has a `bom` block; then it blocks | Tristan | 12-07 | decided: default (standing rule, 2026-11-21) |
| D23 | No unit owns `plane sim drop` (team task run_physics skips forever) | W2-S: a small `ops/sim.py` with `sim.drop` wrapping the existing drop simulation (no `sim.py` edits), after U2.3b merges; unskips run_physics and fixes its skip text | conductor | 11-22 | decided: default (standing rule, 2026-11-21) |
| D27 | U2.2-2: add `knowledge/TEMPLATE-concept.md` for concept and research entries? | yes (no existing template fits) | Tristan | 11-22 | decided: default (standing rule, 2026-11-21) |
| D28 | U2.2-2: import DBF-Combined `docs/research/` (23 files) now? | no: follow-up brief U2.2-3, home v1.1 | Tristan | 11-22 | decided: default (standing rule, 2026-11-21) |
| D29 | U2.2-2: how entries link to morph-chart cells | fixed code-mapping table; L6, L8 approximate and flagged | Tristan | 11-22 | decided: default (standing rule, 2026-11-21) |
| D31 | T2: James's harness-install run before Dec 2? | U4.1 until 11-29; else the CI install test is the evidence, the tester run moves to v1.1, and the slides make no teammate-machine claim | Tristan | 11-29 | decided: default (standing rule, 2026-11-21) |
| D32 | T12: mass gate 2.6 vs 2.7 kg and the other conflicting standards keys | v1.1; keys stay `pending`; slides quote no mass-gate number | Tristan | 11-26 | decided: default (standing rule, 2026-11-21) |
| D33 | T24: U2.5d concept-a re-import cannot land before the 11-30 freeze | v1.1 unit written into §7 by 11-25; R1, R12, R14, R17, R31 shown as open gaps on Dec 2 | Tristan | 11-25 | decided: default (standing rule, 2026-11-21) (2026-11-23: R31 later closed by T72, D53) |
| D34 | T28: port the 40 `read_value` echo functions or mark them stored evidence? | v1.1; the 40 claims stay SKIP and are named on the metrics slide as not recomputed | Tristan | 11-27 | decided: default (standing rule, 2026-11-21) |
| D35 | T40: run the U2.2-2 knowledge import in v1.0? | v1.1 (not demo-blocking); launched earlier only if W4 has a free slot | Tristan | 11-24 | overruled by Tristan 2026-11-22 (D42): run now |
| D36 | T9: SITL and collide.py adapters, open or dropped (§6a cut 5)? | open, v1.1 | Tristan | 11-27 | decided: default (standing rule, 2026-11-21) |
| D37 | T21: exit code for SKIP across ops | exit 0, status SKIP in the OpResult, SKIP prefix in human output; v1.1 | Tristan | 11-27 | decided: default (standing rule, 2026-11-21) |
| D39 | W4c: what does `test_concept_a_d21_on_disk` assert once concept-a has D21 data? | that each discipline gate reads the fields set (no "missing" SKIP), not that concept-a passes; test-only unit before the data commit | Tristan | 11-22 | decided: default (standing rule, 2026-11-22) |
| D40 | W4c: gate-only propulsion keys stale all 28 FEA results (G1) | fix the FEA hash keys first (FEA reads only axis and max_thrust_n); no re-run | Tristan | 11-22 | decided: default (standing rule, 2026-11-22) |
| D41 | W4c: hrn-bat `exposed_ok` and the 14 AWG harness FAIL | `exposed_ok` unset (no source); FAIL kept as a real finding (T60), report-only | Tristan | 11-22 | decided: default (standing rule, 2026-11-22) |
| D43 | R11 "drag the drone around" (interactive physics in Studio) for v1.0? | no: v1.1; v1.0 covers R11 with analytic T6 and Physics mode; R11 reopened | Tristan | 11-24 | decided: default (standing rule, 2026-11-22) |
| D44 | Studio Knowledge mode in v1.0? | no: v1.1; knowledge stays readable as files and on Pages | Tristan | 11-24 | decided: default (standing rule, 2026-11-22) |
| D45 | §2.4 lists `bom list`, `morph list`, `idea list`, `davinci push/pull`, which are not registered | amend §2.4 to the registered ops; the missing verbs are v1.1 | Tristan | 11-24 | decided: default (standing rule, 2026-11-22) |
| D46 | Dec 2 demo: live propose, which update week, which design, who records the backup | show PR #3; publish the 11-30 week merged before the demo; example template then concept-a for Physics; Tristan records the backup at the dry run; Studio launched 15 min early | Tristan | 11-30 | decided: default (standing rule, 2026-11-22) |
| D48 | U2.5d schema gaps (BOM description, CAD .py), spares in qty, R12/R14 closure with remaining FAILs and unverified lines, CHANGELOG replay | keep part_number/notes; qty with spares; close R12/R14 as data gaps, the rest become tasks; append the replay (history kept) | Tristan | 11-25 | decided: default (standing rule, 2026-11-22) |
| D50 | Should `T2.joint_rf` use per-joint ratings, including derived ones (estimated bond strength)? | yes: joint rating when not placeholder, else library; derived ratings reported as pending | Tristan | 11-24 | decided: default (standing rule, 2026-11-23) |
| D51 | Who approves briefs and decisions overnight 2026-11-23? | the conductor; U2.5d-pre-gates approved as written | Tristan | 11-23 | decided (Tristan, P165, 2026-11-23) |
| D52 | U5.1: build T28 (register `read_value`, 40 claims SKIP→PASS) tonight? | no: D34 stands (v1.1); brief `U5.1-t28.md` kept ready; deck line 140 stays true | Tristan | 11-23 | decided (conductor under D51, 2026-11-23) |
| D53 | R31 after T72: is a step that adds only point-mass proxies allowed to be skipped? | yes: reported in `skipped`; a drawable part with no mesh still fails; R31 done (1563a97) | Tristan | 11-23 | decided (conductor under D51, 2026-11-23; W5-R flag) |
| D54 | T7: may Studio /api/op pass `out` paths and fea.setup executables? | no: refused outright (no Studio client sends them; /api/fea-setup is the Studio route); `design.new` template is a bare id; `ledger.seed` plan refused | Tristan | 11-23 | decided (conductor under D51, 2026-11-23; W7-R questions A, B) |
| D55 | T55: how is one entry of a one-line list appended or removed? | flags: `plane design set <path> --append X` / `--remove X`; remove matches by value | Tristan | 11-23 | decided (Tristan, P169, 2026-11-23) |
| D56 | T54: how does the bench grader stop direct edits to `designs/`? | replay: snapshot the design before the run, log every `plane` command, replay the log on a fresh copy; a `designs/` result that differs fails the run | Tristan | 11-23 | decided (Tristan, P169, 2026-11-23) |
| D57 | T60: 12 AWG or a lower peak current for concept-a hrn-bat? | 10 AWG (fix the design, not the threshold; amended from 12 AWG, which gives 55 A x 0.8 = 44.0 A < 44.8 A peak, W11-G; 10 AWG matches DBF-Combined D-64 pack leads); Dillon informed through T60 | Tristan | 11-23 | decided (conductor default, Tristan P175, 2026-11-23; amended same day) |
| D58 | T37: which yaw fix for T3.control_authority? | the advisor's pick (W11-A): fix (a), per-axis max moment at fixed total thrust (linprog), cant only; yaw below 1.5 is SKIP (would_be FAIL) because reaction torque is not modelled; fix (b) deferred to v1.1 (T95); concept-a pinwheel cant to the design team (T96) | Tristan | 11-23 | decided (conductor default per T37 triage, P175) |
| D59 | Build T28 (`read_value`, 40 concept-a claims) before Dec 2? | yes, overrules D52: build now; the deck and metrics lines saying "not recomputed" are updated with the measured result | Tristan | 11-23 | decided (Tristan, P182, 2026-11-23) |
| D60 | T28: PASS or a separate status for the 40 read_value (stored-result) claims? | PASS kept for v1.0; every report and the deck say 53 recomputed + 40 read from source and checked against limits (analyses not re-run); a read marker on PASS was built in v1.1 (T103, U7.4) | Tristan | 11-23 | decided (conductor default on W13-R follow-up, 2026-11-23) |
| D61 | When does concept-a get the T95 propulsion 1.1 data (spin, reaction torque)? | after Dec 2 and after T96, by a design-engineer who confirms motor letters against CAD; baseline accept in the same designs-only commit (T106) | Tristan | 11-24 | decided (conductor default on W17-T flag, 2026-11-24) |
| D62 | "D35, run the import now": which import? | the config-study import (D35/D42) already ran (dc8902a); run the deferred `docs/research/` import (D28, U2.2-3) now as U7.5 | Tristan | 11-24 | decided (Tristan P188; conductor reading, 2026-11-24) |
| D63 | Team workflow rules for the guide (W19-T O1-O11) | defaults in `briefs/U8.1-team-guide.md`: collaborators not forks; teammate changes by PR only; Tristan merges, Dillon approves design PRs; ledger task per teammate job; no conductor for teammates; hooks on; `std/<topic>` and `design/<id>/<slug>` branches; owner trailer kept; concept-a only via `design set` + PR; Python 3.12; only Tristan adds ledger items. The guide marks each as "confirm" | Tristan | 11-24 | decided (conductor defaults, 2026-11-24; to confirm when Tristan reads the guide) |
| D64 | Team guide: commands or conversation? Claude Code only, or Claude Desktop too? | conversation first: teammates ask Claude in plain words and Claude runs the plane CLI/MCP, then validates/tests per its agent role; two setups, Claude Code (full) and Claude Desktop + plane MCP (design work; `design.propose` opens the PR; CI tests); Desktop never edits through `save_design`; "tests" means design validation gates (P191), and people/roles are examples, so the guide is organised by task, not by person | Tristan | 11-24 | decided (Tristan P190, P191, 2026-11-24) |
| D65 | CI speed: which trade-offs? | none that drop coverage: 3 shards per OS, full validate on every main push and PR, ledger/PROGRESS-only commits run only the ledger and progress tests, cancel-in-progress only on std/** and PRs | Tristan | 11-25 | decided (conductor defaults on W20-T, 2026-11-25) |
| D66 | After U8.2: freeze, and lighter process? | yes (Tristan P198): freeze until Dec 2 except teammate fixes, sourcing, deck, process trim; light path for small text/docs and data-only design changes; full path for gates, bench, security, schema; teammates work from a named ledger task; built-in read-only subagents allowed (T112); plan archived and summarised | Tristan | 11-25 | decided (Tristan P198, 2026-11-25) |
| D67 | How to raise the fidelity of the gates? | source concept-a's connection-type ratings by joint count (64 SKIPs + 4 drop FAILs), datasheet > standard/test > team pull test, else pending; decide landing_load_factor; James reviews; track the fidelity line | Tristan | 11-25 | decided (Tristan P198, 2026-11-25) |
| D68 | U8.3: how to turn the 64 joint SKIPs into verdicts? | C now: source stresses into the library, landing_load_factor pending until the T113 drop test, SKIPs labelled honestly; B (per-joint contact area x stress) first in v1.1 (T114) | Tristan | 11-25 | decided (Tristan P199, 2026-11-25) |
| D69 | How does a teammate's full-path change run, and which built-ins pass the gate? | teammate builds on their branch, opens a PR, Tristan runs a fresh reviewer on it; data-only design changes = CI + Dillon, no reviewer agent; built-ins Explore, Plan, claude-code-guide pass the launch gate by exact name, and Write/Edit/NotebookEdit are refused inside any agent with those names (amended by Tristan P203 on W22-A advice; no agent-file scan) | Tristan | 11-23 | decided (conductor default on W22-R; amended Tristan P203, 2026-11-23) |
| D70 | Parametric geometry before Dec 2? | yes for G1 (kernel + PDL 1.2) and G2 (first generators), G5 if capacity; overrides the D66 freeze for this work only; demo = one parameter change regenerates geometry, mass and CG on a parametric copy of concept-a (any parameter); G3, G4, G6, G7 are v1.1 (T116-T119) | Tristan | 11-25 | decided (Tristan P200, 2026-11-25) |
| D71 | Overnight 11-24: who decides, what runs? | conductor decides and merges after fresh review + green CI (irreversible actions wait); U10.3 merges only if reviewed and green by Sun 11-29; 11-30 update drafted not published; idle time goes to audits and QOL improvements under D66 paths | Tristan | 11-24 | decided (Tristan P209, P210, 2026-11-24) |
| D72 | Deck: show R1, R12, R14, R17, R31 as open (D33)? | no: D33's premise is overtaken by the re-import (d24b6df); the deck shows ledger truth; T24, T54, T37 done | Tristan | 11-24 | decided (conductor under D71 on W24-R, 2026-11-24) |
| D73 | Merge U10.3 despite the tier-1 budget miss? | yes, relaxed budget: concept-a-param tier-1 validate up to ~70 s; demo and deck updated to the new FAIL counts and timing | Tristan | 11-24 | decided (Tristan P214, 2026-11-24) |
| D74 | Which mission do designs target? | the VTOL demonstrator brief in knowledge/; 'DBF' here is the capstone, not UC Berkeley's separate DBF competition team (T127 dropped) | Tristan | 11-24 | decided (Tristan P224, 2026-11-24) |
| D75 | Build T129 (parameter changes propagate to attached parts) before Dec 2? | yes; merge only if reviewed and green by Sun 11-29 12:00, else branch + roadmap slide | Tristan | 11-24 | decided (Tristan P226, 2026-11-24) |
| D76 | Shrinking span: what happens to the elevons? | variant A: the elevon chain moves inboard with the tip (1.0 mm centre gap at 820 mm); elevons sized from span plus a forward-flight control gate is v1.1 (T130) | Tristan | 11-24 | decided (Tristan P227, 2026-11-24) |
| D77 | Dec 2 demo: build an A400M RC model from a prompt? | yes: research, generators, real-parts BOM with matching 3D models, PR, Studio; checks general and selected by aircraft type; each design carries its own mission; cut rule Sun 11-29 12:00, fallback concept-a-param | Tristan | 11-24 | decided (Tristan P228, 2026-11-24) |
| D78 | Is the demo capability A400M-only? | no: any real aircraft (A400M, Cessna 172, ...); general research template, generator set and parts library; rehearsal on two unseen aircraft (A400M, Cessna 172) | Tristan | 11-24 | decided (Tristan P229, 2026-11-24) |
| D79 | U11.1: attached-part positions relative to the parent frame, or parameter expressions? | expressions resolved at regeneration; interference reported, never refused (W28-A design) | conductor | 11-24 | decided (default, 2026-11-24) |
| D81 | Speed up design set? | profile a span change, then a mesh cache for the interference step if the profile confirms the double build; nothing else before Dec 2 | Tristan | 11-24 | decided (Tristan P235, 2026-11-24) |
| D82 | Parts without vendor CAD? | dimension-accurate envelopes labelled representative for Dec 2; Tristan supplies real models for the demo's parts, agents swap them in with licence recorded | Tristan | 11-24 | decided (Tristan P236, 2026-11-24) |
| D83 | GrabCAD models can't go on GitHub: how do they show? | local git-ignored CAD overlay on team PCs only; committed parts keep envelopes + source URL + licence; never in CI, public viewer or committed GLB | Tristan | 11-24 | decided (Tristan P237, 2026-11-24) |
| D84 | Dillon's redesign/v1 concept-a vs hangar's edited concept-a? | Dillon's is the truth; he imports it as `concept-a-reborn` by PR with D-212..D-261 and a DaVinci reconnect record; hangar's edits not reapplied; DBF-Combined not archived yet | Tristan | 11-24 | decided (Tristan P263, 2026-11-24) |
| D85 | Mechanical fidelity of generated models (rolling wheels, kinematic linkages, non-clipping surfaces) for Dec 2? | no: post-Dec 2 milestone; Dec 2 shows recognisable geometry and real parts placed sensibly | Tristan | 11-24 | decided (Tristan P267, 2026-11-24) |
| D86 | What does the Dec 2 demo actually show (shape, live change, overlay, prompt)? | decided at the Mon 11-30 dry run; until then the demo-script defaults stay provisional and the work is: keep improving the any-aircraft flow as much as possible | Tristan | 11-25 | decided (Tristan P278, 2026-11-25) |
| D87 | Keep rehearsing the prompt flow? | no: rehearsals stop until 3D generation gives a model genuinely close to the real aircraft (real linkages, joints, parts, wires); mechanical fidelity (I2, D85) starts now as U16.1 instead of after Dec 2 | Tristan | 11-25 | decided (Tristan P279, 2026-11-25) |
| D88 | Source the gates? | yes: every threshold in standards/*.yaml that is `pending` or an internal/team convention gets an opened external source (or a derivation from sourced values, written out), else stays `pending` with the reason; ranked by how many blocking check rows it drives; designs fixed, not thresholds; baselines refreshed in designs-only commits | Tristan | 11-25 | decided (Tristan P281, 2026-11-25) |
| D89 | Use OpenCAE Studio's new `opencae` CLI (OpenCAEModel main, 11-24: mass, propulsion operating point and current margins, CalculiX structure, SU2/OpenFOAM whole-aircraft CFD, 6-DOF hover) for hangar's physics checks? | yes (default taken, conductor 11-25, Tristan P282 pointed at it): run it as an external GPL program through a hangar adapter (PDL -> drone.json + mesh, `opencae run --json` -> check rows); no OpenCAE source copied; SKIP where it is not installed (CI); CFD via SU2 lifts the plan section 8 'no CFD' line for this external route only | Tristan | 11-25 | decided (default, conductor 2026-11-25; Tristan P282; confirmed Tristan P289) |
| D90 | U16.1 showcase design and MJCF timing (design note u16.1/design-note.md)? | showcase = c172-rc (from rehearsal-4 PR #9), landed on main in a designs-only PR (S0); the kinematic MJCF export (S7) follows the Studio-visible steps and is not needed before Tristan judges D87 | Tristan | 11-25 | decided (default, conductor 2026-11-25; Tristan may change; confirmed Tristan P289) |
| D91 | U17.1 inventory findings: 518 blocking rows (481 T4 manufacturing, 27 schema, 8 mtow, 2 connection types) have criteria that resolve to no threshold, and the fidelity count treats any source text but `pending`/`internal convention` as sourced | (a) add a core step to U17.1 that links those criteria to real keys so they count; (b) a `team constraint` counts as sourced only with a named owner and date (D88); scouts run packets 1, 6, 7, 2, 3, 4, 5, then 8, 9 | Tristan | 11-25 | decided (default, conductor 2026-11-25; confirmed Tristan P289) |
| D92 | Studio UI overhaul with a much better 3D viewer? | yes (Tristan P285, 2026-11-25): new wave W19; recon of best-in-class web CAD/model viewers, then an advisor-led UI spec, then briefs; the viewer must show U16.1's moving linkages, wheels and wires; no GrabCAD geometry in published builds (D83) | Tristan | 11-25 | decided (Tristan P285, 2026-11-25) |
| D93 | U18.1 study decisions (u18.1/study.md section 7) | (1) missing OpenCAE inputs (motor kv/R/i0, prop data, battery IR, ESC, material E/nu/yield) go in a sidecar `designs/<id>/opencae-inputs.yaml`, no PDL bump; (2) a pass on estimated inputs stays PASS with `; OpenCAE basis estimate` appended; (3) four provisional thresholds in operations.yaml with `source: pending` (U17.1 sources them); (4) brief -3 stops if a key- or id-enumerating test fails; SU2 download and pip install approved by Tristan (P287); the conductor's `opencae setup su2 --yes` was blocked by the session's permission classifier, Tristan ran it himself (P289) | Tristan | 11-25 | decided (default, conductor 2026-11-25; installs approved Tristan P287; confirmed Tristan P289) |
| D94 | U18.2-U18.4 brief defaults (W34-T4, aec87ed) | C172S reference is a test fixture, not a design; AeroSandbox stays opt-in (not in pyproject or CI), dynamic modes SKIP without it; elevator travel is a standards default until a PDL elevator field (schema bump later); U18.4 reads declared lifting_surface tails only; tail-volume bands stay pending until a real source is opened (the in-repo MIT attribution is not in the MIT note) | Tristan | 11-25 | decided (default, conductor 2026-11-25; confirmed Tristan P289) |
| D95 | U19.1 spec decisions | three.js stays on the pinned CDN (spec default; vendoring into viewer/vendor is the fallback if the demo room has no network); Playwright installed locally in .venv (`pip install -e .[dev]`, `playwright install chromium`) as a brief step (installs approved, Tristan P287); U16.1 S9 drops its x-ray item (B3 covers it) | Tristan | 11-25 | decided (default, conductor 2026-11-25; confirmed Tristan P289) |
| D96 | U16.1 brief defaults (W34-T5, 52e43ea) | S1 jam = no root, transmission angle < 10 deg or follower step > 10 deg per deg (two new `pending` thresholds, FAIL rows); T1 pose sweeps keep rigid rods for now; S2 wheels stay type landing_gear; S3 servo frames are estimates and the c172 wing servos are report-only (wing ~14 mm thick vs 24 mm servo), tail servos are the acceptance; S4 arm 6 mm / horn 13 mm layout defaults; export-hash check on every design | Tristan | 11-25 | decided (default, conductor 2026-11-25; confirmed Tristan P289) |
| D97 | U19.1 brief decisions (W34-T6, 277de38) | B6 renames check-row keys (`pair` -> `unchecked_pairs` etc.) and refreshes concept-a and concept-a-param baselines in a second `migration:` commit with the `migration` label; joint rows resolve to parts through `parts.json` attachments (no check-row change); B5 adds two lines to edit.js; Physics tab folds into the timeline (B4); three pinned at 0.180.0 after a URL check | Tristan | 11-25 | decided (default, conductor 2026-11-25; confirmed Tristan P289) |
| D98 | OpenCAE export: how are `pending` standards values and built-in defaults (air density 1.225) tagged in drone.json? (W34-R section 4) | as `estimate`, never `user`: an unsourced number may not support an OpenCAE pass; done in U18.1-3 together with the rows | Tristan | 11-25 | decided (default, conductor 2026-11-25; confirmed Tristan P289) |
| D99 | How many agents at once? | at most 2 builders and 1 reviewer running at a time (Tristan P290, PC load); no new builder until two are running or fewer; W34-R finishes its current branch and stops, W34-R2 takes every later review and re-review | Tristan | 11-25 | superseded by Tristan P291 (2026-11-25): cap lifted while he is away; launch by free RAM (two reviewers, builders as memory allows) |
| D100 | U17.1 step 2b briefs (e6c36eb): owners and relabelling | criteria brief builds now (+516 rows resolve, statuses unchanged); team-owner Part 1 builds after values merges with owner Tristan, date 2026-11-25 as a placeholder owner that Tristan confirms; Part 2 (relabel 7 `internal convention` values as team decisions, +51) is NOT built until Tristan decides each value himself, because an agent may not create a team decision; schema/mtow/connection keys stay `pending` | Tristan | 11-25 | decided (default, conductor 2026-11-25) |
| D101 | U16.1 S6-S9 brief defaults (11653fa) | S6 ships hinge_style none/bevel (round deferred); S7 kinematic MJCF with gravity 0, ball joint at the rod end + connect loop; S8 wires Catmull-Rom tubes 1.5 mm, visual-only, bend radius deferred, library ports labelled estimates; S9 clevis/screw-head drawing rules (not standards) behind an opt-in `display` block; S9c hollow fuselage changes mass/CG so its showcase opt-in waits for Tristan | Tristan | 11-25 | decided (default, conductor 2026-11-25) |
| D102 | U15.3: `design get/set` on generator designs still load trimesh because loading computes mass_g by building meshes | accept U15.3 as lazy imports only (`plane --help` 8.8 -> 3.5 s, outputs byte-identical); test 2 uses concept-a; a follow-up step U15.3-2 makes mass_g lazy (computed on first use) so get/set on parametric designs skip mesh building | Tristan | 11-25 | decided (default, conductor 2026-11-25) |

Ruling 2026-11-20 (Tristan): D1–D9 take the default above; D10 is decided once v1.0 is done.

## 4. How we execute (superpowers + scheme)

The superpowers pipeline, mapped to this repo:

| Superpowers stage | Here | Who |
|---|---|---|
| brainstorming → spec | §1–§3 of this file (done 11-20) | conductor (Opus, max effort) |
| writing-plans | §6 units (this file) | conductor |
| using-git-worktrees | one worktree per unit: `/home/claude/wt/<unit>` or `../wt/<unit>` on laptops; branch `std/<unit>` off `main` | conductor |
| subagent-driven-development | per unit: implementer (builder or builder-plus) → spec check (tactician) → code-quality check; per wave: fresh **reviewer** on all of the wave's PRs | §5 roster |
| test-driven-development | every step pair "write failing test → make it pass" below | builders |
| systematic-debugging | a unit that fails review twice goes to **advisor**, not a third fix (R21) | conductor |
| requesting-code-review | wave review with `standards/review-scorecard.md` | reviewer |
| verification-before-completion | `pytest -q && plane baseline check --all && plane ledger check` pasted in the PR | implementer |
| finishing-a-development-branch | PR → wave review → merge to `main` by Tristan | Tristan |

Scheme rules on top (R22, R25):
- **Waves** are dependency layers; units inside a wave run in parallel.
- **Unit = one PR.** If a unit's PR is rejected, the same unit is reopened and fixed; no "fix-for-the-fix" unit.
- **Plan is the source of truth**, not the conductor's memory. Agents get the unit text from this file, not a paraphrase. Status changes are checkbox edits here + `plane ledger set`.
- **Brief vs §7**: Where the brief and plan §7 differ, the brief governs; the tactician records the difference in Plan coverage.
- **Design work goes through PRs too**: several agents/people may open `design.propose` PRs on the same design; Tristan merges (Dillon approves concept-a changes, R25).
- **Hourly audit** while a wave runs: `auditor` (Haiku) runs the `get-it-together` skill and reports to the conductor (R21). Scheduled as a looping prompt / scheduled task during long runs.
- **Permissions up front**: before a wave, the conductor posts one prompt listing every command and folder the wave needs, so no agent stalls on a permission check mid-run.

## 5. Agents (the 10-role roster)

Defined in `.claude/agents/<name>.md`. Roles are by **work type and level**, not by aircraft domain (R18). Subagents can't launch subagents, so the conductor launches everything and the tactician works in briefing mode (writes briefs to `plans/2026-11-20-standardization/briefs/`).

| Agent | Model | Work | Never |
|---|---|---|---|
| `conductor` | Opus (main session) | owns the plan, launches agents, merges decisions, the only one who declares a unit done | writes code or bulk text itself |
| `advisor` | Opus | "this works/doesn't, but does it match intent? what should it do and how do we get there?"; called on any unit that failed twice | edits files |
| `tactician` | Sonnet (hard → Opus via `advisor`) | turns one unit into builder-ready briefs; checks a finished unit against its spec | design decisions that belong to the conductor |
| `builder` | Haiku | one brief: exact files, exact test, exact command | guesses; stops and reports on ambiguity |
| `builder-plus` | Sonnet | same as builder for units marked **hard** | — |
| `scout` | Haiku | facts into `knowledge/TEMPLATE-*.md` and ledger extracts from transcripts | opinions outside the template |
| `recon` | Sonnet | "how have others solved this?" — benchmarks 3–5 approaches, sends scouts' results back as a ranked recommendation | builds the chosen approach |
| `design-engineer` | Sonnet | iterates a design using **only** `plane …` commands; considers subtract / modify / adjust before add | edits `core/`, `schema/`, `standards/` |
| `reviewer` | Opus, **fresh per wave**, reused within the wave | runs validators + tests, scores every PR of the wave against spec + scorecard | "looks good" without a criterion |
| `auditor` | Haiku | hourly get-it-together audit: open prompts, rule breaks, stuck agents (> 2 failed fixes or > 45 min no progress), plan drift | fixes anything |

Work-class rule: easy → builder (Haiku); hard → builder-plus (Sonnet). Tactician easy → Sonnet; hard → escalate via advisor (Opus). A unit is **hard** when it is marked **[hard]** below.

## 6. Schedule

| Wave | Dates (PT) | Units |
|---|---|---|
| W0 Seed, harness & ledger | Fri 11-20 (done 15:55; planned → Sat 11-21) | U0.4 first, then U0.1, U0.2, U0.3 in parallel |
| W1 Ops layer & PDL | Fri 11-20 16:45 → 20:13 (planned Sat 11-21 → Mon 11-23) | U1.1 [hard], U1.2, U1.3 [hard], U1.4, U1.5 [hard], U1.6 |
| W2 Gates, adapters, import, team ops | Fri 11-20 20:13 → 23:17 (planned Mon 11-23 → Wed 11-25) | U2.1 [hard], U2.2, U2.3 [hard], U2.4, U2.5 [hard] |
| — async check-in (no meeting) | Wed 11-25 | `plane update publish` → link in the Drive doc |
| W3 One surface, skills, proof | Fri 11-20 23:17 → Sat 11-21 20:22 (planned Wed 11-25 → Sat 11-28) | U3.1 [hard], U3.2, U3.3, U3.4, U3.5, U3.6 [hard] |
| Freeze | Mon 11-30 18:00 | — |
| W4 Whole-branch review and release prep | Sat 11-21 → Sun 11-22 | U4.1 |
| W5 Overnight core fixes | Sun 11-22 → Mon 11-23 | U5.1, U5.2, U5.3, U5.4, U5.5 |
| W6 Hardening and v1.1 batch 1 | Mon 11-23 | U6.1, U6.2, U6.3, U6.4 |
| W7 Dec 2 prep, BOM, v1.1 batch 2, research import | Mon 11-23 | U7.1, U7.2, U7.3, U7.4, U7.5 |
| W8 Team adoption, CI, ratings, process | Mon 11-23 → Tue 11-24 | U8.1, U8.2, U8.3, U8.4 |
| W9 Parametric geometry for the demo (D70) | Tue 11-24 | U9.1, U9.2 |
| W10 Freeze fixes and fresh-session findings | Tue 11-24 | U10.1, U10.2, U10.4, U10.5, U10.6 |
| W11 Parameter propagation and speed (D75, D81) | Tue 11-24 | U11.1, U11.2 |
| W12 Any-aircraft capabilities (D77-D79, D82, D83) | Tue 11-24 → Wed 11-25 | U12.1, U12.2, U12.3, U12.4, U12.5 |
| W13 Rehearsal gaps and visual fidelity | Tue 11-24 → Sat 11-28 18:00 | U13.1, U13.2, U13.3, U13.4, U13.5, U13.6, U13.7, U13.8 |
| W14 Presentation | Mon 11-30 → Wed 12-02 | U14.1 |
| W15 Authoring gaps and speed (D86) | Wed 11-25 → Sat 11-28 | U15.1 [hard], U15.2, U15.3 [hard] |
| W16 3D generation close to the real aircraft (D85, D87) | Wed 11-25 → after Dec 2 | U16.1 [hard], U16.2 [hard] |
| W17 Sourced gates (D88) | Wed 11-25 → Sun 11-29 | U17.1 |
| W18 Physics checks (D89) | Wed 11-25 → after Dec 2 | U18.1 [hard], U18.2, U18.3, U18.4 [hard] |
| W19 Studio UI and 3D viewer (D92) | Wed 11-25 → after Dec 2 | U19.1 [hard] |
| Present | **Wed 12-02** | demo + deck |

**Unit ids by wave (Tue 11-24, Tristan P271):** units are numbered by the wave they run in (U5.x in W5 ... U14.x in W14). Briefs, branches, reviews, commits and code comments written before this change keep the old U4.x names; this table maps them.

| old | new |
|---|---|
| U4.2 | U14.1 |
| U4.3 | U5.1 |
| U4.4 | U5.2 |
| U4.5 | U5.3 |
| U4.6 | U5.4 |
| U4.7 | U5.5 |
| U4.8 | U6.1 |
| U4.9 | U6.2 |
| U4.10 | U6.3 |
| U4.11 | U6.4 |
| U4.12 | U7.1 |
| U4.13 | U7.2 |
| U4.14 | U7.3 |
| U4.15 | U7.4 |
| U4.16 | U7.5 |
| U4.17 | U8.1 |
| U4.18 | U8.2 |
| U4.19 | U8.3 |
| U4.20 | U8.4 |
| U4.21 | U9.1 |
| U4.22 | U9.2 |
| U4.23 | U10.1 |
| U4.24 | U10.2 |
| U4.25 | U10.3 |
| U4.26 | U10.4 |
| U4.27 | U10.5 |
| U4.28 | U10.6 |
| U4.29 | U11.1 |
| U4.30 | U12.1 |
| U4.31 | U12.2 |
| U4.32 | U12.3 |
| U4.33 | U12.4 |
| U4.34 | U13.1 |
| U4.35 | U11.2 |
| U4.36 | U13.2 |
| U4.37 | U13.3 |
| U4.38 | U12.5 |
| U4.39 | U13.4 |
| U4.40 | U13.5 |
| U4.41 | U13.6 |

**Wave names (Tue 11-24, Tristan P260/P261):** the former sub-waves W4.1-W4.7 are now W4-W9 and W14, and the later units are grouped as W10-W13; unit ids (U4.x) are unchanged so briefs, branches and commits still match. Agent ids such as W29-B are launch labels, not schedule waves.

**Revised schedule (Mon 11-23 22:45, conductor; W0-W3 finished early, see archive):**

| When | What | Cut rule |
|---|---|---|
| Tue 11-24 | merge U8.4 a, b, d; G1 brief -> G1 build starts; Tristan adds collaborators; Dillon's first real task (guide) | — |
| Wed 11-25 | async check-in: `plane update add` / `publish` (R26); G2 brief; G1 review | — |
| Thu 11-26 | Thanksgiving, light: G1 fixes | G1 not merged by Fri 11-27 18:00 -> no parametric demo, roadmap slide only |
| Fri 11-27 -> Sat 11-28 | G2 build + review; `concept-a-param`; deck reframed honestly (claims 53+40, fidelity 134/714, real findings first) | G2 not merged by Sun 11-29 12:00 -> demo G1 on one generated part |
| Sun 11-29 | T2 (James), T62 done; re-run demo script incl. the parametric step; record backup video | — |
| Mon 11-30 | freeze 18:00; dry run evening | after freeze: fix only what the dry run breaks |
| Tue 12-01 | fixes only | — |
| **Wed 12-02** | present | — |

*Status 11-24 early morning (audit W24-Au): ahead of this schedule. U8.4 merged 11-23; G1 (U9.1, 225c1b7) and G2 (U9.2, 49a1601 + a0ba030) merged 11-23, so both cut rules are met. Update 11-24 morning: U10.1 and U10.2 merged (6f3bc00, bdbfbd2); U10.3 parked for v1.1 (budget); U10.4 QOL batch running. Remaining: Tristan's items (collaborators, guide send, video Sun, dry run Mon).*

All units: Tristan. Acceptance testers: Dillon (Studio, concept A), Vaibhav (OpenCAE on Windows), James (harness install on his machine).

Ordering follows R17: T6 mechanisms lands before T8 sourcing; U3.4 (an agent iterating concept-a with no code edits) is the acceptance test of the whole plan.

---

### 6a. Core path and cut order (scope check, 2026-11-20)

The Dec 2 demo needs only the **core path**: U0.4 → U0.2/U0.3 → U1.1 → U1.3 → U1.4 → U1.5 → U2.5 → U3.4 (+ U4.1/U14.1). Everything else is in the cut order below, so a slip never threatens the demo. The conductor cuts from the top of this list as soon as a wave runs > 12 h late; a cut unit gets ledger status `dropped` with this section as `decided_in`.

| Cut order | Unit | What is lost if cut | Fallback for the demo |
|---|---|---|---|
| 0a | U3.6 discipline gates | five discipline checks | criteria stay as `review-*` skill items (U3.5) |
| 0b | U3.5 discipline skills, scorecard, procedures | discipline review checklists | §1c and the extracts remain the reference |
| 1 | U3.3 PlaneBench | model-comparison slide | show `design.sweep` table instead |
| 2 | U2.1 T7/T8 parts | wiring/transport/BOM gates | T7/T8 stay report-only via claims (U1.5 already has budget and mass claims) |
| 3 | U2.2 source closing | two `pending` thresholds | listed as open decisions D6 |
| 4 | U3.1 Build/BOM/Proofs/Morph modes | some Studio modes | Designs, Physics, Stress, Updates modes only |
| 5 | U2.3 blender/sitl/davinci adapters | optional adapters | `tools doctor` lists them as planned |
| 6 | U1.6 connection library | connection-type check | attachments keep v0.4 fields |
| never | core path units | — | — |

### 6b. Tester tasks, spread across the waves (R7, R9, R26)

Prepared by the conductor as a one-message task with exact commands; sent by Tristan.

| When | Tester | Task (≤ 20 min) | Evidence |
|---|---|---|---|
| Sat 11-21 | James | `python harness/install.py --target <his repo>`; launch any non-roster agent and confirm it is blocked | screenshot in ledger |
| Mon 11-23 | Dillon | `plane design set` one concept-A mass on a branch, `plane design validate`, `plane design propose` | PR link |
| Tue 11-24 | Vaibhav → Tristan (2026-11-21) | `plane tools doctor` + `plane fea run designs/concept-a --part <one>` on Windows | output pasted in ledger |
| Wed 11-25 | all | `plane update add` own line; Tristan runs `plane update publish` | the link |
| Fri 11-27 | Dillon → Tristan (2026-11-21; counts for R9 as an outside user) | one iteration in Plane Studio, no terminal (U3.4 step 4) | time taken |

### 6c. Agent table for W0-early (launched 2026-11-20, before U0.4)

The harness does not depend on the seed, so it goes first: rules must be enforced before the build agents run.

| Step | Role | Model | Input | Output | Pass criterion |
|---|---|---|---|---|---|
| H1 | `builder` | Haiku | `plans/2026-11-20-standardization/briefs/H1-ledger-and-session-hooks.md` | branch `std/h1-ledger-hooks` | `python -m pytest tests/harness -q` green |
| H2 | `builder` | Haiku | `plans/2026-11-20-standardization/briefs/H2-agent-gate-and-install.md` | branch `std/h2-agent-gate` | same |
| HR | `reviewer` | Opus (fresh) | both branches | `reviews/2026-11-20-w0-harness.md` | ACCEPT per branch |

### 6d. Agent table for W0 (prepared 2026-11-20; run from a fresh conductor session)

Order: W0-1 first; when it is merged, W0-2, W0-3 and W0-4 run in parallel, each in its own worktree; one fresh reviewer for the wave. `auditor` runs hourly while the wave runs; `advisor` only for a unit that fails review twice.

| Step | Role | Model | Input | Output | Pass criterion |
|---|---|---|---|---|---|
| W0-1 | `builder` | Haiku | `plans/2026-11-20-standardization/briefs/U0.4-seed.md` | branch `std/u0.4-seed` | `python -m pytest -q` → 168 + 31 passed, 3 skipped; `plane baseline check --all` exit 0 |
| W0-2 | `builder` | Haiku | `plans/2026-11-20-standardization/briefs/U0.1-roster.md` | branch `std/u0.1-roster` | `python -m pytest tests/test_roster.py -q` green, full suite green |
| W0-3 | `builder` | Haiku | `plans/2026-11-20-standardization/briefs/U0.3-ledger.md` | branch `std/u0.3-ledger` | `python -m pytest tests/test_ledger.py -q` green, full suite green |
| W0-4 | `builder` | Haiku | `plans/2026-11-20-standardization/briefs/U0.2-followups.md` | branch `std/u0.2-followups` | `python -m pytest tests/harness -q` green |
| W0-5 | `builder` | Haiku | the W0-5 prompt (CI: LFS checkout in both workflows, Windows job, CI on `std/**` pushes; added 2026-11-21 after the Pages build failed) | branch `std/w0.5-ci` | GitHub Actions `validate` green on Linux and Windows for the pushed branch |
| W0-6T | `tactician` | Sonnet | W0 lessons (reviews/2026-11-21-w0.md, conductor notes in briefs U0.4/U0.2) | `briefs/W0.6a-harness-fixes.md`, `briefs/W0.6b-brief-standard.md` | each brief meets the builder-ready bar in `standards/agents.md` |
| W0-6a | `builder` | Haiku | `briefs/W0.6a-harness-fixes.md` | branch `std/w0.6a-harness` | brief's pass check; CI `validate` green on Linux and Windows |
| W0-6b | `builder` | Haiku | `briefs/W0.6b-brief-standard.md` | branch `std/w0.6b-briefs` | brief's pass check; CI green |
| W0-6c | `builder` | Haiku | `briefs/W0.6c-roadmap-progress.md` (written by the W0-6T tactician) | branch `std/w0.6c-progress`: `ROADMAP.md`, generated `PROGRESS.md` via `plane progress`, CI staleness check | brief's pass check; CI green |
| W0-6R | `reviewer` | Opus (fresh) | the three W0.6 branches | `reviews/2026-11-21-w0.6.md` | ACCEPT per branch |
| W0-R | `reviewer` | Opus (fresh) | the four branches | `reviews/2026-11-21-w0.md` | ACCEPT per branch |
| W0-A | `auditor` | Haiku | session state, ledger, this table | report to conductor | ≤ 15 lines, evidence per finding |
| W0-X | `advisor` | Opus | a unit that failed review twice | recommendation | one dispatch recommended |

**Permissions for W0 (approve once at the start of the conductor session):** `git worktree add|remove` under `../wt/`; `git commit` on `std/*` branches; `git push` of `std/*` branches and of `main` after a reviewed merge (no force push); `git lfs track|install|push`; `pip install -e ".[mcp,dev]"` and `pip install pytest` into a virtual environment; `python -m pytest`; `plane …`; reading `../aircraft-platform` (at `f462468`). Nothing outside the repo, its worktrees and the read-only source checkout is written.

**LFS fallback (D8):** if `git push` of LFS objects is refused by the git host or proxy, the conductor removes the LFS patterns for meshes (they total about 5 MB) and commits them as plain git, and records "D8 amended: plain git" in §3. No builder handles this.

### 6e. Agent table for W1 (prepared 2026-11-21)

W1 runs in two layers, because the units depend on each other (§7 Interfaces):
- **W1a:** U1.1 [hard] and U1.3 [hard] in parallel. U1.3's `ops/schema.py` is written against U1.1's `@op` interface as fixed in §7. U1.1 merges first, then U1.3 rebases onto it before its final pass check. U1.3 does not edit `core/hangar/cli.py`.
- **W1b**, after W1a is merged (U1.2 needs only U1.1 and touches none of U1.3's files, so it starts once U1.1 is merged; conductor, 2026-11-21): U1.2, U1.4, U1.5 [hard] and U1.6 in parallel. U1.5 and U1.6 both edit `schema/plane.schema.json`; the second one to be accepted rebases before merging. U1.4's Windows CI job already exists (W0-5).
- Briefs follow the template in `standards/agents.md`. Each lists every §7 step in Plan coverage. Hard-unit briefs are drafted by a `tactician` and then checked by the `advisor` before any builder runs (§5: hard → Opus via advisor). Tristan reads the U1.1 and U1.3 briefs before their builders launch.
- Every commit that ticks a box, adds a verdict or changes the ledger also runs `plane progress --write` (W0.6c).
- Test runs (Tristan, 2026-11-21): builders run only their brief's targeted tests locally, then push; CI (Linux + Windows) is the one full-suite run. Reviewers judge CI's result and run targeted probes, not the full suite. Each agent writes logs only under its own worktree (e.g. `C:/Users/trist/wt/<unit>/.logs/`), never a shared scratch path.
- Reviewer notes carried into W1 briefs: the gate rejects worktree or space-containing brief paths unless the brief is inline (give repo-relative brief paths); `progress.py` repeats the ledger count table (U2.4 may unify it).

| Step | Role | Model | Input | Output | Pass criterion |
|---|---|---|---|---|---|
| W1-0 | `builder` | Haiku | inline brief: the progress rule in `.claude/agents/conductor.md` and CLAUDE.md; `gh` by full path and an absolute venv path in the brief template | branch `std/w1.0-rules` | `pytest -q` green, CLAUDE.md ≤ 25 lines, CI green |
| W1-T1 | `tactician` | Sonnet | §7 U1.1 | `briefs/U1.1-ops-registry.md` | builder-ready bar; Plan coverage complete |
| W1-T3 | `tactician` | Sonnet | §7 U1.3 | `briefs/U1.3-pdl.md` | same |
| W1-A1 | `advisor` | Opus | the U1.1 and U1.3 briefs | recommendation per brief | "builder-ready" or a numbered list of gaps |
| W1-1 | `builder-plus` | Sonnet | `briefs/U1.1-ops-registry.md` | branch `std/u1.1-ops` | brief's pass check; CI green on both OSes |
| W1-3 | `builder-plus` | Sonnet | `briefs/U1.3-pdl.md` | branch `std/u1.3-pdl` | same |
| W1-T2, T4, T6 | `tactician` | Sonnet | §7 U1.2, U1.4, U1.6, plus merged W1a code | `briefs/U1.2-surfaces.md`, `briefs/U1.4-edit.md`, `briefs/U1.6-interfaces.md` | builder-ready bar |
| W1-T5 | `tactician` | Sonnet | §7 U1.5, plus DBF-Combined @ `a93f14d` `redesign/proofs/` | `briefs/U1.5-claims.md` | same |
| W1-A2 | `advisor` | Opus | the U1.5 brief | recommendation | as W1-A1 |
| W1-2, W1-4, W1-6 | `builder` | Haiku | their briefs | branches `std/u1.2-surfaces`, `std/u1.4-edit`, `std/u1.6-interfaces` | brief's pass check; CI green |
| W1-5 | `builder-plus` | Sonnet | `briefs/U1.5-claims.md` | branch `std/u1.5-claims` | same |
| W1-M | `builder` | Haiku | inline brief after U1.3 merges: `plane design migrate designs/<id> --write` for every design except concept-a (D12); designs-only PR, no `core/` | branch `std/w1-migrate-designs` | `plane baseline check --all` exit 0; CI green |
| W1-P | `builder` | Haiku | inline brief after W1 merges: `pytest-xdist` (`-n auto`) locally and in CI; `@pytest.mark.slow` on MuJoCo/FEA/per-design tests (local default skips them, CI runs all); CI skips plans/reviews-only commits except a light `plane progress --check` job; `concurrency: cancel-in-progress` per branch; brief template in `standards/agents.md` gets the test-run and per-worktree log rules and a brief checklist of the advisor's recurring gaps (interface precision, no plan-file edits, no new entry points, hash-coupled files, no fixtures outside the repo); worktree venvs via `uv` | branch `std/w1-p-speed` | CI green on both OSes; full CI suite time reported before and after |
| W1-R | `reviewer` | Opus (fresh for W1, reused for W1a, W1b and re-reviews) | each branch as it lands | `reviews/2026-11-2x-w1.md` | "### Verdict: ACCEPT" per unit |
| W1-Au | `auditor` | Haiku | session state, ledger, this table | report to conductor, hourly | ≤ 15 lines, evidence per finding |
| W1-X | `advisor` | Opus | a unit that failed review twice | recommendation | one dispatch recommended |

**Permissions for W1 (approve once):** everything in §6d's W0 list, plus: `git push origin std/*` (CI runs on these branches); the GitHub CLI at `C:/Program Files/GitHub CLI/gh.exe` for `run list|view|watch` and `api` (read-only); `git push origin --delete std/*` for merged branches only; a read-only partial clone of `https://github.com/davinciucberkeley-collab/DBF-Combined` into `C:/Users/trist/DBF-Combined`, checked out at `a93f14d` (`git clone --filter=blob:none --sparse`, sparse to `redesign/`), used by U1.5 and U1.6; `pip install -e ".[mcp,dev]"` in worktree venvs, including new dependencies a brief names (e.g. `ruamel.yaml`), added to `pyproject.toml`; background `sleep 3600` timers that wake the conductor for the hourly audit.

### 6f. Agent table for W2 (briefs prepared during W1, 2026-11-21)

Speed rules (Tristan, 2026-11-21): the next wave's briefs are written while the current wave builds; each wave may use **one or two** fresh reviewers, each owning some units, and the second (or the only) reviewer checks the merge order of the whole wave; Tristan still decides open decisions and reads hard briefs before their builders launch (option 3 declined).

Layers (from the briefs, 2026-11-21): **W2a** U2.3a (FEA hash, D13; first), U2.1 [hard] (after U1.5), U2.4a, U2.5a (after U1.5); **W2b** U2.3b adapters (after U2.3a), U2.2 (scouts any time; builder after U2.3a), U2.4b (after U2.4a), U2.5b [hard] (after U2.1 + U2.5a); **W2c** U2.4c (after U2.4b), U2.5c designs-only (after U2.5b), W2-S `sim.drop` op (after U2.3b, D23). Briefs: `U2.1-gates`, `U2.2-standards`, `U2.3a-fea-hash`, `U2.3-adapters` (U2.3b), `U2.4-team-ops` / `-b` / `-c`, `U2.5a-calcs`, `U2.5-import-concept-a` (U2.5b), `U2.5c-designs`. Proposed later: U2.5d (concept-a plane.yaml re-import after an FEA re-run).

| Step | Role | Model | Input | Output | Pass criterion |
|---|---|---|---|---|---|
| W2-T1, T3, T5 | `tactician` | Sonnet | §7 U2.1, U2.3, U2.5 + merged W1 code | `briefs/U2.1-gates.md`, `briefs/U2.3-adapters.md`, `briefs/U2.5-import-concept-a.md` | builder-ready bar; Plan coverage complete |
| W2-T2, T4 | `tactician` | Sonnet | §7 U2.2, U2.4 | `briefs/U2.2-standards.md`, `briefs/U2.4-team-ops.md` | same |
| W2-A | `advisor` | Opus | the three hard briefs | recommendation per brief | "builder-ready" or numbered gaps |
| W2-1, W2-3, W2-5 | `builder-plus` | Sonnet | hard briefs | `std/u2.1-gates`, `std/u2.3-adapters`, `std/u2.5-import` | brief's targeted tests; CI green on both OSes |
| W2-S1…S9 | `scout` | Haiku | `briefs/U2.2-standards.md` Part A (one source each) | `knowledge/sources/std-*.md` in the u2.2 worktree | each filled from sources actually opened; inline check passes |
| W2-2, W2-4 | `builder` | Haiku | their briefs | `std/u2.2-standards`, `std/u2.4-team-ops` | same |
| W2-T2b | `tactician` | Sonnet | §7 U2.2 step 3a (Tristan 2026-11-21) | `briefs/U2.2-2-knowledge-import.md` | builder-ready bar; paths and names grep-verified against main; scout/builder split stated |
| W2-2b | `builder` | Haiku | brief U2.2-2 (to be written): §7 U2.2 step 3a, knowledge import of DBF-Combined `redesign/config-study/research/` | `std/u2.2b-knowledge` | brief's checks; CI green |
| W2-R1, W2-R2 | `reviewer` | Opus (fresh, up to two) | units split between them | `reviews/2026-11-2x-w2.md` | "### Verdict: ACCEPT" per unit; merge order checked |
| W2-Au | `auditor` | Haiku | session state | hourly report | ≤ 15 lines |
| W2-X | `advisor` | Opus | a unit that failed review twice | recommendation | one dispatch |

**Permissions for W2:** as W1, plus whatever external tools the U2.3 brief names for `plane tools doctor` (read-only probes; installing OpenCAE/MuJoCo is Tristan's, not an agent's), and `uv` for venv installs once W1-P lands.

### 6g. Agent table for the discipline fold-in (Tristan, 2026-11-21; plan-only task, no build)

Fold DBF-Combined `redesign/TEAM.md` (45 roles listed, A1–J6; 39 role folders) into hangar as gate criteria, standards keys, discipline skills, scorecard sections and knowledge entries, not agents (§1b; Douglas 11-18: roles by work level). Source: the read-only clone `C:/Users/trist/DBF-Combined` @ `a93f14d` (sparse to `redesign/`). Extracts go to `plans/2026-11-20-standardization/discipline-extract/<role id>.md`; the conductor writes §1c from them.

| Step | Role | Model | Input | Output | Pass criterion |
|---|---|---|---|---|---|
| DF-S1 | `scout` | Haiku | TEAM.md + team/{A1..A5,B1..B3} | 8 extract files | fixed template filled; gaps "not found"; only what files say |
| DF-S2 | `scout` | Haiku | team/{B4,C1..C6,D1} | 8 extract files | same |
| DF-S3 | `scout` | Haiku | team/{D2..D7,E1,E2} (D4 inactive) | 8 extract files | same |
| DF-S4 | `scout` | Haiku | team/{E3,F1..F5,G1,G2} | 8 extract files | same |
| DF-S5 | `scout` | Haiku | team/{G3,G4,H1..H3,I1,I2,J1} | 8 extract files | same |
| DF-S6 | `scout` | Haiku | TEAM.md rows J2..J6 (no folders) | 5 extract files | same |
| DF-T1…T6 | `scout` | Haiku | the same role groups + `discipline-extract/_RULES.md` (conductor's codes) | a `lands as` column on every check row + a counts block per file | every row has exactly one allowed code; counts sum to the row count |
| DF-T7…T9 | `scout` | Haiku | 15 extract files each + `_RULES.md` DF-A amendments | re-tagged `STD:`, no-limit `GATE:`, H1 rig-tolerance and removed-gate rows; recounted blocks | every row still has exactly one allowed code; counts sum to rows |
| DF-A | `advisor` | Opus | §1c + amended U2.1/U2.2/U3.2/U3.5 text | recommendation | intent check: work-level roles, subtract before adding, gates a design can't pass without working |
| DF-R | `reviewer` | Opus (fresh) | the plan diff | `reviews/2026-11-21-discipline-foldin.md` | "### Verdict: ACCEPT" |

### 6h. Agent table for the R-id ledger audit (Tristan, 2026-11-21; no code changes)

| Step | Role | Model | Input | Output | Pass criterion |
|---|---|---|---|---|---|
| LA-R | `reviewer` | Opus (fresh) | every R-id in §1 whose units are all merged (22, excluding R29: deferred under D3), the merge commits, the requirement text and its transcript source | `reviews/2026-11-21-ledger-audit.md` | one verdict per R-id: DONE with the merge commit(s) as evidence, or OPEN with a one-line note on what is missing |

### 6i. Agent table for W3 (Tristan, 2026-11-21: "do the small fix and launch W3"; started early, W2 done)

Layers: **W3a** briefs for every unit in parallel, plus W3.0 (PROGRESS.md review column misses sub-unit reviews such as `## U2.4a`, so U2.3–U2.5 show "-"); **W3b** builders: W3.0, U3.1 [hard], U3.2, U3.3, U3.6 [hard] in parallel (hard builders only after the advisor check and Tristan has read the brief); U3.5 after U3.2 merges (it extends `tests/test_skills.py`); **W3c** U3.4 `design-engineer` after U3.2 merges (it uses `design-iterate`). Briefs: `W3.0-progress-subunits`, `U3.1-studio`, `U3.2-skills`, `U3.3-bench`, `U3.5-discipline-skills`, `U3.6-discipline-gates`.

| Step | Role | Model | Input | Output | Pass criterion |
|---|---|---|---|---|---|
| W3-T0 | `tactician` | Sonnet | `core/hangar/progress.py` (`REVIEW_HEAD_RE`), `reviews/2026-11-21-w2.md`, `tests/` for progress | `briefs/W3.0-progress-subunits.md` | builder-ready bar |
| W3-T1, T6 | `tactician` | Sonnet | §7 U3.1, U3.6 (+ §1c, §2.7) + merged W2 code | `briefs/U3.1-studio.md`, `briefs/U3.6-discipline-gates.md` | builder-ready bar; Plan coverage complete |
| W3-T2, T3, T5 | `tactician` | Sonnet | §7 U3.2, U3.3, U3.5 (+ §1c, extracts) | `briefs/U3.2-skills.md`, `briefs/U3.3-bench.md`, `briefs/U3.5-discipline-skills.md` | same |
| W3-A | `advisor` | Opus | the two hard briefs | recommendation per brief | "builder-ready" or numbered gaps |
| W3-0, W3-2, W3-3 | `builder` | Haiku | their briefs | `std/w3.0-progress`, `std/u3.2-skills`, `std/u3.3-bench` | brief's checks; CI green on both OSes |
| W3-5a, W3-5b, W3-5c | `builder` | Haiku | `briefs/U3.5-discipline-skills-{1,2,3}.md` (split by the tactician: skills+tests after U3.2 merges; scorecard+pointers and procedures+PROVENANCE (R18) any time) | `std/u3.5-discipline-skills`, `std/u3.5-scorecard`, `std/u3.5-procedures` | same |
| W3-1, W3-6, W3-6b | `builder-plus` | Sonnet | hard briefs (U3.6-2 `design.set --kind add` creates keys, merges first; then U3.6 gates; then a `design-engineer` design PR sets concept-a's D21 fields with `plane design set`) | `std/u3.1-studio`, `std/u3.6-discipline-gates`, `std/u3.6-2-design-set-add` | same |
| W3-4 | `design-engineer` | Sonnet | §7 U3.4 step 1 goal, concept-a | `design/concept-a/*` PRs | as amended §7 U3.4 Step 3 (FAIL not higher, FAIL+WARN lower, no threshold or rating change; Tristan 2026-11-21) |
| W3-S1 | `scout` | Haiku | U3.6 brief decision 4: wire ampacity for 14 AWG (and the other gauges in concept-a harnesses) | `knowledge/sources/std-wire-ampacity.md` via `knowledge/TEMPLATE-source.md` | template filled from sources actually opened; gaps "not found" |
| W3-T1b, W3-1b | `tactician` Sonnet, then `builder` Haiku | U3.1b (Tristan's Studio acceptance run, 2026-11-21: he edited a mass and re-ran checks but found no Validate result view or Propose action; Studio's JS calls only `design.get`/`design.new`) | `briefs/U3.1b-studio-propose.md`, branch `std/u3.1b-studio-propose` | Studio edit mode has Validate (shows the scorecard for the edited design) and Propose (`design.propose` with a why; shows the PR URL); hidden on Pages; Playwright test drives edit → validate → propose with propose mocked |
| W3-T6c, W3-6c | `tactician` Sonnet, then `builder-plus` Sonnet | U3.6c (Tristan 2026-11-21, option a): `plane design set --kind add` accepts list/mapping values (YAML flow) and adds them inside one-line flow mappings, so concept-a's elevon mechanisms and joint articulations can be declared with plane only (U3.4 run 3 blocker) | `briefs/U3.6c-design-set-collections.md`, branch `std/u3.6c-design-set-collections` | byte-diff tests (only added text or the one flow line changes), schema checked once, atomic with `--also`; concept-a mechanisms declarable on a tmp copy with T6 rows evaluated |
| W3-T6d, W3-6d | `tactician` Sonnet, then `builder` Haiku | U3.6d (Tristan 2026-11-21, advisor W3-X path b): `plane design set` removes one list element by id (byte-preserving splice delete, CHANGELOG entry, one strict schema check, atomic with `--also`), so U3.4 run 5 can drop the screw-to-servo attachments E-MEC-HW-R1/L1 that close a loop | `briefs/U3.6d-design-remove.md`, branch `std/u3.6d-design-remove` | byte-diff test (only the element's lines removed), CRLF, unknown id errors, file still validates, refusals for non-list or nested deletes |
| W3-4 (run 5) | `design-engineer` | Sonnet | advisor path (b) steps 1-5, after U3.6d merges | `design/concept-a/*` PR | T6.mechanism elevon-r/l PASS, no T6.undriven, no T1.articulation FAIL, FAIL <= 4 and FAIL+WARN < baseline (D25) |
| W3-T4a, W3-4a | `tactician` Sonnet, then `builder` Haiku | U3.4a (PR #2 review, 2026-11-21): tests stop pinning the committed designs/concept-a; frozen copies under `tests/fixtures/`, tests repointed; test-only, merges before any concept-a design PR | `briefs/U3.4a-test-fixtures.md`, branch `std/u3.4a-test-fixtures` | full CI green; then a throwaway concept-a edit on a scratch branch leaves those 15 tests green |
| W3-T6e, W3-6e | `tactician` Sonnet, `advisor` check, then `builder-plus` Sonnet | U3.6e (PR #2 review): T6 mechanism gate samples every 1 deg plus range ends; exempts declared linked pairs (kinematic_link) from collision; follower tracking no longer proved by the declared ratio alone | `briefs/U3.6e-t6-gate.md`, branch `std/u3.6e-t6-gate` | tests: a 1-deg collision found; a linked pair not counted; concept-a run with ratio 1.33 and servo +-15 gives a physical verdict |
| W3-4 (run 6) | `design-engineer` | Sonnet | after U3.4a and U3.6e merge: honest ratio (about +-1.33 from the meshes), servo range about +-15 deg, `plane baseline update`, PR body with caveats | `design/concept-a/*` PR (PR #2 closed) | D25 + advisor path (b) criteria, CI green, baseline check exit 0 |
| W3-R1, W3-R2 | `reviewer` | Opus (fresh, up to two) | units split between them | `reviews/2026-11-2x-w3.md` | "### Verdict: ACCEPT" per unit; merge order checked |
| W3-Au | `auditor` | Haiku | session state | hourly report | ≤ 15 lines |
| W3-X | `advisor` | Opus | a unit that failed review twice | recommendation | one dispatch |

**Permissions for W3:** read the whole repo; write `plans/2026-11-20-standardization/briefs/`, worktrees `C:/Users/trist/wt/<unit>`, `reviews/`, `bench/`, `skills/`, `viewer/`, `knowledge/procedures/`, `standards/` (U3.6 new keys as `pending` only); commands `git worktree|branch|commit|push` on `std/*` and `design/*`, `python -m pytest`, `plane *`, `npx playwright` (U3.1 smoke), `claude -p` headless (U3.3, 9 bench runs), `gh pr create|view`, `gh run view`. No merges to `main` without a reviewer ACCEPT.

### 6j. Agent table for the concept-a budget unit fix (Tristan, 2026-11-21)
Root cause (conductor, checked): `params-A.json` stores `req.budget_usd` = 2000.0 USD, not k$; `importers/dbf.py::_n(x, 0)` strips trailing zeros from an integer string ("2000" → "2"). `_n(..., 0)` has one call site (budget). Designs and core stay in separate PRs.

| Agent | Role | Model | Input | Output | Pass criterion |
|---|---|---|---|---|---|
| FX-1 [x] | `builder` | Haiku | launch prompt (exact fix + tests) | branch `std/fx-importer-n0` | `_n(2000, 0) == "2000"`; re-import of concept A writes `budget_usd: 2000`; existing importer tests pass; CI green |
| FX-2 [x] | `design-engineer` | Sonnet | `plane design set designs/concept-a requirements.budget_usd --value 2000 --kind modify` | commit on `main` (D30: small fixes, no PR) | validate `--tier all` before/after; baseline updated only if rows change; reviewer check before push |
| FX-R | `reviewer` | Opus (fresh) | both commits (D30) | `reviews/2026-11-21-fixes.md` | "### Verdict: ACCEPT" per PR |

### 6k. Agent table for the ledger task triage (Tristan, 2026-11-21; no code, design or standards changes)
| Agent | Role | Model | Input | Output | Pass criterion |
|---|---|---|---|---|---|
| TR-S1…S4 | `scout` | Haiku | one batch of about 12 open `kind: task` items each | evidence file in the session scratchpad: per task status proposal (done / superseded / dropped / open) with commit, PR or file evidence, duplicate pairs, W4-or-v1.1 home | every task in the batch has one proposal and cites only what was opened |
| TR-R | `reviewer` | Opus (fresh) | every proposed "done" and "superseded" | confirm or reject each, one line | each confirmation names the code or file checked |
Due dates and homes (`units`) are written by the conductor into `ledger/items.yaml` directly (`plane ledger set` sets status only; tool gap logged as a task). New scope calls go to §3 with a default.

### 6l. Agent table for W4 (Tristan, 2026-11-21: "go A and B"; started early)
Tracks: **A** small-fix batch (ledger tasks homed U4.1: T22, T25, T27, T29, T33, T34, T39, T46, T47), pushed to `main` after review (D30). **B** U4.1 Step 2 performance (T44). **C** concept-a D21 data (D38), after A's T47. **D** U4.1 Steps 1, 3–5. **E** U14.1. Rows for C–E are added before they launch.

W4 wave rules (W3 lessons T41–T43):
- R-a: a brief whose output a later agent uses on a design includes a dry run of that handoff on a tmp copy of the design (T41).
- R-b: tacticians run the brief's tests against the base commit first (record red/green under Known failures) and grep-verify every quoted name and path (T42).
- R-c: the conductor launches `auditor` every hour while any W4 agent runs (T43).

| Agent | Role | Model | Input | Output | Pass criterion |
|---|---|---|---|---|---|
| W4-TA | `tactician` | Sonnet | ledger T22, T25, T27, T29, T33, T34, T39, T46, T47 (texts + triage notes) | `briefs/W4a-*.md`, one per fix or per shared file, each marked easy or [hard] | builder-ready bar; R-a, R-b applied |
| W4-A1…An | `builder` (easy) / `builder-plus` ([hard]) | Haiku / Sonnet | one W4a brief each | branch `std/w4a-<task>` | brief's checks; CI green by headSha |
| W4-TB | `tactician` | Sonnet | U4.1 Step 2, T44: profile `plane design validate designs/concept-a` (tiers 0–8, no FEA) and `plane baseline check` per tier | `briefs/U4.1-perf.md` [hard], measured profile in the brief | timings measured, not estimated; Tristan reads the hard brief; `advisor` checks it |
| W4-B | `builder-plus` | Sonnet | `briefs/U4.1-perf.md` | branch `std/u4.1-perf` | validate ≤ 60 s measured before/after; identical check results |
| W4-RA | `reviewer` | Opus (fresh) | every track A and B branch | `reviews/2026-11-2x-w4.md` | "### Verdict: ACCEPT" per unit |
| W4-Au | `auditor` | Haiku | session state | hourly report | ≤ 15 lines |
| W4-X | `advisor` | Opus | hard brief check; a unit that failed review twice | recommendation | one dispatch |
| W4-TC | `tactician` | Sonnet | D38, D21, U3.6 brief handoff (battery, motor, wiring, control-surface fields); DBF-Combined `params-A.json` and BOM as value sources; then D39, D40 | `briefs/W4c-concept-a-d21.md`, `briefs/W4c-pre-*.md`: the exact `plane design set` command list with source per value, dry-run on a tmp copy (R-a), expected gate changes | every command dry-run green on a tmp copy; no tool gap left unflagged |
| W4-C0a, W4-C0b | `builder` | Haiku | `briefs/W4c-pre-fea-hash.md` (D40, G1), `briefs/W4c-pre-d21-test.md` (D39) | branches `std/w4c-fea-hash`, `std/w4c-d21-test` | brief's checks; CI green; merge before W4-C |
| W4-C | `design-engineer` | Sonnet | `briefs/W4c-concept-a-d21.md` | commit on `main` (D30): `designs/concept-a` values + CHANGELOG + `fea/*.json` + `baseline.json` | brief's checks; `plane baseline check` exit 0; part ids `wng-004-l`, `avn-001` kept |
| W4-K | `builder` | Haiku | `briefs/U2.2-2-knowledge-import.md` Part A, then Part B after the scouts (D42) | branch `std/u2.2b-knowledge` | brief pass checks 1 and 3; CI green |
| W4-KS1…KS5 | `scout` | Haiku | same brief, Part S, one batch each (S1–S5) | `knowledge/concepts/<id>.md` in the u2.2b worktree | per-scout self-check in the brief |
| W4-RB | `reviewer` | Opus (fresh) | U2.2-2 branch; later W4 track D fixes | `reviews/2026-11-22-w4.md` | "### Verdict: ACCEPT" |
| W4-R1 | `reviewer` | Opus (fresh) | U4.1 Step 1: whole `main` since `f462468` against §1–§2 and `standards/review-scorecard.md` | `reviews/2026-11-22-whole-branch.md` | blocking items listed per unit (each reopens its unit) |
| W4-AuS | `auditor` | Haiku | U4.1 Step 3 subtraction pass: files, commands, docs, ledger items used by no test, skill or op | list in its report | each item with evidence and delete/archive/keep |
| W4-TD | `tactician` | Sonnet | U4.1 Steps 4–5 (docs, tag, verification record) after W4-R1 | `briefs/U4.1-docs-release.md` | builder-ready bar; R-a, R-b |
| W4-D1 | `builder-plus` | Sonnet | `briefs/W4d-tiers.md` [hard] (approved by Tristan 2026-11-22) | branch `std/w4d-tiers` | brief's checks; CI green |
| W4-D2…D5 | `builder` | Haiku | `briefs/U4.1-docs.md` (after D1), `W4d-concept-a-readme.md`, `W4d-viewer-flake.md`, progress-test fix (inline brief) | branches `std/w4d-*` | brief's checks; CI green |
| W4-TE | `tactician` | Sonnet | §7 U14.1 Steps 1–3; `reviews/*.md` measured values; T35 bench caveat; D32–D34 gaps | `plans/2026-11-20-standardization/u4.2/{demo-script,metrics,deck-outline}.md` | every demo command dry-run on a tmp copy (R-a); every metric cites a review or command output |
| W4-E | `tactician` | Sonnet | U14.1 Step 1 (Tristan 2026-11-22: "build the deck in the repo"): `u4.2/deck-outline.md`, `metrics.md`, `demo-script.md` | `docs/deck/index.html` (self-contained, opens offline, arrow-key navigation) | every number cites a file in the repo; no claim beyond `metrics.md`; caveats (T35, D32–D34) on their slides |
| W4-RC | `reviewer` | Opus (fresh) | `docs/deck/index.html` against `u4.2/metrics.md`, `demo-script.md` and the cited repo files | review section in `reviews/2026-11-22-w4.md` | every slide number traced to its source; caveats present; "### Verdict:" |
| W4-F1 | `builder` | Haiku | ledger T70 (inline brief: test tier defaults 9, cli.py `--tier` help, regenerate `docs/cli.md`) | branch `std/w4f-t70` | tests pass; `docs/cli.md` in sync; CI green |
| W4-F2 | `builder` | Haiku | ledger T69 (inline brief: restore concept ids in one knowledge entry; PROVENANCE research rows) | branch `std/w4f-t69` | test_knowledge passes; CI green |
| W4-TF | `tactician` | Sonnet | D33, T24, T53, R1/R12/R14/R17/R31: U2.5d concept-a re-import (v1.1 unit) | `briefs/U2.5d-reimport.md` with a proposed §7 unit block | builder-ready bar; R-a, R-b; T53 reproduced or closed with evidence |
| W4-RD | `reviewer` | Opus (fresh) | W4-F1, W4-F2 | review sections in `reviews/2026-11-22-w4.md` | "### Verdict:" |
| W4-G1a | `builder` | Haiku | `briefs/U2.5d-reimport.md` Part 1a (importer finishes: mesh kind, load_n, pitot) (D49) | branch `std/u2.5d-core` | Part 1a checks; CI green |
| W4-G1b, W4-G3 | `builder-plus` | Sonnet | Part 1b (missing blocks) and Part 3a/3b (designs re-import, replay, FEA, baseline) [hard; Tristan reads, advisor checks] | `std/u2.5d-core` (1b, after 1a), `std/u2.5d-designs` (3) | brief checks |
| W4-G3c | `design-engineer` | Sonnet | Part 3c gate triage after the re-import | tasks per new FAIL | brief checks |
| W4-XG | `advisor` | Opus | U2.5d hard parts 1b and 3 | READY/NOT READY | one dispatch |
| W4-TG, W4-G0 | `tactician` then `builder-plus` | Sonnet | U2.5d pre-gates fix (advisor 2026-11-23): `discipline.py` joint_rf per-joint rating (D50), D39 regex, repoint test_fea / test_adapters / concept_a_studio pins to the frozen fixture [hard] | `briefs/U2.5d-pre-gates.md`, branch `std/u2.5d-pre-gates`, merged before the designs branch | brief checks; pytest green on main and on the a619fa5 tree |
| W5-T | `tactician` | Sonnet | U5.1 briefs for T72, T52, T58, T17, T26, T28, T68 | `briefs/U5.1-*.md` | builder-ready bar; R-a, R-b |
| W5-B1…B7 | `builder` (easy) / `builder-plus` ([hard]) | Haiku / Sonnet | one U5.1 brief each | branch `std/u4.3-<task>` | brief checks; CI green |
| W5-R | `reviewer` | Opus (fresh) | every U5.1 branch | `reviews/2026-11-23-w5.md` | "### Verdict:" per branch |
| W5-A | `auditor` | Haiku | hourly overnight audit | report | findings acted on |
| W6-T | `tactician` | Sonnet | U5.2 briefs for T84, T85, T15, T21, T23, T3, T20 | `briefs/U5.2-*.md` | builder-ready bar; R-a, R-b |
| W6-B1…B7 | `builder` (easy) / `builder-plus` ([hard]) | Haiku / Sonnet | one U5.2 brief each | branch `std/u4.4-<task>` | brief checks; CI green; launched: W6-B1 = t21 (builder, Haiku), W6-B2 = t84 [hard] (builder-plus, Sonnet), W6-B3 = t3 (builder, Haiku) |
| W6-R | `reviewer` | Opus (fresh) | every U5.2 branch | `reviews/2026-11-23-w6.md` | "### Verdict:" per branch |
| W7-T | `tactician` | Sonnet | U5.3 briefs for T7, T86, T87, T83, T50, T54, T55 | `briefs/U5.3-*.md` | builder-ready bar; R-a, R-b |
| W7-B1…B7 | `builder` (easy) / `builder-plus` ([hard]) | Haiku / Sonnet | one U5.3 brief each | branch `std/u4.5-<task>` | brief checks; CI green; launched: t7 [hard] builder-plus Sonnet; t54, t50, t83, t87, t86 builder Haiku; t55 not briefed |
| W7-R | `reviewer` | Opus (fresh) | every U5.3 branch | `reviews/2026-11-23-w7.md` | "### Verdict:" per branch |
| W8-T, W8-B, W8-R | `tactician`, `builder`, `reviewer` | Sonnet, Haiku, Opus (fresh) | U5.4 (T89) | `briefs/U5.4-t89.md`, branch `std/u4.6-t89`, `reviews/2026-11-23-w8.md` | builder-ready bar; brief checks; "### Verdict:" |
| W9-T, W9-B, W9-R | `tactician`, `builder`/`builder-plus`, `reviewer` | Sonnet, Haiku/Sonnet, Opus (fresh) | U5.5 (T55, T54 grader) | `briefs/U5.5-t55.md`, `briefs/U5.5-t54.md`, branches `std/u4.7-t55`, `std/u4.7-t54`, `reviews/2026-11-23-w9.md` | builder-ready bar; brief checks; "### Verdict:" |
| W10-T, W10-B, W10-R | `tactician`, `builder`/`builder-plus`, `reviewer` | Sonnet, Haiku/Sonnet, Opus (fresh) | U6.1 (T91, T92, T93) | `briefs/U6.1-*.md`, branches `std/u4.8-*`, `reviews/2026-11-23-w10.md` | builder-ready bar; brief checks; "### Verdict:" |
| W11-A, W11-T, W11-B, W11-G, W11-R | `advisor`, `tactician`, `builder-plus`, `design-engineer`, `reviewer` | Opus, Sonnet, Sonnet, Sonnet, Opus (fresh) | U6.2 (T37, T60) | advisor pick in `briefs/U6.2-t37.md`; branches `std/u4.9-t37`, `std/u4.9-t60`; `reviews/2026-11-23-w11.md` | advisor names one fix; gates before/after; "### Verdict:" |
| W12-T, W12-B, W12-R | `tactician`, `builder`/`builder-plus`, `reviewer` | Sonnet, Haiku/Sonnet, Opus (fresh) | U6.3 (T83, T86, T88, T90) | `briefs/U6.3-*.md`, branches `std/u4.10-*`, `reviews/2026-11-23-w12.md` | builder-ready bar; brief checks; "### Verdict:" |
| W13-T, W13-B, W13-R | `tactician`, `builder`, `reviewer` | Sonnet, Haiku, Opus (fresh) | U6.4 (T28; D59) | `briefs/U6.4-t28.md` (refresh of `U5.1-t28.md`), branches `std/u4.11-t28` (core), `std/u4.11-t28-docs` (deck/metrics/claims data), `reviews/2026-11-23-w13.md` | builder-ready bar; claim counts before/after; "### Verdict:" |
| W14-T, W14-B, W14-R | `tactician`, `builder`, `reviewer` | Sonnet, Haiku, Opus (fresh) | U7.1 (demo re-run on main, T104) | `u4.2/demo-script.md`, `briefs/U7.1-t104.md`, branch `std/u4.12-t104`, `reviews/2026-11-24-w14.md` | every demo step re-run on a scratch clone; "### Verdict:" |
| W14-A | `advisor` | Opus | U7.1 CI: T104 branch fails `test_propose_link_survives_real_git_side_effects` on windows twice (GLB 404), T84 reopened | diagnosis in `reviews/2026-11-24-w14.md` | names cause and one fix, who builds it |
| W14-T2, W14-B2 | `tactician`, `builder-plus` | Sonnet, Sonnet | U7.1 step 4 (T84 reopened: Studio fixes its folders at construction, W14-A) | `briefs/U7.1-t84.md`, branch `std/u4.12-t84`, review by W14-R | new isolation test fails on main; windows CI green |
| W15-T, W15-B, W15-R | `tactician`, `builder`, `reviewer` | Sonnet, Haiku, Opus (fresh) | U7.2 (T94) | `briefs/U7.2-t94.md`, branches `std/u4.13-t94` (core), `std/u4.13-t94-design` (designs), `reviews/2026-11-24-w15.md` | BOM total before/after; "### Verdict:" |
| W16-T, W16-B, W16-R | `tactician`, `builder`/`builder-plus`, `reviewer` | Sonnet, Haiku/Sonnet, Opus (fresh) | U7.3 (T99, T100, T101, T102) | `briefs/U7.3-*.md`, branches `std/u4.14-*`, `reviews/2026-11-24-w16.md` | builder-ready bar; "### Verdict:" |
| W17-T, W17-B, W17-R | `tactician`, `builder`/`builder-plus`, `reviewer` | Sonnet, Haiku/Sonnet, Opus (fresh) | U7.4 (T95, T103, T67) | `briefs/U7.4-*.md`, branches `std/u4.15-*`, `reviews/2026-11-24-w17.md` | builder-ready bar; schema minor version for T95; "### Verdict:" |
| W18-T, W18-B, W18-R | `tactician`, `builder`, `reviewer` | Sonnet, Haiku, Opus (fresh) | U7.5 (U2.2-3 docs/research import, D62) | `briefs/U2.2-3-research-import.md`, branch `std/u4.16-research`, `reviews/2026-11-24-w18.md` | knowledge templates, PROVENANCE, copy check (T68), "### Verdict:" |
| W19-T, W19-B, W19-R | `tactician`, `builder-plus`, `reviewer` | Sonnet, Sonnet, Opus (fresh) | U8.1 (team guide, P189) | `briefs/U8.1-team-guide.md`, `docs/team-guide.md`, branch `std/u4.17-team-guide`, `reviews/2026-11-24-w19.md` | every command in the guide run on a fresh clone; reviewer follows it as a newcomer; "### Verdict:" |
| W19-X | `recon` | Sonnet | U8.1 rework (D64): how Claude Desktop connects to a local MCP server on Windows/macOS, Project instructions, limits vs Claude Code | `plans/2026-11-20-standardization/u4.17/desktop-facts.md` | official docs opened and cited |
| W20-T, W20-B, W20-R | `tactician`, `builder-plus`, `reviewer` | Sonnet, Sonnet, Opus (fresh) | U8.2 (CI unit-test speed, T11, P194) | `briefs/U8.2-ci-speed.md`, branch `std/u4.18-ci-speed`, `reviews/2026-11-25-w20.md` | measured before/after wall time per OS; no test dropped from main's full run; "### Verdict:" |
| W21-T, W21-S, W21-X, W21-B, W21-R | `tactician`, `scout`, `recon`, `builder`, `reviewer` | Sonnet, Haiku, Sonnet, Haiku, Opus (fresh) | U8.3 (rating sourcing, D67, T82) | `briefs/U8.3-*.md`, `knowledge/sources/`, branch `std/u4.19-ratings`, `reviews/2026-11-25-w21.md` | every value has an opened source or stays pending with a reason; fidelity line before/after; "### Verdict:" |
| W22-T, W22-B, W22-R | `tactician`, `builder`/`builder-plus`, `reviewer` | Sonnet, Haiku/Sonnet, Opus (fresh) | U8.4 (process trim, D66, T112) | `briefs/U8.4-*.md`, branches `std/u4.20-*`, `reviews/2026-11-25-w22.md` | rules and hooks still enforced; progress tooling still green; "### Verdict:" |
| W23-T, W23-B, W23-R | `tactician`, `builder-plus`, `reviewer` | Sonnet, Sonnet, Opus (fresh) | U9.1 (G1 kernel + PDL 1.2), U9.2 (G2 generators + concept-a parametric copy), D70 | `briefs/U9.1-*.md`, `briefs/U9.2-*.md`, branches `std/u4.21-*`, `std/u4.22-*`, `reviews/2026-11-26-w23.md` | volumes/masses vs hand calculations; regenerated meshes match the imported STLs within tolerance; one `design set` regenerates geometry, mass and CG; "### Verdict:" |
| W24-T, W24-B, W24-R | `tactician`, `builder`/`builder-plus`, `reviewer` | Sonnet, Haiku/Sonnet, Opus (fresh) | U10.1 (demo + deck for Dec 2), U10.2 (fix batch: T115, T105, guide rule 9, T122), U10.3 (T121 pose-aware cut pockets) | `briefs/U14.1x-*.md`, branches `std/u4.2x-*`, `reviews/2026-11-24-w24.md` | demo re-run on a fresh clone; deck numbers re-measured; "### Verdict:" |
| W24-Au | `auditor` | Haiku | overnight 11-24 | report in the conductor's notes | hourly-ish; acted on |
| W24-A | `advisor` | Opus | U10.3 stopped twice (budget; then a new T3.planform FAIL: swept pockets remove ~18,500 mm^2 of measured wing area) | advice section in `reviews/2026-11-24-w24.md` | names the intended pocket geometry and one fix |
| W25-T, W25-B, W25-R | `tactician`, `builder`, `reviewer` | Sonnet, Haiku, Opus (fresh) | U10.4 (QOL batch from audit W24-Au2, D71) | `briefs/U10.4-*.md`, branches `std/u4.26-*`, `reviews/2026-11-24-w25.md` | each fix has a test or a re-run command; "### Verdict:" |
| W26-T, W26-B, W26-R | `tactician`, `builder`, `reviewer` | Sonnet, Haiku, Opus (fresh) | U10.5 (test and tidy follow-ups T108, T109, T110, T123; D71) | `briefs/U10.5-*.md`, branches `std/u4.27-*`, `reviews/2026-11-24-w26.md` | each test fails before its fix; "### Verdict:" |
| W27-T, W27-B, W27-R | `tactician`, `builder`/`builder-plus`, `reviewer` | Sonnet, Haiku/Sonnet, Opus (fresh) | U10.6 (T128 guide, T125 pockets follow moved parts, T126 propose slug; D74) | `briefs/U10.6-*.md`, branches `std/u4.28-*`, `reviews/2026-11-24-w27.md` | each fix has a failing-first test or a re-run; "### Verdict:" |

### 6m. Agent table for W28-W29 (T129, D75; any-aircraft demo, D77-D79)

| Agent | Role | Model | Input | Output | Pass criterion |
|---|---|---|---|---|---|
| W28-A, W28-T, W28-B, W28-R | `advisor`, `tactician`, `builder-plus`, `reviewer` | Opus, Sonnet, Sonnet, Opus (fresh) | U11.1 (T129 parametric propagation, D75) | design note + `briefs/U11.1-*.md`, branches `std/u4.29-*`, `reviews/2026-11-24-w28.md` | one span change on concept-a-param moves fins and attached parts with no new interference; existing designs unchanged; "### Verdict:" |
| W29-X, W29-S | `recon`, `scout` | Sonnet, Haiku | U12.4 (reference-aircraft template + how scale-RC builders turn a real aircraft into a model; filled for A400M and Cessna 172) | `knowledge/TEMPLATE-reference-aircraft.md`, `knowledge/` entries | only opened sources cited |
| W29-T, W29-B, W29-R | `tactician`, `builder`/`builder-plus`, `reviewer` | Sonnet, Haiku/Sonnet, Opus (fresh) | U12.1 (checks by aircraft type + fixed-wing standards + per-design mission), U12.2 (real-parts library), U12.3 (nacelle/prop/nose generators) | `briefs/U5.1x-*.md`, branches `std/u4.3x-*`, `reviews/2026-11-24-w29.md` | each brief builder-ready; "### Verdict:" |
| W29-G | `design-engineer` | Sonnet | U13.1 rehearsal: the Dec 1 prompt run on a branch for A400M and Cessna 172 | `reviews/2026-11-24-w29-rehearsal.md` | gaps listed; nothing merged |
| W30-T, W30-B, W30-R | `tactician`, `builder-plus`, `reviewer` | Sonnet, Sonnet, Opus (fresh) | U11.2 (profile a span change; mesh cache) | `plans/2026-11-20-standardization/u4.35/profile.md`, `briefs/U11.2-*.md`, branch `std/u4.35-*`, `reviews/2026-11-24-w30.md` | profile names where the seconds go; cached results byte-identical to uncached; "### Verdict:" |
| W31-T, W31-S, W31-B, W31-R, W31-R2 | `tactician`, `scout`, `builder`/`builder-plus`, `reviewer` (two in parallel, P262) | Sonnet, Haiku, Haiku/Sonnet, Opus (fresh) | U13.2 (design authoring gaps from rehearsal 1) | `briefs/U13.2-*.md`, `knowledge/parts/` additions, branches `std/u4.36-*`, `reviews/2026-11-25-w31.md` | a fixed-wing design can be built from a blank start with the CLI alone; "### Verdict:" |
| W32-S | `scout` | Haiku | T137 DaVinci hookup facts (R29, D3): Dillon's API guide, DBF-Combined docs (read-only source), live API GET-only | `knowledge/` source entries + `knowledge/research/davinci-api-facts.md`, branch `std/w32-davinci-facts` | every fact sourced; no POST/DELETE; token never printed |
| W32-A | `advisor` | Opus | P259: DBF-Combined origin/redesign/v1 (Dillon's DaVinci-era concept-a) vs dbf-hangar PDL/designs/concept-a: what maps, what would be lost on import | gap report in `plans/2026-11-20-standardization/u4.40/combined-compat.md` (conductor commits) | every DBF-Combined artefact classified: maps / needs adapter / would be lost |
| W32-T | `tactician` | Sonnet | D84: dry-run of the concept-a-reborn import from DBF-Combined origin/redesign/v1 in a scratch copy (no push), then Dillon's step-by-step guide | `plans/2026-11-20-standardization/u4.40/dillon-import-guide.md` | every command in the guide ran once in the dry run; issues listed with fixes |
| W33-Au | `auditor` | Haiku | hourly overnight audits (R-c) | report in chat | 15 lines, fixes named |

### 6n. Agent table for W34 (waves W15-W18: keep improving, D86-D89)

| Agent | Role | Model | Input | Output | Pass criterion |
|---|---|---|---|---|---|
| W34-T | `tactician` | Sonnet | U15.1, U15.2, U15.3 (and rehearsal-5 gaps) | `briefs/U15.1-*.md`, `briefs/U15.2-*.md`, `briefs/U15.3-*.md` | builder-ready bar |
| W34-B | `builder` / `builder-plus` | Haiku / Sonnet | one brief each | branches `std/u13.9-*`, `std/u13.10-*`, `std/u13.11-*` | brief tests pass; CI green |
| W34-R | `reviewer` | Opus (fresh) | every W34 branch | `reviews/2026-11-25-w34.md` | "### Verdict:" per branch |
| W34-X | `recon` | Sonnet | U16.1: how others generate RC/aircraft CAD with real linkages, hinges, wheels on axles and routed wires (OpenVSP, CadQuery/build123d assemblies, FreeCAD Assembly4, RC kit CAD, MuJoCo/URDF practice) | `plans/2026-11-20-standardization/u16.1/recon.md` | 3-5 approaches ranked; only opened sources |
| W34-A | `advisor` | Opus | U16.1: what the repo has (generators, PDL joints/mechanisms/harnesses, T1/T6/T7, MJCF export) vs a model close to the real aircraft; with W34-X's recon | `plans/2026-11-20-standardization/u16.1/design-note.md` | gap list, ordered build steps sized for briefs, what to cut |
| W34-T2 | `tactician` | Sonnet | U17.1: inventory of every pending or convention-sourced threshold, ranked by blocking rows driven across all designs; scout packets | `plans/2026-11-20-standardization/u17.1/inventory.md`, `briefs/U17.1-*.md` | every threshold listed once with its rank and packet |
| W34-S | `scout` (up to 3 in parallel) | Haiku | one U17.1 packet each | `knowledge/sources/` entries + a values table per packet in `u17.1/` | only opened sources; value, units, page/section quoted |
| W34-T3 | `tactician` | Sonnet | U18.1: OpenCAE CLI integration study in a scratch clone of OpenCAEModel main (doctor, quad250 example, a hangar design exported to drone.json by hand) | `plans/2026-11-20-standardization/u18.1/study.md`, `briefs/U18.1-*.md` | every command run once; field mapping PDL -> drone.json complete or gaps named |
| W34-T4 | `tactician` | Sonnet | U18.2, U18.3, U18.4 (calibration, spar bending, trim and stability) | `briefs/U18.2-*.md`, `briefs/U18.3-*.md`, `briefs/U18.4-*.md` | builder-ready bar; every threshold sourced or `pending` |
| W34-B2 | `builder-plus` | Sonnet | U16.2 step 1b: refresh std/u4.25-pockets onto main | the branch, merged with main, tests green, tier-1 time | no force push; T121 rows still gone |
| W34-T5 | `tactician` | Sonnet | U16.1 briefs S0-S9 from `u16.1/design-note.md`, S0 and S1 first | `briefs/U16.1-s<n>-*.md` | builder-ready bar; export sha256 check in every brief |
| W34-X2 | `recon` | Sonnet | U19.1: how best-in-class browser CAD/3D model viewers work (Onshape, Autodesk Viewer/APS, xeokit, three.js editor, Google model-viewer, Babylon.js sandbox, Shapr3D/Fusion web, OpenVSP viewer, MuJoCo web) | `plans/2026-11-20-standardization/u19.1/recon.md` | 3-5 ranked approaches per feature; only opened sources |
| W34-A2 | `advisor` | Opus | U19.1: audit of Studio (viewer/, core/hangar/studio.py) against the recon and Tristan's needs; UI spec | `plans/2026-11-20-standardization/u19.1/ui-spec.md` | ordered build steps sized for briefs, each Studio-visible |
| W34-T6 | `tactician` | Sonnet | U19.1 briefs B0-B8 from `u19.1/ui-spec.md` | `briefs/U19.1-b<n>-*.md` | builder-ready bar; Playwright test per visible step |
| W34-R2 | `reviewer` | Opus (fresh) | second W34 reviewer in parallel (queue too long for one) | sections in `reviews/2026-11-25-w34b.md` | "### Verdict:" per branch |
| W34-R3 | `reviewer` | Opus (fresh) | third W34 reviewer in parallel (replaces W34-R, which finished; cap lifted P291) | sections in `reviews/2026-11-25-w34c.md` | "### Verdict:" per branch |
| W34-A3 | `advisor` | Opus | U16.2 pockets refresh stopped (2 new T1.pocket sliver FAILs of 1-2 mm3 from many overlapping swept cutters; tier-1 84 s warm vs ~70 s) | diagnosis + recommended fix in `plans/2026-11-20-standardization/u16.2/diagnosis.md` | names the cause and one fix, who builds it |
| W34-Au | `auditor` | Haiku | hourly while W34 runs | report in chat | 15 lines, fixes named |

**Permissions for W4 (A and B):** read the whole repo; write `plans/2026-11-20-standardization/briefs/`, worktrees `C:/Users/trist/wt/<unit>`, `reviews/`; commands `git worktree|branch|commit|push` on `std/*`, `git push origin main` (conductor, after ACCEPT), `python -m pytest`, `plane *`, `npx playwright` (Studio fixes), `gh run list|view`. No PRs (D30). Same allow-list as W3 (`.claude/settings.local.json`); nothing new.

## 7. Units

Conventions for every unit: worktree + branch `std/<unit-id>`; `export PYTHONPATH=$PWD/core` in worktrees; finish with
`pytest -q` (all green), `plane baseline check --all; echo $?` (0: no regression against each design's baseline), `plane ledger set <R-ids> done --evidence <PR url>`, commit, PR.

Finished units (every box ticked) live in `plans/2026-11-20-standardization/archive.md`; `plane progress` reads both files. The conductor moves a unit there once its last box is ticked and its review is ACCEPT.

### Unit U8.1: Team guide: how the team works in dbf-hangar (P189)

**Scope:** one guide `docs/team-guide.md` (linked from README.md) that Tristan can send to Dillon, James and Vaibhav: install and connect their own Claude Code sessions to this repo (hooks, agents, output style, MCP); the one-repo rule (no new repos; everything lands on main after review); branches per person and per unit that do not touch each other's files (designs vs core vs tests vs knowledge; e.g. James on tests, Dillon on a new concept); create a design, iterate on it (`plane design new/set/validate/sweep/propose`, Studio), add a test, add a standard with a source, add knowledge; how agents and the conductor/plan/ledger work; review and merge; CI. Every command in it is run on a fresh clone. Docs only (plus a README link); no core/, designs/, standards/.

- [x] **Step 1: Brief** (tactician W19-T): verified facts, outline, open decisions with defaults: `briefs/U8.1-team-guide.md` *(6aac806; O1-O11 defaults recorded as D63; propose, push and PowerShell activation not run)*
- [x] **Step 2: Write** (builder-plus W19-B): `docs/team-guide.md` *(b8e6074, 777 lines, 80 fenced commands all verified)*
- [x] **Step 2b: Rework in place for D64** (recon W19-X facts on Claude Desktop; tactician W19-T amends the brief; builder-plus W19-B rewrites on the same branch): conversation-first, Claude Code and Claude Desktop setups
- [x] **Step 3: Review** (reviewer W19-R follows the guide on a fresh clone as a newcomer); merge *(REOPEN on b8e6074, 9ad7d18, 5d01843; ACCEPT 5fdf401; merged b547fb1; follow-ups T111, T112)*
- [ ] **Step 4:** Tristan reads it and sends it to the team

### Unit U8.2: Faster CI unit tests (T11; P194)

**Scope:** the "Unit tests" step takes 8.7 min on ubuntu and 5.2 min on windows (run 45321467502). Measure the slowest tests (`--durations`), then cut wall time without losing coverage on main: speed up or share the slowest fixtures (e.g. concept-a validate, Studio, viewer/playwright), mark genuinely slow tests and run them on main/nightly only if needed, shard or rebalance xdist, cache installs, and the three T11 items (slow mark for test_baseline, skip validate for PROGRESS/ledger-only commits, cancel-in-progress only on std/**). Core/tests/.github only.

- [x] **Step 1: Measure and brief** (tactician W20-T): `briefs/U8.2-ci-speed.md` *(e748226: CPU-bound, 523 s ubuntu / 311 s windows; shard x3 expected ~60%; D65)*
- [x] **Step 2: Build** (builder-plus W20-B) *(478c2d6 + retune fb2b33d)*
- [x] **Step 3: Review** (reviewer W20-R); merge; T11 done *(ACCEPT, reviews/2026-11-25-w20.md; merged d6212ea; slowest shard ubuntu ~4 min (was ~9.5), windows ~5.5 min (was ~7); follow-ups T115)*

### Unit U8.3: Source the joint ratings behind concept-a's SKIPs and drop failures (D67; T82; P198)

**Scope:** rank the connection types in `standards/connection-types.yaml` by how many concept-a joints use them; scouts collect datasheets/standards into `knowledge/sources/` (only sources opened); recon proposes `landing_load_factor` from its noted sources; a builder writes the sourced values (or `pending` with a reason) into standards; re-run concept-a and report which SKIPs and FAILs changed and the fidelity line before/after. Standards and knowledge only (plus the concept-a baseline refresh as a separate designs-only commit). James reviews the values.

- [x] **Step 1:** Ranking and scout/recon briefs (tactician W21-T) *(cda9184; finding: the joint gates read each joint's own rating, not the library, so library sources clear 0 of the 64 SKIPs; only landing_load_factor moves fidelity; S1, S4, X1 launched, S2/S3 held)*
- [x] **Step 2:** Sources (scouts W21-S, recon W21-X) *(S1: 4 of 5 sourced; S4: 0 of 5; X1: landing_load_factor pending on gear travel, T113; S2/S3 not run)*
- [x] **Step 3:** Values into standards; concept-a re-run; baseline refresh (builder W21-B) *(795cc3e: 3 types sourced, pending 31 -> 28; concept-a counts and fidelity unchanged as D68 expected; no baseline change)*
- [ ] **Step 4: Review** (reviewer W21-R); James reads the values; merge *(REOPEN once (4 note fixes), ACCEPT; merged 2bcd1d8; James's read open)*

### Unit U8.4: Process trim (D66; T112; P198)

**Scope:** (a) write the light path and the teammate rule (named ledger task, no plan unit) into `standards/agents.md` and the `CLAUDE.md` pointer line; (b) agent gate allows Claude Code built-in read-only subagents (Explore, Plan, general read-only) for every session (T112); (c) archive finished units from the plan into `plans/2026-11-20-standardization/archive.md` and keep `plane progress` working; (d) a one-page reader summary. Rules and hooks must stay enforced.

- [x] **Step 1: Briefs** (tactician W22-T) *(a3600cc: a rules easy, b gate easy, c archive hard, d summary easy; merge b, a, c, d; no plan edits by the conductor while c is in flight)*
- [x] **Step 2: Build** (W22-B) *(b 48cca9d, a fd5636f, c 3ee58b1, d cc7d53d)*
- [x] **Step 3: Review** (reviewer W22-R); merge *(c ACCEPT merged c04cec4; b REOPEN twice then advisor W22-A, D69 amended, ACCEPT merged 3f99ab0; a ACCEPT merged 6ac4bae; d REOPEN once, ACCEPT merged c6997e9)*

### Unit U9.1: Geometry kernel and PDL 1.2 (G1; D70) [hard]

**Scope:** `hangar.geom` built from `core/hangar/importers/dbf_geometry.py` (prism, revolve, loft, tube, box, cuts -> watertight trimesh; mass = density x volume from standards materials); PDL schema 1.2: a component may give `geometry: {generator, params}` instead of a mesh file, and a design-level `parameters:` block that params reference; tier 0 checks references; `design set` on a parameter or generator param regenerates the affected meshes and masses and logs one CHANGELOG entry; migrate 1.1 -> 1.2; viewer/export pick up generated meshes. Tests check volumes and masses against hand calculations.

- [x] **Step 1: Brief** (tactician W23-T) *(0df19b6; generated meshes computed on load, PDL 1.2 parameters + `$name` refs + mass_model; cut line in the brief)*
- [x] **Step 2: Build** (builder-plus W23-B) *(b21c1b1, a7434a5, 45d47bb; fix fe08487)*
- [x] **Step 3: Review** (reviewer W23-R); merge *(REOPEN once: slow test pin, T0.generator build, FEA hash of mesh_file; ACCEPT; merged 225c1b7; follow-ups S2, S4-S7 in reviews/2026-11-23-w23.md)*

### Unit U9.2: First generators and a parametric copy of concept-a (G2; D70) [hard]

**Scope:** generators `wing_panel` (airfoil .dat, span, root/tip chord, sweep, dihedral, twist, spar bore, elevon split), `tube`, `fin`, `plate` (holes), `fuselage_loft` (stations), `motor_mount`; `mesh_file` fallback. Port concept-a's wing, spar and fins from DBF-Combined `redesign/qp/A/cad/amodel/` (recorded in PROVENANCE.md) into a new design copy whose regenerated meshes match the current STLs within a stated tolerance; the hub and complex printed parts stay imported meshes. Demo: one `plane design set` on a shared parameter regenerates the parts, mass and CG, and the gates re-run. Depends on U9.1.

- [x] **Step 1: Brief** (tactician W23-T) *(0df19b6; generated meshes computed on load, PDL 1.2 parameters + `$name` refs + mass_model; cut line in the brief)*
- [x] **Step 2: Build** (builder-plus W23-B) *(Part A f8ae078 + tests fix a7252a1, merged 49a1601; Part B 49aae96, 79e4eae, README fix 93b9037)*
- [x] **Step 3: Review** (reviewer W23-R); merge *(Part A ACCEPT; Part B REOPEN once (README residue count), ACCEPT; merged a0ba030; follow-ups T121, T123)*

### Unit U10.1: Demo script and deck for Dec 2 (U14.1 Steps 2-3; D60, D70; P209)

**Scope:** add the parametric step (`plane design set designs/concept-a-param parameters.span_mm --value 940`) to `u4.2/demo-script.md` and re-run every step on a fresh clone of main; reframe `docs/deck/index.html` and `u4.2/deck-outline.md`/`metrics.md` honestly: real concept-a findings first, the one-file workflow, parametric geometry as a demonstration (10 known extra FAILs, T121), claims 53 recomputed + 40 read, fidelity 134 of 714, a roadmap slide (G3-G7, T114, T113); fix the stale op count; draft the 11-30 weekly update entry with `plane update add` (not published). Docs and updates only.

- [x] **Step 1: Brief** (tactician W24-T) *(43c6ddf: demo, deck, update briefs; builds after U9.2 merges)*
- [x] **Step 2: Build** (W24-B) *(35cc386, 032b8fd, 9159905, 44c488d, d561222)*
- [x] **Step 3: Review** (W24-R); merge *(REOPEN once (D72 ledger truth), ACCEPT; merged 6f3bc00; Studio step not re-run 11-24; update drafted, not published)*

### Unit U10.2: Fix batch during the freeze (T115, T105, T122, guide rule 9; D66)

**Scope:** fixes only: T115 (ledger-only commits run test_standards' pending-decision check; rebalance the windows shards; playwright cache key; renamed heavy test warning), T105 (docstrings say read values are not recomputed; D46 cold start 278 s), T122 (G1 review follow-ups S2, S4-S7), the garbled light-path sentence in docs/team-guide.md rule 9. Light path where it applies; full path for CI/core changes.

- [x] **Step 1: Briefs** (tactician W24-T) *(dcd6f1d: ci, text (light path: docstring-only core edits accepted by the conductor), g1fixes)*
- [x] **Step 2: Build** (W24-B) *(text f93b9b9, g1fixes 977500f, ci 239a27c + 3af73b6)*
- [x] **Step 3: Review** (W24-R); merge *(text, g1fixes ACCEPT merged 4d73f1a, 720aa25; ci REOPEN once (windows balance), ACCEPT merged bdbfbd2)*

### Unit U10.4: Quality-of-life batch (audit W24-Au2; D71)

**Scope:** fixes a teammate would notice, no threshold/schema/gate-behaviour changes: `plane design sweep` crash with repeated `--values` (meshes path in the sweep copy) and the team-guide example; CI check names in the guide (8 names); clearer errors for `design get` on a missing design, `design set` with a bad key (deepest prefix + did-you-mean), missing `--why`, `design new` with an unknown template (list templates); README `--kind` list adds `remove`; stale TODO(U2.1) in ops/standards.py. CLI start-up time (lazy imports) only if measured and small.

- [x] **Step 1: Briefs** (tactician W25-T) *(e5eb9af: sweep (hard; per-run sweep folders), errors, docs (light path); start-up is T124 v1.1)*
- [x] **Step 2: Build** (W25-B) *(errors f908559; docs 5164bf2 + 9f15a4c; sweep 6790f64 + 05ae07a)*
- [x] **Step 3: Review** (W25-R); merge *(errors ACCEPT merged 8b8f75d; docs and sweep REOPEN once each, ACCEPT, merged 2ed2ca4, 242b299)*

### Unit U10.5: Test and tidy follow-ups (T108, T109, T110, T123; D71)

**Scope:** review follow-ups that tighten tests or tidy code, no behaviour change for users: T108 (reaction-torque bad-value test asserts the field name; claim-check note counts FAIL/STALE read rows; idea.list reads CRLF front matter); T109 (drain queued Studio jobs at test teardown; delete unused BACKUP_DIR); T110 (knowledge tests cover knowledge/research/ and docs/research/ sources); T123 (old-designs test names concept-a-param or requires >= 8 folders; wing-core test asserts no neutral-pose overlap row for wng-001).

- [x] **Step 1: Briefs** (tactician W26-T) *(64a5112: tests (pins + tightening), code (claim-check note for failing read claims; Studio test drain; BACKUP_DIR removed))*
- [x] **Step 2: Build** (W26-B) *(tests b245f6b, code 6fd11e5)*
- [x] **Step 3: Review** (W26-R); merge *(both ACCEPT; merged e632358, 3ba95df)*

### Unit U10.6: Findings from Tristan's fresh-session trial (T125, T126, T128; D74; P224)

**Scope:** T128 team guide: how to start a new concept (D9: concept-a the only active design; a ledger task with owner; target mission is the VTOL demonstrator, D74) and that from-scratch concept generation is v1.1, plus a one-line mission pointer where Claude sessions will see it; T125 generated parts' `cut_files` follow each neighbour's current position, and T1 reports a part sitting inside a generated core it should be cut for; T126 `design propose` cuts the branch slug at a word boundary.

- [x] **Step 1: Briefs** (tactician W27-T) *(0c007c4: guide + CLAUDE.md mission pointer (light), slug (easy), pockets with T1.pocket (hard))*
- [x] **Step 2: Build** (W27-B) *(guide 7abf7c5, slug 06be12f, pockets faff845)*
- [x] **Step 3: Review** (W27-R); merge *(all ACCEPT, reviews/2026-11-24-w27.md; pockets merged 41ae0e7)*

### Unit U11.1: Parameter changes propagate to attached parts (T129; D75) [hard]

**Scope:** (1) expressions in references (`"$span_mm / 2 - 15"`, + - * / and parentheses over parameters and numbers only, no names beyond parameters); (2) a component position may be given relative to its parent part's attachment frame (from the interface graph joints), so moving or regenerating the parent moves its children; (3) after a regenerating `design set`, T1 interference runs on the changed parts and the result is reported in the set output. Demo target: shortening concept-a-param's span moves the fins and everything attached to them, with no new interference rows. Existing designs (absolute positions) unchanged. Coordinates with U10.6 T125 (pockets follow moved parts) on resolve.py. Cut rule D75: merge by Sun 11-29 12:00 or roadmap.

- [x] **Step 1: Design** (advisor W28-A) and briefs (tactician W28-T) *(design d10eb26; briefs 3ab30be: core (hard, after U10.6 pockets), data (variant A/B pending Tristan; A leaves a 1.0 mm elevon gap at 820 mm))*
- [x] **Step 2: Build** (builder-plus W28-B) *(core 3298078 merged f952c92; data 0cbf4e9 variant A)*
- [x] **Step 3: Review** (W28-R); merge *(both ACCEPT; data merged b4d1710; span 820: 52 parts, 58 joints moved, 0 new interference, 23.2 s)*

### Unit U11.2: Speed up design set (D81) [hard]

**Scope:** profile `plane design set designs/<copy of concept-a-param> parameters.span_mm --value 820` (cProfile, cumulative and own time, with machine load noted); if the interference step's double mesh build is confirmed, cache built meshes by generator+params hash so before/after share unchanged meshes; results (rows, masses, mesh bytes) identical with and without the cache; target: span change under 15 s on an idle machine.

- [x] **Step 1: Profile and brief** (tactician W30-T) *(5a34cab, ec99a85: span change 16-17 s; meshes already cached per process (double build ~1.5 s, mesh cache dropped); interference old+new ~8 s, needed for new/cleared; pure-Python YAML loader ~3.5 s -> brief U11.2-speed (libyaml CSafeLoader), expected 13-14 s)*
- [x] **Step 2: Build** (builder-plus W30-B) *(c421673, f0c581a)*
- [x] **Step 3: Review** (W30-R); merge *(ACCEPT after one reopen; merged 5d53a50; ~4-5 s faster under load; idle timing still to do)*

### Unit U12.1: Checks selected by aircraft type; fixed-wing standards; per-design mission (D77) [hard]

*Progress: -3/4 mission merged a354e56; -1 applicability merged c55632c; -2 fixed-wing merged d1a4642 (ACCEPT on third review, after advisor W29-A's single not-applicable rule).*

**Scope:** audit every gate/check for VTOL or concept-a assumptions; make applicability come from the design's morphology (vtol_method, lift, configuration) so non-applicable checks SKIP 'not applicable' with the reason; fixed-wing thresholds in `standards/` (stall, wing loading, static-margin band, etc.), each sourced or pending; a design-level mission block so each design is judged against its own mission (concept-a keeps the VTOL demonstrator, D74). Existing designs' verdicts unchanged.

- [x] **Step 1: Audit and briefs** (tactician W29-T) *(54625cc: briefs U12.1-1 applicability (hard), -2 fixed-wing (hard), -3 mission schema (easy), -4 mission data (easy); defaults taken (Tristan 2026-11-21 rule): fixed-wing thresholds provisional in standards/fixed-wing.yaml, pending values WARN never FAIL; mission block = name, profile, intent only)*
- [x] **Step 2: Build** (W29-B)
- [x] **Step 3: Review** (W29-R); merge *(all ACCEPT; last merge d1a4642)*

### Unit U12.2: Real-parts library (D77)

*Progress: -1 core, -2 parts, -3 BOM refs merged 7043626 (W29-R ACCEPT after one reopen each).*

**Scope:** extract concept-a's bought parts (servos, ESC, battery, flight controller, receiver, motors, props, connectors, fasteners) into a reusable library under `standards/` or `knowledge/` (decide): part id, vendor and part number, URL, mass, dimensions, and the real 3D mesh; a design references a library part instead of copying its mesh; BOM lines carry the library reference; parts without vendor CAD are marked 'representative envelope'.

- [x] **Step 1: Brief** (tactician W29-T) *(54625cc: briefs U12.2-1 library core (hard), -2 parts (easy), -3 BOM refs (easy); default taken: library in knowledge/parts/ (standards/ holds thresholds only); concept-a keeps its meshes, BOM lines get library refs)*
- [x] **Step 2: Build** (W29-B) *(e569ada, b98bc2c, 38d86bb)* *(see sub-briefs; merged so far noted at Step 3)*
- [x] **Step 3: Review** (W29-R); merge *(ACCEPT; merged 7043626)*

### Unit U12.3: Shape generators for common aircraft configurations (D77, D78) [hard]

*Progress: U12.3-1..4 merged f81bffa; -5 wing placement merged 73c9c46 (W29-R ACCEPT).*

**Scope:** a general set, not one aircraft's: `nacelle` (engine nacelle/cowl loft), `propeller` (n-blade, scale-look, spinner), richer `fuselage_loft` (nose shapes, upswept tail cone, cabin), `strut` (wing struts), `landing_gear` (fixed/spring gear, wheels), tail layouts (conventional, T, V, H) from fin + wing_panel; high/mid/low wing placement; tests with hand-checked volumes. Must cover A400M and Cessna 172 without per-aircraft code.

- [x] **Step 1: Brief** (tactician W29-T) *(54625cc: briefs U12.3-1 fuselage, -2 powerplant, -3 airframe, -4 tails (hard), -5 wing placement (easy); run in sequence)*
- [x] **Step 2: Build** (W29-B) *(see sub-briefs; merged so far noted at Step 3)*
- [x] **Step 3: Review** (W29-R); merge *(all five ACCEPT; last merge 73c9c46)*

### Unit U12.4: Reference-aircraft research template (D77, D78)

**Scope:** `knowledge/TEMPLATE-reference-aircraft.md`: the fields any real aircraft needs to become a PDL design (span, length, height, wing area, sweep, dihedral, wing position, fuselage stations, engine count/positions, tail layout, prop diameter and blades, gear) plus RC-scale guidance (scale factor, target weight, power); recon benchmarks how scale-RC builders do it; scouts fill it for A400M and Cessna 172 as tests, sources opened.

- [x] **Step 1: Research** (recon W29-X, scouts W29-S) *(template + method std/u4.33-recon f16bbae; A400M e11d841 (area -3.0%, height +1.9%); C172 c7ca127 (area -0.2%, span -0.3%); measured from Commons three-views)*
- [x] **Step 2: Review** (W29-R) *(recon d253b16; A400M be4b833, C172 dac4392 merged; reviews/2026-11-24-w29.md)*
- [x] **Step 3: Measuring tool** *(std/u4.33-measure 24a09cd ACCEPT, merged f515665)* in the repo (the recon's scratchpad scripts are not durable): `plane reference measure` reads a three-view PNG/SVG and returns scaled extents per view; brief (tactician W29-T), build (W29-B), review (W29-R)

### Unit U12.5: Local CAD overlay for licensed part models (D82, D83) [hard]

**Scope:** a git-ignored overlay folder (path from an env var or `opencae.local.json`-style local config, default `C:/Users/trist/parts-cad`) maps library part id -> local mesh (STL; STEP if trimesh can load it here) plus a placement transform (re-centre, orient to the part frame, mm); `plane parts show` reports overlay present/absent; geometry uses the overlay mesh when present, the committed envelope otherwise; mass and BOM always from the committed part; exports and build-index mark overlay-built outputs local-only and refuse to write them into tracked paths; CI never sees the overlay. Tristan's files: servo ES08MA STEP (MAII proxy), motor X2814 STL (1000 kV geometry); ESC and receiver have no CAD (envelopes stay).

- [x] **Step 1: Brief** (tactician W31-T) *(6792d4a: -1 overlay core, -2 output guard; STEP needs cascadio (not installed) else STL; defaults: library motors shaft toward -x; servo transform tuned by Tristan from fit ratios; git-ignored viewer/data and .studio count as allowed local outputs)*
- [x] **Step 2: Build** (W31-B) *(d83aada, a958887)*
- [x] **Step 3: Review** (W31-R); merge *(ACCEPT; merged 6116330)*

### Unit U13.1: Any-aircraft rehearsal (D77, D78)

**Scope:** after U12.1-U12.4 merge (and T129), a design-engineer session runs the Dec 1 prompt on a branch exactly as Tristan will, for A400M and for Cessna 172, and lists every gap; fixes go back into U12.1-U12.3; nothing from the rehearsal merges. Cut rule: rehearsal passes by Sun 11-29 12:00 or the demo falls back to concept-a-param.

- [x] **Step 1: Rehearsal** (design-engineer W29-G) *(C172: blocked — no CLI op adds components; no blank start; no airfoil source; gaps -> U13.2. A400M: built in 73 min via an undocumented add form, PR #5, 1 FAIL (static margin: generated tail invisible to T3); gaps -> U13.3)*
- [x] **Step 2: Gap fixes** (W29-B) *(via U13.2, U13.3, U12.5, U13.4)*
- [x] **Step 3: Second rehearsal** *(Tue 11-24 21:40: C172 38 min / ~60 calls, 0 FAIL, draft PR #6; A400M 47 min / ~45 calls, 0 FAIL, draft PR #7 (rehearsal 1: 73 min / ~150 calls, blocked C172). Caveat: both raised joint ratings without a source to clear T2 drop loads. Remaining gaps -> U13.6)*
- [x] **Step 4: Third rehearsal** *(Wed 11-25 ~01:00: A400M 55 min / ~75 calls, renders checked by the agent, 0 FAIL / 28 WARN, static margin fixed by moving the battery (CG x 789 mm, ~7.5 % MAC by hand), no invented ratings or requirements (placeholders listed), draft PR #8; new gap: split-wing ailerons counted as separate lifting surfaces in T3 -> U13.7-8)*
- [x] **Step 5: Fourth rehearsal** *(Wed 11-25 ~03:30: Cessna 172 from a blank design, ~35 min / ~45 calls, renders checked, 0 FAIL / 26 WARN, static margin 9.2 % MAC, wing area 100 %, draft PR #9 with all 6 CI jobs green; placeholders listed, nothing invented; gaps -> U13.8)*
- [ ] **Step 6: Fifth rehearsal**: paused by D87 until U16.1 delivers

### Unit U13.2: Design authoring from a blank start (rehearsal 1 gaps; D78) [hard]

*Progress: -4 airfoils a6b1839, -2 blank 9989382, -1 design add 969b242 merged (W31-R ACCEPT); parts A/B merged 899d9f8 (conductor keeps the two sub-gram receivers: the library is a catalogue, the design picks); C/D merged 5f544cf; -6 wing inboard 84a63e2, -3 remove-last 65db7f2, -5 generators CLI bfc6341, -8 blank-to-fixed-wing 352f11d, -7 generator docs 8b1d95d, -9 team guide d1c156b merged.*

**Scope:** from the C172 rehearsal (gap log 2026-11-24): (1) an op that appends list elements (components, attachments, bom lines) with id checks, also used by Studio edit; (2) `design new --blank` (minimal valid design: no components) and a light remove for many elements; (3) airfoils: NACA 4-digit generated on demand plus a small `knowledge/airfoils/` library, selectable by name; (4) `plane generators list/show` with each generator's params and units, and the team guide's "Starting a new concept" updated; (5) fixed-wing real parts (motor, ESC, servos, 2-blade props with spinner, receiver) in the library with vendor CAD where licensed, envelopes otherwise (scouts); (6) wing_panel multi-section (straight inboard + tapered outboard) if cheap. Existing designs unchanged.

- [x] **Step 1: Briefs** (tactician W31-T) *(92ba76a: 9 briefs U13.2-1..9 + scout spec; defaults taken: no Studio add UI before Dec 2 (CLI/MCP only); blank design has a placeholder `datum` root; flag names and blank lines after remove unchanged; NACA 2412/0012 for the 172 is a modelling assumption until sourced)* and parts research (scouts W31-S)
- [x] **Step 2: Build** (W31-B) *(U13.2-1..9 and parts A-D)*
- [x] **Step 3: Review** (W31-R); merge *(all ACCEPT; last merge d1c156b)*
- [x] **Step 4: Second rehearsal** (U13.1) *(rehearsal 2, Tue 11-24 21:40: PRs #6, #7, see U13.1)*

### Unit U13.3: A400M rehearsal gaps (D78) [hard]

**Scope:** from the A400M rehearsal (PR #5, gap log 2026-11-24, 73 min, 1 FAIL left): (1) tier-3 aero sees generated lifting surfaces: planform derived from wing_panel and tail_surfaces params (no hand-copied `planform`), so stall and static margin include the tail; (2) batch editing: many edits applied with one regeneration and one interference pass (about 150 single calls took ~50 min at 30-70 s each); (3) `design propose --draft`, title kept as given, CHANGELOG entries of one batch compacted, working tree keeps the design; (4) geometry fidelity: fuselage_loft per-station centre z if not already supported, tail control surfaces split from fixed surfaces, landing_gear in-line multi-wheel mains; (5) docs: build-index/Studio how-to. Existing designs unchanged. Items not done by Sat 11-28 18:00 move to after Dec 2.

*Progress: -2 batch apply merged ca54346 (W31-R ACCEPT; 20 edits 161 s vs 315 s single, loaded machine); -3 propose --draft a043894, -4b tails 2a4b2eb, -4a fuselage f722c0b, -4c gear 5e338e4 merged; -1 derived planform merged 899b619 (ACCEPT after one reopen; A400M static margin -6.7% FAIL -> +40.9% WARN).*

- [x] **Step 1: Briefs** (tactician W31-T) *(1fbe834: -1 derived planform, -2 batch apply, -3 propose --draft, -4a/b/c optional fidelity, -5 Studio how-to; defaults taken: `design add` is the one documented way to create elements (set --kind add stays as a field-add); batch CHANGELOG logs count and keys, values in the git diff)*
- [x] **Step 2: Build** (W31-B) *(-1 planform, -2 batch apply, -3 propose --draft, -4a/b/c, -5 Studio how-to 22f74cc)*
- [x] **Step 3: Review** (W31-R); merge *(all ACCEPT; last merge 22f74cc)*

### Unit U13.4: Visual fidelity for any-aircraft models (Tristan P250; advisor W31-A2) [hard]

*Progress: -1 mechanism recipe merged 61bfbce; -2 servo-undriven WARN 097845e; -5 design-engineer guidance 481aedc; 4a/4b/4c merged (see U13.3).*

**Scope:** from Tristan's look at the A400M in Studio: (1) wheels with tyre and hub, nose leg attaches (`front_attach_z`), in-line wheels (extends U13.3-4c); (2) tail control surfaces split (U13.3-4b as written); (3) mechanisms: a recipe (servo just ahead of the hinge line, horn from `plate`, pushrod from `strut`, `mechanisms[]` entry) in the docs and design-engineer guidance, plus a T6 WARN for a servo that drives no mechanism, and a WARN for a part body that touches nothing; (4) smoother fuselages: per-station dz plus opt-in smoothing (extends U13.3-4a). All opt-in: existing designs bit-identical (default taken). Out of scope for Dec 2, stated plainly: scale detailing (glazing, fairings, flap tracks, intakes/exhausts, airfoiled props, oleos/retracts, hollow shells, wiring). Cut: not merged by Sat 11-28 18:00 -> after Dec 2.

- [x] **Step 1: Briefs** (tactician W31-T: amend 4a, 4c; new mechanism brief) *(070163a: U13.4-1 recipe, -2 servo-undriven WARN, -3 floating-body WARN (optional), -4 team guide, -5 design-engineer agent file; 4a gains smooth_rings, 4c gains wheel_shape tyre + front_attach_z; default taken: the recipe uses a pin part at the horn end, validator unchanged before Dec 2)*
- [x] **Step 2: Build** (W31-B) *(merged: -1 recipe, -2 servo WARN, -5 agent file, 4a/4b/4c; -4 team guide mechanisms 67ff0d2, -3 floating-body WARN 959e006 (concept-a-param 6.9 s))*
- [x] **Step 3: Review** (W31-R); merge *(all ACCEPT; last 959e006)*

### Unit U13.5: Importer fixes for Dillon's concept-a-reborn (D84) [hard]

*Final dry run (f9698a0, no stand-ins): v1 import exit 0, 129 meshes, 41 FAIL (real design issues), ledger 55/5; F1 regression (3 of 113 concept-a meshes changed on re-import) fixed in place, merged d8011e0 (W31-R ACCEPT): re-import byte-identical; v1 X-mounts and WNG-001 still import closed. Dillon's guide updated (B7, B8 are his decisions).*

*Progress: -1 types+cost 7cae771, -4 STL weld ef893b9, -3 X-mount c9b2539 merged; -2 changelog adb4fcb merged (ACCEPT after one reopen; v1 import 55 decisions, 5 duplicates) (briefs keep U4.40-* names).*

**Scope:** from the W32-T dry run (u4.40/dryrun-log.md, 1ca356e): B1 STL write/reload loses watertightness (motor PRP-001-LL, wing WNG-001; `dbf.py` `_write_stl`/`_canonical`, `dbf_geometry._separate_pinches`); B2 PRP-006 X-mounts re-opened by `_clean` after union/cuts; B3 connection types CT-A-M3-CSK-MOTOR and CT-A-M3-BOLT-MOUNT missing from the importer and `standards/connection-types.yaml` (sourced or pending); B4 `calcs/concept_a.py` `bom_cost` lacks the `rship` input; B5 `changelog.py` skips decision rows whose first cell is not a bare id (D-212..D-261) and reports success with 0 imported; distinct ids for the four D-212 revisions. B7 (wing planform 71,618 vs 220,500 mm2, static margin 116 % MAC) goes to Dillon/advisor, linked with U13.6 item 6. Existing designs unchanged. Dillon's guide (u4.40/dillon-import-guide.md) is sent only after this merges.

- [x] **Step 1: Briefs** (tactician W32-T) *(311c9f4: U13.5-1 types+cost (easy), -2 changelog import (hard), -3 X-mount pinch (hard), -4 STL weld (hard); guide updated)*
- [x] **Step 2: Build** (W31-B) *(B1-B5)*
- [x] **Step 3: Review** (W31-R); merge *(all ACCEPT; last adb4fcb; end-to-end dry run before sending the guide)*
- [x] **Step 4: Send the guide to Dillon** (Tristan) *(sent, Tristan P289, 2026-11-25)* *(guide ready: plans/2026-11-20-standardization/u4.40/dillon-import-guide.md)*

### Unit U13.6: Rehearsal 2 gaps (D78) 

*Progress: -1 tail count 00fb0ad, -5 elevator-fin gap 75c0ed3, -3a bounds 95611ff, -3b render 8fe6a15, -2 list values 81a4fe7, -4 battery mesh bcbc953, -8 build-index --design 90c9496, -6 docs 1968b5a, -7 no-invention 77dad58 merged (briefs keep U4.41-* names).*

**Scope:** from rehearsal 2 (gap logs 2026-11-24): (1) document the `design apply` edit-file format and the `propulsion` block in the new-concept recipe; (2) `set`/`apply` accept list values (vectors) and remove a mid-list element; (3) a `design bounds` op (component bounding boxes, mm, body frame) and a `design render` PNG op so an agent can look at its model; (4) library meshes centred on their envelope (battery offset, stray lead stub); (5) T-tail and conventional tails: rudder/elevator clearance (T138); (6) investigate T3.static_margin on generated tails (C172 67.6 % MAC, A400M 150 % MAC; was +40.9 % with the hand wing): bug or real; (7) design-engineer guidance: never invent joint ratings or requirements to clear a check; leave them `placeholder` and report; (8) `build-index --design <id>` filter. Cut: not merged by Sat 11-28 18:00 -> after Dec 2.

- [x] **Step 1: Briefs** (tactician W31-T) *(2d60023: static margin was a bug for split tails (stabiliser counted 3x): C172 59.9 % -> 7.8 %, A400M 150 % -> 59 % (real: needs CG/tail change); reborn 116 % is a different cause (mesh wing area), row data added to diagnose. Briefs -1 tail count, -2 list values, -3a bounds, -3b render, -4 battery mesh, -5 elevator-fin gap, -6 docs, -7 agent no-invention, -8 build-index filter. Default taken: matplotlib as an optional `render` extra)*
- [x] **Step 2: Build** (W31-B) *(all 9 briefs)*
- [x] **Step 3: Review** (W31-R); merge *(all ACCEPT; last merge 77dad58)*

### Unit U13.7: Overnight follow-ups (T134, T136, T140, T141, T142, T143)

*Progress: -1 overlay baselines 32d4a47, -2 verdict date 9c83f1f, -3 servo criterion fc6760e, -4 nested remove bbf388a, -5 C172 wing area (measure-and-report by design: no code, finding committed 12f405f, fix via T145/-7), -7 core_fill 4120bad, -8 wing-area WARN 5fd6604, -9 small follow-ups d5dbb99, -10 new-design PRs pass CI 1139dd0 merged; -6 id rename 047edf5 merged.*

**Scope:** baselines/hashes/validation never depend on the local CAD overlay (T136, merged 32d4a47); pin the verdict-fixture date (T134, merged 9c83f1f); a pending criterion for servo-drives-mechanism (T140, merged fc6760e); remove in nested lists such as bom.items (T141, merged bbf388a); measure why the generated C172 wing area is 18 % low (T143; done: design gap, findings in u13.7/; follow-up T145 core fill merged 4120bad; rehearsal-3 A400M static margin 23.4 % -> 7.4 % with core_fill; T3.wing_area_complete WARN merged 5fd6604); rename old U4.x brief files and references to wave ids after all std/u4.* branches merge (T142). Existing designs unchanged.

- [x] **Step 1: Briefs** (tactician W31-T) *(d7d251d: -1 overlay baselines (hard), -2 verdict date, -3 servo criterion, -4 nested remove (hard), -5 C172 wing area measure (likely a design gap: core + ailerons), -6 id rename (last, alone); default: std/u4.25-pockets stays parked (T121) and is excluded from the rename)*
- [x] **Step 2: Build** (W31-B)
- [x] **Step 3: Review** (W31-R, W31-R2); merge *(all ACCEPT; last 047edf5)*

### Unit U13.8: Rehearsal 4 gaps

*Progress: -6 bom verify flow-style 43b72ce (T149), -2 webfetch c003443, servo scout 9008347 (4 sub-micro servos, none reaches 1.5 kg-cm), -4 sweep reference 7ca06d3, -1 pending thrust 1b12bfc, -5 scale props e97f92a, -3 apply kinds merged 0975b0f.*

**Scope:** from rehearsal 4 (gap log 2026-11-25, PR #9): `propulsion.max_thrust_n` accepts `pending` when no source gives it (schema now forces a number, so agents write 1); BOM `verified.method` enum gains `webfetch`; `design apply` CHANGELOG records each edit's kind (add/modify/remove) inside the batch entry; wing_panel sweep semantics with inboard_span documented (or a sweep_outboard param); library props as n-blade scale props instead of solid discs; small servo for 1:10 wings in the library (scout). Existing designs unchanged.

- [x] **Step 1: Briefs** (tactician W31-T) *(147b035: -1 pending thrust (hard), -2 BOM webfetch, -3 apply kinds, -4 wing sweep reference (hard), -5 scale props + servo scout; defaults taken: a webfetch stamp counts like other verification methods; generator-built library props carry vendor none, verified.method computed, a repo reference URL)*
- [x] **Step 2: Build** (W31-B)
- [x] **Step 3: Review** (W31-R, W31-R2); merge *(all ACCEPT; last 7ca06d3)*

### Unit U14.1: Dec 2 presentation package

*Deck updated for D77/D78 (merged 9b1110f): slides 8-10 new (any aircraft, rehearsals measured, honest limits), live-demo slide from the script; PR #8 CI green after U13.7-10.*

*Briefs 96c27aa: U14.1-2 demo script (A400M prompt flow), U14.1-1b deck update. Defaults taken for Tristan to confirm in the morning: demo = pre-built PR #8 plus one live change (A400M wing span if set + tier-1 validate < 60 s on a fresh clone with no new FAIL, else the concept-a-param span step, D75); CAD overlay off on stage (one optional local click); prompt text = the tactician's proposal ending "do not invent ratings, prices or requirements".*

- [x] **Step 1:** Slides deck (Claude Slides artifact; download .pptx/PDF if needed): problem (15 interfaces, rules forgotten, code edits per design) → PDL → ops/CLI/MCP/Studio → gates T0–T8 → harness → PlaneBench results → what's next.
- [x] **Step 2:** Live demo script (8 min), each step one command or click: `plane design new` from a template → `plane design set` a wing mass → `plane design validate` → Studio Physics mode playing the flap mechanism → `plane design propose` → the PR → `plane update publish` → the one link. Recorded backup video. *(rewritten for the A400M prompt flow, merged 7dc0054; live change = concept-a-param span (A400M span change left 8 overlap FAILs); every number cited)*
- [x] **Step 3:** Metrics slide filled from §2.1 with measured values (not targets).
- [ ] **Step 4:** Dry run Mon 11-30 evening; fix only what the dry run breaks.

### Unit U15.1: Control surfaces follow their wing (T130; demo-script Issue 6) [hard]

**Scope:** an aileron, elevator or flap generated from a wing's planform today repeats the wing's span, chords and sweep in its own `geometry.params`, so a wing-only `design set ...span` leaves the surface stale (A400M: 8 new T1 hinge-overlap FAILs at span 1800, u4.2/demo-script.md Decisions 2). Make generated control surfaces derive their planform from the parent wing (reference the wing component's params, or a design `parameters:` entry, or a surface generator that reads the parent), so one wing change regenerates the surfaces and their hinges with no new FAIL. Document it in the new-concept recipe. Existing designs unchanged (byte-identical meshes and baselines) unless they opt in.

- [x] **Step 1: Brief** (tactician W34-T) *(4efe4c6: hard; planform via `$wing_span_mm` clears the 8 FAIL with no code; hinges via new opt-in `hinge_from: generator`; tail hinges out of scope (follow-up))*
- [x] **Step 2: Build** (builder-plus W34-B)
- [x] **Step 3: Review** (W34-R); merge; check on a scratch copy of PR #8's a400m-rc that span 1800 gives no new FAIL *(merged cec9f41; W34-R2 REOPEN once (team-guide line order), ACCEPT)*

### Unit U15.2: Small fixes (T19, T111; T101 already fixed)

**Scope:** T19 `standards.pending` also reads gate-thresholds.yaml (wire_clearance_mm, wing_area_complete_min, servo_must_drive_mechanism; blocks the 12-08 flip) and CT-M3-SHCS-INSERT cites its source; T111 `plane design new/set` write LF on Windows; T101 bench `_map_args` maps only argument values that name parameters. No threshold or gate-behaviour change.

- [x] **Step 1: Briefs** (tactician W34-T) *(4efe4c6: -1 pending reads gate-thresholds (T19), -2 design new writes LF (T111); T101 already fixed on main e72f545; T19 second half already on main)*
- [x] **Step 2: Build** (builder W34-B) *(-1 pending-gates merged 3a6b9d7; -2 LF merged ac3af45 (W34-R ACCEPT))*
- [x] **Step 3: Review** (W34-R); merge

### Unit U15.3: Faster plane CLI start-up (T124) [hard]

**Scope:** every agent call pays about 4.4 s of start-up (hangar.checks import 1.75 s, mostly trimesh -> scipy/networkx). Measure with `python -X importtime`, lazy-import the heavy modules where the op does not need them, and report before/after for `plane --help`, `design get`, `design set`, `design validate --tier 1`. Outputs byte-identical; no behaviour change.

- [x] **Step 1: Brief** (tactician W34-T, with the importtime profile) *(4efe4c6: hard; trimesh 2.26 s of 2.63 s import; lazy proxy; merge after U15.1)*
- [x] **Step 2: Build** (builder-plus W34-B)
- [x] **Step 3: Review** (W34-R); merge *(merged 5b2221b, W34-R3 ACCEPT; --help 8.8 -> 3.5 s; get/set on parametric designs wait for step 4, D102)*
- [ ] **Step 4: Lazy mass_g** (U15.3-2, D102): brief, build, review

### Unit U16.1: 3D generation close to the real aircraft (I2; D85, D87) [hard]

**Scope:** generated models carry real mechanical content, not only shapes: control surfaces on hinge joints driven by servo -> horn -> pushrod -> control horn linkages that move kinematically and do not clip; wheels as separate parts on axle joints that roll; library parts placed where they really go (servos in wing/fuselage bays, not floating); wires as routed harness geometry between real connectors; joints and fasteners visible in the model. Exported to Studio and MJCF so the mechanisms play. Step 1 decides the order; each later step is one brief. Existing designs unchanged unless they opt in. Rehearsals resume when Tristan judges the output close to the real deal (D87).

- [x] **Step 1: Recon and design note** (recon W34-X, then advisor W34-A): `u16.1/recon.md`, `u16.1/design-note.md` *(build order S0 showcase c172-rc on main, S1 four-bar solve (rod posed server-side), S2 wheels on axles, S3 servos in bays, S4 linkage generator op, S5 = U16.2, S6 hinge gap/bevel, S7 mjcf-kinematic, S8 wires as tubes, S9 visual detail + x-ray; PDL 1.3 three optional fields; all opt-in, export sha256 unchanged on existing designs; D90)*
- [x] **Step 2: Briefs** (tactician W34-T5) from the design note, S0 and S1 first *(52e43ea: S0 easy; S1-S4 hard, each with a designs-only Part B; S6-S9 outlines; PDL 1.3 opened by S1; chain S0 -> S1 -> S2 -> S3 -> S4; S0 check: c172-rc on main 0 FAIL / 26 WARN, baseline unchanged; D96)* *(S6-S9 re-briefed 11653fa: S6 hinge geometry, S7 mjcf-kinematic (prototype matches S1 hand angles to 4 decimals), S8 wires (after S1, S3, U19.1 B2), S9a clevis, S9b screws, S9c fuselage wall (Part B on Tristan's word); x-ray dropped (B3); D101)*
- [ ] **Step 3: Build** (W34-B), one brief at a time in the note's order *(S0 c172-rc showcase merged 75c5c2c (PR #12, W34-R ACCEPT); S1 four-bar building)*
- [ ] **Step 4: Review** (W34-R); merge; Tristan looks at the result in Studio

### Unit U16.2: Pose-aware cut pockets for generated parts (was U10.3; T121; D70; P284) [hard]

*Moved from W10 on 11-25 (P284): the parked branch std/u4.25-pockets is 348 commits behind main (3 ahead). Refresh it onto main first, then re-measure against the tier-1 budget; U16.1's design note decides whether its approach (subtract swept poses) or real hinge geometry replaces it.*

**Scope:** `cut_files` subtract the union of a neighbour's swept poses (mechanism range), so concept-a-param's 10 extra tier-1/T6 FAIL rows (wng-007 swept poses, mec-002 range ends, elevon collisions) disappear; concept-a-param's baseline refreshed in a separate designs-only commit; existing designs unchanged.

- [x] **Step 1: Brief** (tactician W24-T) *(dcd6f1d: builds after U9.2 Part B and U10.2-g1fixes merge)*
- [ ] **Step 1b: Refresh** (builder-plus W34-B2): merge main into std/u4.25-pockets (no force push), tests green, re-time tier-1 on concept-a-param *(refresh stopped: 12 swept-pose rows gone but 2 T1.pocket slivers; W34-A3 diagnosis u16.2/diagnosis.md: float32 operands in manifold3d; fix = float64 operands for the cut_files difference (0 FAIL); tier 1 ~99 s loaded vs ~70 s budget (D73): Tristan decides relax to ~90 s / park for a core speed unit / keep out of v1; fix being built, merge waits)*
- [ ] **Step 2: Build** (builder-plus W24-B) *(parked on std/u4.25-pockets: correct (all 14 swept-pose rows gone) but tier-1 validate 54-63 s vs 60.2 s budget; kept out of the demo, v1.1, D71; D73 retry with W24-A convex hulls also missed: tier-1 98-111 s, planform -16.4 % FAIL; parked again, T121)*
- [ ] **Step 3: Review** (W24-R); merge

### Unit U17.1: Source every gate threshold (D88; T19, T82)

**Scope:** list every threshold in standards/*.yaml whose source is `pending`, an internal convention or a team constraint (about 50 pending, about 45 convention, 11-25 count); rank them by how many blocking check rows they drive on all designs; scouts find opened sources (datasheets, standards such as FAA AC 43.13, MIL-HDBK-5/MMPDS, ASTM, manufacturer data, RC references with stated test conditions) per packet; a builder writes the sourced value or keeps `pending` with the reason; re-run all designs and report the fidelity line before/after and which rows changed. Standards and knowledge only; baselines refreshed in separate designs-only commits. James reads the values.

- [x] **Step 1: Inventory and packets** (tactician W34-T2) *(48791cb: 96 entries, 9 packets, 21 team decisions; 518 blocking rows have criteria that resolve to no threshold (D91); connection types move 0 rows (U8.3))*
- [x] **Step 2: Sources** (scouts W34-S, up to 3 at a time; worktree C:/Users/trist/wt/u17.1, branch std/u17.1-sources) *(9 packets + a second pass with pdftotext for binary PDFs; about 45 source files; disagreements for the team: tip_angle_max_deg 30 vs ~15 deg tip-back, fw_static_margin_max 0.25 vs 0.05-0.15, wire_clearance_mm 5 vs 9.5-12.7 mm (AC 43.13-1B), LulzBot Z 256 vs 250 mm, attach/planform tolerances looser than printer accuracy, XPS 25 kg/m3 below the denser grades; hover-moment rows unsourced)*
- [ ] **Step 2b: Criteria that resolve to no threshold, and team-constraint owner/date in the fidelity count** (D91; tactician brief, builder-plus) *(briefs e6c36eb: -criteria (hard) building; -team-owner Part 1 after values merges; Part 2 held for Tristan (D100))*
- [x] **Step 3: Values into standards; re-run; baselines** (W34-B) *(merged 0f67f27: 8 entries sourced, no value changed, fidelity +1 per design; disagreements listed for Tristan)*
- [ ] **Step 4: Review** (W34-R); merge; fidelity line before/after in the plan

### Unit U18.1: OpenCAE CLI as hangar's physics backend (D89; P282) [hard]

**Scope:** OpenCAEModel main (11-24) ships an `opencae` CLI (`doctor`, `new`, `run --only mass,propulsion,structure,cfd,flight --json`, `iterate --set`, `status`) with evidence-status rules close to hangar's (estimate/datasheet/measured). Integrate it as an external GPL program: a hangar op exports a design to an OpenCAE drone project (drone.json from PDL propulsion, battery, ESC, materials, requirements; geometry from the GLB/STL export), runs `opencae run --json`, and maps results to check rows: propulsion current margins (motor, ESC, battery) and thrust-to-weight, structure safety factor (replacing or alongside the old opencae_runner FEA route), whole-aircraft CL/CD/LD from SU2 CFD, hover flight for VTOL/tailsitter. SKIP with the reason where OpenCAE or a solver is missing (CI). Results cached and hashed like FEA. No OpenCAE source copied (PROVENANCE row).

- [x] **Step 1: Integration study and briefs** (tactician W34-T3) *(77414cd: study + fixtures; OpenCAE runs in qt_test; quad250 mass/prop 1.4 s, structure 27 s, flight 1.9 s, SU2 CFD 11 min; concept-a-param mass matches except 2 meshless point masses; briefs -1 cli (hard), -2 export (hard), -3 rows (hard, after -1), -4 ops (easy, after -1 and -2); D93)*
- [ ] **Step 2: Build** (W34-B) *(-1 cli merged d2105bd (one REOPEN: Linux test), -2 export merged 2ba4033; -3 rows merged c0a851b (W34-R ACCEPT, D98); -4 ops building)*
- [ ] **Step 3: Review** (W34-R); merge

### Unit U18.2: Calibration against a real aircraft (D89; P280)

**Scope:** run hangar's mass, aero and performance checks on the full-size Cessna 172S with published figures (POH / type certificate data: MTOW, wing area, span, stall speeds Vs/Vs0, cruise speed, rate of climb, CG range) entered as a reference design or fixture; compare each computed number with the published one and write the error; a test pins each within a stated tolerance (tolerances in standards with a source or `pending`). Findings say which checks are trustworthy and which are not.

- [x] **Step 1: Brief** (tactician W34-T4; scout W34-S for the published figures, opened sources only) *(aec87ed: scout -scout-c172 then -calibration (hard); C172S fixture in tests/fixtures, not designs/; tolerances in new standards/calibration.yaml, pending; default-CLmax stall error +30.7 % pinned as a finding)*
*Unblocked 11-25 (second scout pass, PDF text via pdftotext): TCDS 3A12 Rev 84 (2015, Univair mirror) and the 172S handbook Rev 5 (2004, BEFA copy) read; sources on std/u18-sources. Neither confirmed as the current revision.*
- [x] **Step 2: Build** (W34-B)
- [x] **Step 3: Review** (W34-R); merge *(merged 5f694b3 with the C172S sources; W34-R2 REOPEN once (source assertion), ACCEPT; default CLmax 1.1 reads stall +18.4 % vs Vs1 (flaps up) and +30.7 % vs Vso (flaps 30); implied CLmax 1.54)*

### Unit U18.3: Wing spar bending by beam theory (D89; P280)

**Scope:** a fast analytic check for every winged design in CI: root bending moment at the design load factor (elliptic or Schrenk lift distribution), spar stress from the spar section (tube or generated spar params) and material allowables, tip deflection; safety factor against the sourced material yield; thresholds in standards with a source. FEA (U18.1 structure) stays the detailed check; a test compares both on one wing.

- [x] **Step 1: Brief** (tactician W34-T4) *(aec87ed: -spar-bending (easy) + scout packet B (allowables); FEA comparison deferred to U18.3-2 after U18.1 merges)*
- [x] **Step 2: Build** (W34-B)
- [x] **Step 3: Review** (W34-R); merge *(merged 088ce2d; W34-R2 ACCEPT after the pinned-rows hash fix; CFRP/6061 allowables now sourced on std/u18-sources, wiring them into spar.yaml is a follow-up)* *(follow-up merged 4f05c04: cfrp-tube allowable 1379 MPa, modulus 127553 MPa (Goodwinds minimums); concept-a-param spar PASS RF 16.4)*

### Unit U18.4: Trim and stability (D89; P280) [hard]

**Scope:** elevator deflection to trim at cruise and at stall speed vs its travel; horizontal and vertical tail volume coefficients vs sourced typical bands; dynamic modes (short period, phugoid, Dutch roll, spiral) from AeroSandbox or AVL with damping thresholds from a source (e.g. MIL-F-8785C levels) or `pending`. Fixed-wing and transition designs only.

- [x] **Step 1: Brief** (tactician W34-T4) *(aec87ed: -1 tail volume, -2 trim, -3 dynamic modes (all hard) + scout packet A; AeroSandbox opt-in, not in CI (modes SKIP there); merge order U18.3-1, U18.4-1, -2, -3)*
- [ ] **Step 2: Build** (builder-plus W34-B) *(-1 tail volume merged ca908c6 (W34-R ACCEPT; bands pending: Raymer gives class points); -2 trim next)*
- [ ] **Step 3: Review** (W34-R); merge

### Unit U19.1: Studio UI overhaul and a better 3D viewer (D92; P285) [hard]

**Scope:** a big UI improvement to Studio (viewer/, three.js 0.160 from CDN, core/hangar/studio.py), the 3D viewer first: lighting and materials (PBR, environment light, shadows, edge lines), part selection with highlight and a part tree, section/clipping planes and x-ray, measure tool, exploded view, standard views and a view cube, smooth orbit/pan/zoom with fit-to-selection, playing mechanisms (U16.1 linkages, wheels) with a timeline, check rows shown on the parts they concern (FAIL in red), and a cleaner layout for the other panels (scorecard, BOM, edit, compare). Performance on concept-a (100+ meshes). The public viewer build keeps working; Playwright tests for the click paths (install it in .venv if missing). Step 1 decides the order.

**Must-haves (Tristan P286):** explode the view (slider, by assembly level); move parts by dragging them (view-only by default; an explicit Apply writes the new position through the edit op with `--why`, so the design and CHANGELOG change only on purpose; T1 re-runs on the moved part); see inside the plane (x-ray / transparent skin, section plane, hide/isolate) so internal parts such as the battery, ESC, servos and wires are visible and selectable.

- [x] **Step 1: Recon and UI spec** (recon W34-X2, then advisor W34-A2): `u19.1/recon.md`, `u19.1/ui-spec.md` *(extend our three.js app; three panes (part tree, viewport + toolbar/view cube/apply bar/timeline, inspector); Apply via existing /api/op/design.set; steps B0 three upgrade + one renderer + split app.js, B1 lighting/edges, B2 tree + parts.json, B3 see inside, B4 explode + timeline, B5 move + apply, B6 part ids on check rows (core, first as its own PR), B7 layout, B8 measure + view cube; concept-a GLB 2.29 MB / 118k tris; D95)*
- [x] **Step 2: Briefs** (tactician W34-T6) from the spec *(277de38: B6 part ids (easy, core, own PR), then B0 three 0.180 + split + Playwright, B1 look, B2 tree/inspector/parts.json, B3 see inside, B4 explode + timeline (Physics tab folds in), B5 move + apply, B6b colour by status, B7 layout, B8 measure + cube; strictly sequential after B0; D97)*
- [ ] **Step 3: Build** (W34-B), one brief at a time *(B0 three 0.180 + split merged 335d304; B6 part ids merged 594c831 (PR #13, migration label); B1 look merged b7e3ade; B2 tree/inspector next)*
- [ ] **Step 4: Review** (W34-R); merge; Tristan tries it in Studio

## 8. Not doing for v1.0 (YAGNI; ledger status `dropped` with this file as `decided_in`)

- Mechanical fidelity of generated models (D85): wheels as separate rolling parts, kinematic servo-pushrod-horn linkages, control surfaces that never clip; a post-Dec 2 milestone with R11 interactive physics (idea I2).

- Surrogate models (R37): only worth it for families of tens–hundreds of variants; `design.sweep` rows are already the training-data format, so v1.1 can add them.
- A full DaVinci build (R29) unless D3 is answered by 11-23.
- Assembly-planning agents in the style of the other team's configuration-space work: watch, don't build.
- Real airfoil aero beyond AeroSandbox VLM; CFD (DBF-Combined's `analysis/cfd3d` stays there).
- SITL as a blocking gate: the `sitl` adapter reports flight-case results only.
- Re-importing K09-L, C0 rev G or v0.3.1 as active designs (D9).
- A custom agent-launcher/router like the advisor's; Claude Code agents + hooks cover v1.0.

## 9. Risks

| Risk | Sign | Response |
|---|---|---|
| Usage limits (team hit them on 11-11) | conductor > 40 % weekly use by 11-24 | Haiku-first per §5; advisor only on twice-failed units; no Opus builders |
| U1.1 slips and blocks everything | not merged by 11-22 18:00 | W2 units start on the old CLI with ops stubs; U1.1 lands behind them |
| Gates too strict → nothing accepted | concept-a fails T6–T8 everywhere on 11-25 | D7 default: T7/T8 report-only; T6 blocking only for declared mechanisms |
| Thanksgiving week availability | no PRs 11-26/27 | W3 sized for 3 days; U3.3 can drop to 1 task |
| Agents add instead of subtract | CHANGELOG `kind: add` > 50 % in U3.4 | `design-iterate` requires written reason for add; reviewer scores it |

## 10. Self-review (done 2026-11-20)

- Spec coverage: every R1–R40 maps to a unit or to §8 with a reason; every row of §1b maps to a unit or says why it is not imported.
- Names checked across units: `call`, `registry`, `OpResult`, `run_gates`, `Ledger.set`, `design.set/sweep/propose`, `get_adapter`, `load_roster`, `load_claims`, `import_proofs1` are defined once (U1.1, U2.1, U0.3, U1.4, U2.3, U0.1, U1.5) and used with the same signatures later.
- Review Focus items each have a test in their owning unit (U1.1, U1.4 ×2, U2.3, U0.3).
- Proportion: code shown only as tests and signatures; bodies left to builders.
