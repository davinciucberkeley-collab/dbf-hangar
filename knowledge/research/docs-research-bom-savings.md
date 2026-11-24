---
id: "docs-research-bom-savings"
title: "BOM savings and shipping check (2026-11-01)"
kind: "research"
morph_cells: []
source_repo: DBF-Combined @ a93f14d
source_files: ["docs/research/bom-savings.md"]
created: 2026-11-23
verified: false
---

## Summary
A 2026-11-01 price and shipping check of the C0 bill of materials against a $2,000 budget. It adopts one part swap, finds the shipping allowance far too low, and then shows that moving seven avionics and servo lines to one vendor restores most of the reserve. No morphological cell applies because the file is about purchasing, not configuration.

## Key facts
- The ESC swap (a 45 A 4-pack at $60.00 instead of $79.98, times two) saves $19.98 in goods and also avoids a one-left stock problem. [bom-savings.md verdict and line items]
- The $110 shipping allowance was too low: cart quotes plus estimates came to $186.94, mostly from two China-shipped vendors ($37.47 and $30.00). [bom-savings.md shipping table]
- With the swap only, the reserve falls from $80.58 to $23.76 (goods $1,622.95, tax 10.25 percent, shipping $186.94). [bom-savings.md budget table]
- Consolidating seven avionics and servo lines into one retailer order raises goods by $22.39 but removes about $93 of shipping, giving a new allowance of $91.99 and a reserve of $94.02 (total $1,905.98). [bom-savings.md consolidation section]
- Hot-wire cutter estimate: 24 AWG nichrome is about 5.46 ohm per metre, so a 1.4 m wire is 7.6 ohm and at 2 A needs 15.3 V and 31 W. [bom-savings.md hot-wire sizing]
- Moving to the consolidated airspeed sensor means setting the airspeed type parameter to 1 and drops the address-strap step. [bom-savings.md flight controller and airspeed notes]
- Sources cited by DBF-Combined, not opened by this import: Amazon listings, the ReadyMadeRC shipping policy page, Wikipedia (nichrome), an ArduPilot board page, atoship.com shipping rates. [bom-savings.md]

## Status in the study
none

## Open questions
- The metal tube shipping cost ($50) is an estimate with no cart quote.
- The free-shipping rule at the consolidated vendor was not verified on a cart.
- The consolidated order is held until backordered parts (flight controller, one receiver) arrive.
- Only two units of one Remote ID module were left in stock.
