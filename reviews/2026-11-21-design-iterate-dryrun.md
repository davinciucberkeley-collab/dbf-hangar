# Dry run: design-iterate on example-tailsitter-wing (U3.2)

Skill: `skills/design-iterate/SKILL.md`

Scratch copy designs/dryrun-tailsitter, deleted before commit.

$ plane design copy designs/example-tailsitter-wing dryrun-tailsitter
```
C:\Users\trist\wt\u3.2\designs\dryrun-tailsitter\plane.yaml
```
exit=0
$ C:/Users/trist/wt/u3.2/.venv/Scripts/plane.exe design set designs/dryrun-tailsitter components[wing].geometry.lifting_surface.span --value 800 --why dry-run setup: provoke one failing check --kind modify
```
components[wing].geometry.lifting_surface.span: 1000 -> 800
exit=0
```
$ plane design validate designs/dryrun-tailsitter --tier all | grep -v "| PASS |"
```
validate exit=1
# Scorecard: dryrun-tailsitter

**Accepted:** no

| Tier | Status | Check | Result | Criterion |
|---|---|---|---|---|
| 1 geometry | FAIL | T1.watertight | PASS: all component meshes are closed | design-standards.yaml#interference_max_mm3 |
| 1 geometry | FAIL | T1.connectivity | PASS: all 12 components connect to 'center_body' | design-standards.yaml#attach_tolerance_mm |
| 1 geometry | FAIL | T1.attachment | PASS: wing-body: slot-tab joint OK | design-standards.yaml#attach_tolerance_mm |
| 1 geometry | FAIL | T1.attachment | PASS: mount-l: glued joint OK | design-standards.yaml#attach_tolerance_mm |
| 1 geometry | FAIL | T1.attachment | PASS: mount-r: glued joint OK | design-standards.yaml#attach_tolerance_mm |
| 1 geometry | FAIL | T1.attachment | PASS: motor-l: bolted joint OK | design-standards.yaml#attach_tolerance_mm |
| 1 geometry | FAIL | T1.attachment | PASS: motor-r: bolted joint OK | design-standards.yaml#attach_tolerance_mm |
| 1 geometry | FAIL | T1.attachment | PASS: prop-l: press-fit joint OK | design-standards.yaml#attach_tolerance_mm |
| 1 geometry | FAIL | T1.attachment | PASS: prop-r: press-fit joint OK | design-standards.yaml#attach_tolerance_mm |
| 1 geometry | FAIL | T1.attachment_contact | FAIL: fin-l: parts are 91.0 mm apart (tolerance 2.0 mm) | design-standards.yaml#attach_tolerance_mm |
| 1 geometry | FAIL | T1.attachment_contact | FAIL: fin-r: parts are 91.0 mm apart (tolerance 2.0 mm) | design-standards.yaml#attach_tolerance_mm |
| 1 geometry | FAIL | T1.attachment | PASS: battery-bay: clamp joint OK | design-standards.yaml#attach_tolerance_mm |
| 1 geometry | FAIL | T1.attachment | PASS: fc-mount: bolted joint OK | design-standards.yaml#attach_tolerance_mm |
| 1 geometry | FAIL | T1.motor_has_prop | PASS: motor_l: drives an attached propeller | design-standards.yaml#embed_max_fraction_of_child |
| 1 geometry | FAIL | T1.motor_has_prop | PASS: motor_r: drives an attached propeller | design-standards.yaml#embed_max_fraction_of_child |
| 1 geometry | FAIL | T1.interference | PASS: no clipping between unattached parts | design-standards.yaml#interference_max_mm3 |
| 8 sourcing | WARN | T8.program.budget | WARN: report-only until 2026-12-08: no BOM: budget not checked | program.yaml#budget_usd |

Fidelity: 5 of 61 blocking checks use sourced thresholds; 0 components have measured mass.
```
```
$ plane gate explain T1.attachment_contact
T1.geometry (tier 1, blocking): design-standards.yaml#interference_max_mm3
interference_max_mm3 = 1.0  [internal convention]  Parts that are not attached to each other may not overlap more than this volume (catches clipping and prop strikes).
exit=0
```
```
$ plane design sweep designs/dryrun-tailsitter components[wing].geometry.lifting_surface.span --values 850 --values 900 --values 1000
850: accepted=False mass_g=759.0 static_margin=0.0924 stall_speed_mps=8.45 hover_tw=2.418 failures=['T1.attachment_contact']
900: accepted=False mass_g=759.0 static_margin=0.1083 stall_speed_mps=8.22 hover_tw=2.418 failures=['T1.attachment_contact']
1000: accepted=True mass_g=759.0 static_margin=0.1404 stall_speed_mps=7.79 hover_tw=2.418 failures=[]
exit=0
```

## Option table

| Row | Kind | What it would mean for this wing failure |
|---|---|---|
| subtract | subtract | Remove the outer wing panel that carries the fin contact, so no part sits at the fin mount; this drops mass but changes the planform. |
| modify | modify | Move the fin mount geometry so the fin contact clears at the current span; this keeps the planform but edits a joint. |
| adjust | adjust | Restore the span so the fin contact clears again, as the sweep shows; this changes one existing parameter and adds no parts. |
| add | add | Add a spacer or bracket between wing and fin; this adds a part and mass that the failure does not need. |

`add` is not chosen because an adjust row (restoring the span) fixes the failure without adding mass.

recon not triggered: this check has not failed twice.

$ plane design set designs/dryrun-tailsitter components[wing].geometry.lifting_surface.span --value 1000 --why "restore span: attachment contact passes again in the sweep" --kind modify
```
components[wing].geometry.lifting_surface.span: 800 -> 1000
exit=0
```
$ plane design validate designs/dryrun-tailsitter --tier all | grep -v "| PASS |"
```
exit=0
# Scorecard: dryrun-tailsitter

**Accepted:** yes

| Tier | Status | Check | Result | Criterion |
|---|---|---|---|---|
| 8 sourcing | WARN | T8.program.budget | WARN: report-only until 2026-12-08: no BOM: budget not checked | program.yaml#budget_usd |

Fidelity: 5 of 61 blocking checks use sourced thresholds; 0 components have measured mass.
```
$ cat designs/dryrun-tailsitter/CHANGELOG.yaml
```
- date: '2026-11-21T19:49:27Z'
  key: components[wing].geometry.lifting_surface.span
  old: 1000
  new: 800
  why: 'dry-run setup: provoke one failing check'
  kind: modify
- date: '2026-11-21T19:50:16Z'
  key: components[wing].geometry.lifting_surface.span
  old: 800
  new: 1000
  why: 'restore span: attachment contact passes again in the sweep'
  kind: modify
```

plane design propose skipped in the dry run (it opens a PR).

$ rm -rf designs/dryrun-tailsitter .sweeps && git status --short
```
 M skills/design-concept/SKILL.md
 M skills/make-skill/SKILL.md
 M skills/research/SKILL.md
 M skills/review-design/SKILL.md
?? .logs/
?? reviews/2026-11-21-design-iterate-dryrun.md
?? skills/design-iterate/
?? skills/get-it-together/
?? skills/plan-scheme/
?? skills/recon/
?? skills/weekly-update/
?? tests/test_skills.py
```
