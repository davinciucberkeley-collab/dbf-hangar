---
name: plan-scheme
description: Use when starting a goal that needs a plan with several units before launching any agent.
---

# Plan a scheme

## Goal
`plans/<date>-<slug>.md` with waves, units and an agent table, plus one permissions prompt, before any agent runs.

## Agents
| Step | Role | Model |
|---|---|---|
| Planning, at maximum effort | conductor | Opus |
| Checks the intent | advisor | Opus |
| Writes the briefs, later | tactician | Sonnet |

## Steps
1. Set effort to maximum for the planning.
2. Read the goal, `plane ledger report`, `plane ledger check`, and the newest plan in `plans/`.
3. List the units. Each is about one PR and one agent.
4. Order the units into waves by dependency. A unit goes in the earliest wave whose dependencies are done.
5. Mark a unit hard only when it cannot be written as exact, checkable instructions.
6. Write the agent table with the header `| Step | Role | Model | Input | Output | Pass criterion |`, as `standards/agents.md` requires.
7. Surface every unknown decision now: `plane ledger add decision "<text>" --source <plan>`.
8. Write the one permissions prompt, listing every command and folder each wave needs.
9. A broken unit is fixed in place. Never patch it with a new unit.
10. Save the plan, run `plane progress --write`, drop to medium effort, and hand over to the conductor.

## Pass check
- `grep -q "| Step | Role | Model | Input | Output | Pass criterion |" plans/<file>` exits zero.
- The plan has a permissions prompt section and a decisions list.

## Stop rules
- The goal is unclear: send it to the advisor before writing any unit.
- A unit cannot be written as exact, checkable instructions: mark it hard. Do not guess at it.
