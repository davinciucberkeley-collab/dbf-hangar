"""U1.4, Review Focus #2: Windows paths and CRLF give the same results as Linux."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from hangar import design as design_mod
from hangar.ops import call
from hangar.pdledit import resolve_design_path

EXAMPLE_DIR = design_mod.DESIGNS_DIR / "example-tailsitter-wing"


@pytest.fixture
def tmp_example(tmp_path) -> Path:
    dst = tmp_path / "example-tailsitter-wing"
    shutil.copytree(EXAMPLE_DIR, dst)
    return dst


def test_backslash_and_crlf_roundtrip(tmp_example):
    crlf = tmp_example / "plane.yaml"
    crlf.write_bytes(crlf.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    assert b"\r\n" in crlf.read_bytes()
    backslashed = str(tmp_example).replace("/", "\\")
    assert call("design.validate", path=backslashed).data["design_id"]
    assert call("design.mass", path=backslashed).ok
    assert call("design.get", path=backslashed, key="components[battery].mass_g").data["value"] == 250
    r = call("design.set", path=backslashed, key="components[battery].mass_g", value="260", why="t")
    assert r.ok, r.messages
    assert call("design.get", path=str(tmp_example), key="components[battery].mass_g").data["value"] == 260
    assert b"\r\n" in crlf.read_bytes()


def test_resolve_design_path_normalises_backslashes(tmp_example):
    p = resolve_design_path(str(tmp_example).replace("/", "\\"))
    assert p == tmp_example / "plane.yaml" or p.resolve() == (tmp_example / "plane.yaml").resolve()
    assert resolve_design_path("designs\\nope\\plane.yaml") == Path("designs/nope/plane.yaml")
