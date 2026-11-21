from __future__ import annotations
import copy, importlib.util, json, os, shutil
from pathlib import Path
import pytest
import yaml
from click.testing import CliRunner
from jsonschema import Draft202012Validator
from hangar.checks import validate
from hangar.claims.calc import load_claims_standards, margin, margin_text, register_calcs
from hangar.claims.graph import ClaimGraphError, claims_path, import_proofs1, load_claims
from hangar.cli import cli
from hangar.design import FAIL, PASS, SKIP, WARN, REPO_ROOT, Design, load_design, load_standards
from hangar.gates.claims import tier9_claims
from hangar.ops import call, registry

MINI = REPO_ROOT / "tests" / "fixtures" / "claims-mini"
EXAMPLE = REPO_ROOT / "designs" / "example-tailsitter-wing"
DBF_PROOFS = Path(os.environ.get("DBF_COMBINED", "C:/Users/trist/DBF-Combined")) / "redesign" / "qp" / "A" / "proofs"
SCHEMA = REPO_ROOT / "schema" / "claims.schema.json"
PROOFS1_MINI = REPO_ROOT / "tests" / "fixtures" / "proofs1-mini" / "claims.mini.json"

_spec = importlib.util.spec_from_file_location("claims_mini_calcs", MINI / "calcs.py")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
register_calcs(_mod.CALCS)


@pytest.fixture
def mini():
    return load_design(MINI)


@pytest.fixture
def tmp_mini(tmp_path):
    dst = tmp_path / "claims-mini"
    shutil.copytree(MINI, dst)
    return dst


def edit_claims(folder, fn):
    p = Path(folder) / "claims.yaml"
    doc = yaml.safe_load(p.read_text(encoding="utf-8"))
    by_id = {n["id"]: n for n in doc["nodes"]}
    fn(by_id)
    doc["nodes"] = list(by_id.values())
    p.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def status(design, check_id):
    for r in tier9_claims(design).results:
        if r.check_id == check_id:
            return r.status
    raise KeyError(check_id)


def results(design):
    return {c.id: c for c in load_claims(design).recompute()}


def test_margin_rules_match_proofs_1(mini):
    r = results(mini)
    assert r["CL-AERO-TW"].margin == pytest.approx((1.72 - 1.6) / 1.6)
    assert r["CL-AERO-TW"].value == pytest.approx(1.72)
    assert r["CL-STR-CLEAR"].margin_abs is True
    assert r["CL-MASS-GATE"].margin == pytest.approx(-0.1)
    assert r["CL-MASS-GATE"].margin_abs is False
    assert r["CL-MASS-GATE"].limit == {"op": "<=", "value": 500}


def test_margin_function_zero_limit():
    assert margin(-0.34, 0, ">=") == -0.34
    assert margin(6, 0, "<=") == -6
    assert margin(0.28, 0, ">=") == 0.28
    assert margin(0.0, 0, ">=") == 0.0
    assert str(margin(-0.0, 0, ">=")) == "0.0"
    assert margin(2.4, 2.0, ">=") == pytest.approx(0.2)
    assert margin(34.6, 30.0, "<=") == pytest.approx(-4.6 / 30.0)
    assert margin(-3.0, -2.0, ">=") == pytest.approx(-0.5)
    assert margin("n/a", 0, ">=") is None
    assert margin(float("nan"), 0, ">=") is None
    assert margin(True, 0, ">=") is None
    assert margin_text(-0.00012, 0, "m") == "-0.00012 m abs"
    assert margin_text(-0.154, 30.0, "A") == "-15%"


ZERO = [(-0.34, ">=", True), (-0.00012, ">=", True), (6, "<=", True), (0.28, ">=", False),
        (0.0, ">=", False), (-0.0, ">=", False), (0, "<=", False), (-3.0, "<=", False)]


