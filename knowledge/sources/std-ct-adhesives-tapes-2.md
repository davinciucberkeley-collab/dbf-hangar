---
id: std-ct-adhesives-tapes-2
title: Adhesive and tape strengths for CT-TAPE-FOAM, CT-EPOXY, CT-CA, CT-TAPE-HINGE and CT-GEL-PAD (3M VHB Tapes Technical Data, June 2011, Digi-Key-hosted copy; 3M Performance Plus Duct Tape 8979 TDS, Aug 2019; tesa 4287 product page; Permabond 240 TDS Rev 6; WEST SYSTEM and Epoxyworks wood adhesion articles; Sorbothane catalogue)
authors: 3M; tesa SE; Permabond; Gougeon Brothers, Inc. (WEST SYSTEM); Tom Pawlak (Epoxyworks article); Sorbothane, Inc.
year: 2011 (VHB copy), 2019 (8979), 2025 (Permabond 240 Rev 6), 2003 (Pawlak wood article), unknown (tesa page, WEST SYSTEM page, Sorbothane catalogue)
url: https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/2606/VHB%20tapes.pdf
type: website
retrieved: 2026-11-23
verified: true
---

## Summary
Scout W21-S1 (U4.19 step 2, adhesives and tapes) read the second-pass sources for the five types. Opened and read: 3M VHB Tapes Technical Data, June 2011 (Digi-Key-hosted copy), pages 4 and 5; 3M Performance Plus Duct Tape 8979 TDS, Aug 2019 (RS-hosted copy); tesa 4287 product page; Permabond 240 TDS Rev 6 (13 Sep 2025); WEST SYSTEM "Testing/ASTM" page (westsystem.com/?p=2618); Epoxyworks "Epoxy's Adhesion to Wood" (Spring 2003); Sorbothane catalogue. Sourced: foam-tape stresses to metal (no plastic value), wood tensile adhesion for a 105/206 epoxy, cyanoacrylate shear on ABS and polycarbonate (lower bounds), hinge tape tensile and adhesion. Not found: epoxy lap shear, CA on foam or balsa, a gel-pad load or adhesion value.

Opened sources: https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/2606/VHB%20tapes.pdf ; https://www.digikey.cn/htmldatasheets/production/2421873/0/0/1/VHB-Specialty-Tape-Datasheet.pdf (HTTP 410, not used) ; https://www.westsystem.com/?p=2618 ; https://www.epoxyworks.com/epoxys-adhesion-to-wood/ ; https://www.epoxyworks.com/bond-lines-adhesive-bonded-structures/ ; https://permabond.com/wp-content/uploads/2025/11/240_TDS-1.pdf ; https://assets.rs-online.com/v1698350197/Datasheets/9d852395e641f4c1bd71115ac4dcdb0b.pdf ; https://www.tesa.com/en-us/industry/tesa-4287.html ; https://www.sorbothane.com/wp-content/uploads/Sorbothane-SPG.pdf

blocked: multimedia.3m.com (HTTP 403, 3M 8979 application flyer, 375493O) ; www.3m.com (HTTP 403, VHB product page b40072028, en_XW locale) ; manualmachine.com (HTTP 403, VHB technical data copy) ; sg.rs-online.com (HTTP 403, Taica GC-4 page 0474836) ; www.flyingtech.co.uk (HTTP 403, Kyosho Zeal mounting gel) ; www.farnell.com (timeout, 3M-type 184114.pdf) ; digikey.cn (HTTP 410, VHB specialty datasheet) ; docs.rs-online.com (PDF encrypted, text unreadable, f080/0900766b81446fb3.pdf). Not used: Scotch 375 and 375+ TDS (search snippets only, not opened).

