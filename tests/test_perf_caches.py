"""Performance caches (U4.1): component parts are loaded once per content, posed parts are copied once, design-standards.yaml is parsed once per file version. Each test shows the results are the same as without the cache."""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pytest
import trimesh
import yaml

import hangar.design as design_mod
from hangar.design import load_design, load_standards
from hangar.geometry import clear_parts_cache, component_parts, pose_transforms, posed_component_parts

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def _clean_cache():
    clear_parts_cache()
    yield
    clear_parts_cache()


def _mesh_component() -> dict:
    return {"id": "m", "type": "structure", "mass_g": 1, "geometry": {"mesh": {"file": "m.stl"}}, "position": [0, 0, 0]}


def _box_component(size) -> dict:
    return {"id": "b", "type": "structure", "mass_g": 1, "geometry": {"box": {"size": list(size)}}, "position": [0, 0, 0]}


def _write_stl(folder, size: float, mtime_ns: int) -> None:
    path = folder / "m.stl"
    trimesh.creation.box(extents=[size] * 3).export(path)
    os.utime(path, ns=(mtime_ns, mtime_ns))


def test_mesh_is_loaded_once(tmp_path, monkeypatch):
    _write_stl(tmp_path, 10, 10**18)
    calls = []
    real = trimesh.load
    monkeypatch.setattr(trimesh, "load", lambda *a, **k: (calls.append(1), real(*a, **k))[1])
    c = _mesh_component()
    a = component_parts(c, tmp_path)
    b = component_parts(c, tmp_path)
    assert len(calls) == 1
    assert np.array_equal(a[0].vertices, b[0].vertices)


def test_results_are_independent_copies(tmp_path):
    _write_stl(tmp_path, 10, 10**18)
    c = _mesh_component()
    a = component_parts(c, tmp_path)
    a[0].apply_translation([100, 0, 0])
    b = component_parts(c, tmp_path)
    assert a[0] is not b[0]
    assert np.allclose(b[0].bounds, [[-5, -5, -5], [5, 5, 5]])


def test_changed_mesh_file_is_reloaded(tmp_path):
    _write_stl(tmp_path, 10, 10**18)
    c = _mesh_component()
    assert np.allclose(component_parts(c, tmp_path)[0].bounds, [[-5] * 3, [5] * 3])
    _write_stl(tmp_path, 20, 2 * 10**18)
    assert np.allclose(component_parts(c, tmp_path)[0].bounds, [[-10] * 3, [10] * 3])


def test_changed_component_content_is_not_reused():
    c = _box_component([10, 10, 10])
    assert component_parts(c)[0].volume == pytest.approx(1000)
    c["geometry"]["box"]["size"] = [20, 10, 10]
    assert component_parts(c)[0].volume == pytest.approx(2000)
    c["cavities"] = [{"geometry": {"box": {"size": [2, 2, 2]}}, "position": [0, 0, 0]}]
    assert component_parts(c)[0].volume == pytest.approx(1992, rel=1e-6)


def test_position_is_applied_after_the_cache():
    c = _box_component([20, 10, 10])
    assert np.allclose(component_parts(c)[0].bounds[0], [-10, -5, -5])
    c["position"] = [100, 0, 0]
    assert np.allclose(component_parts(c)[0].bounds[0], [90, -5, -5])


def test_posed_parts_are_copied_once_and_match_the_manual_pose(monkeypatch):
    d = load_design(FIX / "mech-good.yaml")
    angles = {"servo_arm": 10.0, "flap_hinge": 10.0}
    tf = pose_transforms(d, angles)
    expected = {}
    for c in d.components:
        parts = component_parts(c, d.base_dir)
        if not np.allclose(tf[c["id"]], np.eye(4)):
            for p in parts:
                p.apply_transform(tf[c["id"]])
        expected[c["id"]] = parts
    n_parts = sum(len(v) for v in expected.values())
    assert n_parts > 0 and any(not np.allclose(t, np.eye(4)) for t in tf.values())
    calls = []
    real = trimesh.Trimesh.copy
    monkeypatch.setattr(trimesh.Trimesh, "copy", lambda self, *a, **k: (calls.append(1), real(self, *a, **k))[1])
    got = posed_component_parts(d, angles)
    assert len(calls) == n_parts  # one copy per part (in component_parts), none more for moved parts
    assert got.keys() == expected.keys()
    for cid, parts in got.items():
        assert len(parts) == len(expected[cid])
        for a, b in zip(parts, expected[cid]):
            assert np.array_equal(a.vertices, b.vertices) and np.array_equal(a.faces, b.faces)


def test_load_standards_is_parsed_once_per_file_version_and_returns_copies(tmp_path, monkeypatch):
    p = tmp_path / "standards.yaml"
    p.write_text("a: {b: 1}\n", encoding="utf-8")
    os.utime(p, ns=(10**18, 10**18))
    monkeypatch.setattr(design_mod, "STANDARDS_PATH", p)
    calls = []
    real = yaml.safe_load
    monkeypatch.setattr(yaml, "safe_load", lambda *a, **k: (calls.append(1), real(*a, **k))[1])
    first = load_standards()
    first["a"]["b"] = 99
    assert load_standards() == {"a": {"b": 1}}
    assert len(calls) == 1
    p.write_text("a: {b: 2, c: 3}\n", encoding="utf-8")
    os.utime(p, ns=(2 * 10**18, 2 * 10**18))
    assert load_standards() == {"a": {"b": 2, "c": 3}}
    assert len(calls) == 2


def test_load_standards_equals_a_plain_parse_of_the_real_file():
    assert load_standards() == yaml.safe_load(design_mod.STANDARDS_PATH.read_text())
