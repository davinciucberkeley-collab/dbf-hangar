# U19.1 recon: a better Studio 3D viewer (W34-X2, 2026-11-25)

## 1. Question

Studio (viewer/app.js, 306 lines, three.js 0.160 from jsDelivr, no build step, one GLB per design)
has a basic viewer. Tristan wants a much better one, including three must-haves added on 11-25:

1. explode the view (slider, by assembly level);
2. move parts by dragging (gizmo; view-only by default, explicit Apply writes back to the design);
3. see inside the plane (x-ray skin, section plane, hide/isolate; battery, ESC, servos, wires visible and selectable).

Which approach per feature, and overall: adopt a ready-made viewer, or extend our three.js app?

## 2. Baseline (read in the repo)

- `viewer/app.js`: `Viewport` class: one WebGLRenderer per viewport (4 of them: main, A, B, physics), HemisphereLight + one
  DirectionalLight, no environment map, no shadows, no outlines, `DoubleSide` materials, OrbitControls without damping.
- Picking: plain `Raycaster.intersectObject(model, true)` against every mesh, no BVH. Fine at 100 meshes, slow on dense
  triangle counts. Selection = emissive tint + other parts faded to 0.28 opacity (a crude x-ray already).
- Parts are GLB nodes named by component id; mass and CG overlay come from per-design JSON. CG marker exists.
- `modes/designs.js`: scorecard on the right; a FAIL row with `data.pair` highlights two parts (the only "analysis on parts" today).
- `modes/physics.js`: replays mechanism steps by setting `matrix` of named nodes (4x4 per step); slider + 60 ms timer. This is
  the animation timeline we would generalise; it already works in the scene graph, which matters for adopt-vs-extend.
- Render loop only draws when `dirty`; good, keep.

## 3. Approaches opened (all fetched 2026-11-25)

| Candidate | What it gives | Licence | Size / delivery | Source opened |
|---|---|---|---|---|
| three-cad-viewer 5.2.1 (bernhard-42) | Full CAD viewer: tree, clip planes with hatched, outlined caps, explode, measure (distance, properties), select, ortho/persp, standard views, animation, Studio mode (PBR, env map, shadows, AO, tone mapping), pick by id | MIT | `dist/three-cad-viewer.esm.min.js` 1.53 MB, CSS 123 KB, ESM on jsDelivr/npm; bundles its own three.js (dependency r187, so a second three copy next to our 0.160) | github.com/bernhard-42/three-cad-viewer, raw package.json, Changes.md, Readme.md, Data Format.md, data.jsdelivr.com file list |
| xeokit SDK | BIM-grade viewer: SectionPlanesPlugin (gizmo, several planes), NavCube, TreeView, distance and angle measurements, edges, SAO, glTF loader, ESM on jsDelivr | AGPLv3 (commercial licence from Creoox) | npm/CDN ES module, size not stated | github.com/xeokit/xeokit-sdk, xeokit docs index and SectionPlanesPlugin page |
| three.js core + addons | TransformControls (translate/rotate, snap, bounds), OutlinePass, GTAOPass/SSAOPass, EffectComposer, stencil-cap clipping, RoomEnvironment | MIT | Already loaded from CDN as ESM addons; no extra build | threejs.org/docs TransformControls page, examples index (OutlinePass, clipping_stencil pages gave only general text; see 8) |
| three-mesh-bvh | Accelerated raycast (claims 500 rays on 80k polys at 60 fps), BatchedMesh raycast, shapecast, "clipped edges" example, distance/edge queries for measuring | MIT | ESM npm package; CDN use not described on its page, but needs to match three version (not stated) | github.com/gkjohnson/three-mesh-bvh and /example listing |
| Online3DViewer (kovacsv) | Many import formats incl. STEP, glTF; engine as npm `online-3d-viewer`; built on three.js | MIT | size not stated | github.com/kovacsv/Online3DViewer; page does NOT mention explode, section, measure, so unverified here |
| Google model-viewer | `<model-viewer>` web component, AR | Apache-2.0 | npm | modelviewer.dev; no part selection, section, measure, explode mentioned; poor fit for CAD |
| Autodesk Viewer (APS) | Section hatches, explode (hierarchy or radial strategy), ViewCube, isolate/hide/show/ghost events, object tree | cloud service, needs access token | n/a | aps.autodesk.com Viewing reference; used as a feature reference only, not adoptable |
| Babylon.js Inspector | scene explorer tree, gizmos, clipping; CDN | Apache-2.0 | heavy, second engine | doc.babylonjs.com inspector page (brief); not adopt |

