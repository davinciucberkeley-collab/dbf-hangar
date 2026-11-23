from __future__ import annotations
import json, os, re, shutil
from pathlib import Path
import pytest
import yaml
from jsonschema import Draft202012Validator
from hangar.claims.graph import ClaimGraphError, load_claims
from hangar.design import REPO_ROOT, load_design
from hangar.importers import dbf_claims
from hangar.importers.dbf_claims import import_claims
from hangar.importers.changelog import import_decisions
from hangar.ledger import Ledger
from hangar.ops import call, registry

MINI = REPO_ROOT / "tests" / "fixtures" / "dbf-mini"
DBF = Path(os.environ.get("DBF_COMBINED", "C:/Users/trist/DBF-Combined"))


def import_claims_to(tmp_path):
    p = import_claims(MINI, "A", tmp_path / "out", log=lambda m: None)
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def _by_id(doc):
    return {n["id"]: n for n in doc["nodes"]}


def test_claims_import_keeps_every_node_and_declares_each_referenced_parameter(tmp_path):
    doc = import_claims_to(tmp_path)
    assert len(doc["nodes"]) == 5 + 3
    params = [n for n in doc["nodes"] if n["type"] == "parameter"]
    assert [n["id"] for n in params] == ["P:wing.span_m", "P:env.g_ms2", "P:req.lim"]
    assert all("value" in n for n in params)
    ids = _by_id(doc)
    assert "P:req.unused" not in ids
    calc = ids["CALC-X"]
    assert "script" not in calc
    assert calc["imported_from"] == {"script": "redesign/qp/A/proofs/x.py"}


def test_imported_claims_validate_against_the_claims_schema(tmp_path):
    doc = import_claims_to(tmp_path)
    schema = json.loads((REPO_ROOT / "schema" / "claims.schema.json").read_text(encoding="utf-8"))
    assert list(Draft202012Validator(schema).iter_errors(doc)) == []


def test_part_ids_are_lowercased_to_pdl_ids(tmp_path):
    assert _by_id(import_claims_to(tmp_path))["CL-X-A"]["parts"] == ["wng-001", "avn-001"]


def test_undeclared_source_moves_to_note_and_unknown_parameter_errors(tmp_path):
    ids = _by_id(import_claims_to(tmp_path))
    span = ids["P:wing.span_m"]
    assert "source" not in span and "SRC-NOT-DECLARED" in span["note"]
    assert ids["P:req.lim"]["source"] == "SRC-X-ENV"
    assert ids["P:req.lim"]["status"] == "UNVERIFIED"
    copy = tmp_path / "mini"
    shutil.copytree(MINI, copy)
    pj = copy / "redesign" / "qp" / "A" / "params-A.json"
    d = json.loads(pj.read_text(encoding="utf-8"))
    del d["wing"]
    pj.write_text(json.dumps(d), encoding="utf-8")
    with pytest.raises(ClaimGraphError, match=re.escape("P:wing.span_m")):
        import_claims(copy, "A", tmp_path / "o2", log=lambda m: None)


def test_import_claims_writes_only_claims_yaml(tmp_path):
    import_claims(MINI, "A", tmp_path / "out", log=lambda m: None)
    assert sorted(p.name for p in (tmp_path / "out").iterdir()) == ["claims.yaml"]
    with pytest.raises(ValueError):
        import_claims(MINI, "A", None, log=lambda m: None)


def test_reimport_is_stable(tmp_path):
    a = import_claims(MINI, "A", tmp_path / "a", log=lambda m: None).read_bytes()
    b = import_claims(MINI, "A", tmp_path / "b", log=lambda m: None).read_bytes()
    assert a == b


