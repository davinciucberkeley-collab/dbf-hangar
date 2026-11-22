"""docs/cli.md is generated from the ops registry (plane docs cli) and must stay in sync."""
from __future__ import annotations

from pathlib import Path

from hangar.clidoc import build_cli_reference
from hangar.ops import call, registry

REPO = Path(__file__).resolve().parents[1]


def test_cli_doc_is_current():
    assert (REPO / "docs" / "cli.md").read_bytes() == build_cli_reference().encode("utf-8")


def test_cli_doc_lists_every_op_and_no_missing_command():
    text = build_cli_reference()
    for s in registry().values():
        assert f"### `plane {s.group} {s.verb}`" in text
    for ghost in ("plane bom list", "plane morph list", "plane idea list", "plane davinci push", "plane davinci pull"):
        assert ghost not in text


def test_docs_cli_op_writes_same_bytes(tmp_path):
    r = call("docs.cli", out=tmp_path / "cli.md")
    assert r.ok
    assert (tmp_path / "cli.md").read_bytes() == (REPO / "docs" / "cli.md").read_bytes()
