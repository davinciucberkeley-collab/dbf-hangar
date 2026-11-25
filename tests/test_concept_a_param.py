"""U9.2 Part B: concept-a-param (four generated parts, shared parameters) against concept-a (hand numbers from the brief)."""
from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pytest
import trimesh
import yaml

from hangar.baseline import compare, read_baseline, snapshot
from hangar.checks import tier0_schema, validate
from hangar.design import DESIGNS_DIR, load_design
from hangar.geometry import component_parts
from hangar.mass import mass_properties
from hangar.ops import call

A = DESIGNS_DIR / "concept-a"
P = DESIGNS_DIR / "concept-a-param"
GENERATED = ("wng-001", "wng-002", "fin-001-l", "fin-001-r")
DEMO_VALUE = "940"
# The swept-pose residue of the cut pockets is baselined (README); the demo edit adds no regression.
EXPECTED_REGRESSIONS: list = []


def _comp(design, cid):
    return next(c for c in design.data["components"] if c["id"] == cid)


def _mesh(design, cid):
    return trimesh.util.concatenate(component_parts(_comp(design, cid), design.base_dir))


def _rows(card):
    return [r for t in card.tiers for r in t.results]


def _per(mp):
    return {c["id"]: c["mass_g"] for c in mp["per_component"]}


@pytest.fixture(scope="module")
def pd():
    return load_design(P)


@pytest.fixture(scope="module")
def ad():
    return load_design(A)


@pytest.mark.parametrize("cid", ["wng-002", "fin-001-r", "fin-001-l"])
def test_generated_tubes_match_imported_meshes(pd, cid):
    m = _mesh(pd, cid)
    ref = trimesh.load(A / "meshes" / f"{cid}.stl", force="mesh")
    assert abs(m.volume) == pytest.approx(abs(ref.volume), rel=1e-3)
    assert np.abs(m.bounds - ref.bounds).max() <= 0.02


def test_generated_wing_core_matches_outline(pd):
    m = _mesh(pd, "wng-001")
    ref = trimesh.load(A / "meshes" / "wng-001.stl", force="mesh")
    assert m.is_watertight
    assert ref.volume <= m.volume <= ref.volume * 1.16
    assert np.abs(m.bounds - ref.bounds).max() <= 0.1
    cuts = _comp(pd, "wng-001")["geometry"]["params"]["cut_files"]
    assert len(cuts) == 40
    # neutral-pose interference with any neighbour (all are in cut_files): none; swept poses are the baselined residue
    bad = [r.message for r in _rows(validate(pd, max_tier=1))
           if r.check_id == "T1.interference" and "wng-001" in r.message
           and not any(k in r.message for k in ("pose ", "sweep ", "range "))]
    assert bad == []
    # attachment rows name the joint (E-WNG-..), not the part: no neutral-pose overlap row for a joint of wng-001 (the two pose-down rows are the baselined residue)
    joints = {a.get("id") or f"{a['parent']}->{a['child']}" for a in pd.data["attachments"] if "wng-001" in (a["parent"], a["child"])}
    assert len(joints) >= 5
    neutral = [r.message for r in _rows(validate(pd, max_tier=1))
               if r.check_id == "T1.attachment_overlap" and r.message.split(":")[0] in joints]
    assert neutral == []


def test_nominal_masses(pd, ad):
    mp, ma = mass_properties(pd), mass_properties(ad)
    pc, ac = _per(mp), _per(ma)
    assert "mass_model" in _comp(pd, "wng-001") and "mass_g" not in next(
        c for c in pd.raw["components"] if c["id"] == "wng-001")
    assert pc["wng-001"] == pytest.approx(100.1, abs=0.2)
    for cid in GENERATED[1:]:
        assert pc[cid] == pytest.approx(ac[cid], rel=0.01)
    assert mp["mass_g"] == pytest.approx(ma["mass_g"], abs=0.5)
    # CG y: the generated core's cut pockets are not mirror-symmetric, so y moves by 0.12 mm (README); x and z stay tight.
    assert mp["cg_mm"][0] == pytest.approx(ma["cg_mm"][0], abs=0.05)
    assert mp["cg_mm"][1] == pytest.approx(ma["cg_mm"][1], abs=0.15)
    assert mp["cg_mm"][2] == pytest.approx(ma["cg_mm"][2], abs=0.05)


def test_param_design_is_clean(pd, tmp_path):
    rows = {r.check_id: r.status for r in tier0_schema(pd).results}
    assert rows["T0.parameters"] == "PASS" and rows["T0.generator"] == "PASS"
    assert len(pd.data["parameters"]) == 9
    d = tmp_path / "concept-a-param"       # row messages quote the folder name
    shutil.copytree(P, d)
    card = validate(load_design(d))
    assert not [r for r in _rows(card) if r.check_id.endswith(".error")]
    assert compare(snapshot(card), read_baseline(d))["regressions"] == []


