# Provenance

Snapshot import, no history. Full history: aircraft-platform @ f462468 (plans/ and reviews/ there are the record of how it was built).

| hangar path | source repo @ commit : path | edits |
|---|---|---|
| core/ | aircraft-platform @ f462468 : core/ | package dir renamed `aircraft_platform` to `hangar` (see rename row) |
| schema/ | aircraft-platform @ f462468 : schema/ | none |
| standards/ | aircraft-platform @ f462468 : standards/ | none |
| tests/ | aircraft-platform @ f462468 : tests/ | `aircraft_platform` to `hangar` imports; `test_seed.py` added by dbf-hangar |
| designs/ | aircraft-platform @ f462468 : designs/ | none (data); 104 `.stl` meshes stored via Git LFS (D8) |
| knowledge/ | aircraft-platform @ f462468 : knowledge/ | none |
| skills/ | aircraft-platform @ f462468 : skills/ | none |
| viewer/ | aircraft-platform @ f462468 : viewer/ | none |
| docs/ | aircraft-platform @ f462468 : docs/ | `aircraft_platform` to `hangar` in `docs/mcp.md`; MCP server name `aircraft-platform` to `dbf-hangar` in `docs/mcp.md` (the `claude mcp add` line and the JSON key), matching `FastMCP("dbf-hangar")` (D-d) |
| .github/ | aircraft-platform @ f462468 : .github/ | `aircraft_platform` to `hangar` in workflows (none found) |
| pyproject.toml | aircraft-platform @ f462468 : pyproject.toml | name `dbf-hangar`, version `1.0.0.dev0`, packages `["hangar"]`, entry points to `hangar.*`, `[tool.pytest.ini_options]` removed (hangar's `pytest.ini` is the only pytest config) |
| core/hangar/ (rename) | aircraft-platform @ f462468 : core/aircraft_platform/ | directory renamed to `hangar`; `aircraft_platform` to `hangar` in all `*.py` except `opencae_runner.py` (next row); `__version__ = "1.0.0.dev0"` in `core/hangar/__init__.py` |
| core/hangar/opencae_runner.py | aircraft-platform @ f462468 : core/aircraft_platform/opencae_runner.py | kept byte-identical (docstring still says `aircraft_platform`); `fea.part_hash` hashes the runner's bytes and FEA result hashes include it, so editing it marks all 28 concept-a results stale; docstring fix waits for the next FEA re-run. `designs/**/fea/*.json` not edited |
| core/hangar/mcp_server.py, core/hangar/importers/dbf.py (names) | aircraft-platform @ f462468 : core/aircraft_platform/mcp_server.py, core/aircraft_platform/importers/dbf.py | MCP server name `dbf-hangar`; generated-file header and authors text say `dbf-hangar` |
| tests/testutil.py (helper move) | aircraft-platform @ f462468 : tests/conftest.py (`EXAMPLE_PATH`, `statuses`) | moved to new `testutil.py`; `tests/conftest.py` re-imports them; every `from conftest import` in `tests/` now imports from `testutil` (AP's and hangar's conftest modules both named `conftest` clashed) |
| tests/harness/hookutil.py (helper move) | dbf-hangar (own harness, H1): tests/harness/conftest.py | `REPO` and `run_hook` moved from `tests/harness/conftest.py` to new `hookutil.py` to avoid the two `conftest` modules clashing; `test_ledger_hooks.py` imports from `hookutil` |
