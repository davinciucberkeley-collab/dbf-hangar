"""U1.1: the operations registry, the OpResult contract, and the CLI generated from them."""
from __future__ import annotations

import json
import shutil

import click
import jsonschema
import pytest
import yaml
from click.testing import CliRunner

from hangar import ops
from hangar.cli import cli
from hangar.design import DESIGNS_DIR
from hangar.ops import OpResult, call, registry

EXAMPLE_DIR = DESIGNS_DIR / "example-tailsitter-wing"
OP_RESULT_SCHEMA = json.loads(ops.OP_RESULT_SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def tmp_design_with_type_wingletz(tmp_path):
    dst = tmp_path / "wingletz-plane"
    shutil.copytree(EXAMPLE_DIR, dst)
    data = yaml.safe_load((dst / "plane.yaml").read_text(encoding="utf-8"))
    data["components"][0]["type"] = "wingletz"
    (dst / "plane.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return dst


def test_every_op_result_matches_schema():
    for name in ["design.list", "ops.list"]:
        jsonschema.validate(json.loads(call(name).to_json()), OP_RESULT_SCHEMA)


def test_cli_exposes_every_registered_op(cli_runner):
    out = json.loads(cli_runner.invoke(cli, ["ops", "list", "--json"]).output)["data"]["ops"]
    assert {o["name"] for o in out} == set(registry())


def test_old_validate_alias_matches_new(cli_runner):
    a = cli_runner.invoke(cli, ["validate", str(EXAMPLE_DIR), "--format", "json"])
    b = cli_runner.invoke(cli, ["design", "validate", str(EXAMPLE_DIR), "--json"])
    assert json.loads(a.output)["accepted"] == json.loads(b.output)["data"]["accepted"]


def test_unknown_component_type_gives_skip_not_crash(tmp_design_with_type_wingletz):
    r = call("design.validate", path=str(tmp_design_with_type_wingletz))
    assert not r.ok
    row = next(x for t in r.data["tiers"] if t["tier"] == 0 for x in t["results"] if x["check_id"] == "T0.component_type")
    assert row["status"] == "SKIP" and "wingletz" in row["message"]
    assert not any(x["status"] == "FAIL" for t in r.data["tiers"] if t["tier"] == 0 for x in t["results"])
    assert any("wingletz" in s for s in r.skipped)
    assert len(r.data["tiers"]) > 1


def test_schema_file_is_a_valid_schema_and_rejects_junk():
    jsonschema.Draft202012Validator.check_schema(OP_RESULT_SCHEMA)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"ok": True}, OP_RESULT_SCHEMA)


def test_bad_input_is_exit_2_and_valid_json(cli_runner, tmp_path):
    r = cli_runner.invoke(cli, ["design", "validate", str(tmp_path / "nope"), "--json"])
    body = json.loads(r.output)
    jsonschema.validate(body, OP_RESULT_SCHEMA)
    assert r.exit_code == 2 and body["ok"] is False and body["data"]["error"] == "input"
    assert "cannot load" in body["messages"][0]


def test_call_unknown_param_is_input_error_not_exception():
    r = call("design.mass", path=str(EXAMPLE_DIR), bogus=1)
    assert not r.ok and r.exit_code == 2


def test_call_bad_literal_value_is_input_error():
    assert call("design.validate", path=str(EXAMPLE_DIR), tier="10").exit_code == 2


def test_failed_check_is_exit_1(cli_runner, tmp_design_with_type_wingletz):
    r = cli_runner.invoke(cli, ["design", "validate", str(tmp_design_with_type_wingletz), "--json"])
    assert r.exit_code == 1 and json.loads(r.output)["data"].get("error") is None


def test_legacy_command_name_collision_keeps_legacy_behaviour():
    legacy = click.Group("plane")

    @legacy.command("schema")
    def _legacy_schema():
        click.echo("legacy-path")

    def _docs(*, out: str) -> OpResult:
        return OpResult(True, {"out": out})

    spec = ops._build_spec(_docs, name="schema.docs", summary="docs", mutates=False, adapters=(), render=None)
    from hangar.cli import _attach_ops
    _attach_ops(legacy, {spec.name: spec})
    runner = CliRunner()
    assert runner.invoke(legacy, ["schema"]).output.strip() == "legacy-path"
    assert json.loads(runner.invoke(legacy, ["schema", "docs", "--out", "x", "--json"]).output)["data"] == {"out": "x"}


def test_call_none_for_defaulted_param_is_input_error():
    r = call("design.validate", path=str(EXAMPLE_DIR), tier=None)
    assert r.exit_code == 2 and r.data["error"] == "input"


def test_call_none_for_required_param_is_input_error(tmp_path):
    assert call("design.new", new_id=None).exit_code == 2
    assert call("design.export", path=str(EXAMPLE_DIR), format_=None, out=str(tmp_path / "x.json")).exit_code == 2
    assert not (tmp_path / "x.json").exists()
