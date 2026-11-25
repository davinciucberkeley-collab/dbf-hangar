# U17.1 step 1: inventory of unsourced gate thresholds (W34-T2, D88)

Built on `main` f83a70b (checked against b990cbe). Rows driven come from `plane design validate designs/<id> --json` run once per design (8 designs: c0-a1, c0-a2, c0-a3, c0-lift-cruise, concept-a, concept-a-param, example-tailsitter-wing, tiltwing-cakir), counted with the same rule as `core/hangar/gates/fidelity.py`: a blocking row counts as sourced when its criterion `file#key` resolves and its `source` is not exactly `pending` or `internal convention` (`_UNSOURCED`). Fidelity before (sourced of blocking rows): c0-a1 6 of 260, c0-a2 6 of 233, c0-a3 6 of 277, c0-lift-cruise 6 of 233, concept-a 134 of 715, concept-a-param 99 of 692, example-tailsitter-wing 5 of 61, tiltwing-cakir 5 of 130; total 267 of 2601.

## Three findings the plan did not state

1. **Library values move no rows.** `T2.joint_load` and `T2.sim_drop_loads` read each joint's own rating, not `connection-types.yaml` (U8.3, D67, D68). Only `T2.joint_rf` (report-only) and `T7.electrical_rating` read the library. Sourcing a connection type changes 0 blocking rows; sourcing a criterion key changes the fidelity line for every row that names it.
2. **518 blocking rows have a criterion that cannot resolve to a threshold**, whatever the standards say: `manufacturing.yaml` (313), `manufacturing.yaml#jacobs-fdm` (157), `#jacobs-fdm-fortus` (6), `#jacobs-laser` (5) = 481 `T4.*` rows; `schema/plane.schema.json` 27; `requirements.mtow_g` 8; `connection-types.yaml` 2. Fixing this is a `core/` or criterion change (for example `resolve_threshold` for machine entries), not a standards edit. Conductor decision; no scout packet.
3. **The fidelity test is a string match.** Any `source` text other than exactly `pending` or `internal convention` counts as sourced (for example `aero.control_surface_gap_max_fraction`, whose text says "value internal convention", and the 20 "team constraint" entries already count). So the builder writes a source string only when an opened source or a written derivation exists; relabelling to move the line is a defect the reviewer checks.

Also: `gates.yaml` flips the discipline checks (T2.joint_rf, T3.control_authority, T3.transition_margin, T3.endurance, T7.electrical_rating, T3.wing_loading, T3.cruise_stall_ratio) and tiers 7 and 8 from report-only to blocking on 2026-12-08, so their rows are shown in the "report-only rows" column.

## Classes
- **EXT n**: externally sourceable; scout packet n (`briefs/U17.1-packet-n.md`).
- **DER**: needs a written derivation from sourced values or a measurement already in the repo; no scout; the conductor assigns it.
- **TEAM**: team decision: needs a named owner and date, not an external source. Not sent to scouts.
- **NUM**: numerical or method parameter; keep with the stated reason.
- **HELD**: waits on a named measurement.
- **NONE**: no load rating is meaningful for the type; leave pending with the reason (the conductor may mark `structural: false`).

## Counts
96 entries (a connection type counts one each). By current source text: pending 43, internal convention 30, team constraint or team statement 20, other non-external (DBF-Combined code or label, method choice) 3. By class: team decision 21, held 1, derivation 7, numerical keep 6, no-rating connection types 8, externally sourceable the rest (placed in packets 1 to 9; 20 connection types in packets 5, 8, 9 move 0 blocking rows).

## A. Ranked by blocking rows driven (criterion rows, all 8 designs)
"Blocking rows" = rows in blocking gates whose criterion names the key. "FAIL/SKIP" = how many of them are not PASS/WARN. "Also read by" lists check families whose numbers the key changes without being the row's criterion (row totals over the 8 designs).

