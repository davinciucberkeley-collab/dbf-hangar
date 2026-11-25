from __future__ import annotations
import json
import re

import pytest

from hangar.design import REPO_ROOT
from hangar.importers.changelog import import_decisions
from hangar.ledger import Ledger

CHANGELOG = """| ID | Decision |
|---|---|
| **D-210** | **Cup fillets.** fillet text ten |
| **D-211** | **Wing core.** wing text eleven |
| **D-212 (first version, SUPERSEDED by D-212 rev 2 below; REJECTED by the review)** | **Elevon linkage.** first text |
| **D-212 rev 2 (SUPERSEDED by D-212 rev 3 below)** | second text |
| **D-212 rev 3** | third text |
| **D-212 rev 3 minors (T-063 follow-up, 2026-11-19; mechanism engineering)** | minors text |
| **D-213 landing side-load limit re-based (T-064, 2026-11-19)** | **Landing.** landing text | refs |
| **T-096 F-5 rework (media only, 2026-11-23): film S4** | media text |
| **D-214 structures_run.md regenerated (T-065)** | structures text |
| **D-214 repeated row** | duplicate text |
"""


@pytest.fixture
def run(tmp_path):
    p = tmp_path / "dbf" / "redesign" / "params"
    p.mkdir(parents=True)
    (p / "CHANGE-LOG.md").write_text(CHANGELOG, encoding="utf-8", newline="\n")
    msgs: list[str] = []
    out = import_decisions(tmp_path / "dbf", tmp_path / "items.yaml", log=msgs.append)
    return out, msgs, Ledger(tmp_path / "items.yaml"), tmp_path, msgs


def test_rows_with_title_in_first_cell_are_imported(run):
    out, _, led, _, _ = run
    assert out == {"changelog": 8, "decisions_md": 0, "skipped": 0, "duplicates": 1}
    assert {i.id for i in led.items if i.id.startswith("D-")} == {
        "D-210", "D-211", "D-212", "D-212b", "D-212c", "D-212d", "D-213", "D-214"}


def test_d212_revisions_have_distinct_ids_and_sources(run):
    _, _, led, _, _ = run
    assert led.get("D-212b").source == "CHANGE-LOG#D-212b"
    d = led.get("D-212d").text
    assert d.startswith("rev 3 minors (T-063 follow-up") and "minors text" in d
    t = led.get("D-213").text
    assert "landing side-load limit re-based (T-064, 2026-11-19)" in t and "landing text" in t
    assert not any("*" in i.text for i in led.items)


def test_bare_id_rows_keep_their_text(run):
    assert run[2].get("D-210").text == "Cup fillets. fillet text ten"


def test_unnumbered_row_is_logged_not_imported(run):
    _, msgs, led, _, _ = run
    hits = [m for m in msgs if "row without a D-number skipped" in m]
    assert len(hits) == 1 and "T-096" in hits[0]
    assert not any("T-096" in i.id for i in led.items)


def test_second_run_is_idempotent(run):
    _, _, _, tmp_path, _ = run
    again = import_decisions(tmp_path / "dbf", tmp_path / "items.yaml", log=lambda m: None)
    assert again == {"changelog": 0, "decisions_md": 0, "skipped": 8, "duplicates": 1}


def test_new_ids_match_the_ledger_pattern(run):
    _, _, led, _, _ = run
    schema = json.loads((REPO_ROOT / "schema" / "ledger.schema.json").read_text(encoding="utf-8"))
    pat = re.compile(schema["$defs"]["item"]["properties"]["id"]["pattern"])
    assert led.items and all(pat.match(i.id) for i in led.items)


def test_proposed_rows_are_open_not_decided(tmp_path):
    # D-127 and D-128 carry "(PROPOSED)" in the id cell: imported under the bare id, status open;
    # the unmarked D-129 stays decided (derivation: 3 rows -> changelog 3, no skips).
    p = tmp_path / "dbf" / "redesign" / "params"
    p.mkdir(parents=True)
    (p / "CHANGE-LOG.md").write_text(
        "| ID | Decision |\n|---|---|\n"
        "| **D-127 (PROPOSED)** | proposed one |\n"
        "| **D-128 (PROPOSED, awaiting review)** | proposed two |\n"
        "| **D-129** | settled |\n", encoding="utf-8", newline="\n")
    out = import_decisions(tmp_path / "dbf", tmp_path / "items.yaml", log=lambda m: None)
    led = Ledger(tmp_path / "items.yaml")
    assert out["changelog"] == 3 and out["skipped"] == 0
    assert led.get("D-127").status == "open" and led.get("D-128").status == "open"
    assert led.get("D-129").status == "decided"
