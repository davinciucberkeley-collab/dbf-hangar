import copy

import numpy as np
import pytest
import trimesh
from pathlib import Path

from hangar.checks import validate
from hangar.design import Design, load_design
from hangar.export import export_glb
from hangar.geom import library
from hangar.geom.wires import WireError, curve_points, port_point, tube_mesh
from hangar.visuals import visual_nodes

FIX = Path(__file__).parent / "fixtures" / "wires"
REPO = Path(__file__).parent.parent


def rows(data):
    d = Design(data=copy.deepcopy(data), path=FIX / "plane.yaml")
    return {r.check_id: r for t in validate(d).tiers for r in t.results}


def data():
    return copy.deepcopy(load_design(FIX).data)


def test_curve_points():
    c = curve_points([[0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0]])
    assert len(c) == 25
    for i, p in zip((0, 8, 16, 24), ([0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0])):
        assert c[i] == pytest.approx(p, abs=1e-9)
    assert c[12] == pytest.approx([11.25, 5.0, 0], abs=1e-9)
    s = curve_points([[0, 0, 0], [0, 0, 10]])
    assert len(s) == 9
    assert s[:, 2] == pytest.approx([1.25 * k for k in range(9)], abs=1e-9)


def test_tube_mesh_straight():
    pts = curve_points([[0, 0, 0], [0, 0, 10]])
    m = tube_mesh(pts, 1.5)
    assert len(m.vertices) == 110 and len(m.faces) == 216
    assert m.is_watertight
    assert abs(m.volume) == pytest.approx(16.875, abs=1e-6)
    for i in range(9):
        ring = m.vertices[12 * i: 12 * i + 12]
        assert np.linalg.norm(ring - pts[i], axis=1) == pytest.approx(0.75, abs=1e-9)
        assert (ring - pts[i]) @ np.array([0, 0, 1.0]) == pytest.approx(0, abs=1e-9)


def test_port_points():
    d = load_design(FIX)
    p, v = port_point(d, "servo", "signal")
    assert p == pytest.approx([88.5, 50, -8], abs=1e-9) and v == pytest.approx([-1, 0, 0], abs=1e-9)
    p, v = port_point(d, "rx", "ch1")
    assert p == pytest.approx([36.07, -6, 0], abs=1e-9) and v == pytest.approx([1, 0, 0], abs=1e-9)
    dd = data()
    next(c for c in dd["components"] if c["id"] == "servo")["rotation_deg"] = [0, 0, 90]
    d2 = Design(data=dd, path=FIX / "plane.yaml")
    p, v = port_point(d2, "servo", "signal")
    assert p == pytest.approx([100, 38.5, -8], abs=1e-9) and v == pytest.approx([0, -1, 0], abs=1e-9)
    with pytest.raises(WireError, match="library part"):
        port_point(d, "body", "x")
    with pytest.raises(WireError) as e:
        port_point(d, "servo", "nope")
    assert "nope" in str(e.value) and "signal" in str(e.value)


def test_t7_routed_row_passes():
    r = rows(data())["T7.wiring.w1"]
    assert r.status == "PASS", r.message
    assert "routed wire 109 mm through 2 waypoint(s)" in r.message
    assert r.data["length_mm"] == pytest.approx(108.9985, abs=0.06)


def test_t7_leaves_the_envelope():
    dd = data()
    dd["wiring"]["harnesses"][0]["waypoints"][1] = [46.07, 500, 0]
    r = rows(dd)["T7.wiring.w1"]
    assert r.status in ("FAIL", "WARN")
    assert "leaves the envelopes" in r.message


