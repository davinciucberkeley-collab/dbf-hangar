---
id: davinci-api-facts
title: DaVinci API facts for the hookup (T137, W32-S)
authors: W32-S scout (Haiku 5.5), from the sources listed
year: 2026
url: multiple (see Sources)
type: website
retrieved: 2026-11-24
verified: true
---

## Summary
Facts only. Sources: the DaVinci public OpenAPI spec (opened), 18 read-only GET calls to the Concept A project (2026-11-24), and the DBF-Combined docs on origin/redesign/v1 (read only). Source ids in square brackets name files in knowledge/sources/. Items with no source opened in this run are marked secondary.

## 1. Sources
- [davinci-openapi-v2]: public spec
- [davinci-live-reads-2026-11-24]: 18 GET requests, 0 writes
- [dbf-combined-davinci-api-summary], [dbf-combined-davinci-findings], [dbf-combined-davinci-mapping], [dbf-combined-davinci-research], [dbf-combined-davinci-import-2026-11-23], [dbf-combined-davinci-import-2026-11-24-json], [dbf-combined-davinci-step-parts-csv], [dbf-combined-tools-davinci-probe], [dbf-combined-tools-davinci-probe2]

## 2. Endpoints and what each returns (base https://davinci-app.com/api/v2)
| Route | Method | Shape / observed result | Source |
|---|---|---|---|
| /usage | GET | {scope, asOf, totals{amountUsd, promptTokens, completionTokens, reasoningTokens, cacheWriteTokens, cacheReadTokens, eventCount}}. Live 2026-11-24: all zero, asOf null | [davinci-live-reads-2026-11-24]; [davinci-openapi-v2] |
| /projects | GET | {owned[], shared[], organization{folders, placements, capabilities}}. Project keys include id, name, slug, owner, chargeMethod, visibility, storageUsedBytes | [davinci-live-reads-2026-11-24] |
| /projects/{id}/branches | GET | {branches: [names]} | [davinci-live-reads-2026-11-24] |
| /projects/{id}/tree?branch= | GET | {objectCount, tree: [{id, name, type, parent, childrenCount, shortName, subclassId}]}. ETag and If-None-Match supported. Default branch main | [davinci-openapi-v2]; [davinci-live-reads-2026-11-24] |
| /projects/{id}/packages | GET | {packages: [...]} | [davinci-live-reads-2026-11-24] |
| /projects/{id}/usage | GET | {scope: project, projectId, asOf, totals} | [davinci-live-reads-2026-11-24] |
| /projects/{id}/objects/{objectId}?branch= | GET | {object: {type, parent, shortName, name, status, documentation, ...}}. Constraint adds value, kind, resolvedValue. Requirement adds satisfied, satisfactionOutOfDate | [davinci-live-reads-2026-11-24] |
| /users/me/accounting | GET | 401 INVALID_TOKEN with this token. OpenAPI names it for limits and balances | [davinci-live-reads-2026-11-24]; [davinci-openapi-v2] |
| /projects/{id}/objects | POST | create objects (client-minted UUIDs, all or nothing; a commit persists them) | [dbf-combined-davinci-mapping] s2 |
| /projects/{id}/sessions/{sid}/tools/invoke | POST | runs one tool with no model; needs projects:write; spec says it incurs no LLM charges | [davinci-openapi-v2]; [dbf-combined-davinci-findings] s8 |
| /api/v1/file/upload/... | POST | data-plane file upload with a session grant; one file per call | [davinci-openapi-v2] ~line 3345; [dbf-combined-davinci-findings] |
| branch delete | DELETE | personal token refused (403 CREDENTIAL_NOT_PERMITTED); JWT only | [dbf-combined-davinci-findings] AM-055 entry (not re-run) |

Rate: observed header RateLimit-Limit 500, policy 500 per 1 s window [davinci-live-reads-2026-11-24]. DBF notes give 1 to 10,000 requests per minute, default 60 (secondary) [dbf-combined-davinci-findings] s2. One 503 with Retry-After 5 was seen [davinci-live-reads-2026-11-24].

