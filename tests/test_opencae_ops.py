"""U18.1-4: plane opencae run / setup ops. The OpenCAE process is always monkeypatched; none needs OpenCAE installed."""
import json
import shutil
from pathlib import Path

import hangar.fea as fea
import hangar.opencae_cli as opencae_cli
from hangar.design import DESIGNS_DIR
from hangar.ops import call

FIXTURES = Path(__file__).parent / "fixtures" / "opencae"
DOCTOR_TEXT = (FIXTURES / "doctor_no_openfoam.json").read_text(encoding="utf-8")
QUAD_TEXT = (FIXTURES / "quad250_mass_propulsion_structure.json").read_text(encoding="utf-8")


def _design_dir(tmp_path):
    shutil.copytree(DESIGNS_DIR / "example-tailsitter-wing", tmp_path / "d")
    return str(tmp_path / "d" / "plane.yaml")


def _fake_cli(monkeypatch, tmp_path, calls):
    monkeypatch.setattr(opencae_cli, "find_cli", lambda *a, **k: {"python": "py", "root": str(tmp_path), "found": True,
                                                                  "how": "given", "head": "abc1234"})
    monkeypatch.setattr(opencae_cli, "cli_available", lambda: (True, "ok"))
    monkeypatch.setattr(opencae_cli, "doctor", lambda cli: json.loads(DOCTOR_TEXT.replace("\\", "\\\\")))
    monkeypatch.setattr(opencae_cli, "solver_status", lambda doc, environ=None, home=None:
                        {"ccx": (True, "ok"), "cfd": (False, "no CFD solver: test")})

    def fake_run(project_dir, analyses, cli, log=print):
        calls.append(tuple(analyses))
        return {"returncode": 0, "result": json.loads(QUAD_TEXT), "stderr_tail": ""}

    monkeypatch.setattr(opencae_cli, "run_project", fake_run)


def test_run_stores_results(monkeypatch, tmp_path):
    calls = []
    _fake_cli(monkeypatch, tmp_path, calls)
    path = _design_dir(tmp_path)
    r = call("opencae.run", path=path, analyses="mass,propulsion")
    assert r.ok
    assert r.data["status"] == "DONE"
    assert r.data["verdict"] == "conditional"
    stored = tmp_path / "d" / "opencae" / "results.json"
    assert stored.exists()
    rec = json.loads(stored.read_text(encoding="utf-8"))
    assert {"design", "hash", "design_hash", "analyses", "opencae_head", "result"} <= set(rec)
    assert rec["analyses"] == ["mass", "propulsion"]
    assert calls == [("mass", "propulsion")]


def test_second_run_is_cached_and_force_reruns(monkeypatch, tmp_path):
    calls = []
    _fake_cli(monkeypatch, tmp_path, calls)
    path = _design_dir(tmp_path)
    first = call("opencae.run", path=path, analyses="mass,propulsion")
    assert first.data["status"] == "DONE"
    second = call("opencae.run", path=path, analyses="mass,propulsion")
    assert second.data["status"] == "CACHED"
    assert len(calls) == 1
    forced = call("opencae.run", path=path, analyses="mass,propulsion", force=True)
    assert forced.data["status"] == "DONE"
    assert len(calls) == 2


def test_unavailable_solver_is_skipped_not_run(monkeypatch, tmp_path):
    calls = []
    _fake_cli(monkeypatch, tmp_path, calls)
    path = _design_dir(tmp_path)
    r = call("opencae.run", path=path, analyses="mass,cfd")
    assert calls == [("mass",)]
    assert r.skipped == ["cfd"]
    assert any("no CFD solver: test" in m for m in r.messages)
    only = call("opencae.run", path=path, analyses="cfd")
    assert only.data["status"] == "SKIP"
    assert calls == [("mass",)]


def test_cli_missing_is_skip_with_fix(monkeypatch, tmp_path):
    monkeypatch.setattr(opencae_cli, "cli_available",
                        lambda: (False, "OpenCAE CLI not found; run: plane opencae setup --cli-python X --cli-root Y"))
    path = _design_dir(tmp_path)
    r = call("opencae.run", path=path, analyses="mass,propulsion")
    assert r.data["status"] == "SKIP"
    assert any("plane opencae setup" in m for m in r.messages)
    assert not (tmp_path / "d" / "opencae" / "results.json").exists()


def test_bad_analysis_name_is_input_error(monkeypatch, tmp_path):
    calls = []
    _fake_cli(monkeypatch, tmp_path, calls)
    path = _design_dir(tmp_path)
    assert call("opencae.run", path=path, analyses="mass,nonsense").exit_code == 2
    assert calls == []


def test_setup_merges_config_keys(monkeypatch, tmp_path):
    cfg = tmp_path / "local.json"
    monkeypatch.setattr(fea, "CONFIG_FILE", cfg)
    cfg.write_text(json.dumps({"python": "p", "root": "r"}), encoding="utf-8")
    clone = tmp_path / "clone"
    (clone / "opencae").mkdir(parents=True)
    (clone / "opencae" / "cli.py").write_text("", encoding="utf-8")
    py = tmp_path / "py.exe"
    py.write_text("", encoding="utf-8")
    r = call("opencae.setup", cli_python=str(py), cli_root=str(clone))
    assert r.ok
    saved = json.loads(cfg.read_text(encoding="utf-8"))
    assert set(saved) == {"python", "root", "cli_python", "cli_root"}
    assert saved["python"] == "p"


def test_fea_save_config_keeps_cli_keys(monkeypatch, tmp_path):
    cfg = tmp_path / "local.json"
    monkeypatch.setattr(fea, "CONFIG_FILE", cfg)
    cfg.write_text(json.dumps({"cli_python": "a", "cli_root": "b"}), encoding="utf-8")
    monkeypatch.setattr(fea, "runner_python_error", lambda p: "")
    fea.save_config("p", "r")
    saved = json.loads(cfg.read_text(encoding="utf-8"))
    assert saved["cli_python"] == "a"
    assert saved["cli_root"] == "b"
    assert saved["python"] == "p"
    assert saved["root"] == "r"
