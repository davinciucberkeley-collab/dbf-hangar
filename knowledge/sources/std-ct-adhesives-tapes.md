---
id: std-ct-adhesives-tapes
title: Adhesive and tape strengths for bonded and taped connection types (3M VHB Tapes Technical Data; LOCTITE 401 TDS; WEST SYSTEM 105/205 TDS and property table)
authors: 3M; Henkel Corporation; Gougeon Brothers, Inc. (WEST SYSTEM)
year: 2005 (3M VHB), 2012 (LOCTITE 401), 2014 (WEST SYSTEM 105/205)
url: https://westsystem.com/?p=2054
type: website
retrieved: 2026-11-20
verified: true
---

## Summary
Scout S7 (U2.2) collected manufacturer typical values for the bonded and taped connection types. Opened and read: WEST SYSTEM "Compare Epoxy Physical Properties" page (https://westsystem.com/?p=2054); WEST SYSTEM 105/205 Technical Data Sheet, October 2014 (https://www.westsystem.com/app/uploads/2022/12/105-205-Epoxy-Resin.pdf); LOCTITE 401 Technical Data Sheet, February 2012, distributor-hosted copy (https://www.monet.asia/media/pdf/TDS_LOCTITE-401.pdf); 3M "VHB Tapes Technical Data", November 2005, Digi-Key-hosted copy (https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/2605/VHB%20Tape%20Data%20Sheet.pdf). All three makers state their values are typical and not for specification use. The epoxy sheet gives bulk resin properties only (no lap-shear value); the CA and VHB sheets give bond strengths to metals and plastics, not to foam, balsa or printed PETG. The 2005 VHB sheet may differ from current 4910/4950 data; the current 3M sheets could not be opened.
blocked: multimedia.3m.com (HTTP 403 for the VHB product selection guide, the VHB specialty tapes TDS and the Scotch 375 box sealing tape TDS); blocked: www.3m.com (HTTP 403 on the VHB 4910 product page). tdsna.henkel.com was not reached (no URL found); farnell.com copy of LOCTITE 401 timed out.

## Usable rules / numbers
- CT-EPOXY: WEST SYSTEM 105/205 cured neat epoxy tensile strength 7,900 psi (ASTM D638), tensile elongation 3.4 %, tensile modulus 4.08E+05 (psi), compression yield 11,400 psi (ASTM D695), flexural strength 14,100 psi (ASTM D790); 105-205 TDS Oct 2014, "Physical Properties of Cured Epoxy".
- CT-EPOXY: same system on the westsystem.com property table: tensile 7,846 psi, compression yield 11,418 psi, flexural 14,112 psi; specimens cured 2 weeks at room temperature; westsystem.com/?p=2054, "Compare Epoxy Physical Properties" table, 105/205 row.
- CT-EPOXY: pot life 9 to 12 min (100 g at 72 F), cure to working strength 1 to 4 days, heat deflection temperature 118 F (ASTM D648), ultimate Tg 142 F; 105-205 TDS Oct 2014, "Handling Characteristics" and "Physical Properties of Cured Epoxy".
- CT-EPOXY: lap shear / bond strength to substrates: not found (neither WEST SYSTEM source lists one).
- CT-CA: LOCTITE 401 lap shear strength, steel (grit blasted) 20 N/mm2 (2,900 psi); aluminum (etched) 12.4 N/mm2; ABS 7.5 N/mm2 (substrate failure); polycarbonate 9.6 N/mm2 (substrate failure); PVC 10 N/mm2 (substrate failure); LOCTITE 401 TDS Feb 2012, p.2 "Typical Performance of Cured Material", Lap Shear Strength (substrate-to-value pairing read from a column-layout text extraction).
- CT-CA: LOCTITE 401 block shear strength (ISO 13445), polycarbonate 11 N/mm2 (1,600 psi), ABS 23 N/mm2 (3,340 psi, substrate failure), PVC 2.6 N/mm2 (380 psi); same TDS p.2.
- CT-CA: LOCTITE 401 tensile strength (ISO 6922, Buna-N) 6.9 N/mm2 after 10 s cure and 13.7 N/mm2 after 72 h at 22 C; fixture time on balsa under 5 s; full strength 24 to 72 h before service loads; same TDS p.1 to p.3.
- CT-CA: strength on foam (EPP/EPS/foam-safe CA) and on printed PETG: not found.
- CT-TAPE-FOAM / CT-TAPE-TIE (VHB-class double-sided tape): 3M VHB 4910 (1.0 mm clear) 90 deg peel 15 lb/in (260 N/100 mm, ASTM D3330, to stainless steel), normal tensile 100 lb/in2 (690 kPa, ASTM D897, to aluminum), dynamic overlap shear 70 lb/in2 (480 kPa, ASTM D1002, to stainless steel), static shear holds 1000 g on 0.5 in2 for 10,000 min at 22 C (ASTM D3654); 3M VHB Tapes Technical Data Nov 2005, p.4 and p.5, 4910 family rows.
- CT-TAPE-FOAM / CT-TAPE-TIE: 3M VHB 4950 (1.1 mm firm foam) peel 25 lb/in (440 N/100 mm), normal tensile 140 lb/in2 (970 kPa), dynamic overlap shear 80 lb/in2 (550 kPa); 3M VHB 4941 (1.1 mm conformable foam) peel 20 lb/in (350 N/100 mm), normal tensile 85 lb/in2 (585 kPa), dynamic overlap shear 70 lb/in2 (480 kPa); same sheet p.4 (row pairing read from a column-layout text extraction).
- CT-TAPE-SKIN: packing-tape skin strength (peel, tensile): not found (3M Scotch 375 TDS blocked).
- CT-TAPE-HINGE: tape hinge strength or fatigue: not found.
- CT-GEL-PAD: gel pad adhesion or load rating: not found.
- CT-LABEL: label adhesion: not found.

## How we could use it
- Feeds connection-type keys CT-EPOXY, CT-CA, CT-TAPE-FOAM and CT-TAPE-TIE (metal/plastic-substrate typical values only); CT-TAPE-SKIN, CT-TAPE-HINGE, CT-GEL-PAD and CT-LABEL have no value here.
- The bond-to-foam, bond-to-balsa and bond-to-printed-PETG strengths the bonded joints actually see are not given by any opened source; a coupon test would be needed to replace them.
