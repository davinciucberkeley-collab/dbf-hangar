# Review: discipline fold-in (plan step DF-R, §6g)

Reviewer: DF-R (Opus, fresh), 2026-11-21. Plan-only change; no code built.
Diff: `git diff 08ba4e6 55f9611 -- plans/2026-11-20-standardization.md PROVENANCE.md plans/2026-11-20-standardization/briefs/U2.2-standards.md` (W2 merges and U2.1 checkbox ticks ignored), plus `discipline-extract/` (45 role files, `_RULES.md` with DF-A amendments) and `ledger/items.yaml`.
Spec: Tristan's request (§6g task text) and plan §1b. Criteria: `_RULES.md` (codes), plan §1c, §3 standing rule, §5 roster, §6a, CLAUDE.md, `standards/review-scorecard.md`.

## Automated (reviewer run, Windows, main @ 55f9611, `PYTHONPATH=core`; the `plane` on PATH is a stale install without `design`/`ledger`)
| Check | Result |
|---|---|
| `pytest -q` (full) | 456 passed, 31 deselected, 0 failed (17 min) |
| `pytest -q tests/test_ledger.py tests/test_progress.py` | 23 passed |
| `plane design validate --all --json` | n/a: `No such option '--all'` (as in the W2 review); equivalent `plane baseline check --all`: exit 0, tiltwing-cakir 37 known, 0 regressions, others accepted |
| `plane ledger check` | `ledger check: no problems` |
| `plane progress --check` | `PROGRESS.md is up to date` |
| Extract script (parse every `## Checks` table row, last column; allowed codes from `_RULES.md` + DF-A amendments) | 1935 rows, every row exactly one allowed code (0 bad, 0 multi-code); D4 has 0 rows |
| Totals vs §1c line 114 | GATE 259, STD 376 (367 distinct keys), SKILL 97, SCORECARD 60, KNOW 128 (19 topics), DROP 1015 (k09l-instance 650, duplicate 271, covered 47, k09l-only 4, generated-output 38, out-of-scope 5): all match |
| Per-role table §1c lines 129-173 | all 45 rows match the script (rows and six code columns) |
| Removed codes in extracts (`review-mass`, `gate-thresholds`, `T7.thermal`, `T2.modal_separation`, `T2.load_case_coverage`) | none as a code; 1 left as a DROP rule pointer (fix 6) |

## Criteria
| Criterion | Result | Reason |
|---|---|---|
| No agents or new roles (§5, request (a)) | PASS | `.claude/agents/` still 10 files; only change is one stop-rule line in conductor.md; §6g uses scout/advisor/reviewer only; U3.5 adds a pointer line to reviewer/design-engineer, no role |
| Every item lands as exactly one allowed code (`_RULES.md`) | PASS | script above |
| §1c counts match the files | PARTIAL | line 114 and the per-role table match; lines 122, 123 and D19 (297) still carry pre-re-tag numbers (fixes 1-3) |
| U3.5, U3.6 off the core path and in cut order (§6a) | PASS | core path line 369 unchanged; cut order 0a U3.6, 0b U3.5 (lines 373-374) |
| Skill size limit and tests in U3.5 | PASS | line 1057 "each ≤ 120 lines"; line 1060 `test_discipline_skills_size_and_sections`, `test_discipline_skill_items_cite_extract_rows`; U3.2 `test_skill_under_120_lines` (line 1027) |
| D19-D21 defaults and dates (§3 standing rule) | PASS | lines 297-299: default, By 11-24, status "decided: default (standing rule, 2026-11-21)"; ledger D19-D21 `decided` |
| Ledger follow-ups T12-T14 | PARTIAL | present (items.yaml 826-856); T14 text says "seven" gates (fix 5) |
| PROVENANCE row | PASS | PROVENANCE.md last row: 45 extract files, DBF-Combined @ a93f14d, "no files copied" |
| Amendments U2.1/U2.2/U3.2 match §1c | PARTIAL | U2.1 (867) and U3.2 (1023) match; U2.2 plan text (902) matches D19 but its brief (line 136) is broader and governs (§4); §1c line 117 promises U3.6 work that U3.6 does not list (fixes 7, 8) |
| No leftovers from before DF-A | PARTIAL | `gate-thresholds` only in "No gate-thresholds.yaml" (119, correct); "seven" only in D20's question (correct); stale: §1b 105 "40 roles", T14 "seven", A2.md:30 pointer |
| Work bigger than one unit → new units, not on core path | PASS | split into U3.5 and U3.6 [hard], W3, cut order 0a/0b |

