# Review Scorecard Format v0.1

Every review — human or agent — returns this. No free-form "looks good."

```markdown
# Review: <design id or artifact path> @ <git commit>

## Automated (from `plane validate --tier all`)
| Tier | Result | Details |
|---|---|---|
| 0 Schema | PASS | |
| 1 Geometry | FAIL | wing_l overlaps fuselage by 4 mm at x=120 |
| ... | | |

## Criteria (judgment items)
| Criterion (link into standards/) | Result | Reason |
|---|---|---|
| design-standards.yaml#static_margin | PASS | 11% MAC, within 5–15% |
| manufacturing.yaml#jacobs-laser | N/A | no laser-cut parts |

## Blocking issues
1. ...

## Non-blocking suggestions
1. ...
```

Rules:
- A design is **accepted** only when no automated result is FAIL or SKIP and no blocking criterion is FAIL (the validator's `accepted` flag applies this).
- Every row cites a criterion that exists in `standards/`. Link forms: `design-standards.yaml#<leaf key>` (e.g. `static_margin`), `manufacturing.yaml#<machine id>`, `schema/plane.schema.json`, or `requirements.<field>` for a design's own requirement. A test resolves every criterion the validator emits. If you want to judge something that has no criterion, propose the criterion in "Non-blocking suggestions" instead.

## Evidence and closure

Rules for closing a check or a fail; each scorecard row is judged by these.

- A fail closes only by a design change, a corrected model with a stated reason, or a deciding test. [J6#2]
- A limit is never loosened to close a fail, and a hold point that waits for a test is not a fix. [J6#3]
- A figure the reviewer estimated is labelled "reviewer estimate" in its scorecard row.
- Figures quoted in a claim are spot-checked against the claims graph (T9) before they are accepted.
- Check a model result against an independent reference (another code, a polar, a hand calculation or a closed form) and record the difference against its stated limit. [B2#5] [B2#33] [B3#3] [C4#1] [C5#34]
- Check convergence by comparing the finer model with the coarser one, and pass it only within its stated limit. [B1#20] [B2#34] [B2#35] [B3#1] [B3#2]
- Judge a value against the design value its limit refers to, and record a value that has no stated limit as information only. [C2#22] [E2#9] [B3#4]
- Compare a copied or reproduced value with its source, and take a residual or worst-case figure over all cases before comparing it with its limit. [B3#28] [B4#1] [C1#17]
- Hold a marginal test result outside the approved range until its in-flight review passes, and treat any failed result as blocking the first flight. [F5#16] [F5#17]
- Pass a gate only when every item it lists is measured or ticked, do not fly until the ground gates pass, and stop flying when a gate fails twice. [H2#34] [H2#66] [H3#80] [H2#78]
- Give every figure a unit, a source and a status label, show an unknown value as a dash, mark an estimate EST after its number, and say how each link was checked, by opening it or by search. [J4#2] [J4#9] [J6#32] [I1#37] [I1#38]
- Check a spot-checked figure against the graph and label it spot checked, record each check as agreeing or not beside the reviewer figure, and call an untested result a pass on paper only. [J6#6] [J6#14] [J6#7]
- Give each finding one of three severities, blocker, major or minor, according to the phase it blocks. [J6#8]
- List generator warnings as open items, make a strict run fail on them, and keep a rejected option visible, faded, never deleted. [J5#17] [J4#15]
- Hold a build stage until its named change requests close, and have a second person initial each hold point. [G4#11] [G4#44]
- List tooling as drawn or only named, fix an open item before the step that needs it, and rebaseline only baselined subsystems while keeping a kept subsystem's held prefix. [G1#32] [G2#24] [A4#10]

## Discipline sign-off

Rules for signing off a discipline skill item by item against the design.

- Each discipline skill that matches a subsystem of the design (skills/review-structures, review-aero, review-controls, review-propulsion, review-manufacturing, review-test-safety) is read, and every item in it is answered PASS, FAIL or N/A with a one-line reason.
- Buy a gated line only when the condition named against it is met, such as a reserve after the order, a recorded decision, a lab that lacks the item or a failed check. [I1#23] [I1#24] [I1#26] [I1#27] [I1#28]
- Confirm that each item is owned, borrowed with the lender named or bought, release a cart only after its checks, and fail any new line that exceeds the pessimistic margin. [I1#29] [I1#44] [I1#48]
- Keep a part on hold until the freeze named for it, sign off each freeze before its stage starts, and agree one figure with its named owners when the documents disagree. [G1#34] [G2#33] [G4#41] [G4#30]
- Show an open decision as open with the test that will close it, show a figure not found in the repo as not found, and do not assume a workspace exists because the host has the capability; name it with its deadline. [J1#41] [I2#19] [I2#26]
- Require an independent review before any fail counts as closed, and label a board re-check of a team value REVIEWER EST. [J6#1] [J6#5]
- Give each order one verdict, Go, Go with conditions or No-go, and give each condition a latest date and an owner. [J6#11]
- Compute a weighted concept score as the weighted sum of its scores divided by the top score, with weights that total the full weight. [J6#18]
- Record a guideline with no limit as information only, and never let it fail a check. [F1#23]
