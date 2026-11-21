---
name: research
description: Use when asked to research builds, papers, standards or concepts for the knowledge base.
---

# Research

## Goal
New template-conforming entries under `knowledge/`, each with opened sources only.

## Agents
| Step | Role | Model |
|---|---|---|
| Write scout briefs and pick gaps | tactician | Sonnet |
| Fill templates, several scouts in parallel on disjoint topics | scout | Haiku |
| Spot-check a sample of entries | reviewer | Opus |

## Steps
1. `plane research new source <slug>` or `plane research new diy <slug>` creates the entry from its template.
2. Brief the scout with the exact output path and template, the starting queries, and these rules: only URLs it opened, own words, `unknown` instead of guessing, stop and report shortfalls.
3. `plane research check <path>` lists fields still empty. Repeat until it lists none.
4. Gap-driven mode: `plane morph coverage` lists chart options with no design. Brief one scout per empty cell. An empty result is a finding.
5. Add a source-backed option with `plane morph add-option <dimension> <id> "<name>" <source>`.
6. Record candidate combinations with `plane idea add "<title>" "<body>" "<by>"`.
7. For "how have others solved X", use the `recon` skill. It is the one for that question; do not duplicate it here.

## Pass check
- `plane research check <path>` lists nothing for every new file.
- The reviewer's spot-check found no invented URL.

## Stop rules
- A source is paywalled or blocked: record it with `verified: false`. Do not paraphrase from memory.
- A field cannot be filled from opened sources: write `unknown` and report the shortfall.