## Usable rules / numbers
- Erratum (W21-R review, 2026-11-25; table below not edited): the 4950 row in the June 2011 p.4 table reads 25 lb/in (440 N/100 mm) peel, 140 lb/in2 (970 kPa) normal tensile, 80 lb/in2 (550 kPa) dynamic overlap shear, the same as the 2005 sheet. The 20 / 160 / 100 values above belong to 4929, 4930 and 4949. So there is no conflict between the sheets. The 4910 1.0 mm row reads 15 lb/in (260 N/100 mm) peel, 100 lb/in2 (690 kPa), 70 lb/in2 (480 kPa). The 480 kPa used in standards is unchanged.
- [CT-TAPE-FOAM] 3M VHB 4941 family row, June 2011 copy, p.4 "Dynamic Adhesion Performance": 90 deg peel 22 lb/in (385 N/100 mm) to stainless steel, ASTM D3330; normal tensile 85 lb/in2 (585 kPa) to aluminum, ASTM D897; dynamic overlap shear 70 lb/in2 (480 kPa) to stainless steel, ASTM D1002. Typical, not for specification (p.4 note). Row pairing read from a layout text extraction.
- [CT-TAPE-FOAM] 3M VHB 4950 family row, same table, p.4: 90 deg peel 20 lb/in (350 N/100 mm) to stainless steel; normal tensile 160 lb/in2 (1100 kPa) to aluminum; dynamic overlap shear 100 lb/in2 (690 kPa) to stainless steel. This peel conflicts with the 25 lb/in (440 N/100 mm) recorded from the 2005 sheet in std-ct-adhesives-tapes; not resolved here.
- [CT-TAPE-FOAM] 3M VHB 4910 family, same table, p.4: the printed row for the 0.020 in clear product shows 12 lb/in (210 N/100 mm) peel, 100 lb/in2 (690 kPa) normal tensile, 70 lb/in2 (480 kPa) dynamic overlap shear; the 1.0 mm (0.040 in) row has no separate values printed in the extraction.
- [CT-TAPE-FOAM] Static shear, same copy, p.5 "Static Shear" table, ASTM D3654 to stainless steel: 4941 family 1000 g per 0.5 in2 at 72 F held 10,000 min; 4950 family 1500 g per 0.5 in2 at 72 F. This is a hold value, not an ultimate value, and is not usable as the gate's ultimate stress.
- [CT-TAPE-FOAM] Peel or shear to ABS, polycarbonate or other plastics: not found in any opened source. The June 2011 copy's surface-energy chart (no page number read) ranks ABS and polycarbonate in a "medium" band with no number; it is not usable.
- [CT-EPOXY] WEST SYSTEM 105 with 206 slow hardener, wood tensile adhesion (PATTI pull-off, tension), Pawlak, Epoxyworks Spring 2003, table "Average bond strength by species (psi)": lowest species Narra 994 psi and Padauk 994 psi (= 6.85 MPa, using 1 psi = 6.89476 kPa); highest Tambootie 2033 psi (= 14.02 MPa). Failure in the wood in every case; the author notes two specimens per species is not conclusive.
- [CT-EPOXY] WEST SYSTEM 105/205 lap shear on aluminium, wood, carbon fibre, ABS or PETG: not found. westsystem.com/?p=2618 gives tensile adhesion only for G/flex 650 and 655 (ABS 1535 psi and 3288 psi; wood 1503 to 2223 psi). G/flex is a different product and is not used. Epoxyworks "bond lines" article (no 105/205 lap shear value, no units) also checked.
- [CT-EPOXY] 30 min laminating epoxy ASTM D1002 MPa value from a 3M EC-1751 snippet: not used (cure at 200 F, not a laminating system; not opened).
- [CT-CA] Permabond 240 cyanoacrylate, TDS Rev 6, 13 Sep 2025, p.1 "Typical Performance of Cured Adhesive", shear strength ISO 4587: ABS >8 N/mm2 (>1200 psi), substrate failure (SF); PC >5 N/mm2 (>700 psi), SF; steel 21 to 25 N/mm2; aluminium 8 to 9 N/mm2. The ">" values are lower bounds; the sheet calls the values typical and says strength varies with surface prep and gap.
- [CT-CA] Permabond 240, same page: the TDS says it is "ideal for porous substrates" and suitable for plastics, but gives no balsa, wood or foam shear number and no foam-safe statement. Balsa and foam: not found.
- [CT-CA] LOCTITE 401 values already in std-ct-adhesives-tapes (not repeated).
- [CT-TAPE-HINGE] 3M Performance Plus Duct Tape 8979, TDS last revised Aug 2019, p.1 "Typical Performance Characteristics": tensile strength 64 N/cm (ASTM D3759), elongation 17 %; 180 deg peel adhesion 6.2 N/cm (57 oz/in, ASTM D3330, 12 in/min). The sheet says the values are typical and not for specification. Substrate for the peel is not stated in the extracted text.
- [CT-TAPE-HINGE] tesa 4287 (product page tesa.com/en-us/industry/tesa-4287.html, code "EU PV10" as printed): tensile strength 190 N/cm (108.49 lbs/in) and adhesion to steel 6 N/cm (3.43 lbs/in), elongation 35 %. The page gives no test standard and says the data are average values, not appropriate for a specification.
- [CT-TAPE-HINGE] Tape hinge (elevon) fatigue or hinge-line rating: not found.
- [CT-GEL-PAD] Sorbothane catalogue (sorbothane.com Sorbothane-SPG.pdf): the PSA-backed hemisphere and bushing products carry "rated load" values in lb. These are compression loads under 10 to 30 % deflection, per isolator, not pull-off or shear. No adhesion, peel or shear value for any product. Not usable as rated_load_n for a 5 mm gel pad.
- [CT-GEL-PAD] Zeal 5 mm adhesive gel pad datasheet: not found in search; the only Zeal listing is a retailer page (blocked, 403). Taica gel chips (5 mm) listed on RS without load or adhesion values (page blocked, 403; snippet only, not used).