| rank | file#key | value, units | current source | class | check ids (criterion) | blocking rows | FAIL/SKIP | also read by (rows) |
|---|---|---|---|---|---|---|---|---|
| 1 | design-standards.yaml#structure.landing_load_factor | 3.0 (-) | pending | HELD (T113 drop test, D68; U8.3 X1 found no opened source) | T2.joint_load, T2.sim_drop_loads | 1102 | 69 FAIL, 128 SKIP | T2.joint_rf 278 (220 WARN, report-only) |
| 2 | design-standards.yaml#geometry.attach_tolerance_mm | 2.0 mm | internal convention | EXT 1 | T1.attachment, T1.attachment_contact, T1.connectivity, T1.articulation, T1.point_mass_location | 565 | 3 FAIL | - |
| 3 | design-standards.yaml#geometry.interference_max_mm3 | 1.0 mm^3 | internal convention | DER (inputs from packet 1) | T1.interference, T1.pocket, T1.pose, T1.watertight | 54 | 32 FAIL | T6 contact 14 |
| 4 | design-standards.yaml#geometry.prop_chain_max_intermediate_parts | 2 (parts) | internal convention | TEAM | T1.motor_has_prop | 37 | 0 | - |
| 5 | gate-thresholds.yaml#mechanism_ratio_tol | 0.05 (fraction) | internal convention | EXT 1 | T6.ratio, T6.mechanism, T6.link | 14 | 2 FAIL (6 WARN) | - |
| 6 | design-standards.yaml#geometry.embed_max_fraction_of_child | 0.35 (fraction of child volume) | internal convention | TEAM | T1.attachment_overlap | 8 | 8 FAIL | containment_min_fraction (same family, 10 rows) |
| 7 | design-standards.yaml#aero.hover_moment_pass_ratio | 0.2 (fraction of thrust x lever) | internal convention | EXT 3 | T2.hover_moment | 8 | 0 (1 WARN) | hover_moment_fail_ratio and hover_moment_reference_lever_m (same 8) |
| 8 | design-standards.yaml#sim.drop_height_m | 0.3 m | internal convention | EXT 6 | T2.sim_stable | 8 | 0 | T2.sim_drop_loads 551 (drop-derived loads), T2.fea_strength 41 |
| 9 | design-standards.yaml#aero.lateral_cg_max_fraction_span | 0.02 (fraction of span) | internal convention | DER | T3.lateral_cg | 8 | 0 | - |
| 10 | design-standards.yaml#sim.rest_speed_max_mps | 0.05 m/s | internal convention | NUM (packet 6 adds context) | T2.sim_rest | 6 | 0 | - |
| 11 | design-standards.yaml#sim.tip_angle_max_deg | 30.0 deg | internal convention | EXT 6 | T2.sim_rest | 2 | 2 FAIL | - |
| 12 | design-standards.yaml#aero.planform_match_tolerance_fraction | 0.01 (fraction) | internal convention | EXT 1 | T3.planform_matches_geometry | 2 | 0 (2 WARN) | - |
| 13 | design-standards.yaml#geometry.glued_overlap_max_fraction | 0.02 (fraction of smaller part) | internal convention | TEAM | T1.attachment_overlap | 2 | 2 FAIL | - |

Criterion-less rows (finding 2): manufacturing.yaml family 481 (4 FAIL, all `jacobs-fdm-fortus`: four motor parts 55.7 x 55.7 x 297 mm against a 256 mm floor on tiltwing-cakir), schema 27 (16 SKIP), mtow 8, connection-types 2.

## B. Keys with no criterion row of their own (ordered by rows they change, then report-only rows)

