"""Plane Studio and the comment-preserving edit path it shares with `plane new`."""
from __future__ import annotations

import json
import shutil
import threading
import time
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from hangar import cli, design as design_mod, studio
from hangar.design import load_design
from hangar.gates.mechanisms import simulate_mechanism
from hangar.index import index_extras, mechanism_sweeps
from hangar.yamlio import dump, load

FIXTURES = Path(__file__).parent / "fixtures"

EXAMPLE = design_mod.DESIGNS_DIR / "example-tailsitter-wing"


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


def test_new_design_copies_files_and_keeps_comments(sandbox):
    (sandbox / "example-tailsitter-wing" / "meshes").mkdir()
    (sandbox / "example-tailsitter-wing" / "meshes" / "part.stl").write_text("solid x\nendsolid x\n")
    p = cli.new_design("my-copy", "example-tailsitter-wing")
    text = p.read_text()
    assert (sandbox / "my-copy" / "meshes" / "part.stl").is_file(), "mesh files must travel with the copy"
    assert "id: my-copy" in text and "status: concept" in text
    assert "# stacked ply; FDM fit unverifiable" in text, "inline comments survive the copy"
    assert text.startswith("# Copied from designs/example-tailsitter-wing")
    with pytest.raises(ValueError):
        cli.new_design("my-copy", "example-tailsitter-wing")
    with pytest.raises(ValueError):
        cli.new_design("Bad Name", "example-tailsitter-wing")


def _call(base, path, body=None):
    req = urllib.request.Request(base + path, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if r.headers.get_content_type() == "application/json" else raw)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def _wait_idle(base, timeout=240):
    t0 = time.time()
    while time.time() - t0 < timeout:
        _, st = _call(base, "/api/state")
        if not st["busy"]:
            return st
        time.sleep(0.3)
    raise AssertionError("studio jobs did not finish")


def test_studio_api_end_to_end(sandbox):
    s = studio.Studio()
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), studio.make_handler(s))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{httpd.server_port}"
    try:
        st = _wait_idle(base)
        assert [j["state"] for j in st["jobs"]] == ["done"]
        _, index = _call(base, "/data/index.json")
        assert index["version"] == 2 and "generated_at" in index and "scorecards" in index
        (entry,) = index["designs"]
        assert index["studio"] and entry["id"] == "example-tailsitter-wing" and entry["accepted"] and not entry["pending"]
        assert _call(base, "/data/" + entry["glb"])[0] == 200

        # form edit: one field, saved with a backup, re-checked
        code, res = _call(base, "/api/op/design.set", {"path": str(sandbox / "example-tailsitter-wing"),
            "key": "components[wing].mass_g", "value": "999", "why": "test edit", "kind": "modify"})
        assert code == 200 and res["ok"] and res["data"]["changed"]
        assert "mass_g: 999" in (sandbox / "example-tailsitter-wing" / "plane.yaml").read_text()
        assert "test edit" in (sandbox / "example-tailsitter-wing" / "CHANGELOG.yaml").read_text()
        _wait_idle(base)
        _, index = _call(base, "/data/index.json")
        assert index["designs"][0]["mass_g"] > entry["mass_g"]

        # bad edits are refused and leave the file alone
        assert _call(base, "/api/op/design.set", {"path": str(sandbox / "example-tailsitter-wing"), "key": "components[wing].mass_g", "value": "1", "why": ""})[0] == 400
        assert _call(base, "/api/op/design.new", {"new_id": "../escape", "template": "example-tailsitter-wing"})[0] == 400

        # copy, then download the scorecard report
        assert _call(base, "/api/op/design.new", {"new_id": "copy-1", "template": "example-tailsitter-wing"})[0] == 200
        assert (sandbox / "copy-1" / "plane.yaml").is_file()
        _wait_idle(base)
        code, report = _call(base, "/api/export?id=copy-1&format=report")
        assert code == 200 and report.startswith(b"# Scorecard: copy-1")

        # a cross-site POST is refused
        req = urllib.request.Request(base + "/api/check-all", data=b"{}", headers={"Origin": "https://evil.example"})
        with pytest.raises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(req, timeout=10)
        assert e.value.code == 403
    finally:
        httpd.shutdown()
        httpd.server_close()


