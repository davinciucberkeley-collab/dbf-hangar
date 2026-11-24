"""Morphological chart (knowledge/morphological-chart.yaml): add an option by text edit, and coverage by design."""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from . import op, OpResult, OpInputError
from ._paths import repo_root, rel

ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
CHART = "knowledge/morphological-chart.yaml"


def _load_chart(root: Path) -> dict:
    try:
        chart = yaml.safe_load((root / CHART).read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise OpInputError(f"{CHART}: cannot parse YAML: {e}") from e
    if not isinstance(chart, dict):
        raise OpInputError(f"{CHART}: not a mapping")
    return chart


@op(name="morph.add-option", summary="Add one option to a dimension of the morphological chart (source must be an "
                                     "entry in knowledge/sources/).",
    mutates=True, render=lambda r: r.data["line"])
def add_option(dimension: str, id: str, name: str, source: str) -> OpResult:
    if not ID_RE.fullmatch(id):
        raise OpInputError(f"option id {id!r} must match {ID_RE.pattern}")
    if not ID_RE.fullmatch(source):
        raise OpInputError(f"source {source!r} must match {ID_RE.pattern}")
    if not name.strip():
        raise OpInputError("name must not be empty")
    root = repo_root()
    if not (root / "knowledge" / "sources" / f"{source}.md").is_file():
        raise OpInputError(f"no such source: knowledge/sources/{source}.md")
    chart = _load_chart(root)
    dims = chart.get("dimensions") or []
    match = [d for d in dims if isinstance(d, dict) and d.get("id") == dimension]
    if not match:
        raise OpInputError(f"unknown dimension {dimension!r}")
    if any(isinstance(o, dict) and o.get("id") == id for o in (match[0].get("options") or [])):
        raise OpInputError(f"option {id!r} already exists in dimension {dimension!r}")

    path = root / CHART
    text = path.read_bytes().decode("utf-8")
    lines = text.splitlines(keepends=True)
    eol = "\r\n" if "\r\n" in text else "\n"
    start = next((i for i, line in enumerate(lines) if line.rstrip() == f"  - id: {dimension}"), None)
    if start is None:
        raise OpInputError(f"dimension {dimension!r} not found in chart text")
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("  - id:")), len(lines))
    flow = [i for i in range(start, end) if lines[i].startswith("      - {")]
    if not flow:
        raise OpInputError("dimension has no flow-style options to extend")
    last = flow[-1]
    new = f"      - {{id: {id}, name: {json.dumps(name)}, source: {source}}}"
    if not lines[last].endswith("\n"):
        lines[last] = lines[last] + eol
    lines.insert(last + 1, new + eol)
    path.write_bytes(("".join(lines)).encode("utf-8"))
    chart_rel = rel(root, path)
    return OpResult(True, {"path": chart_rel, "line": new.strip()}, changed_files=[chart_rel])


@op(name="morph.coverage", summary="For every dimension and option of the chart, which designs use it.",
    render=lambda r: "\n".join(f"{c['dimension']}/{c['option']}: {', '.join(c['designs']) or '-'}"
                               for c in r.data["cells"]))
def coverage_op() -> OpResult:
    root = repo_root()
    chart = _load_chart(root)
    designs = []
    for plane in sorted((root / "designs").glob("*/plane.yaml")):
        try:
            data = yaml.safe_load(plane.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError, UnicodeDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        did = data.get("id") or plane.parent.name
        morph = data.get("morphology") or {}
        if isinstance(morph, dict):
            designs.append((str(did), morph))
    cells = []
    for dim in chart.get("dimensions") or []:
        for opt in dim.get("options") or []:
            used = [did for did, morph in designs
                    if morph.get(dim["id"]) is not None and str(morph.get(dim["id"])) == str(opt["id"])]
            cells.append({"dimension": dim["id"], "option": opt["id"], "designs": used})
    return OpResult(True, {"cells": cells})


@op(name="morph.list", summary="List every dimension and option of the morphological chart.",
    render=lambda r: "\n".join(f"{c['dimension']}/{c['option']}  {c['name']}" for c in r.data["cells"]))
def list_op() -> OpResult:
    chart = _load_chart(repo_root())
    cells = []
    for dim in chart.get("dimensions") or []:
        for opt in dim.get("options") or []:
            cells.append({"dimension": str(dim["id"]), "option": str(opt["id"]), "name": str(opt.get("name", "")),
                          "source": opt.get("source")})
    return OpResult(True, {"cells": cells})