## 3. Object types
34 writable types: action, assembly, attribute, capability, circuit, code, constraint, dashboard, document, entity, figure, geometry, interface, item, journey, linkage, material, matrix, package, part, port, reference, requirement, resource, risk, simulation, slide, state, table, task, test, toolbox, trade, transition [dbf-combined-davinci-mapping] s1 (2026-11-23 probe; not re-probed). Fields per type: same file s2. The 2026-11-24 tree shows these types in use: package, item, attribute, part, requirement, test, constraint, geometry, assembly.

## 4. Concept A today
Concept A has data on branch concept-a-snapshot-2aba012d; main holds only 2 packages [davinci-live-reads-2026-11-24].
Tree totals on the snapshot branch: objectCount 652; types package 20, item 53, attribute 232, part 6, requirement 51, test 11, constraint 6, geometry 261, assembly 11 [davinci-live-reads-2026-11-24]. The 2026-11-23 import reported 367 objects [dbf-combined-davinci-import-2026-11-23]; later commits added geometry and assemblies [dbf-combined-davinci-findings] (AM-058).

### 4a. Tests (11)
Pass/fail: no verdict was read for any test. The API exposes a test status (pending, started, done, cancelled, waived) [dbf-combined-davinci-mapping] s2. The only test read (TP-1) has status pending.

