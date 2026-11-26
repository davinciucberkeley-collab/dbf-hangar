import copy

import numpy as np
import pytest
import trimesh
from pathlib import Path

from hangar.checks import validate
from hangar.design import Design, load_design
from hangar.export import export_glb
from hangar.index import mechanism_sweeps, parts_json
from hangar.visuals import visual_nodes

FIX = Path(__file__).parent / "fixtures" / "four-bar"


def with_display(**kw):
    data = copy.deepcopy(load_design(FIX).data)
    data["display"] = kw
    return Design(data=data, path=FIX / "plane.yaml")


def test_clevis_node_hand_bounds():
    nodes = {v.name: v for v in visual_nodes(with_display(clevises=True)) if v.kind == "clevis"}
    assert set(nodes) == {"clevis-elevator-drive-driver", "clevis-elevator-drive-follower"}
    drv = nodes["clevis-elevator-drive-driver"]
    fol = nodes["clevis-elevator-drive-follower"]
    assert np.allclose(drv.mesh.bounds, [[19.4, 4.5, -17.75], [28.0, 7.5, -12.75]], atol=0.02), drv.mesh.bounds
    assert np.allclose(fol.mesh.bounds, [[67.0, 3.5, -16.75], [75.6, 8.5, -13.75]], atol=0.02), fol.mesh.bounds
    assert len(drv.mesh.split(only_watertight=False)) == 2
    assert len(fol.mesh.split(only_watertight=False)) == 2
    assert drv.point_mm == [20, 6, -15.25]
    assert fol.point_mm == [75, 6, -15.25]


def test_clevis_aliases_hand_values():
    from hangar.visuals import clevis_aliases
    assert clevis_aliases(with_display(clevises=True)) == [
        ("clevis-elevator-drive-driver", "rod", "elevator-drive"),
        ("clevis-elevator-drive-follower", "rod", "elevator-drive")]
    assert clevis_aliases(with_display()) == []
    assert clevis_aliases(with_display(clevises=False)) == []


def test_pin_component_hidden_in_scene_only():
    from hangar.export import to_scene
    from hangar.visuals import hidden_visual_components
    on, off = with_display(clevises=True), with_display()
    s_on, s_off = to_scene(on), to_scene(off)
    assert "pin" not in s_on.geometry
    assert {"clevis-elevator-drive-driver", "clevis-elevator-drive-follower"} <= set(s_on.geometry)
    assert "pin" in s_off.geometry
    assert not [n for n in s_off.geometry if n.startswith("clevis-")]
    assert hidden_visual_components(on) == {"pin"}
    assert hidden_visual_components(off) == set()
    assert sum(c["mass_g"] for c in on.components) == sum(c["mass_g"] for c in off.components)
    assert [c["id"] for c in on.components] == [c["id"] for c in off.components]


def test_off_by_default():
    assert visual_nodes(load_design(FIX)) == []
    assert not [v for v in visual_nodes(with_display()) if v.kind == "clevis"]
    assert not [v for v in visual_nodes(with_display(clevises=False)) if v.kind == "clevis"]


def test_skips_what_it_cannot_draw():
    data = copy.deepcopy(load_design(FIX).data)
    for m in data["mechanisms"]:
        m.pop("link", None)
        m.pop("kinematics", None)
    d = Design(data=data, path=FIX / "plane.yaml")
    d.data["display"] = {"clevises": True}
    assert not [v for v in visual_nodes(d) if v.kind == "clevis"]


def test_glb_and_parts_json(tmp_path):
    d = with_display(clevises=True)
    export_glb(d, tmp_path / "c.glb")
    scene = trimesh.load(tmp_path / "c.glb")
    names = set(scene.graph.nodes_geometry)
    for n in ("stab", "elevator", "rod", "clevis-elevator-drive-driver", "clevis-elevator-drive-follower"):
        assert n in names
    parts = parts_json(d)["parts"][-2:]
    assert [p["id"] for p in parts] == ["clevis-elevator-drive-driver", "clevis-elevator-drive-follower"]
    for p in parts:
        assert p["type"] == "clevis"
        assert p["visual_only"] is True
        assert p["parent"] is None


def test_physics_moves_the_clevises():
    m = mechanism_sweeps(with_display(clevises=True))["mechanisms"][0]
    step10 = next(s for s in m["steps"] if s["input_deg"] == 10)
    assert step10["transforms"]["clevis-elevator-drive-driver"] == step10["transforms"]["rod"]
    assert step10["transforms"]["clevis-elevator-drive-follower"] == step10["transforms"]["rod"]
    step0 = next(s for s in m["steps"] if s["input_deg"] == 0)
    assert "clevis-elevator-drive-driver" not in step0["transforms"]
    assert "clevis-elevator-drive-follower" not in step0["transforms"]
    plain = mechanism_sweeps(Design(data=copy.deepcopy(load_design(FIX).data), path=FIX / "plane.yaml"))
    for mech in plain["mechanisms"]:
        for s in mech["steps"]:
            assert not [k for k in s["transforms"] if k.startswith("clevis")]


def test_nothing_else_changes():
    plain = Design(data=copy.deepcopy(load_design(FIX).data), path=FIX / "plane.yaml")
    rows = lambda d: [(r.check_id, r.status, r.message) for t in validate(d).tiers for r in t.results]
    assert rows(with_display(clevises=True)) == rows(plain)


def test_schema_and_version():
    data = copy.deepcopy(load_design(FIX).data)
    data["schema_version"] = "1.2"
    data["display"] = {"clevises": True}
    d = Design(data=data, path=FIX / "plane.yaml")
    res = [r for t in validate(d).tiers for r in t.results]
    assert any(r.check_id == "T0.version" and r.status == "FAIL" and "display" in r.message for r in res)

    data = copy.deepcopy(load_design(FIX).data)
    data["display"] = {"clevises": "yes"}
    res = [r for t in validate(Design(data=data, path=FIX / "plane.yaml")).tiers for r in t.results]
    assert any(r.check_id == "T0.schema" and r.status == "FAIL" for r in res)

    data = copy.deepcopy(load_design(FIX).data)
    data["display"] = {"foo": True}
    res = [r for t in validate(Design(data=data, path=FIX / "plane.yaml")).tiers for r in t.results]
    assert any(r.check_id == "T0.schema" and r.status == "FAIL" for r in res)

    text = (Path(__file__).parent.parent / "docs" / "pdl" / "reference.md").read_text(encoding="utf-8")
    assert "clevises" in text