@pytest.mark.parametrize("value,op,fails", ZERO)
def test_zero_limit_table_fails_exactly_when_negative(tmp_mini, value, op, fails):
    edit_claims(tmp_mini, lambda n: n.update({"CL-T": {"id": "CL-T", "type": "claim", "title": "t", "value": value,
                                                       "unit": "-", "limit": {"op": op, "value": 0}, "how": "x"}}))
    d = load_design(tmp_mini)
    assert status(d, "T9.claim.CL-T") == (FAIL if fails else SKIP)
    assert results(d)["CL-T"].margin_abs is True


def test_failing_margin_fails_t9(mini):
    assert status(mini, "T9.claim.CL-MASS-GATE") == FAIL
    assert status(mini, "T9.claim.CL-AERO-TW") == PASS


def test_claim_without_calc_is_proposed_not_pass(mini):
    assert status(mini, "T9.claim.CL-PROP-NOISE") == SKIP
    assert status(mini, "T9.claim.CL-STR-CLEAR") == SKIP
    r = results(mini)
    assert r["CL-PROP-NOISE"].status == "PROPOSED" and r["CL-STR-CLEAR"].status == "PROPOSED"


def test_proposed_claim_with_negative_margin_still_fails(tmp_mini):
    edit_claims(tmp_mini, lambda n: n["CL-STR-CLEAR"].update(value=-0.0003))
    assert status(load_design(tmp_mini), "T9.claim.CL-STR-CLEAR") == FAIL


def test_pdl_edit_flows_into_claim(tmp_mini):
    p = tmp_mini / "plane.yaml"
    text = p.read_bytes().decode()
    assert text.count("mass_g: 250") == 1
    p.write_bytes(text.replace("mass_g: 250", "mass_g: 100").encode())
    d = load_design(tmp_mini)
    r = results(d)
    assert r["CL-MASS-GATE"].status == "PASS"
    assert r["CL-MASS-GATE"].margin == pytest.approx(0.2)
    assert r["CL-AERO-TW"].value == pytest.approx(946 / 400)


def test_recorded_value_that_differs_is_stale(tmp_mini):
    edit_claims(tmp_mini, lambda n: n["CL-AERO-TW"].update(value=9.99))
    d = load_design(tmp_mini)
    r = results(d)["CL-AERO-TW"]
    assert r.status == "STALE"
    assert r.value == pytest.approx(1.72)
    assert status(d, "T9.claim.CL-AERO-TW") == WARN
    assert status(d, "T9.claim.CL-MASS-GATE") == FAIL


def test_unregistered_function_is_proposed_with_reason(tmp_mini):
    edit_claims(tmp_mini, lambda n: n["CALC-MASS"].update(function="no_such_calc"))
    d = load_design(tmp_mini)
    r = results(d)
    assert r["CL-MASS-GATE"].status == "PROPOSED" and "no_such_calc" in r["CL-MASS-GATE"].message
    assert status(d, "T9.claim.CL-MASS-GATE") == SKIP
    assert r["CL-AERO-TW"].status == "PROPOSED" and "CL-MASS-GATE" in r["CL-AERO-TW"].message


def test_calc_that_raises_is_fail(tmp_mini):
    edit_claims(tmp_mini, lambda n: n["P:env.total_thrust_g"].update(value="x"))
    r = results(load_design(tmp_mini))["CL-AERO-TW"]
    assert r.status == "FAIL" and "CALC-TW" in r.message


def test_unknown_reference_is_a_load_error(tmp_mini):
    edit_claims(tmp_mini, lambda n: n["CL-AERO-TW"].update(verifies=["R-NOPE"]))
    d = load_design(tmp_mini)
    with pytest.raises(ClaimGraphError, match="R-NOPE"):
        load_claims(d)
    rows = tier9_claims(d).results
    assert len(rows) == 1 and rows[0].check_id == "T9.claims.load" and rows[0].status == FAIL


def test_missing_pdl_value_is_a_load_error(tmp_mini):
    def fn(n):
        n["CALC-MASS"]["inputs"]["fuselage"] = "P:components[gone].mass_g"
    edit_claims(tmp_mini, fn)
    with pytest.raises(ClaimGraphError, match=r"components\[gone\]\.mass_g"):
        load_claims(load_design(tmp_mini))


