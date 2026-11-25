"""OpenCAEModel's own CLI as an external program (U18.1, D89/D93).

OpenCAEModel is GPL-3.0. It is run only as an external program through `python -m opencae`; no source from it is
copied into this repository. This module finds it, reads its doctor report, hashes its inputs and stores its results.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

from . import fea
from .design import Design

CLI_ENV = ("OPENCAE_CLI_PYTHON", "OPENCAE_CLI_ROOT")
ANALYSES = ("mass", "propulsion", "structure", "cfd", "flight")

# file stem -> keys; each key is found at the top level or one level inside a top-level group of that yaml
STANDARDS_KEYS = {
    "design-standards": ("ultimate_factor", "hover_thrust_to_weight_min"),
    "operations": ("battery_usable_fraction", "mission_hover_min", "mission_cruise_min",
                   "electrical_rating_min_ratio", "energy_reserve_fraction"),
}

NO_CFD = ("no CFD solver: OpenFOAM not found and SU2_CFD not found; run: opencae setup su2 --yes "
          "(downloads about 40 MB from github.com/su2code/SU2, a human step)")


def _head(root: str) -> str:
    try:
        p = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True, timeout=30)
        line = (p.stdout or "").strip().splitlines()
        if p.returncode == 0 and line:
            return line[0]
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        for line in (Path(root) / "pyproject.toml").read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("version") and "=" in line:
                return line.split("=", 1)[1].strip().strip("\"'")
    except OSError:
        pass
    return ""


def find_cli(python: str | None = None, root: str | None = None) -> dict:
    """{python, root, found, how, head}: arguments, then CLI_ENV, then cli_python / cli_root in opencae.local.json,
    then auto (sibling OpenCAEModel* folder with opencae/cli.py; FEA's Python search)."""
    cfg = {}
    if fea.CONFIG_FILE.exists():
        try:
            cfg = json.loads(fea.CONFIG_FILE.read_text())
        except json.JSONDecodeError:
            cfg = {}
        if not isinstance(cfg, dict):
            cfg = {}
    env_py, env_rt = os.environ.get(CLI_ENV[0]), os.environ.get(CLI_ENV[1])
    py = python or env_py or cfg.get("cli_python")
    rt = root or env_rt or cfg.get("cli_root")
    how = ("given" if (python or root) else "env" if (env_py or env_rt)
           else "opencae.local.json" if (cfg.get("cli_python") or cfg.get("cli_root")) else "auto")
    if not rt:
        for cand in sorted(fea.REPO_ROOT.parent.glob("OpenCAEModel*")):
            if (cand / "opencae" / "cli.py").is_file():
                rt = str(cand)
                break
    if not py:
        py = fea.find_opencae()["python"]
    found = bool(py and rt and Path(py).exists() and (Path(rt) / "opencae" / "cli.py").is_file())
    return {"python": py, "root": rt, "found": found, "how": how, "head": _head(rt) if found else ""}


def run_cli(cli: dict, args: list[str], timeout: int = 3600) -> tuple[int, dict | None, str]:
    env = dict(os.environ, PYTHONPATH=cli["root"] + os.pathsep + os.environ.get("PYTHONPATH", ""),
               PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.run([cli["python"], "-m", "opencae", *args], cwd=cli["root"], env=env,
                          capture_output=True, text=True, timeout=timeout)
    try:
        parsed = json.loads(proc.stdout)
    except (ValueError, TypeError):
        parsed = None
    if not isinstance(parsed, dict):
        parsed = None
    return proc.returncode, parsed, (proc.stderr or "")[-3000:]


def doctor(cli: dict) -> dict:
    rc, obj, err = run_cli(cli, ["doctor", "--json"], timeout=300)
    if rc != 0 or obj is None:
        why = (err.strip().splitlines() or [f"opencae doctor exited {rc} without JSON"])[-1]
        return {"error": why}
    return obj


def _su2_exe_name() -> str:
    return "SU2_CFD.exe" if os.name == "nt" else "SU2_CFD"


def _find_su2(environ: dict, home: Path) -> str:
    for var in ("SU2_RUN", "OPENCAE_SU2"):
        v = environ.get(var)
        if not v:
            continue
        p = Path(v)
        if p.is_file():
            return str(p)
        if p.is_dir():
            for hit in sorted(p.glob(f"**/{_su2_exe_name()}")):
                return str(hit)
    w = shutil.which("SU2_CFD")
    if w:
        return w
    for base in (home / ".opencae" / "solvers", Path("C:/SU2")):
        if base.is_dir():
            for hit in sorted(base.glob(f"**/bin/{_su2_exe_name()}")):
                return str(hit)
    return ""


def solver_status(doc: dict, environ: dict | None = None, home: Path | None = None) -> dict:
    environ = os.environ if environ is None else environ
    home = Path.home() if home is None else home
    if "error" in doc:
        return {"ccx": (False, str(doc["error"])), "cfd": (False, str(doc["error"]))}
    cx = doc.get("ccx") or {}
    ccx = (True, str(cx.get("path") or "ccx found")) if cx.get("available") else (
        False, "CalculiX ccx not found" + (f": {cx['note']}" if cx.get("note") else ""))
    of = doc.get("openfoam") or {}
    if of.get("available"):
        return {"ccx": ccx, "cfd": (True, "OpenFOAM " + str(of.get("path") or ""))}
    su2 = _find_su2(environ, home)
    return {"ccx": ccx, "cfd": (True, "SU2_CFD " + su2) if su2 else (False, NO_CFD)}


def cli_available() -> tuple[bool, str]:
    cli = find_cli()
    if cli["found"]:
        return True, f"OpenCAE CLI root={cli['root']} python={cli['python']} head={cli['head']}"
    return False, ("OpenCAE CLI not found; run: plane opencae setup --cli-python <python> "
                   "--cli-root <OpenCAEModel clone>")


def result_path(design: Design) -> Path:
    return design.base_dir / "opencae" / "results.json"


def standards_fingerprint() -> bytes:
    from .gates.fidelity import resolve_threshold
    picked: dict = {}
    for stem, keys in STANDARDS_KEYS.items():
        if stem == "design-standards":   # the file design.STANDARDS_PATH points at, so an edited copy is honoured
            std = fea.load_standards()
            vals = {}
            for k in keys:
                entry = std.get(k)
                if not (isinstance(entry, dict) and "source" in entry):
                    entry = next(g[k] for g in std.values() if isinstance(g, dict) and isinstance(g.get(k), dict))
                vals[k] = entry["value"]
        else:
            vals = {k: resolve_threshold(f"{stem}.yaml#{k}")["value"] for k in keys}
        picked[stem] = vals
    return json.dumps(picked, sort_keys=True, separators=(",", ":")).encode("utf-8")


def project_hash(design: Design, project_dir: Path, analyses: tuple[str, ...], head: str) -> str:
    h = hashlib.sha256()
    h.update(json.dumps(sorted(analyses)).encode())
    h.update((project_dir / "drone.json").read_bytes())
    h.update((project_dir / "airframe.stl").read_bytes())
    h.update(head.encode())
    h.update(standards_fingerprint())
    return h.hexdigest()[:16]


def design_fingerprint(design: Design, analyses: tuple[str, ...]) -> str:
    from .geom import overlay
    from .geom.registry import component_files
    h = hashlib.sha256()
    h.update(json.dumps(sorted(analyses)).encode())
    with overlay.forced_off():
        h.update(json.dumps(design.data, sort_keys=True, separators=(",", ":"), default=str).encode())
        inputs = design.base_dir / "opencae-inputs.yaml"
        if inputs.is_file():
            h.update(inputs.read_bytes())
        files = set()
        for c in design.components:
            mf = ((c.get("geometry") or {}).get("mesh") or {}).get("file")
            if mf and (design.base_dir / mf).is_file():
                files.add(design.base_dir / mf)
            elif "generator" in (c.get("geometry") or {}):
                for rel in sorted(component_files(c)):
                    if (design.base_dir / rel).is_file():
                        files.add(design.base_dir / rel)
        for f in sorted(files):
            h.update(f.read_bytes())
    h.update(standards_fingerprint())
    return h.hexdigest()[:16]


def run_project(project_dir: Path, analyses: tuple[str, ...], cli: dict, log=print) -> dict:
    bad = [a for a in analyses if a not in ANALYSES]
    if bad:
        raise ValueError(f"unknown analysis {bad[0]!r}; expected one of {', '.join(ANALYSES)}")
    log(f"opencae run {project_dir} --only {','.join(analyses)}")
    rc, obj, tail = run_cli(cli, ["run", str(project_dir), "--only", ",".join(analyses), "--force", "--json"])
    return {"returncode": rc, "result": obj, "stderr_tail": tail}


def store_result(design: Design, hash_: str, design_hash: str, analyses: tuple[str, ...], head: str,
                 result: dict) -> Path:
    path = result_path(design)
    path.parent.mkdir(parents=True, exist_ok=True)
    rec = {"design": design.id, "hash": hash_, "design_hash": design_hash, "analyses": list(analyses),
           "opencae_head": head, "result": result}
    path.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
    return path


def load_result(design: Design) -> dict | None:
    try:
        rec = json.loads(result_path(design).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return rec if isinstance(rec, dict) else None
