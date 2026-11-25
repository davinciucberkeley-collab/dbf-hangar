---
id: davinci-live-reads-2026-11-24
title: DaVinci API live GET reads, Concept A project (2026-11-24)
authors: Celedon (DaVinci) API, read by W32-S
year: 2026
url: https://davinci-app.com/api/v2/ (GET routes listed per row)
type: website
retrieved: 2026-11-24
verified: true
---

## Summary
Read-only GET requests with the git-ignored personal access token (scopes include projects:read, usage:read). Covered usage, projects, branches, trees on main and on the snapshot branch, packages, project usage, one test, one constraint and one requirement. No POST, PUT, PATCH or DELETE was sent. The token value was not printed or written.

## Usable rules / numbers
- GET /usage: HTTP 200; body scope account, asOf null, amountUsd 0, eventCount 0. This differs from the DBF-Combined notes ($49.060351, 1,093 events, asOf 2026-11-09). Two readings on 2026-11-24 agreed.
- GET /projects: HTTP 200; keys owned, shared, organization. Owned list empty for this token. Shared list has "Concept A" (id bbb1b6e0-63d1-4a95-8e6d-0e300beed2c9), storageUsedBytes 1,056,091,993.
- GET /projects/{id}/branches: HTTP 200; names concept-a-snapshot-2aba012d and main.
- GET /projects/{id}/tree (default branch main): HTTP 200; objectCount 3; 2 package nodes.
- GET /projects/{id}/tree?branch=concept-a-snapshot-2aba012d: HTTP 200, 131,065 bytes; objectCount 652, 651 nodes returned. Types: package 20, item 53, attribute 232, part 6, requirement 51, test 11, constraint 6, geometry 261, assembly 11.
- GET /projects/{id}/packages: HTTP 200; key packages.
- GET /projects/{id}/usage: HTTP 200; scope project; totals all 0; eventCount 0; asOf null.
- GET /users/me/accounting: HTTP 401, code INVALID_TOKEN (refused with this token).
- GET object, test TP-1, snapshot branch: HTTP 200; keys include type, parent, shortName, name, status ("pending"), documentation.
- GET object, constraint HC-1 check, snapshot branch: HTTP 200; value "[id] <= 2000"; kind analysis; resolvedValue is an error: smallerEq expected Unit, got number.
- GET object, requirement HC-1, snapshot branch: HTTP 200; keys include satisfied (empty string) and satisfactionOutOfDate.
- One GET returned HTTP 503 with Retry-After 5; the retry returned 200.
- Response headers: RateLimit-Policy "500;w=1", RateLimit-Limit 500; RateLimit-Remaining falls with each call.

## How we could use it
Basis for the live-state section of davinci-api-facts. Re-read usage before any cost claim, since this reading disagrees with the notes.
