"""U11.2: libyaml loader gives the same data and the same design.set results."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pytest
import yaml

from hangar import yamlfast
from hangar.ops import call

ROOT = Path(__file__).resolve().parents[1]
FILES = sorted(ROOT.glob("designs/*/plane.yaml")) + sorted(ROOT.glob("standards/*.yaml"))
GEN = ["fin-001-l", "fin-001-r", "wng-001", "wng-002"]


@pytest.mark.parametrize("f", FILES, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_same_data_as_safeloader_on_every_design(f):
    text = f.read_text(encoding="utf-8")
    a = yamlfast.safe_load(text)
    b = yaml.load(text, Loader=yaml.SafeLoader)
    assert a == b
    assert json.dumps(a, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str)


def test_falls_back_without_libyaml(monkeypatch):
    text = (ROOT / "designs/concept-a-param/plane.yaml").read_text(encoding="utf-8")
    default = yamlfast.safe_load(text)
    monkeypatch.setattr(yamlfast, "_LOADER", yaml.SafeLoader)
    assert yamlfast.safe_load(text) == default


def test_yaml_error_is_yamlerror():
    with pytest.raises(yaml.YAMLError):
        yamlfast.safe_load("a: [1, 2")


def _snapshot(d, r):
    cl = re.sub(r"(?m)^.*date:.*\n", "", (d / "CHANGELOG.yaml").read_text(encoding="utf-8")) if (d / "CHANGELOG.yaml").exists() else ""
    meshes = {p.relative_to(d).as_posix(): p.read_bytes() for p in sorted((d / "meshes").rglob("*") if (d / "meshes").exists() else []) if p.is_file()}
    return {
        "ok": r.ok,
        "data": json.dumps(r.data, sort_keys=True, default=str),
        "messages": json.dumps(getattr(r, "messages", None), default=str),
        "plane": (d / "plane.yaml").read_bytes(),
        "changelog": cl,
        "meshes": meshes,
    }


def _run(tmp_path, name, values, monkeypatch, loader):
    d = tmp_path / name
    shutil.copytree(ROOT / "designs/concept-a-param", d)
    monkeypatch.setattr(yamlfast, "_LOADER", loader)
    out = []
    for v in values:
        r = call("design.set", path=str(d), key="parameters.span_mm", value=v, why="t")
        assert r.ok, r
        assert sorted(r.data["regenerated"]["components"]) == GEN
        out.append(_snapshot(d, r))
    return out


def test_design_set_result_unchanged_concept_a_param(tmp_path, monkeypatch):
    fast = _run(tmp_path, "fast", ["820", "900"], monkeypatch, getattr(yaml, "CSafeLoader", yaml.SafeLoader))
    slow = _run(tmp_path, "slow", ["820", "900"], monkeypatch, yaml.SafeLoader)
    assert fast == slow
