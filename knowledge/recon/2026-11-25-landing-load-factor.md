# Recon: `structure.landing_load_factor` (U4.19 step 2, D67, D6, T82)

Question: which value can a source already in `knowledge/sources/` back, or does the key stay `pending`? All seven source files were read in this run.

## 1. The seven sources

| # | File | What it gives on a landing load factor | Rule for this class? | verified |
|---|---|---|---|---|
| 1 | std-astm-f3298-lightweight-uas | No value given (secs 3.1.33.2-3.1.33.4, 7.5.1.3, 7.10.5.1; symbol n3 defined, secs 3.2.21-3.2.24, no number). Gives ultimate 1.5 (sec 7.8.1) and 55 lb scope (secs 4.2.1, 1.3). | Yes, right class, but silent on the number. | true |
| 2 | std-astm-f3298-load-tables | F3298 tables not read (store page only; 19 copy 404, astm.org 403). Only the 14 CFR 23.473(g) 2016 comparison: limit inertia factor not less than 2.67, ground reaction not less than 2.0. | No. The 2.67 is a crewed Part 23 comparison. F3298 value: no value given. | false (the Part 23 text was opened; F3298 body was not) |
| 3 | std-multirotor-design-compendium | No value given (landing appears only as a 3-5 m/s failsafe descent rate, section "Design heuristics" area). | No, other use. | true |
| 4 | std-nasa-std-5001-factors-of-safety | No value given; spaceflight hardware only. | No. | true |
| 5 | std-nasa-x57-static-structural-requirements | No landing value (sec V.A). 3.4 g reduced Nz and 3.8 g original P2006T are manoeuvre loads (sec V). | No, 3000 lb Part 23 derivative. | true |
| 6 | std-stanag-4703-aep-83 | No fixed value; landing is UL.6.2 pointing to Annex B. Manoeuvre factor at least 3.8 (UL5.2); ultimate 1.5 / 1.25 (UL2.2, UL2.3). | Yes, light UAS up to 150 kg, but only as a procedure. | true |
| 7 | std-stanag-4703-annex-b-landing | No fixed value; a formula: nj = (h + d/3)/(ef x d), h [in] = 3.6 sqrt(W/S) with h at least 9 in, ef x d = 0.5 d for tire/rubber/spring (Annex B 1.1, PDF p.68); n = nj + 2/3 (Annex B table notes, PDF pp.67-68). 3.8 is only a threshold (Annex B 1.2). | Yes for conventional gear; "as a reference", case-by-case for others (UL.6.2, PDF p.21). | true |

Note on the source file 3: the compendium states no landing factor; it is listed for completeness.

## 2. STANAG Annex B computed for concept-a

| Input | Value | Where from | Status |
|---|---|---|---|
| Mass W | 1273.24 g | `plane design mass designs/concept-a`, mass_g | measured (sum of design part masses, many are placeholders/estimates) |
| Wing span x chord | 900 mm x 245 mm = 0.2205 m2 | `designs/concept-a/plane.yaml` line 1124 (planform) | design value |
| W/S | 5.774 kg/m2 = 1.183 lb/ft2 | computed here from W and S | computed |
| h | 3.6 x sqrt(1.183) = 3.92 in, below the 9 in floor, so h = 9 in (0.229 m) | computed here; floor from Annex B 1.1 | computed |
| `sim.drop_height_m` | 0.3 m | `standards/design-standards.yaml` line 143 (internal convention) | design value, not the Annex B h |
| Gear travel d (d_tire + d_shock) | not in the design | foot pads GER-002 are named "EVA/PE 12x15x30" (plane.yaml ~line 577); which dimension compresses and by how much is not recorded | missing, not assumed |
| ef | 0.5 (tire / rubber / spring) | Annex B 1.1 | source |

Result: n cannot be computed, because d is missing. The formula is very sensitive to d. Illustration only, with d assumed (not a design value): if d were 10 mm = 0.394 in, nj = (9 + 0.131)/(0.5 x 0.394) = 46.4 and n = 47.0; if d were 30 mm = 1.18 in, nj = 15.9 and n = 16.6 (computed here). Both are far above 3.0 and 3.8. For stiff foam feet and thin tubes the formula gives large loads, so the answer depends on a measured crush/travel, not on a table.

## 3. Candidates

| Value | Source place | Applies? |
|---|---|---|
| 3.0 (current) | No opened file gives it (sources 1-7; standards note says the same). | No source. Stays an internal convention only. |
| 2.67 | std-astm-f3298-load-tables, 14 CFR 23.473(g) 2016 | Crewed Part 23 comparison, not a UAS rule; also a floor on a limit inertia factor, lower than the current 3.0. |
| 3.8 | std-stanag-4703-aep-83 UL5.2; std-stanag-4703-annex-b-landing Annex B 1.2 | Manoeuvre factor and a threshold; not a landing factor. Using it as one would be a choice, not a citation. |
| n = nj + 2/3 | std-stanag-4703-annex-b-landing, Annex B 1.1 | The only opened UAS-class landing method; needs gear travel d (missing) and tailsitter-on-fin-tubes is not "conventional landing gear" (UL.6.2). |

Ranking: only the formula is a real source, and it cannot be evaluated or fully claimed for this gear layout. The others are comparisons. No candidate can be ranked as a sourced fixed value over the others.

## Effect on E-PWR-02 (placeholder, rated 12 N, plane.yaml line 1601)

Brief figure: about 11.9 N at 3.0 x 1.5 (so outboard mass about 270 g, computed here from 11.9 / (9.81 x 4.5)). Scaling linearly (computed here): 2.67 -> 10.6 N; 3.8 -> 15.1 N; formula 16.6 (d = 30 mm assumed) -> about 65.9 N. At 3.8 the joint's 12 N placeholder rating would fail.

## 4. If the value changes from 3.0, what re-runs (not run here)
- `designs/concept-a/baseline.json` (joint loads, rf, drop results change).
- FEA hashes (value edit changes them; source-text-only edits do not, `tests/test_fea_hash.py::test_non_value_edits_leave_hash_unchanged`).
- Claims and checks with criterion `landing_load_factor`: T2.joint_load, T2.sim_drop_loads (fidelity line).

## Recommendation
pending (keep value 3.0 as the working number; no opened source gives a fixed landing load factor, and the only UAS-class source is the STANAG 4703 Annex B formula n = nj + 2/3, which needs gear travel d)
source string: `pending` (note text may add: "std-stanag-4703-annex-b-landing Annex B 1.1 formula is the candidate method; d not yet measured; D6")
open fact: concept-a's real gear travel d (foot pad/leg compression in inches), from a bench drop at about 0.23 m (Annex B h = 9 in floor) or 0.3 m (`sim.drop_height_m`), supplied by Tristan and Dillon who pick the value (D6).
