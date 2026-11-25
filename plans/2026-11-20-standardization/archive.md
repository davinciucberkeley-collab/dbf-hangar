# Archive: finished units of plans/2026-11-20-standardization.md

Moved verbatim from section 7 of the plan (every checkbox ticked). `plane progress` reads this file together with the plan. Do not edit.

## 7. Archived units

### Unit U0.4: Seed hangar from aircraft-platform (runs first)

**Files:**
- Import: aircraft-platform @ `f462468` (`core/`, `schema/`, `standards/`, `tests/`, `designs/`, `knowledge/`, `skills/`, `viewer/`, `docs/`, `.github/`, `pyproject.toml`) with `git archive`, no history rewrite
- Rename: package `core/aircraft_platform/` → `core/hangar/`; project name `dbf-hangar`; entry points `plane`, `plane-mcp` unchanged
- Create: `PROVENANCE.md` (source repo, commit, path → hangar path, edits made), `.gitattributes` (LFS patterns per D8), `README.md` (≤ 40 lines, pointers)
- Test: existing suite + `tests/test_seed.py`

- [x] **Step 1: Failing test**

```python
def test_package_is_hangar_and_cli_still_plane():
    import hangar; assert hangar.__version__.startswith("1.0.0.dev")
    assert shutil.which("plane")

def test_provenance_lists_every_imported_top_level_path(repo_root):
    prov = (repo_root/"PROVENANCE.md").read_text()
    for p in ["core/", "schema/", "standards/", "designs/", "knowledge/", "skills/", "viewer/"]:
        assert p in prov
```

- [x] **Step 2: Run** → FAIL (repo empty apart from plan and agents)
- [x] **Step 3: Import + rename** (`git -C ../aircraft-platform archive f462468 | tar -x`, then `sed` the imports; CI badge and Pages URL point at dbf-hangar)
- [x] **Step 4: Run** `pip install -e ".[mcp,dev]" && pytest -q` → same pass count as aircraft-platform at `f462468`; `plane baseline check --all` → no new failures
- [x] **Step 5: Commit** `git commit -m "seed: aircraft-platform f462468 as package hangar; provenance; LFS"`

### Unit U0.1: Agent roster and pointer files

**Files:**
- Create: `.claude/agents/{conductor,advisor,tactician,builder,builder-plus,scout,recon,design-engineer,reviewer,auditor}.md`, `core/hangar/roster.py`
- Modify: `standards/agents.md` → v0.2 (reviewer fresh per wave; work-class bump table; points to `.claude/agents/`)
- Modify: `CLAUDE.md` → pointer list only (≤ 25 lines)
- Test: `tests/test_roster.py`

**Interfaces:**
- Produces: `hangar.roster.load_roster(root: Path) -> dict[str, AgentSpec]`, `AgentSpec(name: str, model: Literal["opus","sonnet","haiku"], tools: tuple[str, ...], description: str)` (frozen dataclass) in `core/hangar/roster.py`

- [x] **Step 1: Write the failing tests**

```python
from pathlib import Path
import pytest
from hangar.roster import load_roster

REPO = Path(__file__).resolve().parents[1]
ROLES = {"conductor","advisor","tactician","builder","builder-plus","scout","recon","design-engineer","reviewer","auditor"}

def test_roster_has_exactly_the_ten_roles():
    assert set(load_roster(REPO)) == ROLES

def test_models_by_level():
    r = load_roster(REPO)
    assert {n for n, a in r.items() if a.model == "opus"} == {"conductor", "advisor", "reviewer"}
    assert {n for n, a in r.items() if a.model == "haiku"} == {"builder", "scout", "auditor"}

def test_every_agent_has_stop_rules_and_never():
    for name in ROLES:
        text = (REPO / ".claude/agents" / f"{name}.md").read_text(encoding="utf-8")
        assert "## Stop rules" in text and "## Never" in text

def test_design_engineer_cannot_edit_or_write():
    tools = load_roster(REPO)["design-engineer"].tools
    assert "Edit" not in tools and "Write" not in tools

def test_conductor_can_launch_and_reuse_agents():
    tools = load_roster(REPO)["conductor"].tools
    assert "Agent" in tools and "SendMessage" in tools

def test_bad_model_rejected(tmp_path):
    (tmp_path / ".claude/agents").mkdir(parents=True)
    (tmp_path / ".claude/agents/x.md").write_text("---\nname: x\nmodel: gpt\ntools: Read\ndescription: d\n---\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_roster(tmp_path)

def test_agents_md_v02_names_every_role_and_hook():
    text = (REPO / "standards/agents.md").read_text(encoding="utf-8")
    assert text.startswith("# Agent Standard v0.2")
    assert all(f"`{r}`" in text for r in ROLES)
    assert all(h in text for h in ["log_prompt", "agent_gate", "reinject", "stop_gate", "Pass criterion"])

def test_claude_md_is_a_pointer_file():
    assert len((REPO / "CLAUDE.md").read_text(encoding="utf-8").splitlines()) <= 25
```

- [x] **Step 2: Run** `pytest tests/test_roster.py -v` → FAIL (`load_roster` missing)
- [x] **Step 3: Implement `load_roster`** (parse YAML frontmatter between the first two `---` lines; `tools` is the comma list). Update `standards/agents.md` and `CLAUDE.md`.
- [x] **Step 4: Run** `pytest tests/test_roster.py -v` → PASS
- [x] **Step 5: Commit** `git commit -m "harness: roster loader, agent standard v0.2"`

### Unit U0.2: Hooks, output style, installer (delivered early as H1 + H2, §6c; this unit then only ports the hooks onto `plane ledger` once U0.3 lands)

Delivered 2026-11-20: H1 + H2 merged after 3 review rounds (`reviews/2026-11-20-w0-harness.md`). Follow-ups this unit picks up (non-blocking from that review):
- [x] printed `ledger.py` instructions use `sys.executable`, not `python`
- [x] `reinject` also lists `deferred` prompts after compaction
- [x] installer removes older `python …/x.py` hook entries when upgrading to `run.sh`
- [x] installer writes `run.sh` with LF endings and a test fails if any `*.sh` contains `\r`

**Files:**
- Create: `harness/hooks/{log_prompt,agent_gate,reinject,stop_gate}.py`, `.claude/settings.json`, `.claude/output-styles/quiet.md`, `harness/install.py`
- Test: `tests/test_hooks.py`

**Interfaces:**
- Consumes: `load_roster` (U0.1); `Ledger` (U0.3) — U0.2 and U0.3 run in parallel; until U0.3 merges, hooks import `ledger` lazily and tests use the U0.3 fixture file format below.
- Produces: hook scripts read Claude Code hook JSON on stdin; exit 0 = allow, exit 2 = block with stderr message.

- [x] **Step 1: Write the failing tests** (run each script with `subprocess.run([sys.executable, script], input=json.dumps(event))`)

```python
def test_agent_gate_blocks_unknown_role():
    r = run_hook("agent_gate", {"tool_name": "Task", "tool_input": {"subagent_type": "general-purpose", "prompt": "x"}})
    assert r.returncode == 2 and "builder" in r.stderr

def test_agent_gate_allows_roster_role_listed_in_active_plan(active_plan_with_builder):
    r = run_hook("agent_gate", {"tool_name": "Task", "tool_input": {"subagent_type": "builder", "prompt": "x"}})
    assert r.returncode == 0

def test_prompt_is_logged_open(tmp_ledger):
    run_hook("log_prompt", {"prompt": "add a BOM gate", "session_id": "s1"})
    assert tmp_ledger.prompts("s1")[-1].status == "open"

def test_stop_blocked_while_prompt_open_and_allowed_with_override(tmp_ledger, monkeypatch):
    tmp_ledger.add_prompt("s1", "x")
    assert run_hook("stop_gate", {"session_id": "s1"}).returncode == 2
    monkeypatch.setenv("ALLOW_STOP", "1")
    assert run_hook("stop_gate", {"session_id": "s1"}).returncode == 0

def test_reinject_prints_open_items_after_compaction(tmp_ledger):
    tmp_ledger.add_prompt("s1", "keep FEA envelope")
    assert "keep FEA envelope" in run_hook("reinject", {"source": "compact", "session_id": "s1"}).stdout

def test_install_is_idempotent(tmp_path):
    install(tmp_path); install(tmp_path)
    assert len(list((tmp_path/"agents").glob("*.md"))) == 10
```

- [x] **Step 2: Run** `pytest tests/test_hooks.py -v` → FAIL
- [x] **Step 3: Implement the four hooks, `install(target: Path) -> list[Path]`, settings.json wiring** (`PreToolUse` matcher `"Task|Agent"`; `SessionStart` matcher `"compact|resume"`). "Active plan" = newest `plans/*.md` whose agent table lists the role.
- [x] **Step 4: Run** `pytest tests/test_hooks.py -v` → PASS; then one live check: start Claude Code in the repo, ask it to launch a `general-purpose` agent, confirm it is blocked with the roster message. — *Live check passed (Tristan, 2026-11-21): a `general-purpose` launch was refused with the roster message.*
- [x] **Step 5: Commit** `git commit -m "harness: prompt ledger, agent gate, stop gate, compaction re-inject, quiet style, installer"`

