"""U18.1-1: OpenCAE CLI discovery, solver status, hash and result store. No test needs OpenCAE, ccx or a solver."""
import json
import shutil
from types import SimpleNamespace

import pytest
import yaml

import hangar.design as design_mod
import hangar.fea as fea
import hangar.opencae_cli as oc
from hangar.adapters.opencae import OpenCAE
from hangar.design import DESIGNS_DIR, REPO_ROOT, load_design

FIX = REPO_ROOT / "tests" / "fixtures" / "opencae"
EXAMPLE = DESIGNS_DIR / "example-tailsitter-wing"


@pytest.fixture
def edit_standards(tmp_path, monkeypatch):
    def edit(fn):
        std = yaml.safe_load(design_mod.STANDARDS_PATH.read_text(encoding="utf-8"))
        fn(std)
        p = tmp_path / "std.yaml"
        p.write_text(yaml.safe_dump(std, sort_keys=False), encoding="utf-8")
        monkeypatch.setattr(design_mod, "STANDARDS_PATH", p)
    return edit


def _example(tmp_path):
    dst = tmp_path / "example-tailsitter-wing"
    shutil.copytree(EXAMPLE, dst)
    return load_design(dst / "plane.yaml")


def _doctor_fixture():
    # the saved doctor output holds raw Windows paths (unescaped backslashes), so it is not strict JSON as stored
    return json.loads((FIX / "doctor_no_openfoam.json").read_text(encoding="utf-8").replace("\\", "\\\\"))


def _fake_cli(tmp_path):
    py = tmp_path / "python.exe"
    py.write_text("")
    root = tmp_path / "oc"
    (root / "opencae").mkdir(parents=True)
    (root / "opencae" / "cli.py").write_text("")
    return {"python": str(py), "root": str(root), "found": True, "how": "given", "head": ""}


def test_find_cli_prefers_arguments(tmp_path):
    cli = _fake_cli(tmp_path)
    got = oc.find_cli(python=cli["python"], root=cli["root"])
    assert got["found"] is True and got["how"] == "given"


def test_find_cli_not_found(tmp_path, monkeypatch):
    for v in oc.CLI_ENV:
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setattr(fea, "CONFIG_FILE", tmp_path / "none.json")
    monkeypatch.setattr(fea, "REPO_ROOT", tmp_path / "a" / "b")
    assert oc.find_cli(python=None, root=None)["found"] is False


def test_solver_status_fixture_no_openfoam_no_su2(tmp_path):
    doc = _doctor_fixture()
    st = oc.solver_status(doc, environ={}, home=tmp_path)
    assert st["ccx"][0] is True
    assert st["cfd"][0] is False and "opencae setup su2 --yes" in st["cfd"][1]


def test_solver_status_finds_su2_in_home(tmp_path):
    doc = _doctor_fixture()
    exe = tmp_path / ".opencae" / "solvers" / "SU2-v8.1.0" / "bin" / "SU2_CFD.exe"
    exe.parent.mkdir(parents=True)
    exe.write_text("")
    assert oc.solver_status(doc, environ={}, home=tmp_path)["cfd"][0] is True


def test_solver_status_error_doc(tmp_path):
    st = oc.solver_status({"error": "boom"}, environ={}, home=tmp_path)
    assert st["ccx"][0] is False and st["cfd"][0] is False
    assert "boom" in st["ccx"][1] and "boom" in st["cfd"][1]


def test_project_hash_changes_with_inputs(tmp_path):
    design = load_design(EXAMPLE / "plane.yaml")
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "drone.json").write_bytes(b"{}")
    (proj / "airframe.stl").write_bytes(b"solid a")
    an = ("mass", "structure")
    base = oc.project_hash(design, proj, an, "abc")
    assert len(base) == 16 and base == oc.project_hash(design, proj, an, "abc")
    assert oc.project_hash(design, proj, ("structure", "mass"), "abc") == base
    assert oc.project_hash(design, proj, ("mass",), "abc") != base
    assert oc.project_hash(design, proj, an, "abd") != base
    (proj / "drone.json").write_bytes(b"{ }")
    assert oc.project_hash(design, proj, an, "abc") != base
    (proj / "drone.json").write_bytes(b"{}")
    (proj / "airframe.stl").write_bytes(b"solid b")
    assert oc.project_hash(design, proj, an, "abc") != base


