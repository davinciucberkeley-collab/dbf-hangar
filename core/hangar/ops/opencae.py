"""OpenCAE CLI operations (U18.1): run a design through `python -m opencae` and store the results; save the CLI location.
OpenCAE is GPL-3.0 and is only ever run as an external program."""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from . import op, OpResult, OpInputError
from .. import opencae_cli, opencae_export, pdledit
from ..design import load_design


def _load(path: str):
    try:
        return load_design(pdledit.resolve_design_path(path))
    except Exception as e:  # noqa: BLE001 - report any load failure cleanly
        raise OpInputError(f"cannot load {path}: {e}") from e


@op(name="opencae.run", summary="Run a design through the OpenCAE CLI (mass, propulsion, structure, cfd, flight) and store the results (SKIP with the fix command when OpenCAE or a solver is missing).",
    mutates=True, adapters=("opencae",))
def run_op(path: str, analyses: str = "mass,propulsion", force: bool = False) -> OpResult:
    from ..adapters import get_adapter, skip_result
    design = _load(path)
    names = tuple(a.strip() for a in analyses.split(",") if a.strip())
    bad = [a for a in names if a not in opencae_cli.ANALYSES]
    if not names or bad:
        raise OpInputError("analyses must be a comma list of " + ", ".join(opencae_cli.ANALYSES) + (f"; unknown: {', '.join(bad)}" if bad else ""))
    ok, detail = get_adapter("opencae").cli_available()
    if not ok:
        r = skip_result("opencae", detail, design.id)
        r.data = {"status": "SKIP", "adapter": "opencae", "design": design.id}
        return r
    cli = opencae_cli.find_cli()
    solvers = opencae_cli.solver_status(opencae_cli.doctor(cli))
    work = Path(tempfile.mkdtemp(prefix="opencae-proj-"))
    try:
        try:
            exp = opencae_export.export_project(design, work, names, solvers)
        except ValueError as e:
            raise OpInputError(str(e)) from e
        skipped = dict(exp["skipped"])
        msgs = [f"{a}: skipped: {why}" for a, why in skipped.items()]
        todo = tuple(a for a in names if a not in skipped)
        if not todo:
            return OpResult(True, {"status": "SKIP", "adapter": "opencae", "design": design.id, "skipped": skipped}, msgs,
                            skipped=list(skipped))
        h = opencae_cli.project_hash(design, work, todo, cli["head"])
        rec = opencae_cli.load_result(design)
        if rec and rec.get("hash") == h and not force:
            return OpResult(True, {"status": "CACHED", "hash": h, "design": design.id, "skipped": skipped},
                            msgs + ["unchanged since the stored run; add --force to run again"], skipped=list(skipped))
        run = opencae_cli.run_project(work, todo, cli)
        if run["result"] is None:
            return OpResult(False, {"status": "ERROR", "design": design.id, "returncode": run["returncode"]},
                            msgs + ["OpenCAE run failed:\n" + run["stderr_tail"]])
        p = opencae_cli.store_result(design, h, opencae_cli.design_fingerprint(design, todo), todo, cli["head"], run["result"])
        verdict = run["result"].get("verdict")
        return OpResult(run["returncode"] == 0, {"status": "DONE", "hash": h, "design": design.id, "analyses": list(todo),
                                                  "verdict": verdict, "skipped": skipped},
                        msgs + [f"OpenCAE verdict {verdict}; results in {p.as_posix()}"], changed_files=[p.as_posix()],
                        skipped=list(skipped))
    finally:
        shutil.rmtree(work, ignore_errors=True)


@op(name="opencae.setup", summary="Save the OpenCAE CLI location once (opencae.local.json keys cli_python and cli_root).", mutates=True)
def setup_op(cli_python: str = "", cli_root: str = "") -> OpResult:
    cli = opencae_cli.find_cli(cli_python or None, cli_root or None)
    if not cli["found"]:
        raise OpInputError(f"OpenCAE CLI not found with python={cli['python']!r} root={cli['root']!r}; root must hold opencae/cli.py (a clone of OpenCAEModel main)")
    p = opencae_cli.save_cli_config(cli["python"], cli["root"])
    return OpResult(True, {"config": p.as_posix(), "python": cli["python"], "root": cli["root"]}, [f"saved {p}"],
                    changed_files=[p.as_posix()])
