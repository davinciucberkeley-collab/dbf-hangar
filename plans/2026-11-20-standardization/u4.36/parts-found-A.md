# Parts found, lot A (motors, ESCs), W31-S1, checked 2026-11-24

Method: WebFetch opened each page listed; no browser. No vendor CAD link was on any opened page, so every part is `representative-envelope`. Blocked sites are listed at the end.

| part-id | category | vendor | part number | URL | mass g | envelope mm (x y z) | key spec | vendor CAD link | CAD licence | in library (yes/no, why not) |
|---|---|---|---|---|---|---|---|---|---|---|
| tmotor-mn3510-kv700 | motor | T-Motor | MN3510 KV700 | https://store.tmotor.com/goods.php?id=337 | 97 (excl. cables) | 28.5 41.8 41.8 | KV700 variant: 25 A / 555 W at 180 s; shaft 4 mm; page also lists KV360 (15 A/330 W) and KV630 (22 A/495 W) | not found | not stated | yes |
| freewing-2836-3300kv-mo028363 | motor | Freewing | MO028363 | https://motionrc.com/products/freewing-2836-3300kv-brushless-outrunner-motor-mo028363 | 85 (leads not found) | 74 28 28 | KV 3300; 35 A cont., 41 A burst 10 s; 520 W; shaft 3 mm | not found | not stated | yes |
| sunnysky-x2814-v3-900kv | motor | SunnySky | SS-XV3-X2814-900 | https://www.readymaderc.com/products/details/sunny-sky-x-series-v3-x2814-brushless-motor-900kv | 108 (leads not found) | 36 28 28 (body length; shaft not found) | KV 900; 50 A / 30 s; 680 W; 28 mm stator (2814, not 2836) | not found | not stated | yes (x excludes shaft length) |
| hobbywing-flyfun-30a-mini-v5 | esc | Hobbywing | 30202307 | https://www.hobbywing.com/en/products/flyfun-v5-series17 | 23 | 37 17 5 (axes not labelled) | 30 A / 45 A peak; 2-4S; BEC 5.2 V 3.5 A / 5 A; burst duration not found | not found | not stated | yes |
| hobbywing-flyfun-40a-v5 | esc | Hobbywing (retailer page) | 30214002 | https://hobbiesdirect.com.au/products/hobbywing-flyfun-40a-v5-series-brushless-esc-30214002-28207 | 44 | 47 28 14 | 40 A / 60 A, burst 10 s; 3-6S; BEC 5.2/6/7.4 V 8 A / 20 A | not found | not stated | yes (retailer source; S-count wider than 3-4S) |
| hobbywing-platinum-pro-40a-v4 | esc | Hobbywing (retailer page) | 30215001 | https://www.readymaderc.com/products/details/hobby-wing-platinum-pro-40a-v4-esc-bec | 47 | 48 30 15.4 | 40 A / 60 A (10 s); 3-4S; BEC 5-8 V 7 A | not found | not stated | yes |
| hobbywing-skywalker-30a (not written) | esc | Hobbywing | 30205350 | http://www.hobbywing.com/en/products/skywalker-series22.html | 37 | 68 25 8 (axes not labelled) | 30 A / 40 A; 2-3S; linear BEC 5 V 2 A | not found | not stated | no: 2-3S, outside the 3-4S brief |
| hobbywing-platinum-25a-v4 (not written) | esc | Hobbywing | 30204200 | http://www.hobbywing.com/en/products/platinum-25a-v4--platinum-40a-v468 | 27 | 47 22 10 (axes not labelled) | 25 A / 40 A; 3-6S; BEC 6/7.4 V 3 A | not found | not stated | no: 25 A, outside 30-50 A |
| hobbywing-skywalker-40a-v2 (not written) | esc | Hobbywing (retailer) | not found | not found (chinahobbyline.com, blocked) | not found | not found | search snippet only: 40 A / 60 A, 3-4S, BEC 5 V 5 A, 36 g; not verified | not found | not found | no: site blocked (HTTP 429), not opened |
| aerostar-30a-2a-bec (not written) | esc | HobbyKing | not found | not found (hobbyking.com blocked) | not found | not found | search snippet only: 30 A / 40 A, 2-4S; not verified | not found | not found | no: blocked: hobbyking.com (HTTP 403) |
| lumenier-40a-3-6s (not written) | esc | Lumenier (GetFPV) | not found | not found (getfpv.com blocked) | not found | not found | search snippet only: 40 A, 3-6S, BEC 3 A; not verified | not found | not found | no: blocked: getfpv.com (HTTP 403) |

## Count, lot A
- Candidates listed: 11 rows. Written to `knowledge/parts/`: 6 (3 motors, 3 ESCs).
- Not written: SkyWalker 30A (S-count 2-3S, outside brief); Platinum 25A V4 (25 A, outside 30-50 A); SkyWalker 40A V2, AeroStar 30A and Lumenier 40A (site blocked or not opened, so no facts from them).
- Blocked sites: chinahobbyline.com (HTTP 429, not retried), hobbyking.com (HTTP 403, two pages), getfpv.com (HTTP 403).

## Pass check output
(See scout hand-back; `parts list` and `parts show` run on the worktree branch.)