def test_standards_fingerprint_changes_with_a_value(edit_standards):
    before = oc.standards_fingerprint()
    edit_standards(lambda s: s["structure"]["ultimate_factor"].update(source="other text"))
    assert oc.standards_fingerprint() == before
    edit_standards(lambda s: s["structure"]["ultimate_factor"].update(value=1.75))
    assert oc.standards_fingerprint() != before


def test_design_fingerprint(tmp_path):
    design = _example(tmp_path)
    an = ("mass", "flight")
    a = oc.design_fingerprint(design, an)
    assert len(a) == 16 and a == oc.design_fingerprint(design, an)
    assert oc.design_fingerprint(design, ("flight", "mass")) == a
    assert oc.design_fingerprint(design, ("mass",)) != a
    (design.base_dir / "opencae-inputs.yaml").write_text("x: 1\n", encoding="utf-8")
    b = oc.design_fingerprint(design, an)
    assert b != a
    design.data["components"][0]["mass_g"] += 1
    assert oc.design_fingerprint(design, an) != b


def test_store_and_load_result_roundtrip(tmp_path):
    design = _example(tmp_path)
    assert oc.load_result(design) is None
    result = {"verdict": "pass", "analyses": {}}
    path = oc.store_result(design, "h", "dh", ("mass",), "abc", result)
    assert path == oc.result_path(design)
    rec = oc.load_result(design)
    assert rec["result"] == result and rec["hash"] == "h" and rec["design_hash"] == "dh"
    assert rec["design"] == design.id and rec["analyses"] == ["mass"] and rec["opencae_head"] == "abc"
    path.write_text("{", encoding="utf-8")
    assert oc.load_result(design) is None


def test_run_project_uses_the_cli_by_path(tmp_path, monkeypatch):
    cli = _fake_cli(tmp_path)
    seen = {}

    def fake(argv, **kw):
        seen["argv"], seen["kw"] = argv, kw
        return SimpleNamespace(returncode=0, stderr="",
                               stdout=(FIX / "quad250_mass_propulsion_structure.json").read_text(encoding="utf-8"))
    monkeypatch.setattr("hangar.opencae_cli.subprocess.run", fake)
    proj = tmp_path / "proj"
    out = oc.run_project(proj, ("mass", "propulsion"), cli, log=lambda *a: None)
    assert seen["argv"] == [cli["python"], "-m", "opencae", "run", str(proj), "--only", "mass,propulsion",
                            "--force", "--json"]
    assert seen["kw"]["cwd"] == cli["root"]
    res = out["result"]
    assert out["returncode"] == 0 and res["verdict"] == "conditional"
    assert res["analyses"]["propulsion"]["metrics"]["tw_ratio"]["value"] == pytest.approx(6.64785228260017)


def test_run_project_bad_analysis(tmp_path):
    with pytest.raises(ValueError):
        oc.run_project(tmp_path, ("mass", "nonsense"), _fake_cli(tmp_path), log=lambda *a: None)


def test_run_cli_non_json_stdout_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr("hangar.opencae_cli.subprocess.run",
                        lambda argv, **kw: SimpleNamespace(returncode=1, stdout="not json", stderr="bad"))
    assert oc.run_cli(_fake_cli(tmp_path), ["x"]) == (1, None, "bad")


def test_adapter_cli_available_skip_text(monkeypatch):
    monkeypatch.setattr(oc, "find_cli", lambda *a, **k: {"python": "", "root": "", "found": False, "how": "auto", "head": ""})
    ok, text = OpenCAE().cli_available()
    assert ok is False and text.startswith("OpenCAE CLI not found; run: plane opencae setup")


@pytest.mark.skipif(not oc.find_cli()["found"], reason="OpenCAE CLI not set up on this machine")
def test_live_doctor():
    doc = oc.doctor(oc.find_cli())
    assert "python" in doc and "error" not in doc
