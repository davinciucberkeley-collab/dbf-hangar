# U13.7-5 findings: design gap, not a bug
Standards: planform_strip_count 41, strip_gap_tolerance_mm 3.0, control_surface_gap_max_fraction 0.15. Script: scratchpad/u13.7-5/run.py
| case | measured mm2 | hand mm2 | diff % |
| (a) full | 192517 | 192514 | 0.00 |
| (b) core 0.72 | 138612 | 138610 | 0.00 |
| (c) core+2 ailerons | 158131 | 158712 (hand) / 158130 (rehearsal) | -0.37 / 0.00 |
| step4 numeric integral | 192514.0 | 192514 | 0.00 |
| step5 inboard_span=0 | 175822 | 175800 | +0.01 |
(a)-(step5) = 16695 vs hand 16714 (0.1%). No missing/ignored strips; span 1200 in all.
(c) reproduces the rehearsal 158,130 exactly. Verdict: design gap. Wing trailing 28% outside ailerons (inboard and tip) is no component.
Recommendation: build wing as part: full for the area, or add trailing pieces for the uncovered 28%; (not checked which wing_panel options exist beyond part full/core/elevon).
No commit.
