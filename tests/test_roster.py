from pathlib import Path
import pytest
from hangar.roster import load_roster

REPO = Path(__file__).resolve().parents[1]
ROLES = {"conductor","advisor","tactician","builder","builder-plus","scout","recon","design-engineer","reviewer","auditor"}

def test_roster_has_exactly_the_ten_roles():
    assert set(load_roster(REPO)) == ROLES

def test_models_by_level():
    r = load_roster(REPO)
    assert {n for n, a in r.items() if a.model == "opus"} == {"conductor", "advisor", "reviewer"}
    assert {n for n, a in r.items() if a.model == "haiku"} == {"builder", "scout", "auditor"}

def test_every_agent_has_stop_rules_and_never():
    for name in ROLES:
        text = (REPO / ".claude/agents" / f"{name}.md").read_text(encoding="utf-8")
        assert "## Stop rules" in text and "## Never" in text

def test_design_engineer_cannot_edit_or_write():
    tools = load_roster(REPO)["design-engineer"].tools
    assert "Edit" not in tools and "Write" not in tools

def test_conductor_can_launch_and_reuse_agents():
    tools = load_roster(REPO)["conductor"].tools
    assert "Agent" in tools and "SendMessage" in tools

def test_bad_model_rejected(tmp_path):
    (tmp_path / ".claude/agents").mkdir(parents=True)
    (tmp_path / ".claude/agents/x.md").write_text("---\nname: x\nmodel: gpt\ntools: Read\ndescription: d\n---\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_roster(tmp_path)

def test_agents_md_v02_names_every_role_and_hook():
    text = (REPO / "standards/agents.md").read_text(encoding="utf-8")
    assert text.startswith("# Agent Standard v0.2")
    assert all(f"`{r}`" in text for r in ROLES)
    assert all(h in text for h in ["log_prompt", "agent_gate", "reinject", "stop_gate", "Pass criterion"])

def test_claude_md_is_a_pointer_file():
    assert len((REPO / "CLAUDE.md").read_text(encoding="utf-8").splitlines()) <= 25

def test_agents_md_has_brief_template():
    text = (REPO / "standards/agents.md").read_text(encoding="utf-8")
    for needle in [
        "## Brief template", "## Environment", "## Known failures", "## Plan coverage",
        "## Exact steps and outputs", "## Exact tests", "## Pass check", "## Commit", "## Stop rule",
        'pip install -e ".[mcp,dev]"', "C:/Users/trist/wt/<unit>", "Windows 11 + Git Bash",
        "Where the brief and plan §7 differ, the brief governs; the tactician records the difference in Plan coverage",
    ]:
        assert needle in text, needle
    assert text.startswith("# Agent Standard v0.2")


def test_light_path_teammate_rule_and_builtins_are_written():
    agents = (REPO / "standards/agents.md").read_text(encoding="utf-8")
    for needle in ["## Light path and full path (D66)", "## Teammate rule", "under about 20 changed lines",
                   "Dillon's approval", "gates, the bench, security or schema", "never edits `plans/`, `ledger/`, `reviews/` or `PROGRESS.md`",
                   "`Explore`, `Plan` and `claude-code-guide`", "Tristan runs a fresh reviewer agent on the PR before merging",
                   "(D69)", "refused inside any agent with those names"]:
        assert needle in agents, needle
    assert "ledger task with their name" in (REPO / "CLAUDE.md").read_text(encoding="utf-8")
    guide = (REPO / "docs/team-guide.md").read_text(encoding="utf-8")
    assert "are not in it, so the roster gate refuses them" not in guide
    assert "Built-in subagents such as `Explore` are refused too" not in guide
    assert guide.count("`Explore`, `Plan` and `claude-code-guide`") >= 3 and "light path" in guide
    assert "redefines the name" not in guide and "redefines the name" not in agents
    assert guide.count("Write, Edit and NotebookEdit are refused inside") >= 2
