---
id: std-ct-straps-hinges-thermal-2
title: Strap, cable tie, pitot tubing, clevis and hinge pin load sources (Velcro ONE-WRAP listings, Panduit PLT2S-M pages, McMaster-Carr versilic tubing, Gibbs and rs-online music wire PDFs, Machinery's Handbook dowel pin shear)
authors: Velcro Companies (sheets reviewed, no named author); Panduit Corp (product pages); McMaster-Carr (catalog page); Gibbs Wire (datasheets, unreadable); Machinery's Handbook 31st edition (editor not found on opened page)
year: unknown
url: https://www.cableorganizer.com/cdn/shop/files/VELCRO_Brand_ONE-WRAP_General_Purpose_Cable_Wrap.pdf
type: website
retrieved: 2026-11-23
verified: false
---

## Summary
Nothing in this run gives a usable ultimate load for the strap, cable tie, pitot tubing, clevis or hinge pin joint types. The Velcro ONE-WRAP sheets opened as unreadable PDFs or a tape holding claim, the Panduit PLT2S-M product page shows unfilled placeholders, and the McMaster-Carr tubing page gives pressure ratings only. The Gibbs and rs-online music wire PDFs are compressed and unreadable. The only number taken from an opened page is a steel dowel-pin single-shear stress (64,000 psi minimum) in Machinery's Handbook, which is a stress for a dowel pin, not a per-joint load. Verified is false because several opened PDFs had no readable text.

Opened sources: https://www.cableorganizer.com/cdn/shop/files/VELCRO_Brand_ONE-WRAP_General_Purpose_Cable_Wrap.pdf (compressed PDF, no readable strength text) ; https://velcro.com/general-use-velcro-brand-one-wrap-tape-tds (returned a Velcro logo PDF, not a spec sheet) ; https://www.velcro.com/?p=49544 ; https://docs.rs-online.com/c71d/0900766b81454b70.pdf (compressed PDF, no readable text) ; https://panduit.com/en/products/wire-routing-management-protection/cable-wire-ties-mounts-straps/cable-wire-ties/plt2s-m00.html (specification fields are unfilled placeholders) ; https://www.mcmaster.com/versilic-tubing ; https://www.gibbswire.com/pdf/preco-z-music-wire.pdf (compressed PDF, no readable text) ; https://www.gibbswire.com/wp-content/uploads/2025/08/Gibbs-Datasheet-Wire-10-Type-Corrostan-Music-Wire.pdf (compressed PDF, no readable text) ; https://docs.rs-online.com/d240/A700000009631396.pdf (compressed PDF, no readable text) ; https://www.blohm-gmbh.de/doc/de/en/did.252564/B0430_Datasheet_25427_Hinge_pins_steel_or_stainless_steel--en.pdf (compressed PDF, no shear value) ; https://online.flippingbook.com/view/954046886/464 (Machinery's Handbook, printed page 1883)
blocked: mouser.com (timeout, two attempts on the Panduit PLT2S-M PDF) ; farnell.com (timeout, datasheet 37387.pdf) ; static6.arrow.com (timeout, Panduit cable tie PDF) ; fluid-components.nordsonmedical.com (TLS error: unable to verify the first certificate; barb performance PDF)

## Usable rules / numbers
- [CT-STRAP-VELCRO] not found: no opened Velcro page or PDF gives a minimum or ultimate tensile or shear value for a 20 mm hook-and-loop strap. The ONE-WRAP cable wrap PDF (cableorganizer.com) was compressed and yielded no readable text. The velcro.com ONE-WRAP TDS URL returned a logo PDF.
- [CT-STRAP-VELCRO] velcro.com/?p=49544 (ONE-WRAP product page, product highlights): "Holds 1lb per square inch of tape used" (1 lbf/in² = 6.89476 kPa). This is a holding claim with no test method, no minimum, no width and no direction, so it is not usable as an ultimate rating.
- [CT-TIE] not found: the Panduit PLT2S-M00 product page (panduit.com, Specifications section) shows unfilled template placeholders with no loop tensile value. The docs.rs-online.com c71d PDF (Panduit-looking cable tie datasheet) is compressed and gave no readable text, and its manufacturer could not be confirmed. Mouser, Farnell and Arrow copies timed out. The existing 222 N library value rests on a distributor listing that was not re-opened in this run.
- [CT-PITOT-TUBING] not found: McMaster-Carr versilic tubing page (mcmaster.com/versilic-tubing) lists tubing ID, OD, wall, hardness, pressure at temperature and "Barbed" fitting connection, with no pull-off, retention or tensile force at any size. Example pressure rating shown: 20 psi at 72 °F for part 3184K286 (4 mm OD). The Nordson barb performance PDF was not opened (certificate error).
- [CT-CLEVIS] not found: Gibbs Preco Z music wire datasheet (gibbswire.com/pdf/preco-z-music-wire.pdf), Gibbs Corrostan music wire datasheet and rs-online A700000009631396 music wire PDF were all compressed with no readable diameter-versus-tensile table. No Du-Bro or clevis-maker page was opened; the search returned only auto-parts and farm clevises without load values.
- [CT-PIN-HINGE] Machinery's Handbook 31st edition, printed page 1883, section "American National Standard Unhardened Ground Dowel Pins", subheading "Shear Strength": steel pins "must have a single shear strength of 64,000 psi minimum" (64,000 psi = 441.26 MPa using 1 psi = 6.89476 kPa). This is a dowel-pin stress, not a hinge-pin load. No N per pin is given. The double-shear loads are in Table 3, which is not in the opened excerpt.
- [CT-PIN-HINGE] Blohm B0430 steel hinge pin datasheet (blohm-gmbh.de): opened; no shear, tensile or load value readable.

## How we could use it
- [CT-STRAP-VELCRO] stays pending: no ultimate tensile or shear value for a stated strap width.
- [CT-TIE] stays pending: the manufacturer loop-tensile figure was not readable. The library value remains the distributor-listing source until a Panduit or UL 62275 table is opened.
- [CT-PITOT-TUBING] stays pending: no pull-off value in any opened source.
- [CT-CLEVIS] stays pending: no diameter-and-strength table was readable.
- [CT-PIN-HINGE] rated_load_n stays pending. The 64,000 psi (441.26 MPa) single-shear minimum could go in a `note` as a dowel-pin stress, not as a rated load.

## Findings table

| type | key the gate needs | value | unit | direction / condition | source place | status |
|---|---|---|---|---|---|---|
| CT-STRAP-VELCRO | rated_load_n (20 mm strap) or stress for note | not found | N or N/cm2 | shear along strap, ultimate | cableorganizer ONE-WRAP PDF unreadable; velcro.com/?p=49544 holding claim 1 lbf/in2 (not usable) | pending: no opened source |
| CT-TIE | rated_load_n | not found | N | loop tensile, ultimate | panduit.com PLT2S-M00 page placeholders; docs.rs-online c71d PDF unreadable; mouser, farnell, arrow blocked | pending: no opened source |
| CT-PITOT-TUBING | rated_load_n | not found | N | axial pull-off from barb, ultimate | mcmaster.com/versilic-tubing: pressure ratings only | pending: no opened source |
| CT-CLEVIS | rated_load_n | not found | N | tension along rod, ultimate | gibbswire Preco Z and Corrostan PDFs and rs-online A700000009631396 unreadable; no clevis-maker page opened | pending: no opened source |
| CT-PIN-HINGE | rated_load_n (stress for note: 441.26 MPa) | not found (stress: 64,000 psi min) | N (stress: psi, MPa) | single shear of steel dowel pin, minimum; no per-pin N | Machinery's Handbook 31st ed. p.1883, Shear Strength (dowel pin basis; Table 3 not in excerpt) | pending: no opened source |
