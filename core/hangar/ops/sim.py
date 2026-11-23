"""Simulation operations: the MuJoCo drop test (D23), wrapping sim.drop_test (standards drop height unless --height-m)."""
from __future__ import annotations

from . import op, OpInputError, OpResult
from .. import pdledit
from ..adapters import skip_result
from ..design import load_design, load_standards
from ..sim import drop_test

MUJOCO_FIX = "python -m pip install 'mujoco>=3'"


@op(name="sim.drop", summary="Drop-test the design in MuJoCo (joint peak loads, rest, stability) at the standards drop height, or at --height-m.")
def drop(path: str, height_m: float = 0.0) -> OpResult:
    if height_m < 0:
        raise OpInputError("--height-m must not be negative (0 = the standards drop height)")
    p = pdledit.resolve_design_path(path)
    if not p.is_file():
        raise OpInputError(f"no design at {path}")
    try:
        design = load_design(p)
    except Exception as e:  # noqa: BLE001 - unreadable or malformed design is an input error
        raise OpInputError(f"cannot read design {path}: {e}") from e

    std = load_standards()
    used_h = height_m if height_m > 0 else float(std["sim"]["drop_height_m"]["value"])
    results = drop_test(design, used_h, std=std)
    checks = [{"check_id": r.check_id, "status": r.status, "message": r.message,
               "criterion": r.criterion, "data": r.data} for r in results]
    messages = [f"{r.check_id} {r.status}: {r.message}" for r in results]

    if any(r.check_id == "T2.sim" and r.status == "SKIP" for r in results):  # D37: a missing tool is ok, status SKIP, exit 0
        skip = skip_result("mujoco", f"mujoco not installed; dynamic simulation skipped; fix: {MUJOCO_FIX}", "sim.drop")
        skip.data["checks"] = checks
        skip.data["height_m"] = used_h
        return skip
    ok = not any(r.status == "FAIL" for r in results)
    return OpResult(ok=ok, data={"checks": checks, "height_m": used_h}, messages=messages)
