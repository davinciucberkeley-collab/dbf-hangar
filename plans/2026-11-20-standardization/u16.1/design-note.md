# U16.1 design note (W34-A): from shapes to a mechanical model

Date 2026-11-25. Unit U16.1 (was U13.12; D85, D87, idea I2). Inputs: the plan unit, `u16.1/recon.md` (W34-X),
the repo at 828faa0, a400m-rc from closed PR #8 and c172-rc from closed PR #9 (scratch copies, read-only), the
parked branch std/u4.25-pockets (U16.2). Bar (Tristan, D87): the output must be "genuinely close to the real deal
(real links, joints, elements, wires, etc)".

## 0. Intent (what is true when U16.1 is done)

On one showcase design, in Studio: each control surface moves on its hinge, driven by a servo arm whose pushrod stays
pinned to the horn through the whole throw and never clips; wheels are separate parts that spin on their axles and
every leg visibly meets the airframe; servos sit in bays cut in the wing or fuselage with the arm through the skin;
wires run as visible tubes between parts; hinges and rod ends are visible. The same design exports to an MJCF in
which driving the servo moves the surface. Other designs stay byte-identical unless they opt in.

## 1. Gap list against the bar (evidence)

| # | Gap | Evidence |
|---|---|---|
| G1 | The pushrod is not a link: it swings rigidly with the servo arm and leaves the horn | `pose_transforms` (core/hangar/geometry.py:229) moves everything downstream of a joint rigidly; the rod is downstream of the arm (`kinematic_link`), the pin downstream of the hinge. Measured change of the rod-end-to-pin distance over each sweep: A400M 11.0 / 21.3 / 12.4 / 12.4 mm (ele, rud, ail r/l); C172 13.6 / 13.6 / 23.8 / 15.4 mm (ail r/l, ele, rud). Studio Physics replays exactly these transforms (core/hangar/index.py:51-57). |
| G2 | The follower angle is declared, not computed | `simulate_mechanism` (core/hangar/gates/mechanisms.py:35): follower = clamp(declared ratio x input). Only `T6.ratio` compares with geometry, small-angle only. |
| G3 | Rod and horn clash is never checked | a400m validate: `T6.link.* WARN not checked (pinned by declared link)` x4; `T1.kinematic_link SKIP ... linkage path not modelled` on every hinge sweep. |
| G4 | Wheels are not parts and cannot roll | `landing_gear` (core/hangar/geom/airframe.py:80-102) unions legs, axles and wheels into ONE mesh (1 part on both designs); no axle joint. Contact is checked per component, so one leg touching hides a leg that does not (Tristan: front wheel not attached). A400M uses `wheel_shape: disc` (plain cylinder). |
| G5 | Servos sit on the skin, not in bays | Fraction of each servo volume inside its host: A400M servo-ele 0.09, servo-rud 0.29, servo-r/l 0.10; C172 wing servos 0.26 (iso render: boxes on top of wing and stab). C172 tail servos are 1.00 inside a SOLID fuselage loft: buried and invisible. Cavities (schema 0.3, geometry.py:91) work on generated parts but nothing uses them for servos. |
| G6 | Parts are envelopes | Servo = `plate` box 22.8 x 12.2 x 28.5 (knowledge/parts/towerpro-mg90s); no ears, no output spline, no named output frame, so every arm pivot is a hand-typed coordinate. Props render as discs. The CAD overlay helps on team PCs only (docs/cad-overlay.md), not in CI or on stage. |
| G7 | Linkages are hand-coded per design | A400M: 4 x (servo, arm, rod, horn, pin) = 20 components, 24 attachments with literal coordinates (e.g. horn-ele [1665, 66, 379.05]). A wing change (U15.1) moves the surface, not the linkage. No op generates a linkage. |
| G8 | Wires do not exist | `wiring.harnesses` empty on both designs. Schema `harness` = from/to/route as component ids, no points, no diameter; T7.wiring tests straight CG-to-CG segments (core/hangar/gates/integration.py:15). No geometry in GLB. |
| G9 | Control surfaces have no hinge detail and clip on change | Surfaces are a flat cut at hinge_frac (geom/wing.py:134, geom/tails.py:23): no gap, bevel or knuckles. A400M at span 1800: 8 new T1 hinge-overlap FAILs (U15.1 scope). |
| G10 | MJCF has no joints | `sim._build` (core/hangar/sim.py:59): every component a free body, every attachment (articulated too) a `<weld>`. Nothing in the MJCF can move a surface. |
| G11 | No fasteners, clevises, connectors, wheels in the library | knowledge/parts has none (the categories exist in geom/library.py). |

Not a gap: the joint data model. Articulation (revolute, pivot, axis, range), `mechanisms[].link`, the T1 loop rule
and T6 already carry what a four-bar needs (recon section 1). What is missing is computation, generation, geometry.

