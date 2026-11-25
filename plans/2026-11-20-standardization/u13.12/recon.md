# U13.12 recon (W34-X): how others model aircraft CAD with real mechanisms

Date: 2026-11-25. Author: recon. Only sources I opened are cited; all "checked" dates are 2026-11-25.

## 1. Question

Which known approach should dbf-hangar adopt, adapt or ignore so generated RC aircraft carry real mechanical content: hinges, servo -> horn -> pushrod -> control-horn linkages that move without clipping, wheels on axles, parts in bays, routed wires, visible fasteners. Constraints: Python, trimesh meshes, YAML/PDL data, MuJoCo MJCF export, imports adapted not copied (PROVENANCE.md).

What the repo already has (skimmed only): `docs/mechanisms.md` recipe (servo arm plate, pushrod strut, horn plate, hinge as an attachment with `articulation`, `kinematic_link: true` on the driver end, a follower `pin` in the horn, a `mechanisms[]` entry; T6 checks the small-angle ratio). The recipe deliberately leaves the rod unattached at the horn end because T1 refuses articulated joints in an attachment loop. `core/hangar/sim.py` builds MJCF and closes attachments with `<weld>` equalities (around line 117). Generators live in `core/hangar/geom/` (generators.py, tails.py, wing.py, powerplant.py, library.py). So the joint data model exists; what is thin is the generator side that fills it with real parts.

## 2. Approaches

### A. build123d (and CadQuery) joints and assemblies
- Opened: https://build123d.readthedocs.io/en/stable/joints.html ; https://github.com/gumyr/build123d (checked 11-25).
- Models: BREP solids with named Joint objects on each part. Types: RigidJoint, RevoluteJoint (angular_range), LinearJoint (linear_range), CylindricalJoint, BallJoint. Pairing is typed (Revolute pairs with Rigid; Linear with Rigid or Revolute).
- Data model: joint = named frame (location + axis + range) on a part. `connect_to` places the other part once at a given angle/position inside the range, else ValueError. It is a one-shot placement, not a live binding. The page says nothing about loops or a solver.
- Licence: Apache-2.0 (README). Derived from parts of CadQuery, now independent. `pip install build123d`; OpenCascade BREP (heavy, not trimesh).
- Adapt: each part declares named joint frames with type and range; a hinge is "Revolute on A, Rigid on B". PDL attachments with `articulation` already do this. Useful borrow: range validation and one "pose at q" function. Do not adopt the library.
- RC-specific CadQuery work: none found with hinges, pushrods or servos. cq-uav (https://github.com/nomad-vagabond/cq-uav, Apache-2.0, opened) models only a rectangular wing console (three-chamber box, shaper, shell) with mass and stress estimates; no control surfaces. Search also surfaced vibe-cading and Parametric-Drone-Design-Software; I did not open them, so no claim about them.

### B. OpenVSP
- Opened: https://github.com/OpenVSP/OpenVSP ; https://openvsp.org/api_docs/latest/ ; https://openvsp.org/wiki/doku.php?id=sub_surface (checked 11-25). Repo note `knowledge/sources/schema-openvsp-api-geom.md` exists (not re-opened).
- Models: parametric aircraft outer geometry for analysis. API page lists a Sub-Surface group and a VSPAERO Control Surface Group. The wiki page is a stub that names sub-surface types (control surface, line, rectangle; chord fractions and span). I could not read more detail. README mentions STEP and IGES via libraries; STL not confirmed.
- Licence: NASA Open Source Agreement 1.3. Python: SWIG bindings built from source, must match the compiled Python version; no pip route on the pages I read.
- Not modelled (as far as opened): servos, linkages, wheels, wires. Outer mold line and aero tool.
- Adapt: control surface as a sub-surface by chord-fraction and span fractions (the repo likely has this in `surfaces.py`/`wing.py`). Do not depend on it.

### C. FreeCAD Assembly workbench (1.0) and Assembly3
- Opened: https://github.com/FreeCAD/FreeCAD (LGPL-2.1; page says nothing on Assembly) ; https://github.com/realthunder/FreeCAD_assembly3 (GPL-3.0, needs py_slvs solver). Wiki Assembly page blocked (bot wall) and the deepwiki page returned 429. The joint list and the OndselSolver/MbD solver come only from a web search summary (snippets), so treat as unverified: Fixed, Revolute, Cylindrical, Slider, Ball, Distance, Parallel, Perpendicular, Angle, RackPinion, Screw, Gears, Belt.
- Models: parts as links with joints between named references; a constraint solver moves parts, so closed chains are solved.
- Licence: LGPL-2.1 / GPL-3.0 (copyleft; do not copy code). Python: embedded FreeCAD Python; headless use unverified; not installable here.
- Adapt: joint vocabulary only (it matches build123d and MJCF). Do not adopt.

### D. MuJoCo / MJCF practice for closed linkages
- Opened: https://mujoco.readthedocs.io/en/stable/XMLreference.html (equality section only, first 100k chars) ; https://mujoco.readthedocs.io/en/stable/modeling.html (partial) ; https://robolaweb.gitbook.io/robolaweb-docs/basic-concept/equality-overview (third party) (checked 11-25).
- Confirmed: `equality/connect` (body1, body2, anchor or site1/site2, solref, solimp) imposes point coincidence; `equality/weld` adds relpose and torquescale; `equality/joint` ties two joints via `polycoef`; `tendon/fixed` combines joints with coefficients. Joint structure must be a tree and loops are closed by adding an equality (third-party source). modeling.html advises loop closures solref about 0.004-0.005 with solref[0] at least 2 x timestep. I found no official four-bar XML example, so a snippet is untested by me.
- Plan: servo -> arm -> rod as a tree, with a `connect` equality (anchor at the horn pin) closing rod to horn body, itself a hinge child of the wing. The loop lives only in the simulator, so the T1 "no articulated joint in a loop" rule stays intact; the existing follower `pin` marks the anchor.
- Licence: Apache-2.0 (not re-verified). Already a dependency (sim.py).
- Also: for pure kinematics, a planar four-bar is a circle-circle intersection (arm tip radius about servo axis, rod length about horn pin on its radius about the hinge). A few lines of numpy, gives pose per servo angle, real throw, and a clash check with trimesh.

### E. RC kit practice (what real builders do)
- Opened: https://www.rcuniverse.com/forum/beginners-85/10810818-pushrod-geometry.html (forum, anecdotal). Hobbyking article blocked (403). Other rcuniverse threads seen only as search snippets; not cited as evidence.
- Rules stated: servo arm and pushrod at 90 degrees at neutral; pushrod perpendicular to the hinge line; horn hole in line with (or slightly behind) the hinge line, else differential throw or binding; servo arm parallel to the hinge line is ideal only "in a perfect world".
- Adapt: generator defaults and warnings (neutral angle, horn offset from hinge line, rod-to-hinge angle). They are forum opinion: any threshold needs a published source or stays `pending`.
- Not found: any open-source RC generator modelling linkages, bays or wire runs. Reported, not padded.

### F. Wire/harness routing
- Opened: https://raw.githubusercontent.com/mmiscool/BREP.io/master/docs/workbenches/wire-harness.md ; https://github.com/sargo-devel/Cables (checked 11-25).
- BREP.io: ports plus spline-guided paths form a network; each wire has endpoint labels, diameter, route length, status; shared spline segments form bundles whose diameter grows with wire count; unroutable wires keep a failure status. No bend radius in the doc.
- FreeCAD Cables workbench: LGPLv3 (preset models CC BY 4.0). Cable = Arch Pipe along a WireFlex (polyline or B-spline whose vertices attach to other objects); connectors and terminals are named snap points; needs FreeCAD 1.0+.
- Adapt (idea only): wire = {from port, to port, diameter, waypoints}; geometry = tube swept along a spline through waypoints; length reported; failure status if it cannot route. In trimesh: sweep a circle along a Catmull-Rom curve or chain short cylinders. Min bend radius we add ourselves.

## 3. Ranked recommendation per sub-problem

| Sub-problem | First choice | Second | Why |
|---|---|---|---|
| Linkage kinematics | Analytic four-bar solve (D) as a `plane` op, swept over servo range, plus trimesh clash check; sim gets `<connect>` at the follower pin | MJCF-only check | No new dependency, deterministic, respects T1 loop rule. Builder rules (E) as defaults. |
| Hinges | Keep PDL `articulation` revolute; generators add real hinge geometry (barrel and pin on the hinge axis, gap); borrow range check (A) | Gap-only geometry | Data model exists; the gap is geometry. |
| Wheels/axles | Separate wheel plus axle pin, revolute about axle; MJCF hinge with ground contact on the wheel | Static wheel | Plain revolute (A, D). |
| Bays | Bay = pocket from the library part's bounding box plus clearance; part pose = bay frame; parts expose named mounting frames (A's idea) | Coordinates only | No opened source shows RC bay generation; our own design work. |
| Wires | Port-to-port spline tubes with length and bend-radius report (F) | Straight tubes | Data model from F; ideas only (LGPL/unknown). |
| Fasteners | Screw/pin/clevis as small library parts at joint frames, with mass or a visual-only flag | Decals | No opened source covers this; simplest route. |

