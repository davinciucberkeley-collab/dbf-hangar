# U19.1 UI spec: Studio overhaul and a better 3D viewer (W34-A2, 2026-11-25)

Inputs: plan unit U19.1 (D92, P285, must-haves P286), `u19.1/recon.md` (f724ed8, Option B: extend our three.js app),
`u16.1/design-note.md` (S1 four-bar rods, S2 wheels on continuous joints, S3 servos in bays, S8 wires as tubes,
S9 x-ray). Repo at f724ed8. Measured on scratch copies (concept-a from main; c172-rc from the PR #9 branch
`design/c172-rc/rehearsal-4-cessna-172-do-not-merge`); `designs/` in the checkout was not written.

## 0. Intent (true when U19.1 is done)

Tristan opens `plane studio`, picks c172-rc or concept-a and, in one viewport: drags an explode slider and the plane
comes apart by assembly level; turns on x-ray or a section plane and clicks the battery, ESC, a servo or a wire inside
the fuselage; drags a part with a gizmo, sees "moved, not saved", presses Apply, types a why, and the design,
CHANGELOG and checks update (the T1 re-run shows on that part). FAIL parts are red in the model and the tree.
Mechanisms (rods, wheels) play from a timeline under the model. The Pages build shows the same viewer without Apply.

## 1. Audit of today's Studio (evidence)

| # | Finding | Evidence |
|---|---|---|
| A1 | Four WebGL renderers are created at start (Pages too), even when one is visible; one rAF loop ticks all four forever | `app.js` init: `new Viewport` for vp-main, vp-a, vp-b, vp-phys |
| A2 | Nothing is disposed: geometries and materials survive design switches; every loaded GLB stays cached; each mesh gets its own `material.clone()` (113 on concept-a) | `Viewport.clear()` only calls `root.clear()`; `cache.glb` cleared only by Studio `reload()` |
| A3 | Flat look: hemisphere + one directional light, no environment map, no tone mapping, no shadows, no edges; colours are per-type hues baked as RGBA vertex colours | `Viewport` constructor; `export.py` `TYPE_HUES`, `face_colors` (propellers alpha 90) |
| A4 | Selection = emissive tint + every other part at 0.28 opacity; no part tree, hide/isolate, fit-to-selection or multi-select | `highlight()`; `onPick()` toggles one id |
| A5 | Inside parts cannot be reached: the ray takes the first hit (the skin) and dimmed parts stay pickable | `pick()`: `intersectObject(model, true).find(...)` |
| A6 | The GLB is flat: one node per component at identity, vertices already placed; no hierarchy or assembly levels | `export.to_scene`: `add_geometry(..., node_name=c["id"])`, no transform; metadata only `type`, `mass_g` |
| A7 | The assembly tree exists in the data, not in the export: `root` + attachments parent -> child | concept-a: 115 components, 142 attachments, root `wng-001`, depth 0-9, 3 roots (`wng-001`, `hwc-002-l/r` unreached); c172-rc: 35 components, 36 attachments, root `fuselage`, depth 0-4, 1 root |
| A8 | Every component has a `position` list in mm (115/115, 35/35), so one drag = one `design.set` key per part; but articulation `pivot`/`axis`, cavity positions and attachment coordinates are literal and do not follow | schema `articulation.pivot` "body frame (mm), at 0 deg"; `geometry.py:28` `t[:3, 3] = position` |
| A9 | Editing positions today: three number cells per part in the Edit dialog, kind + why, one atomic `design.set` with `also`; `design.set` has no dry run | `modes/edit.js` `editDialog`; `ops/edit.py` `set_op(path, key, value, why, kind, also, ...)` |
| A10 | After a mutating op Studio rescans, the hash changes, a full check job runs and the page reloads on the `rev` poll; this already gives "T1 re-runs after Apply" | `studio.py` `do_POST`: `if registry()[name].mutates and res.ok: studio.scan()`; `edit.js` `poll()` |
| A11 | Check rows name parts through three keys used inconsistently: `component` (one id), `parts` (ids, but schema paths in one place), `pair` (two ids, "a & b" strings, or a list of id pairs) | `checks.py:71,96,1243` `component`; `checks.py:776,792` `parts` ids vs `checks.py:141` `parts` = schema paths; `checks.py:586` pair of ids vs `:595` strings vs `gates/mechanisms.py:234` id pairs. `designs.js` treats any length-2 `pair` as two ids, so two unchecked pairs show "show a & b + c & d" and highlight nothing |
| A12 | Physics is a separate mode and viewport; it writes `node.matrix` directly (`matrixAutoUpdate = false`), needs nodes at rest origin, steps with a 60 ms `setInterval` | `modes/physics.js` `apply()` |
| A13 | Compare = two full viewports + table; Stress, Ledger, Updates are plain tables (fine as is) | `modes/*.js` |
| A14 | Local GLBs include the GrabCAD overlay (D83); `entry.local_only` is written but never shown | `index.py:156-159`; c172 servos with overlay: 4 x 17,774 triangles (74 % of the model) |
| A15 | Playwright smoke tests exist and run in CI (dev extra `playwright>=1.45`; `validate.yml` installs chromium); locally the module is missing so the file skips; the CDN URL `three@0.160.0` is pinned in the test | `tests/test_viewer_static.py:19-23,32`; `pyproject.toml:17`; Physics test compares canvas screenshots |
| A16 | Rendering is on demand (`dirty`), `preserveDrawingBuffer: true` (screenshots in tests) | `Viewport.tick()` |