## Required fixes
1. `plans/2026-11-20-standardization.md:297` D19: "§1c proposes 501 standards keys" → "§1c proposes 367 standards keys (376 rows)". Same text in `ledger/items.yaml:861`.
2. `plans/2026-11-20-standardization.md:122`: "(19 topics, 101 rows)" → "(19 topics, 128 rows)".
3. `plans/2026-11-20-standardization.md:123`: "**Dropped (846):**" → "**Dropped (1015):**".
4. `plans/2026-11-20-standardization.md:105` (§1b, edited in this diff): "`redesign/TEAM.md` (40 discipline roles)" → "(45 discipline roles, A1–J6)", matching §1c line 112 and §6g line 483.
5. `ledger/items.yaml:850` T14: "Build U3.6 seven discipline gates" → "Build U3.6 five discipline gates (D20)".
6. `plans/2026-11-20-standardization/discipline-extract/A2.md:30`: "DROP:k09l-instance (rule: GATE:T2.modal_separation)" → "DROP:k09l-instance (rule: SKILL:review-structures/modal)" (`_RULES.md` DF-A amendment: modal_separation rows become `SKILL:review-structures/modal`; the rule pointer must name a code that exists).
7. `plans/2026-11-20-standardization/briefs/U2.2-standards.md:136`: "(only keys a gate or a discipline skill reads)" contradicts plan line 902 ("only for keys that **existing** gates and skills read (U2.1 and earlier); U3.6 adds its own keys as `pending`"); the discipline skills are W3, so U2.2 cannot know which keys they read, and the brief governs (§4). Replace with the line 902 wording.
8. `plans/2026-11-20-standardization.md:117`: "they become test fixtures and criteria text in U3.6" has no matching Files/Test item in U3.6 (lines 1066-1075, which cover only the five new gates). Either add to U3.6 Test "existing-gate rows: criteria text in each gate's docstring/`gates.yaml` and one fixture per gate that a §1c row adds a case to", or change line 117 to "already enforced by the existing gates; the rows stay in the extracts as evidence".

## Non-blocking
1. Line 120: "`review-mass` and `review-interfaces` drew 1 and 0 rows" is pre-re-tag; after DF-A both draw 0 (review-mass recoded to review-aero).
2. Ledger D19-D21 have `decided_in: ''`; `ledger check` accepts it, but "plan §3 (standing rule)" would make the trace explicit.
3. U3.6 test `test_standards_referenced` (line 1071): existing `design-standards.yaml` keys read by FEA/analysis, not by a gate, would fail "read by a gate or named by a skill"; define "referenced" to include analysis readers.
4. U3.6 acceptance "concept-a gets PASS or FAIL ... once its D21 fields are set" depends on a later designs-only PR (D21: values set later with `plane design set`); name that PR/owner or move the check to U3.4.
5. Spot check of STD rows: 112 carry dimensional values; some look design-sized rather than design-independent (`load-cases#vd_ms` 27.2 m/s, `program#vh_max_ms` 21.76 m/s, `program#aeroelastic_speed_min` 32.64 m/s), and `vd_ms` appears under two files. D19's import filter (U2.2/U3.6) must drop or re-home these; not re-tagged here because D19 already keeps them out of `standards/` unless a gate reads them.
6. U3.5 Step 1 says "the three above" but the Test line names two new tests and one existing.
7. Local env: the `plane` script on PATH is a stale install; `pip install -e .` would let reviewers run the documented commands.

Round 1 result (55f9611): REJECT
Eight text fixes (counts, stale "40"/"seven"/modal pointer, brief scope, §1c↔U3.6 promise). The fold-in itself (codes, counts table, no agents, units off the core path, D19-D21, T12-T14, PROVENANCE) meets the spec; re-review needs only the eight lines.

## Round 2 (main @ 874c16f, "discipline fold-in review fixes 1-8")
Verified with `git diff 55f9611 HEAD -- plans/ ledger/items.yaml` (other changes in that range are W2 merges and ticks, ignored).

| Check | Result |
|---|---|
| Extract script, rerun | 1935 rows, every row exactly one allowed code (0 bad, 0 multi-code); totals unchanged and equal to §1c line 114; 367 distinct STD keys; 0 `T2.modal_separation` references left |
| `plane ledger check` | `ledger check: no problems` |
| `plane progress --check` | `PROGRESS.md is up to date` |

| Fix | Result | Evidence |
|---|---|---|
| 1 D19 count | PASS | plan D19 and ledger D19 text: "367 standards keys (after the re-tag pass)" |
| 2 knowledge rows | PASS | §1c: "(19 topics, 128 rows)" |
| 3 dropped rows | PASS | §1c: "**Dropped (1,015):**" |
| 4 §1b roles | PASS | line 105: "(45 discipline roles)" |
| 5 T14 | PASS | items.yaml T14: "five discipline gates" |
| 6 A2.md:30 pointer | PASS | "DROP:k09l-instance (rule: SKILL:review-structures/modal)" |
| 7 U2.2 brief scope | PASS | brief line 136: "only keys that **existing** gates and skills on `main` read"; matches plan line 902 |
| 8 §1c line 117 vs U3.6 | PASS | plan:1072 inside U3.6: existing-gate rows become fixtures and criteria text (`test_discipline_gates.py::test_existing_gate_rows_*`), no new code |

Non-blocking note 5 (design-sized STD keys) is accepted as handled by D19's design-independence filter when keys are imported; U2.2/U3.6 reviewers should confirm `vd_ms`, `vh_max_ms` and `aeroelastic_speed_min` do not enter `standards/` with K09-L values. Non-blocking notes 1-4, 6, 7 stay open as suggestions.

### Verdict: ACCEPT
