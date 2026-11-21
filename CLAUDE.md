# Instructions for Claude in dbf-hangar

This file only points. Read what applies before acting.

- The plan and spec: `plans/2026-11-20-standardization.md`. Work only on units listed there; tick its checkboxes as you go.
- Agent roles: `.claude/agents/` (10 roles). Launch only roles listed in the plan's agent table. Haiku builds; units marked [hard] go one tier up.
- Designs are data (`designs/<id>/plane.yaml`, PDL). Change them with `plane design set`, never by editing code. A PR that touches `designs/` must not touch `core/` (except the `migration` label).
- Use the `plane` CLI / MCP for every operation; don't reimplement validation, mass, export or analysis logic.
- Thresholds live only in `standards/*.yaml`, each with a source or `pending`. Fix the design, not the threshold.
- Imports from other repos are adapted, not copied, and recorded in `PROVENANCE.md`.
- Research goes into `knowledge/` through its templates. Cite only sources you opened.
- `PROGRESS.md` is generated: after ticking plan boxes, adding review verdicts or changing the ledger, run `plane progress --write` in the same commit.
- Be quiet: report results, decisions and questions; don't narrate.
- Every commit message ends with the trailer `Co-authored-by: Tristan Hottier <185231225+TristanHottier@users.noreply.github.com>` (repo owner), alongside any agent attribution lines.