| file#key | value, units | current source | class | check ids that read it | rows changed (8 designs) | report-only rows (blocking from 2026-12-08) |
|---|---|---|---|---|---|---|
| design-standards.yaml#sim.duration_s | 2.0 s | internal convention | NUM | T2.sim_stable 8, T2.sim_rest 8, T2.sim_drop_loads 551 | 567 | - |
| design-standards.yaml#structure.fea_singularity_band_mm | 2.0 mm | "method choice, not a standard" (Saint-Venant) | DER (packet 7 finds a textbook for the principle) | T2.fea_strength (4 FAIL, 6 SKIP of 41) | 41 | - |
| design-standards.yaml#geometry.strip_gap_tolerance_mm | 3.0 mm | internal convention | DER | planform and wing area feeding T3.planform_matches_geometry 2, T3.stall 8, T3.static_margin 8 | 18 | T3.wing_loading 8 |
| design-standards.yaml#aero.control_surface_gap_max_fraction | 0.15 (fraction of chord) | "standard planform definition ... value internal convention" (counts as sourced) | DER (concept A 23.6 mm = 9.6 % is the written input) | same as strip_gap | 18 | - |
| design-standards.yaml#aero.planform_strip_count | 41 | internal convention | NUM | same | 18 | - |
| design-standards.yaml#geometry.articulation_sweep_step_deg | 15 deg | internal convention | NUM | T1.pose 6, T1.articulation 10 | 16 | - |
| gate-thresholds.yaml#mechanism_abs_tol_deg | 0.5 deg | internal convention | EXT 1 | T6.ratio, T6.mechanism | 14 | - |
| design-standards.yaml#geometry.containment_min_fraction | 0.99 | internal convention | TEAM | T1.attachment_overlap | 10 (8 FAIL) | - |
| design-standards.yaml#aero.aft_surface_efficiency | 0.9 | internal convention | EXT 2 | T3.static_margin (6 FAIL of 8) | 8 | - |
| design-standards.yaml#aero.hover_moment_fail_ratio | 1.0 | internal convention | EXT 3 | T2.hover_moment | 8 | - |
| design-standards.yaml#aero.hover_moment_reference_lever_m | 0.05 m | internal convention | EXT 3 | T2.hover_moment | 8 | - |
| design-standards.yaml#geometry.distributed_mass_max_fraction_each | 0.03 | internal convention | TEAM | T1.point_mass_location | 4 | - |
| design-standards.yaml#geometry.distributed_mass_max_fraction_total | 0.05 | internal convention | TEAM | T1.point_mass_location | 4 | - |
| gate-thresholds.yaml#mechanism_contact_step_deg | 1.0 deg | internal convention | NUM | T6.mechanism | 4 | - |
| design-standards.yaml#aero.planform_area_mismatch_fail_fraction | 0.15 | internal convention | DER | T3.planform_matches_geometry | 2 | - |
| design-standards.yaml#aero.planform_axis_tolerance_deg | 5 deg | internal convention | NUM | T3.planform_matches_geometry | 2 | - |
| gate-thresholds.yaml#wire_clearance_mm | 5.0 mm | pending (D5, Dillon gave none) | EXT 5 | T7.wiring.* | 0 | 28 WARN |
| gate-thresholds.yaml#bom_verified_max_age_days | 30 days | internal convention | TEAM | T8.bom.* | 0 | 95 (32 WARN) |
| gate-thresholds.yaml#transport_box_mm | [1250, 550, 450] mm | team constraint (K09-L box) | TEAM | T7.transport.packed-airframe | 0 | 2 WARN |
| gate-thresholds.yaml#servo_must_drive_mechanism | true | pending (team expectation) | TEAM | T6.undriven | 0 | 2 WARN |
| gate-thresholds.yaml#wing_area_complete_min | 0.97 | pending (internal expectation) | DER (U13.7-5: measured within 0.1 %) | T3.wing_area_complete (no row in the 8 runs) | 0 | 0 |
| fixed-wing.yaml#wing_loading_max_g_dm2 | 100.0 g/dm^2 | pending | EXT 2 | T3.wing_loading | 0 (SKIP on all 8: no fixed-wing design) | 8 SKIP |
| fixed-wing.yaml#fw_static_margin_max | 0.25 (fraction MAC) | pending | EXT 2 | T3.static_margin (fixed-wing only) | 0 | 0 |
| fixed-wing.yaml#cruise_to_stall_ratio_min | 1.3 | team constraint (DBF-Combined params-A) | EXT 2 | T3.cruise_stall_ratio | 0 | 8 SKIP |
| load-cases.yaml#joint_rf_min | 1.0 | internal convention (definition) | EXT 6 | T2.joint_rf | 0 | 278 (220 WARN) |
| operations.yaml#electrical_rating_min_ratio | 1.0 | internal convention (definition) | EXT 5 | T7.electrical_rating | 0 | 14 (10 WARN) |
| operations.yaml#hover_ctrl_factor | 1.5 | team constraint (DBF-Combined params.json) | EXT 3 | T3.control_authority | 0 | 22 (10 WARN) |
| operations.yaml#transition_thrust_fraction_max | 0.8 | team constraint (DBF-Combined ASM-B1-CTRL-RESERVE) | EXT 3 | T3.transition_margin | 0 | 8 (5 WARN) |
| operations.yaml#transition_stall_ratio_min | 1.2 | pending (no extracted value) | EXT 2 | T3.transition_margin | 0 | 8 (8 WARN) |
| operations.yaml#energy_reserve_fraction | 0.2 | team constraint (DBF-Combined A2 row 53) | EXT 4 | T3.endurance | 0 | 8 (6 WARN) |
| operations.yaml#mission_hover_min | 2 min | team constraint | TEAM (mission, D74) | T3.endurance | 0 | 8 |
| operations.yaml#mission_cruise_min | 5 min | team constraint | TEAM (mission, D74) | T3.endurance | 0 | 8 |
| operations.yaml#hover_wind_mps | 5 m/s | pending (A2 extract row 8: "wind moment (5 m/s)") | TEAM (requirement) | T3.control_authority | 0 | 22 |
| operations.yaml#wind_drag_coefficient | 1.2 (-) | pending (bluff body) | EXT 2 | T3.control_authority | 0 | 22 |
| operations.yaml#wind_moment_min_lever_fraction | 0.25 | pending (fraction of frame height) | EXT 3 | T3.control_authority | 0 | 22 |
| operations.yaml#pack_sag_fraction | 0.15 | pending | EXT 4 | T3.control_authority, T3.transition_margin | 0 | 38 |
| operations.yaml#propulsive_efficiency | 0.5 | pending | EXT 4 | T3.endurance | 0 | 8 |
| operations.yaml#battery_usable_fraction | 0.8 | pending | EXT 4 | T3.endurance | 0 | 8 |
| operations.yaml#lipo_nominal_cell_v | 3.7 V | pending | EXT 4 | T3.endurance | 0 | 8 |
| claims.yaml#recompute_rel_tol | 1e-6 | DBF-Combined proofs/SCHEMA.md (team schema; counts as sourced) | NUM (keep) | T9.claim.* | 186 PASS | - |
| materials.yaml#material_density_g_cm3 cfrp-tube | 1.6 g/cm^3 | DBF-Combined amodel/common.py (team code) | EXT 7 | mass_model of generated parts (concept-a-param) | every mass row of a generated part | - |
| materials.yaml#material_density_g_cm3 xps-foam | 0.025 g/cm^3 | DBF-Combined amodel/wing.py label "XPS 25 kg/m3" | EXT 7 | same | same | - |
| manufacturing.yaml jacobs-fdm-fortus build_volume_mm | [256,256,256] mm | team statement 2026-11-11 (floor, not published) | EXT 7 | T4.fits_machine | 6 (4 FAIL; criterion unresolvable) | - |
| manufacturing.yaml jacobs-fdm-lulzbot build_volume_mm | [256,256,256] mm | team statement 2026-11-11 | EXT 7 | T4.fits_machine | 0 now | - |
| manufacturing.yaml jacobs-fdm (Prusa, model not stated) build_volume_mm | [256,256,256] mm | team statement 2026-11-11 | TEAM (Jacobs staff must name the model) | T4.method, T4.fits_machine | 157 PASS | - |
| manufacturing.yaml machine_optional_methods | list | team statement 2026-11-11 | TEAM | T4.method | 313 PASS | - |