## 2. Build steps (one builder brief each, in this order)

Precondition S0 (designs-only): pick ONE showcase design and land it on main through a designs-only PR, so Studio
(scans `designs/*/plane.yaml` only, core/hangar/studio.py:87) can show each step. Default: c172-rc (conventional,
four linkages, tricycle gear, fewer parts than A400M). Each step ends with a separate designs-only commit that opts
the showcase in with `plane design set` (no core and designs in one PR).

**S1 Four-bar linkage solve; Studio shows the rod pinned** [hard]
- What: `mechanisms[].kinematics: four_bar` (default `ratio` = today). Per input angle, solve the follower angle t so
  that the distance from arm_tip(input) to pin(t) equals the rod length at rest (1-D root find on t inside the hinge
  range, branch continuous from rest; works for non-planar 3-D layouts). Rod pose = rigid transform taking the rest
  (start, end) to (arm tip, pin), minimum rotation. No root, or a transmission angle under a limit, is a jam (limit
  in gate-thresholds.yaml with a source or `pending`). T6.link then checks rod vs horn, surface and skin at every
  step instead of skipping; T6.ratio unchanged.
- Files: schema/plane.schema.json, core/hangar/migrate.py (1.3), core/hangar/gates/mechanisms.py,
  core/hangar/geometry.py (pose with per-component override transforms), core/hangar/index.py,
  docs/pdl/reference.md, docs/mechanisms.md, tests (tests/fixtures/mechanism-recipe opted in).
- Acceptance: fixture with `four_bar`: rod-end-to-pin distance constant to 1e-6 mm over the sweep; follower 0 at
  input 0; small-angle slope within mechanism_ratio_tol of the declared ratio; same fixture without the field gives
  byte-identical T6 rows and mechanisms JSON. Scratch c172-rc elevator: gap change 23.8 mm -> 0.
- Studio: Physics, elevator-drive, Play: the rod follows the arm tip and stays on the horn pin; the readout is the
  solved angle. No viewer change (viewer/modes/physics.js applies whatever per-node matrices the server sends).

**S2 Wheels as separate parts on axles** [hard]
- What: `landing_gear.wheels: separate` (default `merged` = today) emits legs, axle stubs and nose/tail fork only;
  new `wheel` generator (tyre profile from airframe.py, hub, bore on the axle). Wheels are components attached to the
  gear with `articulation.type: continuous` (PDL 1.3; no range). T1: no pose sweep for continuous joints
  (axisymmetric); each wheel gets its own contact row on its axle; T6.undriven skips continuous joints; index.py adds
  a spin sweep for undriven continuous joints even when `mechanisms` exists.
- Files: core/hangar/geom/airframe.py, schema, core/hangar/checks.py (_configurations, _articulation_checks),
  core/hangar/gates/mechanisms.py, core/hangar/index.py, docs, tests.
- Acceptance: `merged` byte-identical on every design; `separate` on scratch c172: 3 wheel components, each
  T1.attachment_contact PASS on its axle; removing the nose leg makes the nose wheel FAIL contact.
- Studio: wheels are separate nodes; Physics lists spin-(wheel id) and the wheels turn on their axles.

**S3 Bays: servos in the structure, output through the skin** [hard]
- What: library part.yaml gains optional `frames` (`output: {point, axis}`, `mount_face`) for servos (library
  schema, not PDL). Op `plane design place DESIGN COMPONENT --in HOST --at STATION [--face lower]` puts the part
  inside the host, ears flush with the chosen skin, and writes a box `cavity` on the host (part dims + clearance from
  standards, source or `pending`). The arm pivot reads the output frame. Uses existing cavities: no PDL change.
- Files: core/hangar/geom/library.py, new op in core/hangar/ops/ (CLI and MCP via the op registry), servo entries in
  knowledge/parts (frames), docs/team-guide.md, tests.
- Acceptance: scratch c172 wing servos at least 0.9 inside the uncut wing envelope; T1 overlap and pocket PASS after
  the cut; mass_model hosts report the removed volume; mass_g hosts unchanged.
- Studio: servo in a recess with the arm below the lower skin; wing translucent (S9) to see inside.

**S4 Linkage generator op** [hard]
- What: `plane design add-linkage DESIGN --servo ID --hinge ATTACHMENT --station S` writes arm, rod, horn and pin
  components, their attachments and the `four_bar` mechanism entry from the hinge line and the servo output frame
  (S3). Builder rules from recon E (arm perpendicular to rod at neutral, horn hole over the hinge line) are defaults,
  never thresholds. Idempotent: re-running after a wing change (U15.1) rewrites the same ids.
