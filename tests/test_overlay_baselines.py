"""U13.7-1: baselines and FEA hashes/runs never depend on the local CAD overlay (synthetic overlay only)."""
from __future__ import annotations

import contextlib
import copy
import math
from pathlib import Path

import pytest
import trimesh
import yaml
from click.testing import CliRunner

import hangar.cli
from hangar import fea, geometry
from hangar.design import Design
from hangar.geom import library, overlay

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "parts"
BASE = Path(__file__).parent / "fixtures" / "gates-base.yaml"
REPO = Path(__file__).resolve().parents[1]
PART = "test-servo"
NOTE = "CAD overlay ignored here"


@pytest.fixture(autouse=True)
def lib(monkeypatch):
    monkeypatch.setattr(library, "PARTS_DIR", FIXTURE_DIR)


def ov(tmp_path, monkeypatch):
    root = tmp_path / "ov"
    (root / PART).mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("PLANE_CAD_OVERLAY", str(root))
    trimesh.creation.box((20, 10, 22)).export(root / PART / "model.stl")
    (root / PART / "overlay.yaml").write_text(
        yaml.safe_dump({"file": "model.stl", "licence": "synthetic test"}), encoding="utf-8")
    return root


def servo_design() -> Design:
    data = copy.deepcopy(yaml.safe_load(BASE.read_text(encoding="utf-8")))
    data["schema_version"] = "1.2"
    esc = next(c for c in data["components"] if c["id"] == "esc")
    del esc["geometry"]["box"]
    esc["geometry"] = {"generator": "library_part", "params": {"part": PART}}
    return Design(data, path=BASE)


def test_forced_off_semantics(tmp_path, monkeypatch):
    ov(tmp_path, monkeypatch)
    assert overlay.status(PART)["state"] == "present"
    with overlay.forced_off():
        assert overlay.overlay_root() is None
        assert overlay.status(PART)["state"] == "absent"
        assert overlay.mesh(PART) is None
        assert overlay.overlay_configured() is True
        with overlay.forced_off():
            assert overlay.overlay_root() is None
        assert overlay.overlay_root() is None
    assert overlay.status(PART)["state"] == "present"
    with pytest.raises(RuntimeError):
        with overlay.forced_off():
            raise RuntimeError("x")
    assert overlay.status(PART)["state"] == "present"


def test_geometry_really_differs_with_overlay(tmp_path, monkeypatch):
    ov(tmp_path, monkeypatch)
    esc = next(c for c in servo_design().components if c["id"] == "esc")

    def vol():
        parts = geometry.component_parts(copy.deepcopy(esc), tmp_path)
        return abs(float(parts[0].volume))

    assert vol() == pytest.approx(4400, rel=1e-6)
    with overlay.forced_off():
        assert vol() == pytest.approx(math.pi * 25 * 20, rel=0.01)


def test_part_hash_ignores_the_overlay(tmp_path, monkeypatch):
    monkeypatch.setenv("PLANE_CAD_OVERLAY", "off")
    off = fea.part_hash(servo_design(), "esc")
    ov(tmp_path, monkeypatch)
    assert fea.part_hash(servo_design(), "esc") == off


def test_fea_entry_points_force_the_overlay_off(tmp_path, monkeypatch):
    ov(tmp_path, monkeypatch)
    count = [0]

    @contextlib.contextmanager
    def spy():
        count[0] += 1
        yield

    monkeypatch.setattr(fea.overlay, "forced_off", spy)
    d = servo_design()
    fea.part_hash(d, "esc")
    assert count[0] == 1
    try:
        fea.run(d, "esc")
    except Exception:
        pass
    assert count[0] >= 2
    n = count[0]
    fea.tier2_fea(d)
    assert count[0] >= n + 1


def _two(tmp_path):
    a, b = tmp_path / "a" / "sd", tmp_path / "b" / "sd"
    for p in (a, b):
        p.mkdir(parents=True)
        (p / "plane.yaml").write_text(yaml.safe_dump(servo_design().data, sort_keys=False), encoding="utf-8")
    return a, b


def _out(r):
    return (r.output or "") + (getattr(r, "stderr", "") or "")


def test_baseline_update_is_the_same_with_and_without_overlay(tmp_path, monkeypatch):
    a, b = _two(tmp_path)
    ov(tmp_path, monkeypatch)
    ra = CliRunner().invoke(hangar.cli.cli, ["baseline", "update", str(a)])
    monkeypatch.setenv("PLANE_CAD_OVERLAY", "off")
    rb = CliRunner().invoke(hangar.cli.cli, ["baseline", "update", str(b)])
    assert ra.exit_code == 0, _out(ra)
    assert rb.exit_code == 0, _out(rb)
    assert (a / "baseline.json").read_bytes() == (b / "baseline.json").read_bytes()
    assert NOTE in _out(ra)
    assert NOTE not in _out(rb)


def test_baseline_check_note(tmp_path, monkeypatch):
    a, b = _two(tmp_path)
    monkeypatch.setenv("PLANE_CAD_OVERLAY", "off")
    assert CliRunner().invoke(hangar.cli.cli, ["baseline", "update", str(a)]).exit_code == 0
    ov(tmp_path, monkeypatch)
    r = CliRunner().invoke(hangar.cli.cli, ["baseline", "check", str(a)])
    assert r.exit_code == 0, _out(r)
    assert NOTE in _out(r)


def test_doc_paragraph():
    text = (REPO / "docs" / "cad-overlay.md").read_text(encoding="utf-8")
    assert "## Baselines and FEA" in text
    assert NOTE in text
