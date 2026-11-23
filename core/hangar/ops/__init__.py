"""Operations registry and the OpResult contract (U1.1).

Exit-code rule: `data.error` is "input" (exit 2) or "internal" (exit 1) when present.
Op modules are any `hangar/ops/<name>.py` not starting with `_`; `registry()` imports them all.
"""
from __future__ import annotations

import importlib
import inspect
import json
import pkgutil
import re
import typing
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal

import numpy as np

OP_RESULT_SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schema" / "op-result.schema.json"

_NAME_RE = re.compile(r"^[a-z][a-z0-9]*\.[a-z][a-z0-9-]*$")


def _jsonable(o):
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, np.generic):
        return o.item()
    return str(o)


class OpInputError(Exception):
    """Bad input (unreadable design, unknown id, bad value): exit 2."""


@dataclass
class OpResult:
    ok: bool
    data: dict
    messages: list[str] = field(default_factory=list)
    changed_files: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    schema_version = "1.0"

    def to_json(self) -> str:
        body = {"schema_version": self.schema_version, "ok": self.ok, "data": self.data,
                "messages": self.messages, "changed_files": self.changed_files, "skipped": self.skipped}
        return json.dumps(body, indent=2, default=_jsonable)

    @property
    def exit_code(self) -> int:
        if self.ok:
            return 0
        return 2 if self.data.get("error") == "input" else 1


@dataclass(frozen=True)
class ParamSpec:
    name: str
    cli_name: str
    type_name: str
    kind: str
    required: bool
    default: Any
    choices: tuple[str, ...] | None
    multiple: bool


@dataclass(frozen=True)
class OpSpec:
    name: str
    summary: str
    mutates: bool
    adapters: tuple[str, ...]
    func: Callable
    params: tuple[ParamSpec, ...]
    render: Callable[[OpResult], str] | None

    @property
    def group(self) -> str:
        return self.name.split(".")[0]

    @property
    def verb(self) -> str:
        return self.name.split(".", 1)[1]


_REGISTRY: dict[str, OpSpec] = {}
_LOADED = False


def _classify(t, where: str) -> tuple[str, tuple[str, ...] | None]:
    if t is str:
        return "str", None
    if t is bool:
        return "bool", None
    if t is int:
        return "int", None
    if t is float:
        return "float", None
    if t is Path:
        return "path", None
    if typing.get_origin(t) is Literal:
        vals = typing.get_args(t)
        if not vals or not all(isinstance(v, str) for v in vals):
            raise TypeError(f"{where}: Literal must hold string values")
        return "choice", tuple(vals)
    if typing.get_origin(t) is list and typing.get_args(t) == (str,):
        return "list[str]", None
    raise TypeError(f"{where}: unsupported annotation {t!r}")


def _build_spec(func, *, name, summary, mutates, adapters, render) -> OpSpec:
    if not _NAME_RE.match(name):
        raise ValueError(f"invalid op name {name!r}: must match {_NAME_RE.pattern}")
    hints = typing.get_type_hints(func)
    params = []
    for p in inspect.signature(func).parameters.values():
        where = f"{name}: parameter {p.name!r}"
        if p.name not in hints:
            raise TypeError(f"{where} has no annotation")
        if p.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            raise TypeError(f"{where}: *args/**kwargs not supported")
        type_name, choices = _classify(hints[p.name], where)
        has_default = p.default is not inspect.Parameter.empty
        keyword_only = p.kind is inspect.Parameter.KEYWORD_ONLY
        if type_name == "bool" and not has_default:
            raise TypeError(f"{where}: bool needs a default")
        kind = "option" if (has_default or keyword_only) else "argument"
        required = (not has_default) and not (kind == "argument" and type_name == "list[str]")
        cli_name = p.name[:-1] if p.name.endswith("_") else p.name
        cli_name = cli_name.replace("_", "-")
        params.append(ParamSpec(
            name=p.name, cli_name=cli_name, type_name=type_name, kind=kind, required=required,
            default=p.default if has_default else None, choices=choices,
            multiple=type_name == "list[str]"))
    return OpSpec(name, summary, mutates, tuple(adapters), func, tuple(params), render)


