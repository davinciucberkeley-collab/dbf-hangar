"""Generator registry: a generator turns validated parameters into watertight parts (component-local frame, mm)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .._lazy import trimesh

from hangar.geom.kernel import GeometryError, require_solid

Mesh = "trimesh.Trimesh"
_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(frozen=True)
class ParamSpec:
    kind: str                 # "number" | "int" | "string" | "choice" | "vec2" | "vec3" | "list"
    required: bool = False
    default: object = None
    minimum: float | None = None        # inclusive, numbers/ints
    exclusive_minimum: float | None = None
    choices: tuple[str, ...] = ()
    doc: str = ""


@dataclass(frozen=True)
class Generator:
    name: str
    params: dict[str, ParamSpec]
    build: Callable[[dict, Path], list[Mesh]]
    files: Callable[[dict], list[str]] = field(default=lambda p: [])
    check: Callable[[dict], list[str]] = field(default=lambda p: [])


_REGISTRY: dict[str, Generator] = {}


def register(gen: Generator) -> None:
    if not _NAME_RE.match(gen.name):
        raise ValueError(f"bad generator name {gen.name!r}")
    if gen.name in _REGISTRY:
        raise ValueError(f"generator {gen.name!r} is already registered")
    _REGISTRY[gen.name] = gen


def get(name: str) -> Generator:
    try:
        return _REGISTRY[name]
    except (KeyError, TypeError):
        raise KeyError(f"unknown generator {name!r}; known: {', '.join(names())}") from None


def names() -> list[str]:
    return sorted(_REGISTRY)


def _is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _vec_ok(v, n: int) -> bool:
    return isinstance(v, (list, tuple)) and len(v) == n and all(_is_num(x) for x in v)


def _kind_error(spec: ParamSpec, v) -> str | None:
    k = spec.kind
    if k == "number":
        ok = _is_num(v)
    elif k == "int":
        ok = isinstance(v, int) and not isinstance(v, bool)
    elif k == "string":
        ok = isinstance(v, str)
    elif k == "choice":
        ok = isinstance(v, str)
    elif k == "vec2":
        ok = _vec_ok(v, 2)
    elif k == "vec3":
        ok = _vec_ok(v, 3)
    elif k == "list":
        ok = isinstance(v, (list, tuple))
    else:
        return f"has unknown kind {k!r}"
    return None if ok else f"must be a {k}, got {v!r}"


def validate_params(gen: Generator, params: dict) -> list[str]:
    errs: list[str] = []
    params = params or {}
    for name in params:
        if name not in gen.params:
            errs.append(f"{name}: unknown parameter for generator {gen.name!r}; known: {', '.join(sorted(gen.params))}")
    for name, spec in gen.params.items():
        if name not in params:
            if spec.required:
                errs.append(f"{name}: required parameter is missing")
            continue
        v = params[name]
        bad = _kind_error(spec, v)
        if bad:
            errs.append(f"{name}: {bad}")
            continue
        if spec.kind == "choice" and v not in spec.choices:
            errs.append(f"{name}: must be one of {', '.join(spec.choices)}, got {v!r}")
        if spec.kind in ("number", "int"):
            if spec.minimum is not None and v < spec.minimum:
                errs.append(f"{name}: must be >= {spec.minimum}, got {v!r}")
            if spec.exclusive_minimum is not None and v <= spec.exclusive_minimum:
                errs.append(f"{name}: must be > {spec.exclusive_minimum}, got {v!r}")
    if not errs:
        errs.extend(gen.check(fill_defaults(gen, params)))
    return errs


def fill_defaults(gen: Generator, params: dict) -> dict:
    out = dict(params or {})
    for name, spec in gen.params.items():
        if name not in out and not spec.required and spec.default is not None:
            out[name] = list(spec.default) if isinstance(spec.default, (list, tuple)) else spec.default
    return out


def build_component(component: dict, base_dir) -> list[Mesh]:
    cid = component.get("id", "?")
    g = component.get("geometry") or {}
    try:
        gen = get(g.get("generator"))
        params = g.get("params") or {}
        errs = validate_params(gen, params)
        if errs:
            raise GeometryError("; ".join(errs))
        parts = gen.build(fill_defaults(gen, params), Path(base_dir))
        if not parts:
            raise GeometryError("generator produced no parts")
        return [require_solid(p, f"part {i}") for i, p in enumerate(parts)]
    except (GeometryError, KeyError) as e:
        msg = e.args[0] if isinstance(e, KeyError) and e.args else str(e)
        raise GeometryError(f"{cid}: {msg}") from e


def component_files(component: dict) -> list[str]:
    g = component.get("geometry") or {}
    try:
        gen = get(g.get("generator"))
        return list(gen.files(fill_defaults(gen, g.get("params") or {})))
    except Exception:
        return []