Not reached: Onshape docs, Fusion web, FreeCAD web, Shapr3D, MuJoCo web, OpenVSP viewer (not opened, so no claims made).
xeokit x-ray, ghost and explode were not on the pages I opened (the docs index omits them); I know of them but cannot cite them.

## 4. Per-feature ranking (1 = try first)

### 4.1 Lighting, materials, CAD look
1. Extend ours: `RoomEnvironment` via PMREM (one call, no asset file) + MeshStandardMaterial with sane metalness/roughness, ACES or
   Neutral tone mapping, one soft shadow-catcher plane. Cheapest, biggest visual gain. Source: three.js addons (opened docs index only; API is standard, verify in a spike).
2. Edge lines: `EdgesGeometry` (threshold angle ~30 deg) as `LineSegments` per mesh, built once at load, merged per part. Cheap and gives the CAD look; no post-processing.
3. Post: EffectComposer + GTAOPass (ambient occlusion) + OutlinePass for the selected set only. Costs two extra scene renders; OutlinePass only outlines `selectedObjects` (general knowledge; docs fetch returned nav only). Make AO a toggle, off on weak GPUs; this PC is memory-tight.
4. three-cad-viewer Studio mode gives all of this ready-made, but only inside its own scene.
5. xeokit SAO/edges: good, but AGPL and a different scene graph.

### 4.2 Part tree, selection, highlight, isolate/hide
1. Extend ours: a DOM tree built from the GLB node hierarchy (we already name nodes by component id), with eye toggle, isolate (hide others), tree hover highlights, click selects both ways. ~150 lines. Matches existing `highlight()` and `onPick`.
2. three-cad-viewer: tree with hover-highlight of all faces under a node, state 1/0 for shown/hidden, pick by id, `setSelection`, `setAgentHighlight` (second highlight colour, handy for FAIL pairs). Best reference UX.
3. APS: isolate/hide/show-all/ghost events; reference for the verbs to offer (Isolate, Hide, Show all, Ghost others).

### 4.3 Section planes, x-ray, see inside (must-have 3)
Needs three things: ghost skin, section plane, hide/isolate with internal parts pickable.
1. Extend ours with three.js native clipping: `renderer.localClippingEnabled = true`, `material.clippingPlanes = [plane]` shared by all materials; a slider or a TransformControls gizmo on the plane. Caps via the three.js stencil recipe (back-face increment, front-face decrement, draw cap where stencil nonzero) needs closed solids; our GLB parts may not all be watertight (wires, thin skins), so make caps optional and default to uncapped (plain cut + back faces visible, which is how we already render `DoubleSide`).
2. Skin x-ray: "ghost" = `transparent`, opacity 0.12-0.25, `depthWrite:false`, applied to chosen parts (skin, wing, fuselage) by group; our current dim-others-to-0.28 is the seed. Order problem: sorting of many transparent meshes causes flicker; use `renderOrder` (skin last) and only ghost the skin set.
3. Picking inside: raycast must skip ghosted and hidden parts (three-cad-viewer fixed exactly this bug in Studio, v4.2.0: "hidden objects ignored in raycasting"). Add a "pick through skin" rule: ghosted parts are not pickable by default; Alt-click cycles hits front to back.
4. three-cad-viewer clip tab: three planes with sliders, hatched and outlined caps (v5.1.0), caps only for planes that actually cut a solid (v5.0.0), caps outline skipped while camera moves. Best reference behaviour.
5. xeokit SectionPlanesPlugin: gizmo + overview canvas, multiple planes, flip; no cap detail found. Reference only (AGPL).
Cheapest test: load concept-a, enable one plane at x=0, ghost skin; battery/ESC/servos must be visible and clickable.

