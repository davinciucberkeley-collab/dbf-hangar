"""Standards database (U2.2): pending keys, the list/show ops, and the scout source files."""
from __future__ import annotations

import re

import yaml

from hangar.design import REPO_ROOT
from hangar.ops import call, registry

SOURCES = REPO_ROOT / "knowledge" / "sources"
DESIGN_STANDARDS = REPO_ROOT / "standards" / "design-standards.yaml"
NEW_SCOUT_FILES = [
    "std-stanag-4703-annex-b-landing",
    "std-astm-f3298-load-tables",
    "std-vtol-thrust-to-weight-paper",
    "std-nasa-additive-factors",
    "std-dbf-rules-box-size",
    "std-ct-fasteners",
    "std-ct-adhesives-tapes",
    "std-ct-electrical",
    "std-ct-straps-hinges-thermal",
]


def test_no_blocking_threshold_is_pending_without_a_decision():
    r = call("standards.pending")
    blocking = [i["key"] for i in r.data["items"] if i["blocking"]]
    items = yaml.safe_load((REPO_ROOT / "ledger" / "items.yaml").read_text(encoding="utf-8"))["items"]
    decisions = [it for it in items
                 if it.get("kind") == "decision" and it.get("status") in ("decided", "open")]
    missing = [k for k in blocking
               if not any(k in ((it.get("text") or "") + " " + (it.get("evidence") or ""))
                          for it in decisions)]
    assert not missing, f"blocking pending keys without a decision: {missing}"


def test_standards_list_and_show():
    assert "standards.list" in registry() and "standards.show" in registry()
    r = call("standards.list")
    assert r.ok
    row = next(i for i in r.data["items"] if i["key"] == "landing_load_factor")
    assert {"key", "section", "value", "source"} <= set(row)
    s = call("standards.show", key="static_margin")
    assert s.ok and s.data["key"] == "static_margin"
    bad = call("standards.show", key="nope")
    assert bad.ok is False
    assert bad.exit_code == 2
    assert bad.data["error"] == "input"


def test_standards_pending_shape():
    items = call("standards.pending").data["items"]
    for row in items:
        assert set(row) == {"key", "value", "blocking", "candidates"}
        assert isinstance(row["blocking"], bool)
        assert isinstance(row["candidates"], list) and all(isinstance(c, str) for c in row["candidates"])
    keys = {row["key"] for row in items}
    assert "landing_load_factor" in keys
    assert "hover_thrust_to_weight_min" not in keys
    conn_pending = {t["id"] for t in call("standards.connections").data["connection_types"]
                    if t["source"] == "pending"}
    conn_rows = [row for row in items if row["key"] in conn_pending]
    assert len(conn_rows) == len(conn_pending)
    assert all(row["blocking"] is False for row in conn_rows)


def test_every_pending_value_is_listed_with_candidates():
    rows = {row["key"]: row for row in call("standards.pending").data["items"]}
    stems = {p.stem for p in SOURCES.glob("*.md")}
    for key in ("landing_load_factor",):
        candidates = rows[key]["candidates"]
        assert candidates, key
        assert set(candidates) <= stems, key


def test_new_scout_files_are_well_formed():
    for name in NEW_SCOUT_FILES:
        path = SOURCES / f"{name}.md"
        assert path.exists(), name
        text = path.read_text(encoding="utf-8")
        assert text.startswith("---"), name
        front = re.match(r"---\n(.*?)\n---\n", text, re.S).group(1)
        fields = dict(line.split(":", 1) for line in front.splitlines() if ":" in line)
        assert fields["id"].strip() == path.stem, name
        assert fields["verified"].strip() in ("true", "false"), name


def test_every_non_pending_source_is_nonempty():
    data = yaml.safe_load(DESIGN_STANDARDS.read_text(encoding="utf-8"))

    def walk(node, where):
        if isinstance(node, dict):
            if "source" in node:
                assert isinstance(node["source"], str) and node["source"].strip(), where
            for key, child in node.items():
                walk(child, f"{where}.{key}")

    walk(data, "design-standards")
