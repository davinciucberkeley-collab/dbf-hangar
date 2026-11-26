# T168-id-rename: `plane design rename-id` (core)

class: hard
ledger: T168 (due 2026-12-08). Environment: `plans/2026-11-20-standardization/briefs/U16.1-env.md`, with SLUG = `t168-id-rename`, `<unit>` = `t168-id-rename`, branch `std/t168-id-rename`, worktree `C:/Users/trist/wt/t168-id-rename`. Core only: no file under `designs/` may change.

## Choice and why
Options: (a) new op `design rename-id`; (b) list-element replace in `design set`; (c) add-linkage rewrites assembly/transport/bom itself.
Chosen: (a). The stale ids sit in four kinds of place (assembly.sequence[].add, transport groups, bom items component_ids, and elsewhere: attachments, mechanisms, harness, cavities). (b) needs one call per element and an index/selector syntax for block lists that `pdledit` does not have (`replace_list` handles one-line `[list]`s only; these lists are block lists). (c) fixes only add-linkage, not a hand rename. (a) is one call, reuses the existing byte-preserving pattern (patch lines at ruamel line/col, re-parse, compare to expected data, allow only changed lines in the diff), and is idempotent.

Semantics (authoritative):
- A reference = any YAML mapping VALUE or list ITEM that is a string exactly equal to OLD. Mapping keys are never touched. Under these top-level keys nothing is touched: `id`, `name`, `description`, `notes`, `lineage`, `authors`, `status`.
- Substring matches (e.g. `meshes/OLD.stl`, `E-OLD-1`) are NOT renamed; they are listed in a warning message (`not renamed: <path>`), max 10 shown, so a human can decide.
- OLD == NEW, or NEW not matching `ID_RE` (`core/hangar/ids.py`) -> `OpInputError`.
- OLD with zero references: if NEW has at least one reference -> success, `changed: False`, message `OLD -> NEW: already renamed` (idempotent re-run, nothing written, no CHANGELOG entry); if NEW has none either -> `OpInputError` `unknown id 'OLD'` (with a `did you mean` hint via `pdledit._suggest` over all `components[].id`).
- Collision: OLD and NEW both are `id` values in `components` -> `OpInputError` `both 'OLD' and 'NEW' are components; cannot rename`. Also, if the rename would make any list contain NEW twice where it did not before -> `OpInputError` `would duplicate 'NEW' in <path>`. NEW being a component while OLD is not (stale ids, the U16.3-3 case) is allowed and is the main use.
- Renaming OLD that is itself a component id also renames that component's `id:` line (so it works as a true rename).

## Files and exact functions
1. `core/hangar/pdledit.py`: add after `remove_item`:
   `def rename_id(text: str, old: str, new: str) -> tuple[str, list[str], list[str]]` returning `(patched text, changed paths, not-renamed substring paths)`; paths are `design.set`-style keys like `assembly.sequence[28].add[0]` (numeric index form is fine). Implementation: LF-normalise as `_edit_list` does (restore CRLF at the end); `data = yamlfast.safe_load(t)`; walk `yamlio.load(t)` (ruamel tree) recursively, for each str value equal to OLD record `(line, col)` from `parent.lc.value(key)` (map) or `parent.lc.item(i)` (seq); at `(line, col)` match `_TOKEN` (or the existing plain-scalar regex used in `remove_element`) and require its unquoted text == OLD, else `OpInputError(f"rename-id: cannot edit {path} without rewriting other text; edit the file by hand")`; replace only the OLD characters (keep quotes), editing each line right to left. Then check: `yamlfast.safe_load(out) == expected` (expected = deep copy of data with the same values replaced), and with `difflib.SequenceMatcher` only `equal` or one-line `replace` opcodes whose line indexes are exactly the recorded lines. Failure of either -> same "edit the file by hand" error.
2. `core/hangar/ops/edit.py`: add after `add_op`:
   `@op(name="design.rename-id", summary="Rename a component id everywhere it is used as a value or list item in plane.yaml (components, attachments parent/child, mechanisms, harness from/to/route, cavities, assembly.sequence, transport groups, bom component_ids), byte-preserving, and log it in CHANGELOG.yaml. A stale id with no component (OLD absent) is re-pointed to an existing NEW. Errors on an unknown id, on a collision (both ids are components) or when a list would hold NEW twice; idempotent (already renamed -> unchanged). Substrings such as file names are reported, not renamed.", mutates=True, render=lambda r: "\n".join(r.messages))`
   `def rename_id_op(path: str, old: str, new: str, *, why: str) -> OpResult` : same flow as `add_op` (`_plane`, `_text`, empty-`why` error `why must not be empty`), calls `pdledit.rename_id`, then `pdledit.check_schema(before, after, "rename-id")` and the `expression_errors` diff check exactly as in `add_op`; log entry `{"date": stamp, "key": "rename-id", "old": old, "new": new, "why": why, "kind": "modify", "paths": changed}` through `_write_with_log`. Message: `OLD -> NEW: N reference(s) renamed` plus one `not renamed: PATH` line per substring hit. `data`: `{"old","new","changed": bool,"count": N,"paths": [...]}`. `changed_files=[str(plane), str(log)]`. No `regeneration_report` call (ids only; mesh file names untouched).
