# U19.2 spec: human-readable scorecards (P315)

Author: W34-T9 (tactician). Measured on main at cae4f6a with `plane validate designs/<id> --tier all --format json` (c172-rc 75 s, concept-a about 3 min; PLANE_CAD_OVERLAY=off). Note: the command is `plane validate PATH --format md|json --out FILE`; `plane design validate` has no `--out`. The markdown is the `markdown` key of `design.validate` (`core/hangar/ops/design.py:74`) and the default of `plane validate`.

## 1. Inventory

Producers: `Scorecard.to_markdown` (`core/hangar/design.py:136`), `CheckResult` (`design.py:66`), 296 `CheckResult(` call sites (`checks.py` 90, `gates/*.py` about 200). Gate table: `standards/gates.yaml` (10 tier gates + 11 discipline checks). Consumers: `plane validate` (CLI, md), `design.validate` (ops/MCP, JSON + md), Studio (`viewer/modes/designs.js` rows, `viewer/ui/inspector.js` part check list, `viewer/vp/status.js` part colours), `studio.py:266` (md download), `baseline.py` (reads JSON only).

| | c172-rc | concept-a | both |
|---|---|---|---|
| rows | 287 | 938 | 1225 |
| PASS / WARN / SKIP / FAIL | 167 / 31 / 89 / 0 | 703 / 148 / 77 / 10 | 870 / 179 / 166 / 10 |
| check families (first two id segments) | | | 50 |

Families: T0 schema generator mission (version, parameters, unique_ids on error paths); T1 articulation attachment connectivity interfaces interference kinematic_link motor_has_prop point_mass_location pose watertight; T2 fea_strength hover_moment joint_load joint_rf sim_drop_loads sim_rest sim_stable; T3 control_authority cruise_stall_ratio dynamic_modes endurance hover_tw lateral_cg mass planform_matches_geometry spar_bending stall static_margin tail_volume transition_margin trim wing_area_complete wing_loading; T4 method; T5 part107_mass registration; T6 link mechanism ratio; T7 assembly electrical_rating transport wiring; T8 bom budget program; T9 claim. Many rows add a third segment (`T7.wiring.e-hrn-01`, `T8.bom.verified.w06`, `T6.link.elevon-r`): the family is the first two segments, the rest names the subject.

Readable today (measured on the 355 non-PASS rows of both designs; PASS rows are one line "ok" and are not the problem):
- 111 of 355 (31%) state a number and a comparison (limit, target, "vs", "exceeds").
- 174 of 179 WARN rows start with the machine prefix `report-only until 2026-12-08: ` (`gates/__init__.py:15`) and bury the real sentence behind it; the unwrapped FAIL or SKIP is only in `data.raw_status` / `data.would_be`.
- 0 name the part in words: parts are ids (`cge-001`, `wng-006-r`, `hrn-002`); concept-a ids are opaque. No component has a `name`; 134 of 153 have a `description` that starts with a usable noun phrase ("Hub (printed PETG, ...)").
- 0 give the source of the limit; the criterion column shows `file#key` only. The source text exists in `standards/*.yaml` (`source:` per key, or `pending`).
- about 130 contain an action-like word, but it is buried in the middle (for example "add exposed_ok with a reason or reroute"); none are in a separate hint.
- 166 SKIP rows: 77 are "not applicable" (`data.not_applicable`, not a result), the rest are real "not checked" (placeholder rating, linkage not modelled, no OpenCAE result yet). Today both look alike. 39 identical-looking `T2.joint_load` SKIP rows and 39 `T2.sim_drop_loads` rows in c172-rc make the list unreadable.
- Part naming in `data` is inconsistent (U19.1 finding A11, fixed by U19.1 B6): `component`, `parts`, `pair`, `joint` (an attachment id, not a part), `link_pairs`. `viewer/vp/status.js::rowParts` already resolves them in JS; U19.2 resolves them once in Python.

Non-PASS families that occur in the two designs (the ones the registry must fully template, brief 1 list A): T1.kinematic_link, T2.fea_strength, T2.joint_load, T2.joint_rf, T2.sim_drop_loads, T2.sim_rest, T3.control_authority, T3.cruise_stall_ratio, T3.dynamic_modes, T3.endurance, T3.hover_tw, T3.planform_matches_geometry, T3.spar_bending, T3.static_margin, T3.tail_volume, T3.transition_margin, T3.trim, T3.wing_loading, T2.hover_moment, T6.link, T7.assembly, T7.electrical_rating, T7.transport, T7.wiring, T8.bom, T8.program.