def test_duplicate_id_unit_mismatch_cycle_and_shadow_are_load_errors(tmp_path):
    def fresh(i):
        dst = tmp_path / f"c{i}"
        shutil.copytree(MINI, dst)
        return dst

    d0 = fresh(0)
    doc = yaml.safe_load((d0 / "claims.yaml").read_text(encoding="utf-8"))
    doc["nodes"].append(copy.deepcopy(doc["nodes"][0]))
    (d0 / "claims.yaml").write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    with pytest.raises(ClaimGraphError, match="R-MASS"):
        load_claims(load_design(d0))

    d1 = fresh(1)
    edit_claims(d1, lambda n: n["CALC-MASS"]["units"].update(battery="kg"))
    with pytest.raises(ClaimGraphError, match="expects kg"):
        load_claims(load_design(d1))

    d2 = fresh(2)
    edit_claims(d2, lambda n: n["CALC-MASS"]["inputs"].update(fuselage="CL-MASS-GATE"))
    with pytest.raises(ClaimGraphError, match="cycle"):
        load_claims(load_design(d2))

    d3 = fresh(3)
    edit_claims(d3, lambda n: n.update({"P:requirements.mtow_g": {"id": "P:requirements.mtow_g", "type": "parameter",
                                                                   "title": "mtow", "value": 1}}))
    with pytest.raises(ClaimGraphError, match="shadows"):
        load_claims(load_design(d3))


@pytest.mark.parametrize("fn", ["../evil.py", "a/b", "C:\\x\\y", "mod.fn"])
def test_calc_function_must_be_a_name_not_a_path(tmp_mini, fn):
    edit_claims(tmp_mini, lambda n: n["CALC-MASS"].update(function=fn))
    with pytest.raises(ClaimGraphError):
        load_claims(load_design(tmp_mini))


def test_builtin_and_registered_fixture_calcs_both_resolve(mini):
    r = results(mini)
    assert r["CL-MASS-GATE"].value == 550
    assert r["CL-AERO-TW"].value == pytest.approx(1.72)
    with pytest.raises(ValueError):
        register_calcs({"sum_values": lambda **k: {}})
    register_calcs(_mod.CALCS)
    register_calcs(_mod.CALCS)
    for f in ("claims/calc.py", "claims/graph.py", "gates/claims.py"):
        assert "spec_from_file_location" not in (REPO_ROOT / "core" / "hangar" / f).read_text(encoding="utf-8")


def test_design_without_claims_yaml_has_no_tier9():
    d = load_design(EXAMPLE)
    assert claims_path(d) is None
    assert tier9_claims(d) is None
    assert tier9_claims(Design(copy.deepcopy(d.data), path=None)) is None


def test_validate_adds_tier_9_on_full_runs_only(mini):
    sc = validate(mini, max_tier=5)
    assert sc.tiers[-1].tier == 9 and sc.tiers[-1].name == "claims"
    assert sc.accepted is False
    assert all(t.tier != 9 for t in validate(mini, max_tier=3).tiers)
    assert all(t.tier != 9 for t in validate(load_design(EXAMPLE), max_tier=1).tiers)


def test_t9_criterion_resolves_in_standards(mini):
    assert all(r.criterion == "claims.yaml#recompute_rel_tol" for r in tier9_claims(mini).results)
    assert (REPO_ROOT / "standards" / "claims.yaml").exists()
    rt = load_claims_standards()["recompute_rel_tol"]
    assert rt["value"] and rt["rule"] and rt["source"]
    assert "claims" not in load_standards()