Measured (GLB export only; checks run separately):

| design | GLB | nodes | triangles | biggest meshes | export |
|---|---|---|---|---|---|
| concept-a (overlay on or off: same) | 2.29 MB | 113 (2 point masses not drawn) | 118,512 | cge-001 22,874; cge-003-* ~4,600 each | 1.1-1.7 s |
| c172-rc, overlay on (local) | 1.14 MB | 35 | 96,044 | 4 servos 17,774 each | 2.3 s |
| c172-rc, overlay off (= CI, Pages) | 0.50 MB | 35 | 24,996 | wing-core 8,296; landing-gear 6,222 | 0.4 s |

Check rows that name a part (`validate`, scratch): concept-a 934 rows (10 FAIL, 146 WARN), 32 of 156 FAIL/WARN
name a component in `data` or the message; c172-rc 254 rows (6 FAIL, 26 WARN), 29 of 32. So colour-by-status works
on c172 nearly as is, but on concept-a most WARNs (likely attachment rows; not classified here) would stay uncoloured.

Conclusion: 113 meshes and ~120k triangles are small; no BVH or merging in v1 (recon 4.10). The costs to fix are A1
(contexts), A2 (no dispose) and, once x-ray is on, transparent sorting. Recon Option B (extend ours) is confirmed:
nothing in the audit needs a ready-made viewer, and A10 means Apply needs no new server route.

## 2. Target UI

### 2.1 Layout (Designs mode becomes Model; Physics folds into it as a timeline)

```
+------------------------------------------------------------------------------------------------+
| Plane Studio  [design v]   Model | Compare | Stress | Ledger | Updates         [Check] [Edit] ..|
+---------------+-------------------------------------------------------------+------------------+
| PARTS         | [Select][Move][Measure] [Explode --o----] [X-ray] [Section] | INSPECTOR        |
| [filter    ]  | [Iso][Front][Top][Side][Fit]   Colour by [status v]         | servo-elev servo |
| v fuselage  o | +---------------------------------------------------------+ | mass 12 g        |
|   v wing    o | |                                                [cube] | | position mm      |
|     srv-l  o! | |                     3D viewport                       | |  590  -9  2      |
|   battery   o | |                                                       | | parent fuselage  |
|   esc       o | |  [ 2 parts moved, not saved   Review & Apply  Revert ]| | checks (3)       |
| v Wiring      | +---------------------------------------------------------+ |  FAIL T1.overlap |
|   rx-srv-l  o | TIMELINE [elevator-drive v] [>] |---o------| 12 deg x1 loop | Scorecard | BOM  |
+---------------+-------------------------------------------------------------+------------------+
  o = eye toggle, ! = FAIL/WARN dot
```
- Left: part tree from the attachment tree (3.1): eye toggle, status dot, groups Wiring (visual-only, U16.1 S8) and
  Unattached. The design list becomes a picker (text and VTOL filters kept inside it).
