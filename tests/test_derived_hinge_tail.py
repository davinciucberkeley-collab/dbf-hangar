import copy
from pathlib import Path

import pytest
import trimesh

from hangar.geom.resolve import resolve_design_data
from hangar.geometry import component_parts

BASE = Path(__file__).parent
COMMON = dict(airfoil_file="naca0009", stab_span=325, stab_root_chord=120, stab_tip_chord=92, stab_sweep_le_deg=5.9,
              stab_x_le=0, stab_z=0, hinge_frac=0.6, layout="conventional", fin_thickness=6, fin_height=140,
              fin_root_chord=150, fin_tip_chord=86, fin_sweep_le_deg=28.5, fin_x_le=-40, fin_z_root=0)
FIN = dict(thickness=6, root_chord=150, tip_chord=86, height=140, x_le=-40, z_root=0, sweep_le_deg=28.5,
           hinge_frac=0.6, part="rear")


def _comp(cid, part, **extra):
    return {"id": cid, "type": "tail_surface", "position": [640, 0, 16],
            "geometry": {"generator": "tail_surfaces", "params": {**COMMON, "part": part, **extra}}}


def _att(aid, child):
    return {"id": aid, "parent": "tail-fixed", "child": child, "method": "hinge", "hinge_from": "generator",
            "location": [0, 0, 0], "rated_load_n": 10,
            "articulation": {"type": "revolute", "pivot": [0, 0, 0], "axis": [0, -1, 0], "range_deg": [-10, 10]}}


def raw_design(gap=24):
    return {"components": [_comp("tail-fixed", "fixed"),
                           _comp("elevator", "elevator", hinge_gap=0, hinge_style="none", elevator_fin_gap=gap),
                           _comp("rudder", "rudder")],
            "attachments": [_att("tail-elev", "elevator"), _att("tail-rud", "rudder")]}


def att(data, i):
    return next(a for a in data["attachments"] if a["id"] == i)


def check(a, pivot, axis, tol=1e-3):
    assert a["location"] == pytest.approx(pivot, abs=0.01)
    assert a["articulation"]["pivot"] == pytest.approx(pivot, abs=0.01)
    assert a["articulation"]["axis"] == pytest.approx(axis, abs=tol)


def test_elevator_gap_pivot():
    data, errors = resolve_design_data(raw_design(24), BASE)
    a = att(data, "tail-elev")
    check(a, [711.9958, 94.75, 16.0], [0.0, 1.0, 0.0])
    assert a["articulation"]["range_deg"] == [-10, 10]
    assert errors == {}


def test_elevator_no_gap_pivot():
    data, errors = resolve_design_data(raw_design(0), BASE)
    check(att(data, "tail-elev"), [711.996, 81.25, 16.0], [0.0, 1.0, 0.0])
    assert errors == {}


def test_elevator_pivot_lies_on_part():
    data, _ = resolve_design_data(raw_design(24), BASE)
    pivot = att(data, "tail-elev")["articulation"]["pivot"]
    comp = next(c for c in data["components"] if c["id"] == "elevator")
    parts = component_parts(comp, BASE)

    def dist(pt):
        return min(abs(trimesh.proximity.signed_distance(m, [pt])[0]) for m in parts)
    assert dist(pivot) < 0.05
    assert dist([711.9958, 0.0, 16.0]) > 20


def test_rudder_pivot_and_axis():
    data, errors = resolve_design_data(raw_design(), BASE)
    check(att(data, "tail-rud"), [708.8069, 0.0, 86.0], [0.2595, 0.0, 0.9658], tol=5e-4)
    assert errors == {}


def test_fin_rear_pivot_and_axis():
    raw = raw_design()
    rud = next(c for c in raw["components"] if c["id"] == "rudder")
    rud["geometry"] = {"generator": "fin", "params": dict(FIN)}
    data, errors = resolve_design_data(raw, BASE)
    check(att(data, "tail-rud"), [708.8069, 0.0, 86.0], [0.2595, 0.0, 0.9658], tol=5e-4)
    assert errors == {}


def test_follows_the_parameter():
    raw = raw_design()
    for c in raw["components"]:
        c["geometry"]["params"].update(stab_span=400, fin_height=160)
    data, errors = resolve_design_data(raw, BASE)
    assert att(data, "tail-elev")["articulation"]["pivot"][1] == pytest.approx((27 + 200) / 2, abs=1e-3)
    assert att(data, "tail-rud")["articulation"]["pivot"][2] == pytest.approx(16 + 80, abs=0.01)
    assert errors == {}


def test_bad_parts_are_errors():
    raw = raw_design()
    raw["attachments"] = [{**_att("bad", "tail-fixed"), "parent": "elevator"}]
    data, errors = resolve_design_data(raw, BASE)
    assert "hinge_from" in errors["tail-fixed"]
    assert att(data, "bad")["location"] == [0, 0, 0]
    raw = raw_design()
    for c in raw["components"]:
        c["geometry"]["params"]["layout"] = "h"
    data, errors = resolve_design_data(raw, BASE)
    assert "hinge_from" in errors["rudder"]


def test_stored_values_without_hinge_from_unchanged():
    raw = raw_design()
    for a in raw["attachments"]:
        del a["hinge_from"]
    data, _ = resolve_design_data(copy.deepcopy(raw), BASE)
    for aid in ("tail-elev", "tail-rud"):
        a = att(data, aid)
        assert a["location"] == [0, 0, 0]
        assert a["articulation"]["pivot"] == [0, 0, 0]
        assert a["articulation"]["axis"] == [0, -1, 0]