### 4.4 Explode (must-have 1)
1. Extend ours: per-part displacement along a direction from the assembly centre (radial) or per assembly level (hierarchy), driven by one slider. Store each node's rest position; offset = (partCentre - assemblyCentre) * level_factor * t. Needs the assembly level per node: use GLB hierarchy depth, or PDL's group/parent field if available (to confirm with `plane` fields; flagged, not checked). Animate by lerp; reset on t=0.
2. APS: two strategies, `hierarchy` (default) and `radial`: offer both; matches Tristan's "by assembly level". Opened reference.
3. three-cad-viewer: explode tool exists (key `x`), notes say it composes with animation and flags captured views as "displaced: explode". Details of its algorithm not found on pages opened.
Gotcha: explode and mechanism animation (physics.js) and drag-move all write node transforms. Use one transform layer: rest -> design-edit offset -> explode offset -> mechanism transform, never overwrite `node.position` directly. three-cad-viewer hit a bug of exactly this kind (v4.3.8, explode vs measurement tools).

### 4.5 Drag to move parts (must-have 2)
1. Extend ours with `TransformControls` (translate first, rotate second): `attach(node)`, add `getHelper()` to scene, disable OrbitControls on `dragging-changed`, `setTranslationSnap` (e.g. 1 mm = 0.001 in scene metres) for numbers that match PDL. Read-only by default: a "Move" mode toggle; on drag store the delta in mm in body z-up coordinates (use the same `mmToScene` axes, inverse for write-back); show a floating Apply / Revert bar. Apply calls `plane design set` through the studio.py endpoint, never writes code or GLB; Revert restores rest. Source: threejs.org TransformControls docs (opened). Note: `dragging-changed` is used in the examples but not in the docs event table; verify against 0.160 source in the spike.
2. Constrain: axis lock keys (X/Y/Z), numeric entry in the inspector, optional min/max bounds (the docs list `minX`..`maxZ`).
3. Pick for dragging should go via the same pick path as selection, with the mesh's component node (not the child mesh) as target.
4. three-cad-viewer: no part-move tool seen on pages opened. xeokit/APS: none found. This feature is ours to build; no benchmark to copy except Blender-style gizmo from TransformControls itself.
Risk: Apply writes to PDL; parts placed by formulas or inherited from a parent need `design set` on the right field. The UI must show which PDL field will change before Apply.

### 4.6 Measurement
1. three-cad-viewer has distance and property tools (bounding-aware; ids by key D, P). Needs B-rep topology for vertex/edge/face filters, which our GLB lacks, so only the point-to-point and mesh-measure side applies.
2. Extend ours: two-click point-to-point with raycast hit points, snap to vertices (nearest vertex of the hit triangle), draw line + CSS2D label in mm. three-mesh-bvh `distancecast`/`edgeIntersect` examples (listed) suit snapping.
3. xeokit DistanceMeasurementsPlugin: reference UX only.

### 4.7 Standard views, view cube, camera, fit-to-selection
1. Extend ours: preset buttons (iso, front, top, side, back) animating camera with a short tween; fit-to-selection by `Box3` of selection and distance from FOV; double-click on part frames it; OrbitControls `enableDamping = true` needs a render loop while moving (adapt `dirty`). ViewCube: small separate scene with a cube and a second camera (the three.js `ViewHelper` addon is a gizmo, not cube; a CSS 3D cube is the simplest, ~80 lines).
2. three-cad-viewer: cursor-pivot rotation and zoom to cursor (v5.2.0), ortho toggle. Worth copying the behaviour: pivot around the point under the cursor.
3. xeokit NavCubePlugin and APS ViewCube: references.
Ortho toggle: needed for sections and measuring; swap camera type while preserving target.

### 4.8 Mechanism animation timeline
1. Extend ours: generalise `physics.js` into a timeline bar under the main viewport (play/pause/scrub, speed, loop, mechanism select) and have it feed the transform layer of 4.4. Keep the replay data format (4x4 per step per node).
2. three-cad-viewer animation: tracks with play/stop; useful reference for a timeline, but a different data model (position/quaternion tracks).
3. three.js `AnimationMixer` + clips: possible but our data is already stepwise and precomputed (T6 sweep); not needed.

### 4.9 Overlay analysis results (colour by status or value)
1. Extend ours: a "Colour by" dropdown: none / check status (FAIL red, WARN amber, PASS green, using `data.pair` and any component ids in scorecard rows) / mass per part (scale) / type. Clicking a scorecard row selects, ghosts the rest, frames the parts. Legend panel with scale. Use per-part material `color` override, remembered rest colour.
2. three-cad-viewer `setAgentHighlight(paths)` shows the pattern: a second highlight colour for "flagged by a check" alongside user selection. Copy the idea.
3. Badges on tree rows (red dot when a FAIL concerns the part): high value, very cheap.
Needs: check results must carry component ids (today only `data.pair`). Ask for a `data.parts` list in check output; flagged as a PDL/`plane` request.