def test_t7_bad_port_and_collision():
    dd = data()
    dd["wiring"]["harnesses"][0]["to_port"] = "nope"
    r = rows(dd)["T7.wiring.w1"]
    assert r.status in ("FAIL", "WARN") and "nope" in r.message
    dd = data()
    dd["components"].append({"id": "wire-w1", "type": "other", "geometry": {"box": {"size": [1, 1, 1]}},
                             "position": [100, 0, 0], "mass_g": 1, "manufacturing": {"method": "foamboard"}})
    dd["attachments"].append({"id": "body-wire-w1", "parent": "body", "child": "wire-w1", "method": "glued",
                              "location": [100, 0, 0], "embed_ok": True, "rated_load_n": 1})
    r = rows(dd)["T7.wiring.w1"]
    assert r.status in ("FAIL", "WARN") and "wire-w1 is also a component id" in r.message


def test_glb_has_the_wire_node(tmp_path):
    d = load_design(FIX)
    export_glb(d, tmp_path / "w.glb")
    scene = trimesh.load(tmp_path / "w.glb")
    names = set(scene.graph.nodes_geometry)
    assert {"body", "rx", "servo", "wire-w1"} <= names
    assert len([n for n in names if n.startswith("wire-")]) == 1
    g = scene.geometry[scene.graph["wire-w1"][1]]
    assert len(g.vertices) == 302 and len(g.faces) == 600
    lo, hi = g.bounds
    assert lo[0] >= -0.05 and hi[0] <= 0.25
    assert lo[1] >= -0.03 and hi[1] <= 0.03
    assert lo[2] >= -0.06 and hi[2] <= 0.06
    vn = visual_nodes(d)
    assert len(vn) == 1 and vn[0].kind == "wire"


def test_designs_without_routes_are_untouched(tmp_path):
    d = load_design(REPO / "designs" / "example-tailsitter-wing")
    assert visual_nodes(d) == []
    export_glb(d, tmp_path / "t.glb")
    scene = trimesh.load(tmp_path / "t.glb")
    assert not [n for n in scene.graph.nodes_geometry if n.startswith("wire-")]


def test_parts_json_lists_the_wire():
    from hangar.index import parts_json
    pj = parts_json(load_design(FIX))
    assert len(pj["parts"]) == 4
    w = pj["parts"][-1]
    assert w["id"] == "wire-w1" and w["type"] == "wire" and w["visual_only"] is True and w["parent"] is None
    assert w["position_mm"] == pytest.approx([36.07, -6.0, 0.0], abs=1e-9)


def test_version_gate_and_schema():
    dd = data()
    dd["schema_version"] = "1.2"
    r = rows(dd)
    assert any(x.check_id == "T0.version" and x.status == "FAIL" and "waypoints" in x.message for x in r.values())
    dd = data()
    dd["wiring"]["harnesses"][0]["waypoints"] = [[1, 2]]
    assert rows(dd)["T0.schema"].status == "FAIL"
    dd = data()
    dd["wiring"]["harnesses"][0]["diameter_mm"] = 0
    assert rows(dd)["T0.schema"].status == "FAIL"
    ref = (REPO / "docs" / "pdl" / "reference.md").read_text(encoding="utf-8")
    assert "waypoints" in ref and "from_port" in ref


PARTS = ["emax-es08maii-metal", "hobbywing-flyfun-30a-mini-v5", "radiomaster-rp3-v2-elrs-rx",
         "tmotor-mn3510-kv700", "tattu-2300mah-4s-75c"]


def test_part_ports_validation():
    pid = "emax-es08maii-metal"
    base = {k: v for k, v in library.load_part(pid).items() if k != "_dir"}
    assert library.part_errors(base, pid) == []
    d = copy.deepcopy(base)
    del d["ports_source"]
    assert any("ports_source" in e for e in library.part_errors(d, pid))
    d = copy.deepcopy(base)
    d["ports"]["signal"]["point"] = [1, 2]
    assert any("point" in e for e in library.part_errors(d, pid))
    d = copy.deepcopy(base)
    d["ports"]["signal"]["direction"] = [0, 0, 0]
    assert any("direction" in e for e in library.part_errors(d, pid))
    assert library.load_part("radiomaster-rp3-v2-elrs-rx")["ports"]["ch5"]["point"] == [36.07, 6.0, 0]
    for p in PARTS:
        part = library.load_part(p)
        assert "ports" in part and "ports_source" in part
