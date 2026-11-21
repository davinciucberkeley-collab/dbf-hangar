---
id: std-ct-electrical
title: Connector current and voltage ratings for electrical connection types (Amass XT60-F spec, Amass catalogue, JST GH series page, Holybro connector rating, ExpressLRS hardware selection)
authors: Changzhou Amass Electronics Co. Ltd.; J.S.T. Mfg. Co. Ltd.; Holybro; ExpressLRS project; RS PRO; Unmanned Tech
year: 2025
url: https://www.china-amass.net/uploads/57.XT60-F-SPEC-2025V0.pdf
type: website
retrieved: 2026-11-20
verified: true
---

## Summary
Maker ratings for the battery, motor-phase and signal connectors in the connection-type library. Opened: Amass XT60-F product spec 2025V0 (https://www.china-amass.net/uploads/57.XT60-F-SPEC-2025V0.pdf); Amass product catalogue, undated distributor copy (https://www.rcscomponents.kiev.ua/datasheets/Amas-cat1.pdf); RS PRO XT60L datasheet (https://docs.rs-online.com/4d7b/A700000008956715.pdf); Holybro "Connector & Wire Rating" (https://docs.holybro.com/power-module-and-pdb/power-module/connector-and-wire-rating); Unmanned Tech connector guide, 2026-05-15 (https://www.unmannedtechshop.co.uk/blogs/knowledge-base/fpv-drone-battery-connector-guide-xt30-xt60-xt90-ratings); JST GH series page (https://www.jst-mfg.com/product/detail_e.php?series=105); ExpressLRS hardware selection (https://www.expresslrs.org/hardware/hardware-selection/). Amass gives a "MAX" current tied to a wire gauge and a temperature-rise limit (shown as "<85" in the catalogue text; the unit symbol did not extract). Holybro and Unmanned Tech give lower continuous figures over a stated duration. No maker rating was found for gold bullets, solder joints or JR servo connectors. The JST GH datasheet PDFs (Mouser, Farnell) timed out; only the JST web page was read.

## Usable rules / numbers
- [CT-XT60] Amass XT60-F: current rating 35 A (12 AWG, temperature rise <= 85 K), rated voltage 80 V DC, contact resistance 1.0 mOhm (Amass XT60-F spec 2025V0, "Electrical SPEC" table, p. 1).
- [CT-XT60] Amass catalogue, XT60 / XT60U / XT60H: 35 A MAX (12 AWG, rise < 85), 500 V DC, temperature -20 to 120 (catalogue p. 13, "Specifications" table).
- [CT-XT60] Genuine Amass XT60, 12 AWG: 30 A continuous (4 h, rise < 60 C), 60 A burst (1 min, rise < 60 C) (Holybro, "Genuine AMASS Connector Rating" table). Same 30 A / 60 A on RS PRO XT60L datasheet ("Material & Parameter", rated 30 A, momentary 60 A, DC 500 V, 12 AWG) and Unmanned Tech guide ("XT30 vs XT60 vs XT90: The Useful Numbers").
- [CT-XT90] Amass catalogue, XT90H / XT90HW / XT90S: 45 A MAX (10 AWG, rise < 85), 500 V DC (catalogue p. 21, "Specifications" table). Holybro: XT90, 10 AWG, 45 A continuous (4 h), 90 A burst (1 min) ("Genuine AMASS Connector Rating" table).
- [CT-AS150U] Amass catalogue, AS150U: 75 A MAX (8 AWG, rise < 85), 500 V (catalogue p. 27, "Specifications" table). Holybro: AS150, 8 AWG, 75 A continuous (4 h), 150 A burst (1 min) ("Genuine AMASS Connector Rating" table). The 70 A / 140 A in the library spec was not found in an opened source.
- [CT-MR30] Amass catalogue, MR30 / MT30: 20 A MAX (16 AWG, rise < 85), 500 V DC, temperature -20 to 120 (catalogue p. 9, "Specifications" table).
- [CT-JST-GH-4] [CT-JST-GH-6] JST GH series, 1.25 mm pitch: rated current 1 A AC/DC (AWG #26), rated voltage 50 V AC/DC, temperature -40 to +105 C, wire AWG #30 to #26 (JST GH series page, specifications).
- [CT-ELRS-RF] ExpressLRS: RF chip without PA about +13 dBm (20 mW); most receiver PAs 20 dBm (100 mW); most transmitters capped at 250 mW or 500 mW, some 1 W; 5 km at 250 Hz / 100 mW line of sight for a ceramic-antenna receiver (ExpressLRS hardware selection, "Receiver Selection: PA/LNA, Range" and "Transmitter Selection: Power").
- [CT-BULLET-3] not found (no maker datasheet for RC gold bullet connectors opened; search results were audio jacks).
- [CT-SOLDER-PHASE] [CT-SOLDER-DC] not found.
- [CT-SERVO-JR] not found (Pololu / Core Electronics JR packs give no current rating, per search listing; no datasheet opened).

## How we could use it
- Feeds connection-type ratings in `standards/connection-types.yaml` for `CT-XT60`, `CT-XT90`, `CT-AS150U`, `CT-MR30`, `CT-JST-GH-4`, `CT-JST-GH-6`, `CT-ELRS-RF`.
- `CT-BULLET-3`, `CT-SOLDER-PHASE`, `CT-SOLDER-DC`, `CT-SERVO-JR` stay pending (not found).