def test_claims_schema_is_valid_and_rejects_junk():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    v = Draft202012Validator(schema)
    doc = yaml.safe_load((MINI / "claims.yaml").read_text(encoding="utf-8"))
    assert not list(v.iter_errors(doc))

    def bad(node):
        return list(v.iter_errors({"schema": "claims/1", "nodes": [node]}))

    base = {"id": "CL-A", "type": "claim", "title": "t", "unit": "m", "value": 1}
    assert not bad(base)
    assert bad({**base, "extra": 1})
    assert bad({**base, "status": "PASS"})
    assert bad({**base, "calc": "CALC-A"})
    assert bad({"id": "CALC-A", "type": "calculation", "title": "t", "function": "f", "inputs": {}, "script": "x.py"})


def test_explain_chain_goes_down_to_sources():
    chain = call("claim.explain", path=str(MINI), claim_id="CL-AERO-TW").data["chain"]
    ids = [n["id"] for n in chain]
    assert ids[:2] == ["CL-AERO-TW", "CALC-TW"]
    for x in ("P:env.total_thrust_g", "SRC-MOTOR-DS", "ASM-STATIC-THRUST", "CL-MASS-GATE", "CALC-MASS",
              "P:components[center_body].mass_g"):
        assert x in ids
    assert chain[0]["depth"] == 0 and all(n["depth"] >= 0 for n in chain)


def test_claim_ops_list_and_check():
    assert {"claim.list", "claim.explain", "claim.check"} <= set(registry())
    r = call("claim.list", path=str(MINI))
    assert r.ok and len(r.data["claims"]) == 4
    assert r.data["counts"] == {"PASS": 1, "FAIL": 1, "PROPOSED": 2, "STALE": 0}
    c = call("claim.check", path=str(MINI))
    assert c.ok is False and c.exit_code == 1 and "error" not in c.data
    assert any(m.startswith("T9.claim.CL-MASS-GATE FAIL") for m in c.messages)
    assert c.data["uncovered_requirements"] == []


def test_claim_ops_bad_input(tmp_mini):
    def bad(r):
        assert r.ok is False and r.exit_code == 2 and r.data["error"] == "input"

    bad(call("claim.explain", path=str(MINI), claim_id="CL-NOPE"))
    bad(call("claim.check", path=str(EXAMPLE)))
    p = tmp_mini / "claims.yaml"
    doc = yaml.safe_load(p.read_text(encoding="utf-8"))
    doc["schema"] = "nope"
    p.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    bad(call("claim.list", path=str(tmp_mini)))


def test_check_reports_uncovered_requirement(tmp_mini):
    edit_claims(tmp_mini, lambda n: n.update({"R-EXTRA": {"id": "R-EXTRA", "type": "requirement", "title": "e", "text": "e"}}))
    assert call("claim.check", path=str(tmp_mini)).data["uncovered_requirements"] == ["R-EXTRA"]


def test_cli_claim_commands_json():
    runner = CliRunner()
    r = runner.invoke(cli, ["claim", "check", str(MINI), "--json"])
    assert r.exit_code == 1
    assert json.loads(r.output)["data"]["status"] == "FAIL"
    assert runner.invoke(cli, ["claim", "list", str(MINI), "--json"]).exit_code == 0
    assert runner.invoke(cli, ["claim", "explain", str(MINI), "CL-AERO-TW", "--json"]).exit_code == 0


@pytest.mark.skipif(not DBF_PROOFS.exists(), reason="DBF-Combined clone not present")
def test_concept_a_claims_import_roundtrip():
    files = sorted(DBF_PROOFS.glob("claims.*.json"))
    assert len(files) == 4
    count = sum(len(json.loads(f.read_text(encoding="utf-8"))["nodes"]) for f in files)
    g = import_proofs1(files)
    assert len(g.nodes) == count
    d = g.to_dict()
    assert len(d["nodes"]) == count
    assert not list(Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).iter_errors(d))
    assert all("script" not in n for n in d["nodes"])
    assert all("imported_from" in n for n in d["nodes"] if n["type"] == "calculation")
    res = g.recompute()
    assert len(res) == sum(1 for n in g.nodes.values() if n["type"] == "claim")
    for r in res:
        assert r.status in ("PROPOSED", "FAIL"), (r.id, r.status, r.message)
        if r.status == "FAIL":
            assert r.margin is not None and r.margin < 0


