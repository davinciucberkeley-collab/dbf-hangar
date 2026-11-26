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

## Baselined residue (79 known rows: 6 FAIL + 73 SKIP; concept-a has 10 FAIL + 73 SKIP)
Verified row by row from the two `baseline.json` files. Net FAIL: 10 - 4 absent = 6.

The swept-pose and neutral-pose FAIL rows for `wng-007-l/r` and `mec-002-l/r` against `wng-001` are gone since U16.2
(7d183bf) made the cut pockets follow the pose: 10 T1.interference, 2 T1.attachment_overlap, and 2 T6.mechanism.elevon-l/r
were removed from the baseline.

4 concept-a FAIL rows are absent because `fea/` is not copied: cge-001 landing and thrust (SF 0.37, 0.44) and cge-006
landing and thrust (SF 0.83, 0.72). The cge-008 SKIP is absent too; in their place one SKIP ("28 printed part(s) have no
OpenCAE stress check yet"). The hub-clamp parts are identical to concept-a, so those stress failures still apply:
running `plane fea` on concept-a-param would bring them back as FAIL rows (the baseline was recorded without `fea/`).

Other rows keep their status and only change numbers (T2.sim_drop_loads, T2.sim_rest, T3.static_margin 15.7 % vs 16.4 %,
FAIL in both). No neutral-pose interference. `baseline check` messages quote the folder name: check a scratch copy only
if the folder is also named `concept-a-param`.

## Demo: `plane design set designs/concept-a-param parameters.span_mm --value 940 --why "demo"`
| | 900 | 940 |
|---|---|---|
| mass | 1272.99 g | 1279.79 g (+6.80: core +4.6, spar +2.2) |
| CG (mm) | 21.35, -2.02, 6.62 | 21.65, -2.01, 6.58 |
| stall | 11.7 m/s | 11.5 m/s |
| static margin | 15.7 % (FAIL) | 15.6 % (FAIL) |

Printed: `regenerated wng-001, wng-002`. `baseline check` at 940: pass, 0 regressions, 1 improvement (the E-MEC-10 drop-load
FAIL row disappears). No fallback value was needed.