def _serve_studio(sandbox):
    s = studio.Studio()
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), studio.make_handler(s))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_port}"


@pytest.mark.parametrize("eol", [b"\n", b"\r\n"], ids=["lf", "crlf"])
def test_studio_set_changes_only_the_edited_line(sandbox, eol):
    src = Path(design_mod.REPO_ROOT) / "tests" / "fixtures" / "concept-a-frozen" / "plane.yaml"
    raw = src.read_bytes().replace(b"\r\n", b"\n")
    before = raw.replace(b"\n", eol)
    dst = sandbox / "concept-a" / "plane.yaml"
    dst.parent.mkdir()
    dst.write_bytes(before)
    httpd, base = _serve_studio(sandbox)
    try:
        code, res = _call(base, "/api/op/design.set", {"path": str(sandbox / "concept-a"),
            "key": "components[pwr-001].mass_g", "value": "275", "why": "test", "kind": "modify"})
        assert code == 200 and res["ok"]
    finally:
        httpd.shutdown()
        httpd.server_close()
    after = dst.read_bytes()
    a, b = before.splitlines(keepends=True), after.splitlines(keepends=True)
    assert len(a) == len(b)
    diff = [(x, y) for x, y in zip(a, b) if x != y]
    assert len(diff) == 1
    assert diff[0][0].strip() == b"mass_g: 270"
    assert diff[0][1].strip() == b"mass_g: 275"
    assert diff[0][0].endswith(eol) and diff[0][1].endswith(eol)
    assert (b"\r\n" in after) == (eol == b"\r\n")
    assert b"E-WNG-10" in after
    assert before.count(eol) == after.count(eol)
    log = yaml.safe_load(dst.with_name("CHANGELOG.yaml").read_text())
    assert isinstance(log, list) and len(log) == 1
    assert log[0]["key"] == "components[pwr-001].mass_g"
    assert log[0]["old"] == 270 and log[0]["new"] == 275
    assert log[0]["why"] == "test" and log[0]["kind"] == "modify"


def test_studio_has_no_reemitting_save_routes(sandbox):
    httpd, base = _serve_studio(sandbox)
    try:
        assert _call(base, "/api/patch", {"id": "x", "changes": []})[0] == 404
        assert _call(base, "/api/yaml", {"id": "x", "text": ""})[0] == 404
    finally:
        httpd.shutdown()
        httpd.server_close()
    assert not hasattr(studio.Studio, "patch")
    assert not hasattr(studio.Studio, "write_yaml")


PUBLIC_KEYS = {"id", "kind", "status", "owner", "summary", "due", "decided_in"}


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def test_index_extras_v2_shape(tmp_path):
    _write(tmp_path / "ledger" / "items.yaml", "schema: ledger/1\nitems:\n  - {id: R1, kind: ruling, text: t, source: s, status: open}\n")
    _write(tmp_path / "updates" / "2026-11-16" / "updates.yaml",
           'entries:\n  - {person: Ana, link: "https://example.com/a", changed: did x}\n')
    ex = index_extras([{"id": "a", "scorecard": "a.scorecard.json", "mechanisms": None}], tmp_path)
    assert set(ex) == {"version", "generated_at", "scorecards", "mechanisms", "ledger", "updates"}
    assert ex["version"] == 2 and ex["scorecards"] == {"a": "a.scorecard.json"} and ex["mechanisms"] == {}
    assert ex["ledger"][0]["id"] == "R1"
    assert ex["updates"] == [{"week": "2026-11-16", "entries": [{"person": "Ana", "link": "https://example.com/a", "changed": "did x"}]}]
    empty = tmp_path / "empty"
    empty.mkdir()
    ex = index_extras([], empty)
    assert ex["ledger"] == [] and ex["updates"] == []


def test_mechanism_sweep_matches_gate_and_moves_parts():
    design = load_design(FIXTURES / "mech-good.yaml")
    mech = design.data["mechanisms"][0]
    sw = mechanism_sweeps(design)
    (m,) = sw["mechanisms"]
    assert m["id"] == "flap_l" and len(m["steps"]) == 21
    assert m["steps"][0]["transforms"] == {}
    assert m["steps"][-1]["followers"] == {"flap_hinge": 20.0}
    assert m["steps"][-1]["followers"] == simulate_mechanism(design, mech)["steps"][-1]["followers"]
    assert len(m["steps"][-1]["transforms"]["flap"]) == 16
    assert mechanism_sweeps(load_design(EXAMPLE / "plane.yaml")) is None


