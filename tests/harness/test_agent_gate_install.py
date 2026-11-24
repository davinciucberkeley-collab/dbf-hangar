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
    brief = root / "plans" / "2026-11-20-x" / "briefs" / "H1-a.md"
    brief.parent.mkdir(parents=True)
    brief.write_text("# brief\n", encoding="utf-8")
    assert gate(task("builder", "make it better"), root).returncode == 2
    assert gate(task("builder", "Follow plans/2026-11-20-x/briefs/H1-a.md"), root).returncode == 0
    assert gate(task("builder", "Pass check: pytest. Stop rule: report."), root).returncode == 0

def test_reviewer_in_plan_allowed(root):
    assert gate(task("reviewer", "review"), root).returncode == 0

def test_agent_tool_name_also_gated(root):
    assert gate({"tool_name": "Agent", "tool_input": {"subagent_type": "helper"}}, root).returncode == 2

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

def test_upgrade_removes_old_python_hook_entries(tmp_path):
    proj = tmp_path / "p"; (proj / ".claude").mkdir(parents=True)
    old = {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": 'python "$CLAUDE_PROJECT_DIR/harness/hooks/stop_gate.py"'}]},
                              {"hooks": [{"type": "command", "command": "echo other"}]}]}}
    (proj / ".claude/settings.json").write_text(json.dumps(old))
    installer.install(proj)
    cmds = [h["command"] for e in json.loads((proj / ".claude/settings.json").read_text())["hooks"]["Stop"] for h in e["hooks"]]
    assert not any(c.endswith('stop_gate.py"') for c in cmds) and "echo other" in cmds and any("run.sh" in c for c in cmds)

def test_installed_shell_scripts_have_no_cr(tmp_path):
    proj = tmp_path / "p"; proj.mkdir()
    installer.install(proj)
    for sh in (proj / "harness").rglob("*.sh"):
        assert b"\r" not in sh.read_bytes()

def test_repo_shell_scripts_have_no_cr():
    for sh in (REPO / "harness").rglob("*.sh"):
        assert b"\r" not in sh.read_bytes()


def test_brief_reference_accepts_every_path_form(root):
    brief = root / "plans" / "2026-11-20-x" / "briefs" / "H1-a.md"
    brief.parent.mkdir(parents=True)
    brief.write_text("# brief\n", encoding="utf-8")
    refs = [
        "plans/2026-11-20-x/briefs/H1-a.md",
        "plans\\2026-11-20-x\\briefs\\H1-a.md",
        brief.as_posix(),
        str(brief).replace("/", "\\"),
    ]
    for ref in refs:
        assert gate(task("builder", f"Follow {ref} now."), root).returncode == 0, ref


def test_brief_reference_rejected_when_missing_or_outside_plans(root):
    other = root / "other" / "plans" / "p" / "briefs" / "b.md"
    other.parent.mkdir(parents=True)
    other.write_text("# b\n", encoding="utf-8")
    notes = root / "plans" / "2026-11-20-x" / "notes" / "a.md"
    notes.parent.mkdir(parents=True)
    notes.write_text("# a\n", encoding="utf-8")
    for ref in ["plans/2026-11-20-x/briefs/missing.md", other.as_posix(), "plans/2026-11-20-x/notes/a.md"]:
        assert gate(task("builder", f"Follow {ref} now."), root).returncode == 2, ref


def test_agent_gate_roster_matches_hangar_roster():
    sys.path.insert(0, str(REPO / "harness" / "hooks"))
    import agent_gate
    from hangar.roster import load_roster
    assert agent_gate.roster_names(REPO) == sorted(load_roster(REPO))


BUILTINS = ["Explore", "Plan", "claude-code-guide"]


@pytest.mark.parametrize("tool", ["Task", "Agent"])
@pytest.mark.parametrize("name", BUILTINS)
def test_builtin_read_only_subagent_passes_without_roster_or_table(root, tool, name):
    r = gate({"tool_name": tool, "tool_input": {"subagent_type": name, "prompt": "find x"}}, root)
    assert r.returncode == 0, r.stderr


