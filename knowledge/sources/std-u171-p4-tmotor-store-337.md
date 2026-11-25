---
id: std-u171-p4-tmotor-store-337
title: T-Motor store product page (id 337), test data export table
authors: T-Motor (maker store)
year: unknown
url: https://store.tmotor.com/goods.php?id=337
type: website
retrieved: 2026-11-25
verified: true
---

## Summary
Maker store page with a motor and propeller bench-test table. The efficiency it reports is thrust per electrical watt, in grams per watt, at throttle steps of 50 to 100 percent. It gives no dimensionless efficiency, no battery-to-thrust fraction and no advance ratio, and it names no propeller diameter test condition beyond the prop size in each row.

## Usable rules / numbers
- [propulsive_efficiency] Thrust per electrical watt (unit: g/W), not a fraction. Example row: KV360, 14.8 V, 14x4.8CF prop, 50 percent throttle: 15.77 g/W; 100 percent throttle: 10.31 g/W. Place: section "Test Data Export to Excel", KV360 table.
- [propulsive_efficiency] Other rows in the same table: KV360 at 22.2 V, 14x4.8CF prop: 11.89 g/W at 50 percent, 7.22 g/W at 100 percent. Place: same section.
- The page gives no nominal voltage per cell; the test voltages are 11.1, 14.8 and 22.2 V.

## How we could use it
- Feeds `propulsive_efficiency` only as a motor-plus-prop thrust-per-watt table; converting g/W to a battery-to-thrust fraction needs inputs this page does not give, so the packet keeps the key pending.
