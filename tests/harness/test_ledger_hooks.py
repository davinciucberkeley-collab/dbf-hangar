import os, subprocess, sys
import pytest
from hookutil import REPO, run_hook
from harness import ledger

def test_ids_increment_and_state_merges(root):
    assert ledger.add_prompt(root, "s1", "a") == "P1"
    assert ledger.add_prompt(root, "s1", "b") == "P2"
    ledger.set_status(root, "P1", "addressed", evidence="commit abc")
    assert [p["id"] for p in ledger.open_prompts(root, "s1")] == ["P2"]

def test_addressed_needs_evidence_and_known_id(root):
    ledger.add_prompt(root, "s1", "a")
    with pytest.raises(ValueError): ledger.set_status(root, "P1", "addressed", evidence="  ")
    with pytest.raises(KeyError): ledger.set_status(root, "P9", "addressed", evidence="x")

def test_log_prompt_hook_logs_and_tells_id(root):
    r = run_hook("log_prompt", {"session_id": "s1", "prompt": "add a BOM gate"}, root)
    assert r.returncode == 0 and "Logged as P1" in r.stdout
    assert ledger.open_prompts(root, "s1")[0]["text"] == "add a BOM gate"

def test_empty_prompt_not_logged(root):
    run_hook("log_prompt", {"session_id": "s1", "prompt": "   "}, root)
    assert ledger.prompts(root) == []

def test_stop_blocked_while_open_then_allowed_when_addressed(root):
    ledger.add_prompt(root, "s1", "keep FEA envelope")
    r = run_hook("stop_gate", {"session_id": "s1", "stop_hook_active": False}, root)
    assert r.returncode == 2 and "P1" in r.stderr
    ledger.set_status(root, "P1", "addressed", evidence="U2.3")
    assert run_hook("stop_gate", {"session_id": "s1"}, root).returncode == 0

def test_other_sessions_prompts_do_not_block(root):
    ledger.add_prompt(root, "s2", "x")
    assert run_hook("stop_gate", {"session_id": "s1"}, root).returncode == 0

def test_override_and_forced_stop_after_three_blocks(root):
    ledger.add_prompt(root, "s1", "x")
    assert run_hook("stop_gate", {"session_id": "s1"}, root, HANGAR_ALLOW_STOP="1").returncode == 0
    codes = [run_hook("stop_gate", {"session_id": "s1", "stop_hook_active": True}, root).returncode for _ in range(4)]
    assert codes == [2, 2, 2, 0]
    assert "stop-forced" in (root / "ledger" / "events.jsonl").read_text()

def test_reinject_after_compaction_lists_open_prompts_and_units(root):
    ledger.add_prompt(root, "s1", "keep FEA envelope")
    out = run_hook("reinject", {"source": "compact", "session_id": "s1"}, root).stdout
    assert "keep FEA envelope" in out and "Unit U9.2: Open thing" in out and "U9.1" not in out

def test_reinject_startup_is_short(root):
    out = run_hook("reinject", {"source": "startup", "session_id": "s1"}, root).stdout
    assert "plans/2026-11-20-x.md" in out and "Open prompts: 0" in out

def test_hook_never_crashes_on_bad_input(root):
    r = subprocess.run([sys.executable, str(REPO / "harness/hooks/stop_gate.py")], input="not json",
                       capture_output=True, text=True, env=dict(os.environ, CLAUDE_PROJECT_DIR=str(root)))
    assert r.returncode == 0

def test_cli_list_and_addressed(root):
    ledger.add_prompt(root, "s1", "a")
    cli = [sys.executable, str(REPO / "harness/ledger.py")]
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(root))
    assert subprocess.run(cli + ["addressed", "P1"], env=env, capture_output=True).returncode == 2
    assert subprocess.run(cli + ["addressed", "P1", "--evidence", "done"], env=env).returncode == 0
    assert "[addressed]" in subprocess.run(cli + ["list"], env=env, capture_output=True, text=True).stdout

def test_non_ascii_prompt_survives_cp1252_console(root):
    r = run_hook("log_prompt", {"session_id": "s1", "prompt": "Ángulo → σ ≤ 2"}, root, PYTHONIOENCODING="cp1252")
    assert r.returncode == 0 and ledger.open_prompts(root, "s1")[0]["text"] == "Ángulo → σ ≤ 2"
    out = run_hook("reinject", {"source": "compact", "session_id": "s1"}, root, PYTHONIOENCODING="cp1252")
    assert out.returncode == 0 and "Ángulo → σ ≤ 2" in out.stdout

def test_deferred_does_not_block_and_needs_reason(root):
    ledger.add_prompt(root, "s1", "which box size?")
    with pytest.raises(ValueError): ledger.set_status(root, "P1", "deferred", evidence="")
    ledger.set_status(root, "P1", "deferred", evidence="asked user for D5")
    assert run_hook("stop_gate", {"session_id": "s1"}, root).returncode == 0

def test_corrupt_line_is_skipped(root):
    ledger.add_prompt(root, "s1", "a")
    with open(root / "ledger" / "prompts.jsonl", "a", encoding="utf-8") as f: f.write("{not json\n")
    ledger.add_prompt(root, "s1", "b")
    assert [p["id"] for p in ledger.open_prompts(root, "s1")] == ["P1", "P2"]

def test_stop_message_has_absolute_ledger_path(root):
    ledger.add_prompt(root, "s1", "x")
    r = run_hook("stop_gate", {"session_id": "s1"}, root)
    assert str(root / "harness" / "ledger.py") in r.stderr or str(root) in r.stderr

def test_instructions_use_running_interpreter(root):
    r = run_hook("log_prompt", {"session_id": "s1", "prompt": "x"}, root)
    assert sys.executable in r.stdout

def test_reinject_lists_deferred(root):
    ledger.add_prompt(root, "s1", "box size?")
    ledger.set_status(root, "P1", "deferred", evidence="asked user")
    out = run_hook("reinject", {"source": "compact", "session_id": "s1"}, root).stdout
    assert "Deferred prompts:" in out and "box size?" in out


@pytest.mark.parametrize("text", [
    '<agent-message from="a1b2">\n[Subagent hand-back] The text below is the final report of a subagent.',
    "<task-notification>\n<task-id>a1b2</task-id>\n<status>completed</status>",
    "  \n[SYSTEM NOTIFICATION] something finished",
    "Another Claude session sent a message: hello",
])
def test_system_messages_are_not_logged(root, text):
    r = run_hook("log_prompt", {"session_id": "s1", "prompt": text}, root)
    assert r.returncode == 0 and r.stdout == ""
    assert ledger.prompts(root) == []


def test_user_prompt_quoting_a_notification_is_still_logged(root):
    run_hook("log_prompt", {"session_id": "s1", "prompt": 'why was <agent-message from="a1"> logged as a prompt?'}, root)
    run_hook("log_prompt", {"session_id": "s1", "prompt": "Please fix: <task-notification> shows up as P5"}, root)
    assert len(ledger.prompts(root)) == 2
