---
id: dbf-combined-tools-davinci-probe2
title: DBF-Combined: tools/davinci_probe2.py (write probe on scratch branch, not run)
authors: DBF-Combined project (author not stated)
year: 2026
url: origin/redesign/v1:tools/davinci_probe2.py
type: website
retrieved: 2026-11-24
verified: true
---

## Summary
Write probe that uses a scratch branch. Grep hits show the route set; per davinci-findings section 8 it creates a branch, opens a session, adds one object, calls invokeTool, deletes the object and closes the session. Read with grep only; not run and not copied.

## Usable rules / numbers
- Base URL https://davinci-app.com/api/v2 (line 15).
- Route set as described in davinci-findings section 8: branch create (POST), session open, object add (POST), invokeTool, object delete, session close.
- Helpers load_key, call, usd, finish (grep lines 19-90).

## How we could use it
Reference for the write sequence only; W32-S made no write.
