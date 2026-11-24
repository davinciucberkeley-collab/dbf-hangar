"""Gate T8: BOM coverage, BOM verification age, budget (design and program)."""
from __future__ import annotations

import datetime

import yaml

from ..design import REPO_ROOT, FAIL, PASS, SKIP, WARN, CheckResult, TierReport
from . import gate, load_gate_thresholds

PROGRAM_PATH = REPO_ROOT / "standards" / "program.yaml"
CRIT = "gate-thresholds.yaml#bom_verified_max_age_days"


def load_program() -> dict[str, dict]:
    if not PROGRAM_PATH.exists():
        return {}
    return (yaml.safe_load(PROGRAM_PATH.read_text(encoding="utf-8")) or {}).get("constraints") or {}


def _total(items: list[dict]) -> tuple[float, list[str]]:
    total, missing = 0.0, []
    for it in items:
        if "unit_cost_usd" in it:
            total += it.get("qty", 1) * it["unit_cost_usd"]
        else:
            missing.append(it["id"])
    return total, missing


def _budget_row(check_id: str, crit: str, items: list[dict], limit: float, label: str) -> CheckResult:
    total, missing = _total(items)
    ok = total <= limit
    msg = (f"BOM total ${total:.2f} within {label}budget ${limit:.2f}" if ok
           else f"BOM total ${total:.2f} exceeds {label}budget ${limit:.2f}")
    if missing:
        msg += "; no unit cost for: " + ", ".join(missing)
    return CheckResult(check_id, (WARN if missing else PASS) if ok else FAIL, msg, crit, {"parts": []})


def _library_rows(d: dict, items: list) -> list[CheckResult]:
    from hangar.geom.library import list_parts, load_part
    rows: list[CheckResult] = []
    known = set(list_parts())
    for it in items:
        part = it.get("library_part")
        if not part:
            continue
        data = {"parts": it.get("component_ids") or []}
        if part in known:
            data["cad_status"] = load_part(part)["cad_status"]
            rows.append(CheckResult(f"T8.bom.library.{it['id']}", PASS,
                                    f"{it['id']}: library part {part} ({data['cad_status']})", CRIT, data))
        else:
            rows.append(CheckResult(f"T8.bom.library.{it['id']}", FAIL,
                                    f"{it['id']}: library part {part} not in knowledge/parts/", CRIT, data))
    for c in d.get("components", []):
        g = c.get("geometry") or {}
        if g.get("generator") != "library_part":
            continue
        cid, x = c["id"], (g.get("params") or {}).get("part")
        line = next((it for it in items if cid in (it.get("component_ids") or [])), None)
        z = line.get("library_part") if line else None
        y = line["id"] if line else "none"
        if line is None or z != x:
            rows.append(CheckResult(f"T8.bom.library_match.{cid}", FAIL,
                                    f"{cid}: 3D model is library part {x} but its BOM line {y} says {z}", CRIT,
                                    {"parts": [cid]}))
        else:
            rows.append(CheckResult(f"T8.bom.library_match.{cid}", PASS,
                                    f"{cid}: 3D model and BOM line {y} both name library part {x}", CRIT,
                                    {"parts": [cid]}))
    return rows


@gate("T8.sourcing", 8)
def tier8_sourcing(ctx) -> TierReport | None:
    d = ctx.design.data
    program = load_program()
    prog_budget = (program.get("budget_usd") or {}).get("value")
    has_bom = "bom" in d
    if not has_bom and prog_budget is None:
        return None
    limit_days = load_gate_thresholds()["bom_verified_max_age_days"]["value"]
    res: list[CheckResult] = []
    items = (d.get("bom") or {}).get("items", [])
    if has_bom:
        covered = {cid for it in items for cid in it.get("component_ids") or []}
        purchased = [c["id"] for c in d.get("components", [])
                     if (c.get("manufacturing") or {}).get("method") == "purchased"]
        missing = [cid for cid in purchased if cid not in covered]
        for cid in missing:
            res.append(CheckResult(f"T8.bom.line.{cid}", FAIL, f"{cid} is purchased but has no BOM line", CRIT,
                                   {"component": cid}))
        if not missing and purchased:
            res.append(CheckResult("T8.bom.coverage", PASS,
                                   f"all {len(purchased)} purchased components have a BOM line", CRIT))
        for it in items:
            data = {"parts": it.get("component_ids") or []}
            cid, v = f"T8.bom.verified.{it['id']}", it.get("verified")
            if not v:
                res.append(CheckResult(cid, FAIL, f"{it['id']}: not verified", CRIT, data))
                continue
            try:
                n = (ctx.today - datetime.date.fromisoformat(str(v["date"]))).days
            except (ValueError, KeyError):
                n = -1
            if n < 0:
                res.append(CheckResult(cid, FAIL, f"{it['id']}: verified.date {v.get('date')} is not a past date", CRIT, data))
            elif n > limit_days:
                res.append(CheckResult(cid, FAIL, f"{it['id']}: verified {n} days ago by {v.get('by')} (limit {limit_days} days)",
                                       CRIT, data))
            else:
                res.append(CheckResult(cid, PASS, f"{it['id']}: verified {n} days ago by {v.get('by')} ({v.get('method')})",
                                       CRIT, data))
        res.extend(_library_rows(d, items))
        budget = d.get("requirements", {}).get("budget_usd")
        if budget is not None:
            res.append(_budget_row("T8.budget", "requirements.budget_usd", items, budget, ""))
    if prog_budget is not None:
        if has_bom:
            res.append(_budget_row("T8.program.budget", "program.yaml#budget_usd", items, prog_budget, "program "))
        else:
            res.append(CheckResult("T8.program.budget", SKIP, "no BOM: budget not checked", "program.yaml#budget_usd",
                                   {"parts": []}))
    return TierReport(8, "sourcing", res)
