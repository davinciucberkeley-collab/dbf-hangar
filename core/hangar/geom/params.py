"""Design-level `parameters` and the whole-string "$name" references to them (PDL 1.2)."""
from __future__ import annotations

import copy
import re

REF_RE = re.compile(r"^\$([a-z][a-z0-9_]*)$")
REF_PATHS = ("geometry.params", "planform", "position", "rotation_deg")   # under components[*]; nowhere else


def _is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _walk(node, path: str):
    if isinstance(node, str):
        m = REF_RE.match(node)
        if m:
            yield path, m.group(1)
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from _walk(v, f"{path}.{k}")
    elif isinstance(node, (list, tuple)):
        for i, v in enumerate(node):
            yield from _walk(v, f"{path}[{i}]")


def _at(component: dict, dotted: str):
    node = component
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return None, False
        node = node[part]
    return node, True


def find_references(data: dict) -> list[tuple[str, str, str]]:
    """[(component id, dotted path inside the component, parameter name)] for every whole-string "$name" under REF_PATHS."""
    out = []
    for c in (data.get("components") or []):
        if not isinstance(c, dict):
            continue
        for rp in REF_PATHS:
            node, ok = _at(c, rp)
            if ok:
                out.extend((str(c.get("id")), p, n) for p, n in _walk(node, rp))
    return out


def _sub(node, params: dict):
    if isinstance(node, str):
        m = REF_RE.match(node)
        if m and _is_num(params.get(m.group(1))):
            return params[m.group(1)]
        return node
    if isinstance(node, dict):
        return {k: _sub(v, params) for k, v in node.items()}
    if isinstance(node, list):
        return [_sub(v, params) for v in node]
    return node


def resolve_references(data: dict) -> dict:
    """Deep copy of `data` with each "$name" under REF_PATHS replaced by parameters[name]; `data` is not mutated."""
    out = copy.deepcopy(data)
    params = out.get("parameters") if isinstance(out.get("parameters"), dict) else {}
    for c in (out.get("components") or []):
        if not isinstance(c, dict):
            continue
        for rp in REF_PATHS:
            parent: dict = c
            parts = rp.split(".")
            for part in parts[:-1]:
                parent = parent.get(part) if isinstance(parent, dict) else None
                if not isinstance(parent, dict):
                    break
            else:
                if parts[-1] in parent:
                    parent[parts[-1]] = _sub(parent[parts[-1]], params)
    return out
