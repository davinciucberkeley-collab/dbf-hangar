from __future__ import annotations
import subprocess
from pathlib import Path
import pytest, yaml
from click.testing import CliRunner
from hangar import cli, ledger, progress
from hangar.ops import call, registry

REPO = Path(__file__).resolve().parents[1]
WEEK = "2026-11-23"


@pytest.fixture
def root(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _inbox(root, items, name="2026-11-24.yaml"):
    p = root / "ledger" / "inbox" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump({"items": items}), encoding="utf-8")
    return p


GOOD = [{"kind": "task", "text": "Order foam", "source": "transcript 11-24 00:03:10", "owner": "ana"},
        {"kind": "idea", "text": "Try coroplast", "source": "transcript 11-24 00:07:00"}]


def test_new_ops_registered():
    assert {"ledger.seed", "ledger.add", "ledger.set", "ledger.check", "ledger.report", "ledger.ingest",
            "idea.add", "update.new", "update.add", "update.publish"} <= set(registry())


def test_count_table_is_shared():
    items = [ledger.Item(id="T1", kind="task", text="a", source="s")]
    full = ledger.count_table(items, total_row=True)
    short = ledger.count_table(items, total_row=False)
    assert full[:-1] == short
    assert full[-1].startswith("| **all** |")
    assert short[0].startswith("| kind |")
    assert '"| kind | "' not in Path(progress.__file__).read_text(encoding="utf-8")


def test_ledger_add_set_check(root):
    r = call("ledger.add", kind="task", text="x", source="t", owner="a")
    assert r.ok and r.data["id"] == "T1"
    assert call("ledger.set", item_id="T1", status="done").exit_code == 2
    assert call("ledger.set", item_id="T1", status="done", evidence="no/such/file.md").ok
    r = call("ledger.check")
    assert r.exit_code == 1
    assert r.data["issues"][0]["kind"] == "missing-evidence"
    assert call("ledger.set", item_id="T1", status="done", evidence="abc1234").ok
    assert call("ledger.check").exit_code == 0


def test_ledger_set_updates_due_units_and_note_on_an_open_item(root):  # T52
    call("ledger.add", kind="task", text="x", source="t", due="2026-12-01")
    r = call("ledger.set", item_id="T1", status="open", due="2026-12-15", units="U4.3, v1.1", note="triage 2026-11-23: keep")
    assert r.ok, r.messages
    item = ledger.Ledger(root / "ledger" / "items.yaml").get("T1")
    assert (item.status, item.due, item.units, item.text) == ("open", "2026-12-15", ["U4.3", "v1.1"], "x [triage 2026-11-23: keep]")


def test_ledger_set_without_the_new_options_keeps_due_units_text(root):  # T52
    call("ledger.add", kind="task", text="x", source="t", due="2026-12-01")
    call("ledger.set", item_id="T1", status="open", units="U1.1")
    assert call("ledger.set", item_id="T1", status="open").ok
    item = ledger.Ledger(root / "ledger" / "items.yaml").get("T1")
    assert (item.due, item.units, item.text) == ("2026-12-01", ["U1.1"], "x")


def test_ledger_set_rejects_a_bad_due_exit2(root):  # T52
    call("ledger.add", kind="task", text="x", source="t")
    r = call("ledger.set", item_id="T1", status="open", due="next week")
    assert r.exit_code == 2 and any("YYYY-MM-DD" in m for m in r.messages)


def test_ledger_report_matches_method(root):
    call("ledger.add", kind="task", text="x", source="t")
    r = call("ledger.report", today="2026-11-20")
    expected = ledger.Ledger(root / "ledger" / "items.yaml").report(
        today="2026-11-20", prompts=root / "ledger" / "prompts.jsonl")
    assert r.data["markdown"] == expected


def test_ingest_valid_appends(root):
    r = call("ledger.ingest", path=str(_inbox(root, GOOD)))
    assert r.ok
    assert r.data["added"] == ["T1", "I1"]
    assert ledger.Ledger(root / "ledger" / "items.yaml").get("T1").owner == "ana"


def test_ingest_invalid_writes_nothing(root):
    r = call("ledger.ingest", path=str(_inbox(root, [{"kind": "chore", "text": "x", "source": "s"}])))
    assert r.exit_code == 2
    assert not (root / "ledger" / "items.yaml").exists()


def test_ingest_invalid_keeps_existing_bytes(root):
    call("ledger.add", kind="task", text="already here", source="t")
    before = (root / "ledger" / "items.yaml").read_bytes()
    bad = [{"kind": "task", "text": "good one", "source": "s"}, {"kind": "task", "text": "no source"}]
    r = call("ledger.ingest", path=str(_inbox(root, bad)))
    assert r.exit_code == 2
    assert (root / "ledger" / "items.yaml").read_bytes() == before


def test_ingest_dry_run_writes_nothing(root):
    r = call("ledger.ingest", path=str(_inbox(root, GOOD)), dry_run=True)
    assert r.ok
    assert r.data["would_add"] == 2
    assert not (root / "ledger" / "items.yaml").exists()


