---
name: get-it-together
description: Use when the hourly audit is due, before a weekly meeting, or when a run feels stuck.
---

# Get it together

## Goal
A read-only report of at most 15 lines comparing recorded intent with the session's actual state. It fixes nothing.

## Agents
| Step | Role | Model |
|---|---|---|
| Runs the audit | auditor | Haiku |
| Called when a fix has failed twice | advisor | Opus |

## Steps
1. Read the last entries of `ledger/prompts.jsonl`. List prompts still open and older than an hour.
2. Read the newest `plans/*.md`: units, agent table, ticked boxes. Run `git log --oneline`. Work that maps to no unit is drift. The same failure after two fixes is stuck: send it to the advisor.
3. Read the roster rules in `.claude/agents/*.md` and check for: the conductor writing code; a role not in the agent table; Opus or Sonnet on an easy brief; a PR touching both `designs/` and `core/` without the migration label; thresholds in code or skills.
4. `plane ledger check` for items done without evidence. `plane ledger report` for overdue items. `plane progress --check` for a stale `PROGRESS.md`.
5. Every finding carries evidence: command output, a file and line, or a commit id.

Output format, as a fenced block in the report:

```
Audit <time>: <n> findings
<n>. [stuck|rule|drift|ledger|prompt] <what> -> <who>
```

## Pass check
- The report is at most 15 lines and every finding has evidence.
- A check that could not run is reported as `could not check <x>: <error>`.

## Stop rules
- `ledger/prompts.jsonl` cannot be read: report it as a could-not-check line and continue.
- A finding needs a fix: do not fix it. Report it to the conductor.
