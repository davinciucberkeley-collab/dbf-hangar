# Roadmap

Goal: hangar v1.0 is ready to demo on Wed 2026-12-02 (Present, next team meeting), with the core path below working end to end.

## Waves

- **W0 Seed, harness & ledger** (Fri 11-20 → Sat 11-21): seed hangar from aircraft-platform (U0.4), agent roster (U0.1), hooks and installer (U0.2), ledger (U0.3).
- **W1 Ops layer & PDL** (Sat 11-21 → Mon 11-23): operations registry (U1.1), MCP and Studio from the registry (U1.2), PDL v1.0 schema and migration (U1.3), edit/sweep/diff/propose (U1.4), claims graph and T9 gate (U1.5), connection library (U1.6).
- **W2 Gates, adapters, import, team ops** (Mon 11-23 → Wed 11-25): gate registry with T6, T7, T8 (U2.1), standards database (U2.2), tool adapters (U2.3), team-ops commands (U2.4), import of concept A (U2.5).
- **Async check-in** (Wed 11-25): `plane update publish`, link in the Drive doc. No meeting.
- **W3 One surface, skills, proof** (Wed 11-25 → Sat 11-28; Thu 11-26 light): Studio with modes (U3.1), skills on the ops layer (U3.2), PlaneBench v0 (U3.3), proof that an agent iterates concept A with no code edits (U3.4).
- **Freeze** (Mon 11-30 18:00).
- **W4 Review, release, presentation** (Mon 11-30 → Tue 12-01): whole-branch review, performance, release (U4.1), presentation package (U4.2).
- **Present** (Wed 12-02): demo and deck.

## Core path and cut order

Core path: U0.4 → U0.2/U0.3 → U1.1 → U1.3 → U1.4 → U1.5 → U2.5 → U3.4 (+ U4.1/U4.2). Core units are never cut.

Cut from the top as soon as a wave runs more than 12 h late. A cut unit is marked `dropped` in the ledger.

1. U3.3 PlaneBench: show the `design.sweep` table instead.
2. U2.1 T7/T8 parts: T7/T8 stay report-only through claims.
3. U2.2 source closing: the two `pending` thresholds become open decisions (D6).
4. U3.1 Build/BOM/Proofs/Morph modes: only Designs, Physics, Stress and Updates modes.
5. U2.3 optional adapters: `tools doctor` lists them as planned.
6. U1.6 connection library: attachments keep the v0.4 fields.

## Open decisions

- **D10**: Archive DBF-Combined and aircraft-platform (read-only) once hangar v1.0 is out? Default: yes, on 12-05, with a README pointer to hangar. Date: 12-01.

## Where to look

- [plan](plans/2026-11-20-standardization.md)
- [PROGRESS.md](PROGRESS.md) (live status, generated)
