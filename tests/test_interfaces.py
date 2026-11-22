from __future__ import annotations
import copy, json, os
from pathlib import Path
import pytest
import yaml
from click.testing import CliRunner
from jsonschema import Draft202012Validator
from hangar.checks import tier0_schema, validate
from hangar.cli import cli
from hangar.design import FAIL, PASS, REPO_ROOT, Design, load_design
from hangar.gates.interfaces import load_connection_types
from hangar.importers.dbf import account_interface_edges, read_interface_edges
from hangar.ops import call, registry

EXAMPLE = REPO_ROOT / "designs" / "example-tailsitter-wing" / "plane.yaml"
CONCEPT_A = REPO_ROOT / "tests" / "fixtures" / "concept-a-frozen"
DBF = Path(os.environ.get("DBF_COMBINED", "C:/Users/trist/DBF-Combined"))
SCHEMA = json.loads((REPO_ROOT / "schema" / "plane.schema.json").read_text(encoding="utf-8"))
ROW = "T1.interfaces.connection_known"


def _with(connection):
    data = copy.deepcopy(load_design(EXAMPLE).data)
    data["schema_version"] = "1.0"
    if connection is not None:
        data["attachments"][0]["connection"] = connection
    return Design(data, EXAMPLE)


def _row(design):
    return [r for t in validate(design, max_tier=1).tiers for r in t.results if r.check_id == ROW]


def test_unknown_connection_type_fails():
    rows = _row(_with("CT-NOPE"))
    assert len(rows) == 1
    assert rows[0].status == FAIL
    assert "CT-NOPE" in rows[0].message


def test_every_library_type_has_source_or_pending():
    import re
    lib = load_connection_types()
    assert len(lib) == 44
    methods = {"fastened", "bonded", "clamped", "press_fit", "taped", "strapped", "hinged", "slid",
               "connector", "soldered", "conductive", "radio"}
    for t in lib.values():
        assert re.match(r"^CT-[A-Z0-9-]+$", t["id"])
        assert t["kind"] in {"mechanical", "electrical", "thermal", "kinematic"}
        assert t["method"] in methods
        assert isinstance(t["spec"], str) and t["spec"]
        assert t["rating_basis"] in {"sourced", "derived", "placeholder"}
        assert isinstance(t["source"], str) and t["source"]
        if "structural" in t:
            assert t["structural"] is False
        if t["rating_basis"] == "placeholder":
            assert t["source"] == "pending"
    unstructural = sorted(t["id"] for t in lib.values() if t.get("structural") is False)
    assert unstructural == ["CT-LABEL", "CT-PITOT-TUBING", "CT-TIE", "CT-WIRE-CHANNEL"]


def test_known_connection_passes():
    rows = _row(_with("CT-M3-SHCS-INSERT"))
    assert len(rows) == 1
    assert rows[0].status == PASS


def test_design_without_connection_has_no_interfaces_row_and_example_still_passes_t0():
    assert _row(load_design(EXAMPLE)) == []
    assert tier0_schema(load_design(EXAMPLE)).status == PASS


def test_connection_and_seat_need_schema_1_0():
    d = _with("CT-EPOXY")
    d.data["schema_version"] = "0.4"
    msgs = [r for r in tier0_schema(d).results if r.check_id == "T0.version" and r.status == FAIL]
    assert msgs and "connection" in msgs[0].message
    ok = _with("CT-EPOXY")
    assert not [r for r in tier0_schema(ok).results if r.check_id == "T0.version" and r.status == FAIL]
    ok.data["attachments"][0]["seat"] = "pod recess"
    assert tier0_schema(ok).status == PASS


def test_attachment_schema_accepts_connection_and_seat_and_rejects_junk():
    v = Draft202012Validator(SCHEMA)
    data = _with("CT-EPOXY").data
    data["attachments"][0]["seat"] = "pocket"
    assert list(v.iter_errors(data)) == []
    for bad_key, bad_val in (("connection", "ct-epoxy"), ("connection", 5), ("seat", 5), ("seat", "")):
        data2 = copy.deepcopy(data)
        data2["attachments"][0][bad_key] = bad_val
        assert list(v.iter_errors(data2)), (bad_key, bad_val)


