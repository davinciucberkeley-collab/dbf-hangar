"""U4.29 / T129: parameter expressions in positions, joint locations and pivots; design set reports new interference."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import trimesh
import yaml

from hangar.design import DESIGNS_DIR, REPO_ROOT, load_design, load_standards
from hangar.geom import params as params_mod
from hangar.geom.params import ExprError, evaluate, find_references, resolve_references
from hangar.checks import tier0_schema
from hangar.ops import call
from testutil import LEGACY_DESIGNS

GEN = Path(__file__).parent / "fixtures" / "pdl-gen"
REPO = Path(__file__).resolve().parent.parent


def _boxes(tmp_path, x=20, cz=40, joint_x=10, loc="10") -> Path:
    d = tmp_path / "d"
    (d / "meshes").mkdir(parents=True)
    for n in "abc":
        trimesh.creation.box((20, 20, 20)).export(str(d / "meshes" / f"{n}.stl"))
    comps = [{"id": n, "type": "other", "geometry": {"mesh": {"file": f"meshes/{n}.stl"}},
              "position": pos, "mass_g": 1}
             for n, pos in (("a", [0, 0, 0]), ("b", ["$x", 0, 0]), ("c", [0, 0, "$cz"]))]
    lx = joint_x if loc == "10" else loc
    doc = {"schema_version": "1.2", "id": "boxes", "name": "Boxes", "status": "concept",
           "morphology": {"lift": "flying-wing", "vtol_method": "none"},
           "parameters": {"x": x, "cz": cz}, "root": "a", "components": comps,
           "attachments": [{"id": "j-ab", "parent": "a", "child": "b", "method": "glued",
                            "location": [lx, 0, 0], "rated_load_n": 1}]}
    (d / "plane.yaml").write_text(yaml.safe_dump(doc, sort_keys=False))
    return d


def _edit(d, fn):
    p = d / "plane.yaml"
    doc = yaml.safe_load(p.read_text())
    fn(doc)
    p.write_text(yaml.safe_dump(doc, sort_keys=False))


@pytest.mark.parametrize("expr,params,expected", [
    ("1+2*3", {}, 7), ("(1+2)*3", {}, 9), ("-2*-3", {}, 6), ("--3", {}, 3), ("2-3-4", {}, -5),
    ("8/2/2", {}, 2), ("7/2", {}, 3.5), (".5+.5", {}, 1), ("1.5e2", {}, 150), ("0.1+0.2", {}, 0.3),
    ("450 - $s/2", {"s": 900}, 0), ("450 - $s/2", {"s": 820}, 40), ("$s/2 - 450", {"s": 820}, -40),
    ("-($s/2 - 70)", {"s": 900}, -380), ("$s/2 - 450 + 128.599", {"s": 900}, 128.599),
    ("450 - $s/2 + 128.599", {"s": 820}, 168.599), (" " * 199 + "1", {}, 1),
])
def test_evaluate_values(expr, params, expected):
    got = evaluate(expr, params)
    assert got == expected and type(got) is type(expected)


@pytest.mark.parametrize("expr,params,kind", [
    ("$nope", {}, "name"), ("$s", {"s": "x"}, "name"), ("$s", {"s": True}, "name"),
    ("2**3", {}, "syntax"), ("__import__('os')", {}, "syntax"), ("span", {}, "syntax"),
    ("abs(1)", {}, "syntax"), ("", {}, "syntax"), ("1 +", {}, "syntax"), ("(1", {}, "syntax"),
    ("1)", {}, "syntax"), ("$", {}, "syntax"), ("$S", {}, "syntax"), ("+1", {}, "syntax"),
    ("1//2", {}, "syntax"), ("1/0", {}, "zero"), ("1/($s-900)", {"s": 900}, "zero"),
    ("1" + "+0" * 100, {}, "syntax"), ("1e999", {}, "range"),
])
def test_evaluate_refusals(expr, params, kind):
    with pytest.raises(ExprError) as ei:
        evaluate(expr, params)
    assert ei.value.kind == kind
    if expr == "$nope":
        assert "nope" in str(ei.value)


def test_parser_source_has_no_dynamic_execution():
    src = Path(params_mod.__file__).read_text()
    for word in ("eval(", "exec(", "compile(", "import ast"):
        assert word not in src


def test_whole_string_reference_unchanged():
    out = resolve_references({"parameters": {"a": 450, "b": 2.5, "t": True},
                              "components": [{"id": "x", "position": ["$a", "$b", "$t"]}]})
    pos = out["components"][0]["position"]
    assert pos == [450, 2.5, "$t"]
    assert [type(v) for v in pos] == [int, float, str]


def _pure():
    return {"parameters": {"a": 1, "b": 2},
            "components": [{"id": "x", "position": [0, "$a + $b*2", "$a - $a"],
                            "geometry": {"params": {"length": "2 * $b"}}}],
            "attachments": [{"id": "j1", "location": [0, "$a + 1", 0], "articulation": {"pivot": [1, "$b", 0]}}]}


def test_find_references_sees_expressions_and_attachments():
    data = _pure()
    assert find_references(data) == [
        ("x", "geometry.params.length", "b"), ("x", "position[1]", "a"), ("x", "position[1]", "b"),
        ("x", "position[2]", "a"), ("attachments[j1]", "location[1]", "a"),
        ("attachments[j1]", "articulation.pivot[1]", "b")]
    out = resolve_references(data)
    c, a = out["components"][0], out["attachments"][0]
    assert c["position"] == [0, 5, 0] and c["geometry"]["params"]["length"] == 4
    assert a["location"] == [0, 2, 0] and a["articulation"]["pivot"] == [1, 2, 0]
    assert data["components"][0]["position"][1] == "$a + $b*2"        # input not mutated
    data["attachments"][0]["location"][1] = "1 +"
    assert resolve_references(data)["attachments"][0]["location"][1] == "1 +"


def _t0(d):
    return [r for r in tier0_schema(load_design(d)).results if r.check_id == "T0.parameters"]


def _fails(d):
    return [r for r in _t0(d) if r.status == "FAIL"]


def test_t0_parameters_names_in_expressions(tmp_path):
    d = _boxes(tmp_path)
    assert _fails(d) == [] and len([r for r in _t0(d) if r.status == "PASS"]) == 1

    def setpos(v):
        def f(doc):
            doc["components"][1]["position"] = [v, 0, 0]
        return f

    _edit(d, setpos("$x + $nope"))
    f = _fails(d)
    assert len(f) == 1 and f[0].message == "component b: position[0] references $nope, which is not in parameters"
    _edit(d, setpos("$x +"))
    f = _fails(d)
    assert len(f) == 1 and f[0].message.startswith("component b: position[0]: expression '$x +'")
    _edit(d, setpos("$x / 0"))
    f = _fails(d)
    assert len(f) == 1 and f[0].message.startswith("component b: position[0]: expression '$x / 0'") \
        and "zero" in f[0].message
    _edit(d, setpos("$x"))
    _edit(d, lambda doc: doc["attachments"][0].__setitem__("location", [0, "$nope", 0]))
    f = _fails(d)
    assert len(f) == 1 and f[0].message == "attachment j-ab: location[1] references $nope, which is not in parameters"
    assert f[0].data == {"attachment": "j-ab"}


def test_only_argument_filters(tmp_path):
    from hangar.checks import interference_rows
    d = _boxes(tmp_path, cz=15)
    std = load_standards()
    rows = interference_rows(load_design(d), std)
    inter = [r for r in rows if r.check_id == "T1.interference"]
    assert len(inter) == 1 and inter[0].data["pair"] == ["a", "c"]
    assert abs(inter[0].data["volume_mm3"] - 2000) < 20
    assert not [r for r in interference_rows(load_design(d), std, {"b"}) if r.check_id == "T1.interference"]
    for only in ({"c"}, {"a"}):
        got = [r for r in interference_rows(load_design(d), std, only) if r.check_id == "T1.interference"]
        assert len(got) == 1 and got[0].data["pair"] == ["a", "c"]
    assert interference_rows(load_design(d), std, set()) == []


def _set(d, key, value):
    return call("design.set", path=str(d), key=key, value=value, why="test")


def test_set_reports_a_new_collision_and_writes_it(tmp_path):
    d = _boxes(tmp_path)
    r = call("design.set", path=str(d), key="parameters.cz", value="15", why="push c into a")
    assert r.ok
    assert yaml.safe_load((d / "plane.yaml").read_text())["parameters"]["cz"] == 15
    i = r.data["interference"]
    assert i["moved"] == ["c"] and i["joints"] == [] and i["cleared"] == []
    assert len(i["new"]) == 1 and i["new"][0]["check_id"] == "T1.interference"
    assert i["new"][0]["key"] == ["a", "c"] and "a and c overlap" in i["new"][0]["message"]
    assert any(m.startswith("new interference:") and "a and c" in m for m in r.messages)
    assert any(m.startswith("moved 1 part(s), 0 joint(s); interference: 1 new, 0 cleared") for m in r.messages)


def test_set_reports_a_part_moved_without_its_joint(tmp_path):
    d = _boxes(tmp_path)
    r = _set(d, "parameters.x", "40")
    assert r.ok
    i = r.data["interference"]
    assert i["moved"] == ["b"]
    assert len(i["new"]) == 1 and i["new"][0]["check_id"] == "T1.attachment_contact"
    assert i["new"][0]["key"] == "j-ab" and "20.0 mm apart" in i["new"][0]["message"]


def test_set_reports_cleared_rows(tmp_path):
    d = _boxes(tmp_path, x=40)
    r = _set(d, "parameters.x", "20")
    assert r.ok
    i = r.data["interference"]
    assert i["new"] == [] and len(i["cleared"]) == 1 and i["cleared"][0]["key"] == "j-ab"


def test_set_without_a_geometry_change_has_no_interference_key(tmp_path):
    d = _boxes(tmp_path)
    r = _set(d, "components[a].mass_g", "2")
    assert r.ok and "interference" not in r.data


def test_set_refuses_a_new_bad_expression(tmp_path):
    d = _boxes(tmp_path)
    before = (d / "plane.yaml").read_bytes()
    for v in ("$cz / 0", "$cz +", "$nope * 2"):
        r = _set(d, "components[c].position[2]", v)
        assert not r.ok
        assert (d / "plane.yaml").read_bytes() == before
    assert _set(d, "components[c].position[2]", "$cz - 40 + 40").ok


def test_expression_in_a_joint_location_follows_the_part(tmp_path):
    d = _boxes(tmp_path, x=20)
    _edit(d, lambda doc: doc["attachments"][0]["location"].__setitem__(0, "$x - 10"))
    assert load_design(d).data["attachments"][0]["location"] == [10, 0, 0]
    r = _set(d, "parameters.x", "30")
    assert r.ok
    assert load_design(d).data["attachments"][0]["location"] == [20, 0, 0]
    i = r.data["interference"]
    assert i["moved"] == ["b"] and i["joints"] == ["j-ab"]
    assert len(i["new"]) == 1 and i["new"][0]["key"] == "j-ab"


def test_converted_concept_a_param_resolves_identically_at_900(tmp_path):
    orig = DESIGNS_DIR / "concept-a-param"
    d = tmp_path / "p"
    shutil.copytree(orig, d)
    doc = yaml.safe_load((d / "plane.yaml").read_text())
    comps = {c["id"]: c for c in doc["components"]}
    atts = {a["id"]: a for a in doc["attachments"]}
    comps["avn-005"]["position"][1] = "450 - $span_mm/2"
    comps["wng-006-r"]["position"][1] = "$span_mm/2 - 450"
    atts["E-WNG-10"]["location"][1] = "$span_mm/2 - 450 + 128.599"
    atts["E-WNG-10"]["articulation"]["pivot"][1] = "$span_mm/2 - 450 + 195"
    comps["fin-001-l"]["geometry"]["params"]["center"][1] = "-($span_mm/2 - 70)"
    (d / "plane.yaml").write_text(yaml.safe_dump(doc, sort_keys=False))
    a, b = load_design(orig), load_design(d)
    assert a.data["components"] == b.data["components"]
    assert a.data["attachments"] == b.data["attachments"]
    r = _set(d, "parameters.span_mm", "820")
    assert r.ok
    n = load_design(d).data
    comps = {c["id"]: c for c in n["components"]}
    atts = {x["id"]: x for x in n["attachments"]}
    assert comps["avn-005"]["position"] == [0, 40, 0]
    assert comps["wng-006-r"]["position"] == [0, -40, 0]
    assert atts["E-WNG-10"]["location"] == [183.717, 88.599, 0.18]
    assert atts["E-WNG-10"]["articulation"]["pivot"] == [183.75, 155, 0.295]
    assert comps["fin-001-l"]["geometry"]["params"]["center"][1] == -340


def test_designs_without_expressions_resolve_unchanged():
    n = 0
    for name in LEGACY_DESIGNS:
        folder = DESIGNS_DIR / name
        p = folder / "plane.yaml"
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8")
        if "parameters" in yaml.safe_load(text):
            continue
        assert load_design(folder).data == yaml.safe_load(text), folder.name
        n += 1
    assert n >= 1
    if DESIGNS_DIR == REPO_ROOT / "designs":
        assert n == len(LEGACY_DESIGNS)
    data = load_design(GEN).data
    rod = next(c for c in data["components"] if c["id"] == "rod")
    assert rod["geometry"]["params"]["length"] == 100