## How we could use it
- [CT-TAPE-FOAM] Stress for the type's note: the lowest sourced ultimate stress is 480 kPa (dynamic overlap shear, 4941 and 4910 rows, stainless steel). Plastic (ABS, PC) peel stays pending. The builder keeps the type without rated_load_n.
- [CT-EPOXY] Stress for the note: 6.85 MPa tensile adhesion to wood (PATTI, 105/206), area-dependent. Lap shear and plastic or foam bond stay pending.
- [CT-CA] Stress for the note: 5 MPa lower bound on polycarbonate (SF). Foam-safe and balsa values stay pending.
- [CT-TAPE-HINGE] Tensile in N/cm of width (64 N/cm for 8979, 190 N/cm for tesa 4287) and adhesion in N/cm (6.2 and 6 N/cm to steel) as separate rows; rated_load_n stays pending because no tape width is stated in the hinge spec.
- [CT-GEL-PAD] Stays pending: no opened source gives a load, adhesion, shear or pull-off value for a 5 mm adhesive gel pad.

## Findings table
type | key the gate needs | value | unit | direction / condition | source place | status
CT-TAPE-FOAM | stress for the note (area-dependent) | 480 | kPa | dynamic overlap shear, ASTM D1002, to stainless steel, 4941/4910 rows (metal only); peel to ABS/PC not found | std-ct-adhesives-tapes-2: VHB Tapes Technical Data June 2011 (Digi-Key copy) p.4 "Dynamic Adhesion Performance" | sourced
CT-EPOXY | stress for the note (area-dependent) | 6.85 | MPa | tensile pull-off (PATTI), wood, WEST SYSTEM 105/206, lowest species (Narra, Padauk 994 psi); lap shear not found | Pawlak, Epoxyworks Spring 2003, species table (epoxyworks.com/epoxys-adhesion-to-wood/) | sourced
CT-CA | stress for the note | 5 | MPa (N/mm2) | ISO 4587 shear, polycarbonate, substrate failure, lower bound (>5); typical; foam and balsa not found | Permabond 240 TDS Rev 6, 13 Sep 2025, p.1 "Typical Performance of Cured Adhesive" | sourced
CT-TAPE-HINGE | N per cm width, tensile (ultimate) | 64 | N/cm | tensile, ASTM D3759, 3M 8979, typical; tesa 4287 gives 190 N/cm; adhesion 6.2 N/cm (ASTM D3330) listed separately | 3M Performance Plus Duct Tape 8979 TDS, Aug 2019, p.1 "Typical Performance Characteristics" (assets.rs-online.com copy) | sourced
CT-GEL-PAD | rated_load_n per pad, or kPa | not found | N or kPa | pull-off or shear: no opened source; Sorbothane rated loads are compression, not adhesion | Sorbothane catalogue (Sorbothane-SPG.pdf), isolator tables | pending: no opened source
