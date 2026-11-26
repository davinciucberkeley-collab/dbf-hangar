---
id: std-tail-volume-coefficients
title: Tail Sizing - AERO_TN_TailSizing_13-04-15 (Technical Note, HAW Hamburg), Tables 2.3 and 2.4
authors: Dieter Scholz (HAW Hamburg, Technical Note); reproduces Raymer 1992 and other authors
year: 2013
url: https://www.fzt.haw-hamburg.de/pers/Scholz/Aero/AERO_TN_TailSizing_13-04-15.pdf
type: website
retrieved: 2026-11-25
verified: true
---

## Summary
A 2013 technical note by Dieter Scholz compiles tail volume coefficient suggestions by aircraft type, with a column per author. The Raymer 1992 column gives horizontal (Vh, called CH) and vertical (Vv, called Cv) values for sailplane, homebuilt, general aviation single and twin engine, and other classes. The note also states the definitions of both coefficients. This run reads the Raymer column as printed; the note is a secondary compilation, not the Raymer book.

## Usable rules / numbers
Column read: "Raymer" (first value column). Column assignment checked with pdftotext table mode, which separates the sparse rows.

Horizontal tail volume Vh (note's CH), Raymer column, Table 2.3, printed p. 51:
- Sailplane: 0.500 (Table 2.3, p. 51)
- Homebuilts: 0.500 (Table 2.3, p. 51)
- GA single engine: 0.700 (Table 2.3, p. 51)
- GA twin engine: 0.800 (Table 2.3, p. 51)
- Regional turboprop: 0.900 (Table 2.3, p. 51)
- Jet transport: 1.000 (Table 2.3, p. 51)
- Jet trainer: 0.700 (Table 2.3, p. 51)
- Jet fighter: 0.400 (Table 2.3, p. 51)
- Military transport: 1.000 (Table 2.3, p. 51)
- Agricultural: 0.500 (Table 2.3, p. 51)
- Flying boat: 0.700 (Table 2.3, p. 51)

Vertical tail volume Vv (note's Cv), Raymer column, Table 2.4, printed p. 52:
- Sailplane: 0.020 (Table 2.4, p. 52)
- Homebuilts: 0.040 (Table 2.4, p. 52)
- GA single engine: 0.040 (Table 2.4, p. 52)
- GA twin engine: 0.070 (Table 2.4, p. 52)
- Regional turboprop: 0.080 (Table 2.4, p. 52)
- Jet transport: 0.090 (Table 2.4, p. 52)
- Military trainer: 0.060 (Table 2.4, p. 52)
- Military fighter: 0.070 (Table 2.4, p. 52)
- Military transport: 0.080 (Table 2.4, p. 52)
- Agricultural: 0.040 (Table 2.4, p. 52)
- Flying boat: 0.060 (Table 2.4, p. 52)

Definitions (section 2.5.2, p. 50; equations 2.6 and 2.7):
- Vh = S_H * l_H / (S_W * c_MAC): reference chord is the wing mean aerodynamic chord; S_W is wing reference area. (section 2.5.2, p. 50)
- Vv = S_v * l_v / (S_W * b_W): reference span is the wing span b_W. (section 2.5.2, p. 50)
- Caution: the note's prose assigns the two equation labels in the opposite order from the symbols; the equations themselves match the brief's definitions. (section 2.5.2, p. 50)

Not in this source: personal, commuter, business jet and twin-engine values from other authors; Gudmundsson; any sailplane or homebuilt value other than Raymer.

## How we could use it
- Feeds U18.4-1 as class starting values for Vh and Vv (Raymer column, Tables 2.3 and 2.4 above); treat as a secondary reproduction until the Raymer book table is opened.
- Definitions above fix the reference chord (MAC for Vh) and reference span (wing span for Vv) for the design tool.
- values still missing: Raymer 1992 original table (not opened); Gudmundsson "General Aviation Aircraft Design" (not opened); values for classes outside the Raymer column are not used here.