| shortName | name | state read |
|---|---|---|
| TP-1 | TP-1 Bench derate and one-motor current | status pending (read) |
| TP-2 | TP-2 Lua cap on the real FC | not read |
| TP-3 | TP-3 Pad drop | not read |
| TP-4 | TP-4 CF-in-Al bond | not read |
| TP-5 | TP-5 Tube interlaminar shear | not read |
| TP-6 | TP-6 **WITHDRAWN (D-225, 2026-11-21 | not read |
| TP-7 | TP-7 Printed joints | not read |
| TP-8 | TP-8 Glass skin | not read |
| TP-9 | TP-9 Pad friction drag | not read |
| TP-10 | TP-10 Tap test A-P10 / D-185 (a) | not read |
| TP-10b | TP-10b **T-A-TAP (D-233 A, T-085) | not read |

Note: TP-6 name carries "WITHDRAWN" with a decision reference (D-225) [live read].

### 4b. Requirements (51: 45 A-series, 6 hard constraints)
Satisfied state: requirement objects have a satisfied field and satisfactionOutOfDate. HC-1 read showed satisfied empty, not TRUE or FALSE [davinci-live-reads-2026-11-24]. The DBF mapping says satisfaction is computed from constraints (TRUE/FALSE/INCOMPLETE) [dbf-combined-davinci-mapping] s2 (secondary).

| shortName | name as stored (cut at 110 chars) |
|---|---|
| A-U1 | A-U1 Total physical spend <= $2,000 incl. tax, shipping, packs, charger, radio, test gear, tools, crash reserv |
| A-U2 | A-U2 Built and flight-tested by 2027-04-30 |
| A-U3 | A-U3 Transport: multi-piece allowed; must fit **one car trunk, two pieces at most**; team of 4 carries it |
| A-U4 | A-U4 3-D gates (CLAUDE.md wording "3-D physics simulation"; computed: interference check, static, at neutral a |
| A-U5 | A-U5 Mass < 25 kg (55 lb) |
| A-U6 | A-U6 CAD fidelity: every part modelled to its real shape and dimensions from the vendor drawing or data sheet  |
| A-U7 | A-U7 Limit exposed wiring: wires inside the arm tubes, wing-core channels, fairings or covers; every wire left |
| A-D1 | A-D1 Scaled quad tailsitter: 0.90 x 0.245 m wing, 2 fins, 4 fixed SunnySky X2216 V3 short-shaft 880KV (D-227,  |
| A-D2 | A-D2 Mission: 3.0 min hover-mode incl. 40 s go-around, 3.41 min cruise at 17 m/s (requirement 3.5), 20 % reser |
| A-P1 | A-P1 [T-084 update 2026-11-22: the gate still fails at 1,633.0 g drawn, tallied predicted **1.8796 kg** EST, C |
| A-D3 | A-D3 Design target <= **1.46 kg** predicted incl. growth and overrun (D-195, QP-5: was 1.44; now 1.449 kg item |
| A-P2 | A-P2 Hover T/W >= 2.0 fresh, >= 1.6 worst pack state (20 % rest, 3.73 V/cell); hover throttle <= 0.625 |
| A-P3 | A-P3 Transition entry window >= +-5 % of the weight-ratio entry thrust (R2 floor) by a time-domain pitch-over  |
| A-P4 | A-P4 Static margin >= 5 % chord; CG **19-26 mm** aft of LE (D-195: forward edge 20 -> 19 because the CAD CG 21 |
| A-D4 | A-D4 Pack accepted at <= listed + 5 g (Tattu 2300: 270 g, 275 g; 2,800 mAh pack 270 g listing per BOM-T083b.cs |
| A-P5 | A-P5 Pack retained at 12 g crash decel (1.2 m/s on 6 mm crush) |
| A-D5 | A-D5 Crash reserve = pack + motor + servo + full airframe set beyond spares, x 1.1025 + 3 shipments; FC and ES |
| A-D6 | A-D6 One BOM, one mission, one gate shared by all A reports; per-subsystem cost caps in `bom_a.py` |
| A-P6 | A-P6 Clean stall Vs <= cruise / 1.3 at the gate mass: Vs 12.07 m/s at 1.47 kg, 1.3 Vs 15.69 < 17 m/s cruise (1 |
| A-P7 | A-P7 Hover yaw authority >= **0.35 N m** at +-0.10 throttle (fail < 0.30 N m: the hover wind card is reopened) |
| A-P8 | A-P8 Wind (D-192): hover and loiter **<= 4 m/s mean (RCMC1 basis, rescaled by the H3 RFS ratio), gust <= 6.4 m |
| A-P8a | A-P8a **Heading rule (D-184):** hover and loiter with the wing edge into the wind within +-10 deg by pilot yaw |
| A-P9 | A-P9 Landing on fin tips: static tip-over >= 30 deg (33.2 deg `EST`; **[T-084, D-233: drawn pads, FIN_H 0.1937 |
| A-P10 | A-P10 **Vibration (D-185, BOARD QP-3 s3).** (a) No strongly coupled mode (motor coupling cx or cy >= 0.5, the  |
| A-P11 | A-P11 Cruise control: elevons **y 0.04-0.34 m each side, stops +-20 deg** (the drawn part; the SITL plant had  |
| A-P12 | A-P12 Cruise prop chosen on the bench with hover T/W still >= 2.0 fresh at the gate |
| A-P13 | A-P13 Loads: limit +3.4 / -1.5 g floor, ultimate 1.5 x limit, MS >= 0 on spar, cage, fin root at 1.5 x limit;  |
| A-P14 | A-P14 Airspeed error <= 0.5 m/s at cruise; pitot outside rotor wash |
| A-P15 | A-P15 Directional stability Cn_beta >= 0.03 /rad; no spiral divergence (fins + wing) |
| A-P16 | A-P16 Winding and ESC current <= rating: motor 13 A / 180 s; `Q_M_SPIN_MAX` 0.90 required: APC 9x4.5MR uncappe |
| A-P17 | A-P17 Harmonic notch on hover 1P **100-119 Hz** (`INS_HNTCH_FREQ` 105, BW 40, in A.param). `MODE` 3 (rpm) only |
| A-P18 | A-P18 Thermal limits from maker; BEC >= 2 x servo stall; compass interference <= 30 % at hover current; HDOP < |
| A-P19 | A-P19 Arm and hard kill stop all motors <= 1 s; ELRS LQ >= 0.9; RC loss in a Q mode -> QLAND; failsafes |
| A-P25 | A-P25 Flight-control settings frozen for the tether (D-186): `THR_MAX` 68 with `FWD_BAT_VOLT_MAX/MIN` 16.8 / 1 |
| A-P20 | A-P20 **Any motor out in hover: not survivable** (4 fixed rotors in an X); controls: motor test before every f |
| A-P21 | A-P21 Param file passes the firmware-name check; tailsitter frame name `UNVERIFIED` until read in `vehicleinfo |
| A-P22 | A-P22 Harness: supports <= 0.15 m, chafe, strain relief at motors; mass from the routed harness |
| A-P23 | A-P23 Battery handling: LiPo bag, charge 10-45 C, no re-flying a part-used pack |
| A-D7 | A-D7 Test order, no gate skipped: SITL crosswind hover, M1 thrust stand, M3 hanging yaw, M4 fin tap, M5 CG bre |
| A-D8 | A-D8 First tethered hover by 2027-02-18 (R4 trigger, revised by BOARD QP-3: the SCHEDULE-A latest-safe date; 0 |
| A-D9 | A-D9 >= 10 h SITL on the tailsitter model with A's param file before first hover; stick time on a small quad |
| A-P24 | A-P24 Site and law: RFS yellow fields, FRIA, VLOS <= 500 m, <= 400 ft, spotter, request >= 7 business days ahe |
| A-D10 | A-D10 Transport drop 0.3 m, <= 6 kg loaded; field setup <= 5 min one person (props on, one piece) |
| A-D11 | A-D11 Print bed 0.2 m; thread engagement; claims graph without failing claims |
| A-D12 | A-D12 Wind measured at the field before each sortie |
| HC-1 | Budget: $2,000 total physical spend |
| HC-2 | Schedule: built and flight-tested by end of April 2027 |
| HC-3 | Portable: under 25 kg, fits one to two car trunks |
| HC-4 | 3-D physics gates, no exemptions |
| HC-5 | CAD fidelity |
| HC-6 | Enclosed wiring |

### 4c. Constraints (6, one per hard constraint, named "HC-n check")
- HC-1 check: value "[BOM total id] <= 2000", kind analysis. resolvedValue is an error: smallerEq expected Unit, got number [davinci-live-reads-2026-11-24]. The check does not resolve to TRUE or FALSE.
- HC-2 to HC-6: not read. The DBF import doc says HC-2, HC-4, HC-5 and HC-6 are inspection checks with text only, and HC-3 is an equation "[Aircraft mass] <= 25000" [dbf-combined-davinci-import-2026-11-23] (secondary).

## 5. Analysis tools (secondary: [dbf-combined-davinci-research] s3)
- Simulation: SetupSimulation, CompileSimulation, QuerySimulation, OptimizeSimulation, VerifySimulation, CaptureSimulationView, QueryOptics, ExportSimulationPlot, GetSimulationReference, RunSimulation.
- Geometry: MeasureModel (distances, bounding boxes, volumes).
- Other toolboxes: Requirements Engineering, Constraints and Verification, Attributes and Analysis, Risk Management, Parts and Components, Documents, Tasks, Entities and Relationships, Circuits and Electronics, Software Engineering, Source Control.
- Physics: certified steady thermal, linear statics, thermo-elastic; gate-validated modal, harmonic, random vibration, shock, transient thermal and structural, laminar flow, optics; system multibody, networks, controls, contact dynamics.
- Not offered: aerodynamics beyond laminar CFD, flight dynamics, a landing-gear tool.
- The API has no route that lists tools; the list depends on the session's project. W32-S did not call invokeTool (POST not permitted in this task).

## 6. Geometry and CAD: can DaVinci hold STEP?
- Yes, as a geometry object of kind step (kinds per docs: code, step, onshape) [dbf-combined-davinci-mapping] s2.
- Upload: POST /api/v1/file/upload/... with a data-plane grant from an open session [davinci-openapi-v2] ~line 3345; used on 2026-11-24 [dbf-combined-davinci-findings].
- Done in Concept A: 129 part STEPs uploaded; 129 geometries, 0 missing, 0 duplicates; storage 396,073,794 bytes for 23.6 MB of STEP, about 17x [dbf-combined-davinci-findings] AM-058.
- Assembly of 10 sub-assemblies: uploaded; does not render; Compile says "source is required" [dbf-combined-davinci-findings].
- Whole-aircraft STEP: full 25.4 MB fails Compile (socket hang up); lite 12.7 MB renders, per Dillon's report [dbf-combined-davinci-api-summary] s3-5.
- The 2026-11-23 mapping doc said geometry upload was not found; superseded by the 2026-11-24 uploads [dbf-combined-davinci-mapping] s4-5 vs [dbf-combined-davinci-findings].
- Faceted (mesh-based) CAD, not a solid B-rep [dbf-combined-davinci-api-summary] s5.

## 7. Cost facts
- Usage endpoint, live 2026-11-24: amountUsd 0, eventCount 0, asOf null [davinci-live-reads-2026-11-24]. DBF notes: amountUsd 49.060351, 1,093 events, asOf 2026-11-09 [dbf-combined-davinci-findings] s7-8. These disagree; resolved in section 10.
- invokeTool: no LLM charge per spec [davinci-openapi-v2].
- Object creation: an embedding charge under one cent each, per the billing page as quoted in DBF notes [dbf-combined-davinci-api-summary] s4 (secondary). The balance did not visibly change across the imports (same source).
- Storage is the main cost driver. The 1 GB limit was hit, then raised to 50 GB [dbf-combined-davinci-api-summary] s4-5 (secondary; not checked via API). Concept A storage read 1,056,091,993 bytes [davinci-live-reads-2026-11-24].
- Soft-deleted projects release storage from the owner's balance per spec [davinci-openapi-v2] ~line 473. The DBF notes say a deleted project's storage still counted until admin cleanup [dbf-combined-davinci-findings] AM-056.
- Plan prices (secondary): Free $0; Core $20 per month; Max $200 per month; Group $40 per user per month [dbf-combined-davinci-research] s5.

## 8. Limits
- Token: expiry at most 90 days; rate 1 to 10,000 per minute, default 60 (secondary) [dbf-combined-davinci-findings] s2.
- Branches: branch delete not possible with a personal token (JWT only) [dbf-combined-davinci-findings] AM-055. Keep branches few.
- Storage: 1 GB account limit returned 413 STORAGE_LIMIT_EXCEEDED; raised to 50 GB (secondary) [dbf-combined-davinci-findings] AM-056.
- Relationships over REST: not found [dbf-combined-davinci-mapping] s2; the import did not create test-to-requirement links [dbf-combined-davinci-import-2026-11-23].
- Usage reads are eventually consistent [davinci-openapi-v2] ~line 3110.
- Object names: the objectName sent with an upload was not applied; the file name was used [dbf-combined-davinci-api-summary] s5.
- Assembly source format undocumented; no object-update endpoint found [dbf-combined-davinci-findings] AM-056.

## 9. DBF-Combined mapping proposal (from [dbf-combined-davinci-mapping] s4; a proposal, not a decision)
| Our source | DaVinci object | Parent |
|---|---|---|
| BOM-A.csv line | part with Qty, Spares, Unit cost attributes; source_url and date_checked in a reference | Procurement / subsystem |
| BOM total and budget | resource with a constraint on the total | Procurement |
| cad_mass.json scalars | attributes on the aircraft part | Design / Aircraft |
| per-part mass and CG (viewer data) | child attributes on each part | the part |
| params-A.json groups | package per group, attribute per parameter | Design / Parameters |
| REQUIREMENTS-A rows, hard constraints | requirement (shortName = ID) with constraint children | Requirements |
| TEST-PLAN-O4B TP-n | test (shortName = TP-n); verify link not creatable over REST | Verification |
| proof-graph claim | constraint with a value attribute | Requirements |
| proof-graph calculation | code object (python) | Verification / Calculations |
| decision D-entry | document (shortName = D-nnn) | Decisions |
| CAD geometry | geometry (kind step) per part | the part |

## 10. Discrepancies and open items (facts only)
- Usage: live 2026-11-24 read is 0 / 0 events / asOf null [davinci-live-reads-2026-11-24]; DBF notes read $49.060351 / 1,093 events / asOf 2026-11-09 [dbf-combined-davinci-findings]. RESOLVED (Tristan, chat 2026-11-24): Tristan and Dillon use separate API keys on separate accounts while working on the same project, so /usage reports only the token owner's account. The two readings are from different accounts, not a conflict in one account's data. Source: Tristan, chat 2026-11-24 (not a DaVinci document).
- Tree objectCount 652, but 651 nodes returned [davinci-live-reads-2026-11-24]. Not explained.
- The 131-part 3-D import (2026-11-23) was in API Test, now deleted; the Concept A snapshot shows 6 part objects [dbf-combined-davinci-import-2026-11-23] vs [davinci-live-reads-2026-11-24].
- Geometry count 261 on the snapshot. The DBF notes imply 129 part STEPs + 129 assembly copies + whole-aircraft STEPs; this is an inference, not checked object by object.
- Only TP-1 (test), the HC-1 constraint and the HC-1 requirement were read in full.
- /users/me/accounting returned 401 with this token; not resolved.
- The DBF-Combined probe scripts were not run; probe2 contains POST and DELETE calls on scratch branches [dbf-combined-tools-davinci-probe2].

## How we could use it
- Facts for the DaVinci hookup decision (T137, R29, D3). Re-read usage before any cost claim.
