import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

from hangar.cli import cli
from hangar.ledger import Ledger
from hangar.progress import archive_path, build_progress, latest_verdicts, parent_verdicts, parse_units

REPO = Path(__file__).resolve().parents[1]

PLAN = """# P
## 6. Schedule

| Wave | Dates (PT) | Units |
|---|---|---|
| W0 First | Fri 11-20 | U0.1, U0.2 [hard] |
| W1 Second | Sat 11-21 | U1.1 |
| Freeze | Sun | - |

## 7. Units

### Unit U0.1: Alpha
- [x] **Step 1: a**
- [x] **Step 2: b**
### Unit U0.2: Beta (extra) [hard]
- [x] a
- [ ] b
@@
- [ ] inside a code fence is ignored
@@
### Unit U1.1: Gamma
- [ ] a
### Unit U9.9: Orphan
- [x] a
## 8. End
- [ ] not counted
""".replace("@@", "```")
REVIEW_A = """## U0.1 Alpha @ branch
### Verdict: REJECT (round 1). fix
### Round 2
### Verdict round 2: ACCEPT
## U0.2 Beta
### Verdict: REJECT (round 1). fix
## W9 not a unit
### Verdict: ACCEPT
"""
REVIEW_B = """## U0.2 Beta round 2
### Verdict: ACCEPT
"""


@pytest.fixture
def repo(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / "plans").mkdir()
    (tmp_path / "plans" / "2026-11-20-p.md").write_text(PLAN, encoding="utf-8")
    (tmp_path / "reviews").mkdir()
    (tmp_path / "reviews" / "2026-11-20-a.md").write_text(REVIEW_A, encoding="utf-8")
    (tmp_path / "reviews" / "2026-11-21-b.md").write_text(REVIEW_B, encoding="utf-8")
    led = Ledger(tmp_path / "ledger" / "items.yaml")
    led.add("task", "late thing", source="x", due="2026-11-01")
    led.add("idea", "someday", source="x")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def run(*args):
    return CliRunner().invoke(cli, ["progress", *args])


def test_counts_per_unit_ignore_fences_and_other_sections(repo):
    u = parse_units(PLAN.splitlines())
    assert (u["U0.1"]["done"], u["U0.1"]["total"]) == (2, 2)
    assert (u["U0.2"]["done"], u["U0.2"]["total"]) == (1, 2)
    assert (u["U1.1"]["done"], u["U1.1"]["total"]) == (0, 1)


def test_waves_status_and_verdict_columns(repo):
    text = build_progress(repo)
    assert text.index("### W0 First") < text.index("### W1 Second") < text.index("### Unscheduled")
    assert "| U0.1 | Alpha | 2/2 | done | ACCEPT |" in text
    assert "| U0.2 | Beta (extra) [hard] | 1/2 | in progress | ACCEPT |" in text
    assert "| U1.1 | Gamma | 0/1 | not started | - |" in text
    assert "| U9.9 | Orphan | 1/1 | done | - |" in text


def test_verdict_rule_last_in_section_then_later_file_wins(repo):
    assert latest_verdicts(repo) == {"U0.1": "ACCEPT", "U0.2": "ACCEPT"}


REVIEW_SUB = """## U1.1a Gamma part a
### Verdict: ACCEPT
## U1.1b Gamma part b
### Verdict: REJECT (round 1). fix
## U9.9a Orphan part a
### Verdict: ACCEPT
## U9.9b Orphan part b
### Verdict: ACCEPT
"""
REVIEW_SUB_FIX = """## U1.1b Gamma part b round 2
### Verdict: ACCEPT
"""
REVIEW_OWN_AND_SUB = """## U0.1a Alpha follow-up
### Verdict: REJECT (round 1). fix
"""


def test_latest_verdicts_keyed_per_sub_unit_heading(repo):
    (repo / "reviews" / "2026-11-22-c.md").write_text(REVIEW_SUB, encoding="utf-8")
    assert latest_verdicts(repo) == {
        "U0.1": "ACCEPT",
        "U0.2": "ACCEPT",
        "U1.1a": "ACCEPT",
        "U1.1b": "REJECT",
        "U9.9a": "ACCEPT",
        "U9.9b": "ACCEPT",
    }


def test_sub_unit_latest_wins_per_heading_then_parent_rolls_up(repo):
    (repo / "reviews" / "2026-11-22-c.md").write_text(REVIEW_SUB, encoding="utf-8")
    text = build_progress(repo)
    assert "| U1.1 | Gamma | 0/1 | not started | REJECT |" in text
    assert "| U9.9 | Orphan | 1/1 | done | ACCEPT |" in text
    (repo / "reviews" / "2026-11-23-d.md").write_text(REVIEW_SUB_FIX, encoding="utf-8")
    assert latest_verdicts(repo)["U1.1b"] == "ACCEPT"
    assert "| U1.1 | Gamma | 0/1 | not started | ACCEPT |" in build_progress(repo)


def test_parent_with_own_and_sub_sections_rejects_if_any_rejects(repo):
    (repo / "reviews" / "2026-11-22-c.md").write_text(REVIEW_OWN_AND_SUB, encoding="utf-8")
    assert "| U0.1 | Alpha | 2/2 | done | REJECT |" in build_progress(repo)


def test_parent_verdicts_unit():
    assert parent_verdicts({"U0.1": "ACCEPT", "U2.4a": "ACCEPT", "U2.4b": "ACCEPT"}) == {"U0.1": "ACCEPT", "U2.4": "ACCEPT"}
    assert parent_verdicts({"U2.4a": "ACCEPT", "U2.4b": "REJECT"}) == {"U2.4": "REJECT"}
    assert parent_verdicts({"U2.4": "ACCEPT", "U2.4c": "REJECT"}) == {"U2.4": "REJECT"}
    assert parent_verdicts({}) == {}