## 2. Row format

Every non-PASS row a person sees becomes five lines (PASS rows stay one short line, grouped by family with a count):

```
STATUS  <Plain name>: <Part readable name (id)>[, <second part>]
<One sentence: what was measured, the value with unit, the limit with unit, and where the limit comes from.>
Fix: <what to do>                         (only where the registry has a hint; never invented)
Details: <the original machine message>   (markdown: indented line; Studio: behind "details")
[T2.fea_strength]                          (machine id: markdown column; Studio: small grey text and hover title)
```

Rules (these are the acceptance rules the briefs test):
1. Plain name = `title` of the family in the registry (sentence case, no tier jargon, no id). Status words stay FAIL / WARN / SKIP / PASS; a not-applicable SKIP is labelled "Not applicable" and counted separately, never listed among problems.
2. Value vs limit: built from `row.data` numbers and the limit read from `standards/` through the row's `criterion` (`file#key`: `value`, or `min`/`max`, units are written in the template text). Source text = that key's `source:`; when it is `pending` the sentence says "source pending". A limit is never typed into the registry (thresholds live only in `standards/`, CLAUDE.md).
3. Parts by readable name. `part_label(design, id)`: `name` if the component has one; else the first clause of `description` (cut at the first of ` (`, `, `, `; `, ` - `; at most 40 characters); else the id with hyphens as spaces. Always printed as `Label (id)`. Parts come from `data.component`, `data.parts`, `data.pair`, `data.link_pairs`, and `data.joint` resolved through the attachment's parent and child.
4. Fix hint: one imperative sentence in the registry, only where a person can act (reroute, give a rating, add a mechanism). No hint is better than a guess.
5. Report-only wrapper: strip the prefix and print "Report-only until 2026-12-08" as a tag, plus "would be FAIL today" from `data.would_be` or `data.raw_status` when present. The status shown stays WARN (behaviour unchanged).
6. Grouping: three views of the same rows. By problem (default): FAIL first, then WARN, then Not checked, one block per family, repeated rows of a family folded into one entry listing parts ("39 joints"), worst value first. By part: one block per part id with its rows (design-level rows under "Whole aircraft"). By tier (today's order). Design-level rows = `baseline.DESIGN_LEVEL` (same set Studio mirrors) or more than a third of the parts.
7. Machine ids stay: markdown keeps the full old table as an appendix (byte-identical to today's table lines), Studio keeps `data-check-id` and shows the id on hover and in small text.
8. JSON unchanged: `Scorecard.to_dict()` and `plane validate --format json` do not change by one byte. Texts are computed at render time, never stored in `CheckResult`. (The `markdown` key of the `design.validate` op result is a rendering and does change; the scorecard dict next to it does not.)
9. No threshold or gate behaviour change; a row's status, order and count do not change.

## 3. Where the plain text lives

One registry next to the gates: `core/hangar/gates/describe.yaml` (data, templates only) read by `core/hangar/gates/describe.py` (loader, label rules, renderer). Key = family (first two id segments). Per family:

```yaml
T2.fea_strength:
  title: "Printed part is too weak"
  what:                       # one template per status; names come from row.data / standards / parts
    FAIL: "{label} reaches {max_von_mises_away_mpa:.1f} MPa in the {case} case; the limit is {limit} MPa ({source}). Safety factor {safety_factor_at_ultimate:.2f}, must be at least 1."
  hint: "Make the part thicker where the load enters it, or change material, then run `plane fea {design_id} --all`."
  group: part                 # part | problem | design (design = whole-aircraft row)
```

Optional `extract:` per family = one regex with named groups run on the unwrapped message; each group becomes a placeholder (for values only the message carries, e.g. the load case or the rating).

Placeholders: any `data` key; `{limit}`, `{min}`, `{max}`, `{source}` (the first 100 characters of the key's `source:`, cut at a word; the examples below paraphrase it) from `standards/<file>#<key>`; `{label}`, `{labels}` from parts; `{design_id}`; `{message}` = the raw message with the report-only prefix stripped. A missing placeholder never raises: the renderer falls back to `{message}` for that row (so an unknown family or a short `data` still prints the old text under a humanised title). A test fails when a family that code can emit has no entry (scan of `CheckResult("Tn.xxx"` literals plus `standards/gates.yaml`). The viewer holds no text; Studio gets finished sentences from the server (section 5).

## 4. Before / after (real rows)

1. FAIL, concept-a, T2.fea_strength (part)
   Before: `T2.fea_strength FAIL | cge-001 landing: 34.44 MPa peak away from the clamps vs 12.6 MPa allowable at 1.5x load (SF 0.37; 34.44 MPa at the clamp edges) | design-standards.yaml#fea_allowable_printed_petg_mpa`
   After:
   `FAIL  Printed part is too weak: Hub (cge-001), landing case`
   `The hub reaches 34.4 MPa in the landing case; printed PETG is allowed 12.6 MPa (UltiMaker PETG data sheet v1.00, Z-direction strength minus one standard deviation). Safety factor 0.37; it must be at least 1.`
   `Fix: make the part thicker where the load enters it, or change material, then run plane fea concept-a --all.`

2. FAIL, concept-a, T3.static_margin (design-level)
   Before: `T3.static_margin FAIL | 16.4% MAC (NP x=59 mm, CG x=21 mm; target 5%-15%; fuselage effect not modelled) (mesh wing: chord measured at 41 stations) | design-standards.yaml#static_margin`
   After:
   `FAIL  Aircraft is too stable (static margin): whole aircraft`
   `The centre of gravity sits 16.4% of the wing chord ahead of the neutral point; the allowed band is 5% to 15% (MIT 16.01 design rules, uavmodel DIY UAV guide). Above the band means the nose is heavy.`
   `Fix: move the centre of gravity aft (for example the battery) or move the wing forward until the margin is under 15%.`

3. FAIL, concept-a, T2.sim_drop_loads (part; joint resolved to its two parts)
   Before: `T2.sim_drop_loads FAIL | E-WNG-20: peak 1.8 N in drop test exceeds rating 1.4 N | design-standards.yaml#landing_load_factor`
   After:
   `FAIL  Joint breaks in the drop test: Elevon right (wng-006-r) to Elevon balance (wng-007-r)`
   `In the simulated drop this glued joint (E-WNG-20) carries a peak of 1.8 N; it is rated for 1.4 N (rating derived from foam shear; the landing load factor 3.0 has source pending).`
   `Fix: raise the joint rating (more bonded area or a stronger connection) or reduce what hangs on it.`

4. WARN, concept-a, T7.wiring (report-only wrapper, two parts)
   Before: `T7.wiring.e-hrn-01 WARN | report-only until 2026-12-08: harness e-hrn-01: segment pwr-001 to hrn-002 leaves the envelopes by 40 mm (> 5 mm); add exposed_ok with a reason or reroute | gate-thresholds.yaml#wire_clearance_mm`
   After:
   `WARN  Wire runs outside the airframe: Pack Tattu 2300 mAh 4S (pwr-001), XT60 female + 14 AWG tail to the ESC (hrn-002)   [report-only until 2026-12-08, would FAIL today]`
   `Harness e-hrn-01 leaves the part envelopes by 40 mm between these two parts; the limit is 5 mm (gate-thresholds.yaml#wire_clearance_mm, source pending).`
   `Fix: reroute the wire through the airframe, or add exposed_ok with a reason to the harness.`

5. WARN, c172-rc, T3.tail_volume (design-level, provisional limit)
   Before: `T3.tail_volume WARN | Vh 0.631 above 0.3-0.6; provisional: stability.yaml#tail_volume_h_min pending | stability.yaml#tail_volume_h_min`
   After:
   `WARN  Horizontal tail is large for its wing: Tailplane and fin (tail-fixed)`
   `Horizontal tail volume is 0.631; the usual band is 0.30 to 0.60 (a scale-RC note quoting MIT; source pending, so this is advice, not a rule).`
   `Fix: none needed for a scale copy (the standards note gives about 0.64 for the real Cessna 172); otherwise reduce the tail area or arm.`

6. WARN, c172-rc, T2.joint_rf (cannot be judged)
   Before: `T2.joint_rf WARN | report-only until 2026-12-08: fuselage-gear: CT-M3-SHCS-NYLOC has no rated_load_n in standards/connection-types.yaml and the joint states none (pending a sourced rating) | load-cases.yaml#joint_rf_min`
   After:
   `WARN  Joint strength can't be judged: Fuselage and cowl (fuselage) to landing-gear (landing-gear)   [report-only until 2026-12-08]`
   `The bolted joint fuselage-gear uses connection type CT-M3-SHCS-NYLOC, which has no rated load, so its reserve factor (rating / load, must be at least 1.0) cannot be computed.`
   `Fix: add a sourced rated_load_n for CT-M3-SHCS-NYLOC in standards/connection-types.yaml.`

7. SKIP, c172-rc, T1.kinematic_link (not checked)
   Before: `T1.kinematic_link SKIP | range min of tail-elevator (-25°): 1 pair(s) not checked — linkage path not modelled: elevator, tail-elevator-rod | schema/plane.schema.json`
   After:
   `SKIP  Moving linkage not checked: Elevator (elevator), tail elevator rod (tail-elevator-rod)`
   `With the elevator at its -25 degree limit the rod and the elevator touch and the tool cannot tell if that is a clash, because the linkage between them is not modelled.`
   `Fix: describe the linkage as a four_bar mechanism (plane design add-linkage) so it is checked.`

8. SKIP, c172-rc, T2.joint_load (39 rows folded into one)
   Before (39 rows like): `T2.joint_load SKIP | fuselage-wing: carries 2.1 N; rating is a placeholder, not checked | design-standards.yaml#landing_load_factor`
   After:
   `SKIP  Joint strength not checked: 39 joints`
   `Each of these 39 joints (first: fuselage-wing, fuselage-tail, tail-elevator, ...) carries a landing load but has only a placeholder rating, so no pass or fail is given. Landing load factor 3.0, source pending.`
   `Fix: give each joint a connection type with a sourced rated_load_n.` (the 39 joints are listed one per line under a "show all" fold)

Also covered by the format (no separate example): not-applicable rows ("T3.hover_tw: this aircraft does not hover on thrust (fixed wing), so the check is left out") fold into one line "77 checks do not apply to this aircraft" with the list behind a fold.

## 5. What changes where

Markdown (`Scorecard.to_markdown(design=None)`, `core/hangar/design.py`; callers `ops/design.py:74` and `studio.py:266` pass the design): header and verdict as today plus a counts line; "## Needs fixing" (FAIL blocks, by problem, the five-line format as list items), "## Warnings", "## Not checked", "## Not applicable (N)" one line, "## Passing (N checks)" one line per family with a count; "## Full table" = today's table unchanged (the machine view with ids and criterion). The `Fidelity:` line stays at the end. With `design=None` labels fall back to humanised ids, so old callers keep working.

CLI: `plane validate` prints the same markdown; no new flag; `--format json` byte-identical. The counts line at the top ("10 FAIL, 179 WARN, 166 not checked, 870 pass") is what the user reads first.

Studio: `build_index` also writes `<id>.rows.json` (new sidecar; `scorecard.json` unchanged) holding for every row, in scorecard order, the rendered text (title, sentence, hint, parts as `{id,label}`, group keys, source text, report-only flag). The index entry gets a `rows` key. The Scorecard tab renders from it: bold plain name, one sentence, "Fix:" line, part chips (click focuses the parts as the row does today), small grey machine id with a `title=` hover, a details fold with the raw message, and a group switch (Problem / Part / Tier, default Problem) in place of the fixed tier-only list; repeated rows fold ("39 joints", expandable). The inspector's part check list shows the plain name and sentence instead of id and raw message; click still scrolls to the row. If `rows.json` is missing (old index, old Pages build) Studio renders today's rows unchanged.

## 6. Briefs (in order, one branch each)

| Brief | Class | What | Branch |
|---|---|---|---|
| U19.2-1-registry | hard | `describe.yaml` + `describe.py` + tests; 50 families | `std/u19.2-1-registry` |
| U19.2-2-markdown | easy | markdown and CLI use the registry; old table kept as appendix | `std/u19.2-2-markdown` |
| U19.2-3-rows-json | easy | `<id>.rows.json` in build_index, index entry key | `std/u19.2-3-rows-json` |
| U19.2-4-studio | hard | Scorecard tab and inspector render from rows.json, group switch, hover id | `std/u19.2-4-studio` |

Order is forced (2 and 3 import 1; 4 needs 3). Plan step 2 (Tristan reads section 4) happens before brief 1 is launched; his wording changes go into the example text of brief 1, which is the test fixture.
