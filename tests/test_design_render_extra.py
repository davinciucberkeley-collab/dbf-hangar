"""U13.7 (T144): design.render refusals and the missing-matplotlib message. Needs no matplotlib."""
from __future__ import annotations

import copy
import subprocess
import sys
from pathlib import Path

import pytest
import trimesh
import yaml

from hangar import design as design_mod
from hangar.design import Design
from hangar.geom import library, overlay
from hangar.ops import call

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "parts"
BASE = Path(__file__).parent / "fixtures" / "gates-base.yaml"
EXAMPLE_DIR = design_mod.DESIGNS_DIR / "example-tailsitter-wing"
PART = "test-servo"


@pytest.fixture(autouse=True)
def lib(monkeypatch):
    monkeypatch.setattr(library, "PARTS_DIR", FIXTURE_DIR)
    for k in ("GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME"):
        monkeypatch.setenv(k, "t")
    for k in ("GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"):
        monkeypatch.setenv(k, "t@example.com")


def ov(tmp_path, monkeypatch):
    root = tmp_path / "ov"
    (root / PART).mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("PLANE_CAD_OVERLAY", str(root))
    trimesh.creation.box((20, 10, 22)).export(root / PART / "model.stl")
    (root / PART / "overlay.yaml").write_text(
        yaml.safe_dump({"file": "model.stl", "licence": "synthetic test"}), encoding="utf-8")


def repo(tmp_path, monkeypatch) -> Path:
    r = tmp_path / "r"
    r.mkdir()
    run = lambda *a: subprocess.run(["git", "-C", str(r), *a], check=True, capture_output=True)  # noqa: E731
    run("init", "-b", "main")
    (r / ".gitignore").write_text("local/\n", encoding="utf-8")
    (r / "designs" / "x").mkdir(parents=True)
    (r / "designs" / "x" / "f.txt").write_text("x", encoding="utf-8")
    run("add", "-A")
    run("-c", "commit.gpgsign=false", "commit", "-m", "base")
    monkeypatch.setattr(overlay, "REPO_ROOT", r)
    return r


def servo_design() -> Design:
    data = copy.deepcopy(yaml.safe_load(BASE.read_text(encoding="utf-8")))
    data["schema_version"] = "1.2"
    esc = next(c for c in data["components"] if c["id"] == "esc")
    del esc["geometry"]["box"]
    esc["geometry"] = {"generator": "library_part", "params": {"part": PART}}
    return Design(data, path=BASE)


def test_render_refuses_a_tracked_path_for_an_overlay_design(tmp_path, monkeypatch):
    r = repo(tmp_path, monkeypatch)
    ov(tmp_path, monkeypatch)
    (tmp_path / "d").mkdir()
    (tmp_path / "d" / "plane.yaml").write_text(
        yaml.safe_dump(servo_design().data), encoding="utf-8")
    monkeypatch.setattr("hangar.render.render_png",
                        lambda design, out, **kw: Path(out).write_bytes(b"png") or Path(out))

    target = r / "designs" / "x" / "a.png"
    res = call("design.render", path=str(tmp_path / "d"), out=target)
    assert res.ok is False
    msg = " ".join(res.messages)
    assert "local-only" in msg and PART in msg
    assert not target.exists()

    allowed = tmp_path / "out" / "a.png"
    res = call("design.render", path=str(tmp_path / "d"), out=allowed)
    assert res.ok is True, res.messages
    assert allowed.is_file()
    assert (tmp_path / "out" / "LOCAL-ONLY-cad-overlay.txt").is_file()


def test_missing_matplotlib_message(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "matplotlib", None)
    out = tmp_path / "a.png"
    res = call("design.render", path=str(EXAMPLE_DIR), out=out)
    assert res.ok is False
    msg = " ".join(res.messages)
    assert "render failed" in msg
    assert "design render needs matplotlib" in msg
    assert "pip install" in msg
    assert not out.exists()

    from hangar.render import render_png

    with pytest.raises(RuntimeError, match="needs matplotlib"):
        render_png(None, tmp_path / "b.png")
