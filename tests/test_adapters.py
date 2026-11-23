"""Tool adapters (U2.3): one contract, a missing tool is a SKIP with its fix command."""
from __future__ import annotations

import json
import shutil
import sys
import types

import numpy as np
import pytest
import trimesh
from click.testing import CliRunner

import hangar.fea as fea
from hangar import adapters
from hangar.adapters.opencae import OpenCAE
from hangar.checks import validate
from hangar.cli import cli
from hangar.design import REPO_ROOT, load_design
from hangar.ops import call, registry

CA = str(REPO_ROOT / "tests" / "fixtures" / "concept-a-frozen")
FOUND = {"python": "py", "root": "R", "found": True, "how": "test"}


def _copy_ca(tmp_path):
    dst = tmp_path / "concept-a"
    shutil.copytree(CA, dst, ignore=shutil.ignore_patterns("fea"))
    return dst


def test_missing_tool_is_skip_with_fix(monkeypatch, tmp_path):
    monkeypatch.setattr(OpenCAE, "available",
                        lambda self: (False, "run: plane fea setup --opencae-python X --opencae-root Y"))
    r = call("fea.run", path=CA, part="wng-004-l")
    assert r.ok and r.skipped == ["wng-004-l"]
    assert "plane fea setup" in r.messages[0]
    assert r.changed_files == []
    assert r.data["status"] == "SKIP"
    dst = _copy_ca(tmp_path)
    card = validate(load_design(dst / "plane.yaml"))
    assert card.accepted is False
    rows = [c for t in card.tiers for c in t.results if c.check_id == "T2.fea_strength"]
    assert any(c.status == "SKIP" for c in rows)


def test_doctor_lists_every_adapter():
    r = call("tools.doctor")
    rows = r.data["adapters"]
    assert {a["name"] for a in rows} == {"opencae", "mujoco", "aerosandbox", "blender", "sitl", "davinci"}
    for a in rows:
        assert {"name", "available", "planned", "status", "detail"} <= set(a)
        if not a["available"]:
            assert a["detail"]
    assert r.ok


def test_doctor_cli_json_is_an_opresult():
    res = CliRunner().invoke(cli, ["tools", "doctor", "--json"])
    assert res.exit_code == 0
    assert len(json.loads(res.output)["data"]["adapters"]) == 6


def test_get_adapter_unknown_name():
    with pytest.raises(KeyError, match="known: opencae"):
        adapters.get_adapter("nope")
    for n in adapters.ADAPTER_NAMES:
        assert isinstance(adapters.get_adapter(n), adapters.Adapter)


def test_davinci_ships_as_skip_with_reason():
    ad = adapters.get_adapter("davinci")
    ok, why = ad.available()
    assert not ok and "not configured" in why
    design = load_design(CA + "/plane.yaml")
    for r in (ad.push(design), ad.pull()):
        assert r.skipped and why in r.messages[0]


def test_mujoco_import_failure_is_skip_with_fix(monkeypatch):
    monkeypatch.setitem(sys.modules, "mujoco", None)
    ad = adapters.get_adapter("mujoco")
    ok, detail = ad.available()
    assert not ok and "pip install" in detail
    assert ad.run(load_design(CA + "/plane.yaml")).skipped


def test_every_unavailable_adapter_skips_never_passes():
    design = load_design(CA + "/plane.yaml")
    for n in adapters.ADAPTER_NAMES:
        ad = adapters.get_adapter(n)
        if not ad.available()[0]:
            r = ad.run(design, part="wng-004-l")
            assert r.skipped
            assert r.messages[0] == ad.available()[1]
            assert r.data["status"] == "SKIP"


def test_opencae_solve_job_runs_the_runner_by_path(monkeypatch):
    monkeypatch.setattr(fea, "find_opencae", lambda *a, **k: dict(FOUND))

    def fake_run(*args, **kwargs):
        assert args[0][1] == str(fea.RUNNER)
        assert kwargs["env"]["PYTHONPATH"].startswith("R")
        job = json.loads(open(args[0][2]).read())
        with open(job["out"], "w") as f:
            json.dump({"cases": [{"case": "tip", "max_displacement_mm": 1.0}], "error": None}, f)
        return types.SimpleNamespace(stdout="", stderr="", returncode=0)

    monkeypatch.setattr("hangar.adapters.opencae.subprocess.run", fake_run)
    res = OpenCAE().solve_job({"name": "x"})
    assert res["cases"][0]["max_displacement_mm"] == 1.0