def op(name: str, summary: str, mutates: bool = False, adapters: tuple[str, ...] = (),
       render: Callable[[OpResult], str] | None = None):
    def deco(func):
        spec = _build_spec(func, name=name, summary=summary, mutates=mutates, adapters=adapters, render=render)
        if name in _REGISTRY:
            raise ValueError(f"duplicate op name {name!r}")
        _REGISTRY[name] = spec
        return func
    return deco


def registry() -> dict[str, OpSpec]:
    global _LOADED
    if not _LOADED:
        for m in pkgutil.iter_modules(__path__):
            if not m.name.startswith("_"):
                before = set(_REGISTRY)
                try:
                    importlib.import_module(f"{__name__}.{m.name}")
                except BaseException:
                    for added in set(_REGISTRY) - before:  # a retry re-runs this module: drop what it registered before failing
                        if _REGISTRY[added].func.__module__ == f"{__name__}.{m.name}":   # not the ops of an ops module it imported: that import stays cached
                            del _REGISTRY[added]
                    raise
        _LOADED = True
    return dict(sorted(_REGISTRY.items()))


def _input_error(message: str) -> OpResult:
    return OpResult(ok=False, data={"error": "input"}, messages=[message])


def _convert(p: ParamSpec, v):
    t = p.type_name
    if t == "str":
        if not isinstance(v, str):
            raise ValueError
        return v
    if t == "path":
        if isinstance(v, Path):
            return v
        if isinstance(v, str):
            return Path(v)
        raise ValueError
    if t == "choice":
        if v not in p.choices:
            raise KeyError
        return v
    if t == "list[str]":
        if isinstance(v, (list, tuple)) and all(isinstance(x, str) for x in v):
            return list(v)
        raise ValueError
    if t == "bool":
        if isinstance(v, bool):
            return v
        if isinstance(v, str) and v.lower() in ("true", "1", "yes"):
            return True
        if isinstance(v, str) and v.lower() in ("false", "0", "no"):
            return False
        raise ValueError
    if t in ("int", "float"):
        cast = int if t == "int" else float
        if isinstance(v, bool):
            raise ValueError
        if isinstance(v, cast) or (t == "float" and isinstance(v, int)):
            return cast(v)
        if isinstance(v, str):
            return cast(v)
        raise ValueError
    raise ValueError


def call(name: str, /, **params) -> OpResult:
    return _call_spec(registry()[name], **params)


def _call_spec(spec: OpSpec, /, **params) -> OpResult:
    declared = {p.name for p in spec.params}
    for k in params:
        if k not in declared:
            return _input_error(f"unknown parameter {k!r}")
    kwargs = {}
    for p in spec.params:
        if p.name in params:
            raw = params[p.name]
        elif p.required:
            return _input_error(f"missing parameter {p.name!r}")
        elif p.type_name == "list[str]" and p.default is None:
            raw = []
        else:
            raw = p.default
        if raw is None and p.default is None and not p.required:
            kwargs[p.name] = None
            continue
        try:
            kwargs[p.name] = _convert(p, raw)
        except KeyError:
            return _input_error(f"invalid value {raw!r} for {p.name!r}: choose from {', '.join(p.choices)}")
        except (ValueError, TypeError):
            return _input_error(f"invalid value {raw!r} for {p.name!r}")
    try:
        result = spec.func(**kwargs)
    except OpInputError as e:
        return _input_error(str(e))
    except Exception as e:  # noqa: BLE001 - never a traceback
        return OpResult(ok=False, data={"error": "internal"}, messages=[f"{type(e).__name__}: {e}"])
    if not isinstance(result, OpResult):
        return OpResult(ok=False, data={"error": "internal"},
                        messages=[f"TypeError: op {spec.name} returned {type(result).__name__}, not OpResult"])
    return result