- Centre: floating toolbar, viewport, view cube, apply bar (only while moves are pending), timeline (only when the
  design has mechanisms).
- Right: inspector for the selection over tabs Scorecard (as today, FAIL first, rows clickable) and BOM.
- Compare keeps its two viewports, created lazily, toolbar without Move. Stress, Ledger, Updates unchanged.
- Deep links keep working: `#m=designs` -> Model; `#m=physics` -> Model with the timeline open.

### 2.2 Interaction rules

Selection: click selects one part, Ctrl-click adds, Esc clears, double-click frames. Tree and viewport select both
ways. Picking skips hidden, ghosted and clipped-away parts; Alt-click cycles through hits front to back.

Must-have 3, see inside:
- X-ray ghosts the skin set: types fuselage, wing, tail_surface, plus parts ghosted from the tree (opacity ~0.15,
  depthWrite off, drawn last, not pickable). Battery, ESC, servos, receiver, wires stay solid and pickable.
- Section: axis X/Y/Z, slider across the model box, flip; one clipping plane shared by all materials; uncapped
  (back faces show, as with `DoubleSide` today).
- Tree verbs: Hide, Isolate, Show all, Ghost (keys H, I, Shift+H).

Must-have 1, explode (view only):
- Slider t in 0..1 and a level stepper (All, 1 .. max depth). Hierarchy strategy (default): each part moves along
  (its centre - parent centre) * t * factor, accumulated down the tree, so subassemblies separate and keep their
  shape; "radial" alternative from the model centre. Root never moves; t = 0 restores exactly.
- Explode never enters the apply bar; Move is disabled while t > 0.

Must-have 2, move with explicit Apply:
- Move tool = TransformControls, translate only, on the selected part; snap 1 mm (Shift 0.1 mm); X/Y/Z axis keys;
  numeric nudge in the inspector. Toggle "with attached parts" (default on) moves the subtree below the part.
- A drag stores an edit offset; moved parts get an outline and a "moved" tag. Nothing is written. Revert drops all
  offsets; switching design or mode asks "Discard N unsaved moves?".
- Review & Apply opens a preview: per part `components[<id>].position: [old] -> [new]`; the exact CLI line
  (`plane design set designs/<id> "components[<a>].position" "[x, y, z]" --also ... --kind modify --why "..."`);
  warnings for literal fields that will not follow (pivots of articulated joints touching moved parts, cavities on
  hosts, attachment coordinates). Why is required. Apply = one `design.set` call through `/api/op` (`also` for the
  other parts), so one CHANGELOG entry. Then the existing rescan + check job runs (A10); selection and camera are
  kept, and the inspector shows the moved parts' T1 rows when the check is done.
- Pages build: Move works for exploring; Apply does not exist (`data-edit` rule kept).

Timeline (replaces Physics mode): mechanism picker, play/pause, scrub, speed, loop, rAF instead of setInterval;
reads `<id>.mechanisms.json` unchanged (4x4 per step per node), so U16.1 S1 rods and S2 wheel spins play as sent.

Colour by: type (today) / check status (FAIL red, WARN amber, rest grey, legend) / mass. A check row click selects
and frames its parts and ghosts the rest.

### 2.3 Transform layers (one owner of node matrices)

Per component node: `rest` (identity, A6), `edit` (vec3, scene m), `explode` (vec3), `mech` (Matrix4 from the
timeline, identity when stopped). A changed node gets `node.matrix = T(explode) * T(edit) * mech` with
`matrixAutoUpdate = false`. Only `vp/transforms.js` writes matrices; explode, move and timeline call
`setEdit/setExplode/setMech(id, ...)`. Mechanism transforms are about the rest pivots, so the timeline is disabled
while moves are pending ("Apply or revert moves to play"). Explode and timeline compose. Scene -> PDL:
`d_mm = [dx * 1000, -dz * 1000, dy * 1000]` (inverse of `mmToScene`), rounded to 0.1 mm, in one function with a
round-trip unit test.

## 3. API and data changes

