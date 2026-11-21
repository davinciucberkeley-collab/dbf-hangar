"""OpenCAE adapter. OpenCAE Studio is GPL-3.0 and is run as an external program; its source is never copied into
this repository. The adapter launches the in-repo runner (`hangar/opencae_runner.py`) with OpenCAE's own Python."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from .. import fea
from ..ops import OpInputError, OpResult
from . import skip_result


class OpenCAE:
    name = "opencae"
    planned = False

    def available(self) -> tuple[bool, str]:
        oc = fea.find_opencae()
        if oc["found"]:
            detail = f"OpenCAE python={oc['python']} root={oc['root']} (found via {oc['how']})"
            exe = shutil.which("opencae")
            if exe:
                detail += f"; an 'opencae' executable is on PATH at {exe}, not used yet"
            return True, detail
        return False, ("OpenCAE not found; run: plane fea setup --opencae-python <python of the environment with "
                       "OpenCAE's libraries> --opencae-root <OpenCAE folder>")

    def solve_job(self, job: dict, oc: dict | None = None, log=print) -> dict:
        oc = oc or fea.find_opencae()
        if not oc["found"]:
            raise RuntimeError(self.available()[1])
        work = Path(tempfile.mkdtemp(prefix="opencae-job-"))
        try:
            job = dict(job, out=str(work / "result.json"))
            (work / "job.json").write_text(json.dumps(job))
            env = dict(os.environ, PYTHONPATH=str(oc["root"]) + os.pathsep + os.environ.get("PYTHONPATH", ""),
                       PYTHONIOENCODING="utf-8")
            proc = subprocess.run([oc["python"], str(fea.RUNNER), str(work / "job.json")], cwd=str(work), env=env,
                                  capture_output=True, text=True, timeout=3600)
            for line in proc.stdout.splitlines():
                log(line)
            if not (work / "result.json").exists():
                raise RuntimeError("OpenCAE run failed:\n" + (proc.stderr or proc.stdout)[-3000:])
            return json.loads((work / "result.json").read_text())
        finally:
            shutil.rmtree(work, ignore_errors=True)

    def run(self, design, **params) -> OpResult:
        part = params.get("part")
        if not part:
            raise OpInputError("opencae.run needs part=<component id>")
        drop = params.get("drop")
        log = params.get("log", print)
        ok, detail = self.available()
        if not ok:
            return skip_result("opencae", detail, part)
        try:
            record = fea.run(design, part, fea.find_opencae(), drop=drop, log=log)
        except ValueError as e:
            return OpResult(ok=False, data={"status": "ERROR", "part": part}, messages=[str(e)])
        return OpResult(ok=record["status"] != "FAIL" and not record.get("error"), data=record,
                        messages=[f"{part}: {record['status']}"],
                        changed_files=[fea.result_path(design, part).as_posix()])
