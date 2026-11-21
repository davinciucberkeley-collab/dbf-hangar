"""Tool operations (U2.3): doctor."""
from __future__ import annotations

from . import op, OpResult


def _render(r: OpResult) -> str:
    return "\n".join(f"{x['name']:<12} {x['status']:<8} {x['detail']}" for x in r.data["adapters"])


@op(name="tools.doctor", summary="List every tool adapter: found, missing (with the fix command) or planned.", render=_render)
def doctor() -> OpResult:
    from ..adapters import ADAPTER_NAMES, get_adapter
    rows = []
    for name in ADAPTER_NAMES:
        ad = get_adapter(name)
        ok, detail = ad.available()
        rows.append({"name": name, "available": ok, "planned": ad.planned,
                     "status": "ok" if ok else ("planned" if ad.planned else "missing"), "detail": detail})
    return OpResult(True, {"adapters": rows},
                    messages=[f"{r['name']}: {r['detail']}" for r in rows if not r["available"]],
                    skipped=[r["name"] for r in rows if not r["available"]])