### Unit U0.3: Ledger (meeting → tasks → evidence) — builds on `harness/ledger.py` from H1: same `ledger/prompts.jsonl` format, `plane ledger` wraps it

**Files:**
- Create: `core/hangar/ledger.py`, `ledger/items.yaml`, `ledger/prompts.jsonl` (gitignored), `schema/ledger.schema.json`
- Test: `tests/test_ledger.py`

**Interfaces:**
- Produces: `Ledger(path: Path)` over `ledger/items.yaml`, `.add(kind: Literal["ruling","task","idea","decision"], text: str, source: str, owner: str = "", item_id: str | None = None, due: str = "") -> str` (returns `R12`/`T3`/`D4`/`I2`), `.set(item_id: str, status: Literal["open","done","dropped","superseded","decided"], evidence: str = "", decided_in: str = "") -> None`, `.get(item_id) -> Item`, `.check(repo: Path) -> list[Issue]`, `.report_overdue(today: str) -> list[str]`, `.report() -> str`, `.seed_from_plan(plan: Path) -> int`. Prompts stay in `harness/ledger.py` (stdlib, used by hooks); `report()` reads `ledger/prompts.jsonl` (same format) only to count open prompts. Brief: `briefs/U0.3-ledger.md` (its tests supersede the sketch below).

- [x] **Step 1: Write the failing tests**

```python
def test_dropped_needs_decision_and_is_not_overdue(tmp_ledger):
    t = tmp_ledger.add("task", "OpenCAE GUI port", source="2026-11-11#61:02")
    with pytest.raises(ValueError, match="decided_in"):
        tmp_ledger.set(t, "dropped")
    tmp_ledger.set(t, "dropped", decided_in="2026-11-18#26:16")
    assert t not in tmp_ledger.report_overdue()

def test_done_needs_evidence_that_exists(tmp_ledger, repo_root):
    t = tmp_ledger.add("task", "x", source="s")
    tmp_ledger.set(t, "done", evidence="designs/does-not-exist/plane.yaml")
    assert [i.kind for i in tmp_ledger.check(repo_root)] == ["missing-evidence"]

def test_seeded_with_requirements_R1_to_R40(repo_root):
    ids = {i.id for i in Ledger(repo_root/"ledger/items.yaml").items if i.kind == "ruling"}
    assert {f"R{n}" for n in range(1, 41)} <= ids
```

- [x] **Step 2: Run** → FAIL
- [x] **Step 3: Implement**; seed `ledger/items.yaml` from §1 (scout transcribes the table; each R-id keeps its transcript timestamp as `source`). Add `ledger ingest` input format: a scout produces `ledger/inbox/<date>.yaml` from a transcript; `ingest` validates against `schema/ledger.schema.json` and appends. — *Status 2026-11-21: seed done (R1–R40, D1–D10); `ledger ingest` was not in the U0.3 brief; moved to U2.4 (Tristan, 2026-11-21).*
- [x] **Step 4: Run** → PASS
- [x] **Step 5: Commit** `git commit -m "ledger: tracked rulings/tasks/decisions with evidence; seeded R1-R40"`

### Unit U1.1: Operations registry and the OpResult contract [hard]

**Files:**
- Create: `core/hangar/ops/__init__.py` (registry), `ops/design.py`, `ops/meta.py`, `schema/op-result.schema.json`
- Modify: `core/hangar/cli.py` (generated groups; old commands become aliases)
- Test: `tests/test_ops_contract.py`

**Interfaces:**
- Produces:
  - `@op(name: str, summary: str, mutates: bool = False, adapters: tuple[str, ...] = ())` decorator; params from the function's type hints (str, int, float, bool, Path, Literal, list[str]).
  - `OpResult(ok: bool, data: dict, messages: list[str] = [], changed_files: list[str] = [], skipped: list[str] = [])`, `.to_json() -> str`, `schema_version = "1.0"`.
  - `registry() -> dict[str, OpSpec]`; `call(name: str, **params) -> OpResult`.
  - CLI: `plane <group> <verb>` from `name="<group>.<verb>"`; `--json` prints `OpResult`; exit 0/1/2 per Global Constraints.
  - Ops moved in this unit: `design.list, design.get, design.validate, design.mass, design.export, design.new, ops.list`.

- [x] **Step 1: Write the failing tests**

```python
def test_every_op_result_matches_schema():
    for name in ["design.list", "ops.list"]:
        jsonschema.validate(json.loads(call(name).to_json()), OP_RESULT_SCHEMA)

def test_cli_exposes_every_registered_op(cli_runner):
    out = json.loads(cli_runner.invoke(cli, ["ops", "list", "--json"]).output)["data"]["ops"]
    assert {o["name"] for o in out} == set(registry())

def test_old_validate_alias_matches_new(cli_runner):
    a = cli_runner.invoke(cli, ["validate", "designs/example-tailsitter-wing", "--format", "json"])
    b = cli_runner.invoke(cli, ["design", "validate", "designs/example-tailsitter-wing", "--json"])
    assert json.loads(a.output)["accepted"] == json.loads(b.output)["data"]["accepted"]

def test_unknown_component_type_gives_skip_not_crash(tmp_design_with_type_wingletz):
    r = call("design.validate", path=str(tmp_design_with_type_wingletz))
    assert not r.ok and any("wingletz" in m for m in r.messages)
```

- [x] **Step 2: Run** `pytest tests/test_ops_contract.py -v` → FAIL
- [x] **Step 3: Implement the registry and click generation** (click `Group` per prefix, `Command` per op; `Literal` → `click.Choice`). `design.validate` wraps `checks.validate` unchanged.
- [x] **Step 4: Run** full `pytest -q` → PASS (existing CLI tests must still pass through aliases)
- [x] **Step 5: Commit** `git commit -m "ops: one registry and OpResult contract; CLI generated from it"`

### Unit U1.2: MCP and Studio generated from the registry (subtraction)

**Files:**
- Modify: `core/hangar/mcp_server.py` (replace hand-written tools with a loop over `registry()`), `core/hangar/studio.py` (one `POST /api/op/<name>` route; delete `/api/patch`, `/api/check`, `/api/new`, … after `viewer/studio.js` calls the new route)
- Test: `tests/test_surfaces_in_sync.py`

**Interfaces:**
- Consumes: `registry()`, `call()` (U1.1)
- Produces: MCP tool name = op name with `.` → `_` (`design_validate`); Studio `POST /api/op/design.validate {"path": ...}` → `OpResult` JSON.

- [x] **Step 1: Failing tests**: `test_mcp_tools_equal_registry()` (tool names == `{n.replace('.', '_') for n in registry()}`); `test_studio_op_route_returns_op_result()`; `test_no_handwritten_api_routes_left()` (grep `studio.py` for `/api/` strings other than `/api/op/`, `/api/state`, `/api/ping`, file downloads).
- [x] **Step 2: Run** → FAIL
- [x] **Step 3: Implement**; net line count of `mcp_server.py` + `studio.py` must go down (record in PR).
- [x] **Step 4: Run** `pytest -q` → PASS; manual: `plane studio`, edit a mass, scorecard refreshes.
- [x] **Step 5: Commit** `git commit -m "mcp, studio: generated from ops registry; remove duplicate handlers"`

### Unit U1.3: PDL v1.0 schema, reference doc, migration [hard]

**Files:**
- Modify: `schema/plane.schema.json` (title "Plane Design Language v1.0"; add `"1.0"` to `schema_version`; blocks from §2.3; `requirements.transport_box_mm`)
- Create: `core/hangar/migrate.py`, `ops/schema.py` (`schema.docs`, `design.migrate`), `docs/pdl/reference.md` (generated), `docs/pdl/README.md` (one page: how a plane is described, with concept-a excerpts)
- Test: `tests/test_pdl.py`

**Interfaces:**
- Produces: `migrate(data: dict) -> tuple[dict, list[str]]` (new data, notes); ops `design.migrate(path, write: bool = False)`, `schema.docs(out: Path)`.

- [x] **Step 1: Failing tests**

```python
@pytest.mark.parametrize("d", list_designs())
def test_every_committed_design_migrates_to_1_0_with_same_verdict(d):
    before = validate(load_design(d)).accepted
    data, _ = migrate(load_design(d).data)
    assert data["schema_version"] == "1.0"
    assert validate(Design(data, d)).accepted == before

def test_v1_blocks_validate(pdl_v1_example):   # tests/fixtures/pdl-v1-full.yaml uses every new block
    assert tier0_schema(load_design(pdl_v1_example)).status == "PASS"

def test_reference_doc_is_current(tmp_path):
    call("schema.docs", out=tmp_path/"ref.md")
    assert (tmp_path/"ref.md").read_text() == (REPO_ROOT/"docs/pdl/reference.md").read_text()
```

