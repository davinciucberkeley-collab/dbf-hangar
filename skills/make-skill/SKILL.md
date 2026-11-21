---
name: make-skill
description: Use when creating or revising any skill in `skills/`.
---

# Make a skill

## Goal
A skill with the same shape as every other, that calls `plane` commands only and passes `tests/test_skills.py`.

## Agents
| Step | Role | Model |
|---|---|---|
| Existing skills and prior art | recon | Sonnet |
| Synthesize into one outline | tactician | Sonnet |
| Write it | builder | Haiku |
| Check the shape | reviewer | Opus |

## Steps
1. Research what the skill must do, from `knowledge/` and the plan.
2. Recon: read every `skills/*/SKILL.md` and the `knowledge/` entries, run the `recon` skill, and list what the best ones do.
3. Synthesize the best of them into one outline.
4. Write it in this shape: frontmatter with `name` and a `description` starting "Use when", then Goal, Agents, Steps, Pass check and Stop rules, in that order.
5. De-bloat: delete anything a step does not need. The line limit is the one in `tests/test_skills.py`.
6. No numbers or thresholds in the skill. Link `standards/<file>.yaml#<key>` instead.
7. Every step names a `plane` command or a file path.
8. `pytest tests/test_skills.py -q` must pass.
9. Try the skill once on a real input and commit the transcript under `reviews/`.

Every analysis becomes a skill.

## Pass check
- `pytest tests/test_skills.py -q` passes.
- A transcript of one real run is committed under `reviews/`.

## Stop rules
- The skill needs logic the platform lacks: stop. Add that logic to `core/` first, through the conductor.
- The same test fails after two fixes: stop and report the test id and output.
