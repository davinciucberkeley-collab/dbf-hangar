"""U13.3-3: design.propose --draft, title kept as given, design kept in the working tree."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from hangar import cli as cli_mod
from hangar.ops import call, OpInputError
from hangar.ops import edit


def _fake_run_factory(calls, top):
    def fake_run(argv, cwd):
        calls.append(list(argv))
        if "--show-toplevel" in argv:
            return str(top) + "\n"
        if "status" in argv:
            return " M designs/x/plane.yaml\n"
        if "--abbrev-ref" in argv:
            return "main\n"
        if "create" in argv:
            return "https://github.com/o/r/pull/7\n"
        return ""
    return fake_run


def _make_design(tmp_path: Path) -> Path:
    d = tmp_path / "designs" / "x"
    d.mkdir(parents=True)
    (d / "plane.yaml").write_text("id: x\nname: a\n", encoding="utf-8")
    return d


def test_draft_flag_adds_draft_to_gh(tmp_path, monkeypatch):
    d = _make_design(tmp_path)
    calls: list[list[str]] = []
    monkeypatch.setattr(edit, "_run", _fake_run_factory(calls, tmp_path))
    monkeypatch.setenv("HANGAR_GH", "gh-test")
    r = call("design.propose", path=str(d), title="Rehearsal", draft=True)
    assert r.ok, r.messages
    gh = [c for c in calls if c[0] == "gh-test"]
    assert len(gh) == 1
    assert gh[0][-1] == "--draft"
    assert gh[0][gh[0].index("--title") + 1] == "Rehearsal"


def test_title_is_kept_as_given(tmp_path, monkeypatch):
    d = _make_design(tmp_path)
    calls: list[list[str]] = []
    monkeypatch.setattr(edit, "_run", _fake_run_factory(calls, tmp_path))
    monkeypatch.setenv("HANGAR_GH", "gh-test")
    title = "REHEARSAL: Cessna 172 (do not merge)"
    r = call("design.propose", path=str(d), title=title)
    assert r.ok, r.messages
    gh = [c for c in calls if c[0] == "gh-test"]
    assert gh[0][gh[0].index("--title") + 1] == title
    commit = [c for c in calls if "commit" in c][0]
    assert commit[-1].split("\n")[0] == f"design(x): {title}"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True).stdout


@pytest.fixture
def real_repo(tmp_path, monkeypatch):
    repo = tmp_path / "r"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, capture_output=True, text=True, check=True)
    for k, v in (("user.email", "t@t"), ("user.name", "t")):
        subprocess.run(["git", "config", k, v], cwd=repo, check=True)
    for k, v in (("GIT_AUTHOR_NAME", "t"), ("GIT_AUTHOR_EMAIL", "t@t"),
                 ("GIT_COMMITTER_NAME", "t"), ("GIT_COMMITTER_EMAIL", "t@t")):
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("HANGAR_GH", "gh-test")

    def real_run(argv, cwd):
        if "push" in argv:
            return ""
        if argv[0] == "gh-test":
            return "https://github.com/o/r/pull/9\n"
        p = subprocess.run(argv, cwd=cwd, capture_output=True, text=True)
        if p.returncode != 0:
            raise OpInputError(f"{' '.join(argv[:4])} failed: {(p.stderr or p.stdout).strip()}")
        return p.stdout

    monkeypatch.setattr(edit, "_run", real_run)
    return repo


def test_design_stays_in_the_working_tree(real_repo):
    repo = real_repo
    d = repo / "designs" / "x"
    d.mkdir(parents=True)
    (d / "plane.yaml").write_text("id: x\nname: a\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "base")
    (d / "plane.yaml").write_text("id: x\nname: b\n", encoding="utf-8")
    r = call("design.propose", path=str(d), title="B")
    assert r.ok, r.messages
    assert _git(repo, "branch", "--show-current").strip() == "main"
    assert (d / "plane.yaml").read_text(encoding="utf-8") == "id: x\nname: b\n"
    assert _git(repo, "status", "--porcelain") == " M designs/x/plane.yaml\n"
    assert len(_git(repo, "log", "--oneline", "main").splitlines()) == 1
    assert len(_git(repo, "log", "--oneline", "design/x/b").splitlines()) == 2


def test_new_design_folder_survives(real_repo):
    repo = real_repo
    x = repo / "designs" / "x"
    x.mkdir(parents=True)
    (x / "plane.yaml").write_text("id: x\nname: a\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "base")
    d = repo / "designs" / "y"
    d.mkdir(parents=True)
    (d / "plane.yaml").write_text("id: y\nname: n\n", encoding="utf-8")
    r = call("design.propose", path=str(d), title="New y")
    assert r.ok, r.messages
    assert (d / "plane.yaml").exists()
    assert _git(repo, "status", "--porcelain") == "?? designs/y/\n"


def test_cli_flag():
    res = CliRunner().invoke(cli_mod.cli, ["design", "propose", "--help"])
    assert res.exit_code == 0, res.output
    assert "--draft" in res.output


def test_propose_warns_on_stale_baseline(tmp_path, monkeypatch):
    d = _make_design(tmp_path)
    calls: list[list[str]] = []
    monkeypatch.setattr(edit, "_run", _fake_run_factory(calls, tmp_path))
    monkeypatch.setattr(edit, "_stale_baseline_note", lambda p: "warning: baseline is stale (x)")
    r = call("design.propose", path=str(d), title="T")
    assert r.ok, r.messages
    assert r.data["warnings"] == ["warning: baseline is stale (x)"]
    assert r.messages[0] == "https://github.com/o/r/pull/7"
    assert r.messages[1] == "warning: baseline is stale (x)"
    assert any("create" in c for c in calls)


def test_propose_without_note_has_no_warning(tmp_path, monkeypatch):
    d = _make_design(tmp_path)
    calls: list[list[str]] = []
    monkeypatch.setattr(edit, "_run", _fake_run_factory(calls, tmp_path))
    monkeypatch.setattr(edit, "_stale_baseline_note", lambda p: None)
    r = call("design.propose", path=str(d), title="T")
    assert r.ok, r.messages
    assert r.data["warnings"] == []
    assert r.messages == ["https://github.com/o/r/pull/7"]


def test_stale_baseline_note_real(tmp_path):
    import shutil
    from hangar.baseline import write_baseline
    from hangar.checks import validate
    from hangar.design import load_design

    fix = Path(__file__).parent / "fixtures" / "linkage-op"
    f = tmp_path / "f"
    shutil.copytree(fix, f)
    plane = f / "plane.yaml"
    card = validate(load_design(plane))
    note = edit._stale_baseline_note(plane)
    assert (note is None) == bool(card.accepted)
    if not card.accepted:
        assert "plane baseline update" in note
        write_baseline(plane.parent, card)
        assert edit._stale_baseline_note(plane) is None
