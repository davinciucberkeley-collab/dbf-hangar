# Recon: control-surface throws and servo travel (W34-X3, U16.4)

Question: sane default surface deflection for `plane design add-linkage`. Access date for all URLs: 2026-11-26.

## Today's defaults (core/hangar/ops/linkage.py, brief U16.1)

`input_range=20`, `servo_range=30`, `arm_length=6`, horn lever about 13 mm. The brief's worked example has gate ratio -0.49 and solved follower angles of 9.74 deg at input -20 (4.9 at -10). So today's default is **about ±9.7 deg at ±20 deg input** (±4.9 at ±10), not ±5 at full input. Linkage ratio about 0.49 deg/deg is arm/horn lever (6/13 = 0.46 plus geometry).

## Table

Throws are as printed. Degrees are my conversion where a chord was needed: delta = atan(throw / chord). **No page I opened states the surface chord**, so chords are assumed (flagged "est."). Treat est. degrees as ±3 deg.

| Source | Class | Elevator | Aileron | Rudder | Rates | URL |
|---|---|---|---|---|---|---|
| Top Flite Cessna 182 Skylane .60-.91 (TOPA0300 manual p.52; 81 in span, 898 sq in, per Horizon listing) | Scale GA, 1:~5 high wing (closest to our C172 case) | 1-1/16 in hi, 3/4 in lo, up=down. est. chord 3.0 in: atan(1.0625/3.0)=19.5 hi, atan(0.75/3.0)=14.0 lo | 5/8 in hi, 1/2 in lo. est. chord 2.5 in: atan(0.625/2.5)=14.0 hi, atan(0.5/2.5)=11.3 lo | 1 in hi, 5/8 in lo. est. chord 4 in: atan(1/4)=14.0 hi, 8.9 lo | high and low; "measured at the widest part" | https://www.manualsdir.com/manuals/714583/top-flite-topa0300.html?page=52 |
| E-flite Rhapsody 25e ARF (p.19) | Sport trainer | 25 mm hi, 13 mm lo. est. chord 60 mm: atan(25/60)=22.6 hi, 12.2 lo | 15 mm hi, 9 mm lo. est. chord 45 mm: 18.4 hi, 11.3 lo | 50 mm hi, 38 mm lo. est. chord 100 mm: 26.6 hi, 20.8 lo | high and low; "at the inner or widest point"; "general guidelines ... higher rates can be tried" | https://www.manualsdir.com/manuals/591079/e-flite-rhapsody-25e-arf.html?page=19 |
| E-flite J-3 Cub 25 ARF (p.48) | Scale trainer | 5/8 in hi, 3/8 in lo (no chord given) | 3/4 in hi, 1/2 in lo | 1-3/8 in hi, 1 in lo (low-rate side typo in page) | high and low, expo 20/10 %; "good starting point for most flight conditions"; measurement point not stated | https://www.manualsdir.com/manuals/591081/e-flite-j-3-cub-25-arf.html?page=48 |
| Skywalker X8 Pro build guide (uavmodel blog; third-party, unverified) | Small fixed-wing UAV, aileron/elevator/rudder variant | ±12-15 mm | ±15-20 mm | ±20-25 mm | single setting; chord not stated, so no degree conversion | https://blog.uavmodel.com/?p=2267 |
| ArduPilot Plane, Four Channel Planes | Autopilot doc | not given in degrees; says throws come from the airframe instructions "in millimeters or inches ... of the trailing edge"; SERVOn_MIN/MAX default 1100-1900 us, "1000 to 2000 or beyond is normal" | same | same | none | https://ardupilot.org/plane/docs/guide-four-channel-plane.html |
| Full-size Cessna 172 TCDS 3A12 (knowledge/sources/std-faa-tcds-3a12-text.md, p.30) | Full-size reference | up 28 (+1/-0), down 23 (+1/-0) | up 20 ±1, down 15 ±1 | 16 deg 10 min (waterline) or 17 deg 44 min (perp. to hinge), ±1, each side | rigging limits, no rates | local file, cited as opened |

Reading the table: scale/trainer RC models run roughly ±11-20 deg on aileron and ±12-23 deg on elevator, with low rate about 60-75 % of high; rudder ±9-27. Full-size C172 is 15-28 deg elevator/aileron and 16-18 rudder, i.e. the same band; RC high rate is about the full-size value, low rate is about 2/3 of it. The "est." numbers depend on assumed chords; the ratio of low to high (0.5-0.75) does not.

