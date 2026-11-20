# Agent Standard v0.2

Roles are by type and level of work, not aircraft domain. The role files are `.claude/agents/*.md`; this file is the policy, those are the definitions.

## Core rule

**The clearer the goal, the cheaper the agent.** If a task can be written as exact, checkable instructions, it goes to Haiku. If you can't write it that way yet, the task isn't ready to delegate — break it down further first.

## Roles

| Role | Model | Does |
|---|---|---|
| `conductor` | Opus (main session) | Owns the plan, launches agents, merges decisions, the only one who declares a unit done. Never writes code or bulk text itself. |
| `advisor` | Opus | "This works / doesn't, but does it match intent? What should it do and how do we get there?" Called on any unit that failed twice. Edits nothing. |
| `tactician` | Sonnet (hard → Opus via `advisor`) | Turns one unit into builder-ready briefs; checks a finished unit against its spec. |
| `builder` | Haiku | One brief: exact files, exact test, exact command. Stops and reports on ambiguity. |
| `builder-plus` | Sonnet | Same as `builder`, for units marked hard. |
| `scout` | Haiku | Facts into `knowledge/TEMPLATE-*.md` and ledger extracts from transcripts. No opinions outside the template. |
| `recon` | Sonnet | "How have others solved this?" Benchmarks 3–5 approaches and returns a ranked recommendation. Does not build. |
| `design-engineer` | Sonnet | Iterates a design using only `plane …` commands; considers subtract / modify / adjust before add. Edits no `core/`, `schema/` or `standards/`. |
| `reviewer` | Opus, fresh per wave, reused within the wave | Runs validators and tests, scores every PR of the wave against spec and scorecard. No "looks good" without a criterion. |
| `auditor` | Haiku | Hourly get-it-together audit: open prompts, rule breaks, stuck agents, plan drift. Fixes nothing. |

## Work class

- **Easy** → `builder` (Haiku). Tactician easy → Sonnet.
- **Hard** (unit marked `[hard]` in the plan) → `builder-plus` (Sonnet). Tactician hard → escalate via `advisor` (Opus).
- A unit that fails review twice goes to `advisor`, not a third fix.

## Agent tables

Before any agent is launched, the conductor writes an **agent table** in the current plan:

```
| Step | Role | Model | Input | Output | Pass criterion |
```

The `agent_gate` hook allows only roles that appear (in backticks) in such a table in the newest `plans/*.md`. No agent is launched that isn't in the table. Adding one mid-task means updating the table first.

## Builder-ready bar

Instructions can go to Haiku only if they include all of the following (or are a brief file under `plans/<plan>/briefs/`):

1. **Exact output** — file path(s) and format (schema version, template name).
2. **Exact inputs** — the files/URLs to use; nothing to "find."
3. **A mechanical pass check** — a command to run (`plane validate`, `pytest`) or template fields that must all be filled.
4. **Stop rule** — what to do when stuck: report the blocker, don't improvise.

## Brief template

A brief file (`plans/<plan>/briefs/<unit>-<n>.md`) meets the builder-ready bar and has these headings in this order. Where the brief and plan §7 differ, the brief governs; the tactician records the difference in Plan coverage.

```
# Brief <unit>-<n>: <title>

class: easy|hard · role: builder|builder-plus · plan: §<n> <unit> · rules: R<n>…

## Environment
- Windows 11 + Git Bash. Use absolute paths only (e.g. `C:/Users/trist/wt/<unit>/...`); never `../` or `~`: they resolve from the wrong folder inside a worktree.
- Worktree: `git -C C:/Users/trist/dbf-hangar worktree add C:/Users/trist/wt/<unit> -b <branch> main`; work only there; create nothing outside `C:/Users/trist/wt/<unit>`.
- Venv per worktree: `python -m venv C:/Users/trist/wt/<unit>/.venv`, then from the worktree `.venv/Scripts/python -m pip install -e ".[mcp,dev]"`; use that python for every command.
- `.gitattributes` forces LF (`* text=auto eol=lf`); do not change line endings. After your commit, `git ls-files --eol | grep -c "w/crlf"` must print `0`.
- Edit only the files the brief lists. No repo-wide `sed` or search-and-replace; nothing "while you are there".
- Iterate with targeted tests; run the full suite once at the end (4 to 24 minutes; do not interrupt it).
- Push only the branch named in the brief and wait for CI; never push or merge `main`.

## Where
Branch, worktree, and the exact list of files the builder may change.

## Known failures
Test ids that already fail on `main` and who owns the fix, or `none`.

## Plan coverage
| §7 step | Status |
|---|---|
| <every step of the unit, one row each> | covered / deferred to <unit> / dropped (<reason>) |

## Exact steps and outputs
## Exact tests
## Pass check
## Commit
## Stop rule
```

The Environment block is copied verbatim into every brief; only `<unit>` and `<branch>` change. Plan coverage lists every §7 step of the unit; a step the brief does not do is `deferred` (to a named unit) or `dropped` (with the reason), never silently missing.

## Reviews

- One **fresh** reviewer per wave, reused (`SendMessage`) for that wave's re-reviews. Don't spawn a new reviewer per item.
- Reviewer always runs the automated validators first (`plane validate --tier all`) and pastes the scorecard.
- Human-judgment items are scored against named criteria from `standards/` (e.g. `design-standards.yaml#static_margin`), each as PASS / FAIL / N/A with a one-line reason.
- Scorecard format: `standards/review-scorecard.md`. Scorecards go in `reviews/`.

## Enforcement

Hooks live in `harness/hooks/`:

- `log_prompt` — on each prompt, logs it to the ledger and reports its id.
- `agent_gate` — before a Task/Agent launch, checks the role against the roster, the newest plan's agent table, and the builder-ready bar.
- `reinject` — at session start, re-injects hangar context and the unfinished units.
- `stop_gate` — blocks stopping while the session has open prompts; after 3 blocks in a row the stop is forced and logged. Override with `HANGAR_ALLOW_STOP=1`.

For other repos: `python harness/install.py --target <project>`.

## Cost check

At the end of a task the conductor reports how many agents of each role ran. If Opus or Sonnet did work that met the builder-ready bar, note it as a process miss.
