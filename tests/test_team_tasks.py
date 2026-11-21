from __future__ import annotations
import importlib.util, os, shutil, subprocess, sys
from pathlib import Path
import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "tests" / "team_tasks"
TEAM_TASKS = ["send_design", "change_parameter", "compare_designs", "run_stress", "run_physics",
              "update_morph_chart", "send_idea", "research_entry", "verify_bom", "test_assembly",
              "weekly_update", "meeting_tasks_check"]
BOM = ("\nbom:\n  items:\n    - id: motor-a\n      qty: 2\n      unit_cost_usd: 12.5\n      url: https://example.com/m\n")
ASSEMBLY = "\nassembly:\n  sequence:\n    - {step: 1, add: [center_body]}\n    - {step: 2, add: [wing]}\n"

EXPECT = {
    "send_design": {"designs/example-tailsitter-wing/plane.yaml"},
    "change_parameter": {"designs/example-tailsitter-wing/plane.yaml"},
    "compare_designs": {"designs/example-b/plane.yaml"},
    "run_stress": set(),
    "run_physics": set(),
    "update_morph_chart": {"knowledge/morphological-chart.yaml"},
    "send_idea": set(),
    "research_entry": {"knowledge/sources/my-paper.md"},
    "verify_bom": {"designs/example-tailsitter-wing/plane.yaml"},
    "test_assembly": {"out/assembly.glb"},
    "weekly_update": {"updates/2026-11-23/updates.yaml"},
    "meeting_tasks_check": {"ledger/items.yaml"},
}


def _git(root, *args):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
                          cwd=root, check=True, capture_output=True, text=True).stdout


@pytest.fixture
def git_clean_repo(tmp_path):
    root = tmp_path / "repo"
    (root / "ledger" / "inbox").mkdir(parents=True)
    (root / "pyproject.toml").write_text("", encoding="utf-8")
    shutil.copytree(REPO / "knowledge", root / "knowledge", ignore=shutil.ignore_patterns("diy-projects", "concepts"))
    for name in ("example-tailsitter-wing", "example-b"):
        shutil.copytree(REPO / "designs" / "example-tailsitter-wing", root / "designs" / name)
    p = root / "designs" / "example-tailsitter-wing" / "plane.yaml"
    p.write_bytes(p.read_bytes() + (BOM + ASSEMBLY).encode("utf-8"))
    shutil.copy(SCRIPTS / "data" / "inbox.yaml", root / "ledger" / "inbox" / "2026-11-24.yaml")
    _git(root, "init", "-q")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "scratch")
    return root


def changed_files(root) -> set[str]:
    out = _git(root, "status", "--porcelain", "--untracked-files=all")
    return {line[3:].strip().strip('"') for line in out.splitlines()}


def run_task_script(task, root):
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash not available")
    env = {**os.environ, "PATH": str(Path(sys.executable).parent) + os.pathsep + os.environ["PATH"]}
    r = subprocess.run([bash, "-e", str(SCRIPTS / f"{task}.sh")], cwd=root, env=env, capture_output=True, text=True)
    assert r.returncode == 0, f"{task}.sh failed\nstdout:\n{r.stdout}\nstderr:\n{r.stderr}"


@pytest.mark.parametrize("task", TEAM_TASKS)
def test_team_task_needs_no_code_edit(task, git_clean_repo):
    if task == "run_physics" and importlib.util.find_spec("mujoco") is None:
        pytest.skip("mujoco not installed; fix: python -m pip install 'mujoco>=3'")
    run_task_script(task, git_clean_repo)
    changed = changed_files(git_clean_repo)
    assert not any(p.startswith("core/") for p in changed)
    assert EXPECT[task] <= changed
    if task == "send_idea":
        assert any(p.startswith("knowledge/ideas/") for p in changed)


def test_every_script_holds_only_plane_commands():
    for task in TEAM_TASKS:
        for line in (SCRIPTS / f"{task}.sh").read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            assert s.startswith("plane "), f"{task}.sh: {line!r}"
            for bad in ("&&", ";", "|", "$("):
                assert bad not in s, f"{task}.sh: {line!r} contains {bad!r}"


def test_scripts_match_task_list():
    assert sorted(p.stem for p in SCRIPTS.glob("*.sh")) == sorted(TEAM_TASKS)
