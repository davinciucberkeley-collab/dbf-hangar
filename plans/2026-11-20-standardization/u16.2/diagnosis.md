# U16.2 pockets refresh: diagnosis (W34-A3, 2026-11-25)

Unit: U16.2 (was U10.3; T121; D71, D73; `u16.1/design-note.md` S5 and section 7). Branch `std/u16.2-pockets` at
e343403 (revert of 3204340 + merge of main b0eb3c8) plus the uncommitted test edit. Experiments ran on scratch copies
only; the worktree was not touched.

## Intent (done means)
concept-a-param: `cut_files` subtract every sampled swept pose of the moving neighbours, so the 12 swept-pose
T1.interference / T1.attachment_overlap FAIL rows on main are gone; no new FAIL; no threshold changed; other designs
unchanged; tier-1 validate within the D73 relaxed budget (~70 s).

## 1. Cause of the two T1.pocket slivers: float32 operands in the Manifold boolean, not the approach
`importers/dbf_geometry._manifold` hands every operand to manifold3d (3.5.5) as a float32 `Mesh`. Manifold then sets
each operand's tolerance from float32 precision: 4.1e-5 mm for wng-008-ll alone (3.4e-10 mm for the same mesh given as
float64 `Mesh64`), about 1e-4 mm for the 1 m wing core. The pocket cut is one difference of the core against 334
cutters (40 static + 294 swept, many only 0.05 mm apart, `sweeps.MERGE_MM`). Where swept cutters of wng-007 and
wng-010 run over the static wng-008-ll/-rl pocket walls, the result keeps faces that chord 5-14 um into the static
pocket over 340-460 mm2, i.e. 1-2 mm3, above `interference_max_mm3` = 1.0.

Evidence (wing core built in isolation, overlap measured with `checks._overlap_volume`, the T1.pocket function):

| variant (same 334 cutters unless noted) | ll mm3 | rl mm3 | build s | faces |
|---|---|---|---|---|
| A branch as is (one batch difference, float32) | 1.59 | 1.07 | 13-18 | 53 582 |
| S static cutters only (main) | 0 | 0 | 1 | 17 682 |
| U union swept first, then one difference | 2.33 | 0 | 17 | - |
| SEQ static first, then swept (two differences) | 0 | 2.26 | 17 | - |
| IN64 float64 operands (`Mesh64`), float32 output | 0 | 0 | 13-20 | 55 000 |
| D64 float64 operands and output (`to_mesh64`) | 0 | 0 | 13 | - |

- The sliver moves between ll and rl when only the operand order changes (U, SEQ) and vanishes with exact-same geometry
  in float64: numerical, not geometric. No wing vertex lies inside wng-008 (max depth 0.0000 mm); the overlap is a film
  5-14 um thick (2V/A), i.e. faces bridging, not uncut material.
- This also explains the builder's ablations (drop wng-007 poses -> 0; drop wng-010 -> 2.46; two booleans -> 2.26):
  any change of the cutter set reshuffles where the tolerance collapses land.
- The T1.pocket check itself is fine: the same float32 `trimesh.boolean.intersection` reads 0 on the float64-built core.
- Full tier 1 on a scratch copy with the fix below: 0 FAIL (T1.pocket PASS, T1.interference PASS, all 12 swept-pose
  rows gone, 142 T1.attachment PASS).

## 2. Recommended fix (one): float64 operands for the pocket difference only
- `dbf_geometry._manifold(mesh, f64=False)`: when f64, build `m.Manifold(m.Mesh64(vert_properties=float64, tri_verts))`;
  `_boolean(..., f64=False)` passes it through; `kernel.difference(base, tools, f64=False)`; `wing._build` calls
  `kernel.difference(core, hit, f64=True)` for the cut_files difference only. Output stays float32 `to_mesh` (so
  `_separate_pinches` and STL export behave as today); 15 lines.
