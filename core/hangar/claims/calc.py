"""Margin rules and the calculation registry for claims (adapted from proofs/1 proofkit.py)."""
from __future__ import annotations

import math
from typing import Callable

import yaml

from ..design import REPO_ROOT


def is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and not math.isnan(v)


def margin(value, limit_value, op) -> float | None:
    """Signed margin; negative fails. Limit 0: signed distance (value for >=, -value for <=)."""
    if not is_number(value) or not is_number(limit_value):
        return None
    d = (value - limit_value) if op == ">=" else (limit_value - value)
    return (d / abs(limit_value) if limit_value != 0 else d) + 0.0


def margin_text(m, limit_value, unit="", digits=0) -> str:
    if m is None:
        return ""
    if limit_value == 0:
        return f"{m:+.3g}" + (f" {unit}" if unit and unit != "-" else "") + " abs"
    return f"{m:+.{digits}%}"


def close(a, b, rel_tol) -> bool:
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(close(x, y, rel_tol) for x, y in zip(a, b))
    if is_number(a) and is_number(b):
        return math.isclose(a, b, rel_tol=rel_tol, abs_tol=1e-12)
    return a == b


def builtin_calcs() -> dict[str, Callable]:
    from .. import calcs
    return dict(calcs.CALCS)


_REGISTRY: dict[str, Callable] = builtin_calcs()


def register_calcs(table: dict[str, Callable]) -> None:
    for name, fn in table.items():
        if name in _REGISTRY and _REGISTRY[name] is not fn:
            raise ValueError(f"calculation name {name!r} is already registered")
    _REGISTRY.update(table)


def resolve_calc(name: str) -> Callable | None:
    return _REGISTRY.get(name)


def load_claims_standards() -> dict:
    return yaml.safe_load((REPO_ROOT / "standards" / "claims.yaml").read_text(encoding="utf-8"))
