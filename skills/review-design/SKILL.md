---
name: review-design
description: Use when asked to review a design, PR or artifact against the scorecard.
---

# Review a design

## Goal
`reviews/<date>-<design-id>.md` in the format of `standards/review-scorecard.md`, ending accepted or not accepted.

## Agents
| Step | Role | Model |
|---|---|---|
| Every item of the review, one reviewer reused via SendMessage | reviewer | Opus |

Never start one reviewer per item.

## Steps
1. `plane design validate <path> --tier all`. Paste the scorecard unchanged as the Automated section.
2. If a printed part has no stress check or an outdated one, run `plane fea run <path> --all`, commit `designs/<id>/fea/`, and validate again.
3. `plane claim check <path>`. Paste the verdicts.
4. For each judgment item, find its criterion with `plane standards show <key>` or `plane gate explain <check-id>`. Score PASS, FAIL or N/A with a one-line reason.
5. Judge only what the validators cannot: lineage, the README question, joint plausibility, crude modelling.
6. An item with no criterion is a Non-blocking suggestion, never a block.
7. Discipline checks: read the discipline review skills that match the design's subsystems: `review-structures`, `review-aero`, `review-controls`, `review-propulsion`, `review-manufacturing`, `review-test-safety`. Skip any that does not exist yet and say so in the file.
8. Write the file and commit it on the design's branch.

## Pass check
- Every row cites a criterion that exists in `standards/`.
- The Automated section equals the validator output.
- The verdict follows the rule in `standards/review-scorecard.md`.

## Stop rules
- The validator crashes: report the crash. Do not review by hand around it.
- A criterion you need does not exist: propose it under Non-blocking suggestions.
