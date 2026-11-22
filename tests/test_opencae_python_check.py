"""T29: tools doctor and fea setup check that OpenCAE's Python can import numpy and scipy."""
from __future__ import annotations

import sys
import types

from click.testing import CliRunner

from hangar import fea
from hangar.adapters.opencae import OpenCAE
from hangar.cli import cli
from hangar.ops import call

FOUND = {"python": "py", "root": "R", "found": True, "how": "test"}
NO_NUMPY = "py cannot import numpy and scipy (ModuleNotFoundError: No module named 'numpy')"


def _fake_run(returncode, stderr=""):
    def run(argv, **kwargs):
        assert argv[1:] == ["-c", "import numpy, scipy"]
        return types.SimpleNamespace(returncode=returncode, stdout="", stderr=stderr)
    return run


def test_runner_python_error_is_empty_for_a_python_with_numpy_and_scipy():
    assert fea.runner_python_error(sys.executable) == ""


def test_runner_python_error_names_the_missing_module(monkeypatch):
    monkeypatch.setattr(fea.subprocess, "run", _fake_run(1, "Traceback\nModuleNotFoundError: No module named 'numpy'\n"))
    why = fea.runner_python_error("opencae-python")
    assert "opencae-python" in why and "No module named 'numpy'" in why


def test_runner_python_error_for_a_python_that_cannot_start():
    assert "cannot run" in fea.runner_python_error("C:/no/such/python.exe")


def test_doctor_row_is_missing_when_the_python_lacks_numpy(monkeypatch):
    monkeypatch.setattr(fea, "find_opencae", lambda *a, **k: dict(FOUND))
    monkeypatch.setattr(fea, "runner_python_error", lambda python: NO_NUMPY)
    ok, detail = OpenCAE().available()
    assert not ok and "cannot import numpy and scipy" in detail and "plane fea setup" in detail
    row = next(r for r in call("tools.doctor").data["adapters"] if r["name"] == "opencae")
    assert row["status"] == "missing" and "numpy" in row["detail"]


def test_available_is_ok_when_the_python_imports_numpy_and_scipy(monkeypatch):
    monkeypatch.setattr(fea, "find_opencae", lambda *a, **k: dict(FOUND))
    monkeypatch.setattr(fea, "runner_python_error", lambda python: "")
    assert OpenCAE().available()[0] is True


def test_fea_setup_op_refuses_a_python_without_numpy_and_writes_nothing(monkeypatch, tmp_path):
    cfg = tmp_path / "opencae.local.json"
    monkeypatch.setattr(fea, "CONFIG_FILE", cfg)
    monkeypatch.setattr(fea, "find_opencae", lambda *a, **k: dict(FOUND))
    monkeypatch.setattr(fea, "runner_python_error", lambda python: NO_NUMPY)
    r = call("fea.setup", opencae_python="py", opencae_root="R")
    assert r.ok is False and r.exit_code == 2 and "numpy" in " ".join(r.messages)
    assert not cfg.exists()


def test_fea_setup_op_saves_a_python_that_imports_numpy_and_scipy(monkeypatch, tmp_path):
    cfg = tmp_path / "opencae.local.json"
    monkeypatch.setattr(fea, "CONFIG_FILE", cfg)
    monkeypatch.setattr(fea, "find_opencae", lambda *a, **k: dict(FOUND))
    monkeypatch.setattr(fea, "runner_python_error", lambda python: "")
    r = call("fea.setup", opencae_python="py", opencae_root="R")
    assert r.ok, r.messages
    assert cfg.is_file()


def test_fea_setup_flag_refuses_a_python_without_numpy(monkeypatch, tmp_path):
    cfg = tmp_path / "opencae.local.json"
    monkeypatch.setattr(fea, "CONFIG_FILE", cfg)
    monkeypatch.setattr(fea, "find_opencae", lambda *a, **k: dict(FOUND))
    monkeypatch.setattr(fea, "runner_python_error", lambda python: NO_NUMPY)
    res = CliRunner().invoke(cli, ["fea", "--setup", "--opencae-python", "py", "--opencae-root", "R"])
    assert res.exit_code == 2 and "numpy" in res.output
    assert not cfg.exists()
