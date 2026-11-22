# U4.1 Step 3 subtraction pass (auditor W4-AuS, main c447e50, read-only)

## Files
- No code file is unreferenced: modules without an absolute import are loaded via `adapters/__init__.py:7-9 _MODULES`, `gates/__init__.py:93`, `importers/dbf.py:121` (subprocess `_dbf_dump.py`), `dbf.py:28` (`dbf_geometry`), and the ops pkgutil registry. Keep all.
- `tests/test_round3.py`: collected by pytest (testpaths=tests). Keep.
- `viewer/docs/screenshot.png`: embedded by no doc. Link it from `viewer/README.md` or delete.

## Ops
- 45 ops; every op name appears in tests/, skills/ or docs/. Nothing to delete.

## Docs
- All docs are linked from README.md or `docs/pdl/README.md`.
- Stale: `designs/concept-a/README.md:3` cites `core/aircraft_platform/importers/` (now `core/hangar/importers`). Designs-only fix.
- All 46 `plane …` command forms in docs exist in the CLI.

## Ledger
- T53 likely obsolete (no `'mesh'` lookup left in importers; `dbf_geometry.py:277` uses `shape["kind"]`): re-run `plane import dbf` for concept A, then close.
- T23 partly obsolete (subprocess used, no sys import, job.json written once): verify and close.
- T17 partly done (bom.py:28/31 guarded; qty at :99 unguarded): keep, update note.
- Still valid: T9, T11, T19, T20, T26, T52, T61.

## Housekeeping
- Merged worktrees removed by the conductor (11). Untracked `.logs/` in the main tree: add to `.gitignore`.

### Verdict: ACCEPT
