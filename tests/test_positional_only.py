"""Ledger T6: a JSON key `name` or `spec` is an input error (exit 2), never a Python TypeError / HTTP 500."""
from __future__ import annotations

import pytest

from hangar.ops import _call_spec, call, registry

# the fixtures and the POST helper are the ones test_surfaces_in_sync.py already defines
from test_surfaces_in_sync import _post, sandbox, studio_base  # noqa: F401


def test_call_and_call_spec_take_name_and_spec_positionally():
    r = call("design.list", name="x")
    assert r.ok is False and r.exit_code == 2 and "unknown parameter 'name'" in " ".join(r.messages)
    r = _call_spec(registry()["design.list"], spec="x")
    assert r.ok is False and r.exit_code == 2 and "unknown parameter 'spec'" in " ".join(r.messages)


def test_studio_json_key_name_is_exit_2(studio_base):
    status, body = _post(studio_base, "/api/op/design.list", {"name": "x"})
    assert status == 400 and body["ok"] is False and body["data"]["error"] == "input"


def test_mcp_json_key_name_is_exit_2():
    pytest.importorskip("mcp")
    from hangar import mcp_server
    body = mcp_server.GENERATED["design_list"](name="x")
    assert body["ok"] is False and body["data"]["error"] == "input"