- [x] **Step 2: Run** → FAIL
- [x] **Step 3: Implement** schema additions, `migrate`, generator; migrate all committed designs (`plane design migrate designs/* --write`) in this PR — the only PR allowed to touch both `designs/**` and `core/**` (label `migration`, see U1.4). — *Designs not migrated in U1.3 (D12): six designs move to 1.0 in W1-M; concept-a stays at 0.4 until its FEA is re-run.*
- [x] **Step 4: Run** `pytest -q` → PASS; `plane baseline check --all` → no new failures
- [x] **Step 5: Commit** `git commit -m "pdl: v1.0 schema (files, bom, wiring, mechanisms, transport, assembly, provenance) + migrate + reference"`

### Unit U1.4: Edit, sweep, diff, propose — iterate without code (R4, R5, R8, R15, R25)

**Files:**
- Create: `ops/edit.py`, `harness/ci/check_separation.py`, `.github/workflows/validate.yml` (add separation step + Windows job)
- Test: `tests/test_design_edit.py`, `tests/test_paths.py`, `tests/test_separation.py`

**Interfaces:**
- Consumes: `yamlio.load/dump`, `migrate`, `call`
- Produces:
  - `design.set(path: str, key: str, value: str, why: str, kind: Literal["add","subtract","modify"] = "modify") -> OpResult` — `key` is dotted with list selectors by id: `components[wing_l].mass_g`; `value` parsed as YAML scalar; schema-checked before write; appends to `CHANGELOG.yaml`.
  - `design.get(path, key)`, `design.diff(a, b) -> data.changes: list[{key, a, b}]`, `design.copy(src, new_id)`.
  - `design.sweep(path, key, values: list[str]) -> data.rows: list[{value, accepted, mass_g, static_margin, stall_speed_mps, hover_tw, failures}]` (copies to `.sweeps/<id>/<n>/`, never touches the source).
  - `design.propose(path, title) -> data.pr_url` (branch `design/<id>/<slug>`, commit, push, open PR via `gh api`).
  - `check_separation(base: str) -> list[str]` (violations).

- [x] **Step 1: Failing tests**

```python
def test_set_changes_one_value_keeps_comments_and_logs(tmp_concept_a):
    call("design.set", path=tmp_concept_a, key="components[wng-004-l].mass_g", value="41.5", why="measured", kind="modify")
    assert "# " in (tmp_concept_a/"plane.yaml").read_text()           # comments kept
    assert yaml.safe_load((tmp_concept_a/"CHANGELOG.yaml").read_text())[-1]["kind"] == "modify"

def test_set_rejects_bad_path_and_type_without_writing(tmp_concept_a):
    before = (tmp_concept_a/"plane.yaml").read_bytes()
    assert call("design.set", path=tmp_concept_a, key="components[nope].mass_g", value="1", why="x").ok is False
    assert call("design.set", path=tmp_concept_a, key="components[wng-004-l].mass_g", value="heavy", why="x").ok is False
    assert (tmp_concept_a/"plane.yaml").read_bytes() == before

def test_sweep_never_touches_source(tmp_example):
    before = (tmp_example/"plane.yaml").read_bytes()
    rows = call("design.sweep", path=tmp_example, key="components[battery].position_mm[0]", values=["100","140"]).data["rows"]
    assert len(rows) == 2 and (tmp_example/"plane.yaml").read_bytes() == before

def test_backslash_and_crlf_roundtrip(tmp_example):
    crlf = tmp_example/"plane.yaml"; crlf.write_bytes(crlf.read_bytes().replace(b"\n", b"\r\n"))
    assert call("design.validate", path=str(tmp_example).replace("/", "\\")).data["design_id"]

def test_separation_flags_design_pr_touching_core():
    assert check_separation_files(["designs/x/plane.yaml", "core/hangar/checks.py"], labels=[]) != []
    assert check_separation_files(["designs/x/plane.yaml", "core/hangar/checks.py"], labels=["migration"]) == []
```

- [x] **Step 2: Run** → FAIL
- [x] **Step 3: Implement** (path backslashes normalised in the one `_resolve_design_path` helper all ops use).
- [x] **Step 4: Run** `pytest -q` → PASS; CI green on Linux and Windows
- [x] **Step 5: Commit** `git commit -m "ops: design set/get/diff/copy/sweep/propose; CI keeps designs and code apart"`

### Unit U1.5: Claims graph in PDL + T9 Claims gate [hard] (from DBF-Combined `proofs/1`)

**Files:**
- Create: `schema/claims.schema.json` (adapted from DBF-Combined `redesign/proofs/SCHEMA.md`: node types requirement, claim, calculation, parameter, source, assumption, test), `core/hangar/claims/{graph,calc}.py`, `ops/claims.py`, `gates/claims.py`
- Per design: `designs/<id>/claims.yaml` (optional); `calculation.script` must be a function in `core/hangar/calcs/` registered by name (D14: no `calcs.py` inside `designs/`), never a path into another repo
- Test: `tests/test_claims.py`, fixture `tests/fixtures/claims-mini/` (3 requirements, 4 claims, 2 calcs, 1 failing margin)

**Interfaces:**
- Produces: `load_claims(design: Design) -> ClaimGraph`; `ClaimGraph.recompute() -> list[ClaimResult(id, value, limit, margin, margin_abs: bool, status: Literal["PASS","FAIL","PROPOSED","STALE"])]`; ops `claim.list(path)`, `claim.explain(path, claim_id)` (chain down to sources), `claim.check(path)`; gate `T9.claim.<id>`; `parameter` nodes read PDL values (`P:components[wng-004-l].mass_g`) so `design.set` changes flow into claims.

- [x] **Step 1: Failing tests**

```python
def test_margin_rules_match_proofs_1(mini):          # >= and <= margins, limit 0 → margin_abs
    r = {c.id: c for c in load_claims(mini).recompute()}
    assert r["CL-AERO-TW"].margin == pytest.approx((1.72 - 1.6) / 1.6)
    assert r["CL-STR-CLEAR"].margin_abs is True

def test_failing_margin_fails_t9(mini):              assert status(mini, "T9.claim.CL-MASS-GATE") == "FAIL"
def test_claim_without_calc_is_proposed_not_pass(mini): assert status(mini, "T9.claim.CL-PROP-NOISE") == "SKIP"
def test_design_set_flows_into_claim(tmp_mini):
    call("design.set", path=tmp_mini, key="components[battery].mass_g", value="400", why="t", kind="modify")
    assert status(tmp_mini, "T9.claim.CL-MASS-GATE") == "FAIL"
def test_concept_a_claims_import_roundtrip(dbf_combined_claims):   # 4 claims.*.json files from qp/A/proofs
    g = import_proofs1(dbf_combined_claims); assert len(g.nodes) == count_nodes(dbf_combined_claims)
```

- [x] **Step 2: Run** → FAIL
- [x] **Step 3: Implement** (port the margin rules from DBF-Combined `redesign/proofs/build_graph.py`; record the port in `PROVENANCE.md`); `import_proofs1(paths) -> ClaimGraph` used by U2.5.
- [x] **Step 4: Run** → PASS
- [x] **Step 5: Commit** `git commit -m "claims: proofs/1 graph as PDL claims.yaml, recompute, T9 gate, claim ops"`

### Unit U1.6: Interface graph and connection-type library (from DBF-Combined `dbf-interfaces/1`)

**Files:**
- Create: `standards/connection-types.yaml` (from `redesign/interfaces/connection_types.json`, each type with `rating_basis` and `source`), `gates/interfaces.py`
- Modify: `schema/plane.schema.json` (`attachments[].connection: <connection-type id>`, optional `seat`), `core/hangar/importers/dbf.py` (reads `interfaces.json` edges)
- Test: `tests/test_interfaces.py`

