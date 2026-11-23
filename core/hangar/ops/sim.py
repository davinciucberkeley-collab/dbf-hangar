"""Simulation operations: the MuJoCo drop test (D23), wrapping sim.tier2_sim at the standards drop height."""
from __future__ import annotations

from . import op, OpInputError, OpResult
from .. import pdledit
from ..adapters import skip_result
from ..design import load_design, load_standards
from ..sim import tier2_sim

MUJOCO_FIX = "python -m pip install 'mujoco>=3'"


@op(name="sim.drop", summary="Drop-test the design in MuJoCo at the standards drop height (joint peak loads, rest, stability).")
def drop(path: str) -> OpResult:
    p = pdledit.resolve_design_path(path)
    if not p.is_file():
        raise OpInputError(f"no design at {path}")
    try:
        design = load_design(p)
    except Exception as e:  # noqa: BLE001 - unreadable or malformed design is an input error
        raise OpInputError(f"cannot read design {path}: {e}") from e

    results = tier2_sim(design, load_standards(), {})
    checks = [{"check_id": r.check_id, "status": r.status, "message": r.message,
               "criterion": r.criterion, "data": r.data} for r in results]
    messages = [f"{r.check_id} {r.status}: {r.message}" for r in results]

    if any(r.check_id == "T2.sim" and r.status == "SKIP" for r in results):  # D37: a missing tool is ok, status SKIP, exit 0
        skip = skip_result("mujoco", f"mujoco not installed; dynamic simulation skipped; fix: {MUJOCO_FIX}", "sim.drop")
        skip.data["checks"] = checks
        return skip
    ok = not any(r.status == "FAIL" for r in results)
    return OpResult(ok=ok, data={"checks": checks}, messages=messages)