def test_unchanged_parts_are_identical_to_concept_a():
    pa, aa = yaml.safe_load((P / "plane.yaml").read_text()), yaml.safe_load((A / "plane.yaml").read_text())
    ca = {c["id"]: c for c in aa["components"]}
    cp = {c["id"]: c for c in pa["components"]}
    assert set(ca) == set(cp)
    for cid, c in cp.items():
        if cid in GENERATED:
            continue
        # U11.1/T129: a part whose placement is a span expression moves with parameters.span_mm; Test 5 covers its shift
        if any(isinstance(v, str) and "$" in v for v in c.get("position", [])):
            continue
        assert c == ca[cid], cid
        f = ((c.get("geometry") or {}).get("mesh") or {}).get("file")
        if f:
            assert (P / f).read_bytes() == (A / f).read_bytes(), cid
    # U11.1/T129: a joint whose location or pivot is a span expression moves with the span; the rest must match
    ja = {a["id"]: a for a in aa["attachments"]}
    for a in pa["attachments"]:
        if any(isinstance(v, str) and "$" in v for v in [*a["location"], *(a.get("articulation") or {}).get("pivot", [])]):
            continue
        assert a == ja[a["id"]], a["id"]
    assert [a["id"] for a in pa["attachments"]] == [a["id"] for a in aa["attachments"]]


def _demo_copy(tmp_path):
    d = tmp_path / "concept-a-param"
    shutil.copytree(P, d)
    return d


def _stall(card):
    msg = next(x for x in _rows(card) if x.check_id == "T3.stall").message
    return float(msg.split("stall ")[1].split(" m/s")[0])


def test_demo_span_change_regenerates(tmp_path):
    d = _demo_copy(tmp_path)
    before = load_design(d)
    v0 = _mesh(before, "wng-001").volume
    stall0 = _stall(validate(before))
    n0 = len(yaml.safe_load((d / "CHANGELOG.yaml").read_text(encoding="utf-8")))   # U11.1/T129: the file already holds the conversion entries
    r = call("design.set", path=str(d), key="parameters.span_mm", value=DEMO_VALUE, why="demo")
    assert r.ok, r.messages
    reg = r.data["regenerated"]
    # U11.1/T129: the fin tubes are regenerated too (their centre follows span_mm)
    assert sorted(reg["components"]) == ["fin-001-l", "fin-001-r", "wng-001", "wng-002"]
    after = load_design(d)
    dm = {c: v["mass_g"][1] - v["mass_g"][0] for c, v in reg["components"].items()}
    assert dm["wng-002"] == pytest.approx(2.205, abs=0.02)
    dens = after.data["materials"]["xps-tape-lumped"]["density_g_cm3"]
    dv = _mesh(after, "wng-001").volume - v0
    assert dm["wng-001"] == pytest.approx(dens * dv / 1000, abs=0.02)
    assert 4 <= dm["wng-001"] <= 6
    m0, m1 = reg["mass_g"]
    assert m1 - m0 == pytest.approx(sum(dm.values()), abs=0.02)
    xs = {c: _mesh(after, c).center_mass[0] for c in dm}
    expect = (m0 * reg["cg_mm"][0][0] + sum(dm[c] * xs[c] for c in dm)) / (m0 + sum(dm.values()))
    assert reg["cg_mm"][1][0] == pytest.approx(expect, abs=0.01)
    for c in ("wng-001", "wng-002"):   # U11.1/T129: the tubes end at span/2 - 70, not at the wing tips
        b = _mesh(after, c).bounds
        assert (b[0][1], b[1][1]) == pytest.approx((-470, 470), abs=0.05)
    assert _comp(after, "wng-001")["planform"]["lifting_surface"]["span"] == 940
    entries = yaml.safe_load((d / "CHANGELOG.yaml").read_text(encoding="utf-8"))
    assert len(entries) == n0 + 1
    e = entries[-1]
    assert (e["key"], e["old"], e["new"]) == ("parameters.span_mm", 900, 940)
    assert sorted(e["regenerated"]) == ["fin-001-l", "fin-001-r", "wng-001", "wng-002"]
    card = validate(after)
    assert _stall(card) < stall0
    assert compare(snapshot(card), read_baseline(d))["regressions"] == EXPECTED_REGRESSIONS


def test_sweep_over_span(tmp_path, monkeypatch):
    d = _demo_copy(tmp_path)
    monkeypatch.setattr("hangar.ops.edit.SWEEP_ROOT", tmp_path / ".sweeps")
    r = call("design.sweep", path=str(d), key="parameters.span_mm", values=["860", "900", "940"])
    assert r.ok, r.messages
    ms = [x["mass_g"] for x in r.data["rows"]]
    assert len(ms) == 3 and ms[0] < ms[1] < ms[2]
    assert ms[1] == pytest.approx(mass_properties(load_design(P))["mass_g"], abs=0.01)