1. `<fid>.parts.json` (index.py, both builds; listed in the entry as `parts`): per component `{id, type, parent,
   attachment, depth, articulated, position_mm, visual_only, local_only}` from `root` + attachments; parts not
   reached from `root` get `parent: null` and depth 0 (concept-a has two). Tree, explode levels, subtree move and
   Apply warnings all read it. No GLB change.
2. Check rows name parts one way: `data.component` (one id), `data.parts` (ids only), `data.pair` (exactly two ids).
   Rename the misuses (`checks.py:141` schema paths -> `paths`; `checks.py:595` -> `unchecked_pairs`;
   `gates/mechanisms.py:234` -> `link_pairs`) and add ids to the FAIL/WARN rows that lack them (rows about an
   attachment: `data.attachment`, mapped to parent + child through parts.json). The brief first lists the
   uncovered concept-a rows by check_id (124 of 156). No threshold or status change.
3. Per-part status is derived in the viewer from those keys (no new file).
4. Apply needs no new route: `/api/op/design.set` exists and is confined to `designs/` (T7, D54). Positions are
   one-line lists in every design (115/115 in concept-a), so `components[<id>].position` = `[x, y, z]` replaces the
   list (already supported). Optional later: a `design.set` dry run for a server-side preview.
5. GLB extras for U16.1 S8 wires: `visual_only: true` per wire node (S8 owns the export); the viewer reads the flag
   (Wiring group, selectable, not movable).
6. `local_only` (A14) shown as a "local CAD" tag in the inspector.
7. Test hooks on `window.planeViewer.vp`: `select(ids)`, `pick(id)`, `explode(t, level)`, `section(axis, v, flip)`,
   `xray(on)`, `move(id, d_mm)`, `pending()`, `state()` (selection, visible ids, coloured ids); tree rows carry
   `data-id`, `aria-selected`, `data-hidden`, `data-status`.

## 4. Build steps (one brief each, cheapest visible win first)

Builder `builder-plus` (Sonnet; the unit is [hard]). Tests in the `tests/test_viewer_static.py` style (slow mark,
wait for `data-ready`, drive the canvas through the hooks, never pixel clicks; screenshot inequality only to prove
"something changed"). Acceptance = what Tristan sees in `plane studio` on concept-a and c172-rc (scratch copy until
U16.1 S0 lands c172-rc on main). Every brief keeps the Pages build working (`test_pages_build_has_no_edit_controls`).

| # | Brief | Tristan sees | Test approach |
|---|---|---|---|
| B0 | three upgrade spike + housekeeping: pin a current three release (the spike confirms the version, TransformControls `getHelper()`, colour management, light units); one renderer per visible viewport, compare viewports created lazily, dispose on clear; split `app.js` into `viewer/vp/*.js` (scene, materials, pick, transforms), no behaviour change | Same app; lighter mode switches | existing smoke tests with the new CDN pin; new: Model mode has exactly 1 canvas; 10 design switches leave `renderer.info.memory.geometries` flat |
| B1 | Look: RoomEnvironment PMREM, MeshStandardMaterial keeping vertex colours, tone mapping, edge lines (EdgesGeometry ~30 deg, built once), soft ground shadow, dark/light theme | A CAD-looking plane with crisp edges | screenshot differs from B0; no console errors; `renderer.info.render.calls` logged for concept-a |
| B2 | Part tree + inspector + selection (Ctrl, Esc, double-click fit), Hide/Isolate/Show all, standard views, fit, damping; `parts.json` (core: index.py, no designs in the PR) | Click a part in tree or model and see its data; hide the wing | tree click sets `aria-selected` and the inspector id; Isolate leaves 1 visible; pytest: parts.json max depth 9 on concept-a, root depth 0 on a fixture |
| B3 | See inside: x-ray skin set, pick-through ghosts, Alt-click cycle, section plane X/Y/Z + flip | Battery, ESC, servos visible and clickable inside c172 | with x-ray on, a hook ray through the fuselage selects the battery; section at mid-x hides the parts in front |
| B4 | Transform layers + explode (hierarchy, radial, level stepper) + timeline replacing Physics (old `#m=physics` links mapped) | Plane comes apart by level; elevator plays under the model | `explode(1)` moves every non-root part, `explode(0)` returns all matrices to identity; the Physics test rewritten on the timeline (follower 20.0) |
| B5 | Move + apply bar + preview + Apply through `design.set` (with `also`), warnings for pivots and cavities, Revert, discard prompt; Pages has no Apply | Drag a servo 10 mm aft, Apply with a why: plane.yaml and CHANGELOG change once, checks re-run, T1 rows on the servo | Studio on a tmp designs dir: `move(servo, [10,0,0])`, Apply, assert one position line changed by exactly 10 mm and one CHANGELOG entry with the why; Revert leaves the file byte-identical; unit test of the mm/scene conversion |
| B6 | Check rows carry ids (core, 3.2; may go first as its own small PR) + colour by status/mass + tree status dots + row click frames parts | FAIL parts red; clicking a FAIL row frames its parts | pytest: every T1 FAIL/WARN row on a clashing fixture names ids; scorecard tests green after the key renames; viewer: `state()` lists the FAIL ids coloured |
| B7 | Layout pass: three-pane grid, design picker, Scorecard/BOM tabs, compare tidy, stacked under 1100 px | The layout of 2.1 | every-mode smoke test; pages-no-edit test; deep-link test for old hashes |
| B8 | Measure (two-click point to point, vertex snap, mm label) + view cube | Distance in mm between two points | hook-driven measure on a fixture box of known size, within 0.5 mm |

