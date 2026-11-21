"""Stress-check operations (U2.3): plan, run, setup. OpenCAE is reached only through its adapter."""
from __future__ import annotations

from . import op, OpResult, OpInputError
from .. import fea as fea_core
from .. import pdledit
from ..design import load_design


def _load(path: str):
    try:
        return load_design(pdledit.resolve_design_path(path))
    except Exception as e:  # noqa: BLE001 - report any load failure cleanly
        raise OpInputError(f"cannot load {path}: {e}") from e


@op(name="fea.plan", summary="Show the supports and loads for a printed part without running OpenCAE.")
def plan_op(path: str, part: str) -> OpResult:
    design = _load(path)
    try:
        meta = fea_core.plan(design, part)["meta"]
    except ValueError as e:
        raise OpInputError(str(e)) from e
    return OpResult(True, {"part": part, "meta": meta})


@op(name="fea.run", summary="Stress-check printed parts in OpenCAE (SKIP with the fix command when OpenCAE is missing).",
    mutates=True, adapters=("opencae",))
def run_op(path: str, part: str = "", all_: bool = False) -> OpResult:
    from ..adapters import get_adapter, skip_result
    design = _load(path)
    eligible = fea_core.eligible_parts(design)
    todo = [part] if part else (eligible if all_ else [])
    if not todo:
        raise OpInputError("give --part ID or --all; printed structural parts: " + ", ".join(eligible))
    if part and part not in eligible:
        raise OpInputError(f"{part} is not an eligible printed structural part; choose from: " + ", ".join(eligible))
    ad = get_adapter("opencae")
    ok, detail = ad.available()
    if not ok:
        r = skip_result("opencae", detail, todo[0])
        r.skipped = list(todo)
        r.data = {"status": "SKIP", "adapter": "opencae", "parts": todo}
        return r
    drop = fea_core.joint_loads(design)
    rows, msgs, changed = [], [], []
    for pid in todo:
        r = ad.run(design, part=pid, drop=drop)
        rec = r.data if isinstance(r.data, dict) else {}
        if not rec.get("status") or rec["status"] == "ERROR":
            rows.append({"part": pid, "status": "ERROR"})
            msgs.extend(r.messages)
            continue
        rows.append({"part": pid, "status": rec["status"],
                     "cases": [{"name": c.get("name"), "status": c.get("status")} for c in rec.get("cases", [])]})
        msgs.append(f"{pid}: {rec['status']}")
        changed.extend(f for f in r.changed_files if f not in changed)
    ok_all = all(x["status"] not in ("FAIL", "ERROR") for x in rows)
    return OpResult(ok_all, {"results": rows}, msgs, changed_files=changed)


@op(name="fea.setup", summary="Save the OpenCAE location once (opencae.local.json).", mutates=True)
def setup_op(opencae_python: str = "", opencae_root: str = "") -> OpResult:
    oc = fea_core.find_opencae(opencae_python or None, opencae_root or None)
    if not oc["found"]:
        raise OpInputError(f"OpenCAE not found with python={oc['python']!r} root={oc['root']!r}")
    p = fea_core.save_config(oc["python"], oc["root"])
    return OpResult(True, {"config": p.as_posix()}, [f"saved {p}"], changed_files=[p.as_posix()])
