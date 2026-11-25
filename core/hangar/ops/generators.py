"""Read-only view of the generator registry (U13.2)."""
from __future__ import annotations

from . import op, OpResult, OpInputError
from ..geom import registry
import hangar.geom  # noqa: F401  (registers the built-in generators; see core/hangar/geom/__init__.py)

_UNITS = "lengths mm, angles degrees, mass g (component-local frame)"


def _list_render(r: OpResult) -> str:
    lines = []
    for g in r.data["generators"]:
        req = ", ".join(g["required"]) or "-"
        lines.append(f"{g['name']}  ({g['param_count']} params; required: {req})")
    return "\n".join(lines)


@op(name="generators.list",
    summary="List the geometry generators a component can use (geometry: {generator: <name>, params: {...}}).",
    render=_list_render)
def list_() -> OpResult:
    rows = []
    for n in registry.names():
        gen = registry.get(n)
        rows.append({"name": n,
                     "required": [p for p, s in gen.params.items() if s.required],
                     "param_count": len(gen.params)})
    return OpResult(ok=True, data={"generators": rows})


def _param_line(p: dict) -> str:
    bits = [p["kind"], "required" if p["required"] else f"default {p['default']}"]
    if p["minimum"] is not None:
        bits.append(f"min {p['minimum']}")
    if p["exclusive_minimum"] is not None:
        bits.append(f">{p['exclusive_minimum']}")
    if p["choices"]:
        bits.append("one of " + "|".join(p["choices"]))
    line = f"  {p['name']} ({', '.join(bits)})"
    return f"{line}: {p['doc']}" if p["doc"] else line


def _show_render(r: OpResult) -> str:
    req = [p["name"] + ": " + p["kind"] for p in r.data["params"] if p["required"]]
    example = "{" + ", ".join(req) + "}"
    lines = [r.data["name"], f"units: {r.data['units']}"]
    lines += [_param_line(p) for p in r.data["params"]]
    lines.append(f"example: geometry: {{generator: {r.data['name']}, params: {example}}}")
    return "\n".join(lines)


@op(name="generators.show", summary="Show one geometry generator's parameters (name, kind, required, default, bounds, choices, doc).",
    render=_show_render)
def show(name: str) -> OpResult:
    try:
        gen = registry.get(name)
    except KeyError as e:
        raise OpInputError(e.args[0]) from None
    params = [{"name": p, "kind": s.kind, "required": s.required, "default": s.default,
               "minimum": s.minimum, "exclusive_minimum": s.exclusive_minimum,
               "choices": list(s.choices), "doc": s.doc}
              for p, s in gen.params.items()]
    return OpResult(ok=True, data={"name": name, "units": _UNITS, "params": params})