## Servo travel

- Pulse: ArduPilot says 1100-1900 us default and "1000 to 2000 or beyond is normal" (page above, opened).
- Rotation: ServoCity lists HS-82MG at 165 deg maximum with a travel tuner (600-2200 us); Atlanta Hobby chart gives 1500-1900 us travel; Hitec states 900-2100 us at 50 Hz. These came from search-result snippets only (https://www.servocity.com/hs-82mg-servo/, https://www.atlantahobby.com/collections/all/products/hs82mg-micro-servo-universal, https://www.multiplex-rc.de/userdata/files/HiTEC_servos_industry_catalog_2026_V02-EN.pdf); I did not open those pages. The Hitec HS-85MG datasheet (digikey PDF) opened but was unreadable (compressed), so "40 deg per side at 400 us" is a snippet figure only, unverified.
- Practical value: a standard hobby servo gives about ±40-45 deg of horn travel at 1000-2000 us; a flight controller or radio at default 1100-1900 us gives about ±30-35. So **servo_range 30 is a sound limit and ±20 input leaves margin**; ±45-60 is not supported by a page I opened.

## Failed or partial

- manualmachine.com Top Flite A0906 manual: HTTP 403 (no chords obtained).
- No E-flite Cessna 182 / FMS / Durafly / Volantex manual with throws opened; search returned only the E-flite and Top Flite pages above. FMS 1500 mm C182 listing seen in search but not opened.
- No UAV source states throws in degrees; ArduPilot defers to the airframe maker. Skywalker figures are an unverified third-party blog.
- Pages opened: 8 (3 manual pages, ArduPilot four-channel, uavmodel blog, HS-85MG PDF failed to extract, manualmachine 403, plus the TCDS file and linkage.py locally).

## Ranked recommendation for add-linkage defaults

1. **Default target deflection ±15 deg** for all three surfaces (between low rate ≈ 11-14 and high rate ≈ 14-22 on the Top Flite C182, about the aileron full-size figure of 15-20, about the rudder full-size 16-18, below elevator full-size 23-28 which is a rigging limit rather than a flight rate). Safe first-flight value; users override per surface (elevator 20, rudder 20, aileron 12 are reasonable).
2. **Make it a target the op solves for.** New param `--deflection 15` (deg, each side). Keep `input_range=20` (servo ±30 limit leaves 1.5x margin, and 20 deg is a comfortable servo arc for the four-bar transmission angle) and compute the needed ratio r = 15/20 = 0.75, then set arm length = r × horn lever. With today's horn lever about 13 mm that is an arm of about 9.7 mm (today 6 mm gives 0.46-0.49); with horn 8 mm it is 6 mm. Refuse (clear error) if the arm would be at or above W (shaft-to-pin distance, already tested in `_tip`) or the ratio needs the arm longer than the servo arm fits. Report the achieved deflection in `data` (it already reports `ratio`). Keep `--arm-length` as an explicit override that wins over `--deflection`.
3. **Fixed input range alone is worse**: today's ±9.7 deg at ±20 is below even the low-rate band of every source (11-20 deg) and below full-size rigging (15-28), so it under-controls; and a fixed input range hides the intent (deflection is what a designer specifies and what stability/control checks use). Fallback if solving is out of scope: change defaults to arm 9 mm with horn about 12-13 mm (ratio about 0.7), input 20, servo 30, giving ±14-15 deg.

Cheapest test: `plane design add-linkage` on tests/fixtures/linkage-op/plane.yaml with `--arm-length 9.7`, then T6 `simulate_mechanism` follower at input ±20 should read about ±15 (follower scales near-linearly: brief's data 9.74 deg at 20 for ratio 0.49); check `min_transmission_deg` stays above 60 (brief's current bar) since longer arm lowers it.

## Cross-check: C172 against std-faa-tcds-3a12-text.md

Opened locally, line 23: ailerons up 20 ±1, down 15 ±1; elevator up 28 (+1/-0), down 23 (+1/-0), elevator tab up 22 / down 19; rudder 16 deg 10 min parallel to waterline or 17 deg 44 min perpendicular to hinge, ±1 each side; flaps takeoff 0-10, landing 0-30 (p.30). These are asymmetric rigging limits for the real aircraft; they all fall within or just above the RC band, so a symmetric ±15 default is conservative against them (aileron 15 = the down limit; elevator and rudder under their limits).
