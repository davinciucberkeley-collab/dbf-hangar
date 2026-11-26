"""U16.1 S4: `design add-linkage` writes arm, rod, horn, pin, their attachments and the four_bar mechanism."""
import shutil, numpy as np, pytest, yaml
from pathlib import Path

from hangar.ops import call
from hangar.design import load_design
from hangar.checks import validate
from hangar.gates.mechanisms import simulate_mechanism, link_ratios

FIX = Path(__file__).parent / "fixtures" / "linkage-op"
RECIPE = Path(__file__).parent / "fixtures" / "mechanism-recipe"
O, P, AX = np.array([20, 0, -5.0]), np.array([60.0, 0, 0]), np.array([0, -1.0, 0])


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


def test_hand_values(tmp_path):
    f = scratch(tmp_path)
    r = run(f)
    assert r.ok, r.messages
    tip0, pin0 = np.array(r.data["tip0"]), np.array(r.data["pin0"])
    assert tip0 == pytest.approx([20.8651, 5.9373, -5.0], abs=2e-3)
    assert pin0 == pytest.approx([61.6125, 0, -12.8996], abs=2e-3)
    assert r.data["rod_length"] == pytest.approx(41.9285, abs=2e-3)
    assert r.data["ratio"] == -0.48
    d = _plane(f)
    ids = {c["id"] for c in d["components"]}
    assert {"stab-elev-arm", "stab-elev-rod", "stab-elev-horn", "stab-elev-pin"} <= ids
    aids = {a["id"] for a in d["attachments"]}
    assert {"stab-elev-servo-arm", "stab-elev-arm-rod", "stab-elev-horn-mount", "stab-elev-horn-pin"} <= aids
    m = next(m for m in d["mechanisms"] if m["id"] == "stab-elev-drive")
    assert m["kinematics"] == "four_bar"
    assert m["link"] == {"driver_end": "stab-elev-arm-rod", "follower_end": "stab-elev-horn-pin"}
    rod = _comp(f, "stab-elev-rod")["geometry"]["params"]
    u = (pin0 - tip0) / np.linalg.norm(pin0 - tip0)
    assert rod["start"] == pytest.approx(tip0, abs=1e-3)
    assert rod["end"] == pytest.approx(pin0 - 2 * u, abs=1e-3)


def test_geometry_rules(tmp_path):
    f = scratch(tmp_path)
    assert run(f).ok
    atts = {a["id"]: a for a in _plane(f)["attachments"]}
    tip0 = np.array(atts["stab-elev-arm-rod"]["location"], float)
    pin0 = np.array(atts["stab-elev-horn-pin"]["location"], float)
    assert np.linalg.norm(tip0 - O) == pytest.approx(6, abs=1e-3)
    assert (pin0 - tip0) @ (tip0 - O) == pytest.approx(0, abs=1e-3)
    assert (pin0 - P) @ AX == pytest.approx(0, abs=1e-3)
    assert np.linalg.norm(pin0 - P) == pytest.approx(13, abs=1e-3)


def test_t6_passes_t1_reported(tmp_path):
    f = scratch(tmp_path)
    r = run(f)
    assert r.ok
    design = load_design(f / "plane.yaml")
    card = validate(design)
    rows = [x for t in card.tiers for x in t.results]
    assert [x.check_id for x in rows if x.status == "FAIL" and x.check_id.startswith("T0")] == []
    bad = [(x.check_id, x.message) for x in rows if x.status == "FAIL" and x.check_id.startswith("T6")]
    assert bad == []
    reported = [row for row in r.data["rows"] if row[0].startswith("T1.")]
    new_parts = ("stab-elev-arm", "stab-elev-rod", "stab-elev-horn", "stab-elev-pin")
    t1_new = [(x.check_id, x.message) for x in rows
              if x.status == "FAIL" and x.check_id.startswith("T1.") and any(p in x.message for p in new_parts)]
    assert {tuple(row[:1]) + (row[2],) for row in reported} >= {(c, m) for c, m in t1_new}
    by = {x.check_id: x for x in rows}
    assert by["T6.mechanism.stab-elev-drive"].status == "PASS" and "four_bar" in by["T6.mechanism.stab-elev-drive"].message
    assert by["T6.link.stab-elev-drive"].status == "PASS"
    assert by["T6.ratio.stab-elev-drive"].status == "PASS"
    assert "T6.servo_undriven.servo" not in by
    mech = next(m for m in design.data["mechanisms"] if m["id"] == "stab-elev-drive")
    sim = simulate_mechanism(design, mech)
    got = {s["input_deg"]: s["followers"]["stab-elev"] for s in sim["steps"]}
    for inp, want in ((-20, 9.7177), (-10, 4.8605), (10, -4.7349), (20, -9.2377)):
        assert got[inp] == pytest.approx(want, abs=2e-3)
    assert r.data["min_transmission_deg"] > 60


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
    assert r.data["tip0"][2] == pytest.approx(-18.0, abs=1e-3)


def test_hinge_station_moves_the_horn(tmp_path):
    r0 = run(scratch(tmp_path, "f"))
    r1 = run(scratch(tmp_path, "g"), station=20)
    assert r1.ok, r1.messages
    p0, p1 = r0.data["pin0"], r1.data["pin0"]
    assert p1[1] == pytest.approx(-20, abs=1e-3)
    assert p1[0] == pytest.approx(p0[0], abs=1e-3) and p1[2] == pytest.approx(p0[2], abs=1e-3)


def _no_change(folder, **kw):
    before = (folder / "plane.yaml").read_bytes()
    r = run(folder, **kw)
    assert not r.ok and r.data["error"] == "input"
    assert (folder / "plane.yaml").read_bytes() == before
    assert not (folder / "CHANGELOG.yaml").exists()
    return r.messages[0]


def test_input_errors(tmp_path):
    f = scratch(tmp_path)
    assert "nope" in _no_change(f, servo="nope")
    assert "articulation" in _no_change(f, hinge="stab-servo")
    assert "arm length" in _no_change(f, arm_length=60)
    g = scratch(tmp_path, "g")
    txt = (g / "plane.yaml").read_text(encoding="utf-8").replace("emax-es08maii-metal", "towerpro-mg90s")
    (g / "plane.yaml").write_text(txt, encoding="utf-8")
    assert "frames" in _no_change(g)
    h = scratch(tmp_path, "h")
    txt = (h / "plane.yaml").read_text(encoding="utf-8").replace("axis: [0, -1, 0]", "axis: [0, 0, 1]")
    (h / "plane.yaml").write_text(txt, encoding="utf-8")
    assert "give --horn-dir" in _no_change(h)


def test_link_ratios_matches_the_gate_row():
    design = load_design(RECIPE / "plane.yaml")
    mech = next(m for m in design.data["mechanisms"] if m["id"] == "elevator-drive")
    assert link_ratios(design, mech)["stab-elev"] == pytest.approx(-0.3934, abs=1e-3)
    card = validate(design)
    row = next(x for t in card.tiers for x in t.results if x.check_id == "T6.ratio.elevator-drive")
    assert "-0.393" in row.message
