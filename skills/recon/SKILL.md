---
name: recon
description: Use when asked how others have solved a problem, or when the same check failed twice.
---

# Recon

## Goal
`knowledge/concepts/recon-<slug>.md` with the question, the approaches found, and a ranked recommendation that prefers fixes that add no parts. The number of approaches is the one `.claude/agents/recon.md` states.

## Agents
| Step | Role | Model |
|---|---|---|
| Benchmarks and ranks the approaches | recon | Sonnet |
| Gathers the entries | scout | Haiku |
| Spot-checks the sources | reviewer | Opus |

## Steps
1. Write the question as one line, for example "wing too heavy: how did others fix it without adding parts".
2. `plane morph coverage` and `plane design list` show what is already known internally.
3. For each approach found: `plane research new source <slug>` or `plane research new diy <slug>`.
4. `plane research check <path>` until nothing is empty.
5. Write the ranking table into `knowledge/concepts/recon-<slug>.md`: approach, source file, what it changes, adds parts yes or no, evidence.
6. The recommendation lists subtract, modify and adjust options before any add.
7. Unexplored combinations go to `plane idea add "<title>" "<body>" "<by>"`.
8. Hand the recommendation to the caller, who applies it with `design-iterate`.

## Pass check
- `plane research check <path>` lists nothing for each new source file.
- The recon file has the question, the table and the recommendation.
- Every source link was opened.

## Stop rules
- Fewer approaches exist than the role file requires: report the shortfall. Do not pad the table.
- A source cannot be opened: record it with `verified: false`.
