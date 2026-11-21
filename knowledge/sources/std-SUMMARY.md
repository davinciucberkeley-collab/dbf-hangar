# Scout summary: provisional design rules (design-standards.yaml v0.1)

Retrieved 2026-11-11. All sources listed were opened and read, unless noted. Numbers are from the source files in this folder; none were added from memory.

| Rule key | Our value | What sources say | Source ids | Recommendation (keep / change to X / unclear) |
|---|---|---|---|---|
| static_margin | min 0.05, max 0.15 (fraction of MAC, fixed-wing cruise) | MIT 16.01 design rules give 0.05 to 0.15 as a fraction of chord c (not explicitly MAC). uavmodel blog gives 5 to 15 percent for DIY UAVs. A blog on aircraft design calls 5 percent a common rule of thumb with no upper bound and argues for dynamic margin. Model Aviation argues %MAC is unreliable and gives no range. Flite Test gives 25 percent MAC CG as a first-flight reference, with no margin range. | std-mit-unified-desrules; std-uavmodel-diy-uav-airframe; std-aircraftdesigncentral-static-margin-myth; std-modelaviation-simplified-stability; std-flitetest-rc-cg-position | keep (two independent sources agree on 0.05 to 0.15; reviewer should confirm whether MIT's "c" means MAC for wings) |
| hover_thrust_to_weight_min | 1.5 | ArduPilot quadplane docs and PX4 VTOL docs give no numeric value. A forum thread quotes a paper for 1.2 to 1.5 with a 1.05 floor (opinions). Another poster suggests 2 to 2.2 for lift motors (opinion). A robotics reference gives 2.0 as a minimum design heuristic for multirotors with control authority (non-authoritative web page). | std-ardupilot-quadplane-building; std-px4-vtol-quad-configuration; std-ardupilot-forum-hybrid-vtol-twr; std-multirotor-design-compendium | unclear (1.5 sits inside the quoted 1.2 to 1.5 range but below the 2.0 heuristic; get the underlying paper quoted for 1.05 to 1.5 before deciding; 2.0 is the candidate if confirmed) |
| landing_load_factor | 3.0 g (mass outboard x g x 3.0 at each attachment) | No source found that gives a landing load factor of 3 g. ASTM F3298-19 defines landing loads but gives no magnitude in the sections read; it sets ultimate factor 1.5. STANAG 4703 gives a 3.8 g symmetric limit manoeuvre load and 1.5 ultimate factor, with landing loads in an annex not read. NASA X-57 uses 3.4 g for a larger aircraft (manoeuvre-type). | std-astm-f3298-lightweight-uas; std-stanag-4703-aep-83; std-nasa-x57-static-structural-requirements | unclear (no sourced landing value; 3.0 is below the 3.8 g manoeuvre limit in STANAG, which is a different load case; need STANAG Annex B or ASTM F3298 load tables) |
| cl_max_default | 1.1 (used when no flight.cl_max) | Guglielmo and Selig (1997) give CLmax at Re 2e5 for ten airfoils: 2.2 (S1223, high-lift) down to 1.17 (S3021); E214 1.25; FX 63-137 1.75. Ananda, Sukumar and Selig (2015) give flat-plate finite-wing CLmax 0.55 to 0.7 at Re 6e4 to 1.6e5 (non-standard CLmax definition). Lissaman (1983) gives a design target of about 1.6 for one high-lift section at high Re. | std-guglielmo-selig-1997-s1223; std-ananda-sukumar-selig-2015-flat-plate; std-lissaman-low-re-airfoils-1983 | unclear (1.1 is below every plain airfoil tabulated at Re 2e5, so it is conservative for stall speed; no source gives a typical small-UAV value; keep only as a labeled conservative default) |

## NASA documents (item 5)

| Document | What it covers | Applies to small UAVs (under 55 lb)? | Source id |
|---|---|---|---|
| NASA-STD-5001 (Structural Design and Test Factors of Safety for Spaceflight Hardware, Rev B with Change 3) | Structural design, test and service-life factors for spaceflight hardware; technical standard, not mandatory; no mention of aircraft or UAVs | No | std-nasa-std-5001-factors-of-safety |
| X-57 Static Structural Requirements and Airworthiness Approach (Li, NASA Armstrong, NTRS 20240006690) | Structural airworthiness plan for X-57, derived from a 3000 lb Part 23 aircraft; 3.4 g design load factor; 2.25 factor for new analysis-only metal; no landing factor value | No (X-57-specific; does not mention small UAS) | std-nasa-x57-static-structural-requirements |
| NASA UAS airworthiness guidance | Not found. A NASA NTRS search returned several UAS-related reports (for example 20160010170, 20100027489), but none were opened within the search budget. | Unknown | none |

## Notes for the reviewer
- No source in this batch supports a 3.0 g landing load factor. It is the least supported value.
- The ASTM F3298 copy used is a third-party sample of F3298-19; F3298-24 is the active revision and was not read.
- The STANAG read covered only the first 100,000 characters of a longer document.
- design-standards.yaml was not edited.

## U2.2 scouts (2026-11)

| file id | keys it feeds | what it says (one line, numbers copied from the file) | verified |
|---|---|---|---|
| std-stanag-4703-annex-b-landing | landing_load_factor; ultimate_factor | No fixed landing load factor in STANAG 4703. Annex B: n = nj + 2/3, nj = (h + d/3) / (ef x d), h = 3.6 x sqrt(W/S) in, h not less than 9 in; ultimate 1.5 (Annex B 1.3, PDF p.68) | true |
| std-astm-f3298-load-tables | landing_load_factor | F3298-24 and F3298-19 landing and ground load tables not found (store page and sample copy only). Part 23 comparison, 14 CFR 23.473 (2016): inertia load factor not less than 2.67; ground reaction 2.0 | false |
| std-vtol-thrust-to-weight-paper | hover_thrust_to_weight_min | Hover T/W 1.2 to 1.5 cited to Raymer (ref. 16, Introduction p. 166); 1.05 not in the paper | true |
| std-nasa-additive-factors | ultimate_factor; fea_allowable_printed_petg_mpa | NASA-STD-6030 does not set or change factors of safety; polymer AM margin 0.5 (ultimate, elongation at least 3 %) and 2.0 (below 3 %); proof factor 1.2; NASA-STD-5001B metallic ultimate 1.4 (comparison); no PETG allowable in MPa | true |
| std-dbf-rules-box-size | D5 transport box (U2.1 T7; no pending key) | 2026-27 rules set no transport box size; wingspan max 6 ft (1.83 m); arming plug at least 6 in (152 mm) from propeller plane; staging assembly 5 min | true |
| std-ct-fasteners | CT-M3-SHCS-INSERT, CT-M3-SHCS-NYLOC, CT-M3-SHCS-MOTOR, CT-M4-SHCS-NYLOC (sourced); CT-M2-SCREW-PLASTIC, CT-A-M25-SHCS-MOTOR (torque only, pending) | M3 proof load 2920 N (8.8); M4 5100 N (8.8); M3 insert pull-out about 1400 N in as-printed PLA; M2 breaking torque 0.37 Nm (8.8) | true |
| std-ct-adhesives-tapes | CT-TAPE-FOAM, CT-TAPE-TIE (sourced); CT-EPOXY, CT-CA (pending) | VHB 4910 90 deg peel 15 lb/in (260 N/100 mm); 105/205 epoxy bulk tensile 7,900 psi; LOCTITE 401 lap shear steel 20 N/mm2 (pairing unconfirmed) | true |
| std-ct-electrical | CT-XT60, CT-XT90, CT-MR30, CT-JST-GH-4, CT-JST-GH-6 (sourced); CT-AS150U (pending, source conflict) | XT60 35 A; XT90 45 A MAX; MR30 20 A MAX; JST GH 1 A; AS150U 75 A MAX (catalogue) vs 70 A continuous in library spec | true |
| std-ct-straps-hinges-thermal | CT-STRAP-VELCRO, CT-HATCH-HL, CT-TIE (sourced); CT-THERMAL-PAD (pending, not a load) | 13M Loop shear 10 N/cm2 average; Panduit PLT2S-M loop tensile 50 lb (distributor); Gap Pad 1500 1.5 W/m-K | true |
