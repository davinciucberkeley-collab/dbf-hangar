from pathlib import Path
import pytest
from click.testing import CliRunner
from hangar.cli import cli
from hangar.ledger import Ledger

REPO = Path(__file__).resolve().parents[1]
PLAN = REPO / "plans" / "2026-11-20-standardization.md"

@pytest.fixture
def led(tmp_path): return Ledger(tmp_path / "items.yaml")

def test_ids_per_prefix(led):
    assert led.add("task", "a", source="s") == "T1"
    assert led.add("task", "b", source="s") == "T2"
    assert led.add("idea", "c", source="s") == "I1"

def test_dropped_needs_decision_and_is_not_overdue(led):
    t = led.add("task", "OpenCAE GUI port", source="2026-11-11#61:02", due="2026-11-15")
    with pytest.raises(ValueError, match="decided_in"):
        led.set(t, "dropped")
    led.set(t, "dropped", decided_in="2026-11-18#26:16")
    assert t not in led.report_overdue("2026-11-20")

def test_open_past_due_is_overdue(led):
    t = led.add("task", "x", source="s", due="2026-11-19")
    assert led.report_overdue("2026-11-20") == [t]

def test_done_needs_evidence_that_exists(led):
    t = led.add("task", "x", source="s")
    led.set(t, "done", evidence="designs/does-not-exist/plane.yaml")
    assert [i.kind for i in led.check(REPO)] == ["missing-evidence"]
    led.set(t, "done", evidence="https://github.com/davinciucberkeley-collab/dbf-hangar/pull/1")
    assert led.check(REPO) == []

def test_seed_from_plan_has_R1_to_R40_and_D1_to_D10(led):
    led.seed_from_plan(PLAN)
    ids = {i.id for i in led.items}
    assert {f"R{n}" for n in range(1, 41)} <= ids and {f"D{n}" for n in range(1, 11)} <= ids
    assert led.get("D10").status == "open" and led.get("D1").status == "decided"
    assert "U1.3" in led.get("R1").units

def test_seed_is_idempotent_and_keeps_manual_status(led):
    led.seed_from_plan(PLAN); led.set("R1", "done", evidence="https://example.com/pr/1")
    led.seed_from_plan(PLAN)
    assert len([i for i in led.items if i.id == "R1"]) == 1 and led.get("R1").status == "done"

def test_file_validates_against_schema(led):
    import json, jsonschema, yaml
    led.seed_from_plan(PLAN)
    data = yaml.safe_load(led.path.read_text(encoding="utf-8"))
    jsonschema.validate(data, json.loads((REPO / "schema/ledger.schema.json").read_text(encoding="utf-8")))

def test_cli_report_counts_open_prompts(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "ledger").mkdir()
    (tmp_path / "ledger/prompts.jsonl").write_text('{"id":"P1","status":"open","text":"a","session":"s"}\n', encoding="utf-8")
    r = CliRunner().invoke(cli, ["ledger", "report", "--today", "2026-11-20"])
    assert r.exit_code == 0 and "Open prompts: 1" in r.output

def test_committed_ledger_is_seeded():
    led = Ledger(REPO / "ledger" / "items.yaml")
    assert led.get("R39").kind == "ruling"

def test_decided_in_is_required_in_the_call_and_cleared_on_reopen(led):
    t = led.add("task", "x", source="s")
    led.set(t, "superseded", decided_in="D10")
    led.set(t, "open")
    assert led.get(t).decided_in == ""
    with pytest.raises(ValueError, match="decided_in"):
        led.set(t, "dropped")
    with pytest.raises(ValueError, match="decided_in"):
        led.set(t, "superseded")

def test_superseded_without_decided_in_is_an_issue(led):
    t = led.add("task", "x", source="s")
    led.set(t, "superseded", decided_in="D10")
    led.get(t).decided_in = ""
    assert [i.kind for i in led.check(REPO)] == ["dropped-without-decision"]

def test_report_has_overdue_section_and_open_prompt_count(led, tmp_path):
    led.add("task", "late", source="s", due="2026-11-19")
    prompts = tmp_path / "prompts.jsonl"
    prompts.write_text('{"id":"P1","status":"open","text":"a","session":"s"}\n'
                       '{"id":"P2","status":"open","text":"b","session":"s"}\n'
                       '{"id":"P2","status":"addressed","text":"b","session":"s","evidence":"x"}\n', encoding="utf-8")
    text = led.report(today="2026-11-20", prompts=prompts)
    assert "## Overdue as of 2026-11-20" in text and "- T1 (due 2026-11-19): late" in text
    assert "Open prompts: 1" in text
