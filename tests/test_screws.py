import copy
from pathlib import Path

import numpy as np
import pytest
import trimesh

from hangar.checks import validate
from hangar.design import Design, load_design
from hangar.export import export_glb
from hangar.index import parts_json
from hangar.visuals import visual_nodes

FIX = Path(__file__).parent / "fixtures" / "four-bar"
REPO = Path(__file__).resolve().parents[1]


def made(conn="CT-SERVO-SPLINE", **display):
    data = copy.deepcopy(load_design(FIX).data)
    a = next(x for x in data["attachments"] if x["id"] == "servo-arm")
    a["connection"] = conn
    data["display"] = display
    return Design(data=data, path=FIX / "plane.yaml")


def screw_nodes(d):
    return [v for v in visual_nodes(d) if v.kind == "screw"]


def test_screw_head_hand_bounds():
    nodes = screw_nodes(made(screw_heads=True))
    assert len(nodes) == 1
    node = nodes[0]
    assert node.name == "screws"
    assert np.allclose(node.mesh.bounds, [[18.2, -1.8, -14.5], [21.8, 1.8, -12.5]], atol=0.03), node.mesh.bounds
    assert len(node.mesh.split(only_watertight=False)) == 1
    assert node.point_mm == pytest.approx([20, 0, -14.5], abs=1e-6)


def test_only_bolted_with_a_screw_size():
    assert not screw_nodes(made("CT-EPOXY", screw_heads=True))
    d = made(screw_heads=True)
    for a in d.data["attachments"]:
        if a["id"] == "servo-arm":
            a["method"] = "glued"
    assert not screw_nodes(d)
    assert not screw_nodes(made("CT-NOPE", screw_heads=True))


def test_off_by_default():
    assert not screw_nodes(made(screw_heads=False))
    d = made()
    d.data.pop("display", None)
    assert not screw_nodes(d)


def test_m3_size():
    node = screw_nodes(made("CT-M3-SHCS-NYLOC", screw_heads=True))[0]
    assert np.allclose(node.mesh.bounds, [[17.3, -2.7, -14.5], [22.7, 2.7, -11.5]], atol=0.03), node.mesh.bounds


def test_glb_and_parts_json(tmp_path):
    d = made(screw_heads=True)
    export_glb(d, tmp_path / "s.glb")
    scene = trimesh.load(tmp_path / "s.glb")
    assert "screws" in set(scene.graph.nodes_geometry)
    last = parts_json(d)["parts"][-1]
    assert last["id"] == "screws"
    assert last["type"] == "screw"
    assert last["visual_only"] is True


def test_nothing_else_changes():
    def rows(d):
        card = validate(d)
        return [(r.check_id, r.status, r.message) for t in card.tiers for r in t.results]
    assert rows(made(screw_heads=True)) == rows(made(screw_heads=False))


def test_schema():
    d = made(screw_heads="yes")
    rows = [r for t in validate(d).tiers for r in t.results if r.check_id == "T0.schema"]
    assert rows and all(r.status == "FAIL" for r in rows)
    assert "screw_heads" in (REPO / "docs" / "pdl" / "reference.md").read_text(encoding="utf-8")


def test_concept_a_unchanged():
    assert visual_nodes(load_design(REPO / "designs" / "concept-a")) == []
