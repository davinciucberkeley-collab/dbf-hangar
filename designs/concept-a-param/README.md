# concept-a-param

Parametric copy of `concept-a` (D70 demo), made by `plane design copy`, schema 1.2. Four parts are generated; the other
~100 components, attachments, claims and flight data are identical to `concept-a` (importer output, imported meshes).
`designs/concept-a/` is the frozen source.

Generated: `wng-001` (`wing_panel`, S5010 core, 12 mm spar bore, 40 `cut_files` = the neighbours' own meshes),
`wng-002` (spar tube), `fin-001-l/r` (tubes). Parameters: `span_mm` 900, `chord_mm` 245, `spar_x_mm` 60, `spar_od_mm` 12,
`spar_id_mm` 10, `fin_x_mm` 294, `fin_len_mm` 360, `fin_od_mm` 16, `fin_id_mm` 14 (values and sources in `plane.yaml`).
Wing density is lumped: `xps-tape-lumped` 0.03499 g/cm3 = 100.1 g / nominal core volume 2 860 722 mm3 (the brief's
"about 0.03393" was wrong; its rule gives 0.03499).

## Match to concept-a
| Part | Volume | Bounds | Measured |
|---|---|---|---|
| tubes | 0.1 % | 0.02 mm | exact (test) |
| wng-001 | +16 % ceiling | 0.1 mm | +10.6 %, z within 0.05 mm |
| aircraft mass | 0.5 g | n/a | -0.25 g (1272.99 vs 1273.24) |
| CG | x, z 0.05 mm; y 0.15 mm | | x +0.01, z 0.00, y -0.12 |

CG y moves 0.12 mm because the cut pockets (neighbour meshes) are not mirror-symmetric, so the generated core's y centroid
is not 0; the test allows 0.15 mm for y only.

## Baselined residue (93 known rows, 20 FAIL; concept-a has 10)
Cut pockets follow the neutral pose only; swept-pose pockets are a follow-up. Extra rows against `concept-a`:
8 `wng-007-l/r` swept-pose rows (6 T1.interference at pose up/down/sweep, 2 T1.attachment_overlap), 2 `mec-002-l/r`
T1.interference rows (range +-15 deg), and T6.mechanism.elevon-l/r collisions at -15 deg. T2.sim_drop_loads, T2.sim_rest,
T3.static_margin (15.7 % vs 16.4 %, FAIL in both) and the planform WARN change numbers only. No neutral-pose interference.
`baseline check` messages quote the folder name: check a scratch copy only if the folder is also named `concept-a-param`.

## Demo: `plane design set designs/concept-a-param parameters.span_mm --value 940 --why "demo"`
| | 900 | 940 |
|---|---|---|
| mass | 1272.99 g | 1279.79 g (+6.80: core +4.6, spar +2.2) |
| CG (mm) | 21.35, -2.02, 6.62 | 21.65, -2.01, 6.58 |
| stall | 11.7 m/s | 11.5 m/s |
| static margin | 15.7 % (FAIL) | 15.6 % (FAIL) |

Printed: `regenerated wng-001, wng-002`. `baseline check` at 940: pass, 0 regressions, 1 improvement (the E-MEC-10 drop-load
FAIL row disappears). No fallback value was needed.
