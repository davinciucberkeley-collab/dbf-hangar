"""Real-parts library operations (U4.31): list and show knowledge/parts/ entries."""
from __future__ import annotations

from . import OpInputError, OpResult, op
from ..geom import library

_COLS = ("id", "name", "category", "vendor", "part_number", "mass_g", "cad_status")


def _render(r: OpResult) -> str:
    return "\n".join(f"{p['id']:<24} {p['category']:<16} {p['mass_g']:>8} g  {p['cad_status']:<22} {p['vendor']}"
                     for p in r.data["parts"]) or "0 parts"


@op(name="parts.list", summary="List the real-parts library (knowledge/parts/).", render=_render)
def list_(category: str = "") -> OpResult:
    if category and category not in library.CATEGORIES:
        raise OpInputError(f"unknown category {category!r}; use one of {', '.join(library.CATEGORIES)}")
    rows = []
    for pid in library.list_parts():
        part = library.load_part(pid)
        if category and part["category"] != category:
            continue
        rows.append({k: part[k] for k in _COLS})
    return OpResult(ok=True, data={"parts": rows, "count": len(rows)})


def _render_show(r: OpResult) -> str:
    return "\n".join(f"{k}: {v}" for k, v in r.data.items())


@op(name="parts.show", summary="Show one real-parts library record.", render=_render_show)
def show(id: str) -> OpResult:
    try:
        part = library.load_part(id)
    except KeyError as e:
        raise OpInputError(e.args[0]) from None
    return OpResult(ok=True, data={k: v for k, v in part.items() if k != "_dir"})
