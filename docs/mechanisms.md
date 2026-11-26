# Servo, horn and pushrod: a verified mechanism recipe

## 1. What this is for

A control surface needs a servo, an arm on the servo output, a pushrod and a horn on the surface. T6 (`T6.mechanism`, `T6.ratio`) only runs when a `mechanisms[]` entry joins them.

## 2. The recipe

(a) Put the servo just ahead of the hinge line (smaller x on a tail or wing trailing surface), on the side of the fixed surface away from the airflow if possible. Glue it with `embed_ok` where it sits in a recess.

(b) The servo arm is a `plate` (`plane xy`, flat on the servo output). Join it to the servo with attachment `servo-arm`, using `articulation: {type: revolute, pivot: <spline axis point>, axis: [0, 0, 1], range_deg: [...]}`. This is the driver.

(c) The pushrod is a `strut` from the arm tip to a point just short of the horn.

(d) The horn is a `plate` (`plane xz`) glued to the control surface, hanging toward the rod.

(e) The surface hinge is an attachment with `articulation` (revolute, pivot on the hinge line) from the fixed surface to the control surface.

(f) Join the rod to the arm with an attachment that has `kinematic_link: true`. This is the driver end.

(g) The horn end of the link is a small `pin` component fully inside the horn, joined to the horn by an ordinary attachment. This is the follower end. The rod is NOT attached to the horn or the pin: an attachment from the rod to the horn would close a loop, and T1 refuses articulated joints in a loop.

(h) The `mechanisms[]` entry names the driver attachment, the driven hinge, the input range and `link: {driver_end, follower_end}`.

## 3. The numbers T6 checks

`T6.ratio` measures the small-angle ratio from the two link points: `ratio = -(arm lever) / (horn lever)`. In the fixture the arm tip is 6 mm off the servo axis and the horn pin is 15.25 mm from the hinge line, so 6 / 15.25 = 0.393. The sign follows the two axes.

Do not guess `expect.ratio`. Validate once, read the `declared ... geometry gives X` text in the `T6.ratio` message, and write X rounded to two decimals. The tolerance is `gate-thresholds.yaml#mechanism_ratio_tol`.

## 4. Common failures

- `T1.attachment_overlap ... set embed_ok if intended`: the arm sits on the servo, or the horn on the surface. Set `embed_ok` if the overlap is intended.
- `T1.attachment_contact: parts are N mm apart`: move the part or the joint location so they touch within `attach_tolerance_mm`.
- `T1.articulation: joint lies in a loop of attachments`: the rod is attached at both ends. Remove the follower attachment of the rod.
- `T6.ratio ... dead point: link.driver_end and link.follower_end coincide`: the two link points are the same point.
- `T6.mechanism ... collide at input`: the rod or horn sweeps through a surface. Shorten the horn or move the rod.
- `link.driver_end ... must be kinematic_link: true with parent and child on the driver side`: the driver-end attachment is not flagged or is on the wrong side.

## 5. Worked example

The design in `tests/fixtures/mechanism-recipe/plane.yaml` is checked by `tests/test_mechanism_recipe.py`. Copy its six components and six attachments as the pattern, with the numbers for a tail 60 mm deep and an elevator 30 mm deep.

Create the parts with:

- `plane design add <path> components --value '{...}' --why "..."`
- `plane design add <path> attachments --value '{...}' --why "..."`

When a `mechanisms` list already exists, add the mechanism entry with `plane design add <path> mechanisms --value '{id: ..., driver: ..., ...}' --why "..."`. Otherwise use `plane design set <path> mechanisms --kind add --value '[{...}]' --why "..."`.

## 6. Warnings

- `T6.undriven.<joint>`: an articulated joint that no mechanism drives.
- `T6.servo_undriven.<servo>` (for conventional fixed-wing designs, from U13.4-2): a servo that no mechanism uses.

## Four-bar kinematics (PDL 1.3)

Add `kinematics: four_bar` to a `mechanisms[]` entry (schema_version 1.3; default `ratio`, the declared expect ratio x input). It needs a `link`, exactly one driven attachment, the same attachment in `expect`, and an `input_range_deg` containing 0.
- T6 then solves the follower angle so that the distance from the `link.driver_end` point (arm tip) to the `link.follower_end` point (horn pin) stays the rod length, within the follower's `range_deg`. The `expect` ratio is no longer the angle; T6.ratio still checks it against the geometry.
- Jam rows (T6.mechanism FAIL, never a silent clamp): no follower angle keeps the rod length; the transmission angle (rod against the horn arm, 90 = ideal, 0 = dead point) is below `four_bar_min_transmission_deg`; the follower jumps more than `four_bar_max_follower_step_deg` for one degree of input (branch flip).
- The rod is posed on the horn pin at every step: the step collision loop checks rod, horn, pin and surface with nothing exempted, and `T6.link` is a PASS row. Studio Physics shows the rod pinned on the horn.
- Limits: T1 pose sweeps still pose the rod rigidly (their `T1.kinematic_link` SKIP rows stay); a servo or a hinge parent that itself moves with another articulated joint is refused.

## Wheels on axles

Set `landing_gear` `wheels: separate` (PDL 1.3): the gear mesh is then legs, axle stubs and the nose fork only (`main_wheels` must be 1; `axle_d` is the stub diameter, 0 = half the leg diameter).
- Add one `wheel` generator component per wheel (`wheel_d`, `wheel_w`, `shape`, `bore_d`) with `position` at its axle centre, so the wheel sits on its axle stub.
- Attach each wheel to the gear with a `hinge` attachment whose `articulation` is `type: continuous`, `axis: [0, 1, 0]`, `pivot` at the axle centre (no `range_deg`, no `poses`).
- Make the bore 0.4 mm larger than `axle_d`, so the joint point at the axle centre stays on the wheel and clears the stub.
- T1 checks each wheel for contact with the gear (a nose wheel that is not on its fork FAILs); it does not sweep a continuous joint, and T6 does not warn it as undriven. A continuous joint cannot be a mechanism driver or follower.
- Studio Physics gets one `spin-<attachment id>` sweep per wheel (0 to 360 degrees).

## Splitting a wing into core and ailerons

A wing split into a core and two ailerons is three components: the wing (`part: core`) and two `part: elevon` pieces (`side: right` and `side: left`), all with the same airfoil, span, chords and `elevon_y`.

The pitfall: the core ends at `hinge_frac` of the chord everywhere, and the elevon pieces only cover `elevon_y`. Outside `elevon_y` the trailing part of the chord belongs to no component. For the C172 rehearsal (core to 0.72 chord) 28 % of the chord outside `elevon_y` is missing, so the measured wing area is 158,130 mm2 instead of 192,514 mm2 and stall speed and wing loading come out wrong.

The fix: set `core_fill: outside` on the CORE component only (not on the elevon pieces). The core then runs full chord outside the `elevon_y` span, so core plus elevon pieces cover the whole planform (192,517 mm2 measured). The default `core_fill: off` changes nothing. `core_fill: outside` needs `part: core` and a valid `elevon_y`.

Keep the two elevon pieces as `articulated` children of the wing: `T3` measures the planform from the core and its articulated children, so only then is the aileron area counted.

Tier 3 warns with T3.wing_area_complete when the measured wing is less than 97 % of the area its wing_panel params give.
