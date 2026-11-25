---
id: dbf-combined-davinci-mapping
title: DBF-Combined: DaVinci mapping spec (T-037) docs/integration/davinci-mapping.md
authors: DBF-Combined project (author not stated)
year: 2026
url: origin/redesign/v1:docs/integration/davinci-mapping.md
type: website
retrieved: 2026-11-24
verified: true
---

## Summary
Object types and per-type fields as found by a live validator probe (all writes refused, so nothing was created on 2026-11-23). Proposes how concept A files map to DaVinci objects.

## Usable rules / numbers
- 34 writable object types, listed in section 1 (from a 400 response with validTypes).
- Common fields: type, parent, name, shortName, documentation, children, tags (tags assigned after creation). Requirement has satisfied; constraint has value and kind (inspection, analysis, similarity, test, sampling); test has status (pending, started, done, cancelled, waived) and weight (section 2).
- Relationship creation over REST: not found; the base relationship set is listed (section 2). The import did not create test-to-requirement links.
- Geometry upload: this doc (2026-11-23) says not found; superseded by the 2026-11-24 STEP uploads in davinci-findings.
- Proposed layout: Model / Concept A with Requirements, Design, Procurement, Verification and Decisions packages; parts with mass and CG as child attributes (sections 3-4).
- Open: inner shape of test procedure, document body and table rows (section 5).

## How we could use it
Source for the proposed object mapping in davinci-api-facts section 9. Proposal only; not a decision.