@pytest.mark.skipif(not (DBF / "redesign/qp/A/proofs").exists(), reason="DBF-Combined clone not present")
def test_concept_a_claims_import_recomputes_all_93_read_value_echoes_included(tmp_path):
    p = import_claims(DBF, "A", tmp_path / "d", log=lambda m: None)
    folder = tmp_path / "concept-a"
    folder.mkdir()
    shutil.copy(REPO_ROOT / "designs" / "concept-a" / "plane.yaml", folder / "plane.yaml")
    shutil.copy(p, folder / "claims.yaml")
    g = load_claims(load_design(folder))
    r = g.recompute()
    assert len(r) == 93
    nodes = g.nodes

    def mapped(cid, seen=()):
        """True when the claim uses a PDL path, directly or through a claim it consumes."""
        n = nodes[cid]
        refs = []
        if "limit" in n and "ref" in n["limit"]:
            refs.append(n["limit"]["ref"])
        if "calc" in n:
            refs += list(nodes[n["calc"]]["inputs"].values())
        for ref in refs:
            if not isinstance(ref, str):
                continue
            if ref.startswith("P:") and ref not in nodes:
                return True
            if ref in nodes and nodes[ref]["type"] == "claim" and ref not in seen and mapped(ref, seen + (cid,)):
                return True
        return False

    proposed = {x.id for x in r if x.status == "PROPOSED"}
    read_value = {cid for cid, n in nodes.items()
                  if n["type"] == "claim" and nodes[n["calc"]].get("function") == "read_value"}
    assert len(read_value) == 40
    assert proposed == set()
    others = [x for x in r if x.status != "PROPOSED"]
    assert len(others) == 93
    assert {x.status for x in r if x.id in read_value} <= {"PASS", "STALE"}
    for x in others:
        if x.status == "STALE":
            assert mapped(x.id), f"STALE on a claim with no PDL_MAP parameter: {x.id} {x.value} {x.message}"
            print("PDL-vs-proofs drift: STALE", x.id, x.value, x.message)
        elif x.status == "FAIL":
            print("PDL-vs-proofs drift: FAIL" if mapped(x.id) else "finding: FAIL", x.id, x.value, x.limit, x.message)
        else:
            assert x.status == "PASS"


def test_changelog_decisions_in_ledger(tmp_path):
    out = import_decisions(MINI, tmp_path / "items.yaml", log=lambda m: None)
    assert out == {"changelog": 4, "decisions_md": 2, "skipped": 0, "duplicates": 1}
    led = Ledger(tmp_path / "items.yaml")
    it = led.get("D-182")
    assert it.kind == "decision" and it.source == "CHANGE-LOG#D-182" and it.status == "decided"
    assert "concept A" in it.text and "*" not in it.text
    led.get("D-183b")
    led.get("D-90")
    assert led.get("D-01").text == "Chord 0.30 to 0.32 m"


def test_changelog_import_is_idempotent_and_decisions_md_triage(tmp_path):
    import_decisions(MINI, tmp_path / "items.yaml", log=lambda m: None)
    out = import_decisions(MINI, tmp_path / "items.yaml", log=lambda m: None)
    assert out["skipped"] == 6 and out["changelog"] == 0 and out["decisions_md"] == 0
    led = Ledger(tmp_path / "items.yaml")
    d1 = led.get("DD-1")
    assert d1.status == "superseded" and d1.decided_in == "D9" and "adopt one baseline" in d1.text
    d5 = led.get("DD-5")
    assert d5.status == "open" and d5.decided_in == "" and d5.owner == "" and d5.source == "DECISIONS.md#D5"
    assert "Battery disconnect plug" in d5.text and "pick one plug" in d5.text
    assert led.check(REPO_ROOT) == []


def test_ledger_schema_accepts_new_ids_and_rejects_junk():
    schema = json.loads((REPO_ROOT / "schema" / "ledger.schema.json").read_text(encoding="utf-8"))
    pat = re.compile(schema["$defs"]["item"]["properties"]["id"]["pattern"])
    for ok in ("D-182", "D-183b", "DD-15", "D14", "R3"):
        assert pat.search(ok), ok
    for bad in ("D-", "DD-", "X-1", "D-1-2", "d-182"):
        assert not pat.search(bad), bad


def test_pdl_map_is_the_documented_table():
    assert dbf_claims.PDL_MAP == {
        "P:mission.cruise_ms": "P:requirements.cruise_speed_mps",
        "P:mission.clmax": "P:flight.cl_max",
        "P:env.rho_kgm3": "P:flight.air_density_kgm3",
        "P:req.mass_gate_kg": ("P:requirements.mtow_g", 0.001),
        "P:mass.pack_g": "P:components[pwr-001].mass_g",
        "P:cg.chord_mm": "P:components[wng-001].planform.lifting_surface.root_chord",
    }
    assert "P:req.budget_usd" not in dbf_claims.PDL_MAP


def test_scale_one_mapped_refs_become_pdl_paths_without_a_constant_node(tmp_path, monkeypatch):
    monkeypatch.setattr(dbf_claims, "PDL_MAP", {"P:env.g_ms2": "P:requirements.mtow_g"})
    doc = import_claims_to(tmp_path)
    ids = _by_id(doc)
    assert ids["CALC-X"]["inputs"]["b"] == "P:requirements.mtow_g"
    assert "P:env.g_ms2" not in ids and "P:requirements.mtow_g" not in ids
    assert [n["id"] for n in doc["nodes"] if n["type"] == "parameter"] == ["P:wing.span_m", "P:req.lim"]


