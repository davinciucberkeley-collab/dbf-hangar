# Disposition rules for the discipline extracts (conductor, 2026-11-21)

Every check row in `<role>.md` gets exactly one **lands as** code. Use only these codes.

## Codes
- `GATE:<id>` — a gate check. Use an existing id when it already covers the item, else one of the proposed ids below. Nothing else.
  - existing: T0.schema, T1.connectivity, T1.interfaces, T1.interference, T1.attachment, T2.fea_strength, T2.joint_load, T2.hover_moment, T3.mass, T3.hover_tw, T3.static_margin, T3.lateral_cg, T3.stall, T4.fits_machine, T4.method, T6.mechanism, T6.undriven, T7.assembly, T7.transport, T7.wiring, T8.bom, T8.budget, T8.program, T9.claims
  - proposed (new, max 8): T2.joint_rf, T2.load_case_coverage, T2.modal_separation, T3.control_authority, T3.transition_margin, T3.endurance, T7.thermal, T7.electrical_rating
- `STD:<file>#<key>` — a threshold that belongs in standards (file one of design-standards, manufacturing, connection-types, program, gate-thresholds, claims, or new: load-cases, operations). Give the value and its source if the extract has one, else `pending`.
- `SKILL:<skill>/<section>` — a judgment item a reviewer or design-engineer checks by reading. Skills (fixed list): review-structures, review-aero, review-mass, review-interfaces, review-controls (stability, avionics, flight software, RC link), review-propulsion (motors, props, power, energy, thermal), review-manufacturing (process, printing, composites, assembly), review-test-safety (ground/flight test, safety, go/no-go). Section = a short slug.
- `SCORECARD:<section>` — a rule for how reviews are run or closed (standards/review-scorecard.md). Sections: evidence-and-closure, discipline-sign-off.
- `KNOW:<topic>` — a procedure or reference worth keeping as a knowledge/ entry (topic slug, e.g. flight-card, ground-test-plan, build-sequence, procurement-lead-times).
- `DROP:<reason>` — reason one of: `k09l-instance` (a value claim about a specific K09-L part; the general rule, if any, is captured under another code — name it in the row), `k09l-only` (rule meaningful only for the retired K09-L configuration), `duplicate` (same rule as another row/role — name it), `covered` (already enforced by an existing hangar check or rule — name it), `generated-output` (renders, visuals, docs polish), `out-of-scope` (team logistics with no design consequence).

## Rule of thumb
- A numeric claim on a named K09-L part is `DROP:k09l-instance`; if it is one instance of a general rule (e.g. "every joint RF >= 1.0"), tag the **first** such row with the GATE/STD code and the rest `DROP:k09l-instance (rule: <code>)`.
- Prefer existing codes over proposed; prefer GATE over SKILL when the item is mechanically checkable from PDL data; SKILL when it needs judgment or data PDL does not hold.
- No new agents or roles. Leadership/integration items (decisions, change requests, traceability) map to `SCORECARD:` or `covered` (conductor, advisor, ledger, claims graph).
