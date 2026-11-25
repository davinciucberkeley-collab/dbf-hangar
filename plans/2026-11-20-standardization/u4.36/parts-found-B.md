# Parts found, lot B (servos, receivers), W31-S1, checked 2026-11-24

Method: WebFetch opened each page listed; no browser. No vendor CAD link was on any opened page, so every part is `representative-envelope`. Blocked sites are listed at the end.

| part-id | category | vendor | part number | URL | mass g | envelope mm (x y z) | key spec | vendor CAD link | CAD licence | in library (yes/no, why not) |
|---|---|---|---|---|---|---|---|---|---|---|
| freewing-md31093-500 | servo | Freewing | MD31093-500 | https://motionrc.com/eu/products/freewing-9g-digital-hybrid-metal-gear-servo-with-500mm-19-6-lead-md31093-500 | 13 | 23.5 12.2 26.4 | 1.5 kg-cm @4.8 V, 1.8 kg-cm @6.0 V; 0.12 s/60 deg @4.8 V; hybrid (metal and plastic) gears; 4.8-6 V | not found | not stated | yes |
| emax-es08maii-metal | servo | EMAX | EMX-SV-0275 | https://amainhobbies.com/emax-es08maii-12g-analog-metal-gear-servo-emx-sv-0275/p667829 | 12 | 23 11.5 24 | 21 oz/in (~1.51 kg-cm) @4.8 V, 25.2 oz/in (~1.81 kg-cm) @6.0 V; 0.12 s/60 deg @4.8 V; metal gear; analog | not found | not stated | yes (retailer source; torque converted from oz/in) |
| towerpro-mg90s | servo | TowerPro | TP-MG90S | https://www.readymaderc.com/products/details/86506-towerpro-mg90s-metal-gear-servo-90-degree-rotation | 13.4 | 22.8 12.2 28.5 | 1.8 kg/cm @4.8 V, 2.2 kg/cm @6.0 V; 0.10 s/60 deg @4.8 V; metal gear (aluminium 6061-T6 per page) | not found | none stated | yes (retailer source) |
| emax-es08maii-hv (not written) | servo | EMAX | ES08MAIIHV | https://www.readymaderc.com/products/details/85973-emax-es08ma-ii-hv-high-voltage-12g-metal-gear-servo | 12 +/- 1 | not found | 1.4 kg-cm @6.0 V; 0.17 s/60 deg @6.0 V; metal gear; 6.0-8.4 V | not found | not stated | no: envelope dimensions not found |
| hitec-hs-5055mg (not written) | servo | Hitec | HRC35055S | https://motionrc.com/collections/hitec-servos/products/hitec-hs-5055mg-9g-digital-metal-gear-micro-servo-hrc35055s | not found | not found | search snippet only (1.2 kg-cm @4.8 V, 22.6 x 11.4 x 23.8 mm); page returned HTTP 404, not verified | not found | not found | no: page not found (404) |
| tgy2301mg (not written) | servo | HobbyKing | TGY2301MG | https://hobbyking.com/hk-9g-full-metal-gear-micro-servo-tgy2301mg.html | not found | not found | search snippet only; not verified | not found | not found | no: blocked: hobbyking.com (HTTP 403) |
| robotshop 9 g 1.3 kg-cm servo (not written) | servo | Robotshop | not found | https://www.robotshop.com/en/9g-micro-servo-motor-4-8v.html | not found | not found | search snippet only; not verified | not found | not found | no: blocked: robotshop.com (HTTP 403) |
| radiomaster-xr2-nano | receiver | RadioMaster | HP0157-XR2 | https://motionrc.com/products/radiomaster-xr2-nano-2-4ghz-elrs-receiver-hp0157-xr2 | 0.8 (antenna inclusion not stated) | 16 12 6 | 16 channels; Semtech LR1121; 5 V; integrated tower antenna (length not found); output PWM/CRSF not found | not found | not stated | yes (mass below the 5-12 g class; conductor to choose) |
| radiomaster-er5a | receiver | RadioMaster | RMS-ER5A | https://www.readymaderc.com/products/details/radiomaster-er5a-24ghz-5ch-elrs-pwm-receiver | 6.6 (antenna inclusion not stated) | 37 19 13 | 5 PWM channels (4 proportional + 1 switch on ELRS 2.x); 4.5-8.4 V; T-shape antenna (length not found) | not found | not stated | yes |
| emax-aeris-link-24 | receiver | EMAX | AERIS24RX-0107001004 | https://www.readymaderc.com/products/details/85572-emax-aeris-link-2-4ghz-expresslrs-receiver-with-micro-t-antenna | 0.6 (without antenna) | 15 10 2 | micro T antenna via u.FL; channels not found; output not found; input voltage not found | not found | not stated | yes (mass below the 5-12 g class; channels not found) |
| betafpv-elrs-micro (not written) | receiver | BETAFPV | not found | https://betafpv.com/products/elrs-micro-receiver | not found | not found | search snippet only (about 4.5 g with antenna, 5 PWM or CRSF); not verified | not found | not found | no: blocked: betafpv.com (HTTP 429, three attempts) |

## Count, lot B
- Candidates listed: 11 rows (7 servo rows, 4 receiver rows). Written to `knowledge/parts/`: 6 (3 servos, 3 receivers).
- Not written: ES08MA II HV (envelope not found); Hitec HS-5055MG (page 404); TGY2301MG and Robotshop 9 g (blocked); BETAFPV ELRS micro (blocked).
- Blocked sites: hobbyking.com (HTTP 403), robotshop.com (HTTP 403), betafpv.com (HTTP 429, three attempts). motionrc.com Hitec page returned HTTP 404 (not blocked; not found).

## Pass check output
(See scout hand-back; `parts list` and `parts show` run on the worktree branch.)