@pytest.mark.skipif(not fea.find_opencae()["found"], reason="OpenCAE not set up on this machine")
def test_fea_results_identical_through_adapter(tmp_path):
    b = trimesh.creation.box(extents=[200, 20, 20])
    b.apply_translation([100, 0, 0])
    b.export(tmp_path / "beam.stl")
    pts, _ = trimesh.sample.sample_surface_even(b, 20000, seed=1)
    job = {"name": "cantilever", "stl": str(tmp_path / "beam.stl"), "material_id": "mat_steel",
           "mesh": {"size_max": 4.0, "order": 2}, "select_tol_mm": 0.6, "singularity_band_mm": 20.0,
           "supports": [{"name": "root", "points": pts[np.abs(pts[:, 0]) < 0.05].tolist()}],
           "cases": [{"name": "tip", "loads": [{"name": "tip", "points": pts[np.abs(pts[:, 0] - 200) < 0.05].tolist(),
                                                "force": [0, 0, -1000.0], "point": [200, 0, 0]}]}],
           "force_direct": False, "mesher": None}
    res = OpenCAE().solve_job(job)
    assert res["error"] is None
    assert res["cases"][0]["max_displacement_mm"] == pytest.approx(1.0, rel=0.02)
    assert res["cases"][0]["equilibrium_ok"]


def test_fea_run_op_writes_a_record_through_the_adapter(monkeypatch, tmp_path):
    dst = _copy_ca(tmp_path)
    monkeypatch.setattr(fea, "find_opencae", lambda *a, **k: dict(FOUND))
    monkeypatch.setattr(OpenCAE, "available", lambda self: (True, "fake"))
    fake = {"error": None, "opencae_version": "fake", "cases": [{
        "case": "landing", "max_von_mises_away_mpa": 2.0, "max_von_mises_mpa": 3.0, "max_displacement_mm": 0.01,
        "nodes": 100, "mesh_size_max_mm": 1.0, "equilibrium_ok": True, "load_on_clamped_faces_n": [0, 0, 0],
        "applied_force_n": [0, 0, 10], "max_von_mises_away_location": [0, 0, 0]}]}
    monkeypatch.setattr(OpenCAE, "solve_job", lambda self, job, oc=None, log=print: fake)
    r = call("fea.run", path=str(dst), part="ger-001-ll")
    assert r.ok
    assert r.data["results"][0]["part"] == "ger-001-ll"
    assert len(r.changed_files) == 1 and r.changed_files[0].endswith("fea/ger-001-ll.json")
    written = json.loads((dst / "fea" / "ger-001-ll.json").read_text())
    assert written["hash"] == fea.part_hash(load_design(dst / "plane.yaml"), "ger-001-ll")


def test_fea_run_all_skips_every_eligible_part_when_missing(monkeypatch):
    monkeypatch.setattr(OpenCAE, "available", lambda self: (False, "x"))
    assert call("fea.run", path=CA, all_=True).skipped == fea.eligible_parts(load_design(CA + "/plane.yaml"))


def test_fea_plan_op_matches_engine():
    r = call("fea.plan", path=CA, part="cge-001")
    assert sorted(s["other"] for s in r.data["meta"]["supports"]) == ["cge-004", "cge-005-l", "cge-005-r"]


def test_fea_run_bad_input_is_exit_2():
    assert call("fea.run", path=CA, part="nope").exit_code == 2
    assert call("fea.run", path=CA).exit_code == 2


def test_plane_fea_group_and_legacy_alias():
    res = CliRunner().invoke(cli, ["fea", "--help"])
    assert res.exit_code == 0
    for w in ("plan", "run", "setup"):
        assert w in res.output
    assert {"fea.plan", "fea.run", "fea.setup", "tools.doctor"} <= set(registry())
    r = CliRunner().invoke(cli, ["fea", CA, "--plan", "--part", "cge-001"])
    assert r.exit_code == 0 and "cge-004" in r.output
    r = CliRunner().invoke(cli, ["fea", "run", CA, "--part", "nope", "--json"])
    assert r.exit_code == 2


def test_fea_run_writes_no_job_json_of_its_own(monkeypatch, tmp_path):  # T23: the adapter's solve_job writes job.json once
    from pathlib import Path
    dst = _copy_ca(tmp_path)
    monkeypatch.setattr(fea, "find_opencae", lambda *a, **k: dict(FOUND))
    monkeypatch.setattr(OpenCAE, "available", lambda self: (True, "fake"))
    fake = {"error": None, "opencae_version": "fake", "cases": [{
        "case": "landing", "max_von_mises_away_mpa": 2.0, "max_von_mises_mpa": 3.0, "max_displacement_mm": 0.01,
        "nodes": 100, "mesh_size_max_mm": 1.0, "equilibrium_ok": True, "load_on_clamped_faces_n": [0, 0, 0],
        "applied_force_n": [0, 0, 10], "max_von_mises_away_location": [0, 0, 0]}]}
    seen = {}

    def solve(self, job, oc=None, log=print):
        seen["job_json_next_to_stl"] = (Path(job["stl"]).parent / "job.json").exists()
        return fake

    monkeypatch.setattr(OpenCAE, "solve_job", solve)
    assert call("fea.run", path=str(dst), part="ger-001-ll").ok
    assert seen == {"job_json_next_to_stl": False}


def test_fea_module_has_no_unused_imports():  # T23
    import ast
    from pathlib import Path
    tree = ast.parse(Path(fea.__file__).read_text(encoding="utf-8"))
    imported = {(a.asname or a.name).split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    assert imported - used == set()
