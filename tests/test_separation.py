"""U1.4: no commit changes both designs/** and core/** unless its message has a `migration:` line (or the PR is labelled)."""
from __future__ import annotations

import subprocess

from harness.ci.check_separation import ZEROS, check_separation, check_separation_files, main


def test_separation_flags_design_pr_touching_core():
    files = ["designs/x/plane.yaml", "core/hangar/checks.py"]
    assert check_separation_files(files, labels=[]) != []
    assert check_separation_files(files, labels=["migration"]) == []
    assert check_separation_files(files, labels=[], message="fix\n\nmigration: schema 1.0") == []


def test_separation_allows_designs_only_core_only_and_backslashes():
    assert check_separation_files(["designs/x/plane.yaml", "designs/y/README.md"], labels=[]) == []
    assert check_separation_files(["core/hangar/checks.py", "tests/test_x.py"], labels=[]) == []
    assert check_separation_files(["designs\\x\\plane.yaml", "core\\hangar\\checks.py"], labels=[]) != []


def _git(repo, *args):
    p = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=repo, check=True,
                       capture_output=True, text=True)
    return p.stdout.strip()


def _commit(repo, files: dict, msg: str):
    for name, text in files.items():
        f = repo / name
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text)
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", msg)


def _repo(tmp_path):
    _git(tmp_path, "init", "-q", "-b", "main")
    _commit(tmp_path, {"README.md": "x"}, "base")
    return _git(tmp_path, "rev-parse", "HEAD")


def test_commit_touching_both_fails_unless_migration_line_or_label(tmp_path, monkeypatch):
    base = _repo(tmp_path)
    _commit(tmp_path, {"designs/x/plane.yaml": "a: 1\n", "core/a.py": "x = 1\n"}, "both")
    assert check_separation(base, cwd=tmp_path) != []
    assert check_separation(base, labels=["migration"], cwd=tmp_path) == []
    monkeypatch.chdir(tmp_path)
    assert main(["--base", base]) == 1
    assert main(["--base", base, "--labels", "bug,migration"]) == 0
    _commit(tmp_path, {"designs/x/plane.yaml": "a: 2\n", "core/a.py": "x = 2\n"}, "both again\n\nmigration: schema 1.0")
    last = _git(tmp_path, "rev-parse", "HEAD~1")
    assert check_separation(last, cwd=tmp_path) == []          # that one commit carries the migration line


def test_designs_only_then_core_only_passes(tmp_path):
    base = _repo(tmp_path)
    _commit(tmp_path, {"designs/x/plane.yaml": "a: 1\n"}, "design")
    _commit(tmp_path, {"core/a.py": "x = 1\n"}, "code")
    assert check_separation(base, cwd=tmp_path) == []


def test_merge_commit_combining_designs_and_core_passes(tmp_path):
    base = _repo(tmp_path)
    _git(tmp_path, "switch", "-qc", "d")
    _commit(tmp_path, {"designs/x/plane.yaml": "a: 1\n"}, "design")
    _git(tmp_path, "switch", "-q", "main")
    _git(tmp_path, "switch", "-qc", "c")
    _commit(tmp_path, {"core/a.py": "x = 1\n"}, "code")
    _git(tmp_path, "switch", "-q", "main")
    _git(tmp_path, "merge", "-q", "--no-ff", "-m", "merge d", "d")
    _git(tmp_path, "merge", "-q", "--no-ff", "-m", "merge c", "c")
    assert check_separation(base, cwd=tmp_path) == []          # merges are skipped; each parent commit is clean


def test_first_push_checks_since_merge_base_or_skips_with_note(tmp_path, monkeypatch, capsys):
    base = _repo(tmp_path)
    _commit(tmp_path, {"designs/x/plane.yaml": "a: 1\n", "core/a.py": "x = 1\n"}, "both")
    monkeypatch.chdir(tmp_path)
    assert main(["--base", ZEROS]) == 0                         # no origin/main: skipped with a note
    assert "nothing checked" in capsys.readouterr().out
    _git(tmp_path, "update-ref", "refs/remotes/origin/main", base)
    assert main(["--base", ZEROS]) == 1                         # origin/main known: commits since it are checked
