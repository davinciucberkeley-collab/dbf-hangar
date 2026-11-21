---
id: build-sequence
title: Build Sequence
topic: build-sequence
source_repo: DBF-Combined @ a93f14d
source_rows: [D3#7, D5#17, G1#25, G1#26, G1#27, G2#2, G2#14, G2#15, G2#19, G2#22, G2#26, G2#34, G2#35, G2#36, G2#40, G2#45, G4#8, G4#14, I2#12, J5#14, J5#15]
created: 2026-11-21
verified: false
---

## Purpose
The order of the build from the start of the core chain through the wing, fin, cartridges and assembly, and the rules the build manual must follow. Run at the start of each build stage.

## Steps
1. Start the core chain at the first cut, with the people and the workspace arranged in advance [I2#12]
2. Build the fin test article as a rehearsal before the real parts [G2#45]
3. Cut the XPS blank to size [G2#2]
4. Cut the P-02 spar slot [G2#14]
5. Cut the P-02 block pockets from the printed template, with chamfered lips [G2#15]
6. Cut the P-02 grooves and the P1 pass [G2#19]
7. Mark the P-03 spar plug positions from the tube end, then cure for 24 h [G2#22]
8. Cut the P-04 torque-tube groove while the core is still whole [G2#26]
9. Pin and strip the P-06 edges with CF strips, with pins flush and holes square [G2#34]
10. Lay the P-07 tape strips with overlap, and lay the leading-edge strip last [G2#35]
11. Mark the P-07 tape pen lines [G2#36]
12. Check the P-09 CF tubes with calipers and a steel rule, and log them [G2#40]
13. Apply release film on the fin, with spare width beyond the fin face and both aft coves [D3#7]
14. Cut the cartridge segment to length before the pre-crush [D5#17]
15. Drill the motor mounts from a printed guide, never through the motor [G1#25]
16. Pin the edge strips and log each hole [G1#26]
17. Press the cartridge sticks to length on a drill press [G1#27]
18. In stage 4 assembly, fit the collars before the strips [G4#14]

## Checks and stop conditions
- Release film spare width must be at least 0 m [D3#7]
- Cut length must be within its limit before the pre-crush [D5#17]
- Practice stage 2: two practice cores accepted in a row before the real core [G4#8]
- Each build step has an id, a work package, a title, actions and a check; ids are unique [J5#14]
- Check types are limited to dimension, mass, fit, torque, continuity, voltage, function and visual; a visual check gives a warning [J5#15]

## Notes
- (K09-L value) Core chain start 10 Jan 2027; two people needed in town from 10 Jan; workspace named by 30 Nov; FIN-004 blocks printed by 9 Jan [I2#12]
- (K09-L value) XPS blank 1 200 x 330 x 50 mm [G2#2]
- (K09-L value) P-02 spar slot 22.4 mm, centred at x 80 mm, to z +17.8 mm, |y| <= 500 mm [G2#14]
- (K09-L value) P-02 block pockets x 28-97 mm, R 3.15 mm corners; 3 x 3 mm 45 deg lip chamfers [G2#15]
- (K09-L value) P-02 JR recess 18 x 10 x 5 mm; P1 pass 8 mm at 45 deg [G2#19]
- (K09-L value) P-03 dowel marks at 180 mm (block) and 258 mm (anchor) from the tube end [G2#22]
- (K09-L value) P-04 groove 5.4 mm; 30 deg lower bevel; 2.5 mm horn-blade slots; 5 x 4 tubes [G2#26]
- (K09-L value) P-06 CF strips 10 x 1 x 224 mm (x8) and 10 x 2 (x4); 2.5 mm pins; 48 holes logged [G2#34]
- (K09-L value) P-07 strips 48 mm with 10 % overlap; leading-edge strip 100 mm [G2#35]
- (K09-L value) P-07 forward strip ends at x 41.8 mm (lower) and 40.8 mm (upper); leading-edge strip edges at x 45.5 mm (upper) and 46.6 mm (lower) [G2#36]
- (K09-L value) P-09 CF tubes 22 x 20 x 344 mm (x2); spar 1 000 mm; plugs 20 x 18 x 53 mm (x2) [G2#40]
- (K09-L value) Fin test article uses a 300 mm wing stub [G2#45]
- (K09-L value) Fin release film recorded value 0.0142 m [D3#7]
- (K09-L value) Cartridge cut length limit 0.0508 m, recorded value 0.04 m, before the 1 mm pre-crush [D5#17]
- (K09-L value) Motor-mount drill 3.4 mm; slit feeler at 1.5 mm [G1#25]
- (K09-L value) Edge pins 2.5 mm; 48 holes logged [G1#26]
- (K09-L value) Cartridge stick pressed length 34.0 mm; stick 20.9 x 11.0 x 35.0 mm; 108 sticks [G1#27]