def test_articulations_without_mechanisms_get_pseudo_sweeps(tmp_path):
    data = yaml.safe_load((FIXTURES / "mech-good.yaml").read_text())
    del data["mechanisms"]
    _write(tmp_path / "d" / "plane.yaml", yaml.safe_dump(data))
    sw = mechanism_sweeps(load_design(tmp_path / "d" / "plane.yaml"))
    assert sw is not None and sw["mechanisms"]
    for m in sw["mechanisms"]:
        assert m["id"].startswith("sweep-") and len(m["steps"]) > 1
        assert m["steps"][-1]["transforms"]


@pytest.mark.slow
def test_concept_a_pseudo_sweeps_match_articulations():
    sw = mechanism_sweeps(load_design(design_mod.REPO_ROOT / "tests" / "fixtures" / "concept-a-frozen" / "plane.yaml"))
    assert {m["id"] for m in sw["mechanisms"]} == {"sweep-E-WNG-10", "sweep-E-WNG-11"}


def test_public_index_ledger_has_only_allowed_keys(tmp_path):
    _write(tmp_path / "ledger" / "items.yaml",
           "schema: ledger/1\nitems:\n  - {id: R1, kind: ruling, text: t, source: quote, status: open, evidence: secret}\n")
    (item,) = index_extras([], tmp_path, public=True)["ledger"]
    assert set(item) == PUBLIC_KEYS
    assert "secret" not in str(item.values()) and "quote" not in str(item.values())
    assert index_extras([], tmp_path, public=False)["ledger"][0]["evidence"] == "secret"


def test_build_index_writes_v2_and_sweep_files(sandbox, tmp_path):
    (sandbox / "mech-good").mkdir()
    shutil.copy(FIXTURES / "mech-good.yaml", sandbox / "mech-good" / "plane.yaml")
    out = tmp_path / "out"
    res = CliRunner().invoke(cli.cli, ["build-index", "--out", str(out)])
    assert res.exit_code == 0, res.output
    index = json.loads((out / "index.json").read_text())
    assert index["version"] == 2 and "studio" not in index
    assert (out / index["mechanisms"]["mech-good"]).is_file()
    assert all(set(i) == PUBLIC_KEYS for i in index["ledger"])
    by_id = {e["id"]: e for e in index["designs"]}
    assert all("mechanisms" in e and "fea" in e for e in by_id.values())
    assert by_id["example-tailsitter-wing"]["mechanisms"] is None


def _wait_studio_idle(s, timeout=120):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if not s.state()["busy"]:
            return
        time.sleep(0.1)
    raise AssertionError("studio jobs did not finish")


def test_recheck_keeps_the_previous_versions_files_for_one_more_generation(sandbox):  # T84
    # A page that fetched the index just before a re-check finished still asks for the previous version's glb,
    # scorecard and mass: they must not 404 (flaky console error in test_propose_link_survives_real_git_side_effects).
    did = "example-tailsitter-wing"
    s = studio.Studio()
    _wait_studio_idle(s)

    def files():
        e = s.entries[did]
        return {e["glb"], e["scorecard"], e["mass"]}

    v1 = files()
    plane = sandbox / did / "plane.yaml"
    plane.write_text(plane.read_text(encoding="utf-8") + "\n# edit 1\n", encoding="utf-8")
    s.scan()
    _wait_studio_idle(s)
    v2 = files()
    assert v1.isdisjoint(v2)
    assert all((studio.DATA_DIR / f).is_file() for f in v1 | v2), "previous version's files must survive one re-check"
    plane.write_text(plane.read_text(encoding="utf-8") + "# edit 2\n", encoding="utf-8")
    s.scan()
    _wait_studio_idle(s)
    v3 = files()
    assert not any((studio.DATA_DIR / f).exists() for f in v1), "two versions back is deleted"
    assert all((studio.DATA_DIR / f).is_file() for f in v2 | v3)