**Interfaces:**
- Produces: `T1.interfaces.floating` (every component reachable from root through attachments — already T1 connectivity; this adds that each attachment's `connection` exists in the library), `T1.interfaces.connection_known`, op `standards.connections`.

- [x] **Step 1: Failing tests**: `test_unknown_connection_type_fails`, `test_every_library_type_has_source_or_pending`, `test_dbf_interfaces_import_keeps_edge_count` (concept A `interfaces.json` edges == PDL attachments + `edges_pending`).
- [x] **Step 2–4:** implement; run → PASS
- [x] **Step 5: Commit** `git commit -m "interfaces: shared connection-type library; attachments name their connection"`

### Unit U2.1: Gate registry + T6 Mechanisms, T7 Integration, T8 Sourcing [hard]

**Files:**
- Create: `standards/gates.yaml`, `core/hangar/gates/{__init__,mechanisms,integration,sourcing}.py`
- Modify: `core/hangar/checks.py` (tiers 0–5 registered through `gates/`, behaviour unchanged), `standards/design-standards.yaml` (new keys: `mechanism_ratio_tol` (internal convention), `wire_clearance_mm` (pending, D5), `transport_box_mm` default (pending, D5), `bom_verified_max_age_days: 30` (internal convention)), `designs/example-tailsitter-wing/plane.yaml` gets a mechanism and wiring so the gates have a positive example
- Test: `tests/test_gates.py`, fixtures `tests/fixtures/mech-{good,jammed,unlinked}.yaml`
- Also (§1c, 2026-11-21): the five discipline gates from the DBF-Combined role checklists are **not** added here; they register on this unit's registry in U3.6.
- Also (D11, Tristan 2026-11-21): a component whose `type` the gates don't know gets a SKIP naming the type and what is missing, not a T0.schema FAIL; extends `tests/test_ops_contract.py::test_unknown_component_type_gives_skip_not_crash` to assert SKIP (Review Focus #1).

**Interfaces:**
- Produces: `@gate(id: str, tier: int)` registration; `run_gates(design, max_tier: int = 8) -> Scorecard` (Scorecard gains `fidelity: dict`); ops `gate.list`, `gate.explain(check_id)`, `sim.mechanism(path, mechanism_id)` (returns per-step follower angles for the Physics mode).

- [x] **Step 1: Failing tests**

```python
def test_linked_flap_follows_servo(mech_good):     assert status(mech_good, "T6.mechanism.flap_l") == "PASS"
def test_jammed_linkage_fails_with_step(mech_jammed):
    r = result(mech_jammed, "T6.mechanism.flap_l"); assert r.status == "FAIL" and "deg" in r.message
def test_undriven_joint_warns(mech_unlinked):       assert status(mech_unlinked, "T6.undriven.tilt") == "WARN"
def test_exposed_wire_fails_unless_reasoned(wire_outside, wire_outside_ok):
    assert status(wire_outside, "T7.wiring.esc_to_motor_l") == "FAIL"
    assert status(wire_outside_ok, "T7.wiring.esc_to_motor_l") == "PASS"
def test_transport_group_too_big_fails(wing_too_long):  assert status(wing_too_long, "T7.transport.wing") == "FAIL"
def test_stale_bom_line_fails(bom_stale):          assert status(bom_stale, "T8.bom.verified.motor") == "FAIL"
def test_tiers_0_5_unchanged_for_committed_designs(baselines):  # every baseline.json still matches
    for d, base in baselines: assert known_failures(run_gates(d, 5)) == base
def test_scorecard_reports_fidelity(concept_a):
    f = run_gates(concept_a).fidelity; assert {"sourced_blocking", "blocking", "measured_mass_parts"} <= f.keys()
```

- [x] **Step 2: Run** → FAIL
- [x] **Step 3: Implement.** T6 builds on `sim.py`'s MJCF export: position actuator on the driver joint, equality constraints from `kinematic_link`, gravity 0, friction 0; read follower qpos each 1° step; contacts filtered to unattached pairs. D7 default: T7/T8 non-blocking (WARN) via `blocking: false` in `gates.yaml`.
- [x] **Step 4: Run** `pytest -q` → PASS; `plane design validate designs/concept-a --json` shows T6–T8 and the fidelity line
- [x] **Step 5: Commit** `git commit -m "gates: registry; T6 mechanisms (MuJoCo), T7 wiring/transport/assembly, T8 BOM; fidelity line"`

### Unit U2.2: Standards database — close the pending sources (R10, R13)

**Files:**
- Create: `ops/standards.py` (`standards.list`, `standards.show`, `standards.pending`), `knowledge/sources/std-*.md` (new, one per source opened)
- Modify: `standards/design-standards.yaml` (sources), `knowledge/sources/std-SUMMARY.md`
- Test: `tests/test_standards.py`
- Also (§1c, D19, 2026-11-21): close sources only for keys that **existing** gates and skills read (U2.1 and earlier); U3.6 adds its own keys as `pending`. The remaining `STD:` rows stay in `discipline-extract/` as evidence.

**Interfaces:**
- Produces: `standards.pending -> data.items: list[{key, value, blocking: bool, candidates: list[source ids]}]`

- [x] **Step 1: Failing test**: `test_no_blocking_threshold_is_pending_without_a_decision()` — every `pending` key used by a blocking gate has a ledger decision (D5/D6) referencing it.
- [x] **Step 2: Run** → FAIL (2 keys)
- [x] **Step 3a: Knowledge import:** scouts turn DBF-Combined `redesign/config-study/` (43 concept cards, judging) and `docs/research/` into `knowledge/` entries via the templates, each linked to its morph-chart cell; `PROVENANCE.md` lists each source file.
- [x] **Step 3: Scouts** (Haiku, template `knowledge/TEMPLATE-source.md`, only sources actually opened): STANAG 4703 Annex B landing loads, ASTM F3298 load tables, the paper behind the 1.2–1.5 T/W forum claim, NASA-STD-5001 factors for printed parts, DBF rules for box size; `recon` ranks them and proposes values; conductor writes D6 with the options.
- [x] **Step 4: Run** → PASS
- [x] **Step 5: Commit** `git commit -m "standards: sources for landing factor, hover T/W, transport; pending list op"`

### Unit U2.3: Tool adapters — OpenCAE, MuJoCo, AeroSandbox, DaVinci [hard]

**Files:**
- Create: `core/hangar/adapters/{__init__,opencae,mujoco,aerosandbox,blender,sitl,davinci}.py` (`blender` ports DBF-Combined `redesign/collision/collide.py` as an optional higher-fidelity collision/transport check; `sitl` wraps `redesign/qp/A/sitl/a_plant.py`, report-only), `ops/tools.py` (`tools.doctor`), `ops/fea.py` (`fea.plan`, `fea.run`)
- Modify: `opencae_runner.py` → used only by `adapters/opencae.py`; `plane fea` becomes an alias
- Test: `tests/test_adapters.py`
- Also (D13, Tristan 2026-11-21): `fea.part_hash` hashes only the standards keys FEA reads (not the whole `design-standards.yaml`), lands before U2.2 edits standards; concept-a results are re-hashed once from unchanged inputs, with a test that editing an unrelated standards key leaves results fresh.

**Interfaces:**
- Produces: `class Adapter(Protocol): name: str; def available(self) -> tuple[bool, str]` (reason + fix command); `def run(self, design: Design, **params) -> OpResult`. `get_adapter(name) -> Adapter`. OpenCAE adapter prefers Vaibhav's `opencae` CLI if on PATH (contract agreed with him in this unit: `opencae solve --deck <inp> --json`), else the current in-repo runner.

- [x] **Step 1: Failing tests**

```python
def test_missing_tool_is_skip_with_fix(monkeypatch, concept_a):
    monkeypatch.setattr(OpenCAE, "available", lambda self: (False, "run: plane fea --setup …"))
    r = call("fea.run", path=concept_a, part="wng-004-l")
    assert r.skipped and "plane fea --setup" in r.messages[0]
    assert run_gates(load_design(concept_a)).accepted is False

def test_doctor_lists_every_adapter():
    assert {a["name"] for a in call("tools.doctor").data["adapters"]} == {"opencae","mujoco","aerosandbox","blender","sitl","davinci"}

def test_fea_results_identical_through_adapter(cantilever_fixture):   # same 1.003 mm as test_fea.py
    assert abs(call("fea.run", **cantilever_fixture).data["tip_disp_mm"] - 1.003) < 0.01
```

- [x] **Step 2: Run** → FAIL
- [x] **Step 3: Implement.** DaVinci: `available()` returns False with "D3 open: no API access configured" until D3 is answered; then `davinci.push` sends PDL + STEP files, `davinci.pull` brings a DaVinci build back as a `design.propose` PR.
- [x] **Step 4: Run** `pytest -q` → PASS; Vaibhav runs `plane fea run designs/concept-a --all` on his machine and pastes the summary in the PR (R9 first half)
- [x] **Step 5: Commit** `git commit -m "adapters: one contract for OpenCAE, MuJoCo, AeroSandbox, DaVinci; tools doctor"`

### Unit U2.4: Team-ops commands (R7, R14, R26, R27, R31, R38)

**Files:**
- Create: `ops/{idea,research,morph,bom,assembly,ledger_ops,update}.py`, `knowledge/ideas/`, `updates/<YYYY-MM-DD>/` (per-week YAML), `viewer/updates/` (generated)
- Test: `tests/test_team_tasks.py` (the 12-task acceptance list from §2.1)
- Also (moved from U0.3 by Tristan, 2026-11-21): `plane ledger ingest <ledger/inbox/<date>.yaml>` — validates a scout's transcript extract against `schema/ledger.schema.json` and appends to `ledger/items.yaml` via `Ledger.add`; test: an invalid inbox file exits 2 and writes nothing (R27).

**Interfaces:**
- Produces: `idea.add(title, body, by) -> data.path`; `research.new(kind: Literal["source","diy"], slug) -> data.path`; `research.check(path) -> data.missing_fields`; `morph.add_option(dimension, id, name, source)`, `morph.coverage() -> data.cells: list[{dimension, option, designs}]`; `bom.verify(path, item, method, evidence, by)` (records a verification an agent did in Chrome — the CLI never scrapes); `bom.cost(path)`; `assembly.animate(path, out) -> glb with one animation track per sequence step`; `ledger.add/set/check/report/ingest`; `update.new(week)`, `update.add(week, person, link, changed)`, `update.publish(week) -> data.url` (static page + one line per person; posts the URL to the Drive doc through the connector when run by an agent with Drive access, else prints it).

- [x] **Step 1: Failing test** — one test per team task, each calling only ops:

```python
TEAM_TASKS = ["send_design", "change_parameter", "compare_designs", "run_stress", "run_physics",
              "update_morph_chart", "send_idea", "research_entry", "verify_bom", "test_assembly",
              "weekly_update", "meeting_tasks_check"]
@pytest.mark.parametrize("task", TEAM_TASKS)
def test_team_task_needs_no_code_edit(task, git_clean_repo):
    run_task_script(task)                      # tests/team_tasks/<task>.sh: only `plane …` lines
    assert changed_files(git_clean_repo).isdisjoint(set(glob("core/**")))
```

- [x] **Step 2: Run** → FAIL
- [x] **Step 3: Implement** the ops and the 12 scripts.
- [x] **Step 4: Run** → PASS
- [x] **Step 5: Commit** `git commit -m "ops: idea, research, morph, bom, assembly, ledger, update — every team task via CLI"`

### Unit U2.5: Import concept A, decisions and program constraints from DBF-Combined [hard]

**Files:**
- Modify: `core/hangar/importers/dbf.py` → `plane design import dbf --dbf-root <path> --concept A` writes PDL 1.0 with `params` (from `params-A.json`), `bom` (from `BOM-A.csv`: `unit_usd → unit_cost_usd`, `source_url → url`, `date_checked` + `status: verified → verified{method: browser}`), `requirements` (from `REQUIREMENTS-A.md` / `MISSION.md`), `claims.yaml` (via `import_proofs1`, U1.5), interfaces (U1.6), meshes (LFS), `files` manifest pointing to DBF-Combined CAD scripts by commit
- Create: `standards/program.yaml` (DBF-Combined `CLAUDE.md` hard constraints, each with `source: team constraint, <date>`), `core/hangar/importers/changelog.py` (CHANGE-LOG D-ids + `DECISIONS.md` → ledger `decision` items)
- Modify: `designs/concept-a/` (re-imported), `designs/c0-*`, `designs/tiltwing-cakir` → `status: retired` (D9)
- Test: `tests/test_import_dbf_v2.py`

- [x] **Step 1: Failing tests**

```python
def test_concept_a_bom_total_matches_source(imported_a):
    assert call("bom.cost", path=imported_a).data["total_usd"] == pytest.approx(bom_csv_total(DBF/"redesign/qp/A/BOM-A.csv"), abs=0.01)
def test_every_bom_line_keeps_its_url_and_check_date(imported_a):
    assert all(i["url"] and i["verified"]["date"] for i in load_design(imported_a).data["bom"]["items"] if i.get("verified"))
def test_program_constraints_apply_to_every_active_design(repo_root):
    for d in active_designs(): assert "T8.program.budget" in check_ids(d)
def test_changelog_decisions_in_ledger(ledger):     assert ledger.get("D-182").kind == "decision"
def test_reimport_is_stable(dbf_root, tmp_path):     # running the importer twice gives byte-identical output
    a = import_dbf(dbf_root, "A", tmp_path/"a"); b = import_dbf(dbf_root, "A", tmp_path/"b"); assert same_tree(a, b)
```

- [x] **Step 2: Run** → FAIL
- [x] **Step 3: Implement**; the importer is the only code that knows DBF-Combined's layout.
- [x] **Step 4: Run** → PASS; `plane design validate designs/concept-a` scorecard committed as the new baseline; Dillon checks the BOM and claims against the Explorer (acceptance, 15 min) *(Reopened 2026-11-22, whole-branch review B3: no record of the claims check, T62; BOM part waits for U2.5d, D33.) Done by Tristan 2026-11-23 (T62, P181): claims match; BOM matches except P01/M01 spares, T94.)*
- [x] **Step 5: Commit** (label `migration`) `git commit -m "import: concept A full (params, BOM, requirements, claims, interfaces); program constraints; decision log"`

