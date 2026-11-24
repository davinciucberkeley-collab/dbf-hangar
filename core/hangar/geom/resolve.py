"""Resolve a PDL 1.2 design: references -> numbers, generated meshes -> mass_g (computed on load, never stored)."""
from __future__ import annotations

import json
import os
from pathlib import Path

import yaml

from hangar.geom import materials
from hangar.geom.kernel import GeometryError, volume_mm3
from hangar.geom.params import resolve_references
from hangar.geom.registry import build_component, component_files

_VOLUMES: dict[str, list[float]] = {}
_VOLUMES_MAX = 512


def is_generated(c) -> bool:
    return isinstance(c, dict) and isinstance(c.get("geometry"), dict) and "generator" in c["geometry"]


def _strip(cid, msg: str) -> str:
    pre = f"{cid}: "
    return msg[len(pre):] if msg.startswith(pre) else msg


def _key(c: dict, base_dir: Path) -> str | None:
    key = json.dumps(c["geometry"], sort_keys=True, default=str)
    for f in component_files(c):
        p = Path(base_dir) / f
        try:
            st = p.stat()
        except OSError:
            return None
        key += f"|{os.path.abspath(p)}|{st.st_mtime_ns}|{st.st_size}"
    return key


def generated_volumes(c: dict, base_dir: Path) -> list[float]:
    """Volumes (mm3) of the parts a generator component builds; cached in memory by content key. Raises GeometryError."""
    key = _key(c, base_dir)
    if key is not None and key in _VOLUMES:
        return list(_VOLUMES[key])
    vols = [volume_mm3(m) for m in build_component(c, base_dir)]
    if key is not None:
        if len(_VOLUMES) >= _VOLUMES_MAX:
            _VOLUMES.clear()
        _VOLUMES[key] = vols
    return list(vols)


def resolve_design_data(raw: dict, base_dir: Path) -> tuple[dict, dict[str, str]]:
    data = resolve_references(raw)
    errors: dict[str, str] = {}
    design_materials = data.get("materials") if isinstance(data.get("materials"), dict) else None
    for c in data.get("components") or []:
        mm = c.get("mass_model") if isinstance(c, dict) else None
        if not is_generated(c) or not isinstance(mm, dict):
            continue
        cid = str(c.get("id"))
        try:
            vol = sum(generated_volumes(c, base_dir))
            dens = (float(mm["density_g_cm3"]) if "density_g_cm3" in mm
                    else materials.density_g_cm3(str(mm.get("material")), design_materials))
            c["mass_g"] = materials.mass_g(vol, dens, float(mm.get("extra_g", 0.0)))
        except GeometryError as e:
            errors[cid] = _strip(cid, str(e))
        except KeyError as e:
            errors[cid] = str(e.args[0]) if e.args else "unknown material"
        except (TypeError, ValueError) as e:
            errors[cid] = f"mass_model: {e}"
    return data, errors


def _signature(c: dict) -> str:
    return json.dumps([c.get("geometry"), c.get("mass_model"), c.get("position"), c.get("rotation_deg")],
                      sort_keys=True, default=str)


def _aircraft(data: dict, plane_path: Path):
    from hangar.design import Design
    from hangar.mass import mass_properties
    try:
        mp = mass_properties(Design(data, Path(plane_path)))
        return mp["mass_g"], mp["cg_mm"]
    except Exception:
        return None, None


def regeneration_report(old_text: str, new_text: str, plane_path: Path) -> dict | None:
    from hangar.ops import OpInputError
    old_raw, new_raw = yaml.safe_load(old_text), yaml.safe_load(new_text)

    def has_gen(d):
        return isinstance(d, dict) and any(is_generated(c) for c in (d.get("components") or []))

    if not (has_gen(old_raw) or has_gen(new_raw)):
        return None
    base = Path(plane_path).parent
    old, old_err = resolve_design_data(old_raw, base)
    new, new_err = resolve_design_data(new_raw, base)
    for cid, msg in new_err.items():
        raise OpInputError(f"regeneration failed: {cid}: {msg}")
    old_by = {c["id"]: c for c in old.get("components") or []}
    comps = {}
    for c in new.get("components") or []:
        if not is_generated(c):
            continue
        o = old_by.get(c["id"])
        if o is not None and is_generated(o) and _signature(o) == _signature(c):
            continue
        entry = {"volume_mm3": [None, None], "mass_g": [None, None]}
        for i, comp, err in ((0, o, old_err), (1, c, new_err)):
            if comp is None or not is_generated(comp) or comp["id"] in err:
                continue
            try:
                entry["volume_mm3"][i] = sum(generated_volumes(comp, base))
            except GeometryError:
                continue
            entry["mass_g"][i] = comp.get("mass_g")
        comps[c["id"]] = entry
    om, ocg = _aircraft(old, plane_path)
    nm, ncg = _aircraft(new, plane_path)
    return {"components": comps, "mass_g": [om, nm], "cg_mm": [ocg, ncg]}