def test_import_ops_are_registered_and_run(tmp_path):
    assert {"claim.import-dbf", "ledger.import-dbf"} <= set(registry())
    r = call("claim.import-dbf", dbf_root=str(MINI), concept="A", out=str(tmp_path / "o"))
    assert r.ok and r.data["parameters"] == 3
    assert call("ledger.import-dbf", dbf_root=str(MINI), ledger=str(tmp_path / "l.yaml")).data["changelog"] == 4
    bad = call("claim.import-dbf", dbf_root=str(tmp_path / "nope"), concept="A", out=str(tmp_path / "o3"))
    assert bad.ok is False and bad.exit_code == 2 and bad.data["error"] == "input"


@pytest.mark.skipif(not (DBF / "redesign/params/CHANGE-LOG.md").exists(), reason="DBF-Combined clone not present")
def test_real_changelog_import_counts(tmp_path):
    text = (DBF / "redesign/params/CHANGE-LOG.md").read_text(encoding="utf-8")
    n = len(set(re.findall(r"^\|\s*\**(D-\d+[a-z]*)\**\s*\|", text, re.M)))
    out = import_decisions(DBF, tmp_path / "items.yaml", log=lambda m: None)
    assert out["changelog"] == n
    assert out["decisions_md"] == 15
    assert Ledger(tmp_path / "items.yaml").get("D-182").kind == "decision"


def test_no_design_file_is_touched_by_the_importers():
    base = REPO_ROOT / "core" / "hangar" / "importers"
    for name in ("dbf_claims.py", "changelog.py"):
        t = (base / name).read_text(encoding="utf-8")
        assert "plane.yaml" not in t and "designs" not in t, name


def test_scaled_mapping_resolves_and_flows(tmp_path, monkeypatch):
    monkeypatch.setattr(dbf_claims, "PDL_MAP", {"P:req.lim": ("P:requirements.mtow_g", 0.002)})
    d = tmp_path / "d"
    p = import_claims(MINI, "A", d, log=lambda m: None)
    plane = d / "plane.yaml"
    shutil.copy(REPO_ROOT / "tests" / "fixtures" / "claims-mini" / "plane.yaml", plane)
    ids = _by_id(yaml.safe_load(p.read_text(encoding="utf-8")))
    assert ids["P:scale.req.lim"]["value"] == 0.002
    assert ids["CALC-PDL-REQ-LIM"]["function"] == "scale_value"
    assert ids["CALC-PDL-REQ-LIM"]["inputs"] == {"v": "P:requirements.mtow_g", "k": "P:scale.req.lim"}
    assert ids["CL-PDL-REQ-LIM"]["type"] == "claim"
    assert "P:req.lim" not in ids
    assert ids["CL-X-A"]["limit"]["ref"] == "CL-PDL-REQ-LIM"
    r = {c.id: c for c in load_claims(load_design(d)).recompute()}
    assert r["CL-PDL-REQ-LIM"].value == pytest.approx(1.0) and r["CL-PDL-REQ-LIM"].status == "PASS"
    assert r["CL-X-A"].limit["value"] == pytest.approx(1.0)
    text = plane.read_text(encoding="utf-8")
    assert text.count("mtow_g: 500") == 1
    plane.write_text(text.replace("mtow_g: 500", "mtow_g: 600"), encoding="utf-8")
    r = {c.id: c for c in load_claims(load_design(d)).recompute()}
    assert r["CL-PDL-REQ-LIM"].value == pytest.approx(1.2)


def test_n_keeps_integer_zeros():
    from hangar.importers.dbf import _n
    assert _n(2000, 0) == "2000"
    assert _n(10, 0) == "10"
    assert _n(0, 0) == "0"
    assert _n(2000.0, 1) == "2000"
    assert _n(1.50, 2) == "1.5"


@pytest.mark.skipif(not (DBF / "redesign/qp/A/params-A.json").exists(), reason="DBF-Combined clone not present")
def test_concept_a_budget_line_is_2000():
    from hangar.importers.dbf import _n
    P = json.load(open(DBF / "redesign/qp/A/params-A.json", encoding="utf-8"))
    v = P["req"]["budget_usd"]["value"]
    assert v == 2000.0
    assert _n(v, 0) == "2000"
