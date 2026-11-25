"""U4.37-2: design.apply runs a batch of edits with one regeneration pass."""
from __future__ import annotations

import shutil

import pytest
import yaml

from hangar import design as design_mod
from hangar.ops import call, registry

EXAMPLE_DIR = design_mod.DESIGNS_DIR / "example-tailsitter-wing"

ATTACH = {"id": "probe-mount", "parent": "center_body", "child": "probe", "method": "glued",
          "location": [10, 0, 0], "embed_ok": True, "rated_load_n": 5}
COMP = {"id": "probe", "type": "other", "geometry": {"point_mass": {}}, "position": [10, 0, 0], "mass_g": 2}
EDITS = [
    {"set": "components[center_body].mass_g", "value": 125},
    {"append": "attachments", "value": ATTACH},
    {"append": "components", "value": COMP},
    {"remove": "attachments[fc-mount]"},
    {"add": "flight.air_density_kgm3", "value": 1.2},
]


@pytest.fixture
def pair(tmp_path):
    a, b = tmp_path / "a" / "ex", tmp_path / "b" / "ex"
    shutil.copytree(EXAMPLE_DIR, a)
    shutil.copytree(EXAMPLE_DIR, b)
    return a, b


def _file(tmp_path, edits, name="edits.yaml"):
    f = tmp_path / name
    f.write_text(yaml.safe_dump(edits, sort_keys=False), encoding="utf-8")
    return f


def _singles(b):
    p = str(b)
    for r in (call("design.set", path=p, key="components[center_body].mass_g", value="125", why="t"),
              call("design.add", path=p, key="components", value="{id: probe, type: other, geometry: {point_mass: {}}, position: [10, 0, 0], mass_g: 2}", why="t"),
              call("design.add", path=p, key="attachments", value="{id: probe-mount, parent: center_body, child: probe, method: glued, location: [10, 0, 0], embed_ok: true, rated_load_n: 5}", why="t"),
              call("design.set", path=p, key="attachments[fc-mount]", kind="remove", why="t"),
              call("design.set", path=p, key="flight.air_density_kgm3", value="1.2", kind="add", why="t")):
        assert r.ok, r.messages


def test_batch_equals_single_edits_byte_for_byte(pair, tmp_path):
    a, b = pair
    r = call("design.apply", path=str(a), edits=_file(tmp_path, EDITS), why="t")
    assert r.ok, r.messages
    _singles(b)
    assert (a / "plane.yaml").read_bytes() == (b / "plane.yaml").read_bytes()


def test_one_regeneration_pass(pair, tmp_path, monkeypatch):
    import hangar.geom.resolve as res
    calls = []
    real = res.regeneration_report

    def wrap(*args, **kw):
        calls.append(1)
        return real(*args, **kw)
    monkeypatch.setattr(res, "regeneration_report", wrap)
    a, b = pair
    assert call("design.apply", path=str(a), edits=_file(tmp_path, EDITS), why="t").ok
    assert len(calls) == 1
    calls.clear()
    _singles(b)
    assert len(calls) == 5


def test_one_compact_changelog_entry(pair, tmp_path):
    a, b = pair
    f = _file(tmp_path, EDITS, "my-edits.yaml")
    assert call("design.apply", path=str(a), edits=f, why="t").ok
    _singles(b)
    log = yaml.safe_load((a / "CHANGELOG.yaml").read_text(encoding="utf-8"))
    assert len(log) == 1
    e = log[0]
    assert e["kind"] == "batch" and e["count"] == 5 and e["file"] == "my-edits.yaml"
    assert e["keys"] == ["components[center_body].mass_g", "attachments", "components", "attachments[fc-mount]", "flight.air_density_kgm3"]
    assert len(yaml.safe_load((b / "CHANGELOG.yaml").read_text(encoding="utf-8"))) == 5


def _snap(d):
    log = d / "CHANGELOG.yaml"
    return (d / "plane.yaml").read_bytes(), log.read_bytes() if log.exists() else None


def test_atomic_on_error(pair, tmp_path):
    a, _ = pair
    before = _snap(a)
    edits = [EDITS[0], EDITS[3], {"append": "components", "value": {"id": "wing", "type": "other"}}]
    r = call("design.apply", path=str(a), edits=_file(tmp_path, edits), why="t")
    assert r.ok is False
    assert r.messages[0].startswith("edit 3:") and "already exists" in r.messages[0]
    assert _snap(a) == before


def test_shape_errors(pair, tmp_path):
    a, _ = pair
    before = _snap(a)
    cases = [([{"set": "x", "add": "y", "value": 1}], None),
             ([{"set": "components[wing].mass_g"}], None),
             ([{"frobnicate": "x", "value": 1}], None),
             ({"set": "components[wing].mass_g", "value": 1}, False),
             ([{"set": "components[wing].mass_g", "value": {"a": 1}}], "scalar or a list")]
    for edits, frag in cases:
        r = call("design.apply", path=str(a), edits=_file(tmp_path, edits), why="t")
        assert r.ok is False
        if frag is not False:
            assert r.messages[0].startswith("edit 1:")
        if frag:
            assert frag in r.messages[0]
        assert _snap(a) == before


def test_unchanged_batch_writes_nothing(pair, tmp_path):
    a, _ = pair
    cur = yaml.safe_load((a / "plane.yaml").read_text(encoding="utf-8"))
    wing = next(c for c in cur["components"] if c["id"] == "wing")
    before = _snap(a)
    r = call("design.apply", path=str(a), edits=_file(tmp_path, [{"set": "components[wing].mass_g", "value": wing["mass_g"]}]), why="t")
    assert r.ok and r.data["count"] == 0
    assert _snap(a) == before


def test_schema_error_refused(pair, tmp_path):
    a, _ = pair
    before = _snap(a)
    r = call("design.apply", path=str(a), edits=_file(tmp_path, [{"set": "components[wing].mass_g", "value": -5}]), why="t")
    assert r.ok is False
    assert _snap(a) == before


def test_registered():
    assert "design.apply" in registry()
