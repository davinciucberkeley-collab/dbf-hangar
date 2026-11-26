"""Local CAD overlay (U12.5, D82/D83): licensed part models that replace a library part's geometry on this machine only.

Mass, BOM and part.yaml always come from the committed part; the overlay changes geometry only. Nothing is written."""
from __future__ import annotations

import contextlib
import importlib.util
import json
import os
import subprocess
from pathlib import Path

import numpy as np
from .._lazy import trimesh
import yaml

from hangar.design import REPO_ROOT
from hangar.geom import kernel

CONFIG_ENV = "PLANE_CAD_OVERLAY"
CONFIG_FILE = REPO_ROOT / "cad-overlay.local.json"
_MESH_EXT = (".stl", ".obj", ".ply", ".off")
_STEP_EXT = (".step", ".stp")
_UNITS = {"mm": 1.0, "m": 1000.0, "in": 25.4}
_CACHE: dict = {}
_FORCED = 0


def _configured_root() -> Path | None:
    env = os.environ.get(CONFIG_ENV)
    if env is not None:
        root = None if env.strip().lower() in ("", "off") else Path(env)
    elif Path(CONFIG_FILE).exists():
        try:
            val = json.loads(Path(CONFIG_FILE).read_text(encoding="utf-8"))["path"]
            root = None if str(val).strip().lower() in ("", "off") else Path(val)
        except (OSError, ValueError, KeyError, TypeError):
            root = None
    else:
        root = Path.home() / "parts-cad"
    return root if root is not None and root.is_dir() else None


def overlay_root() -> Path | None:
    return None if _FORCED else _configured_root()


def overlay_configured() -> bool:
    return _configured_root() is not None


def manifest_count() -> int:
    """Part folders with an overlay.yaml under the configured root (describes the machine, ignores forced_off)."""
    root = _configured_root()
    if root is None:
        return 0
    try:
        return sum(1 for p in root.glob("*/overlay.yaml") if p.is_file())
    except OSError:
        return 0


def ignored_note() -> str | None:
    """The stderr note for the baseline commands, or None when no manifest exists (an empty folder is no overlay)."""
    if manifest_count() > 0:
        return "note: CAD overlay ignored here (baselines and FEA results never use licensed files)"
    return None


@contextlib.contextmanager
def forced_off():
    """Ignore the overlay inside the block (nesting allowed; restored on exceptions)."""
    global _FORCED
    _FORCED += 1
    try:
        yield
    finally:
        _FORCED -= 1


def _empty(state: str, **kw) -> dict:
    d = {"state": state, "root": None, "file": None, "licence": None, "note": None, "units": None, "reason": None,
         "extents_mm": None, "envelope_mm": None, "fit": None}
    d.update(kw)
    return d


def _manifest(part_id: str):
    """(root, manifest path) or None when there is no overlay for this part."""
    root = overlay_root()
    if root is None:
        return None
    mp = root / part_id / "overlay.yaml"
    if not mp.is_file():
        return None
    return root, mp


def _read(mp: Path) -> dict:
    try:
        data = yaml.safe_load(mp.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as e:
        raise ValueError(f"unreadable manifest: {e}") from None
    if not isinstance(data, dict):
        raise ValueError("manifest is not a mapping")
    if not isinstance(data.get("file"), str) or not data["file"].strip():
        raise ValueError("manifest needs 'file'")
    if not isinstance(data.get("licence"), str) or not data["licence"].strip():
        raise ValueError("manifest needs a non-empty 'licence'")
    if data.get("units", "mm") not in _UNITS:
        raise ValueError(f"units {data.get('units')!r} must be one of {', '.join(_UNITS)}")
    m = data.get("matrix")
    if m is not None and not (isinstance(m, list) and len(m) == 12
                              and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in m)):
        raise ValueError("matrix must be 12 numbers (3x4 row-major)")
    if data.get("recentre", "bbox") not in ("bbox", "none"):
        raise ValueError("recentre must be bbox or none")
    return data


def _closed_bodies(bodies) -> list:
    """Bodies that touch along a face share non-manifold edges, so the split also returns open fragments of the
    junction faces. Drop the open fragments when closed bodies exist and the fragments enclose no net volume
    (opposite-facing junction faces cancel); otherwise keep everything and let the caller fail."""
    closed = [b for b in bodies if b.is_watertight]
    opened = [b for b in bodies if not b.is_watertight]
    if closed and opened:
        tol = 1e-6 * sum(abs(float(b.volume)) for b in closed)
        if abs(sum(float(b.volume) for b in opened)) <= tol:
            return closed
    return bodies


def _load(path: Path, data: dict) -> trimesh.Trimesh:
    loaded = trimesh.load(str(path), force="mesh")
    if isinstance(loaded, trimesh.Scene):
        loaded = trimesh.util.concatenate(list(loaded.geometry.values()))
    m = loaded.copy()
    if path.suffix.lower() in _STEP_EXT:
        m.apply_scale(1000.0)  # cascadio hands trimesh a glb in metres; "units" then describes nothing extra
    m.apply_scale(_UNITS[data.get("units", "mm")])
    if data.get("matrix") is not None:
        t = np.eye(4)
        t[:3, :] = np.array(data["matrix"], dtype=float).reshape(3, 4)
        m.apply_transform(t)
    m.merge_vertices()
    bodies = m.split(only_watertight=False)
    if len(bodies) == 0:
        raise kernel.GeometryError("overlay mesh has no faces")
    bodies = _closed_bodies(bodies)
    m = kernel.require_solid(bodies[0], "overlay") if len(bodies) == 1 else kernel.union(bodies)
    if data.get("recentre", "bbox") == "bbox":
        m = m.copy()
        m.apply_translation(-m.bounds.mean(axis=0))
    return m


