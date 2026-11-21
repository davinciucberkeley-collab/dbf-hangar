"""Standards operations: the shared connection-type library (U1.6) and the design-standards database (U2.2)."""
from __future__ import annotations

import yaml

from . import OpInputError, OpResult, op
from ..design import REPO_ROOT, STANDARDS_PATH
from ..gates.interfaces import load_connection_types

KINDS = ("mechanical", "electrical", "thermal", "kinematic")
SOURCES_DIR = REPO_ROOT / "knowledge" / "sources"
# TODO(U2.1): replace with gates.yaml blocking flags
BLOCKING_KEYS = ("landing_load_factor", "hover_thrust_to_weight_min")


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


def _rules() -> list[tuple[str, str, dict]]:
    """Every (section, key, rule) in standards/design-standards.yaml; a rule is a dict with a `source` key."""
    data = yaml.safe_load(STANDARDS_PATH.read_text(encoding="utf-8"))
    out = []
    for section, group in data.items():
        if not isinstance(group, dict):
            continue
        for key, rule in group.items():
            if isinstance(rule, dict) and "source" in rule:
                out.append((section, key, rule))
    return out


def _sections() -> list[str]:
    data = yaml.safe_load(STANDARDS_PATH.read_text(encoding="utf-8"))
    return sorted(k for k, v in data.items() if isinstance(v, dict))


def _value(rule: dict):
    if "value" in rule:
        return rule["value"]
    if "min" in rule or "max" in rule:
        return {k: rule[k] for k in ("min", "max") if k in rule}
    return None


def _candidates(key: str) -> list[str]:
    stems = []
    for path in sorted(SOURCES_DIR.glob("std-*.md")):
        if path.stem == "std-SUMMARY":
            continue
        if key in path.read_text(encoding="utf-8"):
            stems.append(path.stem)
    return stems


def _render_list(r: OpResult) -> str:
    return "\n".join(f"{i['key']:<34} {i['section']:<11} {i['value']!s:<20} {i['source']}" for i in r.data["items"])


def _render_show(r: OpResult) -> str:
    return f"{r.data['key']} ({r.data['section']})\n" + "\n".join(f"  {k}: {v}" for k, v in r.data["rule"].items())


def _render_pending(r: OpResult) -> str:
    return "\n".join(f"{'BLOCK' if i['blocking'] else '     '} {i['key']:<34} {', '.join(i['candidates']) or '-'}"
                     for i in r.data["items"])


@op(name="standards.list", summary="List design-standards rules with a source (optionally one section).", render=_render_list)
def list_rules(section: str = "") -> OpResult:
    valid = _sections()
    if section and section not in valid:
        raise OpInputError(f"unknown section {section!r}; use one of {', '.join(valid)}")
    rows = [{"key": key, "section": sec, "value": _value(rule), "source": rule["source"]}
            for sec, key, rule in _rules() if not section or sec == section]
    return OpResult(ok=True, data={"items": rows, "count": len(rows)})


@op(name="standards.show", summary="Show one design-standards rule with its full text and source.", render=_render_show)
def show(key: str) -> OpResult:
    for sec, k, rule in _rules():
        if k == key:
            return OpResult(ok=True, data={"key": key, "section": sec, "rule": rule})
    raise OpInputError(f"unknown standards key {key!r}")


@op(name="standards.pending", summary="List every standards value still pending a source, with candidate source files.",
    render=_render_pending)
def pending() -> OpResult:
    items = []
    for sec, key, rule in _rules():
        if rule["source"] == "pending":
            items.append({"key": key, "value": _value(rule), "blocking": key in BLOCKING_KEYS,
                          "candidates": _candidates(key)})
    for t in load_connection_types().values():
        if t["source"] == "pending":
            items.append({"key": t["id"], "value": None, "blocking": False, "candidates": _candidates(t["id"])})
    return OpResult(ok=True, data={"items": items, "count": len(items)})