## C. program.yaml (all TEAM: owner and date needed)
`constraints.budget_usd` 2000 USD (T8.program.budget, 6 WARN of 8, report-only); `deadline` 2027-04-30; `mass_cap_kg` 25 kg (also bounded by 14 CFR 107.3, 24947 g, already sourced); `transport_pieces_max` 2; `transport_box_mm` [1250,550,450] mm (default box, trunk not measured); `physics_pass` true; `cad_real_parts` true; `exposed_wiring_minimised` true. All sourced as "team constraint ... DBF-Combined CLAUDE.md @ a93f14d" (counts as sourced in the fidelity code). None goes to a scout. The owner of each row is the conductor's call (Tristan or Dillon), with a date.

## D. connection-types.yaml: 29 pending types (library edits move 0 blocking rows; they feed T2.joint_rf and, once a design joint is rewritten, the joint gates)
Joints per type are the same in concept-a and concept-a-param (142 joints each). "own-placeholder" = joints whose own `rating_basis` is placeholder (their joint_load and sim_drop_loads rows are SKIP, 2 rows per joint per design).

| type | joints per design | own-placeholder joints | SKIP rows (2 designs) | class |
|---|---|---|---|---|
| CT-PITOT-TUBING | 4 | 4 | 16 | EXT 9 (U8.3 found none; retry only with a new source type) |
| CT-GEL-PAD | 2 | 2 | 8 | EXT 9 (as above) |
| CT-A-PROP-NUT | 8 | 0 (derived) | 0 | EXT 8 |
| CT-HW-SEATED | 7 | 0 | 0 | NONE |
| CT-A-M25-SHCS-MOTOR | 4 | 0 | 0 | EXT 8 |
| CT-A-PROP-ADAPTER | 4 | 0 | 0 | EXT 8 |
| CT-SERVO-SPLINE | 2 | 0 | 0 | EXT 9 |
| CT-CLEVIS | 2 | 0 | 0 | EXT 9 |
| CT-PIN-HINGE, CT-TUBE-CLAMP, CT-M2-SCREW-PLASTIC, CT-TAPE-SKIN | 0 | 0 | 0 | EXT 9 |
| CT-PROP-ADAPTER, CT-PROP-NUT, CT-A-M3-CSK-MOTOR, CT-A-M3-BOLT-MOUNT | 0 | 0 | 0 | EXT 8 |
| CT-AS150U (75 A, pending), CT-BULLET-3, CT-SOLDER-PHASE, CT-SOLDER-DC, CT-SERVO-JR | 0 | 0 | 0 | EXT 5 |
| CT-STRAP-SLOT, CT-CRADLE-CONTACT, CT-PLUG-IN, CT-LABEL, CT-WIRE-CHANNEL, CT-ELRS-RF, CT-THERMAL-PAD, CT-THERMAL-CONTACT | 0 | 0 | 0 | NONE (no meaningful load rating; leave pending with the reason) |

