"""Meta operations: describe the registry."""
from __future__ import annotations

from . import op, OpResult, registry


def _render(r: OpResult) -> str:
    return "\n".join(f"{o['name']:<20} {o['summary']}" for o in r.data["ops"])


def _safe(v):
    return v if v is None or isinstance(v, (str, int, float, bool)) else str(v)


@op(name="ops.list", summary="List every operation and its parameters.", render=_render)
def list_ops() -> OpResult:
    items = []
    for name, s in registry().items():
        items.append({
            "name": name, "summary": s.summary, "mutates": s.mutates, "adapters": list(s.adapters),
            "params": [{"name": p.name, "cli_name": p.cli_name, "type": p.type_name, "kind": p.kind,
                        "required": p.required, "default": _safe(p.default),
                        "choices": list(p.choices) if p.choices else None} for p in s.params]})
    return OpResult(True, {"ops": items})
