"""Gate registry (§2.5). A gate is a whole tier: it yields one TierReport. standards/gates.yaml is the table."""
from __future__ import annotations

import datetime
import functools
from dataclasses import dataclass
from typing import Callable

import yaml

from ..design import (REPO_ROOT, FAIL, SKIP, WARN, CheckResult, Design, Scorecard, TierReport, load_standards)

GATES_PATH = REPO_ROOT / "standards" / "gates.yaml"
THRESHOLDS_PATH = REPO_ROOT / "standards" / "gate-thresholds.yaml"
REPORT_ONLY_PREFIX = "report-only until 2026-12-08: "


@dataclass(frozen=True)
class Gate:
    id: str
    tier: int
    name: str
    fn: Callable[["GateContext"], "TierReport | None"]
    needs_mass: bool


@dataclass
class GateContext:
    design: Design
    std: dict
    mp: dict | None
    today: datetime.date


@dataclass(frozen=True)
class DisciplineCheck:
    id: str
    tier: int
    name: str
    fn: Callable[["GateContext", "TierReport | None"], "list[CheckResult]"]


GATES: dict[str, Gate] = {}
DISCIPLINE: dict[str, DisciplineCheck] = {}


def gate(id: str, tier: int, *, needs_mass: bool = False):
    """Register `fn(ctx) -> TierReport | None` as the gate `id` for `tier`; returns fn unchanged."""
    def deco(fn):
        if id in GATES:
            raise ValueError(f"duplicate gate id {id!r}")
        if any(g.tier == tier for g in GATES.values()):
            raise ValueError(f"duplicate gate tier {tier} ({id!r})")
        GATES[id] = Gate(id, tier, id.split(".", 1)[1], fn, needs_mass)
        return fn
    return deco


def discipline_check(id: str, tier: int):
    """Register `fn(ctx, rep) -> list[CheckResult]` as a sub-check of `tier`; `rep` is that tier's TierReport so far (or None). Returns fn."""
    def deco(fn):
        if id in DISCIPLINE:
            raise ValueError(f"duplicate discipline check id {id!r}")
        DISCIPLINE[id] = DisciplineCheck(id, tier, id.split(".", 1)[1], fn)
        return fn
    return deco


@functools.lru_cache(maxsize=None)
def _text(path) -> str:
    return path.read_text(encoding="utf-8")


def load_gate_table() -> list[dict]:
    """Rows of standards/gates.yaml in file order (fresh copies)."""
    return yaml.safe_load(_text(GATES_PATH))["gates"]


def load_discipline_table() -> list[dict]:
    """Rows of standards/gates.yaml `discipline_checks:` in file order."""
    return yaml.safe_load(_text(GATES_PATH))["discipline_checks"]


def load_gate_thresholds() -> dict[str, dict]:
    """Entries of standards/gate-thresholds.yaml (without `version`); a fresh dict each call."""
    data = yaml.safe_load(_text(THRESHOLDS_PATH))
    data.pop("version", None)
    return data


def _import_gates() -> None:
    from .. import checks  # noqa: F401  (registers tiers 0 to 5)
    from . import mechanisms, integration, sourcing, claims, discipline  # noqa: F401


def _report_only(rep: TierReport) -> None:
    for r in rep.results:
        if r.status in (FAIL, SKIP):
            r.data = {**r.data, "report_only": True, "raw_status": r.status}
            r.message = REPORT_ONLY_PREFIX + r.message
            r.status = WARN


def _run_discipline(ctx: GateContext, g: Gate, rep: "TierReport | None", dtable: list[dict], strict: bool) -> list[CheckResult]:
    out: list[CheckResult] = []
    for row in dtable:
        check = DISCIPLINE.get(row["id"])
        if check is None or check.tier != g.tier:
            continue
        try:
            rows = check.fn(ctx, rep)
        except Exception as e:  # noqa: BLE001
            rows = [CheckResult(check.id, FAIL, f"{type(e).__name__}: {e}", row["criterion"])]
        if not strict and not row["blocking"]:
            tmp = TierReport(g.tier, g.name, rows)
            _report_only(tmp)
            rows = tmp.results
        out += rows
    return out


def run_gates(design: Design, max_tier: int = 9, *, strict: bool = False,
              only_tiers: "set[int] | None" = None, today: "datetime.date | None" = None) -> Scorecard:
    _import_gates()
    from ..mass import mass_properties
    from .fidelity import compute_fidelity

    table = {r["id"]: r for r in load_gate_table()}
    dtable = load_discipline_table()
    ordered = sorted(GATES.values(), key=lambda g: g.tier)
    ctx = GateContext(design, load_standards(), None, today or datetime.date.today())

    def card(tiers):
        return Scorecard(design.id, tiers, max_tier, fidelity=compute_fidelity(design, tiers))

    tiers = [ordered[0].fn(ctx)]                # tier 0 runs unwrapped, always
    if tiers[0].status == FAIL:
        return card(tiers)
    todo = [g for g in ordered[1:] if g.tier <= max_tier and (only_tiers is None or g.tier in only_tiers)]
    for i, g in enumerate(todo):
        if g.needs_mass and ctx.mp is None:
            try:
                ctx.mp = mass_properties(design)
            except Exception as e:  # noqa: BLE001
                tiers += [TierReport(h.tier, h.name, [CheckResult(f"T{h.tier}.blocked", FAIL,
                                                                  f"mass properties failed: {e}", table[h.id]["criterion"])])
                          for h in todo[i:] if h.needs_mass]
                return card(tiers)
        try:
            rep = g.fn(ctx)
        except Exception as e:  # noqa: BLE001
            rep = TierReport(g.tier, g.name, [CheckResult(f"T{g.tier}.error", FAIL, f"{type(e).__name__}: {e}",
                                                          table[g.id]["criterion"])])
        if rep is not None and not strict and not table[g.id]["blocking"]:
            _report_only(rep)
        extra = _run_discipline(ctx, g, rep, dtable, strict)
        if extra:
            rep = rep or TierReport(g.tier, g.name, [])
            rep.results.extend(extra)
        if rep is None:
            continue
        tiers.append(rep)
    return card(tiers)
