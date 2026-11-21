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
| `standards/connection-types.yaml` | DBF-Combined @ a93f14d : redesign/interfaces/connection_types.json | 44 types, ids kept; JSON to YAML; `rating_basis: placeholder` and `source: pending` added to every type (the source gives neither); the file's `note` text not carried |
| `schema/plane.schema.json` (attachment `connection`, `seat`) | DBF-Combined @ a93f14d : redesign/interfaces/SCHEMA.md (edge `via`), redesign/interfaces/seats.json (seat idea) | two optional attachment fields; `connection` is the edge `via`; `seat` is a free-text field, no `seats.json` data carried |
| `core/hangar/gates/interfaces.py` | DBF-Combined @ a93f14d : redesign/interfaces/merge_check.py (connection-type lookup) | rebuilt as one library check on PDL attachments; ownership, dangling, joint_stack, wire, power-path and floating checks (D-46) not ported |
| `core/hangar/importers/dbf.py` (`read_interface_edges`, `account_interface_edges`, `connection:`) | DBF-Combined @ a93f14d : redesign/qp/A/cad/model/*/interfaces.json | edges read and accounted for in `import-report.json`; each emitted attachment names its `via` as `connection` |
| `core/hangar/ops/standards.py`, `tests/test_interfaces.py` | dbf-hangar (new) | no source file; op `standards.connections` and tests are written for hangar (plan U1.6) |
| schema/claims.schema.json | DBF-Combined @ a93f14d : redesign/proofs/SCHEMA.md | node and field tables rebuilt as JSON Schema `claims/1`; `part` node type dropped; calculation `script` path replaced by a registered `function` name (`imported_from.script` kept as provenance); evidence statuses not carried; source `kind` widened with `file`, `repo`, `code` (used by concept-A) |
| core/hangar/claims/calc.py | DBF-Combined @ a93f14d : redesign/proofs/proofkit.py (`margin`, `margin_text`, `close`) | rebuilt; margin rules unchanged (limit 0 gives a signed distance, CDR-03); `bool` excluded from numbers; calculation lookup by name instead of `load_function(script)` |
| core/hangar/claims/graph.py | DBF-Combined @ a93f14d : redesign/proofs/build_graph.py (`Build`, `self_check`), redesign/proofs/proofkit.py (`flatten_params`) | rebuilt on PDL: parameters read `design.data` through `P:` paths instead of `params.json`; drift is status STALE, an un-recomputable claim is PROPOSED; no `graph.json`, `CHAIN.md` or viewer output |
| tests/test_claims.py | DBF-Combined @ a93f14d : redesign/proofs/test_proofs.py (`ZERO` table, `test_margin_function_zero_limit`) | cases re-expressed as pytest on the hangar API |
| core/hangar/ops/claims.py, core/hangar/gates/claims.py, core/hangar/calcs/__init__.py | dbf-hangar (new) | no source file; ops and gate T9 are written for hangar (plan U1.5) |