### Unit U2.5d: Re-import concept A (DBF-Combined a93f14d) into PDL 1.0 and keep every change since the first import [hard]

**Files:**
- Modify: `core/hangar/importers/dbf_geometry.py` (kind `mesh`), `core/hangar/importers/dbf.py` (`_retention_n`, `CONN_METHOD["CT-PITOT-TUBING"]`, `requirements.transport_box_mm`, append the new blocks), `core/hangar/importers/_dbf_dump.py` (`assembly_steps`)
- Create: `core/hangar/importers/dbf_blocks.py` (`bom_block`, `files_block`, `wiring_block`, `transport_block`, `assembly_block`), `tests/test_import_dbf_reimport.py` (core PR), `tests/test_concept_a_reimport.py` (designs PR, reads the live design)
- Modify (designs PR, no `core/`): `designs/concept-a/{plane.yaml, meshes/, import-report.json, fea/, baseline.json, CHANGELOG.yaml (appended), README.md}`; `designs/concept-a/claims.yaml` only if regeneration differs
- Test: `tests/test_import_dbf_reimport.py`, `tests/test_concept_a_reimport.py`; existing `tests/test_import_dbf_v2.py` stays green

**Interfaces:**
- Consumes: `import_concept(dbf_root, concept="A", out_dir=None, log=print) -> Path` (`importers/dbf.py:239`), the `design.set` op (`ops/edit.py:38`), `claim.import-dbf` (`ops/import_dbf.py:16`), `fea.run` (`ops/fea.py:27`), `bom.cost` (`ops/bom.py:88`), `assembly.animate` (`ops/assembly.py:16`)
- Produces: `dbf_blocks.bom_block(root: Path, concept: str, parts_csv: dict[str, dict], commit8: str) -> str`; `files_block(mesh_ids: list[str], commit8: str) -> str`; `wiring_block(edges: list[dict], wire_ids: set[str], commit8: str) -> str`; `transport_block(component_ids: list[str]) -> str`; `assembly_block(steps: list[dict], component_ids: list[str]) -> str`; `dbf_geometry._KIND["mesh"]`; `dbf._retention_n(edge: dict) -> float | None`. Each `*_block` returns YAML text for one top-level key (column 0, ends with a newline).
- Closes: R1, R12, R14, R17, R31 (data gaps, criteria in Part D); ledger T24, T53; the BOM half of T62 becomes runnable. *(R31 did not close here: animate failed at step 44, T72; closed by U5.1 T72, D53)*

- [x] **Step 1: Failing tests** (core PR): `test_mesh_kind_volume_in_mm3`, `test_retention_n_ignores_non_numeric`, `test_conn_method_knows_pitot_tubing`, `test_bom_block_*` (3), `test_files_block_lists_every_mesh`, `test_wiring_block_*` (2), `test_transport_block_one_group`, `test_assembly_block_*` (3), `test_dump_exposes_assembly_steps` (skipif DBF clone missing)
- [x] **Step 2: Run** → FAIL
- [x] **Step 3: Implement** parts 1a and 1b of `briefs/U2.5d-reimport.md`; dry-run the whole importer into a tmp folder (never `designs/`); core PR merged *(merged d421013; ACCEPT 614a820)*
- [x] **Step 3b: Pre-gates fix in place** (D50, D51; brief `briefs/U2.5d-pre-gates.md`, branch `std/u2.5d-pre-gates`): `T2.joint_rf` per-joint rating, D39 detector, test pins to `tests/fixtures/concept-a-frozen`; merged before Step 4. Fixes CI on the Step 4 branch, no new unit (R22). *(merged 41e6689; W4-RD ACCEPT)*
- [x] **Step 4: Designs PR** (part 3 of the brief): re-import into `designs/concept-a/`, replay `CHANGELOG.yaml`, regenerate claims, re-run FEA (hashes change), refresh baseline *(merged d24b6df; W4-RD ACCEPT; 3c findings T73-T82)*
- [x] **Step 5: Run** `plane design validate designs/concept-a`, `plane baseline check --all` (exit 0), `plane progress --write`; Dillon runs the BOM half of T62 against the Explorer *(BOM half done by Tristan 2026-11-23, T62; spares mismatch T94)* *(validate and baseline check --all exit 0 done in 3c and CI 45157339285)*

