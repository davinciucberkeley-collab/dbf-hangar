"""Resolve a PDL 1.2 design: references -> numbers, generated meshes -> mass_g (computed on load, never stored)."""
from __future__ import annotations

import json
from pathlib import Path

from hangar import yamlfast
from hangar.geom import materials
from hangar.geom.kernel import GeometryError, volume_mm3
from hangar.geom.params import resolve_references


def is_generated(c) -> bool:
    return isinstance(c, dict) and isinstance(c.get("geometry"), dict) and "generator" in c["geometry"]


def _strip(cid, msg: str) -> str:
    pre = f"{cid}: "
    return msg[len(pre):] if msg.startswith(pre) else msg


def generated_volumes(c: dict, base_dir: Path) -> list[float]:
    """Volumes (mm3) of the parts a generator component builds, cavities subtracted. Uses the geometry cache. Raises GeometryError."""
    from hangar.geometry import _base_parts
    try:
        return [volume_mm3(m) for m in _base_parts(c, base_dir)]
    except ValueError as e:                    # geometry._apply_cavities: "a cavity removes the whole part"
        raise GeometryError(str(e)) from e


def _cut_poses(data: dict) -> None:
    """Give every wing_panel the current placement of each neighbour in its cut_files (params.cut_poses, derived, never stored)."""
    import numpy as np
    from hangar.geometry import _transform
    comps = [c for c in data.get("components") or [] if isinstance(c, dict)]
    by_file = {}
    for c in comps:
        g = c.get("geometry")
        if isinstance(g, dict) and isinstance(g.get("mesh"), dict) and "file" in g["mesh"]:
            by_file.setdefault(g["mesh"]["file"], c)
    for w in comps:
        if not is_generated(w) or w["geometry"]["generator"] != "wing_panel":
            continue
        params = w["geometry"].get("params")
        if not isinstance(params, dict):
            continue
        params.pop("cut_poses", None)
        out = []
        try:
            inv = np.linalg.inv(_transform(w))
            for f in params.get("cut_files") or []:
                c = by_file.get(f)
                if c is None:
                    continue
                m = inv @ _transform(c)
                if not np.allclose(m, np.eye(4), atol=1e-9):
                    out.append({"file": f, "matrix": [round(float(x), 9) for x in m[:3].ravel()]})
        except (KeyError, TypeError, ValueError, np.linalg.LinAlgError):
            continue
        if out:
            params["cut_poses"] = out


def _derive_hinges(data: dict, base_dir, errors: dict) -> None:
    """hinge_from: generator -> location, articulation.pivot and axis from the child wing_panel hinge line (resolved data only)."""
    import numpy as np
    from hangar.geom.wing import hinge_line
    from hangar.geometry import _transform
    comps = {str(c.get("id")): c for c in data.get("components") or [] if isinstance(c, dict)}
    for a in data.get("attachments") or []:
        if not isinstance(a, dict) or a.get("hinge_from") != "generator":
            continue
        child = comps.get(str(a.get("child")))
        generic = "child must be a wing_panel part elevon with side left or right and the attachment needs an articulation"
        try:
            if (child is None or not is_generated(child) or child["geometry"]["generator"] != "wing_panel"
                    or not isinstance(a.get("articulation"), dict)):
                raise ValueError(generic)
            q0, q1 = hinge_line(child["geometry"]["params"], base_dir)
            T = _transform(child)
            p0, p1 = (( T @ np.array([*q, 1.0]))[:3] for q in (q0, q1))
        except (GeometryError, KeyError, TypeError, ValueError) as e:
            errors.setdefault(str(a.get("child")), "hinge_from: " + (str(e) or generic))
            continue
        axis = (p1 - p0) / np.linalg.norm(p1 - p0)
        if axis[1] < 0:
            axis = -axis
        pivot = [round(float(v), 4) for v in (p0 + p1) / 2]
        a["location"] = list(pivot)
        a["articulation"]["pivot"] = list(pivot)
        a["articulation"]["axis"] = [round(float(v), 4) for v in axis]


def fill_swept_poses(data: dict, base_dir: Path, errors: dict[str, str]) -> None:
    """Set `cut_poses` on swept wing_panel cuts (builds meshes); failures go to `errors`. Runs before the mass fill."""
    for c in data.get("components") or []:
        g = c.get("geometry") if isinstance(c, dict) else None
        gp = g.get("params") if isinstance(g, dict) and g.get("generator") == "wing_panel" else None
        if isinstance(gp, dict) and gp.get("cut_files") and gp.get("cut_sweep", "swept") == "swept":
            try:
                from hangar.geom.sweeps import swept_cut_poses
                by_file = {e["file"]: e for e in gp.get("cut_poses") or []}
                for e in swept_cut_poses(data, list(gp["cut_files"]), base_dir, str(c.get("id"))):
                    by_file.setdefault(e["file"], {"file": e["file"]})["matrices"] = e["matrices"]
                if by_file:
                    gp["cut_poses"] = [by_file[f] for f in sorted(by_file)]
            except Exception as e:
                errors[str(c.get("id"))] = f"cut_sweep: {e}"


