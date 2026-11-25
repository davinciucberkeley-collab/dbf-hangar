"""U13.6: plane design bounds lists every component's bounding box in the body frame."""
from __future__ import annotations

import copy
import shutil
from pathlib import Path

import pytest
import yaml

from hangar import design as design_mod
from hangar.design import load_design
from hangar.ops import call, registry

EXAMPLE_DIR = design_mod.DESIGNS_DIR / "example-tailsitter-wing"
DERIVED_DIR = design_mod.REPO_ROOT / "tests" / "fixtures" / "derived-planform"


def _entry(r, cid):
    return next(e for e in r.data["components"] if e["id"] == cid)


def test_box_component_bounds():
    r = call("design.bounds", path=str(EXAMPLE_DIR))
    assert r.ok
    e = _entry(r, "center_body")
    assert e["min"] == [0.0, -40.0, -40.0]
    assert e["max"] == [300.0, 40.0, 40.0]
    assert e["size"] == [300.0, 80.0, 80.0]
    assert e["center"] == [150.0, 0.0, 0.0]


def test_every_component_listed_in_file_order():
    r = call("design.bounds", path=str(EXAMPLE_DIR))
    assert [e["id"] for e in r.data["components"]] == [
        c["id"] for c in load_design(EXAMPLE_DIR).data["components"]
    ]


def test_generated_wing():
    r = call("design.bounds", path=str(DERIVED_DIR))
    e = _entry(r, "wing")
    assert e["min"][0] == pytest.approx(200.0, abs=1e-3)
    assert e["max"][0] == pytest.approx(400.0, abs=1e-3)
    assert e["min"][1] == pytest.approx(-600.0, abs=1e-3)
    assert e["max"][1] == pytest.approx(600.0, abs=1e-3)


def test_overall_spans_everything():
    r = call("design.bounds", path=str(EXAMPLE_DIR))
    comps = r.data["components"]
    overall = r.data["overall"]
    for i in range(3):
        assert overall["min"][i] == min(c["min"][i] for c in comps if "min" in c)
        assert overall["max"][i] == max(c["max"][i] for c in comps if "max" in c)


def test_point_mass_and_error(tmp_path):
    dst = tmp_path / "example-tailsitter-wing"
    shutil.copytree(EXAMPLE_DIR, dst)
    plane = dst / "plane.yaml"
    data = yaml.safe_load(plane.read_text(encoding="utf-8"))
    data["components"].append({"id": "pm", "type": "other", "geometry": {"point_mass": {}},
                               "position": [1, 2, 3], "mass_g": 1})
    data["components"].append({"id": "bad", "type": "other", "geometry": {"mesh": {"file": "nope.stl"}},
                               "position": [0, 0, 0], "mass_g": 1})
    plane.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    r = call("design.bounds", path=str(dst))
    assert r.ok
    pm = _entry(r, "pm")
    assert pm == {"id": "pm", "type": "other", "point": [1.0, 2.0, 3.0]}
    bad = _entry(r, "bad")
    assert "error" in bad
    assert _entry(r, "center_body")["size"] == [300.0, 80.0, 80.0]


def test_registered_and_rendered():
    assert "design.bounds" in registry()
    r = call("design.bounds", path=str(EXAMPLE_DIR))
    lines = registry()["design.bounds"].render(r).splitlines()
    assert any(line.startswith("center_body") for line in lines)
    assert lines[-1].startswith("overall")
