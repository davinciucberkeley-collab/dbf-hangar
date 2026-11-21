"""Claim operations (U1.5): claim.list, claim.explain, claim.check."""
from __future__ import annotations

from pathlib import Path

from . import op, OpResult, OpInputError
from ..design import Design, load_design
from ..claims.graph import ClaimGraph, ClaimGraphError, claims_path, load_claims
from ..gates.claims import tier9_claims


def _load(path: str) -> tuple[Design, ClaimGraph]:
    try:
        design = load_design(path.replace("\\", "/"))
    except Exception as e:  # noqa: BLE001
        raise OpInputError(f"cannot load {path}: {e}")
    if claims_path(design) is None:
        raise OpInputError(f"{path} has no claims.yaml")
    try:
        return design, load_claims(design)
    except ClaimGraphError as e:
        raise OpInputError(f"cannot load claims for {path}: {e}")


def _rows(graph: ClaimGraph) -> list[dict]:
    out = []
    for r in graph.recompute():
        n = graph.nodes[r.id]
        out.append({"id": r.id, "title": n.get("title", ""), "value": r.value, "unit": n.get("unit", ""),
                    "limit": r.limit, "margin": r.margin, "margin_abs": r.margin_abs,
                    "status": r.status, "message": r.message})
    return out


def _requirements(graph: ClaimGraph) -> list[dict]:
    reqs = []
    for nid, n in graph.nodes.items():
        if n["type"] == "requirement":
            reqs.append({"id": nid, "title": n.get("title", ""),
                         "claims": [c for c, cn in graph.nodes.items()
                                    if cn["type"] == "claim" and nid in cn.get("verifies", [])]})
    return reqs


def _fmt_margin(r: dict) -> str:
    if r["margin"] is None:
        return ""
    return f"{r['margin']:+.3g} abs" if r["margin_abs"] else f"{r['margin']:+.1%}"


def _render_list(res: OpResult) -> str:
    rows = res.data.get("claims", [])
    w = max((len(r["id"]) for r in rows), default=0)
    return "\n".join(f"{r['id']:<{w}}  {r['status']:<8}  {r['value']} {r['unit']}  {_fmt_margin(r)}".rstrip() for r in rows)


def _render_explain(res: OpResult) -> str:
    return "\n".join("  " * n["depth"] + f"{n['id']} ({n['type']}) {n['title']}" for n in res.data.get("chain", []))


def _render_check(res: OpResult) -> str:
    return "\n".join([f"T9 {res.data.get('status')}"] + res.messages)


@op(name="claim.list", summary="List the claims of a design with value, limit, margin and status.", render=_render_list)
def list_op(path: str) -> OpResult:
    _, graph = _load(path)
    rows = _rows(graph)
    counts = {k: sum(1 for r in rows if r["status"] == k) for k in ("PASS", "FAIL", "PROPOSED", "STALE")}
    return OpResult(ok=True, data={"claims": rows, "requirements": _requirements(graph), "counts": counts})


@op(name="claim.explain", summary="Show the chain from a claim down to its sources.", render=_render_explain)
def explain_op(path: str, claim_id: str) -> OpResult:
    _, graph = _load(path)
    if claim_id not in graph.nodes or graph.nodes[claim_id]["type"] != "claim":
        raise OpInputError(f"unknown claim {claim_id!r}")
    return OpResult(ok=True, data={"claim": claim_id, "chain": graph.explain(claim_id)})


@op(name="claim.check", summary="Recompute every claim and report the T9 verdicts.", render=_render_check)
def check_op(path: str) -> OpResult:
    design, graph = _load(path)
    report = tier9_claims(design)
    uncovered = [r["id"] for r in _requirements(graph) if not r["claims"]]
    msgs = [f"{r.check_id} {r.status}: {r.message}" for r in report.results if r.status in ("FAIL", "SKIP", "WARN")]
    msgs += [f"warning: {w}" for w in graph.warnings]
    return OpResult(ok=report.status in ("PASS", "WARN"),
                    data={"status": report.status, "claims": _rows(graph), "uncovered_requirements": uncovered,
                          "warnings": graph.warnings},
                    messages=msgs,
                    skipped=[f"{r.check_id}: {r.message}" for r in report.results if r.status == "SKIP"])
