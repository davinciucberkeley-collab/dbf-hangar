"""Design operations: list, get, validate, mass, export, new."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from . import op, OpResult, OpInputError
from ..design import FAIL, SKIP, list_designs, load_design
from ..ids import ID_RE
from ..checks import validate
from ..mass import mass_properties
from .. import pdledit
from ..export import export_glb, export_stl, export_json


def _load(path: str):
    if not Path(str(path).replace("\\", "/")).exists():
        raise OpInputError(f"no design folder at {path}; see `plane design list`")
    try:
        return load_design(pdledit.resolve_design_path(path))
    except Exception as e:  # noqa: BLE001 - report any load failure cleanly
        raise OpInputError(f"cannot load {path}: {e}") from e


def _render_list(r: OpResult) -> str:
    rows = r.data["designs"]
    if not rows:
        return "no designs found"
    headers = ["id", "name", "status", "lift", "vtol_method"]
    widths = {h: max(len(h), *(len(x[h]) for x in rows)) for h in headers}
    lines = ["  ".join(h.ljust(widths[h]) for h in headers).rstrip()]
    lines += ["  ".join(x[h].ljust(widths[h]) for h in headers).rstrip() for x in rows]
    return "\n".join(lines)


@op(name="design.list", summary="List every design under designs/.", render=_render_list)
def list_op() -> OpResult:
    rows = []
    for p in list_designs():
        try:
            d = load_design(p).data
        except Exception as e:  # noqa: BLE001
            rows.append({"id": p.parent.name, "name": f"<error: {e}>", "status": "", "lift": "", "vtol_method": ""})
            continue
        morph = d.get("morphology") or {}
        rows.append({
            "id": str(d.get("id", p.parent.name)),
            "name": str(d.get("name", "")),
            "status": str(d.get("status", "")),
            "lift": str(morph.get("lift", "")),
            "vtol_method": str(morph.get("vtol_method", "")),
        })
    return OpResult(True, {"designs": rows})


@op(name="design.get", summary="Print a design's plane.yaml, or with --key one value from it.",
    render=lambda r: r.data["text"] if "text" in r.data else json.dumps(r.data["value"], default=str))
def get_op(path: str, *, key: str = "") -> OpResult:
    design = _load(path)
    if key:
        return OpResult(True, {"path": str(design.path), "key": key, "value": pdledit.get_value(design.data, key)})
    return OpResult(True, {"path": str(design.path), "text": Path(design.path).read_text(encoding="utf-8")})


@op(name="design.validate", summary="Run the validation tiers and return the scorecard.",
    render=lambda r: r.data["markdown"])
def validate_op(path: str, tier: Literal["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "all"] = "all") -> OpResult:
    design = _load(path)
    card = validate(design, max_tier=9 if tier == "all" else int(tier))
    data = {**card.to_dict(), "markdown": card.to_markdown()}
    ok = bool(card.clean and (card.accepted or card.partial))
    messages, skipped = [], []
    for t in card.tiers:
        for r in t.results:
            if r.status in (FAIL, SKIP):
                messages.append(f"{r.check_id} {r.status}: {r.message}")
            if r.status == SKIP:
                skipped.append(f"{r.check_id}: {r.message}")
    return OpResult(ok, data, messages, skipped=skipped)


@op(name="design.mass", summary="Mass properties of a design.",
    render=lambda r: json.dumps(r.data, indent=2, default=str))
def mass_op(path: str) -> OpResult:
    return OpResult(True, mass_properties(_load(path)))


@op(name="design.export", summary="Export a design to glb, stl, json or mjcf.", mutates=True,
    render=lambda r: "\n".join(r.data["files"]))
def export_op(path: str, *, format_: Literal["glb", "stl", "json", "mjcf"], out: Path) -> OpResult:
    design = _load(path)
    try:
        if format_ == "stl":
            written = export_stl(design, out)
        elif format_ == "glb":
            written = export_glb(design, out)
        elif format_ == "mjcf":
            from ..sim import export_mjcf
            written = export_mjcf(design, out)
        else:
            written = export_json(design, out)
    except Exception as e:  # noqa: BLE001
        return OpResult(False, {}, [f"export failed: {e}"])
    paths = [str(p) for p in (written if isinstance(written, list) else [written])]
    return OpResult(True, {"files": paths}, changed_files=list(paths))


@op(name="design.new", summary="Create a design from a template.", mutates=True, render=lambda r: r.data["path"])
def new_op(new_id: str, *, template: str = "example-tailsitter-wing") -> OpResult:
    from ..cli import new_design
    if not ID_RE.fullmatch(new_id):
        raise OpInputError(f"invalid id {new_id!r}: must match {ID_RE.pattern}")
    try:
        p = new_design(new_id, template)
    except ValueError as e:
        raise OpInputError(str(e)) from e
    return OpResult(True, {"path": str(p)}, changed_files=[str(p)])
