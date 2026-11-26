---
id: std-u171-p7-comsol-saint-venant-width
title: Applying and Interpreting Saint-Venant's Principle
authors: COMSOL (software vendor blog)
year: unknown
url: https://www.comsol.com/blogs/applying-and-interpreting-saint-venants-principle
type: website
retrieved: 2026-11-25
verified: true
---

## Summary
Vendor blog on Saint-Venant's principle, opened on 2026-11-25. It states that the stress fields from two load cases agree at a distance about equal to the width of the plate, in a worked example with a hole. It is a vendor blog and a single example, not a textbook or a general decay-length rule.

## Usable rules / numbers
- Agreement distance approximately equal to the width of the plate (1 x plate width), for the worked example of a hole in a loaded plate. Kind: derivation input (distance in section sizes). Place: heading "Simple Example: Analyzing Stresses at a Distance".
- The same post says that, when the hole is moved closer to the loaded boundary, that agreement distance doubles, and that stresses from a zero-resultant load system become small at a distance comparable to the size of the loaded boundary. Place: sections "Simple Example: Analyzing Stresses at a Distance" and "Zero Resultant Systems and Strain Energy Density".
- The page gives no decay length in mm and no value for a clamped face.

## How we could use it
- fea_singularity_band_mm: the only usable input is the k = 1 (plate width) factor from a single example; a textbook or NAFEMS decay-length rule is still needed before the 2.0 mm value can be checked.
