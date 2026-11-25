"""U12.5-1: local CAD overlay loader, config, parts show status, library_part geometry (synthetic meshes only)."""
from __future__ import annotations

import copy
import importlib.util
import math
from pathlib import Path

import pytest
import trimesh
import yaml

from hangar import geometry
from hangar.geom import library, overlay
from hangar.ops import call, registry

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "parts"
PART = "test-servo"


@pytest.fixture(autouse=True)
def lib(monkeypatch):
    monkeypatch.setattr(library, "PARTS_DIR", FIXTURE_DIR)


def ov(tmp_path, monkeypatch, manifest=None, mesh=None, name="model.stl"):
    root = tmp_path / "ov"
    (root / PART).mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("PLANE_CAD_OVERLAY", str(root))
    (mesh if mesh is not None else trimesh.creation.box((20, 10, 22))).export(root / PART / name)
    m = {"file": name, "licence": "synthetic test"} if manifest is None else manifest
    (root / PART / "overlay.yaml").write_text(yaml.safe_dump(m), encoding="utf-8")
    return root


def test_absent_by_default_and_off(tmp_path, monkeypatch):
    assert overlay.status(PART)["state"] == "absent" and overlay.mesh(PART) is None
    (tmp_path / "empty").mkdir()
    monkeypatch.setenv("PLANE_CAD_OVERLAY", str(tmp_path / "empty"))
    assert overlay.status(PART)["state"] == "absent" and overlay.mesh(PART) is None


def test_present_loads_and_recentres(tmp_path, monkeypatch):
    ov(tmp_path, monkeypatch)
    st = overlay.status(PART)
    assert st["state"] == "present"
    m = overlay.mesh(PART)
    assert list(m.extents) == pytest.approx([20, 10, 22], abs=1e-6)
    assert list(m.bounds.mean(axis=0)) == pytest.approx([0, 0, 0], abs=1e-6)
    assert st["fit"] == pytest.approx([20 / 23, 10 / 12, 22 / 24])
    assert st["envelope_mm"] == [23, 12, 24]


def test_matrix_and_units(tmp_path, monkeypatch):
    ov(tmp_path, monkeypatch, {"file": "model.stl", "licence": "synthetic test",
                               "matrix": [0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0]})
    assert list(overlay.mesh(PART).extents) == pytest.approx([10, 22, 20], abs=1e-6)
    ov(tmp_path / "b", monkeypatch, {"file": "model.stl", "licence": "synthetic test", "units": "m"},
       mesh=trimesh.creation.box((0.02, 0.01, 0.022)))
    assert list(overlay.mesh(PART).extents) == pytest.approx([20, 10, 22], abs=1e-6)


def test_unusable_cases(tmp_path, monkeypatch):
    def reason(sub, manifest, name="model.stl"):
        ov(tmp_path / sub, monkeypatch, manifest, name=name)
        assert overlay.mesh(PART) is None
        st = overlay.status(PART)
        assert st["state"] == "unusable"
        return st["reason"]

    base = {"file": "model.stl", "licence": "synthetic test"}
    assert "licence" in reason("a", {"file": "model.stl"})
    assert "not found" in reason("b", {**base, "file": "nope.stl"})
    ov(tmp_path / "c", monkeypatch, {**base, "file": "model.step"})
    (tmp_path / "c" / "ov" / PART / "model.step").write_text("", encoding="utf-8")
    real_find_spec = importlib.util.find_spec
    monkeypatch.setattr(importlib.util, "find_spec", lambda n, *a: None if n == "cascadio" else real_find_spec(n, *a))
    assert overlay.mesh(PART) is None and overlay.status(PART)["state"] == "unusable"
    assert "STEP needs cascadio" in overlay.status(PART)["reason"]
    monkeypatch.setattr(importlib.util, "find_spec", real_find_spec)
    assert "units" in reason("d", {**base, "units": "cm"})
    assert "size does not match" in reason("e", {**base, "units": "m"})


def test_multi_body_unmerged_mesh_is_united(tmp_path, monkeypatch):
    a = trimesh.creation.box((10, 10, 10))
    b = trimesh.creation.box((10, 10, 10))
    b.apply_translation((10, 0, 0))
    both = trimesh.util.concatenate([a, b])
    ov(tmp_path, monkeypatch, mesh=both)
    real = library.load_part
    monkeypatch.setattr(library, "load_part", lambda i: {**real(i), "dimensions_mm": [20, 10, 10]})
    m = overlay.mesh(PART)
    assert m is not None and m.is_watertight and m.is_volume
    assert float(m.volume) == pytest.approx(2000, rel=1e-6)
    assert list(m.extents) == pytest.approx([20, 10, 10], abs=1e-6)


COMP = {"id": "s", "type": "servo", "geometry": {"generator": "library_part", "params": {"part": PART}},
        "position": [0, 0, 0], "mass_g": 9}


def test_library_part_uses_overlay_when_present(tmp_path, monkeypatch):
    root = ov(tmp_path, monkeypatch)

    def vol():
        parts = geometry.component_parts(copy.deepcopy(COMP), tmp_path)
        assert len(parts) == 1
        return abs(float(parts[0].volume))

    assert vol() == pytest.approx(4400, rel=1e-6)
    monkeypatch.setenv("PLANE_CAD_OVERLAY", "off")
    assert vol() == pytest.approx(math.pi * 25 * 20, rel=0.01)
    monkeypatch.setenv("PLANE_CAD_OVERLAY", str(root))
    assert vol() == pytest.approx(4400, rel=1e-6)


def test_mass_comes_from_the_committed_part(tmp_path, monkeypatch):
    from hangar.ops import parts
    off = parts.show(PART)
    assert off.data["mass_g"] == 9.0 and off.data["overlay"]["state"] == "absent"
    ov(tmp_path, monkeypatch)
    res = parts.show(PART)
    assert res.data["mass_g"] == 9.0 and res.data["overlay"]["state"] == "present"
    text = registry()["parts.show"].render(res)
    assert "overlay: present" in text and "synthetic test" in text


def test_config_file_and_env_precedence(tmp_path, monkeypatch):
    (tmp_path / "ov").mkdir()
    cfg = tmp_path / "cfg.json"
    cfg.write_text('{"path": "%s"}' % (tmp_path / "ov").as_posix(), encoding="utf-8")
    monkeypatch.setattr(overlay, "CONFIG_FILE", cfg)
    monkeypatch.delenv("PLANE_CAD_OVERLAY")
    assert overlay.overlay_root() == tmp_path / "ov"
    monkeypatch.setenv("PLANE_CAD_OVERLAY", "off")
    assert overlay.overlay_root() is None
    monkeypatch.delenv("PLANE_CAD_OVERLAY")
    monkeypatch.setattr(overlay, "CONFIG_FILE", tmp_path / "missing.json")
    if (Path.home() / "parts-cad").exists():
        assert overlay.overlay_root() == Path.home() / "parts-cad"
    else:
        assert overlay.overlay_root() is None


def test_step_loads_when_cascadio_present(tmp_path, monkeypatch):
    pytest.importorskip("cascadio")
    from stepbox import box_step
    root = ov(tmp_path, monkeypatch, {"file": "model.step", "licence": "synthetic test"})
    (root / PART / "model.step").write_text(box_step(20, 10, 22), encoding="utf-8")
    assert overlay.status(PART)["state"] == "present"
    assert list(overlay.mesh(PART).extents) == pytest.approx([20, 10, 22], abs=1e-3)