def test_standards_connections_op():
    assert "standards.connections" in registry()
    r = call("standards.connections")
    assert r.ok
    assert r.data["count"] == 44 and len(r.data["connection_types"]) == 44
    assert all(isinstance(t["structural"], bool) for t in r.data["connection_types"])
    elec = call("standards.connections", kind="electrical").data["connection_types"]
    assert elec and all(t["kind"] == "electrical" for t in elec)


def test_standards_connections_bad_kind_and_cli():
    r = call("standards.connections", kind="nope")
    assert r.ok is False
    assert r.exit_code == 2
    assert r.data["error"] == "input"
    out = CliRunner().invoke(cli, ["standards", "connections", "--json"])
    assert out.exit_code == 0
    assert json.loads(out.output)["data"]["count"] == 44


@pytest.mark.skipif(not (DBF / "redesign/qp/A/cad/model").exists(), reason="DBF-Combined clone not present")
def test_dbf_interfaces_import_keeps_edge_count():
    ie = read_interface_edges(DBF, "A")
    assert len(ie["edges"]) == 164
    plane = yaml.safe_load((CONCEPT_A / "plane.yaml").read_text(encoding="utf-8"))
    rep = json.loads((CONCEPT_A / "import-report.json").read_text(encoding="utf-8"))
    acc = account_interface_edges(ie, {a["id"] for a in plane["attachments"]},
                                  rep["bridging_edges_not_emitted"], rep["wire_edges_not_emitted"])
    assert acc["edges"] == 164
    assert acc["attachments"] == 121
    assert acc["bridging"] == 6
    assert acc["wires"] == 14
    assert acc["pending"] == 23
    assert acc["declared_pending"] == 0
    assert acc["unknown_ids"] == []
    assert acc["edges"] == acc["attachments"] + acc["bridging"] + acc["wires"] + acc["pending"]
    lib = load_connection_types()
    for e in ie["edges"]:
        assert e["via"] in lib


def test_account_interface_edges_partitions_and_flags_unknown(tmp_path):
    a = tmp_path / "redesign/qp/A/cad/model/x"
    b = tmp_path / "redesign/qp/A/cad/model/y"
    a.mkdir(parents=True)
    b.mkdir(parents=True)
    (a / "interfaces.json").write_text(json.dumps({"schema": "dbf-interfaces/1",
        "edges": [{"id": "E-1"}, {"id": "E-2"}, {"id": "E-3"}, {"id": "E-4"}],
        "edges_pending": [{"id": "E-9"}]}), encoding="utf-8")
    (b / "interfaces.json").write_text(json.dumps({"schema": "dbf-interfaces/1", "edges": []}), encoding="utf-8")
    ie = read_interface_edges(tmp_path, "A")
    assert len(ie["edges"]) == 4
    assert ie["declared_pending"] == ["E-9"]
    acc = account_interface_edges(ie, {"E-1"}, {"E-2"}, {"E-3", "E-X"})
    assert acc["attachments"] == 1 and acc["bridging"] == 1 and acc["wires"] == 1 and acc["pending"] == 1
    assert acc["pending_ids"] == ["E-4"]
    assert acc["unknown_ids"] == ["E-X"]
    (b / "interfaces.json").write_text(json.dumps({"schema": "other/1", "edges": []}), encoding="utf-8")
    with pytest.raises(ValueError):
        read_interface_edges(tmp_path, "A")
    (b / "interfaces.json").write_text(json.dumps({"schema": "dbf-interfaces/1", "edges": [{"id": "E-1"}]}),
                                       encoding="utf-8")
    with pytest.raises(ValueError):
        read_interface_edges(tmp_path, "A")
    assert read_interface_edges(tmp_path / "nowhere", "A") == {"edges": [], "declared_pending": []}


@pytest.mark.skipif(not (DBF / "redesign/interfaces/connection_types.json").exists(),
                    reason="DBF-Combined clone not present")
def test_library_ids_match_source_when_present():
    src = json.loads((DBF / "redesign/interfaces/connection_types.json").read_text(encoding="utf-8"))["connection_types"]
    lib = list(load_connection_types().values())
    assert [(t["id"], t["kind"], t["method"], t["spec"]) for t in lib] == \
        [(t["id"], t["kind"], t["method"], t["spec"]) for t in src]
