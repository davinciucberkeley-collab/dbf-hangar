"""U4.38-2: overlay-built outputs are local-only and refused on tracked paths (synthetic overlay, temp git repos)."""
from __future__ import annotations

import copy
import shutil
import subprocess
from pathlib import Path

import pytest
import trimesh
import yaml
from click.testing import CliRunner

import hangar.cli
from hangar.design import Design, load_design
from hangar.export import export_glb, export_stl
from hangar.geom import library, overlay
from hangar.index import design_entry
from hangar.sim import export_mjcf

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "parts"
BASE = Path(__file__).parent / "fixtures" / "gates-base.yaml"
REPO = Path(__file__).resolve().parents[1]
PART = "test-servo"
MARKER = "LOCAL-ONLY-cad-overlay.txt"


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


def test_output_allowed_cases(tmp_path, monkeypatch):
    r = repo(tmp_path, monkeypatch)
    assert overlay.output_allowed(tmp_path / "out" / "a.glb")[0] is True
    assert overlay.output_allowed(r / "local" / "a.glb")[0] is True
    assert overlay.output_allowed(r / "designs" / "x" / "a.glb")[0] is False
    assert overlay.output_allowed(r / "designs" / "x" / "f.txt")[0] is False
    assert overlay.output_allowed(r / "other" / "a.glb")[0] is False


def test_no_git_refuses_inside_repo(tmp_path, monkeypatch):
    r = repo(tmp_path, monkeypatch)

    def boom(*a, **k):
        raise FileNotFoundError("git")

    monkeypatch.setattr(overlay.subprocess, "run", boom)
    ok, why = overlay.output_allowed(r / "local" / "a.glb")
    assert ok is False and "cannot ask git" in why
    assert overlay.output_allowed(tmp_path / "out" / "a.glb")[0] is True


def test_export_glb_refused_into_tracked_path(tmp_path, monkeypatch):
    r = repo(tmp_path, monkeypatch)
    ov(tmp_path, monkeypatch)
    target = r / "designs" / "x" / "m.glb"
    with pytest.raises(overlay.OverlayOutputRefused) as e:
        export_glb(servo_design(), target)
    assert PART in str(e.value) and "local-only" in str(e.value)
    assert not target.exists()


def test_export_glb_allowed_outside_and_marked(tmp_path, monkeypatch):
    r = repo(tmp_path, monkeypatch)
    ov(tmp_path, monkeypatch)
    d = servo_design()
    export_glb(d, tmp_path / "out" / "m.glb")
    assert (tmp_path / "out" / "m.glb").is_file()
    assert PART in (tmp_path / "out" / MARKER).read_text(encoding="utf-8")
    export_glb(d, r / "local" / "m.glb")
    assert (r / "local" / "m.glb").is_file() and (r / "local" / MARKER).is_file()


def test_no_overlay_no_guard(tmp_path, monkeypatch):
    r = repo(tmp_path, monkeypatch)
    export_glb(servo_design(), r / "designs" / "x" / "m.glb")
    assert (r / "designs" / "x" / "m.glb").is_file()
    assert not (r / "designs" / "x" / MARKER).exists()


def test_export_stl_and_mjcf_guarded(tmp_path, monkeypatch):
    r = repo(tmp_path, monkeypatch)
    ov(tmp_path, monkeypatch)
    d = servo_design()
    with pytest.raises(overlay.OverlayOutputRefused):
        export_stl(d, r / "designs" / "x" / "stl")
    with pytest.raises(overlay.OverlayOutputRefused):
        export_mjcf(d, r / "designs" / "x" / "m.xml")
    assert not (r / "designs" / "x" / "stl").exists() and not (r / "designs" / "x" / "m.xml").exists()
    assert export_stl(d, tmp_path / "out" / "stl")
    assert export_mjcf(d, tmp_path / "out" / "m.xml").is_file()


def test_design_entry_marks_local_only(tmp_path, monkeypatch):
    ov(tmp_path, monkeypatch)
    entry = design_entry(servo_design(), tmp_path / "out")
    assert entry["local_only"] == [PART] and (tmp_path / "out" / MARKER).is_file()
    monkeypatch.setenv("PLANE_CAD_OVERLAY", "off")
    assert "local_only" not in design_entry(servo_design(), tmp_path / "out2")


def test_build_index_refuses_tracked_out_when_overlay_used(tmp_path, monkeypatch):
    r = repo(tmp_path, monkeypatch)
    ov(tmp_path, monkeypatch)
    folder = tmp_path / "d" / "servo-d"
    folder.mkdir(parents=True)
    data = servo_design().data
    data["id"] = "servo-d"
    (folder / "plane.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")
    monkeypatch.setattr(hangar.cli, "list_designs", lambda: [folder / "plane.yaml"])
    monkeypatch.setattr(hangar.cli, "DESIGNS_DIR", tmp_path / "d")
    out = r / "designs" / "x" / "o"
    res = CliRunner().invoke(hangar.cli.cli, ["build-index", "--out", str(out)])
    assert res.exit_code != 0
    assert PART in res.output and "outside the repository" in res.output
    assert not list(out.glob("*"))


def test_real_repo_paths():
    if shutil.which("git") is None:
        pytest.skip("git not on PATH")
    assert overlay.output_allowed(REPO / "designs" / "concept-a" / "m.glb")[0] is False
    assert overlay.output_allowed(REPO / "viewer" / "data" / "m.glb")[0] is True


def test_default_index_entry_unchanged(tmp_path):
    d = load_design(REPO / "designs" / "example-tailsitter-wing")
    assert "local_only" not in design_entry(d, tmp_path / "idx")