Already sourced and out of scope: CT-EPOXY, CT-CA, CT-TAPE-FOAM, CT-STRAP-VELCRO, CT-HATCH-HL, CT-TIE, CT-TAPE-HINGE, CT-M3-*, CT-M4-*, CT-XT60, CT-XT90, CT-MR30, CT-JST-GH-*; also `wire_ampacity_a`, `wire_pair_derate`, `ultimate_factor`, `fea_allowable_printed_petg_mpa`, `fea_material_printed_petg`, `static_margin`, `hover_thrust_to_weight_min`, `cl_max_default`, `faa_*`. The 26 placeholder-own joints on sourced types (TAPE-FOAM 15, EPOXY 4, STRAP-VELCRO 3, TAPE-HINGE 2, TIE 2) are cleared only by per-joint ratings in `designs/` (U8.3), not by this unit.

## E. Packet map
| packet | topic | values (count) |
|---|---|---|
| 1 | dimensional and kinematic tolerances | attach_tolerance_mm, strip_gap_tolerance_mm, interference_max_mm3, planform_match_tolerance_fraction, mechanism_ratio_tol, mechanism_abs_tol_deg, mechanism_contact_step_deg (7) |
| 2 | aero and stability bands | fw_static_margin_max, wing_loading_max_g_dm2, cruise_to_stall_ratio_min, transition_stall_ratio_min, aft_surface_efficiency, wind_drag_coefficient (6) |
| 3 | hover and VTOL control margins | hover_ctrl_factor, transition_thrust_fraction_max, hover_moment_reference_lever_m, hover_moment_pass_ratio, hover_moment_fail_ratio, wind_moment_min_lever_fraction (6) |
| 4 | battery and propulsion model inputs | pack_sag_fraction, propulsive_efficiency, battery_usable_fraction, lipo_nominal_cell_v, energy_reserve_fraction (5) |
| 5 | wiring and electrical connectors | wire_clearance_mm, electrical_rating_min_ratio, CT-AS150U, CT-BULLET-3, CT-SOLDER-PHASE, CT-SOLDER-DC, CT-SERVO-JR (7) |
| 6 | landing and drop test | drop_height_m, tip_angle_max_deg, rest_speed_max_mps, duration_s, joint_rf_min (5) |
| 7 | materials, printer volumes, FEA band | material_density cfrp-tube, xps-foam, Fortus 380MC build volume, LulzBot TAZ 6 build volume, fea_singularity_band_mm (5) |
| 8 | fasteners, motor and prop joints | CT-PROP-ADAPTER, CT-PROP-NUT, CT-A-M25-SHCS-MOTOR, CT-A-PROP-ADAPTER, CT-A-PROP-NUT, CT-A-M3-CSK-MOTOR, CT-A-M3-BOLT-MOUNT (7) |
| 9 | servo, linkage, hinge, clamp, pad, tubing | CT-SERVO-SPLINE, CT-CLEVIS, CT-PIN-HINGE, CT-GEL-PAD, CT-PITOT-TUBING, CT-TUBE-CLAMP, CT-M2-SCREW-PLASTIC, CT-TAPE-SKIN (8) |

Run order by leverage: 1, 6, 7, 2, 3, 4, 5, then 8 and 9 (0 blocking rows moved).

## F. Decisions that are not scout work
- **Team decision (owner and date needed), 21 rows:** prop_chain_max_intermediate_parts, embed_max_fraction_of_child, containment_min_fraction, glued_overlap_max_fraction, distributed_mass_max_fraction_each and _total, bom_verified_max_age_days, transport_box_mm (gate-thresholds and program), servo_must_drive_mechanism, mission_hover_min, mission_cruise_min, hover_wind_mps, the 7 other program.yaml constraints, jacobs-fdm (Prusa) build volume, machine_optional_methods.
- **Held:** landing_load_factor (T113 drop test, D68).
- **Derivation candidates (conductor or advisor assigns):** interference_max_mm3, strip_gap_tolerance_mm, control_surface_gap_max_fraction, planform_area_mismatch_fail_fraction, lateral_cg_max_fraction_span, wing_area_complete_min, fea_singularity_band_mm.
- **Criterion fix (finding 2):** 518 rows; needs a `core/` decision.