def test_import_proofs1_mini_fixture(tmp_path):
    g = import_proofs1([PROOFS1_MINI])
    calc = g.nodes["CALC-X"]
    assert "script" not in calc and calc["imported_from"] == {"script": "redesign/x/analysis.py"}
    assert all(n["defined_in"] == "claims.mini.json" for n in g.nodes.values())
    r = {x.id: x for x in g.recompute()}
    assert r["CL-X-A"].status == "PROPOSED" and "P:wing.span_m" in r["CL-X-A"].message
    assert r["CL-X-B"].status == "FAIL" and r["CL-X-B"].margin_abs is True
    with pytest.raises(ClaimGraphError):
        import_proofs1([PROOFS1_MINI, PROOFS1_MINI])
    doc = json.loads(PROOFS1_MINI.read_text(encoding="utf-8"))
    doc["schema"] = "proofs/2"
    other = tmp_path / "claims.bad.json"
    other.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(ClaimGraphError):
        import_proofs1([other])
    assert not list(Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).iter_errors(g.to_dict()))


def test_design_dir_calcs_py_is_never_imported(tmp_mini):
    (tmp_mini / "calcs.py").write_text(
        'raise RuntimeError("imported")\nCALCS = {"hover_tw": lambda **k: {"tw": 99}}\n', encoding="utf-8")
    d = load_design(tmp_mini)
    r = results(d)
    tier9_claims(d)
    assert r["CL-AERO-TW"].value == pytest.approx(1.72)
    assert call("claim.check", path=str(tmp_mini)).data.get("error") != "internal"


def test_calc_over_stored_only_claim_is_proposed(tmp_mini):
    def fn(n):
        n["CALC-DBL"] = {"id": "CALC-DBL", "type": "calculation", "title": "d", "function": "twice",
                         "inputs": {"x": "CL-STR-CLEAR"}}
        n["CL-DBL"] = {"id": "CL-DBL", "type": "claim", "title": "d", "calc": "CALC-DBL", "output": "y", "unit": "m",
                       "limit": {"op": ">=", "value": 0}, "how": "x"}
    edit_claims(tmp_mini, fn)
    register_calcs({"twice": _twice})
    d = load_design(tmp_mini)
    r = results(d)
    assert r["CL-STR-CLEAR"].status == "PROPOSED"
    assert r["CL-DBL"].status == "PROPOSED" and "CL-STR-CLEAR" in r["CL-DBL"].message
    assert status(d, "T9.claim.CL-DBL") == SKIP


def _twice(x):
    return {"y": 2 * x}


def test_design_set_flows_into_claim(tmp_path):
    import difflib
    dst = tmp_path / "claims-mini"
    shutil.copytree(MINI, dst)
    register_calcs(_mod.CALCS)
    d0 = load_design(dst)
    before = results(d0)["CL-MASS-GATE"]
    assert before.status == "FAIL" and before.margin == pytest.approx(-0.1)
    assert status(d0, "T9.claim.CL-MASS-GATE") == FAIL
    plane = dst / "plane.yaml"
    original = plane.read_bytes().decode("utf-8")
    r = call("design.set", path=str(dst), key="components[battery].mass_g", value="150", why="T5 design.set flows into claim")
    assert r.exit_code == 0
    edited = plane.read_bytes().decode("utf-8")
    a, b = original.splitlines(keepends=True), edited.splitlines(keepends=True)
    assert len(a) == len(b)
    assert sum(x != y for x, y in zip(a, b)) == 1
    assert "".join(difflib.unified_diff(a, b, n=0))
    d1 = load_design(dst)
    after = results(d1)["CL-MASS-GATE"]
    assert after.margin != before.margin
    assert after.margin == pytest.approx(0.1)
    assert after.status == "PASS"
    assert status(d1, "T9.claim.CL-MASS-GATE") == PASS