- Files: core/hangar/ops/ (new), docs/mechanisms.md (the recipe becomes "run add-linkage"), tests.
- Acceptance: scratch copy with its linkages deleted: four add-linkage calls give T6 PASS on all four, no T1 FAIL;
  a second run is an empty diff.
- Studio: as S1 on all four surfaces, generated instead of hand-typed.

**S5 Pocket clearance for imported moving parts = U16.2** [hard; beside S1-S4, after U15.1 merges]
- See section 7: keep the swept-pose UNION approach (00e8c9e), drop the convex-hull commit (3204340).

**S6 Hinge geometry that does not clip** [hard; after U15.1 and U16.2 merge, same files]
- What: opt-in params on the moving part of `wing_panel` (elevon) and `tail_surfaces` (elevator, rudder):
  `hinge_gap` and `hinge_style: bevel | round` (bevelled or rounded leading edge sized from the articulation range so
  the swept surface clears the fixed part) plus hinge knuckles at N stations (part of the surface mesh).
- Files: core/hangar/geom/wing.py, core/hangar/geom/tails.py, docs, tests.
- Acceptance: scratch c172 full-range T1 pose sweep PASS without `embed_ok` on hinges; defaults byte-identical.
- Studio: a hinge gap and knuckles along the hinge line; surfaces sweep without clipping.

**S7 MJCF kinematic export** [hard]
- What: new format `plane design export --format mjcf-kinematic` (`mjcf` and the drop test stay byte-identical): body
  tree from `root`; rigid attachments merge the child geoms into the parent body (no weld); articulated attachments
  become hinge joints with range (continuous: no range); servo arms get a position actuator; the rod hangs from the
  arm on a ball joint and closes on the horn pin with an equality `connect` (soft solref, recon D); wheels collide
  with the ground.
- Files: core/hangar/sim.py (new builder beside `_build`), core/hangar/ops/design.py, core/hangar/cli.py, docs, tests.
- Acceptance: fixture loads, servo driven to +20 deg settles with the surface within 1 deg of the S1 solve (test
  tolerance, not a gate threshold); no NaN; `mjcf` exports of all designs unchanged.
- Seen with `python -m mujoco.viewer` on the exported file (Studio stays the analytic replay).

**S8 Wires as routed geometry** [hard]
- What: PDL 1.3 `harness.from_port`, `to_port` (names from part.yaml `ports`), `waypoints` (vec3 list),
  `diameter_mm` (else from gauge_awg). Tube along a Catmull-Rom curve from port through waypoints to port, emitted
  as GLB nodes in a `wiring` group (visual only, section 6); T7 reports length and checks the polyline when
  waypoints exist (else as today). Ports added to servo, ESC, receiver, battery and motor parts.
- Files: schema, core/hangar/gates/integration.py, core/hangar/export.py, core/hangar/geom/library.py,
  knowledge/parts, docs, tests.
- Acceptance: scratch c172 with 6 harnesses: GLB has 6 wire nodes; T7 PASS; designs without waypoints identical.
- Studio: wires from receiver to each servo, ESC to motor and battery.

**S9 Visual detail and seeing inside** [easy each; one brief per item]
- Clevis at the rod ends and Z-bend at the arm (rod params); screw heads at bolted attachments with a `connection`;
  `fuselage_loft.wall` (hollow shell, opt-in, real geometry) and a Studio x-ray toggle (viewer only) so internal
  servos, battery and wires show.

Tristan looks after S2 (first visible pass: linkages pinned, wheels rolling) and again after S4, S6 and S8 (plan
step 4). Rehearsals resume only on his word (D87).

## 3. Schema changes (PDL 1.3) and migration

One minor version, opened by S1, extended by S2 and S8 (the 1.0 precedent: "1.0 also adds"):
- `mechanism.kinematics`: `ratio` (default) | `four_bar` (S1).
- `attachment.articulation.type`: `revolute` | `continuous`; `range_deg` required only for revolute (S2).
- `harness.from_port`, `harness.to_port`, `harness.waypoints`, `harness.diameter_mm` (S8).
- Not PDL: `landing_gear.wheels`, the `wheel` generator, `hinge_gap`/`hinge_style`, `fuselage_loft.wall` and the
  U16.2 `cut_poses` are generator params (registry ParamSpec); part.yaml `frames` and `ports` are library schema
  (library.py part_errors).
Migration: all optional; migrate.py gains 1.3 (version line only, as for 1.2). Files 0.1-1.2 validate unchanged. A
file below 1.3 that uses a 1.3 field fails T0 (existing `_below` pattern, core/hangar/checks.py:41).

## 4. What keeps existing designs byte-identical

- Every new behaviour hangs on an opt-in value whose default is the current code path: no `kinematics`,
  `wheels: merged`, `hinge_gap: 0` and no `hinge_style`, no `cut_poses`, no `waypoints`, no `wall`; format `mjcf`
  untouched (new format beside it). The Studio x-ray is viewer state only.