@pytest.mark.parametrize("name", ["general-purpose", "statusline-setup", "output-style-setup", "explore", "Explore2", ""])
def test_other_names_including_writing_builtins_still_refused(root, name):
    r = gate(task(name), root)
    assert r.returncode == 2 and "not in the hangar roster" in r.stderr and "Explore" in r.stderr


def test_builtin_allowance_keeps_every_other_check(root):
    assert gate(task("Explore"), root).returncode == 0
    assert gate(task("helper"), root).returncode == 2
    assert gate(task("recon"), root).returncode == 2
    assert gate(task("builder", "make it better"), root).returncode == 2
    assert gate(task("builder", "Pass check: pytest. Stop rule: report."), root).returncode == 0


WRITE_TOOLS = ["Write", "Edit", "NotebookEdit"]


def tool_event(tool, agent_type=None):
    event = {"tool_name": tool, "tool_input": {"file_path": "x"}}
    if agent_type is not None:
        event["agent_type"] = agent_type
    return event


@pytest.mark.parametrize("name", BUILTINS)
@pytest.mark.parametrize("tool", WRITE_TOOLS)
def test_write_tools_refused_inside_builtin_read_only_agents(root, tool, name):
    r = gate(tool_event(tool, name), root)
    assert r.returncode == 2 and "may not write" in r.stderr and name in r.stderr


@pytest.mark.parametrize("agent_type", [None, "", "builder", "reviewer", "explore", "general-purpose"])
@pytest.mark.parametrize("tool", WRITE_TOOLS)
def test_write_tools_pass_for_every_other_agent_and_the_main_session(root, tool, agent_type):
    assert gate(tool_event(tool, agent_type), root).returncode == 0


@pytest.mark.parametrize("tool", ["Read", "Grep", "Glob", "Bash"])
def test_read_tools_and_bash_pass_inside_a_builtin(root, tool):
    assert gate(tool_event(tool, "Explore"), root).returncode == 0


def test_builtin_launch_reads_no_user_agent_files(root, tmp_path):
    home = tmp_path / "home"
    agents = home / ".claude" / "agents"
    agents.mkdir(parents=True)
    nl = chr(10)
    (agents / "Explore.md").write_text(nl.join(["---", "name: Explore", "tools: Read, Write, Edit, Bash", "---", "# x", ""]), encoding="utf-8")
    (agents / "cp.md").write_bytes((nl.join(["---", "name: cp", "---", chr(0x201C) + "q" + chr(0x201D), ""])).encode("cp1252", errors="replace") + bytes([0x93, 0x94]))
    (agents / "u16.md").write_bytes(nl.join(["---", "name: u16", "---", ""]).encode("utf-16"))
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(root), HOME=str(home), USERPROFILE=str(home))
    r = subprocess.run([sys.executable, str(REPO / "harness/hooks/agent_gate.py")], input=json.dumps(task("Explore")),
                       capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr


def test_settings_route_the_write_tools_to_the_gate(tmp_path):
    def gate_matcher(settings):
        return next(e["matcher"] for e in settings["hooks"]["PreToolUse"]
                    if any("agent_gate" in h["command"] for h in e["hooks"]))
    s = json.loads((REPO / ".claude/settings.json").read_text())
    assert set(gate_matcher(s).split("|")) == {"Task", "Agent", "Write", "Edit", "NotebookEdit"}
    proj = tmp_path / "p"
    installer.install(proj)
    assert gate_matcher(json.loads((proj / ".claude/settings.json").read_text())) == gate_matcher(s)


def test_install_upgrades_an_old_gate_matcher_without_a_second_entry(tmp_path):
    proj = tmp_path / "p"
    (proj / ".claude").mkdir(parents=True)
    installer.install(proj)
    path = proj / ".claude/settings.json"
    s = json.loads(path.read_text())
    for e in s["hooks"]["PreToolUse"]:
        e["matcher"] = "Task|Agent"
    path.write_text(json.dumps(s))
    installer.install(proj)
    pre = json.loads(path.read_text())["hooks"]["PreToolUse"]
    assert len(pre) == 1 and pre[0]["matcher"] == "Task|Agent|Write|Edit|NotebookEdit"