### 4.10 Performance for 100-300 meshes
1. Don't optimise first. 300 meshes is ~300 draw calls: fine on a laptop GPU. Measure on concept-a (`renderer.info.render.calls`, triangles) before changing anything.
2. three-mesh-bvh: `acceleratedRaycast` + `computeBoundsTree` per geometry, `firstHitOnly = true`. Add only if pick latency is visible. MIT, ESM.
3. Merge static geometry per material, or `BatchedMesh` (instanced draw with per-part visibility and colour), only if draw calls hurt; BatchedMesh breaks per-mesh material tricks (clipping caps, ghost) so it is the last resort.
4. One renderer per viewport (4 WebGL contexts) is the real memory cost on this PC: share one renderer or lazily create compare/physics viewports. Also dispose geometry and textures on design switch (app.js `clear()` does not dispose).
5. Frame-on-demand (already there) keep; post-processing makes idle frames cost more, so keep `dirty` gating.

### 4.11 UI layout patterns
Observed in opened sources: three-cad-viewer: left tree panel with tabs (Tree, Clip, Material, Studio, Zebra), top toolbar of tool icons, bottom info/slider bar, light/dark theme, pinning. xeokit/APS: left model tree, right properties/inspector, bottom or top toolbars, NavCube top-right. Babylon Inspector: dockable explorer and property panes.
Recommendation (ranked):
1. Three-pane layout: left (design list + part tree, collapsible), centre viewport with floating toolbar (select/move/measure/section/explode/views) and bottom timeline, right inspector (selected part: type, mass, CG, PDL fields, its check rows) over the scorecard tabs (Checks, BOM, Edit, Compare).
2. Dark theme default for the viewer area, CSS variables already used (`--vp-bg`); add a theme toggle, keep prefers-color-scheme.
3. Keep vanilla JS and a small `h()` helper; split viewer into ES modules (`viewer/vp/*.js`: scene, materials, tree, clip, explode, gizmo, views, timeline). No framework: it would force a build step with little gain.

## 5. Adopt vs extend: overall direction

### Option A: adopt three-cad-viewer as the viewer
Pros: MIT, active (5.2.1, three r187), most CAD features done and tested (tree, clip with caps, explode, measure, ortho, Studio PBR, animation, picking).
Cons, serious for us:
- Data model is its own tessellated JSON (`Shapes` tree, `vertices/triangles/normals/edges`, `loc` per node). A GLB to that converter is feasible (the Data Format page suggests it) but needs `triangles_per_face`, and we have no B-rep edges (would have to compute edges from triangles).
- 1.5 MB minified + 123 KB CSS, and a second three.js copy (r187 inside vs our 0.160); mixing our Raycaster/TransformControls with its scene is not supported; its scene is internal.
- No drag-move-part tool found; our CG marker, mass overlay, check-row highlight, physics mechanism replay and the `Viewport` API (highlight by id, `onPick`) all live in our scene graph and would be redone through its API (`setAgentHighlight`, `setSelection`, `captureView`), which is smaller and tuned to CadQuery workflows.
- Four viewports (compare, physics) means four Viewer instances at 1.5 MB scripts each loaded once but heavy GPU use.
- Its UI would clash with a custom Studio layout (own Display class with toolbar and tree), so the "cleaner layout" goal is constrained by its chrome.

### Option B (recommended): extend our three.js app, borrow three-cad-viewer's behaviours
- Stay on vanilla ESM from CDN; bump three from 0.160 to a current pin (r17x or later; TransformControls API changed at `getHelper()`; spike the upgrade first since 0.160 is old; confirm the exact version). Add addons already in the three package (EffectComposer, GTAOPass, OutlinePass, TransformControls, RoomEnvironment) via the import map. No build step needed.
- Add `three-mesh-bvh` (MIT) only after measuring.
- Re-implement in small modules, adapting ideas (not code) from three-cad-viewer (cap hatch/outline, cursor pivot, tree hover, agent highlight, state per part), APS (explode strategies, isolate/ghost verbs), xeokit (section plane gizmo, NavCube) (AGPL: no code).
- A build step is NOT clearly worth it: three, addons and three-mesh-bvh all ship ESM and import maps cover it. Revisit only if we want to vendor and tree-shake for the offline/public build (then vendor files into `viewer/vendor/` instead of CDN, which also removes the CDN dependency for demo day).

