"""MCP tools and Studio routes are generated from the ops registry and must agree with hangar.ops.call()."""
from __future__ import annotations

import asyncio
import json
import re
import shutil
import threading
import time
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from hangar import cli, design as design_mod, studio
from hangar.ops import call, registry
from hangar.surfaces import public_name

EXAMPLE = design_mod.DESIGNS_DIR / "example-tailsitter-wing"
HANDWRITTEN_TOOLS = {"save_design", "get_schema", "get_standards", "structural_check", "list_structural_parts"}
STUDIO_ONLY_ROUTES = {"/api/ping", "/api/state", "/api/fea", "/api/fea-file", "/api/design", "/api/export",
                      "/api/check", "/api/check-all", "/api/yaml", "/api/patch", "/api/import-dbf",
                      "/api/fea-setup", "/api/rescan"}


def _mcp():
    pytest.importorskip("mcp")
    from hangar import mcp_server
    return mcp_server


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """A designs/ folder holding only the example design, and a private .studio/ cache."""
    designs = tmp_path / "designs"
    shutil.copytree(EXAMPLE, designs / "example-tailsitter-wing")
    for mod in (cli, design_mod, studio):
        monkeypatch.setattr(mod, "DESIGNS_DIR", designs, raising=False)
    monkeypatch.setattr(studio, "STUDIO_DIR", tmp_path / ".studio")
    monkeypatch.setattr(studio, "DATA_DIR", tmp_path / ".studio" / "data")
    monkeypatch.setattr(studio, "CACHE_FILE", tmp_path / ".studio" / "cache.json")
    monkeypatch.setattr(studio, "BACKUP_DIR", tmp_path / ".studio" / "backups")
    return designs


def _post(base, path, body):
    req = urllib.request.Request(base + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


@pytest.fixture
def studio_base(sandbox):
    s = studio.Studio()
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), studio.make_handler(s))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{httpd.server_port}"
    t0 = time.time()
    while time.time() - t0 < 240:
        with urllib.request.urlopen(base + "/api/state", timeout=60) as r:
            if not json.loads(r.read())["busy"]:
                break
        time.sleep(0.3)
    else:
        raise AssertionError("studio jobs did not finish")
    yield base
    httpd.shutdown()
    httpd.server_close()


def test_mcp_tools_equal_registry_plus_handwritten():
    names = {t.name for t in asyncio.run(_mcp().mcp.list_tools())}
    generated = {n.replace(".", "_") for n in registry()}
    assert generated <= names
    assert names - generated == HANDWRITTEN_TOOLS
    assert set(_mcp().GENERATED) == generated


def test_mcp_tool_input_schema_matches_op_params():
    by_tool = {n.replace(".", "_"): n for n in registry()}
    for t in asyncio.run(_mcp().mcp.list_tools()):
        if t.name not in _mcp().GENERATED:
            continue
        schema = getattr(t, "inputSchema", None) or t.input_schema
        assert set(schema.get("properties", {})) == {public_name(p) for p in registry()[by_tool[t.name]].params}


@pytest.mark.parametrize("tool, op, kw", [
    ("design_list", "design.list", {}),
    ("design_mass", "design.mass", {"path": str(EXAMPLE)}),
    ("design_get", "design.get", {"path": str(EXAMPLE)}),
])
def test_mcp_tool_returns_same_op_result_as_call(tool, op, kw):
    assert _mcp().GENERATED[tool](**kw) == json.loads(call(op, **kw).to_json())


def test_bad_input_is_input_error_on_call_mcp_and_studio(studio_base):
    bad = str(EXAMPLE) + "-missing"
    a = call("design.mass", path=bad)
    assert a.exit_code == 2 and a.data["error"] == "input"
    m = _mcp().GENERATED["design_mass"](path=bad)
    code, s = _post(studio_base, "/api/op/design.mass", {"path": bad})
    assert code == 400
    assert json.loads(a.to_json()) == m == s


def test_studio_op_route_exists_for_every_registry_op(studio_base):
    for name in registry():
        code, body = _post(studio_base, "/api/op/" + name, {"__probe__": 1})
        assert code == 400, name
        assert body["ok"] is False
        assert body["data"]["error"] == "input"
        assert any("unknown parameter" in m for m in body["messages"])


def test_studio_op_route_returns_same_op_result(studio_base, sandbox):
    sandbox_example = sandbox / "example-tailsitter-wing"
    for op, kw in [("design.list", {}), ("design.mass", {"path": str(sandbox_example)}),
                   ("design.get", {"path": str(sandbox_example)})]:
        code, body = _post(studio_base, "/api/op/" + op, kw)
        assert code == 200
        assert body == json.loads(call(op, **kw).to_json())


def test_studio_op_route_runs_mutating_op_and_rescans(studio_base, sandbox):
    code, body = _post(studio_base, "/api/op/design.new", {"new_id": "copy-2", "template": "example-tailsitter-wing"})
    assert code == 200 and body["ok"] is True
    assert (sandbox / "copy-2" / "plane.yaml").is_file()
    with urllib.request.urlopen(studio_base + "/api/ping", timeout=60) as r:
        assert "copy-2" in json.loads(r.read())["designs"]


def test_studio_unknown_op_is_404(studio_base):
    code, body = _post(studio_base, "/api/op/no.such-op", {})
    assert code == 404
    assert body["ok"] is False and body["data"]["error"] == "input"


def test_no_handwritten_api_routes_left():
    src = Path(studio.__file__).read_text(encoding="utf-8")
    found = set(re.findall(r'"(/api/[a-z0-9/_-]*)"', src))
    assert found == STUDIO_ONLY_ROUTES | {"/api/op/"}


def test_removed_studio_routes_are_gone(studio_base):
    assert _post(studio_base, "/api/new", {"id": "x", "from": "example-tailsitter-wing"})[0] == 404
    try:
        urllib.request.urlopen(studio_base + "/api/yaml?id=example-tailsitter-wing", timeout=60)
        raise AssertionError("GET /api/yaml should be gone")
    except urllib.error.HTTPError as e:
        assert e.code == 404


def test_studio_js_calls_op_route_for_new_and_yaml_read():
    js = (design_mod.REPO_ROOT / "viewer" / "studio.js").read_text(encoding="utf-8")
    assert "op('design.new'" in js
    assert "op('design.get'" in js
    assert "api('new'" not in js
    assert "api('yaml?" not in js


def test_design_export_takes_public_name_format(studio_base, sandbox, tmp_path):
    src = str(sandbox / "example-tailsitter-wing")
    m = _mcp().GENERATED["design_export"](path=src, format="json", out=str(tmp_path / "m.json"))
    assert m["ok"] is True
    assert (tmp_path / "m.json").is_file()
    code, s = _post(studio_base, "/api/op/design.export", {"path": src, "format": "json", "out": str(tmp_path / "s.json")})
    assert code == 200 and s["ok"] is True
    assert (tmp_path / "s.json").read_bytes() == (tmp_path / "m.json").read_bytes()