- Brief rule for every step: sha256 before/after of the glb, stl and mjcf exports, the index.py mechanisms JSON and
  `validate --json` for every design on main and the fixtures; tests/test_overlay_baselines.py and baselines green;
  no baseline refresh in a core PR.
- U15.1 already promises the same for control surfaces; S6 adds params and must not change its defaults.

## 5. Cut or defer

- Cut: build123d, CadQuery, FreeCAD or OpenVSP as dependencies (recon 5); physical cable simulation; relaxing the T1
  loop rule; thresholds from forum advice; the convex-hull pocket variant (3204340).
- Defer past the D87 judgement: nose-wheel steering coupled to the rudder, retracts, multi-link flaps, differential
  aileron tuning, live MuJoCo inside Studio (R11 interactive physics stays post-v1.0), a wire bend-radius gate
  (report only, `pending`), fastener mass bookkeeping, a full parametric servo CAD (the overlay covers looks locally).
- Regenerating A400M with all of this: after the showcase passes (S4 makes it a few calls).

## 6. Risks

- MuJoCo loop closure: hinge (servo) + hinge (surface) + `connect` over-constrains a 3-D four-bar when the axes are
  not exactly parallel (jitter, constraint fight). Mitigation in S7: ball joint at the arm end (the `connect` is
  itself a ball at the pin), soft solref (recon D: about 0.004-0.005, solref[0] at least 2 x timestep), small damping
  on the rod roll; prove on the fixture first. The analytic S1 solve stays the reference.
- Studio posing rods per frame: solved server-side; physics.js already applies arbitrary per-node matrices but needs
  each node at the rest origin (`position.lengthSq() === 0`); generated rods sit at [0, 0, 0]. A branch flip near
  toggle must be reported as a jam, never drawn as a jump.
- Visual-only geometry vs mass and T1: wires, clevises and screw heads as components would add mass, T1 overlap FAILs
  (wires through ribs), floating-part rows and MJCF bodies. Keep them out of `components`: derived at export only,
  GLB metadata `visual_only: true`; their mass stays in the existing point_mass allowances. Hinge knuckles inside the
  surface mesh are real printed geometry and do count.
- Bays change mass for `mass_model` hosts and may cut spars: S3 reports the volume removed and runs T1.pocket.
- Four-bar dead points: no root inside the hinge range is a T6 FAIL with the input angle, never a silent clamp.
- Part count: four linkages add 16-20 components and T1 pair checks grow; re-time against the U15.3 numbers. U16.2
  already showed tier-1 budget pressure (54-63 s with the union).
- Scope creep: every step opts in on one design; if a step needs a second design to look right, stop and ask.

## 7. U16.2 (pose-aware pockets, branch std/u4.25-pockets): keep, replace or both

Both, for different parts. U16.2 serves IMPORTED moving parts listed in a wing core `cut_files` (concept-a-param: a
hot-wire foam core with STL elevons, balance horns and hinge parts). The real build does cut the swept envelope out
of the foam, so subtracting the swept poses is the true geometry, not a workaround; generated hinge geometry (S6)
cannot replace it because those parts are meshes, not generator output. S6 serves GENERATED surfaces, where the
surface and its parent can be shaped (gap, bevel, knuckles) so nothing needs cutting.
Keep the union-of-poses version (00e8c9e: all 14 swept-pose rows gone, tier-1 54-63 s, inside the D73 relaxed budget
of about 70 s). Drop the convex-hull retry (3204340): 98-111 s and a -16.4 % planform FAIL because the balance-horn
hull cuts a wedge out of the core. Order: W34-B2 refreshes the branch onto main and re-times (step 1b); if tier-1
stays within D73, review and merge it as S5, after U15.1 (both edit geom/wing.py) and before S6 (same file). If it
misses D73 again, it waits for U15.3 (start-up time) rather than another geometry variant.

## 8. How U15.1 (was U13.9) fits

U15.1 makes control surfaces derive their planform from the parent wing. That fixes the surface, not what hangs on
it: the articulation pivot and axis and the servo, horn and rod coordinates stay literal and go stale on a span
change (T1.articulation catches the pivot; nothing catches a horn left in the air). So S4 add-linkage is the
re-derivation for linkages (re-run after `design set`), and the U15.1 brief should either derive the hinge
`pivot`/`axis` from the same parent or say it is out of scope so S4 owns it. U16.2 and S6 edit the same generators
as U15.1 and start from its merged code.

## 9. Decisions for the human

1. Showcase design: c172-rc (default) or a400m-rc; it must land on main (designs-only PR) for Studio to show it.
2. Is S7 (MJCF) needed before the D87 judgement, or may it follow (Studio is what Tristan will look at)?