def test_real_repo_split_units_show_accept():
    text = build_progress(REPO)
    for uid in ("U2.3", "U2.4", "U2.5"):
        row = next(line for line in text.splitlines() if line.startswith(f"| {uid} |"))
        assert row.endswith("| ACCEPT |"), row


def test_ledger_counts_and_overdue(repo):
    text = build_progress(repo)
    assert "| task | 1 | 0 | 0 | 0 | 0 | 1 |" in text
    assert "| idea | 1 | 0 | 0 | 0 | 0 | 1 |" in text
    assert "not computed" in text and "As of" not in text
    dated = build_progress(repo, today="2026-11-20")
    assert "As of 2026-11-20." in dated and "(due 2026-11-01): late thing" in dated


def test_output_is_deterministic(repo):
    assert build_progress(repo) == build_progress(repo)
    assert build_progress(repo, today="2026-11-20") == build_progress(repo, today="2026-11-20")


def test_check_exit_codes(repo):
    assert run("--check").exit_code == 1  # no PROGRESS.md yet
    assert run("--write").exit_code == 0
    assert run("--check").exit_code == 0
    p = repo / "plans" / "2026-11-20-p.md"
    p.write_text(PLAN.replace("- [ ] b", "- [x] b"), encoding="utf-8")
    r = run("--check")
    assert r.exit_code == 1 and "stale" in r.output and len(r.output.strip().splitlines()) == 1
    assert run("--write", "--check").exit_code == 2


def test_no_flag_prints_to_stdout_and_writes_nothing(repo):
    r = run()
    assert r.exit_code == 0 and r.output.startswith("# Progress")
    assert not (repo / "PROGRESS.md").exists()


def test_print_survives_cp1252_stdout():
    env = dict(os.environ, PYTHONIOENCODING="cp1252", PYTHONUTF8="0", PYTHONPATH=str(REPO / "core"))
    r = subprocess.run([sys.executable, "-m", "hangar.cli", "progress"], cwd=REPO, env=env, capture_output=True)
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    assert "→".encode("utf-8") in r.stdout


def test_real_repo_write_then_check_passes(tmp_path, monkeypatch):
    shutil.copytree(REPO / "plans", tmp_path / "plans")
    shutil.copytree(REPO / "reviews", tmp_path / "reviews")
    shutil.copytree(REPO / "ledger", tmp_path / "ledger", ignore=shutil.ignore_patterns("prompts.jsonl", "events.jsonl"))
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert run("--write").exit_code == 0
    assert run("--check").exit_code == 0


def test_committed_progress_md_is_fresh_and_marked_generated():
    committed = (REPO / "PROGRESS.md").read_bytes()
    assert committed == build_progress(REPO).encode("utf-8")
    assert b"GENERATED by `plane progress --write`" in committed


def test_roadmap_is_short_and_traceable():
    text = (REPO / "ROADMAP.md").read_text(encoding="utf-8")
    assert len(text.splitlines()) <= 60
    for needle in ["2026-12-02", "W0", "W1", "W2", "W3", "W4", "D10", "plans/2026-11-20-standardization.md", "PROGRESS.md"]:
        assert needle in text, needle


ARCHIVE = """# Archive
## 7. Archived units
### Unit U5.1: Old and done
- [x] a
- [x] b
### Unit U1.1: Gamma archived copy
- [x] a
"""


def _with_archive(repo):
    plan = repo / "plans" / "2026-11-20-p.md"
    plan.write_text(PLAN.replace("| W1 Second | Sat 11-21 | U1.1 |", "| W1 Second | Sat 11-21 | U1.1, U5.1 |"), encoding="utf-8")
    arch = archive_path(plan)
    arch.parent.mkdir()
    arch.write_text(ARCHIVE, encoding="utf-8")
    return arch


def test_archive_path_is_a_sub_folder_named_like_the_plan(repo):
    plan = repo / "plans" / "2026-11-20-p.md"
    assert archive_path(plan) == repo / "plans" / "2026-11-20-p" / "archive.md"


def test_archived_units_appear_in_progress_with_their_verdict(repo):
    _with_archive(repo)
    text = build_progress(repo)
    assert "| U5.1 | Old and done | 2/2 | done | - |" in text
    assert "U9.9" in text and "| U0.1 | Alpha | 2/2 | done | ACCEPT |" in text


def test_unit_in_plan_wins_over_archived_copy(repo):
    _with_archive(repo)
    text = build_progress(repo)
    assert "| U1.1 | Gamma | 0/1 | not started | - |" in text
    assert "archived copy" not in text


def test_archive_does_not_become_the_active_plan(repo):
    sys.path.insert(0, str(REPO / "harness" / "hooks"))
    import agent_gate
    from hangar.progress import active_plan
    arch = _with_archive(repo)
    plan = repo / "plans" / "2026-11-20-p.md"
    assert active_plan(repo) == plan
    assert agent_gate.active_plan(repo) == plan
    assert arch.parent.parent == repo / "plans"


def test_real_repo_archive_holds_only_finished_units_not_in_the_plan():
    archive = archive_path(REPO / "plans" / "2026-11-20-standardization.md")
    archived = parse_units(archive.read_text(encoding="utf-8").splitlines())
    in_plan = parse_units((REPO / "plans" / "2026-11-20-standardization.md").read_text(encoding="utf-8").splitlines())
    assert len(archived) >= 30
    assert all(u["total"] and u["done"] == u["total"] for u in archived.values())
    assert not set(archived) & set(in_plan)
