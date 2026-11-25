# Calibration findings: hangar tier-3 checks against the Cessna 172S

Fixture `tests/fixtures/c172s/plane.yaml` with `tests/test_calibration_c172.py` (branch std/u18.2-calibration, based on std/u18-sources 7784338); published stall speeds are the handbook table KCAS values at 2,550 lb (std-cessna-172s-poh, p.124).

| quantity | published (source id) | hangar computed | error | tolerance key (pending/sourced) | verdict |
|---|---|---|---|---|---|
| mass | 1,157,000 g = 2,550 lb (std-faa-tcds-3a12-text p.29) | 1,157,000 g | 0.0 % | calibration_tol_mass_fraction (pending) | trustworthy |
| wing area | 16.17 m2 (std-textron-cessna-skyhawk-172s) | 16.17 m2 (input: rectangular 11.00 x 1.47 m) | 0.0 %, equal by construction | calibration_tol_geometry_fraction (pending) | trustworthy |
| wing loading | 14.7 lb/sq ft = 717.7 g/dm2 (std-cessna-172s-poh PDF p.15) | 715.52 g/dm2 | -0.3 %; fixed-wing.yaml limit 100 g/dm2 gives WARN above | calibration_tol_geometry_fraction (pending) | trustworthy only with measured input |
| stall Vs1 (default CLmax 1.1) | 53 KCAS = 27.27 m/s (std-cessna-172s-poh p.124) | 32.27 m/s | +18.4 % | none (pinned as known finding) | not trustworthy |
| stall Vs1 (CLmax 1.54) | 27.27 m/s | 27.27 m/s | +0.0 % (CLmax 1.54 is implied by Vs1, so a formula check only) | calibration_tol_stall_fraction (pending) | trustworthy only with measured input |
| stall Vso (default CLmax 1.1) | 48 KCAS (flaps 30) = 24.69 m/s (p.124) | 32.27 m/s | +30.7 % | none | not trustworthy |
| cruise/stall ratio (default CLmax) | 63.79 / 27.27 = 2.34 (124 KTAS, p.2, over Vs1; mixes true and calibrated speed) | 1.98 | -15.5 % | none | not trustworthy |
| neutral point | none published | 2639.5 mm (fixture frame; hand calc 2639.5) | not comparable | none | not trustworthy |
| CG margin at aft limit 47.3 in (36.4 % MAC) | aft limit inside the envelope (std-faa-tcds-3a12-text p.29) | static margin +11.2 % MAC (NP x 2640 mm, CG x 2475 mm), PASS | not comparable (no published NP) | none | not trustworthy |
| rate of climb | 730 fpm (std-cessna-172s-poh p.2) | no check | n/a | none | not computed |
| cruise speed | 124 KTAS (p.2) | 63.79 m/s (input) | 0.0 %, input | none | not computed |
| range and ceiling | 518 NM at 75 % power (p.2) | no check | n/a | none | not computed |

## Trustworthy
- Mass sum against the maximum takeoff mass: error 0.0 % (unit conversion only).
- Wing loading: 715.52 g/dm2, error -0.3 % against the published 717.7 g/dm2.
- Stall formula with a measured CLmax: +0.0 % (it uses the value it was derived from, so only units and formula are tested).

## Not trustworthy and why
- Default CLmax 1.1 (`cl_max_default`): stall +18.4 % against Vs1 (flaps up) and +30.7 % against Vso (flaps 30); the cruise/stall ratio is 1.98 against 2.34 published (-15.5 %). The real wing gives an implied CLmax of 1.54 flaps up.
- Wing-loading threshold 100 g/dm2 is a scale-RC figure: the full-size 172S reads 715.5 g/dm2 and WARNs.
- Neutral point: the model has no fuselage term (the row says so); there is no published neutral point for the 172S to compare, so the +11.2 % MAC margin at the aft CG limit is unverified. The fixture also simplifies the wing to a rectangle and lumps all mass at one point.

## Not computed by any check today
- Rate of climb (730 fpm published), range and ceiling (518 NM published); cruise speed is an input.
- Figures the sources do not give: Vx, 172S airfoil, wing incidence, dihedral, printed empty-weight CG (std-cessna-172s-poh, std-faa-tcds-3a12-text "figures still missing"). The tier-1 attachment checks of the fixture FAIL (lumped fuselage box, attachment points); only tier 3 is used.
