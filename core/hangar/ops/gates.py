"""Gate operations: list the registry, explain a check id, drive one mechanism (U2.1)."""
from __future__ import annotations

import re

from . import OpInputError, OpResult, op
from ..design import load_design
from .. import pdledit


# Check ids a run emits only when they FAIL, so a passing design cannot show them: every criterion checks.py gives
# the id, the first one is the primary (T83). tests/test_gates.py keeps this table in step with checks.py.
SCHEMA_CRIT = "schema/plane.schema.json"
FAIL_ONLY_CRITERIA = {
    "T0.version": [SCHEMA_CRIT],
    "T0.unique_ids": [SCHEMA_CRIT],
    "T0.attachment_refs": [SCHEMA_CRIT],
    "T0.root": [SCHEMA_CRIT],
    "T1.attachment_contact": ["design-standards.yaml#attach_tolerance_mm"],
    "T1.attachment_overlap": ["design-standards.yaml#embed_max_fraction_of_child", "design-standards.yaml#glued_overlap_max_fraction"],
    "T1.attachment_location": ["design-standards.yaml#attach_tolerance_mm", SCHEMA_CRIT],
    "T4.machine": ["manufacturing.yaml"],
}


def _rows() -> list[dict]:
    from ..gates import _import_gates, load_discipline_table, load_gate_table
    _import_gates()
    rows = [{k: g[k] for k in ("id", "tier", "blocking", "needs", "criterion")} | {"name": g["id"].split(".", 1)[1]}
            for g in load_gate_table()]
    rows += [{k: g[k] for k in ("id", "tier", "blocking", "criterion")} | {"needs": [], "name": g["id"].split(".", 1)[1]}
             for g in load_discipline_table()]
    return rows


def _render_list(r: OpResult) -> str:
    return "\n".join(f"T{g['tier']} {g['id']:<18} {'blocking' if g['blocking'] else 'report-only':<12} {g['criterion']}"
                     for g in r.data["gates"])


@op(name="gate.list", summary="List the registered gates (tier, blocking, needs, criterion).", render=_render_list)
def list_gates() -> OpResult:
    rows = _rows()
    return OpResult(ok=True, data={"gates": rows, "count": len(rows)})


def _render_explain(r: OpResult) -> str:
    d, t = r.data, r.data["threshold"]
    lines = [f"{d['id']} (tier {d['tier']}, {'blocking' if d['blocking'] else 'report-only'}): {d['criterion']}"]
    if t:
        lines.append(f"{t['key']} = {t['value']}  [{t['source']}]  {t['rule']}")
    return "\n".join(lines)


@op(name="gate.explain", summary="Explain one check id: its gate, whether it blocks, and the threshold behind it. With --design, an exact check id (e.g. T1.attachment) is looked up in a run on that design and explained by its own criterion.",
    render=_render_explain)
def explain(check_id: str, design: str = "") -> OpResult:
    from ..gates.fidelity import resolve_threshold
    rows = _rows()
    m = re.match(r"^T(\d+)", check_id)
    row = next((g for g in rows if g["id"] == check_id), None)
    if row is None and m:
        row = next((g for g in rows if g["tier"] == int(m.group(1))), None)
    if row is None:
        raise OpInputError(f"unknown check id {check_id!r}; gate ids: {', '.join(g['id'] for g in rows)}")
    if design and not any(g["id"] == check_id for g in rows):
        from ..gates import run_gates
        card = run_gates(_load(design))
        results = [r for t in card.tiers for r in t.results if r.check_id == check_id]
        if not results and check_id in FAIL_ONLY_CRITERIA:
            criteria = list(FAIL_ONLY_CRITERIA[check_id])
        elif not results:
            emitted = sorted({r.check_id for t in card.tiers for r in t.results if r.check_id.startswith(f"T{m.group(1)}.")})
            raise OpInputError(f"check id {check_id!r} is not emitted by a run on {design}; T{m.group(1)} ids emitted: {', '.join(emitted)}")
        else:
            criteria = list(dict.fromkeys(r.criterion for r in results if r.criterion))
        checks = [{"criterion": c, "threshold": resolve_threshold(c)} for c in criteria]
        if checks:
            return OpResult(ok=True, data={**row, "criterion": checks[0]["criterion"], "threshold": checks[0]["threshold"],
                                           "check_id": check_id, "exact": True, "checks": checks})
    return OpResult(ok=True, data={**row, "threshold": resolve_threshold(row["criterion"])})


def _load(path: str):
    try:
        return load_design(pdledit.resolve_design_path(path))
    except Exception as e:  # noqa: BLE001
        raise OpInputError(f"cannot load {path}: {e}") from e


def _render_mech(r: OpResult) -> str:
    return "\n".join(f"{s['input_deg']:>6.1f}  " + "  ".join(f"{k}={v:.1f}" for k, v in s["followers"].items())
                     for s in r.data["steps"])


@op(name="sim.mechanism",
    summary="Drive one mechanism through its input range and return the follower angles per 1 degree step.",
    render=_render_mech)
def mechanism(path: str, mechanism_id: str) -> OpResult:
    from ..gates.mechanisms import simulate_mechanism
    design = _load(path)
    mech = next((m for m in design.data.get("mechanisms", []) if m["id"] == mechanism_id), None)
    if mech is None:
        ids = [m["id"] for m in design.data.get("mechanisms", [])]
        raise OpInputError(f"unknown mechanism {mechanism_id!r}; mechanisms: {', '.join(ids) or 'none'}")
    try:
        return OpResult(ok=True, data=simulate_mechanism(design, mech))
    except RuntimeError as e:
        raise OpInputError(str(e)) from e