- Blast radius: only concept-a-param has `cut_files` (grep of designs/*/plane.yaml), so every other design builds
  byte-identically; concept-a-param's baseline is refreshed in the separate designs-only commit the unit already needs.
- No threshold, no epsilon inflation, no geometry change beyond removing the numerical film.
- Tests: the edited `test_concept_a_param_pockets_unchanged` (row PASS) is the regression test and fails on the branch
  today; add one unit test that a float64 operand reports tolerance < 1e-9 and that the A-vs-IN64 core above gives
  T1.pocket PASS.
- Expected time: unchanged from the branch. Wing build 12.9 s (D64) vs 13.0 s (A) in back-to-back runs; profiled tier 1
  99 s (fix) vs 109 s (branch) vs 59 s (main) on a loaded machine (about 20 other python processes), so about the
  builder's 84 s warm on an idle one.

Options considered:
- subtract: drop wng-007/wng-010 swept poses -> sliver goes but their 4-8 swept rows come back. Not enough.
- modify: float64 operands (above). Fixes the cause; no time cost. Chosen.
- adjust: raise `MERGE_MM` / decimate poses -> changes which poses are cut (dropped poses may overlap > 1 mm3) and only
  reshuffles the float32 collapses; inflate swept cutters by an epsilon -> unsourced geometry change, cuts foam the build
  does not; tolerance on the check -> a threshold change, ruled out.
- add: union swept cutters first (U) or two booleans (SEQ) -> tested, sliver moves to the other side (2.33 / 2.26 mm3).

## 3. The test edit is correct
`test_concept_a_param_pockets_unchanged` (faff845, T125) guarded that concept-a-param's neighbours sit at identity, so
no static pocket matrix is needed, and that T1.pocket passes. With swept poses the resolver now adds `matrices` entries
without `matrix`; asserting "no entry carries a static `matrix`" keeps the original intent, and the PASS assertion is
unchanged. Keep it (drop the unit id from the inline comment, or not; cosmetic).

## 4. Time: still over D73; needs Tristan
- Where the extra ~25-45 s goes (profiles, main -> branch): wing build +11 s (one 334-cutter boolean); per-pose contact
  and clash checks +30-38 s, almost all `trimesh.proximity.signed_distance` in `checks._min_distance` against a wing that
  now has 3x the faces (53.6k vs 17.7k), with its rtree rebuilt on every posed copy (`bounds_tree` 4.6 -> 9.6-12.4 s).
- The fix above does not change this. U15.3 (start-up, about 4.4 s) cannot close a ~14 s gap, so the design note's
  rule "if it misses D73 again, it waits for U15.3" would park it indefinitely.
- So D73 needs a decision: (a) relax to about 90 s and merge with the fix; (b) keep parked until a separate core speed
  unit (reuse the unposed wing mesh across poses so its rtree is built once; crop wing vertices/faces to the neighbour's
  box plus the gap limit in `_min_distance`), which would also speed main; (c) leave U16.2 out of v1 (D71 status quo).

## Recommendation
builder-plus on std/u16.2-pockets: brief = section 2 above (float64 operands for the pocket difference only; keep the
test edit; commit; designs-only baseline refresh for concept-a-param; report tier-1 time on an idle machine).
Decision needed from Tristan: D73 option (a), (b) or (c) before merge.

## 5. Follow-up (second stop): T3.planform_matches_geometry -16.3 % on 9b45412
Measured on scratch copies of b0eb3c8 (main) and 9b45412 with `geometry.strip_planform` as `_planform_parts` calls it.
- main 203 021 mm2, no ignored strips; 9b45412 184 455 mm2, `ignored_strips` [5-9] and [31-35], each 76.57 mm.
  Loss = 84.6 mm x 10 strips x 21.95 mm = 18.57k mm2, the whole drop.
- The cause is in the geometry, and it is real. At strip 33 the core section on main is one loop x 0..183.75. On
  9b45412 it is two: x 0..160.42 and x 168.43..183.75, an 8 mm gap through the full thickness. wng-007-l/r is the elevon
  balance lead (10 x 1.07 x 106 mm, 20 mm ahead of the hinge). Swung through +-21 deg, it sweeps a lens through both
  skins. That matches the real part: the lead swings in a lens closed by the PETG lens caps wng-008-ll/lu/rl/ru
  ("clearance to the lead at the +-21 deg stop"), which sit at x 135..179.8 over the same 116 mm of span.
- The measure misreads it. The 8 mm gap is between two loops of the same owner, so `gap_tol` (3 mm) applies, and the
  aft group (15 mm foam + 61.5 mm elevon = 76.57 mm) is dropped as "detached material". It is not detached: the aft foam
  joins the core outside the lens span, and the caps close the opening. The top-view outline is unchanged.
- Variants (fix copy): the uncut generated core (cut_files emptied) gives 203 021 on both main and fix. Lens caps
  added as owners also give 203 021. A 20 mm gap_tol gives 203 021, but that changes a threshold, so it is ruled out.
  All 40 cut_files parts as owners give 219 946 on main as well: the fins and others inflate it, so that is wrong.
- Not (b): clipping the swept cutters inside the skins would leave the lead hitting foam (the 12 rows come back),
  and the real build does open the lens. Not (c): the physical wing loses no planform area.

Recommendation: (a). In `checks._planform_parts`, a generated `wing_panel` with `cut_files` is measured from its build
with `cut_files`/`cut_poses` emptied. cut_files are pockets for parts that sit in them (T1.pocket checks each one), not
outline changes. The build is cached and takes about 1 s.
- This feeds both T3.planform_matches_geometry and the tier-3 aero strips (checks.py:1086, 1095), so MAC, x_ac and AR
  go back to main's values too.
- Every other design is byte-identical: only concept-a-param has cut_files. Main's number is unchanged (203 021 either way).
- Test: concept-a-param's measured area equals the uncut-core area, with swept poses on.
- Brief to builder-plus on the same branch, in core/ (no designs/ change); then rerun `plane baseline check --all`.
