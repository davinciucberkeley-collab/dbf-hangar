"""U16.1 S4: `design add-linkage` writes arm, rod, horn, pin, their attachments and the four_bar mechanism, clear of the servo and the surface."""
import shutil, numpy as np, pytest, yaml
from pathlib import Path

from hangar.ops import call
from hangar.design import load_design
from hangar.checks import validate
from hangar.geometry import component_parts
from hangar.gates.mechanisms import simulate_mechanism, link_ratios

FIX = Path(__file__).parent / "fixtures" / "linkage-op"
RECIPE = Path(__file__).parent / "fixtures" / "mechanism-recipe"
O, OP, P, AX = (np.array(v, float) for v in ((20, 0, -12.4), (20, 0, -11.05), (60, 0, 0), (0, -1, 0)))


def scratch(tmp_path, name="f"):
    shutil.copytree(FIX, tmp_path / name)
    return tmp_path / name


def run(folder, **kw):
    args = dict(path=str(folder), servo="servo", hinge="stab-elev", station=0, why="x")
    args.update(kw)
    return call("design.add-linkage", **args)


def _plane(folder):
    return yaml.safe_load((folder / "plane.yaml").read_text(encoding="utf-8"))


def _comp(folder, cid):
    return next(c for c in _plane(folder)["components"] if c["id"] == cid)


def _strut(folder, cid):
    return _comp(folder, cid)["geometry"]["params"]


def test_hand_values(tmp_path):
    f = scratch(tmp_path)
    r = run(f)
    assert r.ok, r.messages
    ap = pytest.approx
    assert r.data["tip0"] == ap([20.5439, 5.9753, -11.05], abs=2e-3)
    assert r.data["pin0"] == ap([69.7072, 1.5, -11.05], abs=2e-3)
    assert r.data["horn_root"] == ap([66.7467, 0, -1.5], abs=2e-3)
    assert r.data["arm_pivot"] == ap([20, 0, -11.05], abs=2e-3)
    assert r.data["rod_length"] == ap(49.3665, abs=2e-3)
    assert r.data["skin_to_pin"] == ap(9.9984, abs=2e-3)
    assert r.data["ratio"] == -0.55
    d = _plane(f)
    ids = {c["id"] for c in d["components"]}
    assert {"stab-elev-arm", "stab-elev-rod", "stab-elev-horn", "stab-elev-pin"} <= ids
    aids = {a["id"] for a in d["attachments"]}
    assert {"stab-elev-servo-arm", "stab-elev-arm-rod", "stab-elev-horn-mount", "stab-elev-horn-pin"} <= aids
    m = next(m for m in d["mechanisms"] if m["id"] == "stab-elev-drive")
    assert m["kinematics"] == "four_bar"
    assert m["link"] == {"driver_end": "stab-elev-arm-rod", "follower_end": "stab-elev-horn-pin"}
    arm, rod, horn, pin = (_strut(f, f"stab-elev-{k}") for k in ("arm", "rod", "horn", "pin"))
    assert arm["start"] == ap([20, 0, -11.05], abs=2e-3) and arm["end"] == ap([20.5439, 5.9753, -11.05], abs=2e-3)
    assert rod["start"] == ap(r.data["tip0"], abs=2e-3) and rod["end"] == ap([67.7154, 1.6813, -11.05], abs=2e-3)
    assert horn["start"] == ap([66.4506, 0, -0.5448], abs=2e-3) and horn["end"] == ap([70.0033, 0, -12.0052], abs=2e-3)
    assert pin["start"] == ap([69.7072, 2.1, -11.05], abs=2e-3) and pin["end"] == ap([69.7072, 0.9, -11.05], abs=2e-3)


def test_geometry_rules(tmp_path):
    f = scratch(tmp_path)
    assert run(f).ok
    atts = {a["id"]: a for a in _plane(f)["attachments"]}
    tip0 = np.array(atts["stab-elev-arm-rod"]["location"], float)
    pin0 = np.array(atts["stab-elev-horn-pin"]["location"], float)
    root = np.array(atts["stab-elev-horn-mount"]["location"], float)
    assert np.linalg.norm(tip0 - OP) == pytest.approx(6, abs=1e-3)
    assert (pin0 - tip0) @ (tip0 - OP) == pytest.approx(0, abs=5e-3)   # 4-decimal rounding of written points x 49 mm rod
    assert (pin0 - OP)[2] == pytest.approx(0, abs=1e-3)
    assert root[2] == pytest.approx(-1.5, abs=1e-3)
    assert root[0] > 60 + 2 + 1
    assert pin0[1] - P[1] == pytest.approx(1.5, abs=1e-3)
    design = load_design(f / "plane.yaml")
    sv = np.vstack([m.vertices for m in component_parts(design.component("servo"), design.base_dir)])
    assert OP[2] - 0.75 - sv[:, 2].max() == pytest.approx(0.6, abs=1e-3)