def fill_generated_mass(data: dict, base_dir: Path, errors: dict[str, str]) -> None:
    """Set `mass_g` on every generated component with a mass_model (builds its meshes); failures go to `errors`."""
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


def resolve_design_data(raw: dict, base_dir: Path, *, mass: bool = True) -> tuple[dict, dict[str, str]]:
    data = resolve_references(raw)
    errors: dict[str, str] = {}
    _cut_poses(data)
    _derive_hinges(data, base_dir, errors)   # before the swept poses: hinge_from pockets sweep about the derived axis
    if mass:
        fill_swept_poses(data, base_dir, errors)
        fill_generated_mass(data, base_dir, errors)
    return data, errors


def _signature(c: dict) -> str:
    return json.dumps([c.get("geometry"), c.get("mass_model"), c.get("position"), c.get("rotation_deg")],
                      sort_keys=True, default=str)


def _aircraft(data: dict, plane_path: Path, errors: dict):
    """(mass_g, cg_mm) of the resolved design, or (None, None) while a generated part fails (no mass without it). Other errors propagate."""
    if errors:
        return None, None
    from hangar.design import Design
    from hangar.mass import mass_properties
    mp = mass_properties(Design(data, Path(plane_path)))
    return mp["mass_g"], mp["cg_mm"]


def regeneration_report(old_text: str, new_text: str, plane_path: Path) -> dict | None:
    """Regeneration report for an edit, or None when no generated part is involved.

    Refuses (OpInputError) only when the edit NEWLY breaks a generated part. `data["regenerated"]` is only reported
    by the op when `components` is non-empty; `failing` lists parts that still fail and were failing before the edit.
    """
    from hangar.ops import OpInputError
    old_raw, new_raw = yamlfast.safe_load(old_text), yamlfast.safe_load(new_text)

    def has_gen(d):
        return isinstance(d, dict) and any(is_generated(c) for c in (d.get("components") or []))

    def has_params(d):
        return isinstance(d, dict) and "parameters" in d

    if not (has_gen(old_raw) or has_gen(new_raw) or has_params(old_raw) or has_params(new_raw)):
        return None
    base = Path(plane_path).parent
    old, old_err = resolve_design_data(old_raw, base)
    new, new_err = resolve_design_data(new_raw, base)
    for cid, msg in new_err.items():
        if cid not in old_err:                 # newly broken by this edit; a part that already failed is reported, not refused
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
    if comps:
        om, ocg = _aircraft(old, plane_path, old_err)
        nm, ncg = _aircraft(new, plane_path, new_err)
    else:
        om = ocg = nm = ncg = None
    inter = {"moved": [], "joints": [], "new": [], "cleared": []}
    if not new_err and not old_err:
        try:
            _interference(old, new, plane_path, inter)
        except Exception as e:                 # reported, never a reason to refuse
            inter["error"] = str(e)
    return {"components": comps, "mass_g": [om, nm], "cg_mm": [ocg, ncg],
            "failing": {cid: msg for cid, msg in new_err.items()}, "interference": inter}


def _interference(old: dict, new: dict, plane_path: Path, inter: dict) -> None:
    """Fill `inter` (moved parts, changed joints, new and cleared neutral-pose interference rows) for two resolved designs."""
    from hangar.checks import interference_rows
    from hangar.design import Design, load_standards

    def dump(*x):
        return json.dumps(list(x), sort_keys=True, default=str)

    def comps(d):
        return {c["id"]: dump(c.get("geometry"), c.get("position"), c.get("rotation_deg"))
                for c in d.get("components") or [] if isinstance(c, dict)}

    def joints(d):
        out = {}
        for a in d.get("attachments") or []:
            if isinstance(a, dict):
                art = a.get("articulation")
                out[a.get("id") or f"{a.get('parent')}->{a.get('child')}"] = (
                    dump(a.get("location"), art.get("pivot") if isinstance(art, dict) else None), a)
        return out

    oc, nc = comps(old), comps(new)
    oj, nj = joints(old), joints(new)
    moved = sorted(i for i, s in nc.items() if oc.get(i) != s)
    changed = {k: v[1] for k, v in nj.items() if k not in oj or oj[k][0] != v[0]}
    inter["moved"], inter["joints"] = moved, sorted(changed)
    if not moved and not changed:
        return
    only = set(moved)
    for a in changed.values():
        only |= {a.get("parent"), a.get("child")}
    std = load_standards()
    rows = {}
    for tag, data in (("new", new), ("old", old)):
        out = {}
        for r in interference_rows(Design(data, Path(plane_path)), std, only):
            key = r.data["joint"] if "joint" in r.data else tuple(sorted(r.data["pair"]))
            out[(r.check_id, key)] = r
        rows[tag] = out

    def entry(r):
        key = r.data["joint"] if "joint" in r.data else sorted(r.data["pair"])
        return {"check_id": r.check_id, "key": key, "message": r.message}

    for name, a, b in (("new", rows["new"], rows["old"]), ("cleared", rows["old"], rows["new"])):
        inter[name] = sorted((entry(r) for k, r in a.items() if k not in b),
                             key=lambda e: (e["check_id"], str(e["key"])))
