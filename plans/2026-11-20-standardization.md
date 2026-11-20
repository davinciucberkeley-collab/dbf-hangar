# DBF Hangar v1.0 Implementation Plan (CLI, Plane Design Language, one surface)

Repo: [davinciucberkeley-collab/dbf-hangar](https://github.com/davinciucberkeley-collab/dbf-hangar). Owner of every unit: **Tristan**. Teammates (Dylan, James, Vibhav) are users and acceptance testers; Douglas is the advisor.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan unit by unit. Steps use checkbox (`- [ ]`) syntax for tracking. Every unit is one branch and one PR. Agents come only from `.claude/agents/` (see §5).

**Goal:** By Tuesday 2026-12-01, one new repo (`dbf-hangar`) holds what the team's other repos do, rebuilt to one standard, and every team task (new design, design change, analysis, research, morphological chart, BOM check, assembly test, weekly update) can be done by an agent or a teammate through one `plane` CLI on one shared design language, without editing code, and the result is visible at one link.

**Architecture:** One operations layer (`core/hangar/ops/`) is the API. The `plane` CLI, the MCP server and Plane Studio are generated from it, so there is one way to do each thing. Designs are data in the Plane Design Language (PDL v1.0, `schema/plane.schema.json`); analyses are gates and adapters that read PDL and never require code edits to accept a new plane. A team harness (`.claude/agents/`, hooks, ledger) makes the agent rules part of the system instead of a file agents forget.

**Tech Stack:** Python 3.12, click, jsonschema, ruamel.yaml, trimesh/manifold3d, MuJoCo 3, mcp ≥1.2, pytest; OpenCAE Studio (CalculiX) via adapter; vanilla JS viewer on GitHub Pages; Claude Code agents, hooks and output styles.

**Spec:** §1–§4 of this file (the spec and the plan travel together, per the team's request for one file). Sources: DBF weekly check-in transcripts 2026-11-04, 2026-11-11, 2026-11-18 (team Drive folder "161 Design-Build-Fly"); repos `aircraft-platform` @ `f462468`, `DBF-Combined` @ `a93f14d` (itself a snapshot of DBF-VTOL, DillonVTOL, TiltWing and OpenCAEModel, see its `PROVENANCE.md`), `OpenCAEModel` @ `792f0ab`.

## Global Constraints

- Deadline: presentable v1.0 on **2026-12-01**. Feature freeze **2026-11-29 18:00 PT**; after it only fixes from review.
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

1. **A teammate's design that the importer has never seen** (e.g. Dylan's next CAD revision with a new part type): expected to load, migrate and get a scorecard with SKIPs naming what is missing, never a traceback. Pinned by `tests/test_ops_contract.py::test_unknown_component_type_gives_skip_not_crash` (U1.1).
2. **Windows paths and line endings** in every op (`designs\concept-a`, CRLF YAML): expected identical results to Linux. Pinned by `tests/test_paths.py::test_backslash_and_crlf_roundtrip` (U1.4) and the Windows CI job.
3. **`design.set` on a path that does not exist, or a value of the wrong type**: expected exit 2 with the schema path and the allowed type, file untouched. Pinned by `tests/test_design_edit.py::test_set_rejects_bad_path_and_type_without_writing` (U1.4).
4. **An external tool missing** (OpenCAE not installed, DaVinci not connected, MuJoCo import fails on a laptop): expected SKIP with the fix command from `plane tools doctor`, and `accepted` stays false with a reason, never a silent PASS. Pinned by `tests/test_adapters.py::test_missing_tool_is_skip_with_fix` (U2.3).
5. **A ledger item closed as "dropped" vs "not done"** (advisor, 11-18: Claude marks decided-against items as overdue): expected `dropped` to require `decided_in:` and never appear in the overdue list. Pinned by `tests/test_ledger.py::test_dropped_needs_decision_and_is_not_overdue` (U0.3).

---

## 1. What was asked (traceability)

Every requirement has an id. The ledger (U0.3) is seeded from this table; a unit is not done until its R-ids are marked `done` with evidence (PR or file), or `dropped` with a decision reference. "A" = advisor (Douglas), "T" = team member.

| R | Who / when | Requirement (paraphrased from the transcript) | Unit(s) |
|---|---|---|---|
| R1 | A 11-11, 11-18 | A consistent file format for a plane ("schema"): if Tristan submits a plane to the system Dylan works in, it drops into the same bucket; CAD files go here, BOM goes here | U1.3 |
| R2 | A 11-11 | CLI **and** MCP so different agents interface with one app; `plane add …` instead of agents editing HTML per plane | U1.1, U1.2 |
| R3 | A 11-18 | API → CLI on top → simple natural-language layer on top of that (skills) | U1.1, U1.2, U3.2 |
| R4 | A 11-18 | Separate operations and data from code; don't edit code every time you run a simulation; saves tokens | U1.1, U1.4, U2.3 |
| R5 | A 11-18 | Bring in new plane designs without changing design-software code ("put a window in, don't remove bricks") | U1.4 (CI rule), U2.1 |
| R6 | A 11-18 | Lots of new things, **no new interfaces**; you have ~15, need ~3; one interface, different modes, one design language, one surface | U3.1 |
| R7 | A 11-18 | Stretch: every team task doable via CLI without editing code: sending designs, updating morphological chart, sending an idea, researching, consolidating, testing assembly, Dylan's tasks | U1.4, U2.4, U3.4 |
| R8 | A 11-18 (to Tristan) | CLI lets Claude test a design, change one parameter, re-test, see how it evolves, iterate fast | U1.4 (`design.set`, `design.sweep`) |
| R9 | A 11-18 (to Vibhav) | OpenCAE behind a CLI: can an agent run a full simulation + design iteration without editing or crawling code? then can Dylan? | U2.3, U3.4 |
| R10 | A 11-11 | Success conditions close to the real goal, hard enough Claude can't meet them unless it works: full 3D physics sim where parts can't pass through each other; mechanism works there or it doesn't; NASA standards; lift ratio | U2.1, U2.2 |
| R11 | A 11-18 | Rigid-body physics (frictionless first) to check mechanisms: motor motions, flap movements, "if you pull this, does it pull that"; drop the drone in and drag it around | U2.1 (T6), U3.1 (Physics mode) |
| R12 | A 11-11 | Gates: transport by car (the box), no exposed wires and rules for how wiring works | U1.3, U2.1 (T7) |
| R13 | A 11-11 | Database of plane guidelines and standards every design is evaluated against; manufacturing methods; "does a tailsitter actually work?" evidence | U2.2 (builds on `knowledge/`, `standards/`) |
| R14 | T 11-11 (Dylan) | BOM: verify parts are real (Amazon blocks agents → use Claude in Chrome) | U1.3 (`bom`), U2.4 (`bom.verify`) |
| R15 | A 11-18 | Claude adds, rarely subtracts; fixes must consider add / subtract / modify / adjust and not add unless needed; weight is the constraint | U1.4 (change kind log), U3.2 (`design-iterate` skill), agent `design-engineer` |
| R16 | A 11-18 | Iterative research at every step: "wing too heavy → research how others fixed it without adding parts"; recon + benchmarking | U3.2 (`recon` skill), agent `recon` |
| R17 | A 11-18 | Hardest goal first: working, non-placeholder mechanisms before weight | §6 ordering, U2.1 T6 before T8 |
| R18 | A 11-18 | Agent roles by **type and level** of work, not domain; Haiku builds, Sonnet for hard; tactician Sonnet (hard → Opus); advisor Opus; one conductor decides; batch of ~10 units → fresh Opus reviewer | U0.1, §5 |
| R19 | A 11-18 | Embed rules in the system: hook on agent launch asking "did you follow the rules", role must be picked; roles + output styles in Claude Code; hooks and looping prompts | U0.1, U0.2 |
| R20 | A 11-18 | Every prompt logged; agent may not stop until each prompt is marked addressed; compaction re-loads the task file; tasks in files, not memory | U0.2, U0.3 |
| R21 | A 11-18 | Hourly "get it together" audit (cheap Haiku): rules broken, stuck agent, plan drift; a fix that fails twice means something is wrong → advisor | U0.2, U3.2, agent `auditor` |
| R22 | A 11-18 | Plan before executing (scheme): max effort for planning, waves by dependency, units ≈ one PR each, one agent per unit; broken unit is fixed in place, not patched with a new unit; surface unknown decisions and a permissions prompt up front | §4–§6, U3.2 (`plan-scheme`) |
| R23 | A 11-18 | Pointer files: AGENTS/CLAUDE.md point to rule files, not contain them; trim bloat (280 stale items) | U0.1, U4.1 |
| R24 | A 11-18 | Team harness repo + install script so every teammate's Claude gets the same roles | U0.2 (`harness/install.py`) |
| R25 | A 11-18 | Multiple PRs on the same plane from different people/agents; Dylan picks which to merge | U1.4 (`design.propose`), §4 |
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
| DBF-Combined : `redesign/TEAM.md` (40 discipline roles) | agent roles by discipline | not imported: replaced by the 10 work-level roles (R18); its useful checklists become gate criteria | — |
| DBF-Combined : `analysis/`, `cad/` (SOLIDWORKS rev G), `inventory/`, `fusion/` (v0.3.1), `explorations/tiltwing/`, `sim/` | earlier design states (C0 lift+cruise, K09-L, tiltwing) | `status: retired` designs only where aircraft-platform already has them (`c0-*`, `tiltwing-cakir`); the rest stays in DBF-Combined, linked from `PROVENANCE.md` | U2.5 |
| OpenCAEModel @ `792f0ab` (= DBF-Combined `tools/opencae-studio/`) | CalculiX-based CAE app, GPL-3.0 | external dependency behind the `opencae` adapter; hangar pins the version | U2.3 |
| DBF-VTOL, DillonVTOL, TiltWing | already inside DBF-Combined (its `PROVENANCE.md`) | nothing extra | — |

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
| `bom` | `list, verify, cost` | real parts |
| `assembly` | `animate` | assembly test |
| `morph` | `list, add-option, coverage` | morphological chart |
| `idea` | `add, list` | send an idea |
| `research` | `new, check` | research into templates |
| `ledger` | `add, ingest, set, check, report` | tasks from meetings |
| `update` | `new, add, publish` | weekly update |
| `bench` | `list, run, report` | PlaneBench |
| `claim` | `list, explain, check` | why a number is believed |
| `davinci` | `push, pull` | DaVinci build (D3) |
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

Each has a default the plan uses if nobody answers by the date. Recorded with `plane ledger add --kind decision`.

| D | Question | Default if unanswered | Ask | By | Status |
|---|---|---|---|---|---|
| D1 | Name of the language: PDL? keep `plane.yaml`? | PDL, file stays `plane.yaml` | — | 11-21 | decided: default (Tristan, 2026-11-20) |
| D2 | Dec 1: who is the audience (Douglas only, Kosa, class?), live demo or recorded, length? | Douglas + Kosa, 10-min live demo + Slides deck, recorded backup | Douglas | 11-22 | decided: default (Tristan, 2026-11-20) |
| D3 | DaVinci API: who has access, which account, is a Claude connector set up? | adapter ships as SKIP-with-reason; full DaVinci build moves to after Dec 1 | Douglas / Chris (Slack) | 11-23 | decided: default (Tristan, 2026-11-20) |
| D4 | Harness in hangar (`harness/`) or its own repo? | in hangar; `harness/install.py` installs it on any teammate's machine | — | 11-21 | decided: default (Tristan, 2026-11-20) |
| D5 | Transport box size and wiring clearance | box from DBF-Combined's constraint (K09-L box about 1.25 × 0.55 × 0.45 m) marked `source: team constraint`; clearance `pending` | Dylan | 11-24 | decided: default (Tristan, 2026-11-20) |
| D6 | Hover T/W 1.5 vs 2.0, landing factor 3.0 vs STANAG 3.8 (both `pending`); concept A's claims use T/W ≥ 1.6 | one value per key, chosen from sources found in U2.2, recorded as a decision | Dylan | 11-25 | decided: default (Tristan, 2026-11-20) |
| D7 | Does accepted require T6–T9 for v1.0, or report-only first? | T6 and T9 blocking; T7/T8 report-only (WARN) until 12-08 | — | 11-24 | decided: default (Tristan, 2026-11-20) |
| D8 | Binary files: Git LFS in hangar, or meshes stay in DBF-Combined and hangar stores `{repo, commit, path, sha256}` references? | LFS for the meshes the gates need (concept A, about 130 STL); CAD sources referenced, not copied | — | 11-21 | decided: default (Tristan, 2026-11-20) |
| D9 | Which design states are active? | concept A active; K09-L, C0 rev G, v0.3.1, tiltwing `retired` | Dylan | 11-22 | decided: default (Tristan, 2026-11-20) |
| D10 | Archive DBF-Combined and aircraft-platform (read-only) once hangar v1.0 is out? | yes, after 12-01, with a README pointer to hangar | team | 12-01 | open: decided when v1.0 is done |

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
| verification-before-completion | `pytest -q && plane design validate --all --json && plane ledger check` pasted in the PR | implementer |
| finishing-a-development-branch | PR → wave review → merge to `main` by Tristan | Tristan |

Scheme rules on top (R22, R25):
- **Waves** are dependency layers; units inside a wave run in parallel.
- **Unit = one PR.** If a unit's PR is rejected, the same unit is reopened and fixed; no "fix-for-the-fix" unit.
- **Plan is the source of truth**, not the conductor's memory. Agents get the unit text from this file, not a paraphrase. Status changes are checkbox edits here + `plane ledger set`.
- **Design work goes through PRs too**: several agents/people may open `design.propose` PRs on the same design; Tristan merges (Dylan approves concept-a changes, R25).
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
| W0 Seed, harness & ledger | Fri 11-20 → Sat 11-21 | U0.4 first, then U0.1, U0.2, U0.3 in parallel |
| W1 Ops layer & PDL | Sat 11-21 → Mon 11-23 | U1.1 [hard], U1.2, U1.3 [hard], U1.4, U1.5 [hard], U1.6 |
| W2 Gates, adapters, import, team ops | Mon 11-23 → Wed 11-25 | U2.1 [hard], U2.2, U2.3 [hard], U2.4, U2.5 [hard] |
| — async check-in (no meeting) | Wed 11-25 | `plane update publish` → link in the Drive doc |
| W3 One surface, skills, proof | Wed 11-25 → Sat 11-28 (Thu 11-26 Thanksgiving, light) | U3.1 [hard], U3.2, U3.3, U3.4 |
| Freeze | Sun 11-29 18:00 | — |
| W4 Review, release, presentation | Sun 11-29 → Mon 11-30 | U4.1, U4.2 |
| Present | **Tue 12-01** | demo + deck |

All units: Tristan. Acceptance testers: Dylan (Studio, concept A), Vibhav (OpenCAE on Windows), James (harness install on his machine).

Ordering follows R17: T6 mechanisms lands before T8 sourcing; U3.4 (an agent iterating concept-a with no code edits) is the acceptance test of the whole plan.

---

### 6a. Core path and cut order (scope check, 2026-11-20)

The Dec 1 demo needs only the **core path**: U0.4 → U0.2/U0.3 → U1.1 → U1.3 → U1.4 → U1.5 → U2.5 → U3.4 (+ U4.1/U4.2). Everything else is in the cut order below, so a slip never threatens the demo. The conductor cuts from the top of this list as soon as a wave runs > 12 h late; a cut unit gets ledger status `dropped` with this section as `decided_in`.

| Cut order | Unit | What is lost if cut | Fallback for the demo |
|---|---|---|---|
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
| Mon 11-23 | Dylan | `plane design set` one concept-A mass on a branch, `plane design validate`, `plane design propose` | PR link |
| Tue 11-24 | Vibhav | `plane tools doctor` + `plane fea run designs/concept-a --part <one>` on Windows | output pasted in ledger |
| Wed 11-25 | all | `plane update add` own line; Tristan runs `plane update publish` | the link |
| Fri 11-27 | Dylan | one iteration in Plane Studio, no terminal (U3.4 step 4) | time taken |

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
| W0-R | `reviewer` | Opus (fresh) | the four branches | `reviews/2026-11-21-w0.md` | ACCEPT per branch |
| W0-A | `auditor` | Haiku | session state, ledger, this table | report to conductor | ≤ 15 lines, evidence per finding |
| W0-X | `advisor` | Opus | a unit that failed review twice | recommendation | one dispatch recommended |

**Permissions for W0 (approve once at the start of the conductor session):** `git worktree add|remove` under `../wt/`; `git commit` on `std/*` branches; `git push` of `std/*` branches and of `main` after a reviewed merge (no force push); `git lfs track|install|push`; `pip install -e ".[mcp,dev]"` and `pip install pytest` into a virtual environment; `python -m pytest`; `plane …`; reading `../aircraft-platform` (at `f462468`). Nothing outside the repo, its worktrees and the read-only source checkout is written.

**LFS fallback (D8):** if `git push` of LFS objects is refused by the git host or proxy, the conductor removes the LFS patterns for meshes (they total about 5 MB) and commits them as plain git, and records "D8 amended: plain git" in §3. No builder handles this.

## 7. Units

Conventions for every unit: worktree + branch `std/<unit-id>`; `export PYTHONPATH=$PWD/core` in worktrees; finish with
`pytest -q` (all green), `plane design validate --all --json > /dev/null; echo $?` (0 or only known baseline failures), `plane ledger set <R-ids> done --evidence <PR url>`, commit, PR.

### Unit U0.4: Seed hangar from aircraft-platform (runs first)

**Files:**
- Import: aircraft-platform @ `f462468` (`core/`, `schema/`, `standards/`, `tests/`, `designs/`, `knowledge/`, `skills/`, `viewer/`, `docs/`, `.github/`, `pyproject.toml`) with `git archive`, no history rewrite
- Rename: package `core/aircraft_platform/` → `core/hangar/`; project name `dbf-hangar`; entry points `plane`, `plane-mcp` unchanged
- Create: `PROVENANCE.md` (source repo, commit, path → hangar path, edits made), `.gitattributes` (LFS patterns per D8), `README.md` (≤ 40 lines, pointers)
- Test: existing suite + `tests/test_seed.py`

- [x] **Step 1: Failing test**

```python
def test_package_is_hangar_and_cli_still_plane():
    import hangar; assert hangar.__version__.startswith("1.0.0.dev")
    assert shutil.which("plane")

def test_provenance_lists_every_imported_top_level_path(repo_root):
    prov = (repo_root/"PROVENANCE.md").read_text()
    for p in ["core/", "schema/", "standards/", "designs/", "knowledge/", "skills/", "viewer/"]:
        assert p in prov
```

- [x] **Step 2: Run** → FAIL (repo empty apart from plan and agents)
- [x] **Step 3: Import + rename** (`git -C ../aircraft-platform archive f462468 | tar -x`, then `sed` the imports; CI badge and Pages URL point at dbf-hangar)
- [x] **Step 4: Run** `pip install -e ".[mcp,dev]" && pytest -q` → same pass count as aircraft-platform at `f462468`; `plane baseline check --all` → no new failures
- [x] **Step 5: Commit** `git commit -m "seed: aircraft-platform f462468 as package hangar; provenance; LFS"`

### Unit U0.1: Agent roster and pointer files

**Files:**
- Create: `.claude/agents/{conductor,advisor,tactician,builder,builder-plus,scout,recon,design-engineer,reviewer,auditor}.md` (drafts already in this branch)
- Modify: `standards/agents.md` → v0.2 (reviewer fresh per wave; work-class bump table; points to `.claude/agents/`)
- Modify: `CLAUDE.md` → pointer list only (≤ 25 lines)
- Test: `tests/test_harness.py`

**Interfaces:**
- Produces: `harness.roster.load_roster(root: Path) -> dict[str, AgentSpec]`, `AgentSpec(name: str, model: Literal["opus","sonnet","haiku"], tools: list[str], description: str)` in `core/hangar/harness/roster.py`

- [x] **Step 1: Write the failing tests**

```python
def test_roster_has_exactly_the_ten_roles(repo_root):
    assert set(load_roster(repo_root)) == {"conductor","advisor","tactician","builder","builder-plus",
                                          "scout","recon","design-engineer","reviewer","auditor"}

def test_every_agent_has_model_stop_rule_and_never_section(repo_root):
    for spec in load_roster(repo_root).values():
        text = (repo_root/".claude/agents"/f"{spec.name}.md").read_text()
        assert spec.model in {"opus","sonnet","haiku"}
        assert "## Stop rules" in text and "## Never" in text

def test_design_engineer_cannot_edit_code(repo_root):
    assert "Edit" not in load_roster(repo_root)["design-engineer"].tools

def test_claude_md_is_a_pointer_file(repo_root):
    assert len((repo_root/"CLAUDE.md").read_text().splitlines()) <= 25
```

- [x] **Step 2: Run** `pytest tests/test_harness.py -v` → FAIL (`load_roster` missing)
- [x] **Step 3: Implement `load_roster`** (parse YAML frontmatter between the first two `---` lines; `tools` is the comma list). Update `standards/agents.md` and `CLAUDE.md`.
- [x] **Step 4: Run** `pytest tests/test_harness.py -v` → PASS
- [x] **Step 5: Commit** `git commit -m "harness: 10-role agent roster, agents.md v0.2, CLAUDE.md as pointer file"`

### Unit U0.2: Hooks, output style, installer (delivered early as H1 + H2, §6c; this unit then only ports the hooks onto `plane ledger` once U0.3 lands)

Delivered 2026-11-20: H1 + H2 merged after 3 review rounds (`reviews/2026-11-20-w0-harness.md`). Follow-ups this unit picks up (non-blocking from that review):
- [x] printed `ledger.py` instructions use `sys.executable`, not `python`
- [x] `reinject` also lists `deferred` prompts after compaction
- [x] installer removes older `python …/x.py` hook entries when upgrading to `run.sh`
- [x] installer writes `run.sh` with LF endings and a test fails if any `*.sh` contains `\r`

**Files:**
- Create: `harness/hooks/{log_prompt,agent_gate,reinject,stop_gate}.py`, `.claude/settings.json`, `.claude/output-styles/quiet.md`, `harness/install.py`
- Test: `tests/test_hooks.py`

**Interfaces:**
- Consumes: `load_roster` (U0.1); `Ledger` (U0.3) — U0.2 and U0.3 run in parallel; until U0.3 merges, hooks import `ledger` lazily and tests use the U0.3 fixture file format below.
- Produces: hook scripts read Claude Code hook JSON on stdin; exit 0 = allow, exit 2 = block with stderr message.

- [ ] **Step 1: Write the failing tests** (run each script with `subprocess.run([sys.executable, script], input=json.dumps(event))`)

```python
def test_agent_gate_blocks_unknown_role():
    r = run_hook("agent_gate", {"tool_name": "Task", "tool_input": {"subagent_type": "general-purpose", "prompt": "x"}})
    assert r.returncode == 2 and "builder" in r.stderr

def test_agent_gate_allows_roster_role_listed_in_active_plan(active_plan_with_builder):
    r = run_hook("agent_gate", {"tool_name": "Task", "tool_input": {"subagent_type": "builder", "prompt": "x"}})
    assert r.returncode == 0

def test_prompt_is_logged_open(tmp_ledger):
    run_hook("log_prompt", {"prompt": "add a BOM gate", "session_id": "s1"})
    assert tmp_ledger.prompts("s1")[-1].status == "open"

def test_stop_blocked_while_prompt_open_and_allowed_with_override(tmp_ledger, monkeypatch):
    tmp_ledger.add_prompt("s1", "x")
    assert run_hook("stop_gate", {"session_id": "s1"}).returncode == 2
    monkeypatch.setenv("ALLOW_STOP", "1")
    assert run_hook("stop_gate", {"session_id": "s1"}).returncode == 0

def test_reinject_prints_open_items_after_compaction(tmp_ledger):
    tmp_ledger.add_prompt("s1", "keep FEA envelope")
    assert "keep FEA envelope" in run_hook("reinject", {"source": "compact", "session_id": "s1"}).stdout

def test_install_is_idempotent(tmp_path):
    install(tmp_path); install(tmp_path)
    assert len(list((tmp_path/"agents").glob("*.md"))) == 10
```

- [ ] **Step 2: Run** `pytest tests/test_hooks.py -v` → FAIL
- [ ] **Step 3: Implement the four hooks, `install(target: Path) -> list[Path]`, settings.json wiring** (`PreToolUse` matcher `"Task|Agent"`; `SessionStart` matcher `"compact|resume"`). "Active plan" = newest `plans/*.md` whose agent table lists the role.
- [ ] **Step 4: Run** `pytest tests/test_hooks.py -v` → PASS; then one live check: start Claude Code in the repo, ask it to launch a `general-purpose` agent, confirm it is blocked with the roster message.
- [ ] **Step 5: Commit** `git commit -m "harness: prompt ledger, agent gate, stop gate, compaction re-inject, quiet style, installer"`

### Unit U0.3: Ledger (meeting → tasks → evidence) — builds on `harness/ledger.py` from H1: same `ledger/prompts.jsonl` format, `plane ledger` wraps it

**Files:**
- Create: `core/hangar/ledger.py`, `ledger/items.yaml`, `ledger/prompts.jsonl` (gitignored), `schema/ledger.schema.json`
- Test: `tests/test_ledger.py`

**Interfaces:**
- Produces: `Ledger(path: Path)` over `ledger/items.yaml`, `.add(kind: Literal["ruling","task","idea","decision"], text: str, source: str, owner: str = "", item_id: str | None = None, due: str = "") -> str` (returns `R12`/`T3`/`D4`/`I2`), `.set(item_id: str, status: Literal["open","done","dropped","superseded","decided"], evidence: str = "", decided_in: str = "") -> None`, `.get(item_id) -> Item`, `.check(repo: Path) -> list[Issue]`, `.report_overdue(today: str) -> list[str]`, `.report() -> str`, `.seed_from_plan(plan: Path) -> int`. Prompts stay in `harness/ledger.py` (stdlib, used by hooks); `report()` reads `ledger/prompts.jsonl` (same format) only to count open prompts. Brief: `briefs/U0.3-ledger.md` (its tests supersede the sketch below).

- [x] **Step 1: Write the failing tests**

```python
def test_dropped_needs_decision_and_is_not_overdue(tmp_ledger):
    t = tmp_ledger.add("task", "OpenCAE GUI port", source="2026-11-11#61:02")
    with pytest.raises(ValueError, match="decided_in"):
        tmp_ledger.set(t, "dropped")
    tmp_ledger.set(t, "dropped", decided_in="2026-11-18#26:16")
    assert t not in tmp_ledger.report_overdue()

def test_done_needs_evidence_that_exists(tmp_ledger, repo_root):
    t = tmp_ledger.add("task", "x", source="s")
    tmp_ledger.set(t, "done", evidence="designs/does-not-exist/plane.yaml")
    assert [i.kind for i in tmp_ledger.check(repo_root)] == ["missing-evidence"]

def test_seeded_with_requirements_R1_to_R40(repo_root):
    ids = {i.id for i in Ledger(repo_root/"ledger/items.yaml").items if i.kind == "ruling"}
    assert {f"R{n}" for n in range(1, 41)} <= ids
```

- [x] **Step 2: Run** → FAIL
- [ ] **Step 3: Implement**; seed `ledger/items.yaml` from §1 (scout transcribes the table; each R-id keeps its transcript timestamp as `source`). Add `ledger ingest` input format: a scout produces `ledger/inbox/<date>.yaml` from a transcript; `ingest` validates against `schema/ledger.schema.json` and appends. — *Status 2026-11-21: seed done (R1–R40, D1–D10); `ledger ingest` was not in the U0.3 brief and is still open.*
- [x] **Step 4: Run** → PASS
- [x] **Step 5: Commit** `git commit -m "ledger: tracked rulings/tasks/decisions with evidence; seeded R1-R40"`

### Unit U1.1: Operations registry and the OpResult contract [hard]

**Files:**
- Create: `core/hangar/ops/__init__.py` (registry), `ops/design.py`, `ops/meta.py`, `schema/op-result.schema.json`
- Modify: `core/hangar/cli.py` (generated groups; old commands become aliases)
- Test: `tests/test_ops_contract.py`

**Interfaces:**
- Produces:
  - `@op(name: str, summary: str, mutates: bool = False, adapters: tuple[str, ...] = ())` decorator; params from the function's type hints (str, int, float, bool, Path, Literal, list[str]).
  - `OpResult(ok: bool, data: dict, messages: list[str] = [], changed_files: list[str] = [], skipped: list[str] = [])`, `.to_json() -> str`, `schema_version = "1.0"`.
  - `registry() -> dict[str, OpSpec]`; `call(name: str, **params) -> OpResult`.
  - CLI: `plane <group> <verb>` from `name="<group>.<verb>"`; `--json` prints `OpResult`; exit 0/1/2 per Global Constraints.
  - Ops moved in this unit: `design.list, design.get, design.validate, design.mass, design.export, design.new, ops.list`.

- [ ] **Step 1: Write the failing tests**

```python
def test_every_op_result_matches_schema():
    for name in ["design.list", "ops.list"]:
        jsonschema.validate(json.loads(call(name).to_json()), OP_RESULT_SCHEMA)

def test_cli_exposes_every_registered_op(cli_runner):
    out = json.loads(cli_runner.invoke(cli, ["ops", "list", "--json"]).output)["data"]["ops"]
    assert {o["name"] for o in out} == set(registry())

def test_old_validate_alias_matches_new(cli_runner):
    a = cli_runner.invoke(cli, ["validate", "designs/example-tailsitter-wing", "--format", "json"])
    b = cli_runner.invoke(cli, ["design", "validate", "designs/example-tailsitter-wing", "--json"])
    assert json.loads(a.output)["accepted"] == json.loads(b.output)["data"]["accepted"]

def test_unknown_component_type_gives_skip_not_crash(tmp_design_with_type_wingletz):
    r = call("design.validate", path=str(tmp_design_with_type_wingletz))
    assert not r.ok and any("wingletz" in m for m in r.messages)
```

- [ ] **Step 2: Run** `pytest tests/test_ops_contract.py -v` → FAIL
- [ ] **Step 3: Implement the registry and click generation** (click `Group` per prefix, `Command` per op; `Literal` → `click.Choice`). `design.validate` wraps `checks.validate` unchanged.
- [ ] **Step 4: Run** full `pytest -q` → PASS (existing CLI tests must still pass through aliases)
- [ ] **Step 5: Commit** `git commit -m "ops: one registry and OpResult contract; CLI generated from it"`

### Unit U1.2: MCP and Studio generated from the registry (subtraction)

**Files:**
- Modify: `core/hangar/mcp_server.py` (replace hand-written tools with a loop over `registry()`), `core/hangar/studio.py` (one `POST /api/op/<name>` route; delete `/api/patch`, `/api/check`, `/api/new`, … after `viewer/studio.js` calls the new route)
- Test: `tests/test_surfaces_in_sync.py`

**Interfaces:**
- Consumes: `registry()`, `call()` (U1.1)
- Produces: MCP tool name = op name with `.` → `_` (`design_validate`); Studio `POST /api/op/design.validate {"path": ...}` → `OpResult` JSON.

- [ ] **Step 1: Failing tests**: `test_mcp_tools_equal_registry()` (tool names == `{n.replace('.', '_') for n in registry()}`); `test_studio_op_route_returns_op_result()`; `test_no_handwritten_api_routes_left()` (grep `studio.py` for `/api/` strings other than `/api/op/`, `/api/state`, `/api/ping`, file downloads).
- [ ] **Step 2: Run** → FAIL
- [ ] **Step 3: Implement**; net line count of `mcp_server.py` + `studio.py` must go down (record in PR).
- [ ] **Step 4: Run** `pytest -q` → PASS; manual: `plane studio`, edit a mass, scorecard refreshes.
- [ ] **Step 5: Commit** `git commit -m "mcp, studio: generated from ops registry; remove duplicate handlers"`

### Unit U1.3: PDL v1.0 schema, reference doc, migration [hard]

**Files:**
- Modify: `schema/plane.schema.json` (title "Plane Design Language v1.0"; add `"1.0"` to `schema_version`; blocks from §2.3; `requirements.transport_box_mm`)
- Create: `core/hangar/migrate.py`, `ops/schema.py` (`schema.docs`, `design.migrate`), `docs/pdl/reference.md` (generated), `docs/pdl/README.md` (one page: how a plane is described, with concept-a excerpts)
- Test: `tests/test_pdl.py`

**Interfaces:**
- Produces: `migrate(data: dict) -> tuple[dict, list[str]]` (new data, notes); ops `design.migrate(path, write: bool = False)`, `schema.docs(out: Path)`.

- [ ] **Step 1: Failing tests**

```python
@pytest.mark.parametrize("d", list_designs())
def test_every_committed_design_migrates_to_1_0_with_same_verdict(d):
    before = validate(load_design(d)).accepted
    data, _ = migrate(load_design(d).data)
    assert data["schema_version"] == "1.0"
    assert validate(Design(data, d)).accepted == before

def test_v1_blocks_validate(pdl_v1_example):   # tests/fixtures/pdl-v1-full.yaml uses every new block
    assert tier0_schema(load_design(pdl_v1_example)).status == "PASS"

def test_reference_doc_is_current(tmp_path):
    call("schema.docs", out=tmp_path/"ref.md")
    assert (tmp_path/"ref.md").read_text() == (REPO_ROOT/"docs/pdl/reference.md").read_text()
```

- [ ] **Step 2: Run** → FAIL
- [ ] **Step 3: Implement** schema additions, `migrate`, generator; migrate all committed designs (`plane design migrate designs/* --write`) in this PR — the only PR allowed to touch both `designs/**` and `core/**` (label `migration`, see U1.4).
- [ ] **Step 4: Run** `pytest -q` → PASS; `plane baseline check --all` → no new failures
- [ ] **Step 5: Commit** `git commit -m "pdl: v1.0 schema (files, bom, wiring, mechanisms, transport, assembly, provenance) + migrate + reference"`

### Unit U1.4: Edit, sweep, diff, propose — iterate without code (R4, R5, R8, R15, R25)

**Files:**
- Create: `ops/edit.py`, `harness/ci/check_separation.py`, `.github/workflows/validate.yml` (add separation step + Windows job)
- Test: `tests/test_design_edit.py`, `tests/test_paths.py`, `tests/test_separation.py`

**Interfaces:**
- Consumes: `yamlio.load/dump`, `migrate`, `call`
- Produces:
  - `design.set(path: str, key: str, value: str, why: str, kind: Literal["add","subtract","modify"] = "modify") -> OpResult` — `key` is dotted with list selectors by id: `components[wing_l].mass_g`; `value` parsed as YAML scalar; schema-checked before write; appends to `CHANGELOG.yaml`.
  - `design.get(path, key)`, `design.diff(a, b) -> data.changes: list[{key, a, b}]`, `design.copy(src, new_id)`.
  - `design.sweep(path, key, values: list[str]) -> data.rows: list[{value, accepted, mass_g, static_margin, stall_speed_mps, hover_tw, failures}]` (copies to `.sweeps/<id>/<n>/`, never touches the source).
  - `design.propose(path, title) -> data.pr_url` (branch `design/<id>/<slug>`, commit, push, open PR via `gh api`).
  - `check_separation(base: str) -> list[str]` (violations).

- [ ] **Step 1: Failing tests**

```python
def test_set_changes_one_value_keeps_comments_and_logs(tmp_concept_a):
    call("design.set", path=tmp_concept_a, key="components[wng-004-l].mass_g", value="41.5", why="measured", kind="modify")
    assert "# " in (tmp_concept_a/"plane.yaml").read_text()           # comments kept
    assert yaml.safe_load((tmp_concept_a/"CHANGELOG.yaml").read_text())[-1]["kind"] == "modify"

def test_set_rejects_bad_path_and_type_without_writing(tmp_concept_a):
    before = (tmp_concept_a/"plane.yaml").read_bytes()
    assert call("design.set", path=tmp_concept_a, key="components[nope].mass_g", value="1", why="x").ok is False
    assert call("design.set", path=tmp_concept_a, key="components[wng-004-l].mass_g", value="heavy", why="x").ok is False
    assert (tmp_concept_a/"plane.yaml").read_bytes() == before

def test_sweep_never_touches_source(tmp_example):
    before = (tmp_example/"plane.yaml").read_bytes()
    rows = call("design.sweep", path=tmp_example, key="components[battery].position_mm[0]", values=["100","140"]).data["rows"]
    assert len(rows) == 2 and (tmp_example/"plane.yaml").read_bytes() == before

def test_backslash_and_crlf_roundtrip(tmp_example):
    crlf = tmp_example/"plane.yaml"; crlf.write_bytes(crlf.read_bytes().replace(b"\n", b"\r\n"))
    assert call("design.validate", path=str(tmp_example).replace("/", "\\")).data["design_id"]

def test_separation_flags_design_pr_touching_core():
    assert check_separation_files(["designs/x/plane.yaml", "core/hangar/checks.py"], labels=[]) != []
    assert check_separation_files(["designs/x/plane.yaml", "core/hangar/checks.py"], labels=["migration"]) == []
```

- [ ] **Step 2: Run** → FAIL
- [ ] **Step 3: Implement** (path backslashes normalised in the one `_resolve_design_path` helper all ops use).
- [ ] **Step 4: Run** `pytest -q` → PASS; CI green on Linux and Windows
- [ ] **Step 5: Commit** `git commit -m "ops: design set/get/diff/copy/sweep/propose; CI keeps designs and code apart"`

### Unit U1.5: Claims graph in PDL + T9 Claims gate [hard] (from DBF-Combined `proofs/1`)

**Files:**
- Create: `schema/claims.schema.json` (adapted from DBF-Combined `redesign/proofs/SCHEMA.md`: node types requirement, claim, calculation, parameter, source, assumption, test), `core/hangar/claims/{graph,calc}.py`, `ops/claims.py`, `gates/claims.py`
- Per design: `designs/<id>/claims.yaml` (optional); `calculation.script` must be a function in `core/hangar/calcs/` or the design's own `calcs.py` registered by name, never a path into another repo
- Test: `tests/test_claims.py`, fixture `tests/fixtures/claims-mini/` (3 requirements, 4 claims, 2 calcs, 1 failing margin)

**Interfaces:**
- Produces: `load_claims(design: Design) -> ClaimGraph`; `ClaimGraph.recompute() -> list[ClaimResult(id, value, limit, margin, margin_abs: bool, status: Literal["PASS","FAIL","PROPOSED","STALE"])]`; ops `claim.list(path)`, `claim.explain(path, claim_id)` (chain down to sources), `claim.check(path)`; gate `T9.claim.<id>`; `parameter` nodes read PDL values (`P:components[wng-004-l].mass_g`) so `design.set` changes flow into claims.

- [ ] **Step 1: Failing tests**

```python
def test_margin_rules_match_proofs_1(mini):          # >= and <= margins, limit 0 → margin_abs
    r = {c.id: c for c in load_claims(mini).recompute()}
    assert r["CL-AERO-TW"].margin == pytest.approx((1.72 - 1.6) / 1.6)
    assert r["CL-STR-CLEAR"].margin_abs is True

def test_failing_margin_fails_t9(mini):              assert status(mini, "T9.claim.CL-MASS-GATE") == "FAIL"
def test_claim_without_calc_is_proposed_not_pass(mini): assert status(mini, "T9.claim.CL-PROP-NOISE") == "SKIP"
def test_design_set_flows_into_claim(tmp_mini):
    call("design.set", path=tmp_mini, key="components[battery].mass_g", value="400", why="t", kind="modify")
    assert status(tmp_mini, "T9.claim.CL-MASS-GATE") == "FAIL"
def test_concept_a_claims_import_roundtrip(dbf_combined_claims):   # 4 claims.*.json files from qp/A/proofs
    g = import_proofs1(dbf_combined_claims); assert len(g.nodes) == count_nodes(dbf_combined_claims)
```

- [ ] **Step 2: Run** → FAIL
- [ ] **Step 3: Implement** (port the margin rules from DBF-Combined `redesign/proofs/build_graph.py`; record the port in `PROVENANCE.md`); `import_proofs1(paths) -> ClaimGraph` used by U2.5.
- [ ] **Step 4: Run** → PASS
- [ ] **Step 5: Commit** `git commit -m "claims: proofs/1 graph as PDL claims.yaml, recompute, T9 gate, claim ops"`

### Unit U1.6: Interface graph and connection-type library (from DBF-Combined `dbf-interfaces/1`)

**Files:**
- Create: `standards/connection-types.yaml` (from `redesign/interfaces/connection_types.json`, each type with `rating_basis` and `source`), `gates/interfaces.py`
- Modify: `schema/plane.schema.json` (`attachments[].connection: <connection-type id>`, optional `seat`), `core/hangar/importers/dbf.py` (reads `interfaces.json` edges)
- Test: `tests/test_interfaces.py`

**Interfaces:**
- Produces: `T1.interfaces.floating` (every component reachable from root through attachments — already T1 connectivity; this adds that each attachment's `connection` exists in the library), `T1.interfaces.connection_known`, op `standards.connections`.

- [ ] **Step 1: Failing tests**: `test_unknown_connection_type_fails`, `test_every_library_type_has_source_or_pending`, `test_dbf_interfaces_import_keeps_edge_count` (concept A `interfaces.json` edges == PDL attachments + `edges_pending`).
- [ ] **Step 2–4:** implement; run → PASS
- [ ] **Step 5: Commit** `git commit -m "interfaces: shared connection-type library; attachments name their connection"`

### Unit U2.1: Gate registry + T6 Mechanisms, T7 Integration, T8 Sourcing [hard]

**Files:**
- Create: `standards/gates.yaml`, `core/hangar/gates/{__init__,mechanisms,integration,sourcing}.py`
- Modify: `core/hangar/checks.py` (tiers 0–5 registered through `gates/`, behaviour unchanged), `standards/design-standards.yaml` (new keys: `mechanism_ratio_tol` (internal convention), `wire_clearance_mm` (pending, D5), `transport_box_mm` default (pending, D5), `bom_verified_max_age_days: 30` (internal convention)), `designs/example-tailsitter-wing/plane.yaml` gets a mechanism and wiring so the gates have a positive example
- Test: `tests/test_gates.py`, fixtures `tests/fixtures/mech-{good,jammed,unlinked}.yaml`

**Interfaces:**
- Produces: `@gate(id: str, tier: int)` registration; `run_gates(design, max_tier: int = 8) -> Scorecard` (Scorecard gains `fidelity: dict`); ops `gate.list`, `gate.explain(check_id)`, `sim.mechanism(path, mechanism_id)` (returns per-step follower angles for the Physics mode).

- [ ] **Step 1: Failing tests**

```python
def test_linked_flap_follows_servo(mech_good):     assert status(mech_good, "T6.mechanism.flap_l") == "PASS"
def test_jammed_linkage_fails_with_step(mech_jammed):
    r = result(mech_jammed, "T6.mechanism.flap_l"); assert r.status == "FAIL" and "deg" in r.message
def test_undriven_joint_warns(mech_unlinked):       assert status(mech_unlinked, "T6.undriven.tilt") == "WARN"
def test_exposed_wire_fails_unless_reasoned(wire_outside, wire_outside_ok):
    assert status(wire_outside, "T7.wiring.esc_to_motor_l") == "FAIL"
    assert status(wire_outside_ok, "T7.wiring.esc_to_motor_l") == "PASS"
def test_transport_group_too_big_fails(wing_too_long):  assert status(wing_too_long, "T7.transport.wing") == "FAIL"
def test_stale_bom_line_fails(bom_stale):          assert status(bom_stale, "T8.bom.verified.motor") == "FAIL"
def test_tiers_0_5_unchanged_for_committed_designs(baselines):  # every baseline.json still matches
    for d, base in baselines: assert known_failures(run_gates(d, 5)) == base
def test_scorecard_reports_fidelity(concept_a):
    f = run_gates(concept_a).fidelity; assert {"sourced_blocking", "blocking", "measured_mass_parts"} <= f.keys()
```

- [ ] **Step 2: Run** → FAIL
- [ ] **Step 3: Implement.** T6 builds on `sim.py`'s MJCF export: position actuator on the driver joint, equality constraints from `kinematic_link`, gravity 0, friction 0; read follower qpos each 1° step; contacts filtered to unattached pairs. D7 default: T7/T8 non-blocking (WARN) via `blocking: false` in `gates.yaml`.
- [ ] **Step 4: Run** `pytest -q` → PASS; `plane design validate designs/concept-a --json` shows T6–T8 and the fidelity line
- [ ] **Step 5: Commit** `git commit -m "gates: registry; T6 mechanisms (MuJoCo), T7 wiring/transport/assembly, T8 BOM; fidelity line"`

### Unit U2.2: Standards database — close the pending sources (R10, R13)

**Files:**
- Create: `ops/standards.py` (`standards.list`, `standards.show`, `standards.pending`), `knowledge/sources/std-*.md` (new, one per source opened)
- Modify: `standards/design-standards.yaml` (sources), `knowledge/sources/std-SUMMARY.md`
- Test: `tests/test_standards.py`

**Interfaces:**
- Produces: `standards.pending -> data.items: list[{key, value, blocking: bool, candidates: list[source ids]}]`

- [ ] **Step 1: Failing test**: `test_no_blocking_threshold_is_pending_without_a_decision()` — every `pending` key used by a blocking gate has a ledger decision (D5/D6) referencing it.
- [ ] **Step 2: Run** → FAIL (2 keys)
- [ ] **Step 3a: Knowledge import:** scouts turn DBF-Combined `redesign/config-study/` (43 concept cards, judging) and `docs/research/` into `knowledge/` entries via the templates, each linked to its morph-chart cell; `PROVENANCE.md` lists each source file.
- [ ] **Step 3: Scouts** (Haiku, template `knowledge/TEMPLATE-source.md`, only sources actually opened): STANAG 4703 Annex B landing loads, ASTM F3298 load tables, the paper behind the 1.2–1.5 T/W forum claim, NASA-STD-5001 factors for printed parts, DBF rules for box size; `recon` ranks them and proposes values; conductor writes D6 with the options.
- [ ] **Step 4: Run** → PASS
- [ ] **Step 5: Commit** `git commit -m "standards: sources for landing factor, hover T/W, transport; pending list op"`

### Unit U2.3: Tool adapters — OpenCAE, MuJoCo, AeroSandbox, DaVinci [hard]

**Files:**
- Create: `core/hangar/adapters/{__init__,opencae,mujoco,aerosandbox,blender,sitl,davinci}.py` (`blender` ports DBF-Combined `redesign/collision/collide.py` as an optional higher-fidelity collision/transport check; `sitl` wraps `redesign/qp/A/sitl/a_plant.py`, report-only), `ops/tools.py` (`tools.doctor`), `ops/fea.py` (`fea.plan`, `fea.run`)
- Modify: `opencae_runner.py` → used only by `adapters/opencae.py`; `plane fea` becomes an alias
- Test: `tests/test_adapters.py`

**Interfaces:**
- Produces: `class Adapter(Protocol): name: str; def available(self) -> tuple[bool, str]` (reason + fix command); `def run(self, design: Design, **params) -> OpResult`. `get_adapter(name) -> Adapter`. OpenCAE adapter prefers Vibhav's `opencae` CLI if on PATH (contract agreed with him in this unit: `opencae solve --deck <inp> --json`), else the current in-repo runner.

- [ ] **Step 1: Failing tests**

```python
def test_missing_tool_is_skip_with_fix(monkeypatch, concept_a):
    monkeypatch.setattr(OpenCAE, "available", lambda self: (False, "run: plane fea --setup …"))
    r = call("fea.run", path=concept_a, part="wng-004-l")
    assert r.skipped and "plane fea --setup" in r.messages[0]
    assert run_gates(load_design(concept_a)).accepted is False

def test_doctor_lists_every_adapter():
    assert {a["name"] for a in call("tools.doctor").data["adapters"]} == {"opencae","mujoco","aerosandbox","blender","sitl","davinci"}

def test_fea_results_identical_through_adapter(cantilever_fixture):   # same 1.003 mm as test_fea.py
    assert abs(call("fea.run", **cantilever_fixture).data["tip_disp_mm"] - 1.003) < 0.01
```

- [ ] **Step 2: Run** → FAIL
- [ ] **Step 3: Implement.** DaVinci: `available()` returns False with "D3 open: no API access configured" until D3 is answered; then `davinci.push` sends PDL + STEP files, `davinci.pull` brings a DaVinci build back as a `design.propose` PR.
- [ ] **Step 4: Run** `pytest -q` → PASS; Vibhav runs `plane fea run designs/concept-a --all` on his machine and pastes the summary in the PR (R9 first half)
- [ ] **Step 5: Commit** `git commit -m "adapters: one contract for OpenCAE, MuJoCo, AeroSandbox, DaVinci; tools doctor"`

### Unit U2.4: Team-ops commands (R7, R14, R26, R27, R31, R38)

**Files:**
- Create: `ops/{idea,research,morph,bom,assembly,ledger_ops,update}.py`, `knowledge/ideas/`, `updates/<YYYY-MM-DD>/` (per-week YAML), `viewer/updates/` (generated)
- Test: `tests/test_team_tasks.py` (the 12-task acceptance list from §2.1)

**Interfaces:**
- Produces: `idea.add(title, body, by) -> data.path`; `research.new(kind: Literal["source","diy"], slug) -> data.path`; `research.check(path) -> data.missing_fields`; `morph.add_option(dimension, id, name, source)`, `morph.coverage() -> data.cells: list[{dimension, option, designs}]`; `bom.verify(path, item, method, evidence, by)` (records a verification an agent did in Chrome — the CLI never scrapes); `bom.cost(path)`; `assembly.animate(path, out) -> glb with one animation track per sequence step`; `ledger.add/set/check/report/ingest`; `update.new(week)`, `update.add(week, person, link, changed)`, `update.publish(week) -> data.url` (static page + one line per person; posts the URL to the Drive doc through the connector when run by an agent with Drive access, else prints it).

- [ ] **Step 1: Failing test** — one test per team task, each calling only ops:

```python
TEAM_TASKS = ["send_design", "change_parameter", "compare_designs", "run_stress", "run_physics",
              "update_morph_chart", "send_idea", "research_entry", "verify_bom", "test_assembly",
              "weekly_update", "meeting_tasks_check"]
@pytest.mark.parametrize("task", TEAM_TASKS)
def test_team_task_needs_no_code_edit(task, git_clean_repo):
    run_task_script(task)                      # tests/team_tasks/<task>.sh: only `plane …` lines
    assert changed_files(git_clean_repo).isdisjoint(set(glob("core/**")))
```

- [ ] **Step 2: Run** → FAIL
- [ ] **Step 3: Implement** the ops and the 12 scripts.
- [ ] **Step 4: Run** → PASS
- [ ] **Step 5: Commit** `git commit -m "ops: idea, research, morph, bom, assembly, ledger, update — every team task via CLI"`

### Unit U2.5: Import concept A, decisions and program constraints from DBF-Combined [hard]

**Files:**
- Modify: `core/hangar/importers/dbf.py` → `plane design import dbf --dbf-root <path> --concept A` writes PDL 1.0 with `params` (from `params-A.json`), `bom` (from `BOM-A.csv`: `unit_usd → unit_cost_usd`, `source_url → url`, `date_checked` + `status: verified → verified{method: browser}`), `requirements` (from `REQUIREMENTS-A.md` / `MISSION.md`), `claims.yaml` (via `import_proofs1`, U1.5), interfaces (U1.6), meshes (LFS), `files` manifest pointing to DBF-Combined CAD scripts by commit
- Create: `standards/program.yaml` (DBF-Combined `CLAUDE.md` hard constraints, each with `source: team constraint, <date>`), `core/hangar/importers/changelog.py` (CHANGE-LOG D-ids + `DECISIONS.md` → ledger `decision` items)
- Modify: `designs/concept-a/` (re-imported), `designs/c0-*`, `designs/tiltwing-cakir` → `status: retired` (D9)
- Test: `tests/test_import_dbf_v2.py`

- [ ] **Step 1: Failing tests**

```python
def test_concept_a_bom_total_matches_source(imported_a):
    assert call("bom.cost", path=imported_a).data["total_usd"] == pytest.approx(bom_csv_total(DBF/"redesign/qp/A/BOM-A.csv"), abs=0.01)
def test_every_bom_line_keeps_its_url_and_check_date(imported_a):
    assert all(i["url"] and i["verified"]["date"] for i in load_design(imported_a).data["bom"]["items"] if i.get("verified"))
def test_program_constraints_apply_to_every_active_design(repo_root):
    for d in active_designs(): assert "T8.program.budget" in check_ids(d)
def test_changelog_decisions_in_ledger(ledger):     assert ledger.get("D-182").kind == "decision"
def test_reimport_is_stable(dbf_root, tmp_path):     # running the importer twice gives byte-identical output
    a = import_dbf(dbf_root, "A", tmp_path/"a"); b = import_dbf(dbf_root, "A", tmp_path/"b"); assert same_tree(a, b)
```

- [ ] **Step 2: Run** → FAIL
- [ ] **Step 3: Implement**; the importer is the only code that knows DBF-Combined's layout.
- [ ] **Step 4: Run** → PASS; `plane design validate designs/concept-a` scorecard committed as the new baseline; Dylan checks the BOM and claims against the Explorer (acceptance, 15 min)
- [ ] **Step 5: Commit** (label `migration`) `git commit -m "import: concept A full (params, BOM, requirements, claims, interfaces); program constraints; decision log"`

### Unit U3.1: One surface — Studio with modes, same app on Pages [hard]

**Files:**
- Modify: `viewer/index.html`, merge `viewer/app.js` + `viewer/studio.js` → `viewer/app.js` with `modes/{designs,compare,physics,stress,build,bom,proofs,morph,knowledge,ledger,updates}.js` (Build, BOM and Proofs adapt the DBF-Combined Explorer's build guide, BOM tab, vendor links and proof viewer); `core/hangar/index.py` (`build-index` also writes mechanism sweeps, ledger, updates); `.github/workflows/pages.yml`
- Delete: duplicate render/scorecard code in `studio.js`; the separate OpenCAE dashboard link (its content is the Stress mode)
- Test: `tests/test_studio.py` (extend), `tests/test_viewer_static.py` (Playwright smoke: every mode loads with no console errors, read-only build hides edit controls)

**Interfaces:**
- Consumes: `/api/op/<name>` (U1.2), `build-index` JSON
- Produces: `viewer/data/index.json` v2: `{designs, scorecards, mechanisms, ledger, updates, generated_at}`

- [ ] **Step 1: Failing tests** (`test_every_mode_renders_without_console_errors[mode]`, `test_pages_build_has_no_edit_controls`, `test_physics_mode_plays_mechanism_sweep`)
- [ ] **Step 2: Run** → FAIL
- [ ] **Step 3: Implement**; budget: total JS lines after ≤ lines before + 30 %.
- [ ] **Step 4: Run** → PASS; the Pages URL shows this week's update (R28)
- [ ] **Step 5: Commit** `git commit -m "studio: one app with modes; Pages build is the same app read-only"`

### Unit U3.2: Skills on the ops layer (R3, R15, R16, R21, R22, R30)

**Files:**
- Rewrite: `skills/{design-concept,review-design,research,make-skill}/SKILL.md` to call ops only
- Create: `skills/design-iterate/SKILL.md`, `skills/recon/SKILL.md`, `skills/plan-scheme/SKILL.md`, `skills/get-it-together/SKILL.md`, `skills/weekly-update/SKILL.md`
- Test: `tests/test_skills.py`

Content rules (from the advisor): `design-iterate` — before any fix list ≥ 1 subtract, 1 modify and 1 adjust option, choose add only with a written reason, record `kind`, and run `recon` when the same check failed twice. `plan-scheme` — max effort, waves by dependency, units = PRs, surface decisions + one permissions prompt, then drop to medium. `get-it-together` — compares `ledger/prompts.jsonl`, the active plan and the roster rules with the session's actual state; output ≤ 15 lines. `make-skill` — research → recon of existing skills → synthesize → de-bloat pass (≤ 120 lines).

- [ ] **Step 1: Failing tests**: `test_every_skill_has_six_sections`, `test_skill_commands_exist` (every `plane x y` in a skill is in `registry()`), `test_no_numbers_in_skills` (no thresholds; links to `standards/…#key` instead), `test_skill_under_120_lines`.
- [ ] **Step 2–4:** write skills; run → PASS; dry-run `design-iterate` once on `example-tailsitter-wing` and commit the transcript to `reviews/`.
- [ ] **Step 5: Commit** `git commit -m "skills: rebuilt on ops; design-iterate, recon, plan-scheme, get-it-together, weekly-update"`

### Unit U3.3: PlaneBench v0 (R32)

**Files:**
- Create: `bench/tasks/{mass-cut-10,fix-static-margin,add-working-flap}.yaml`, `ops/bench.py`, `bench/results/`
- Test: `tests/test_bench.py`

**Interfaces:**
- Produces: task YAML `{id, prompt, start_design, allowed: ["plane *"], grader: [{op, path, expect}]}`; `bench.run(task, agent: str, model: str) -> data.{passed, score, tokens, minutes}` (runs the agent headless with `claude -p` and the `design-engineer` role; grader uses ops only); `bench.report -> markdown table`.

- [ ] **Step 1: Failing tests**: `test_grader_passes_on_known_good_solution` (hand-made solution design per task), `test_grader_fails_if_core_changed`.
- [ ] **Step 2–4:** implement; run → PASS; run each task once with Haiku, Sonnet, Opus as `design-engineer` (9 runs) and commit `bench/results/2026-11-28.md` — this is a slide for Dec 1.
- [ ] **Step 5: Commit** `git commit -m "bench: PlaneBench v0, 3 graded design tasks, first model comparison"`

### Unit U3.4: Proof — an agent iterates concept-a with no code edits (R9, R7 acceptance)

Not a code unit; it tests everything above.

- [ ] **Step 1:** Conductor launches `design-engineer` (Sonnet) on concept-a with the goal: "reduce failing checks without adding mass; mechanisms first." Hooks active; `design-engineer` has Bash limited to `plane *` and no Edit on `core/`.
- [ ] **Step 2:** It runs `plane design validate`, `plane sim mechanism`, `plane fea run`, `plane design set|sweep`, and opens one or more `plane design propose` PRs. `auditor` runs hourly.
- [ ] **Step 3:** Verify mechanically: `git diff --name-only main...design/concept-a/* | grep -c '^core/'` → `0`; scorecard failures fewer than `baseline.json`.
- [ ] **Step 4:** Acceptance: Dylan repeats one iteration himself in Plane Studio (no terminal), Vibhav repeats one with `plane fea` on Windows. Each records time taken in the ledger.
- [ ] **Step 5:** Tristan merges or closes the PRs after Dylan's approval (R25). `plane ledger set R7 R9 done --evidence <PR urls>`.

### Unit U4.1: Whole-branch review, performance, release

- [ ] **Step 1:** Fresh `reviewer` (Opus) reviews `main` since `f462468` against §1–§2 and `standards/review-scorecard.md`; blocking items reopen their unit (not a new unit).
- [ ] **Step 2:** Performance (R33): measure `plane design validate designs/concept-a` (tiers 0–8, no FEA); if > 60 s, one `builder-plus` unit to cut it, measured before/after.
- [ ] **Step 3:** Subtraction pass: `auditor` lists files, commands, docs and ledger items not used by any test, skill or op; conductor deletes or archives; stale ledger items closed with `superseded` (R23).
- [ ] **Step 4:** Docs: `README.md` ≤ 80 lines pointing to `docs/pdl/`, `docs/cli.md` (generated from `ops list`), `standards/agents.md`. Tag `v1.0.0`; Pages deploys.
- [ ] **Step 5:** verification-before-completion: paste `pytest -q`, `plane design validate --all`, `plane ledger report`, `plane tools doctor` outputs into `reviews/2026-11-30-v1.0.md`.

### Unit U4.2: Dec 1 presentation package

- [ ] **Step 1:** Slides deck (Claude Slides artifact; download .pptx/PDF if needed): problem (15 interfaces, rules forgotten, code edits per design) → PDL → ops/CLI/MCP/Studio → gates T0–T8 → harness → PlaneBench results → what's next.
- [ ] **Step 2:** Live demo script (8 min), each step one command or click: `plane design new` from a template → `plane design set` a wing mass → `plane design validate` → Studio Physics mode playing the flap mechanism → `plane design propose` → the PR → `plane update publish` → the one link. Recorded backup video.
- [ ] **Step 3:** Metrics slide filled from §2.1 with measured values (not targets).
- [ ] **Step 4:** Dry run Mon 11-30 evening; fix only what the dry run breaks.

## 8. Not doing for v1.0 (YAGNI; ledger status `dropped` with this file as `decided_in`)

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