### Unit U3.1: One surface — Studio with modes, same app on Pages [hard]

**Files:**
- Modify: `viewer/index.html`, merge `viewer/app.js` + `viewer/studio.js` → `viewer/app.js` with `modes/{designs,compare,physics,stress,build,bom,proofs,morph,knowledge,ledger,updates}.js` (Build, BOM and Proofs adapt the DBF-Combined Explorer's build guide, BOM tab, vendor links and proof viewer); `core/hangar/index.py` (`build-index` also writes mechanism sweeps, ledger, updates); `.github/workflows/pages.yml`
- Delete: duplicate render/scorecard code in `studio.js`; the separate OpenCAE dashboard link (its content is the Stress mode)
- Test: `tests/test_studio.py` (extend), `tests/test_viewer_static.py` (Playwright smoke: every mode loads with no console errors, read-only build hides edit controls)

**Interfaces:**
- Consumes: `/api/op/<name>` (U1.2), `build-index` JSON
- Produces: `viewer/data/index.json` v2: `{designs, scorecards, mechanisms, ledger, updates, generated_at}`

- [x] **Step 1: Failing tests** (`test_every_mode_renders_without_console_errors[mode]`, `test_pages_build_has_no_edit_controls`, `test_physics_mode_plays_mechanism_sweep`)
- [x] **Step 2: Run** → FAIL
- [x] **Step 3: Implement**; budget: total JS lines after ≤ lines before + 30 %.
- [x] **Step 4: Run** → PASS; the Pages URL shows this week's update (R28)
- [x] **Step 5: Commit** `git commit -m "studio: one app with modes; Pages build is the same app read-only"`

### Unit U3.2: Skills on the ops layer (R3, R15, R16, R21, R22, R30)

**Files:**
- Rewrite: `skills/{design-concept,review-design,research,make-skill}/SKILL.md` to call ops only
- Create: `skills/design-iterate/SKILL.md`, `skills/recon/SKILL.md`, `skills/plan-scheme/SKILL.md`, `skills/get-it-together/SKILL.md`, `skills/weekly-update/SKILL.md`
- Test: `tests/test_skills.py`
- Also (§1c, 2026-11-21): the six discipline review skills are U3.5, built on this unit's skill shape and tests; `review-design` points to them.

Content rules (from the advisor): `design-iterate` — before any fix list ≥ 1 subtract, 1 modify and 1 adjust option, choose add only with a written reason, record `kind`, and run `recon` when the same check failed twice. `plan-scheme` — max effort, waves by dependency, units = PRs, surface decisions + one permissions prompt, then drop to medium. `get-it-together` — compares `ledger/prompts.jsonl`, the active plan and the roster rules with the session's actual state; output ≤ 15 lines. `make-skill` — research → recon of existing skills → synthesize → de-bloat pass (≤ 120 lines).

- [x] **Step 1: Failing tests**: `test_every_skill_has_six_sections`, `test_skill_commands_exist` (every `plane x y` in a skill is in `registry()`), `test_no_numbers_in_skills` (no thresholds; links to `standards/…#key` instead), `test_skill_under_120_lines`.
- [x] **Step 2–4:** write skills; run → PASS; dry-run `design-iterate` once on `example-tailsitter-wing` and commit the transcript to `reviews/`.
- [x] **Step 5: Commit** `git commit -m "skills: rebuilt on ops; design-iterate, recon, plan-scheme, get-it-together, weekly-update"`

### Unit U3.3: PlaneBench v0 (R32)

**Files:**
- Create: `bench/tasks/{mass-cut-10,fix-static-margin,add-working-flap}.yaml`, `ops/bench.py`, `bench/results/`
- Test: `tests/test_bench.py`

**Interfaces:**
- Produces: task YAML `{id, prompt, start_design, allowed: ["plane *"], grader: [{op, path, expect}]}`; `bench.run(task, agent: str, model: str) -> data.{passed, score, tokens, minutes}` (runs the agent headless with `claude -p` and the `design-engineer` role; grader uses ops only); `bench.report -> markdown table`.

- [x] **Step 1: Failing tests**: `test_grader_passes_on_known_good_solution` (hand-made solution design per task), `test_grader_fails_if_core_changed`.
- [x] **Step 2–4:** implement; run → PASS; run each task once with Haiku, Sonnet, Opus as `design-engineer` (9 runs) and commit `bench/results/2026-11-28.md` — this is a slide for Dec 1.
- [x] **Step 5: Commit** `git commit -m "bench: PlaneBench v0, 3 graded design tasks, first model comparison"`

### Unit U3.4: Proof — an agent iterates concept-a with no code edits (R9, R7 acceptance)

Not a code unit; it tests everything above.

- [x] **Step 1:** Conductor launches `design-engineer` (Sonnet) on concept-a with the goal: "reduce failing checks without adding mass; mechanisms first." Hooks active; `design-engineer` has Bash limited to `plane *` and no Edit on `core/`.
- [x] **Step 2:** It runs `plane design validate`, `plane sim mechanism`, `plane fea run`, `plane design set|sweep`, and opens one or more `plane design propose` PRs. `auditor` runs hourly.
- [x] **Step 3:** Verify mechanically: `git diff --name-only main...design/concept-a/* | grep -cE '^(core|standards|schema)/'` → `0`; compared with `baseline.json`, FAIL count not higher and FAIL+WARN count lower (T8 report-only and T6.link declared-exemption rows excluded, D26); `CHANGELOG.yaml` shows each change's kind and every `add` has a written reason; no rating or threshold changed. (Amended after two runs, advisor W3-X; approved by Tristan 2026-11-21.)
- [x] **Step 4:** Acceptance: Dillon repeats one iteration himself in Plane Studio (no terminal), Vaibhav repeats one with `plane fea` on Windows. Each records time taken in the ledger. *(Tristan, 2026-11-21: Tristan runs both checks himself to close W3; each is logged as "done by Tristan". Tristan does the Studio iteration cold, as an outside user who does not know the internals, so his run counts for R9 and Dillon need not repeat it; R25 approval of concept-a PRs is Tristan's until Dillon is available.)*
- [x] **Step 5:** Tristan merges or closes the PRs after Dillon's approval (R25). `plane ledger set R7 R9 done --evidence <PR urls>`.

### Unit U3.5: Discipline skills, scorecard and procedures (from §1c; not on the core path)

**Files:**
- Create: `skills/{review-structures,review-aero,review-controls,review-propulsion,review-manufacturing,review-test-safety}/SKILL.md` (each ≤ 120 lines, six sections like the U3.2 skills, every check item cites its extract row `discipline-extract/<id>.md#<n>`, no thresholds in skill text — numbers come from `standards/` keys by name)
- Modify: `standards/review-scorecard.md` (sections *Evidence and closure*, *Discipline sign-off*), `.claude/agents/{reviewer,design-engineer}.md` (one pointer line each: read the discipline skills that match the design's subsystems)
- Create: `knowledge/procedures/<topic>.md` for the 19 §1c knowledge topics via the knowledge template; `PROVENANCE.md` rows (one per source role folder)
- Test: `tests/test_skills.py` gains `test_discipline_skills_size_and_sections` (each ≤ 120 lines, six sections), `test_discipline_skill_items_cite_extract_rows`, `test_no_numbers_in_skills` already covers thresholds

- [x] **Step 1: Failing tests** (the three above)
- [x] **Step 2–4:** write skills from the `SKILL:` rows of the extracts, the scorecard sections from the `SCORECARD:` rows, knowledge entries from the `KNOW:` rows; run → PASS
- [x] **Step 5: Commit** `git commit -m "skills: six discipline review skills, scorecard evidence and sign-off, procedures (from DBF-Combined TEAM roles)"`

### Unit U3.6: Discipline gates [hard] (from §1c; not on the core path)

**Files:**
- Create: `core/hangar/gates/discipline.py` registering `T2.joint_rf`, `T3.control_authority`, `T3.transition_margin`, `T3.endurance`, `T7.electrical_rating` in the U2.1 gate registry (criteria in §1c; each names its PDL paths and standards keys); `standards/load-cases.yaml`, `standards/operations.yaml`; its own keys as `pending` there, in `standards/connection-types.yaml` (ratings) or in non-FEA keys of `design-standards.yaml`; optional PDL fields the gates need (D21)
- Test: `tests/test_discipline_gates.py` (per gate: a passing and a failing fixture from the §1c rules; missing data or a pending threshold gives SKIP naming what is missing, never PASS; acceptance: concept-a gets PASS or FAIL, not SKIP, for each gate once its D21 fields are set); `tests/test_standards_referenced.py` (D19: every `standards/*.yaml` key is read by a gate or named by a skill)
- Also: the §1c rows coded to existing gates become test fixtures and criteria text for those gates (`tests/test_discipline_gates.py::test_existing_gate_rows_*`), no new code.
- Rules: five gates (D20); every new gate is report-only (WARN) until D7's date; a gate a design can pass without the data it checks is a bug (§1c, advisor); no `design-standards.yaml` key that FEA reads

- [x] **Step 1: Failing tests**
- [x] **Step 2–4:** implement the five gates on the registry; run → PASS; `plane baseline check --all` shows only new WARN rows
- [x] **Step 5: Commit** `git commit -m "gates: five discipline gates (joint RF, control authority, transition, endurance, electrical rating)"`

### Unit U4.1: Whole-branch review, performance, release

- [x] **Step 1:** Fresh `reviewer` (Opus) reviews `main` since `f462468` against §1–§2 and `standards/review-scorecard.md`; blocking items reopen their unit (not a new unit).
- [x] **Step 2:** Performance (R33): measure `plane design validate designs/concept-a` (tiers 0–8, no FEA); if > 60 s, one `builder-plus` unit to cut it, measured before/after.
- [x] **Step 3:** Subtraction pass: `auditor` lists files, commands, docs and ledger items not used by any test, skill or op; conductor deletes or archives; stale ledger items closed with `superseded` (R23).
- [x] **Step 4:** Docs: `README.md` ≤ 80 lines pointing to `docs/pdl/`, `docs/cli.md` (generated from `ops list`), `standards/agents.md`. Tag `v1.0.0`; Pages deploys.
- [x] **Step 5:** verification-before-completion: paste `pytest -q`, `plane baseline check --all`, `plane ledger report`, `plane tools doctor` outputs into `reviews/2026-11-30-v1.0.md`.

### Unit U5.1: Overnight core fixes (D51; ledger tasks agents can close without a design or standards decision)

**Scope:** T72 (assembly animate skips non-drawable proxy steps; closes R31), T52 (`plane ledger set` sets due, units, note), T58 (`design set --value` with ": "), T17 (bom.py exits 2 on bad input; ingest de-dup), T26 (`gate explain` exact check id), T28 (held for v1.1, D52), T68 (knowledge copy check). Core and tests only: no `designs/`, no `standards/` threshold change. One branch per task `std/u4.3-<task>`, merged to main after review (D30, D47).

- [x] **Step 1: Briefs** (tactician W5-T; T28 held, D52; T57 needs none, closed): `plans/2026-11-20-standardization/briefs/U5.1-<task>.md`, each builder-ready (R-a dry run, R-b tests against base)
- [x] **Step 2: Build** one builder per brief (builder-plus for [hard]); at most 2 at once (memory) *(t72 7c9e406, t58 48a15f8, t68 1f47011, t17 f4443ce, t52 ca0fedb, t26 c1fb8f7)*
- [x] **Step 3: Review** W5-R; merge; tasks set done with the merge commit; R31 done if T72 merges. (T57 added after audit 2 if the flake recurred.) *(all six ACCEPT, reviews/2026-11-23-w5.md; merged; last 11beb6f; follow-ups T83-T85)*

### Unit U5.2: Overnight core fixes, round 2 (D51)

**Scope:** T84 (flaky `test_propose_link_survives_real_git_side_effects` 404), T85 (U5.1 small follow-ups), T15 (T7 point-mass rows SKIP, not PASS), T21 (one exit-code rule for a missing tool, D37), T23 (fea.py/mcp.md polish), T3 (ops registry retry after a failed import), T20 (`sim drop --height-m`). Core, tests and docs only; no `designs/`, no `standards/` change, no CI workflow change. Not in scope: T11 (workflow), T16 (FEA hash change would stale concept-a results), T83 (agent file).

- [x] **Step 1: Briefs** (tactician W6-T; all seven, T84 [hard]; T20 after T21): `briefs/U5.2-<task>.md`, builder-ready (R-a, R-b)
- [x] **Step 2: Build** one builder per brief (builder-plus for [hard]); at most 2 at once (memory) *(t84 2e16152, t21 0f3efc8, t3 ff3d60a, t23 eb780b9, t85 0f4fde5, t15 8cc6e53, t20 1645724)*
- [x] **Step 3: Review** W6-R; merge; tasks set done with the merge commit *(all seven ACCEPT, reviews/2026-11-23-w6.md; last merge d563766; follow-ups T86, T87)*

### Unit U5.3: Overnight core fixes, round 3 (D51)

**Scope:** T7 (Studio `/api/op` path confinement to the repo's designs/ and tmp outputs) [hard], T86 and T87 (W6-R follow-ups), T83 (`gate explain` for FAIL-only ids; design-engineer doc line), T50 (`design migrate` writes a CHANGELOG entry), T54 (bench grader protects designs/; newline), T55 (pdledit flow-list append/remove). Core, tests, docs and agent docs only; no `designs/`, `standards/` or CI workflow change.

- [x] **Step 1: Briefs** (tactician W7-T): `briefs/U5.3-<task>.md`, builder-ready (R-a, R-b) *(six briefs; T55 not briefed: flow-list key syntax undefined, needs Tristan; T54 newline half only; T86 four of six sub-items; T83 table holds T1.attachment_contact only)*
- [x] **Step 2: Build** one builder per brief (builder-plus for [hard]); at most 2 at once (memory) *(t54 c3bf979, t50 8dc23ca, t87 bf71e18, t83 34a715a, t86 2c57859, t7 cefea52)*
- [x] **Step 3: Review** W7-R; merge; tasks set done with the merge commit *(six ACCEPT, T7 after one REOPEN (D54); reviews/2026-11-23-w7.md; last merge ab0ad38; T54 T83 T86 stay open for undone halves; T55 not briefed; T89 follow-up)*

### Unit U5.4: bench.run agent id check (T89, from the W7-R T7 re-review; D51)

**Scope:** T89 only: `bench.run` checks `agent` (and `task` if it names a file) against the id rule in the op, so CLI, MCP and Studio are all covered; `ID_RE` defined once and matched exactly (fullmatch). Core and tests only.

- [x] **Step 1: Brief** (tactician W8-T): `briefs/U5.4-t89.md` *(easy; mcp_server.py _ID_RE and morph.py ID_RE left out of scope)*
- [x] **Step 2: Build** (builder W8-B) *(e3f4eda)*
- [x] **Step 3: Review** (reviewer W8-R); merge; T89 done *(ACCEPT, reviews/2026-11-23-w8.md; merged 798fc37; follow-up T90)*

### Unit U5.5: List-entry edits and bench grader replay (T55, T54; D55, D56)

**Scope:** T55: `plane design set <path> --append X` / `--remove X` on one-line flow lists (D55). T54 grader half: the bench grader snapshots the design, logs every `plane` command of the run, replays the log on a fresh copy and fails the run when `designs/` differs (D56). Core and tests only.

- [x] **Step 1: Briefs** (tactician W9-T): `briefs/U5.5-t55.md`, `briefs/U5.5-t54.md` *(7aaeecc; t55 easy, t54 hard)*
- [x] **Step 2: Build** (W9-B, one per brief) *(t55 0215d10 builder; t54 27ae9ea builder-plus)*
- [x] **Step 3: Review** (reviewer W9-R); merge; T55, T54 done *(both ACCEPT, reviews/2026-11-23-w9.md; merged 99fc961, 41aa2a8; follow-ups T92, T93)*

### Unit U6.1: Bench grader hardening (T91, T92, T93; P175)

**Scope:** T91 ops that write under `DESIGNS_DIR` write into the run's workspace, not the repo; T92 pin the pre-run snapshot (hash in memory or separate temp dir) and replay only an allow-list of ops; T93 the minor W9-R items (workspace path mapping, unwritable log path, `--append` spacing, `--remove` of a mapping, `pass` at edit.py:62). Core and tests only.

- [x] **Step 1: Briefs** (tactician W10-T): `briefs/U6.1-*.md` *(d207730: U6.1-bench hard, U6.1-edit easy; no shared files)*
- [x] **Step 2: Build** (W10-B, one per brief; at most 2 at once) *(bench c703281 builder-plus; edit dd0d83f builder)*
- [x] **Step 3: Review** (reviewer W10-R); merge; T91, T92, T93 done *(edit ACCEPT merged ea7c0f5; bench REOPEN once (-- before verb, validate --out), ACCEPT on re-review, merged 58df639; follow-ups T101)*

### Unit U6.2: Yaw authority fix and concept-a battery harness (T37, T60; D57, D58)

**Scope:** T37: advisor W11-A picks the `T3.control_authority` yaw fix (D58), tactician briefs it, builder-plus builds it (core and tests only). T60: design-engineer W11-G sets concept-a `hrn-bat` to 10 AWG with `plane design set` (designs only, D57) and reports the gates before and after. Separate branches; the T60 branch touches no `core/`.

- [x] **Step 1:** Advisor pick and brief (W11-A, W11-T): `briefs/U6.2-t37.md` *(pick: `briefs/U6.2-t37-advice.md`, D58; brief f234a51, hard; baseline unchanged)*
- [x] **Step 2:** Build T37 (W11-B); T60 design change (W11-G) *(t37 b3049cd builder-plus, baseline unchanged; t60 07969fd 10 AWG, D57 amended)*
- [x] **Step 3: Review** (reviewer W11-R); merge; T37, T60 done *(T37 ACCEPT merged 2c41f6f; T60 REOPEN once (reimport test pinned 14 AWG), ACCEPT on re-review, merged 7c3b87a; follow-ups T98, T99)*

### Unit U6.3: v1.1 cleanup, first batch (T83, T86, T88, T90; P175)

**Scope:** T83 explain the remaining FAIL-only check ids; T86 T3 nested-import rollback and the mixed point-mass/mesh harness test; T88 move `PROP_CHAIN_MAX_INTERMEDIATE` to `standards/*.yaml` with a source or `pending`; T90 one shared `hangar/ids.py` `ID_RE` with fullmatch in mcp_server.py and morph.py, Studio message wording. T28 stays held until after Dec 2 (D52); T67 and the T4-T19 items come in a later batch.

- [x] **Step 1: Briefs** (tactician W12-T): `briefs/U6.3-*.md` *(four easy briefs, landed in 285d9e4; order: T88+T90, then T83 before T86)*
- [x] **Step 2: Build** (W12-B, one per brief; at most 2 at once) *(t88 9c8375a, t90 018f74e, t83 e7efc5c, t86 4a1263f; all builder)*
- [x] **Step 3: Review** (reviewer W12-R); merge; T83, T86, T88, T90 done *(T83, T88 ACCEPT merged 8c720eb, 34d21b2; T86, T90 REOPEN once, ACCEPT on re-review, merged 7741d29, a4894dc; follow-ups T100, T102)*

### Unit U6.4: Recompute the 40 read_value claims (T28; D59 overrules D52)

**Scope:** register `read_value` (brief `U5.1-t28.md`, refreshed on current main), core and tests only; then, on a separate branch, refresh concept-a claim statuses through the CLI if they are stored in `designs/` and update the deck (`docs/deck/index.html`) and `u4.2/metrics.md`/`deck-outline.md` lines that say the claims are not recomputed, with the measured PASS/FAIL counts.

- [x] **Step 1: Brief** (tactician W13-T): `briefs/U6.4-t28.md` (core) and the docs/designs follow-up steps *(0c113a6; measured: 40 SKIP -> 40 PASS, 0 FAIL; baseline 40 improvements, refresh in part 2; stale deck totals T97 go into part 2)*
- [x] **Step 2: Build** (W13-B): core branch, then the docs/designs branch *(core e03fc2b, W13-R ACCEPT, merged b8b03cc, T28 done; docs 0f84a10/64e851d/7728d83 merged 57a3a40)*
- [x] **Step 3: Review** (reviewer W13-R); merge; T28 done *(core ACCEPT; part 2 REOPEN once (slide title), ACCEPT; reviews/2026-11-23-w13.md; T97 done; follow-ups T103, T104)*

### Unit U7.1: Dec 2 prep: demo re-run on current main, claims wording sweep (U14.1 Step 2, T104; P186)

**Scope:** re-run every step of `u4.2/demo-script.md` on a scratch clone of current main (never `designs/`) and update expected outputs, wall times and fallbacks; brief and build T104 (README.md, docs/cli.md wording per D60). The backup video stays with Tristan.

- [x] **Step 1:** Demo re-run and T104 brief (tactician W14-T) *(d54bef8: re-run on 39c7c58, steps 2-6 pass, issues 9-11 added (11-30 URL 404 until merged + Pages run; cold Studio 278 s); `update publish` not run (permission refused), read from code)*
- [x] **Step 2:** Build T104 (W14-B) *(5b31c07)*
- [x] **Step 3: Review** (reviewer W14-R); merge; T104 done *(T104 ACCEPT, merged c7a5dc7 with windows red only on the T84 race (W14-A diagnosis); demo re-run REOPEN once, ACCEPT 7540ad7; follow-up T105)*
- [x] **Step 4:** T84 reopened in place: Studio stores DESIGNS_DIR/DATA_DIR/CACHE_FILE at construction so leaked workers cannot touch another test's sandbox (W14-A); brief W14-T2, build W14-B2 (builder-plus), review W14-R *(38bb968, W14-R ACCEPT, windows CI green, merged afcc8d2; T84 done; follow-up T109)*

### Unit U7.2: BOM spares double count (T94; P186)

**Scope:** importer `importers/dbf_blocks.py:27` stops adding spares to a qty that already includes them (core + tests); then a designs-only branch sets concept-a P01 qty 5 and M01 qty 3 with `plane design set` (BOM lines total $1262.50) and refreshes any test that pins the old quantities.

- [x] **Step 1: Brief** (tactician W15-T): `briefs/U7.2-t94.md` *(d4407ec; only P01 and M01 have spares)*
- [x] **Step 2: Build** (W15-B): core branch, then designs branch *(core d5bcda9, W15-R ACCEPT, merged df2d19e; designs 50aeb72/b70291a merged be51625)*
- [x] **Step 3: Review** (reviewer W15-R); merge; T94 done *(both parts ACCEPT, reviews/2026-11-24-w15.md; BOM $1262.50)*

### Unit U7.3: v1.1 cleanup, second batch (T99, T100, T101, T102; P186)

**Scope:** the non-blocking follow-ups of W10-R to W12-R: yaw SKIP text and control-moment data key (T99); T83 guard beyond checks.py, scorecard criterion form, T1.motor_has_prop criterion, research.py SLUG_RE fullmatch, ID_RE imports from hangar.ids (T100); bench path mapping of option values, PLANE_BENCH_LOG pinning, SWEEP_ROOT redirect, tree_digest docstring (T101; the paid redirection probe stays open); T86 recovery test and comment (T102).

- [x] **Step 1: Briefs** (tactician W16-T): `briefs/U7.3-*.md` *(bb136c4: four easy briefs; T99 before U7.4 T95; T101 before T100; T99 untrimmed-yaw criterion deferred to U7.4; paid probe stays open)*
- [x] **Step 2: Build** (W16-B, at most 2 at once) *(t99 5ec7d16, t102 297f94e, t101 579406a (brief amendment 1: patch extracted mechanically), t100 4946c8a; all builder)*
- [x] **Step 3: Review** (reviewer W16-R); merge; T99-T102 done *(T99, T102, T100 ACCEPT merged 9fb1a6b, 790249e, 672bc11; T101 REOPEN once (--template path), ACCEPT, merged e72f545; T101 stays open for the paid redirection probe)*

### Unit U7.4: v1.1 features (T95, T103, T67; P186)

**Scope:** T95 prop reaction torque in PDL (optional `propulsion.spin`, `propulsion.torque_per_thrust_m` with `_source`; schema minor 1.0 -> 1.1) and its use in T3.control_authority yaw; T103 a distinct status or marker for stored-result (read_value) claims; T67 ops `bom.list`, `morph.list`, `idea.list` (davinci push/pull only if the adapter supports it, else stays open).

- [x] **Step 1: Briefs** (tactician W17-T): `briefs/U7.4-*.md` *(32336a4: t95 hard (patch A/B by T99), t103 easy (read flag on PASS), t67 easy (3 list ops); D61; leftovers T106, T107)*
- [x] **Step 2: Build** (W17-B, at most 2 at once) *(t103 8b71ce1, t67 712ed3b builder; t95 7385e97 builder-plus, patch B)*
- [x] **Step 3: Review** (reviewer W17-R); merge; T95, T103, T67 done *(all ACCEPT, reviews/2026-11-24-w17.md; merged e3c5b99, f9463d4, dce451a; follow-ups T107, T108)*

### Unit U7.5: Knowledge import of DBF-Combined docs/research (U2.2-3; D28 deferred, D62 runs it now; P188)

**Scope:** turn DBF-Combined `docs/research/` (23 files @ a93f14da) into `knowledge/` entries through the existing templates (same pattern as U2.2-2, merged dc8902a): adapted not copied (the knowledge copy check must pass), each entry linked to its morph-chart cell where one fits, each source file listed in `PROVENANCE.md`; only sources actually opened are cited. Knowledge and provenance files only; no core/, designs/, standards/.

- [x] **Step 1: Brief** (tactician W18-T): `briefs/U2.2-3-research-import.md` *(646708f: 23 entries in knowledge/research/, extracted by script; copy check 0 shared 10-word runs; test widening T110)*
- [x] **Step 2: Build** (builder W18-B) *(b306c2d; corrected 8aa03d4)*
- [x] **Step 3: Review** (reviewer W18-R); merge *(REOPEN once: 7 accuracy errors fixed via brief amendment 1; ACCEPT; merged 1b0bcac; test widening T110)*
