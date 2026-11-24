"""T90: one shared ID_RE (hangar/ids.py), always matched with fullmatch, so an id with a trailing newline is refused everywhere."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from hangar import cli, ids, studio
from hangar.ops import call

REPO = Path(__file__).resolve().parents[1]
CORE = REPO / "core" / "hangar"


def test_shared_id_re_matches_exactly():
    assert ids.ID_RE.fullmatch("ok-1_a") is not None
    for bad in ("ok\n", "", "-x", "A", "a/b", "a b", "../x"):
        assert ids.ID_RE.fullmatch(bad) is None, repr(bad)


def test_cli_and_studio_use_the_shared_id_re():
    assert cli.ID_RE is ids.ID_RE and studio.ID_RE is ids.ID_RE


def test_mcp_server_uses_the_shared_id_re_with_fullmatch():
    pytest.importorskip("mcp")
    from hangar import mcp_server
    assert mcp_server.ID_RE is ids.ID_RE and not hasattr(mcp_server, "_ID_RE")
    assert mcp_server._design_path("example-tailsitter-wing").name == "plane.yaml"
    for bad in ("example-tailsitter-wing\n", "x\n", "../x", ""):
        with pytest.raises(ValueError, match="invalid design id"):
            mcp_server._design_path(bad, must_exist=False)


def test_morph_add_option_refuses_ids_with_a_trailing_newline(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    (tmp_path / "knowledge" / "sources").mkdir(parents=True)
    shutil.copy(REPO / "knowledge" / "morphological-chart.yaml", tmp_path / "knowledge" / "morphological-chart.yaml")
    shutil.copy(REPO / "knowledge" / "sources" / "morph-uaav-hybrid-2022.md", tmp_path / "knowledge" / "sources" / "morph-uaav-hybrid-2022.md")
    monkeypatch.chdir(tmp_path)
    chart = tmp_path / "knowledge" / "morphological-chart.yaml"
    before = chart.read_bytes()
    r = call("morph.add-option", dimension="tail", id="x-opt\n", name="X", source="morph-uaav-hybrid-2022")
    assert r.exit_code == 2 and "option id" in " ".join(r.messages)
    r = call("morph.add-option", dimension="tail", id="x-opt", name="X", source="morph-uaav-hybrid-2022\n")
    assert r.exit_code == 2 and "source" in " ".join(r.messages)
    assert chart.read_bytes() == before
    assert call("morph.add-option", dimension="tail", id="x-opt", name="X", source="morph-uaav-hybrid-2022").ok   # a plain id still works


def test_bench_design_and_edit_ops_use_the_shared_id_re():  # T100
    from hangar.ops import bench, design, edit
    assert bench.ID_RE is ids.ID_RE and design.ID_RE is ids.ID_RE and edit.ID_RE is ids.ID_RE
    for rel in ("ops/bench.py", "ops/design.py", "ops/edit.py"):
        assert "from ..cli import ID_RE" not in (CORE / rel).read_text(encoding="utf-8"), rel


def test_research_new_refuses_a_slug_with_a_trailing_newline(tmp_path, monkeypatch):  # T100
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    shutil.copytree(REPO / "knowledge", tmp_path / "knowledge", ignore=shutil.ignore_patterns("diy-projects", "concepts"))
    monkeypatch.chdir(tmp_path)
    r = call("research.new", kind="source", slug="my-paper\n")
    assert r.exit_code == 2 and "slug" in " ".join(r.messages)
    assert not any((tmp_path / "knowledge" / "sources").glob("my-paper*"))
    assert call("research.new", kind="source", slug="my-paper").ok     # a plain slug still works


def test_no_module_matches_ids_with_match_or_defines_its_own_id_pattern():
    for rel in ("cli.py", "studio.py", "mcp_server.py", "ops/morph.py", "ops/design.py", "ops/edit.py", "ops/bench.py", "ops/research.py"):
        assert "ID_RE.match(" not in (CORE / rel).read_text(encoding="utf-8"), rel
    assert "SLUG_RE.match(" not in (CORE / "ops/research.py").read_text(encoding="utf-8")      # T100
    assert 're.compile(r"^[a-z0-9][a-z0-9_-]*$")' not in (CORE / "cli.py").read_text(encoding="utf-8")
    assert 're.compile(r"^[a-z0-9][a-z0-9_-]*$")' not in (CORE / "mcp_server.py").read_text(encoding="utf-8")


@pytest.mark.parametrize("op_name,key", [("bench.run", "agent"), ("bench.run", "task"), ("design.new", "template")])
def test_studio_refusal_of_a_non_id_says_bare_id_not_design_id(op_name, key):
    why = studio.confine_op_params(op_name, {key: "../../x"})
    assert why is not None and "bare id" in why and "design id" not in why and key in why