def test_ingest_duplicate_text_skipped(root):
    call("ledger.ingest", path=str(_inbox(root, GOOD)))
    r = call("ledger.ingest", path=str(_inbox(root, GOOD)))
    assert r.data["added"] == []
    assert len(r.skipped) == 2


def test_ingest_same_text_in_another_kind_is_kept(root):  # T17
    call("ledger.ingest", path=str(_inbox(root, [{"kind": "task", "text": "Order foam", "source": "s"}])))
    r = call("ledger.ingest", path=str(_inbox(root, [{"kind": "idea", "text": "Order foam", "source": "s"},
                                                      {"kind": "task", "text": " order FOAM ", "source": "s"}], name="b.yaml")))
    assert len(r.data["added"]) == 1 and len(r.skipped) == 1
    assert ledger.Ledger(root / "ledger" / "items.yaml").get(r.data["added"][0]).kind == "idea"


def test_cli_ingest_invalid_exit2(root):
    runner = CliRunner()
    r = runner.invoke(cli.cli, ["ledger", "ingest", str(_inbox(root, [{"kind": "x"}]))])
    assert r.exit_code == 2
    assert not (root / "ledger" / "items.yaml").exists()
    r = runner.invoke(cli.cli, ["ledger", "ingest", str(_inbox(root, GOOD))])
    assert r.exit_code == 0
    assert "added 2" in r.output


def test_cli_ledger_still_works(root):
    runner = CliRunner()
    r = runner.invoke(cli.cli, ["ledger", "add", "task", "hello", "--source", "t"])
    assert r.exit_code == 0
    assert r.output.strip() == "T1"
    r = runner.invoke(cli.cli, ["ledger", "set", "T1", "done"])
    assert r.exit_code == 2
    plan = REPO / "plans" / "2026-11-20-standardization.md"
    r = runner.invoke(cli.cli, ["ledger", "seed", "--plan", str(plan)])
    assert r.exit_code == 0


def test_idea_add_writes_file(root):
    r = call("idea.add", title="Use foam", body="Cheap.", by="alex")
    assert r.ok
    assert r.data["path"].startswith("knowledge/ideas/")
    text = (root / r.data["path"]).read_text(encoding="utf-8")
    assert text.startswith('---\ntitle: "Use foam"')
    assert "Cheap." in text


def test_idea_add_twice_same_day_exit2(root):
    assert call("idea.add", title="Use foam", body="Cheap.", by="alex").ok
    assert call("idea.add", title="Use foam", body="Cheap.", by="alex").exit_code == 2


def test_update_flow(root):
    assert call("update.new", week=WEEK).ok
    assert call("update.new", week=WEEK).exit_code == 2
    assert call("update.add", week=WEEK, person="Ana", link="https://example.com/a", changed="wing sized").ok
    assert call("update.add", week=WEEK, person="Ana", link="https://example.com/b", changed="wing resized").ok
    doc = yaml.safe_load((root / "updates" / WEEK / "updates.yaml").read_text(encoding="utf-8"))
    assert len(doc["entries"]) == 1
    assert doc["entries"][0]["link"] == "https://example.com/b"
    assert call("update.add", week=WEEK, person="Bo", link="not a link", changed="x").exit_code == 2
    r = call("update.publish", week=WEEK)
    assert r.data["url"] == "https://davinciucberkeley-collab.github.io/dbf-hangar/updates/2026-11-23/"
    assert len(r.data["lines"]) == 1
    page = (root / "viewer" / "updates" / WEEK / "index.html").read_text(encoding="utf-8")
    assert "Ana" in page and "https://example.com/b" in page and "wing resized" in page
    index = root / "viewer" / "updates" / "index.html"
    assert index.exists()
    assert "2026-11-23" in index.read_text(encoding="utf-8")


def test_update_html_is_escaped(root):
    call("update.new", week=WEEK)
    call("update.add", week=WEEK, person="<b>x</b>", link="https://example.com/a", changed="wing")
    call("update.publish", week=WEEK)
    html = (root / "viewer" / "updates" / WEEK / "index.html").read_text(encoding="utf-8")
    assert "&lt;b&gt;x&lt;/b&gt;" in html
    assert "<b>x</b>" not in html


def test_update_publish_errors(root):
    assert call("update.publish", week=WEEK).exit_code == 2
    call("update.new", week=WEEK)
    assert call("update.publish", week=WEEK).exit_code == 2
    assert call("update.new", week="11-23").exit_code == 2


def test_viewer_updates_is_gitignored():
    assert subprocess.run(["git", "check-ignore", "-q", "viewer/updates/2026-11-23/index.html"],
                          cwd=REPO).returncode == 0


def test_ledger_set_rejects_an_impossible_due_date_exit2(root):  # T85
    call("ledger.add", kind="task", text="x", source="t")
    r = call("ledger.set", item_id="T1", status="open", due="2026-13-45")
    assert r.exit_code == 2 and any("YYYY-MM-DD" in m for m in r.messages)