def _evaluate(part_id: str) -> tuple[dict, "trimesh.Trimesh | None"]:
    found = _manifest(part_id)
    if found is None:
        root = overlay_root()
        return _empty("absent", root=str(root) if root else None), None
    root, mp = found
    st = _empty("unusable", root=str(root))
    try:
        data = _read(mp)
    except ValueError as e:
        return {**st, "reason": str(e)}, None
    f = mp.parent / data["file"]
    st.update(file=str(f), licence=data["licence"], note=data.get("note"), units=data.get("units", "mm"))
    if f.suffix.lower() not in _MESH_EXT + _STEP_EXT:
        return {**st, "reason": f"unsupported file type {f.suffix!r}"}, None
    if not f.is_file():
        return {**st, "reason": f"file not found: {f}"}, None
    if f.suffix.lower() in _STEP_EXT and importlib.util.find_spec("cascadio") is None:
        return {**st, "reason": "STEP needs cascadio (pip install cascadio) or export an STL"}, None
    sf, sm = f.stat(), mp.stat()
    key = (str(f.resolve()), sf.st_mtime_ns, sf.st_size, sm.st_mtime_ns, sm.st_size)
    if key not in _CACHE:
        try:
            _CACHE[key] = (_load(f, data), None)
        except Exception as e:  # noqa: BLE001 - any load failure makes the overlay unusable, never fatal
            _CACHE[key] = (None, f"cannot load overlay: {e}")
    m, err = _CACHE[key]
    if m is None:
        return {**st, "reason": err}, None
    from hangar.geom import library
    try:
        env = [float(x) for x in library.load_part(part_id)["dimensions_mm"]]
    except Exception as e:  # noqa: BLE001
        return {**st, "reason": f"committed part unavailable: {e}"}, None
    ext = [float(x) for x in m.extents]
    fit = [a / b for a, b in zip(ext, env)]
    st.update(extents_mm=ext, envelope_mm=env, fit=fit)
    if any(r > 3.0 or r < 1 / 3 for r in fit):
        return {**st, "reason": "overlay size does not match the committed envelope "
                f"(fit x y z = {fit[0]:.2f} {fit[1]:.2f} {fit[2]:.2f}); check units and matrix"}, None
    return {**st, "state": "present"}, m


def status(part_id: str) -> dict:
    return _evaluate(part_id)[0]


def mesh(part_id: str) -> "trimesh.Trimesh | None":
    return _evaluate(part_id)[1]


def cache_files(part_id: str) -> list[str]:
    found = _manifest(part_id)
    if found is None:
        return []
    _, mp = found
    out = [str(mp.resolve())]
    try:
        f = mp.parent / _read(mp)["file"]
        if f.is_file():
            out.append(str(f.resolve()))
    except ValueError:
        pass
    return out


class OverlayOutputRefused(RuntimeError):
    """An output built from licensed overlay parts was aimed at a tracked or unignored repository path."""


def design_overlay_parts(design) -> list[str]:
    """Sorted unique library part ids used by the design whose overlay is present. Never raises."""
    ids = set()
    try:
        for c in design.components:
            g = c.get("geometry") or {}
            pid = (g.get("params") or {}).get("part")
            if g.get("generator") == "library_part" and isinstance(pid, str):
                try:
                    if status(pid)["state"] == "present":
                        ids.add(pid)
                except Exception:  # noqa: BLE001
                    pass
    except Exception:  # noqa: BLE001
        return []
    return sorted(ids)


def output_allowed(path) -> tuple[bool, str]:
    p = Path(path).resolve()
    root = Path(REPO_ROOT).resolve()
    if p != root and root not in p.parents:
        return True, "outside the repository"

    def git(*args) -> int:
        return subprocess.run(["git", "-C", str(root), *args, "--", str(p)], capture_output=True).returncode

    try:
        if git("ls-files", "--error-unmatch") == 0:
            return False, "tracked by git"
        rc = git("check-ignore", "-q")
    except OSError:
        return False, "cannot ask git; refusing"
    if rc == 0:
        return True, "git-ignored"
    if rc == 1:
        return False, "inside the repository and not git-ignored"
    return False, "cannot ask git; refusing"


def guard_output(path, design) -> list[str]:
    ids = design_overlay_parts(design)
    if not ids:
        return []
    ok, why = output_allowed(path)
    if not ok:
        raise OverlayOutputRefused(
            f"{path}: this design uses licensed CAD overlay parts ({', '.join(ids)}); outputs built from them stay "
            f"local-only and may not be written to a tracked or unignored path in the repository ({why}). Use a "
            "folder outside the repository, or an ignored one such as viewer/data/ or .studio/.")
    p = Path(path)
    folder = p if (p.is_dir() or not p.suffix) else p.parent
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "LOCAL-ONLY-cad-overlay.txt").write_text(
        f"Built from licensed CAD overlay parts: {', '.join(ids)}. Local use only (non-commercial, internal). "
        "Do not commit, upload or publish this folder.\n", encoding="utf-8")
    return ids
