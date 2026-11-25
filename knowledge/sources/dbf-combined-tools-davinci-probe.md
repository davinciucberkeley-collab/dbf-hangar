---
id: dbf-combined-tools-davinci-probe
title: DBF-Combined: tools/davinci_probe.py (read-only probe, not run)
authors: DBF-Combined project (author not stated)
year: 2026
url: origin/redesign/v1:tools/davinci_probe.py
type: website
retrieved: 2026-11-24
verified: true
---

## Summary
Read-only probe script. Its docstring and code path call GET usage, GET projects, GET project tree and GET usage again; it opens no session and writes nothing. Read with grep for routes and scopes only; not run and not copied.

## Usable rules / numbers
- Base URL https://davinci-app.com/api/v2 (line 12).
- Calls: GET usage, GET projects, GET projects/{id}/tree, GET usage (docstring lines 4-6).
- Scopes it needs: projects:read and usage:read (line 6).

## How we could use it
Confirms the read-only route pattern. W32-S used the same GET set with its own script, not this file.
