---
id: procurement-lead-times
title: Procurement Lead Times
topic: procurement-lead-times
source_repo: DBF-Combined @ a93f14d
source_rows: [I1#25, I1#36, I1#42, I1#43]
created: 2026-11-21
verified: false
---

## Purpose
Ordering parts in time for the build: listing checks, the gated line, and the lead-time assumptions. Run before each order.

## Steps
1. Re-read the supplier listings before each order, logging price and stock [I1#36]
2. Order the gated line before the first drive to the field, and collect it at store pick-up [I1#25]
3. Plan the early order against its lead-time assumptions [I1#42]
4. Buy the US-stock carbon tube early, and keep the overseas fallback in view [I1#43]

## Checks and stop conditions
- none

## Notes
- (K09-L value) Re-read six listings on 20 Nov and 15 Dec [I1#36]
- (K09-L value) Gated line X07 (D7 box and field kit, $71.00) [I1#25]
- (K09-L value) Lead times: 5 d carts; packs about 14 d from Germany (EST); servos 7 d (EST); carbon tube 2-4 weeks [I1#42]
- (K09-L value) Overseas carbon tube fallback about 14 d [I1#43]
- The source gives 7 d for packs in the schedule script, which differs from the 14 d here; not reconciled [I1#42]