Cheapest proof: one elevator on an existing design: add the four-bar solve and `<connect>`; `plane design sweep` over servo range; check throw matches the T6 ratio (0.39 in the docs fixture) and no clash.

## 4. Risks

- MuJoCo loop closure: `connect` plus hinge can fight (over-constraint, jitter); docs advise soft solref. I did not run it. Prove on one mechanism first.
- Studio must pose the rod per frame, not only the horn.
- Builder rules are forum opinion; thresholds need a source or `pending`.
- Part count (fasteners, wires) inflates meshes, T1 overlap checks and mass bookkeeping; needs a visual-only flag.
- Copyleft: Assembly3 (GPL-3.0), FreeCAD and Cables (LGPL): ideas only, no code.
- Unverified or unopened: official MuJoCo four-bar example, FreeCAD wiki pages, Hobbyking page, OpenVSP control-surface API detail.

## 5. What not to do

- Do not add build123d, CadQuery, FreeCAD or OpenVSP as runtime dependencies. `connect_to` does not solve loops and the repo is trimesh plus MJCF.
- Do not relax the T1 articulated-loop rule; close loops in the simulator and kinematic solve only.
- Do not simulate wires as physical cables (MuJoCo rods exist but are costly); use static spline geometry.
- Do not change existing designs; opt in per design.
- Do not write thresholds from forum advice.

## 6. Recommendation (3 lines)

1. Analytic four-bar solver plus MJCF `<connect>` at the existing follower pin, proven on one elevator first.
2. Borrow build123d's vocabulary (named, typed, ranged joint frames) for bays, axles and fasteners; wires as port-to-port spline tubes.
3. No open-source RC generator with these features was found; expect to design the bay and fastener generators ourselves.