### Option C: embed three-cad-viewer only for the "Inspect" mode
A hedge: one extra mode that shows a design in three-cad-viewer through a GLB converter, for its clip caps and measure. Not recommended now: duplicates the scene, doubles maintenance, and Dec 2 is close.

## 6. Order by value per effort (suggestion for Step 1 of the unit)

1. Lighting/materials + edges + tone mapping; three version bump spike (visible win, 1 day).
2. Part tree + hover/isolate/hide + ghost skin (see inside, must-have 3 part 1).
3. Section plane (uncapped, then optional caps) with gizmo (must-have 3 part 2).
4. Standard views, fit-to-selection, damping, cursor pivot.
5. Transform layer + explode slider (must-have 1).
6. TransformControls move with Apply/Revert (must-have 2): after 5, because it shares the transform layer.
7. Colour-by status/mass, FAIL badges on tree, scorecard row to part.
8. Timeline from physics.js; measurement; layout overhaul (can overlap with 2).
9. BVH/merging only if measurements demand it.

## 7. Risks

- three.js upgrade from 0.160: addons paths and APIs (`getHelper`, colour management, `useLegacyLights` gone) change; one spike, visually diff screenshots.
- Four WebGL contexts and post-processing on a memory-tight PC; share one renderer or render on demand.
- Transparent sorting with many ghosted parts; limit ghosting to a skin group.
- Section caps need watertight solids; GLB parts (wires, thin skins) are not; default to uncapped.
- Apply writes back to PDL: wrong field, parametric parts, units (mm vs scene metres, z-up vs y-up). Preview the exact `plane design set` command in the UI and require confirmation; test with a round trip.
- Check rows lack component ids except `pair`; colour-by-status needs a `data.parts` convention (PDL/`plane` request).
- Playwright click-path tests: canvas picking is hard to assert; expose a test hook (e.g. `window.planeViewer.pickAt(id)` and a `data-selected` attribute on the tree) rather than pixel clicks.
- Licence: do not copy xeokit (AGPLv3). three-cad-viewer, three-mesh-bvh, Online3DViewer, three.js are MIT: ideas free, code adapted and recorded in PROVENANCE.md.

## 8. What not to do

- No framework, no bundler, no TypeScript migration for this unit.
- Do not adopt xeokit (AGPL) or APS (cloud, token) or model-viewer (no CAD tools) or Babylon (second engine).
- Do not move parts by editing the GLB or any code; only `plane design set` through Apply.
- Do not write node `position` from three places; one transform layer.
- Do not add SSAO/outline everywhere by default; toggle, and off for compare/physics viewports.
- Do not optimise with BatchedMesh or merging before measuring on concept-a.
- Do not rely on sources I could not open: Onshape, Fusion web, FreeCAD web, Shapr3D, MuJoCo web, OpenVSP viewer were not read; xeokit x-ray/explode and Online3DViewer feature set are unverified; three.js OutlinePass/GTAOPass/stencil-cap pages returned only nav text, so those API notes come from general knowledge and must be checked in the spike.

## 9. Sources opened (2026-11-25)

- https://github.com/bernhard-42/three-cad-viewer (README page, package.json 5.2.1, Changes.md, Readme.md, Data Format.md)
- https://data.jsdelivr.com/v1/package/npm/three-cad-viewer@5.2.1/flat (file sizes)
- https://github.com/xeokit/xeokit-sdk ; https://xeokit.github.io/xeokit-sdk/docs/ ; .../SectionPlanesPlugin
- https://github.com/gkjohnson/three-mesh-bvh and /tree/master/example
- https://github.com/kovacsv/Online3DViewer
- https://threejs.org/docs/pages/TransformControls.html ; https://threejs.org/docs and /examples (nav only for OutlinePass, clipping_stencil)
- https://modelviewer.dev/
- https://aps.autodesk.com/en/docs/viewer/v7/reference/Viewing/
- https://doc.babylonjs.com/toolsAndResources/inspector (brief)
- Repo: viewer/app.js, viewer/modes/designs.js, viewer/modes/physics.js; plan U19.1 scope.
- New sources not yet added with `plane research new` (recon cannot edit other files this task); conductor to register.
