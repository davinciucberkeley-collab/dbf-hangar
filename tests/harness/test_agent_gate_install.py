import json, os, subprocess, sys
from pathlib import Path
import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "harness"))
import install as installer  # harness/install.py

ROLES = ["advisor","auditor","builder","builder-plus","conductor","design-engineer","recon","reviewer","scout","tactician"]

@pytest.fixture
def root(tmp_path):
    (tmp_path / ".claude" / "agents").mkdir(parents=True)
    for r in ROLES:
        (tmp_path / ".claude" / "agents" / f"{r}.md").write_text(f"---\nname: {r}\nmodel: haiku\n---\n# {r}\n", encoding="utf-8")
    (tmp_path / "plans").mkdir()
    (tmp_path / "plans" / "2026-11-20-x.md").write_text("| Step | Role | Model | Pass criterion |\n|---|---|---|---|\n| H1 | `builder` | Haiku | t |\n| HR | `reviewer` | Opus | t |\n", encoding="utf-8")
    return tmp_path

def gate(event, root):
    return subprocess.run([sys.executable, str(REPO / "harness/hooks/agent_gate.py")], input=json.dumps(event),
                          capture_output=True, text=True, env=dict(os.environ, CLAUDE_PROJECT_DIR=str(root)))

def task(role, prompt="x"):
    return {"tool_name": "Task", "tool_input": {"subagent_type": role, "prompt": prompt}}

def test_unknown_role_blocked_with_roster(root):
    r = gate(task("general-purpose"), root)
    assert r.returncode == 2 and "builder" in r.stderr and "not in the hangar roster" in r.stderr

def test_roster_role_missing_from_plan_blocked(root):
    r = gate(task("recon"), root)
    assert r.returncode == 2 and "agent table" in r.stderr

def test_builder_needs_builder_ready_brief(root):
    assert gate(task("builder", "make it better"), root).returncode == 2
    assert gate(task("builder", "Follow plans/2026-11-20-x/briefs/H1-a.md"), root).returncode == 0
    assert gate(task("builder", "Pass check: pytest. Stop rule: report."), root).returncode == 0

def test_reviewer_in_plan_allowed(root):
    assert gate(task("reviewer", "review"), root).returncode == 0

def test_agent_tool_name_also_gated(root):
    assert gate({"tool_name": "Agent", "tool_input": {"subagent_type": "Explore"}}, root).returncode == 2

def test_other_tools_and_bad_input_pass(root):
    assert gate({"tool_name": "Bash", "tool_input": {"command": "ls"}}, root).returncode == 0
    r = subprocess.run([sys.executable, str(REPO / "harness/hooks/agent_gate.py")], input="not json",
                       capture_output=True, text=True, env=dict(os.environ, CLAUDE_PROJECT_DIR=str(root)))
    assert r.returncode == 0

def test_settings_wire_all_four_hooks_and_quiet_style():
    s = json.loads((REPO / ".claude/settings.json").read_text())
    assert s["outputStyle"] == "quiet"
    assert set(s["hooks"]) == {"UserPromptSubmit", "PreToolUse", "SessionStart", "Stop"}
    assert (REPO / ".claude/output-styles/quiet.md").read_text().startswith("---\nname: quiet")

def test_install_is_idempotent_and_merges_settings(tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude/settings.json").write_text(json.dumps({"outputStyle": "mine", "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "echo hi"}]}]}}))
    installer.install(tmp_path); installer.install(tmp_path)
    s = json.loads((tmp_path / ".claude/settings.json").read_text())
    assert s["outputStyle"] == "mine"
    stop_cmds = [h["command"] for e in s["hooks"]["Stop"] for h in e["hooks"]]
    assert stop_cmds.count("echo hi") == 1 and sum('run.sh" stop_gate' in c for c in stop_cmds) == 1
    assert len(list((tmp_path / ".claude/agents").glob("*.md"))) == 10
    assert (tmp_path / "harness/hooks/agent_gate.py").exists()

def test_role_must_be_in_an_agent_table_not_just_mentioned(root):
    (root / "plans" / "2026-11-21-y.md").write_text(
        "We might use `recon` later.\n\n| Step | Role | Model | Pass criterion |\n|---|---|---|---|\n| H1 | `builder` | Haiku | tests |\n", encoding="utf-8")
    assert gate(task("recon"), root).returncode == 2
    assert gate(task("builder", "Pass check: x. Stop rule: y."), root).returncode == 0

def test_non_ascii_prompt_cannot_slip_past_gate(root):
    r = subprocess.run([sys.executable, str(REPO / "harness/hooks/agent_gate.py")],
                       input=json.dumps(task("general-purpose", "Ángulo → σ"), ensure_ascii=False).encode("utf-8"),
                       capture_output=True, env=dict(os.environ, CLAUDE_PROJECT_DIR=str(root), PYTHONIOENCODING="cp1252"))
    assert r.returncode == 2

def test_settings_use_launcher():
    s = json.loads((REPO / ".claude/settings.json").read_text())
    cmds = [h["command"] for ev in s["hooks"].values() for e in ev for h in e["hooks"]]
    assert all(c.startswith('sh "$CLAUDE_PROJECT_DIR/harness/hooks/run.sh" ') for c in cmds)

def test_launcher_runs_a_hook(root):
    r = subprocess.run(["sh", str(REPO / "harness/hooks/run.sh"), "agent_gate"], input=json.dumps(task("general-purpose")),
                       capture_output=True, text=True, env=dict(os.environ, CLAUDE_PROJECT_DIR=str(root)))
    assert r.returncode == 2 and "not in the hangar roster" in r.stderr

def test_install_refuses_home_and_writes_gitignore(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path)); monkeypatch.setenv("USERPROFILE", str(tmp_path))
    with pytest.raises(ValueError): installer.install(tmp_path)
    proj = tmp_path / "proj"; proj.mkdir()
    installer.install(proj); installer.install(proj)
    assert (proj / ".gitignore").read_text().count("ledger/prompts.jsonl") == 1

def test_repo_forces_lf_for_shell_scripts():
    assert "*.sh text eol=lf" in (REPO / ".gitattributes").read_text().splitlines()

def test_launcher_with_missing_hook_does_not_block(root):
    r = subprocess.run(["sh", str(REPO / "harness/hooks/run.sh"), "no_such_hook"], input="{}",
                       capture_output=True, text=True, env=dict(os.environ, CLAUDE_PROJECT_DIR=str(root)))
    assert r.returncode == 0

def test_install_writes_gitattributes_once(tmp_path):
    proj = tmp_path / "p"; proj.mkdir()
    installer.install(proj); installer.install(proj)
    assert (proj / ".gitattributes").read_text().count("*.sh text eol=lf") == 1
