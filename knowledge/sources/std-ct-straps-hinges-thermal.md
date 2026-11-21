---
id: std-ct-straps-hinges-thermal
title: Hook-and-loop, cable tie and thermal pad ratings (Velcro 13M Loop TDS, Velcro Velstick TDS, Panduit PLT2S-M listing, Bergquist Gap Pad 1500 TDS)
authors: Velcro Companies; Panduit Corp (via DigiKey listing); Bergquist / Henkel
year: 2025
url: https://www.trivantage.com/itemfiles/pdfs/tds/VELCRO_Essentials_13M_Loop_Specifications.pdf
type: website
retrieved: 2026-11-20
verified: true
---

## Summary
Manufacturer data sheets and one distributor listing for the hook-and-loop, cable tie and thermal pad parts used in the strapped and thermal connection types. Velcro gives closure peel and shear for two hook-and-loop pairs and says the values are typical, not for specification. The Panduit PLT2S-M listing gives a loop tensile rating. The Bergquist Gap Pad 1500 sheet gives thermal conductivity and thermal impedance against compression.

Opened sources: https://www.trivantage.com/itemfiles/pdfs/tds/VELCRO_Essentials_13M_Loop_Specifications.pdf ; https://www.trivantage.com/itemfiles/pdfs/tds/VELCRO_Velstick_Specifications.pdf ; https://www.digikey.com/en/products/detail/panduit-corp/PLT2S-M/280044 ; https://www.stockwell.com/data-sheets/thermal-bq-gap-pad-1500.pdf
blocked: farnell.com (Velcro and Panduit PDFs, fetch timed out); mouser.com (Bergquist TGP 3000 PDF, fetch timed out); henkel-adhesives.com (TGP 1500 page returned 404 after redirect).

## Usable rules / numbers
- [CT-STRAP-VELCRO, CT-HATCH-HL] Velcro 13M Loop tested with 13G Hook: peel average 2 N/cm (1.1 PIW), shear average 10 N/cm² (14.5 psi); values marked average and for reference only (13M Loop TDS-00412, Feb 2025, page 1, "Performance characteristics").
- [CT-STRAP-VELCRO, CT-HATCH-HL] Velcro Velstick hook 088 tested with Loop 1000: hook closure peel minimum 0.876 N/cm (0.50 PIW), hook closure shear minimum 11 N/cm² (16.0 lb); sheet states typical values, "should not be used for specification purposes" (Velstick 192657 TDS, rev 02, July 2020, page 1, "Performance characteristics").
- [CT-TIE] Panduit PLT2S-M nylon 6/6 locking cable tie, 4.83 mm (0.190 in) wide, 188 mm long: tensile strength 50 lb (22.68 kg) (DigiKey product page, "Product Attributes"; distributor listing, not the Panduit datasheet).
- [CT-THERMAL-PAD] Bergquist Gap Pad 1500: thermal conductivity 1.5 W/m-K (ASTM D5470); thickness 0.508 to 5.080 mm; hardness 40 Shore 00 (ASTM D2240); thermal impedance of the 0.040 in pad 1.62 / 1.50 / 1.33 °C-in²/W at 10 / 20 / 30 % strain (TDS Gap Pad 1500, July 2011, "Typical properties" and "Thermal performance vs. strain" tables).
- CT-STRAP-SLOT: strap tensile (webbing) not found in opened sources.
- CT-TUBE-CLAMP, CT-CRADLE-CONTACT, CT-PLUG-IN, CT-WIRE-CHANNEL, CT-PITOT-TUBING, CT-PIN-HINGE, CT-CLEVIS, CT-SERVO-SPLINE, CT-THERMAL-CONTACT: not found (no manufacturer load or conductance value in any opened source; a search for RC clevis load ratings returned no published value).

## How we could use it
- Feeds `CT-STRAP-VELCRO`, `CT-HATCH-HL` (hook-and-loop closure shear and peel, multiply by tab area or width), `CT-TIE` (loop tensile) and `CT-THERMAL-PAD` (conductivity and impedance) in standards/connection-types.yaml.
- Keys listed as not found stay `pending`.
