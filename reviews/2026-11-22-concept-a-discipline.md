# Concept-a discipline sign-off @ 7553ddd (W4-RB, fresh Opus; closes whole-branch blocking item B6)

Validate (read-only, `--tier all --json`): exit 1; 4 FAIL (T2.sim_drop_loads E-WNG-20/21, T2.sim_rest, T3.static_margin), 13 WARN, 104 SKIP.
Shorthand: **NB** nothing built yet (designs/concept-a/README.md:56); **NP** PDL 1.0 has no slot (flight-software params, flight card, test plan); **pending (no key)** the skill's limit is pending and no `standards/` key exists; **sc:N** `standards/review-scorecard.md` line N.

## review-structures
| item | verdict | evidence |
|---|---|---|
| coupon-record (H1#126) | pending (no key) | no foam coupon record; only an E1 damper coupon (claims.yaml:4023) |
| modal (A2#21) | pending (no key) | T9 CL-A-VIB-LOW 77 ≤ 83.6 Hz, VIB-HIGH 432 ≥ 303.6 Hz, VIB-FC 27.1 ≤ 30 m/s² PASS (design parameters) |
| modal (B3#70) | FAIL | CL-A-VIB-GM / VIB-GM-SHIFT (claims.yaml:5254, 5306) state no torsion damping; zeta 1 % / 0.5 % only in CALC-A-VIB-FC, unsourced (sc:46) |
| modal (H1#156) | pending (no key) | hover 1P 100-119 Hz, cruise 2P 243-253 Hz, clear of 77 and 432 Hz |
| modal (J1#5) | pending (no key) | arms CGE-002 12x10 CFRP (plane.yaml:136-178); no bare-tube mode or modulus sweep |
| post-impact-inspection | N/A | NB |
| proof-inspection | N/A | no proof test; NB |
| proof-path-decision (H1#88/89/90) | pending (no key) | no proof-load strain, strip strain or pad deflection data |
| tube-material-E | pending (no key) | "CFRP tube", no modulus (plane.yaml:144) |

## review-aero
| item | verdict | evidence |
|---|---|---|
| cruise-cl | PASS (info, sc:65) | reviewer estimate CL 0.38 (declared S 0.2205 m²), 0.41 on measured S 0.2009 m² (T3.planform_matches_geometry WARN) |
| pitot-placement | PASS on paper (sc:47) | avn-006 tip 130 mm ahead of LE (≥ 10 mm); y 408-412 vs prop disc edge y 318 |
| prop-normal-force | pending (no key) | reviewer estimate: prop planes ~142 mm ahead of CG |
| station-band-check | pending (no key) | NB |
| tuft-check | N/A | flight test; NB |

## review-controls
| item | verdict | evidence |
|---|---|---|
| airspeed-calibration | pending (no key) | NB |
| airspeed-fallback (B2#23/24/25) | pending (no key) | T3.stall 11.7 m/s at CLmax 0.75 (EST); no fallback speeds, full-travel speed or trip ratio |
| airspeed-sensor (G4#33) | N/A | bench test of MS4525; NB |
| airspeed-sensor (H2#46) | N/A | NP; MS4525 and pitot designed in (plane.yaml:81-102) |
| arming-interlock | pending (no key) | NP |
| bench-channels | N/A | NB; motor map NP |
| failsafe-check | pending (no key) | NB |
| failsafe-map | pending (no key) | CL-A-FENCE 220 m PASS; RC-loss mode NP |
| fbwa-trim | pending (no key) | NB |
| fc-sku-check | FAIL (not found, sc:61) | Kakute F405 Wing Mini (plane.yaml:48); no power board or capacitor component |
| flex-loop-margin (B3#55/56/57) | pending (no key) | CL-A-VIB-GM 2.19 PASS; yaw torsion mode not separate; no phase margin |
| fsw-params, harmonic-notch, param-readback, transition-mode | N/A | NP |
| loop-crossover (B3#58/59) | pending (no key) | no crossover figure |
| neutral-point | pending (no key) | model NP 59 mm vs claim CL-A-SM 40.7 mm (claims.yaml:2181); T3.static_margin FAIL |
| param-update | pending (no key) | Q_M_SPIN_MAX 0.90 cap (plane.yaml:786); peak needs bench test |
| rc-failsafe-mode | N/A | NP, NB |
| rc-variant | FAIL (not found, sc:61) | RP3 V2 ELRS, no regional variant (plane.yaml:59); no BOM |
| rx-power-source | pending (no key) | only hrn-bat modelled |
| tailsitter-handover | pending (no key) | T3.transition_margin WARN (transition_speed_mps missing) |
| weathervane, yaw-damper | pending (no key) | NP; yaw model under T37 |
| yaw-doublet | pending (no key) | T3.control_authority yaw WARN 1.10 vs 1.5 (T37) |

## review-propulsion
| item | verdict | evidence |
|---|---|---|
| esc-listing | FAIL (not found, sc:61) | SpeedyBee BLS 35A 4-in-1 (plane.yaml:878); CL-A-ESC-I 17.8 ≤ 35 A PASS; no BOM listing |
| incoming-inspection, prop-hand-check | N/A | NB |
| punch-test | pending (no key) | NB |
| motor-direction | PASS on paper (sc:47) | UR/LL CW, UL/LR CCW (plane.yaml:834-867), diagonal pairs match |
| motor-out-handling | N/A | NP |
| pack-capacity | pending (no key) | 2300 mAh nameplate only |
| pack-spec | PASS on paper (sc:47) | 4S matches 16.8 V case; 172.5 A ≥ 44.8 A (T7.electrical_rating PASS); XT60 tail; pack-side connector and SKU not stated |
| prop-selection | pending (no key) | CL-A-TW-SAG-GATE PASS; no baseline comparison |
| thermal (E1#4, E2#8, E3#24, E3#35) | pending (no key) | CL-A-MOTOR-I 12.1 A PASS; no winding or pack temperature; ESC under AVN-008; no CFD factor |

## review-manufacturing
| item | verdict | evidence |
|---|---|---|
| assembly, block-fit, colour-coding, core-handling, hot-wire-safety, le-quality | N/A | NB; no assembly sequence (T24) |
| chemical-safety | FAIL | CT-CA on XPS parts E-FIN-05..08 and 13..16 (plane.yaml:1304-1337) |
| fillet-keepout | N/A | fillets lumped in hrd-001 |
| jig-material, material-grade, pod-box-accept, printing | N/A | no jigs, no cartridge, no pod, no ASA |
| lab-access | FAIL (not found, sc:61) | 7 hotwire-foam parts; no BOM for hot-wire gear |
| printer-access (G3#14) | FAIL | 38 PETG parts on jacobs-fdm, which lists PLA only (standards/manufacturing.yaml:40-45) |
| printer-access (G3#15) | PASS | jacobs-fdm lists PLA |
| printer-class | PASS | PETG only; standard FDM class |

## review-test-safety
| item | verdict | evidence |
|---|---|---|
| build-safety, compliance-check (H3#75/76/77), crew-roles, fence-recovery, prearm-checks, range-check (G4#40), site-approval | N/A | NB, NP or operations; no Remote ID module in components |
| fatigue-limit, first-hover-entry, go-around-triggers, landing-site, lipo-retermination, range-check (F5#14), site-rules, spin-test, wind-check, wind-ratio (H3#3/5) | pending (no key) | NB or NP |
| hover-hold | pending (no key) | T3.hover_tw 2.72 ≥ 1.5 |
| post-contact-spin-down | pending (no key) | T2.sim_rest FAIL 79° vs 30° |

## FAIL items that are real design findings
1. printer-access G3#14 (new, T63): 38 PETG parts routed to a PLA-only machine.
2. chemical-safety (new, T64): CA on XPS fin fairings.
3. modal B3#70 (new, T65): torsion damping behind the gain-margin claims unstated and unsourced.
4. fc-sku-check (new data gap, T66): FC power board and capacitor not modelled; RC regional variant; no Remote ID (flights stay inside a FRIA).
5. esc-listing, rc-variant, lab-access: no BOM (T24, R14).

Known validator FAILs sit behind pending items (static margin, with model NP 59 mm vs claim 40.7 mm; T2.sim_rest behind post-contact-spin-down). T60, T37, T31 tracked separately.

### Verdict: ACCEPT
All 97 items across the six skills are answered.
