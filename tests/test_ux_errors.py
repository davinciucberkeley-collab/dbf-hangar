"""U4.26: error messages say what to do next (audit W24-Au2)."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from hangar.cli import cli
from hangar.ops import call

REPO = Path(__file__).resolve().parents[1]


def _msgs(args):
    r = CliRunner().invoke(cli, args + ["--json"])
    return r.exit_code, json.loads(r.output)["messages"][0]


def test_get_on_a_missing_design_says_where_to_look(tmp_path):
    code, msg = _msgs(["design", "get", str(tmp_path / "does-not-exist")])
    assert code == 2
    assert msg == f"no design folder at {tmp_path / 'does-not-exist'}; see `plane design list`"


def test_set_bad_key_names_the_prefix_and_suggests(tmp_path):
    dst = tmp_path / "concept-a-param"
    shutil.copytree(REPO / "designs" / "concept-a-param", dst, ignore=shutil.ignore_patterns("fea"))
    code, msg = _msgs(["design", "set", str(dst), "parameters.spna_mm", "--value", "1", "--why", "t"])
    assert code == 2
    assert msg.startswith("parameters.spna_mm: no key 'spna_mm' under 'parameters' (have: ")
    assert msg.endswith("; did you mean 'span_mm'?")


def test_set_bad_top_level_key_says_top_level(tmp_path):
    dst = tmp_path / "example-tailsitter-wing"
    shutil.copytree(REPO / "designs" / "example-tailsitter-wing", dst)
    code, msg = _msgs(["design", "set", str(dst), "nme", "--value", "x", "--why", "t"])
    assert code == 2
    assert msg.startswith("nme: no key 'nme' at the top level (have: ") and msg.endswith("; did you mean 'name'?")


def test_set_without_why_says_why_is_required(tmp_path):
    dst = tmp_path / "example-tailsitter-wing"
    shutil.copytree(REPO / "designs" / "example-tailsitter-wing", dst)
    code, msg = _msgs(["design", "set", str(dst), "requirements.mtow_g", "--value", "1"])
    assert code == 2
    assert msg == "--why is required: say why the value changes (it goes to CHANGELOG.yaml)"


def test_new_with_unknown_template_lists_templates():
    r = call("design.new", new_id="zz-never-created", template="nope")
    assert not r.ok and r.exit_code == 2
    assert r.messages[0].startswith("template 'nope' not found; available: ")
    assert "example-tailsitter-wing" in r.messages[0]
    assert not (REPO / "designs" / "zz-never-created").exists()