def test_t6_passes_no_t1_fail(tmp_path):
    f = scratch(tmp_path)
    r = run(f)
    assert r.ok, r.messages
    design = load_design(f / "plane.yaml")
    card = validate(design)
    rows = [x for t in card.tiers for x in t.results]
    bad = [(x.check_id, x.message) for x in rows if x.status == "FAIL" and x.check_id.startswith(("T0", "T1", "T6"))]
    assert bad == []
    assert [row for row in r.data["rows"] if row[1] == "FAIL"] == []
    by = {x.check_id: x for x in rows}
    assert by["T6.mechanism.stab-elev-drive"].status == "PASS" and "four_bar" in by["T6.mechanism.stab-elev-drive"].message
    assert by["T6.link.stab-elev-drive"].status == "PASS"
    assert by["T6.ratio.stab-elev-drive"].status == "PASS"
    assert "T6.servo_undriven.servo" not in by
    mech = next(m for m in design.data["mechanisms"] if m["id"] == "stab-elev-drive")
    sim = simulate_mechanism(design, mech)
    got = {s["input_deg"]: s["followers"]["stab-elev"] for s in sim["steps"]}
    for inp, want in ((-20, 11.5128), (-10, 5.6207), (10, -5.2578), (20, -10.0839)):
        assert got[inp] == pytest.approx(want, abs=2e-3)
    assert r.data["min_transmission_deg"] > 30


def test_second_run_is_an_empty_diff(tmp_path):
    f = scratch(tmp_path)
    assert run(f).ok
    a, b = (f / "plane.yaml").read_bytes(), (f / "CHANGELOG.yaml").read_bytes()
    r = run(f)
    assert r.ok and r.data["changed"] is False
    assert (f / "plane.yaml").read_bytes() == a and (f / "CHANGELOG.yaml").read_bytes() == b


def test_rerun_after_a_change_follows(tmp_path):
    f = scratch(tmp_path)
    assert run(f).ok
    s = call("design.set", path=str(f), key="components[servo].position", value="[14.5, 0, -30]", why="move")
    assert s.ok, s.messages
    r = run(f)
    assert r.ok, r.messages
    assert r.data["changed"] is True
    assert len([c for c in _plane(f)["components"] if c["id"].startswith("stab-elev-")]) == 4
    assert r.data["tip0"][2] == pytest.approx(-16.65, abs=2e-3)
    assert r.data["pin0"] == pytest.approx([74.072, 1.5, -16.65], abs=2e-3)


def test_hinge_station_moves_the_horn(tmp_path):
    r = run(scratch(tmp_path), station=20)
    assert r.ok, r.messages
    ap = pytest.approx
    assert r.data["pin0"] == ap([69.7072, -18.5, -11.05], abs=2e-3)
    assert r.data["tip0"] == ap([22.7155, 5.3503, -11.05], abs=2e-3)
    assert r.data["horn_root"] == ap([66.7467, -20, -1.5], abs=2e-3)
    assert r.data["ratio"] == -0.61


def test_horn_height_option(tmp_path):
    r = run(scratch(tmp_path), horn_height=4)
    assert r.ok, r.messages
    assert r.data["skin_to_pin"] == pytest.approx(4, abs=2e-3)
    assert r.data["pin0"] == pytest.approx([67.9311, 1.5, -5.3206], abs=2e-3)


@pytest.mark.skipif(not Path("C:/Users/trist/parts-cad").exists(), reason="no local CAD overlay on this machine")
def test_overlay_does_not_change_the_written_file(tmp_path, monkeypatch):
    monkeypatch.delenv("PLANE_CAD_OVERLAY", raising=False)
    a = scratch(tmp_path, "a")
    assert run(a).ok
    monkeypatch.setenv("PLANE_CAD_OVERLAY", "off")
    b = scratch(tmp_path, "b")
    assert run(b).ok
    assert (a / "plane.yaml").read_bytes() == (b / "plane.yaml").read_bytes()


def _no_change(folder, **kw):
    before = (folder / "plane.yaml").read_bytes()
    r = run(folder, **kw)
    assert not r.ok and r.data["error"] == "input"
    assert (folder / "plane.yaml").read_bytes() == before
    assert not (folder / "CHANGELOG.yaml").exists()
    return r.messages[0]


def _edit(folder, old, new):
    txt = (folder / "plane.yaml").read_text(encoding="utf-8").replace(old, new)
    (folder / "plane.yaml").write_text(txt, encoding="utf-8")


def test_input_errors(tmp_path):
    f = scratch(tmp_path)
    assert "nope" in _no_change(f, servo="nope")
    assert "articulation" in _no_change(f, hinge="stab-post")
    assert "arm length" in _no_change(f, arm_length=60)
    g = scratch(tmp_path, "g")
    _edit(g, "emax-es08maii-metal", "towerpro-mg90s")
    assert "frames" in _no_change(g)
    h = scratch(tmp_path, "h")
    _edit(h, "axis: [0, -1, 0]", "axis: [0, 0, 1]")
    assert "give --horn-toward" in _no_change(h)
    k = scratch(tmp_path, "k")
    _edit(k, "position: [14.5, 0, -24.4]", "position: [14.5, 0, -8]")
    assert "arm plane" in _no_change(k)
    assert "horn root" in _no_change(scratch(tmp_path, "m"), horn_offset=80)


def test_link_ratios_matches_the_gate_row():
    design = load_design(RECIPE / "plane.yaml")
    mech = next(m for m in design.data["mechanisms"] if m["id"] == "elevator-drive")
    assert link_ratios(design, mech)["stab-elev"] == pytest.approx(-0.3934, abs=1e-3)
    card = validate(design)
    row = next(x for t in card.tiers for x in t.results if x.check_id == "T6.ratio.elevator-drive")
    assert "-0.393" in row.message
