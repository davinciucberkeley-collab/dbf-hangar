---
name: design-iterate
description: Use when a design has failing or warning checks and you must change it to fix them.
---

# Iterate a design

## Goal
Fewer failing checks, with mass not increased unless justified in writing. Every change logged with its kind. No code edited.

## Agents
| Step | Role | Model |
|---|---|---|
| Runs the steps | design-engineer | Sonnet |
| Same check failed twice | recon | Sonnet |
| The pull request | reviewer | Opus |

## Steps
1. `plane design validate <path> --tier all`. List every FAIL, WARN and SKIP check id.
2. For each id, run `plane gate explain <check-id>` and read the criterion. The threshold is never changed. `plane standards show <key>` gives it.
3. If the same check id already failed in two earlier iterations (read the design's `CHANGELOG.yaml`), run the `recon` skill on it before the option table and cite its file.
4. Before any fix, write an option table with at least one row each for:
   - subtract: remove or shrink a part, joint or feature;
   - modify: change a part's type, geometry, material or method;
   - adjust: change the value of an existing parameter.

   Weight is the constraint. Choose `add` only with a written reason why no subtract, modify or adjust row works.
5. Try values without touching the design: `plane design sweep <path> <key> --values <a> --values <b>`.
6. Apply the chosen row: `plane design set <path> <key> --value <v> --why "<reason from the table>" --kind <add|subtract|modify>`. An adjust row is recorded as `--kind modify`. `plane design set` writes `CHANGELOG.yaml` itself.
7. Run `plane design validate <path> --tier all` again. Repeat the gate check for what still fails. Stop after the same check fails twice in a row, and use the recon rule above.
8. When failures dropped: `plane baseline update <path>`, then `plane design propose <path> "<title>"`. That opens a PR. Never edit `core/`, `schema/` or `standards/`.

## Pass check
- Every change has a `CHANGELOG.yaml` entry with its `kind`.
- `plane design validate <path> --tier all` shows no more failing check ids than before.
- `git diff --name-only main... -- core standards schema` prints nothing.

## Stop rules
- A fix would need an edit to `core/`, `schema/` or `standards/`: stop and report to the conductor.
- The same check fails twice in a row after a fix: stop and use the recon rule above.
