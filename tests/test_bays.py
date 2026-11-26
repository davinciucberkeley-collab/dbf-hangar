"""U16.1 S3: `design place` puts a library servo in a bay (a box cavity on the host); part frames."""
import copy, shutil, numpy as np, pytest, yaml
from pathlib import Path

from hangar.ops import call
from hangar.design import load_design
from hangar.geom.library import load_part, part_errors
from hangar.checks import validate

FIX = Path(__file__).parent / "fixtures" / "bay"
ROOT = Path(__file__).resolve().parents[1]


def scratch(tmp_path):
    shutil.copytree(FIX, tmp_path / "bay")
    return tmp_path / "bay"


def _plane(folder):
    return yaml.safe_load((folder / "plane.yaml").read_text(encoding="utf-8"))


def _comp(folder, cid):
    return next(c for c in _plane(folder)["components"] if c["id"] == cid)


def _place(folder, **kw):
    args = dict(path=str(folder), component="servo", host="host", at="0,0", face="lower", why="x")
    args.update(kw)
    return call("design.place", **args)


def test_place_lower_hand_values(tmp_path):
    folder = scratch(tmp_path)
    r = _place(folder, why="bay for the test")
    assert r.ok, r.messages
    d = r.data
    assert d["position"] == pytest.approx([0, 0, 5.5], abs=1e-4)
    assert d["rotation_deg"] == [180, 0, 0]
    assert d["output_point"] == pytest.approx([5.5, 0, -6.5], abs=1e-4)
    assert d["output_axis"] == pytest.approx([0, 0, -1], abs=1e-4)
    assert d["cavity"]["geometry"]["box"]["size"] == pytest.approx([23.6, 12.1, 18.8], abs=1e-4)
    assert d["cavity"]["position"] == pytest.approx([0, 0, -11.6], abs=1e-4)
    assert d["removed_mm3"] == pytest.approx(5082.97, abs=1)
    assert d["body_inside_fraction"] == pytest.approx(1.0, abs=1e-3)
    servo, host = _comp(folder, "servo"), _comp(folder, "host")
    assert servo["position"] == pytest.approx([0, 0, 5.5], abs=1e-4)
    assert servo["rotation_deg"] == [180, 0, 0]
    assert [c["description"] for c in host["cavities"]] == ["bay for servo"]
    log = yaml.safe_load((folder / "CHANGELOG.yaml").read_text(encoding="utf-8"))
    assert any("bay for the test" in str(e.get("why")) for e in log)


def test_validate_after_placing(tmp_path):
    folder = scratch(tmp_path)
    assert _place(folder).ok
    card = validate(load_design(folder / "plane.yaml"), 1)
    rows = [r for t in card.tiers if t.tier in (0, 1) for r in t.results]
    assert not [r.check_id for r in rows if r.status == "FAIL"]
    att = [r for r in rows if r.check_id == "T1.attachment" and "host-servo" in (r.message + str(r.data))]
    assert att and all(r.status == "PASS" for r in att)


def test_idempotent(tmp_path):
    folder = scratch(tmp_path)
    assert _place(folder).ok
    first = (folder / "plane.yaml").read_bytes()
    assert _place(folder).ok
    assert (folder / "plane.yaml").read_bytes() == first
    assert len(_comp(folder, "host")["cavities"]) == 1


def test_upper_face(tmp_path):
    folder = scratch(tmp_path)
    r = _place(folder, face="upper")
    assert r.ok, r.messages
    d = r.data
    assert d["rotation_deg"] in ([0, 0, 0], None) or list(d["rotation_deg"]) == [0, 0, 0]
    assert "rotation_deg" not in _comp(folder, "servo")
    assert d["position"] == pytest.approx([0, 0, 34.5], abs=1e-4)
    size = d["cavity"]["geometry"]["box"]["size"]
    assert size[2] == pytest.approx(18.8, abs=1e-4)
    z_lo, z_hi = 22.2, 41.0
    centre = d["cavity"]["position"][2] + 20
    assert centre == pytest.approx((z_lo + z_hi) / 2, abs=1e-4)


def test_shaft_sideways(tmp_path):
    folder = scratch(tmp_path)
    r = _place(folder, shaft="0,1,0")
    assert r.ok, r.messages
    assert r.data["rotation_deg"] == [270, 0, 0]
    assert r.data["output_axis"] == pytest.approx([0, 1, 0], abs=1e-9)
    assert 0 < r.data["body_inside_fraction"] <= 1


def test_input_errors(tmp_path):
    folder = scratch(tmp_path)
    r = _place(folder, shaft="1,1,0")
    assert not r.ok and r.data["error"] == "input"
    r = _place(folder, at="500,0")
    assert not r.ok and r.data["error"] == "input" and "no host surface" in " ".join(r.messages)
    p = folder / "plane.yaml"
    t = p.read_text(encoding="utf-8")
    p.write_text(t.replace("position: [0, 0, 20], mass_g: 12", "position: [0, 0, 20], mass_g: 12").replace(
        "part: emax-es08maii-metal", "part: towerpro-mg90s"), encoding="utf-8")
    r = _place(folder)
    assert not r.ok and r.data["error"] == "input" and "towerpro-mg90s" in " ".join(r.messages)
    folder2 = scratch(tmp_path / "two")
    p2 = folder2 / "plane.yaml"
    p2.write_text(p2.read_text(encoding="utf-8").replace("position: [0, 0, 20], mass_g: 50", "position: [0, 0, 20], rotation_deg: [0, 0, 10], mass_g: 50"), encoding="utf-8")
    r = _place(folder2)
    assert not r.ok and r.data["error"] == "input"


def test_part_frames_validation():
    raw = yaml.safe_load((ROOT / "knowledge/parts/emax-es08maii-metal/part.yaml").read_text(encoding="utf-8"))
    assert part_errors(raw, "emax-es08maii-metal") == []
    bad = copy.deepcopy(raw)
    del bad["frames_source"]
    assert any("frames_source" in e for e in part_errors(bad, "emax-es08maii-metal"))
    bad = copy.deepcopy(raw)
    bad["frames"]["output"]["axis"] = [1, 1, 0]
    assert any("axis" in e for e in part_errors(bad, "emax-es08maii-metal"))
    bad = copy.deepcopy(raw)
    bad["category"] = "motor"
    assert any("frames" in e for e in part_errors(bad, "emax-es08maii-metal"))
    assert load_part("emax-es08maii-metal")["frames"]["output"]["point"] == [5.5, 0, 12.0]


def test_threshold_and_docs():
    th = yaml.safe_load((ROOT / "standards/gate-thresholds.yaml").read_text(encoding="utf-8"))
    assert th["bay_clearance_mm"]["source"] == "pending"
    assert "frames_source" in (ROOT / "knowledge/parts/README.md").read_text(encoding="utf-8")
