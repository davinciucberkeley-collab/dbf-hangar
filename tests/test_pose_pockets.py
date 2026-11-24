"""U4.25: wing_panel cut pockets follow the swept poses of moving neighbours (hand numbers from the brief)."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from hangar.checks import _overlap_volume
from hangar.design import DESIGNS_DIR, load_design, load_standards
from hangar.geom import registry
from hangar.geom.kernel import box
from hangar.geom.registry import get, validate_params
from hangar.geometry import posed_component_parts

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "pdl-gen"
DAT = "airfoils/diamond.dat"


def wing(**kw):
    p = {"airfoil_file": DAT, "span": 400, "root_chord": 100, "tip_chord": 100, "part": "core", "hinge_frac": 0.75}
    p.update(kw)
    return p


def vol(m):
    return abs(float(m.volume))


def _build(p, base):
    return registry.build_component({"id": "t", "geometry": {"generator": "wing_panel", "params": p}}, base)


def _stage(tmp_path):
    (tmp_path / "airfoils").mkdir(exist_ok=True)
    shutil.copy(FIXTURE_DIR / DAT, tmp_path / DAT)
    box((20, 30, 10), (100, 0, 0)).export(tmp_path / "cutter.stl")


def test_cut_poses_hull_over_neutral_and_posed(tmp_path):
    _stage(tmp_path)
    p = wing(root_chord=200, tip_chord=200, cut_files=["cutter.stl"],
             cut_poses=[{"file": "cutter.stl", "matrices": [[1, 0, 0, 35, 0, 1, 0, 0, 0, 0, 1, 0]]}])
    (m,) = _build(p, tmp_path)
    assert vol(m) == pytest.approx(700000 - 16500, rel=1e-6)
    p["cut_poses"] = [{"file": "cutter.stl", "matrices": [[0, -1, 0, 100, 1, 0, 0, -100, 0, 0, 1, 0]]}]
    (m,) = _build(p, tmp_path)
    assert vol(m) == pytest.approx(691500, rel=1e-6)


def test_cut_poses_default_is_empty_and_unchanged(tmp_path):
    _stage(tmp_path)
    (m,) = _build(wing(root_chord=200, tip_chord=200, cut_files=["cutter.stl"]), tmp_path)
    assert vol(m) == pytest.approx(694000, rel=1e-6)
    msgs = validate_params(get("wing_panel"), wing(cut_sweep="sideways"))
    assert any("cut_sweep" in s for s in msgs)
    msgs = validate_params(get("wing_panel"), wing(cut_files=["a.stl"], cut_poses=[{"file": "b.stl", "matrices": []}]))
    assert any("cut_poses" in s for s in msgs)
    msgs = validate_params(get("wing_panel"), wing(cut_files=["a.stl"], cut_poses=[{"file": "a.stl", "matrices": [[1, 2]]}]))
    assert any("cut_poses" in s for s in msgs)


def _flap_design(tmp_path, sweep):
    _stage(tmp_path)
    (tmp_path / "meshes").mkdir(exist_ok=True)
    box((20, 30, 10), (100, 0, 0)).export(tmp_path / "meshes" / "flap.stl")
    params = {"airfoil_file": DAT, "span": 400, "root_chord": 200, "tip_chord": 200, "part": "core",
              "cut_files": ["meshes/flap.stl"]}
    if sweep:
        params["cut_sweep"] = sweep
    d = {"schema_version": "1.2", "id": "pose-pocket", "name": "Pose pocket fixture", "status": "concept",
         "morphology": {"lift": "flying-wing", "vtol_method": "none"}, "root": "wing",
         "components": [
             {"id": "wing", "type": "structure", "geometry": {"generator": "wing_panel", "params": params},
              "position": [0, 0, 0], "mass_model": {"density_g_cm3": 0.05}},
             {"id": "flap", "type": "structure", "geometry": {"mesh": {"file": "meshes/flap.stl"}},
              "position": [0, 0, 0], "mass_g": 1}],
         "attachments": [{"id": "hinge", "parent": "wing", "child": "flap", "method": "hinge", "location": [100, 0, 0],
                          "rated_load_n": 1,
                          "articulation": {"type": "revolute", "pivot": [100, 0, 0], "axis": [0, 0, 1],
                                           "range_deg": [-90, 90]}}]}
    (tmp_path / "plane.yaml").write_text(yaml.safe_dump(d, sort_keys=False))
    return load_design(tmp_path)


def test_resolver_derives_poses_from_the_joints(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir(), b.mkdir()
    swept = _flap_design(a, None)
    plain = _flap_design(b, "none")
    assert not swept.resolve_errors
    wp = swept.component("wing")["geometry"]["params"]
    (entry,) = wp["cut_poses"]
    assert entry["file"] == "meshes/flap.stl" and len(entry["matrices"]) == 12
    assert all(len(m) == 12 for m in entry["matrices"])
    assert "cut_poses" not in swept.raw["components"][0]["geometry"]["params"]
    assert "cut_poses" not in plain.component("wing")["geometry"]["params"]
    vs = sum(vol(m) for m in posed_component_parts(swept, {})["wing"])
    vp = sum(vol(m) for m in posed_component_parts(plain, {})["wing"])
    assert vs < vp
    limit = load_standards()["geometry"]["interference_max_mm3"]["value"]
    for ang in range(-90, 91, 15):
        posed = posed_component_parts(swept, {"hinge": float(ang)})
        assert _overlap_volume(posed["wing"], posed["flap"]) <= limit, ang
    posed = posed_component_parts(plain, {"hinge": 30.0})
    assert _overlap_volume(posed["wing"], posed["flap"]) > limit


def test_mechanism_pose_angles_matches_the_t6_picks():
    from hangar.gates.mechanisms import mechanism_pose_angles
    design = load_design(DESIGNS_DIR / "concept-a")
    got = mechanism_pose_angles(design, 1.0)
    assert len(got) == 2 * 31
    assert got[0] == {"E-MEC-02": -15.0, "E-WNG-10": pytest.approx(19.95)}
    assert got[31] == {"E-MEC-07": -15.0, "E-WNG-11": pytest.approx(-19.95)}


def test_existing_designs_build_identically():
    for name in ("concept-a", "example-tailsitter-wing"):
        design = load_design(DESIGNS_DIR / name)
        for c in design.components:
            assert "cut_poses" not in (c.get("geometry") or {}).get("params", {})


def test_merged_poses_cover_every_sampled_pose(tmp_path):
    """The merged cutter set stays within 0.05 mm (farthest vertex) of every T1 and T6 pose, extremes kept."""
    import numpy as np
    import trimesh
    from hangar.checks import _configurations
    from hangar.gates import load_gate_thresholds
    from hangar.gates.mechanisms import mechanism_pose_angles
    from hangar.geom.sweeps import MERGE_MM, swept_cut_poses
    from hangar.geometry import pose_transforms
    design = load_design(DESIGNS_DIR / "concept-a")
    cut = ["meshes/wng-006-r.stl", "meshes/mec-002-r.stl", "meshes/wng-007-r.stl"]
    got = {e["file"]: e["matrices"] for e in swept_cut_poses(design.data, cut, design.base_dir)}
    step = load_standards()["geometry"]["articulation_sweep_step_deg"]["value"]
    configs = [a for _, a in _configurations(design, step)]
    configs += mechanism_pose_angles(design, load_gate_thresholds()["mechanism_contact_step_deg"]["value"])
    n_all = 0
    for f in cut:
        cid = next(c["id"] for c in design.components if (c["geometry"].get("mesh") or {}).get("file") == f)
        v = np.asarray(trimesh.load(design.base_dir / f, force="mesh").vertices)
        kept = [v @ np.array(r).reshape(3, 4)[:, :3].T + np.array(r).reshape(3, 4)[:, 3] for r in got[f]]
        worst, ext = 0.0, 0.0
        for ang in configs:
            t = pose_transforms(design, ang)[cid]
            want = v @ t[:3, :3].T + t[:3, 3]
            if np.abs(want - v).max() < 1e-9:
                continue
            n_all += 1
            worst = max(worst, min(float(np.abs(want - k).max()) for k in kept))
            ext = max(ext, float(np.abs(want - v).max()))
        assert worst <= MERGE_MM + 1e-9, (f, worst)
        assert max(float(np.abs(k - v).max()) for k in kept) == pytest.approx(ext, abs=1e-6)   # extremes kept
        assert len(kept) <= len(configs)
    assert n_all > 0


def test_hull_pocket_covers_union_of_posed_copies():
    import numpy as np
    from hangar.geom import kernel
    b = box((20, 30, 10), (100, 0, 0))
    copies = [b]
    for deg in (0, 15, 30, 45, 60, 75, 90):
        c = b.copy()
        a = np.radians(deg)
        t = np.eye(4)
        t[:2, :2] = [[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]]
        t[:2, 3] = np.array([100, 0]) - t[:2, :2] @ np.array([100, 0])
        c.apply_transform(t)
        copies.append(c)
    import trimesh
    hull = trimesh.convex.convex_hull(np.vstack([c.vertices for c in copies]))
    assert abs(hull.volume) >= abs(kernel.union(copies).volume) - 1e-6