Order: B0 first because every later brief edits the files it splits and the upgrade changes the look B1 tunes. B2
before B3-B5 because all three need the tree and selection. B4 before B5 because Move writes the same transform
layer. Tristan looks after B3 (see inside), B5 (all three must-haves done) and B7.
U16.1 links: B4 works unchanged when S1/S2 change the transforms (same file format); S8 wires appear under Wiring;
B3 is the viewer x-ray of U16.1 S9, so S9 drops that item.

## 5. Out of scope

Rotate gizmo and writing `rotation_deg`; re-deriving pivots, cavities or linkages on Apply (U16.1 S4 add-linkage owns
that); section caps and multiple planes; a what-if T1 before Apply (needs a dry run + check); adopting
three-cad-viewer or xeokit, frameworks, bundlers, TypeScript; BatchedMesh, BVH; AO and outline post-processing by
default (a toggle after B1 only if frame time allows); live MuJoCo; adding parts or editing joints in 3D; publishing
overlay geometry (D83).

## 6. Risks

- three upgrade from 0.160: addon paths, TransformControls API, colour and light defaults change the look. B0 alone,
  screenshots before/after, CDN pin updated in the test. Demo-day network: vendoring three into `viewer/vendor/`
  removes the CDN dependency (decision for Tristan; default: stay on the CDN, pinned).
- WebGL contexts and memory on this PC: 4 contexts today (A1); target 1 in Model, 2 in Compare; dispose on clear;
  keep on-demand rendering (damping and the timeline request frames only while something moves).
- Transparent sorting with x-ray: ghost only the skin set, fixed render order, depthWrite off.
- Apply writes a wrong value (units, axes, subtree): one conversion function, round-trip test, a preview with
  old -> new and the CLI line, one atomic `design.set`; Studio still writes only `designs/`.
- Moved parts leave literal pivots, cavities and linkage coordinates behind: the preview warns; T1.articulation flags
  pivots after the check; U16.1 S4 add-linkage is the real fix.
- Public build: edit code never loads there (`studio` flag); `parts.json` adds nothing not already public in
  plane.yaml; overlay meshes never reach Pages (A14).
- Performance: ~120k triangles and 113 meshes are fine; edges add line segments, built once per load; measure
  `renderer.info` in B1 before optimising anything.
- Tests: canvas clicks are flaky, so hooks. Playwright is missing locally; brief step for conductor approval:
  `.venv/Scripts/pip install -e .[dev]` then `.venv/Scripts/python -m playwright install chromium`; run one test at a
  time (`pytest tests/test_viewer_static.py -k NAME`), never parallel browsers; CI runs the whole file.
- U16.1 S1: a four-bar branch flip must appear as a reported jam, never as a jump in the timeline (S1 owns it).
