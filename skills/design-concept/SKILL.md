---
name: design-concept
description: Use when asked to create or change an aircraft design or concept in `designs/<id>/plane.yaml`.
---

# Design a concept

## Goal
A design that passes `plane design validate` and has a README stating the question it answers.

## Agents
| Step | Role | Model |
|---|---|---|
| Pick morphology, set requirements | conductor | Opus |
| Write the YAML to a precise spec | builder | Haiku |
| Fix a named failing check after repeated failed tries | builder-plus | Sonnet |
| Final review | reviewer | Opus |

## Steps
1. `plane design list` shows what exists.
2. Check `knowledge/morphological-chart.yaml` and `knowledge/diy-projects/` for the cell this concept fills and for prior art. Record both under `lineage`.
3. Start from the closest design: `plane design copy <closest-path> <id>` or `plane design new <id> --template <closest-id>`.
4. Set morphology, requirements and components. Units: mm, g, N, deg. Body frame: +x aft from the nose, +y right, +z up. Model propellers as swept-disc cylinders.
5. Declare every joint in `attachments` with `location`, `method` and `rated_load_n`. Set `embed_ok: true` only when a part passes into another, such as a spar into a slot.
6. `plane design validate <path> --tier all`. Fix failures in tier order. Fix the design, never the threshold. `plane standards show <key>` gives a limit and its source.
7. Printed parts: after any change run `plane fea run <path> --part <part>` and commit `designs/<id>/fea/<part>.json`.
8. Moving parts: add `articulation` to the joint attachment, using the schema version documented in `docs/pdl/`. Name the poses `flight.hover_pose` and `flight.cruise_pose`.
9. After failures drop, run `plane baseline update <path>`. Never add baseline entries to hide a new failure.
10. Write `designs/<id>/README.md`: one paragraph and the question the concept answers.
11. A design that keeps failing goes to the `design-iterate` skill.

## Pass check
`plane design validate <path> --tier all` exits zero and the scorecard says `Accepted: yes`.

## Stop rules
- The schema cannot express the concept: stop and propose a schema change to the conductor.
- A check fails and you believe the check is wrong: stop and report the check id and its output. Do not change the threshold.
