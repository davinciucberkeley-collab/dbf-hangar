"""Standards operations: the shared connection-type library (U1.6)."""
from __future__ import annotations

from . import OpInputError, OpResult, op
from ..gates.interfaces import load_connection_types

KINDS = ("mechanical", "electrical", "thermal", "kinematic")


def _render(r: OpResult) -> str:
    return "\n".join(f"{t['id']:<24} {t['kind']:<11} {t['method']:<10} {t['spec']}" for t in r.data["connection_types"])


@op(name="standards.connections", summary="List the shared connection-type library (optionally one kind).", render=_render)
def connections(kind: str = "") -> OpResult:
    if kind and kind not in KINDS:
        raise OpInputError(f"unknown kind {kind!r}; use one of {', '.join(KINDS)}")
    rows = []
    for t in load_connection_types().values():
        if kind and t["kind"] != kind:
            continue
        row = dict(t)
        row["structural"] = row.get("structural", True)
        rows.append(row)
    return OpResult(ok=True, data={"connection_types": rows, "count": len(rows)})
