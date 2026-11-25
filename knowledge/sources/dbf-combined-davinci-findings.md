---
id: dbf-combined-davinci-findings
title: DBF-Combined: DaVinci findings (T-037) docs/integration/davinci-findings.md
authors: DBF-Combined project (author not stated)
year: 2026
url: origin/redesign/v1:docs/integration/davinci-findings.md
type: website
retrieved: 2026-11-24
verified: true
---

## Summary
Chronological log of probes, imports and limits on DaVinci, with the raw numbers for each step. Sections read: 1, 2, 7, 8 and the later 2026-11-24 entries (branch delete, Concept A import, STEP upload and assembly).

## Usable rules / numbers
- Probe 1 (read-only, 2026-11-23): GET usage $49.06, 1,093 events, asOf 2026-11-09; project list; tree of 10 objects (section 7).
- Probe 2: scratch branch created, session opened, one requirement added and read back via invokeTool, object deleted, session closed; usage unchanged (section 8).
- Concept A import: branch concept-a-snapshot-2aba012d; every POST 201 (AM-056 entry).
- All 129 part STEPs uploaded: 129 geometries, 0 missing, 0 duplicates; storage 396,073,794 bytes for 23.6 MB of STEP, about 17x (AM-058 entry).
- Branch delete via API: 400 BRANCH_NOT_FOUND on the path form; 403 CREDENTIAL_NOT_PERMITTED on the query form (only jwt allowed) (AM-055 entry).
- Storage: a 1 GB account limit returned 413 STORAGE_LIMIT_EXCEEDED; the deleted project's storage still counted until admin cleanup (AM-056 entry).
- Spend caveat in the file: usage asOf stayed 2026-11-09, so equal before/after values are not proof of $0 (fix pass C, R13-3).

## How we could use it
Source for the limits and the cost-measurement method. Its usage figures conflict with the live read of 2026-11-24; see davinci-api-facts section 10.