3. `docs/cli.md`: regenerate, never hand-edit: `$PY -m hangar.cli docs cli --out docs/cli.md`.
4. New test file `tests/test_rename_id.py` (only new test file; do not edit other tests unless one fails only because it counts ops or lists ops, then update that one number/list and say so).

No other file. Do not touch `designs/`, `standards/`, `plans/`, `ledger/`.

## Tests first (write, run, paste the failing summary, then code)
Fixture `tmp_path/ref`: copy `designs/example-tailsitter-wing` (`design_mod.DESIGNS_DIR / "example-tailsitter-wing"`) and append, by a plain text write in the fixture (not via ops), whatever is needed so one id `rn-old` is referenced in EVERY place the schema allows: a component `{id: rn-old, ...point_mass}` (id), `attachments` parent and child (two attachments), `mechanisms[].driver`/`driven`/`link` if the schema allows ids there, `wiring.harnesses` from/to/route, a `cavities`/bay host or component ref if the schema has one, `assembly.sequence[].add` (block list), `transport.disassembly` group list, `bom.items[].component_ids` (block list), plus a quoted occurrence (`"rn-old"`) in a flow list. Read `schemas/plane.schema.json` and `designs/concept-a-test-refactor/plane.yaml` (lines 2430-2460, 2830-2850, 3020-3050) for exact shapes; if a place is not in the schema, leave it out and list it in the report. Add substring traps: a mesh path `meshes/rn-old.stl` and a key-like text in `notes`. Tests (names exact):
- `tests/test_rename_id.py::test_rename_every_reference` : call `call("design.rename-id", path=..., old="rn-old", new="rn-new", why="t")`; parsed data equals the original with every exact `rn-old` value replaced (deep compare) and zero `rn-old` exact values remain; the `notes` text and mesh path are unchanged; the message list contains `not renamed:` for the mesh path.
- `::test_only_reference_lines_change` : `difflib` over `splitlines()` before/after: every opcode is `equal` or a one-line `replace`; the number of replaced lines equals `r.data["count"]` minus occurrences sharing a line.
- `::test_quotes_and_crlf_preserved` : the quoted `"rn-old"` becomes `"rn-new"`; a CRLF copy of the fixture stays CRLF (`b"\r\n" in bytes`, no lone LF added).
- `::test_idempotent` : second identical call: `ok`, `data["changed"] is False`, plane.yaml bytes and CHANGELOG.yaml bytes identical to after the first call.
- `::test_unknown_id_error` : OLD `nope-zz` (no reference anywhere, NEW also absent) -> `OpInputError` containing `unknown id`; nothing written (bytes identical).
- `::test_collision_error` : OLD and NEW both components -> `OpInputError` containing `both`; nothing written.
- `::test_duplicate_in_list_error` : OLD and NEW both in one `component_ids` list but NEW not a component pair collision (make NEW a component, OLD a stale id in a bom list that already holds NEW) -> `OpInputError` containing `would duplicate`.
- `::test_stale_id_repoint` : OLD only in lists (no component), NEW a component (the T168 case) -> renamed in the lists, count correct.
- `::test_bad_new_id_and_empty_why` : NEW `Bad Id!` -> error; `why=" "` -> `why must not be empty`.
- `::test_changelog_entry` : one new entry with key `rename-id`, `old`, `new`, `why`, `paths`.
- `::test_validate_unchanged_except_ids` : `design.validate` tier 0 PASS after the rename on the fixture.
Existing: `tests/test_cli_doc.py::test_cli_doc_is_current` must pass after regenerating docs/cli.md (it fails first: that is expected, paste it).

## Pass check
Local, in the worktree (Python env per U16.1-env.md):
1. `$PY -m pytest tests/test_rename_id.py tests/test_cli_doc.py tests/test_design_add.py tests/test_design_edit.py tests/test_list_values.py tests/test_add_linkage.py -q` : all pass (paste the summary line).
2. `$PY -m hangar.cli design rename-id --help` shows `OLD`, `NEW`, `--why`.
3. Export-hash check per U16.1-env.md (hashset.sh, SLUG = t168-id-rename; DIRS = every folder under `designs/`, in groups of at most 3, plus `tests/fixtures/c172-rc-frozen`): `diff .logs/hash-base.txt .logs/hash-after.txt` must print nothing (expected: empty; this brief changes no design and no export logic). Paste "empty".
4. `git ls-files --eol | grep -c "i/crlf"` prints `0`; `git status` shows only: `core/hangar/pdledit.py`, `core/hangar/ops/edit.py`, `docs/cli.md`, `tests/test_rename_id.py` (plus at most one updated count/list test, named in the report).
5. CI green on headSha (U16.1-env.md commands).

## Stop rule
Stop and report (do not adjust a test, do not widen scope) if: a place in the fixture cannot be renamed without rewriting other lines (report the key); `pdledit.rename_id` needs to re-emit a document or touch `design.py`/`yamlio.py`; more than the four listed files need change; the export-hash diff is not empty; or any existing test fails for a reason other than an op count/list. Also stop if you find yourself implementing substring rename, a `--dry-run` flag, or claims.yaml editing: those are out of scope.
