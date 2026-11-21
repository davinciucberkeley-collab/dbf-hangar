# Ledger audit LA-R: 22 R-ids whose units are all merged

Plan step LA-R (`plans/2026-11-20-standardization.md` §6h). Reviewer: fresh `reviewer` (Opus), read-only. Audited at `main` d00f9f3 (code); `main` moved to 55ab9d4 during the audit, a plan-only commit. R29 is excluded (deferred under D3).

## Method

- **Source of truth.** The meeting transcripts (11-11 and 11-18 check-ins, Tristan 11-20) are not in the repo. The §1 column "Requirement (paraphrased from the transcript)" is the only transcript record here, so each R-id is judged against that wording and its "Who / when" source.
- **What was checked.** For each R-id: the merge commits of its §1 units (all verified in `git log --merges`), the code and tests they added, the unit's verdicts in `reviews/2026-11-2*-w*.md`, the §1 parenthetical hints, and live probes through `PYTHONPATH=core python -m hangar.cli ...` (`ops list` = 46 ops).
- **Rule.** DONE = the requirement as worded is met by merged work on committed data, not only on test fixtures. If the wording reaches beyond what the units built, the R-id stays OPEN, even when the unit itself was ACCEPTed against its brief.
- **Recurring cause of OPEN.** `designs/concept-a` (the team's real plane) is still PDL 0.4 and has no `files`, `bom`, `mechanisms`, `wiring`, `transport` or `assembly` block. The U2.5 brief defers `params`, `bom`, `requirements`, `files` and schema 1.0 to "U2.5d", which is not yet a unit (briefs/U2.5-import-concept-a.md:40). No committed design has `mechanisms`, `wiring`, `transport` or `assembly` either, so T6 PASS, T7, `assembly.animate` and `bom.verify` have only been shown on test fixtures.

## Automated checks (reviewer run, Windows, main checkout)

| Check | Result |
|---|---|
| `pytest -q` (full, serial) | PYTEST_RESULT |
| `plane design validate --all` | no `--all` option on `design validate` (exit 2, "No such option"). Per design: example-tailsitter-wing accepted; concept-a and the 5 retired designs not accepted (as their baselines record) |
| `plane baseline check --all` (stands in for validate --all, as in the W2 reviews) | exit 0; 0 regressions on all 7 designs (concept-a 108 known, unchanged) |
| `plane ledger check` | `ledger check: no problems`, exit 0 |
| `plane design diff` | not applicable (no design PR) |
| Probes | `design sweep designs/example-tailsitter-wing components[battery].mass_g --values 150 --values 300`: 2 rows (mass 659 g / 809 g, static margin 0.121 / 0.148), plane.yaml sha1 unchanged (6a0e3742...). `assembly animate` on concept-a and on example: `ok false`, "design has no assembly.sequence". `design validate designs/concept-a`: tiers run 0-6, 8, 9 (no T7); T6 = 2 `T6.undriven.*` WARN; fidelity `measured_mass_parts 0`. `tools doctor`: blender and sitl `planned`, opencae and aerosandbox missing, davinci missing (D3). `standards pending`: `landing_load_factor` blocking, still pending |

## Verdicts

| R | verdict | evidence or missing |
|---|---|---|
| R1 | OPEN | The PDL 1.0 format with `files` and `bom` exists (dfcbf16; schema/plane.schema.json properties `files`, `bom`). But the team's plane, concept-a, is still 0.4 with no `files` or `bom`, so it has not "dropped into the same bucket". Needed: concept-a in PDL 1.0 with files and BOM, which is U2.5d (not yet a unit) |
| R2 | DONE | d6c1573 (U1.1), 73b0986 (U1.2). CLI generated from the registry; MCP tools generated at core/hangar/mcp_server.py:68 (`for _spec in registry().values()`); tests/test_surfaces_in_sync.py:77; `design.new` replaces per-plane HTML edits |
| R4 | DONE | d6c1573, b483b22, f99054d + 65ee21f. Simulations and analyses are ops (`fea.run`, `fea.plan`, `sim.mechanism`, `sim.drop` via ac5f76b) on data; tests/test_team_tasks.py:67 runs run_stress, run_physics and change_parameter with only `plane` lines |
| R5 | DONE | b483b22: CI separation step .github/workflows/validate.yml:44, tests/test_separation.py:9. c82b07b: an unknown component type gives a SKIP, not a crash (tests/test_ops_contract.py:53) |
| R8 | DONE | b483b22. Probe: `design sweep` gives a row per value (mass, static margin, accepted) and leaves the source byte-identical; `design.set` logs kind/why (tests/test_design_edit.py:39, :114) |
| R10 | OPEN | Not a "full 3D physics sim where parts can't pass through each other": T6 is analytic (D15, c82b07b), the Blender collision adapter is `planned` (tools doctor), and the blocking `landing_load_factor` is still pending (D6). Needed: a physics-sim mechanism check (U3.1 Physics mode / R11) and the blender adapter, which has no unit; landing factor source, D6 |
| R12 | OPEN | T7 wiring/transport gates exist (c82b07b) but are report-only (D7, until 12-08), `wire_clearance_mm` is pending (D5), and T7 never runs on a committed design (concept-a tiers 0-6, 8, 9; no design has `wiring` or `transport`). Needed: concept-a wiring/transport data (U2.5d) and the D7 flip |
| R13 | DONE | b4663d5 (U2.2): `standards list/show/pending` ops; every gate reads `standards/*.yaml` (gate list criteria); standards/manufacturing.yaml; knowledge/concepts/tailsitter-evidence.md; 9 scout source files. Residual: the blocking `landing_load_factor` is still pending under D6, and the config-study import (U2.2 step 3a) is deferred to an unscheduled U2.2-2 |
| R14 | OPEN | `bom.verify` and T8 staleness exist (9d1ce6a, c82b07b; tests/test_team_ops_b.py:135), but no committed design has a BOM: concept-a's BOM-A.csv is not imported, so no real part can be verified. Needed: concept-a BOM import, U2.5d |
| R17 | OPEN | The ordering was kept (T6 blocking, T8 report-only per D7; c82b07b), but no design has working, non-placeholder mechanisms: concept-a has no `mechanisms` block and gets 2 `T6.undriven.*` WARN. Needed: concept-a mechanisms data and iteration, U2.5d plus U3.4 |
| R18 | DONE | 7e18070 (U0.1): 10 work-level roles; opus = conductor/advisor/reviewer, sonnet = tactician/builder-plus/recon/design-engineer, haiku = builder/scout/auditor (.claude/agents/*.md `model:`); tests/test_roster.py:11; fresh reviewer per wave at standards/agents.md:21 |
| R19 | DONE | 9db8a0e + 5d31dad (H1/H2), 015fac7 (U0.2), 7e18070 (U0.1). The PreToolUse `Task|Agent` hook blocks roles off the roster and briefs without a pass check or stop rule (.claude/settings.json; tests/harness/test_agent_gate_install.py:27, :72); quiet output style; live check passed (plan U0.2 step 4) |
| R20 | DONE | 9db8a0e, 015fac7, dc255c9. `log_prompt` logs every prompt, `stop_gate` blocks while prompts are open, `reinject` reloads open prompts and units after compaction (tests/harness/test_ledger_hooks.py:17, :26, :44). Forced stop after 3 blocks is logged as `stop-forced` (:37), per the H1 review |
| R24 | DONE | 5d31dad, 015fac7: harness/install.py installs agents, style, hooks and harness into a target project; tests/harness/test_agent_gate_install.py:61 (idempotent, merges settings) |
| R25 | OPEN | `design.propose` exists (b483b22), but it has only run with git/gh mocked (W1 review U1.4: "nothing reaches GitHub"). No `design/*` branch or PR exists, and no teammate has opened competing PRs for Dillon to pick from. Needed: a live propose round with Dillon's pick, U3.4 step 5 |
| R27 | DONE | dc255c9 (U0.3) + dac0ed8 (U2.4a): `ledger ingest/check/report`; `dropped` needs `decided_in` and is never overdue (tests/test_ledger.py:18); an invalid inbox writes nothing (tests/test_team_ops.py:73); ledger holds 40 rulings, 23 tasks, 225 decisions |
| R31 | OPEN | `assembly.animate` exists (7fb3e9d) but no committed design has `assembly.sequence` (probe on concept-a and example: "design has no assembly.sequence"), and with no sequence nothing flags the plane as broken. Needed: concept-a's build steps as an assembly sequence; no unit owns this (the §1b `a_build_steps.py` row goes to the `planned` blender adapter, U2.3), so it needs a ledger task |
| R35 | DONE | 7e18070 (standards/agents.md:1 "Agent Standard v0.2", names every role and hook; tests/test_roster.py:35); enforced by hooks 5d31dad/015fac7 |
| R36 | DONE | d6c1573, 73b0986, dfcbf16, b483b22: ops-generated CLI with `--json` OpResult (46 ops) and PDL 1.0 schema + `design.migrate` + docs/pdl/reference.md. Concept-a's own migration is tracked under R1 |
| R38 | DONE | 4f8f2b2 (knowledge/morphological-chart.yaml synthesized from 5 literature sources, `sources:` line 2) + 9d1ce6a (`morph.add-option` requires a source, `morph.coverage`); team task update_morph_chart.sh |
| R39 | OPEN | dbf-hangar exists and adapts aircraft-platform, proofs and interfaces (4f8f2b2, 33e6655, b43daf0, 654888d). But several §1b rows have not landed: concept-A params/BOM/requirements/files (U2.5d, not yet a unit), config-study knowledge (U2.2-2, unscheduled), Explorer features (U3.1), blender/sitl adapters (`planned`) |
| R40 | OPEN | Integration started (same commits as R39), but "one software tool everyone works on" is not met yet: the Explorer still lives in DBF-Combined until U3.1, and no teammate works in hangar until the U3.4 acceptance |

DONE 13, OPEN 9.

## Flags for the conductor / advisor (not verdicts)

1. "U2.5d" and "U2.2-2" are referenced in briefs but are not units in plan §7. Four OPEN verdicts (R1, R12, R14, R39) wait on U2.5d.
2. R31: nothing owns concept-a's assembly sequence (see the R31 row).
3. The plan's unit convention cites `plane design validate --all`, but the CLI has no such option; reviews use `plane baseline check --all` instead.
4. The first full `pytest -q -x` run failed `tests/test_progress.py::test_roadmap_is_short_and_traceable` while the working tree held an uncommitted plan edit. The test passed alone, and after the plan edit was committed (55ab9d4); see the pytest row.
