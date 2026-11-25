---
id: dbf-combined-davinci-api-summary
title: DBF-Combined: DaVinci API summary (T-037) docs/integration/DAVINCI.md
authors: DBF-Combined project (author not stated)
year: 2026
url: origin/redesign/v1:docs/integration/DAVINCI.md
type: website
retrieved: 2026-11-24
verified: true
---

## Summary
Team summary of the DaVinci attempt dated 2026-11-24: access, what worked over REST, the Concept A import, real cost, failures and the agreed workflow. Points to the other DBF-Combined davinci files for detail.

## Usable rules / numbers
- Tokens are personal access tokens; scopes projects read/write, sessions:manage, usage:read; no agent:message, so the DaVinci agent cannot run (section 1).
- Concept A id bbb1b6e0-63d1-4a95-8e6d-0e300beed2c9, org design-build-fly; all writes on scratch branches, main not written (sections 1, 3).
- Snapshot import: 367 objects in the first import; all 129 CAD parts uploaded as STEP; whole-aircraft full STEP 25.4 MB fails Compile with a socket error; lite 12.7 MB renders (sections 3, 5).
- Cost: AI chat none; object creation has embedding charges under one cent each per the billing page; the usage endpoint did not show them (section 4).
- Storage: 1 GB account limit hit, then raised to 50 GB; storage per object is the cost driver (sections 4, 5).
- Branch delete not possible with a personal token; needs a web (JWT) session (findings, AM-055 entry).
- Agreed workflow: Claude does reasoning, DaVinci stores and runs tools; the agent is never prompted (section 6).

## How we could use it
Context only. Its claims are cited in davinci-api-facts with the file they came from, not as independent evidence.
