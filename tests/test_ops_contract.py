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
    assert "no design folder at" in body["messages"][0]


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


def test_registry_retries_after_a_module_fails_mid_import(tmp_path, monkeypatch):  # T3
    import importlib
    import sys
    (tmp_path / "zz_flaky.py").write_text(
        "import os\n"
        "from hangar.ops import op, OpResult\n"
        "\n"
        "\n"
        "@op(name='zz.flaky', summary='registers, then the module fails')\n"
        "def flaky() -> OpResult:\n"
        "    return OpResult(True, {})\n"
        "\n"
        "\n"
        "if os.environ.get('ZZ_FLAKY_FAIL') == '1':\n"
        "    raise RuntimeError('boom')\n", encoding="utf-8")
    monkeypatch.setattr(ops, "__path__", [*ops.__path__, str(tmp_path)])
    monkeypatch.setattr(ops, "_LOADED", False)
    importlib.invalidate_caches()
    try:
        monkeypatch.setenv("ZZ_FLAKY_FAIL", "1")
        with pytest.raises(RuntimeError, match="boom"):
            ops.registry()
        assert "zz.flaky" not in ops._REGISTRY, "a failed import must not leave its ops behind"
        monkeypatch.setenv("ZZ_FLAKY_FAIL", "0")
        reg = ops.registry()
        assert "zz.flaky" in reg
        assert "design.get" in reg, "ops of modules that imported fine before the failure stay registered"
    finally:
        ops._REGISTRY.pop("zz.flaky", None)
        sys.modules.pop("hangar.ops.zz_flaky", None)


def test_registry_keeps_the_ops_of_a_module_that_a_failing_module_imported(tmp_path, monkeypatch):  # T86: nested ops import
    import importlib
    import sys
    (tmp_path / "zz_b_inner.py").write_text(
        "from hangar.ops import op, OpResult\n"
        "\n"
        "\n"
        "@op(name='zz.inner', summary='registered by the inner module, which stays cached')\n"
        "def inner() -> OpResult:\n"
        "    return OpResult(True, {})\n", encoding="utf-8")
    (tmp_path / "zz_a_outer.py").write_text(   # sorts first, so the registry loads it first and it imports the inner one
        "import os\n"
        "from hangar.ops import op, OpResult\n"
        "from hangar.ops import zz_b_inner  # noqa: F401\n"
        "\n"
        "\n"
        "@op(name='zz.outer', summary='registers, then the module fails')\n"
        "def outer() -> OpResult:\n"
        "    return OpResult(True, {})\n"
        "\n"
        "\n"
        "if os.environ.get('ZZ_OUTER_FAIL') == '1':\n"
        "    raise RuntimeError('boom')\n", encoding="utf-8")
    monkeypatch.setattr(ops, "__path__", [*ops.__path__, str(tmp_path)])
    monkeypatch.setattr(ops, "_LOADED", False)
    importlib.invalidate_caches()
    try:
        monkeypatch.setenv("ZZ_OUTER_FAIL", "1")
        with pytest.raises(RuntimeError, match="boom"):
            ops.registry()
        assert "zz.outer" not in ops._REGISTRY, "the failed module's own op is dropped"
        assert "zz.inner" in ops._REGISTRY, "the op of the module it imported stays: that import is cached and never re-runs"
        monkeypatch.setenv("ZZ_OUTER_FAIL", "0")
        reg = ops.registry()
        assert "zz.outer" in reg and "zz.inner" in reg
    finally:
        for name in ("zz.outer", "zz.inner"):
            ops._REGISTRY.pop(name, None)
        for mod in ("hangar.ops.zz_a_outer", "hangar.ops.zz_b_inner"):
            sys.modules.pop(mod, None)
        for attr in ("zz_a_outer", "zz_b_inner"):
            ops.__dict__.pop(attr, None)


def test_registry_drops_the_op_of_an_imported_module_that_failed_after_registering(tmp_path, monkeypatch):  # T86 (W12-R blocker): inner import fails
    import importlib
    import sys
    (tmp_path / "zz_d_bad.py").write_text(
        "import os\n"
        "from hangar.ops import op, OpResult\n"
        "\n"
        "\n"
        "@op(name='zz.badinner', summary='registers, then its own import fails')\n"
        "def bad_inner() -> OpResult:\n"
        "    return OpResult(True, {})\n"
        "\n"
        "\n"
        "if os.environ.get('ZZ_BAD_FAIL') == '1':\n"
        "    raise RuntimeError('inner boom')\n", encoding="utf-8")
    (tmp_path / "zz_c_outer.py").write_text(   # sorts first, so it loads first and imports the failing inner one
        "from hangar.ops import zz_d_bad  # noqa: F401\n",
        encoding="utf-8")
    monkeypatch.setattr(ops, "__path__", [*ops.__path__, str(tmp_path)])
    monkeypatch.setattr(ops, "_LOADED", False)
    importlib.invalidate_caches()
    try:
        monkeypatch.setenv("ZZ_BAD_FAIL", "1")
        with pytest.raises(RuntimeError, match="inner boom"):
            ops.registry()
        assert "zz.badinner" not in ops._REGISTRY, "the failed inner module's op is dropped: it is not cached and will re-run"
        with pytest.raises(RuntimeError, match="inner boom"):   # the retry must reach the real error, not 'duplicate op name'
            ops.registry()
        monkeypatch.setenv("ZZ_BAD_FAIL", "0")   # T102: the fault is gone; the third call recovers and registers the op
        assert "zz.badinner" in ops.registry()
    finally:
        ops._REGISTRY.pop("zz.badinner", None)
        for mod in ("hangar.ops.zz_c_outer", "hangar.ops.zz_d_bad"):
            sys.modules.pop(mod, None)
        for attr in ("zz_c_outer", "zz_d_bad"):
            ops.__dict__.pop(attr, None)
