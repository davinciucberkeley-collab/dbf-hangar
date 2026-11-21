---
name: weekly-update
description: Use when preparing the weekly team update for the Monday meeting.
---

# Weekly update

## Goal
`updates/<week>/updates.yaml` with one entry per person, and the published page `viewer/updates/<week>/index.html` (generated, git-ignored).

## Agents
| Step | Role | Model |
|---|---|---|
| Collects what changed per person | scout | Haiku |
| Approves the wording | conductor | Opus |

## Steps
1. Pick the week's Monday, as `YYYY-MM-DD`.
2. `plane update new <week>`.
3. For each person: `plane update add <week> <person> <link> "<changed>"`. The link goes to the PR, review or design that changed. The changed text is one plain sentence.
4. `plane ledger report` shows the decisions and open items to mention.
5. `plane update publish <week>`.
6. Open the generated page and check every link.
7. Commit `updates/<week>/updates.yaml` only.

## Pass check
- `plane update publish <week>` exits zero and `viewer/updates/<week>/index.html` exists.
- `git status --short` shows no file under `viewer/updates/`.

## Stop rules
- A person's change has no link: leave that person out and report it.
- `plane update publish` fails: stop and report its output.
