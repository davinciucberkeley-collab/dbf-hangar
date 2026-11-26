"""Per-design viewer artifacts (glb, scorecard, mass) and index entries.

Shared by `plane build-index` (static viewer on GitHub Pages) and `plane studio` (local app),
so both show exactly the same data for a design.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import yaml

from . import fea
from .checks import validate
from .export import export_glb
from .gates.mechanisms import _atts, _clamp, _input_range, link_overrides, simulate_mechanism
from .geometry import articulated_attachments, att_label, is_point_mass, pose_transforms
from .mass import mass_properties


def _jsonable(o):
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, np.generic):
        return o.item()
    if isinstance(o, Path):
        return str(o)
    return str(o)


def dumps(obj) -> str:
    return json.dumps(obj, indent=2, default=_jsonable)


def parts_json(design) -> dict:
    """The part tree the viewer draws: parent, depth and flags per component, plus every attachment label.

    Carries only ids, positions and booleans already in plane.yaml; `local_only` is a flag, never geometry (D83).
    """
    from .geom import overlay
    comps = design.components
    atts = design.data.get("attachments", []) or []
    root = design.data.get("root")
    ids = {c["id"] for c in comps}
    reached: dict[str, tuple] = {}
    if root in ids:
        reached[root] = (None, 0, None)
        queue = [root]
        while queue:
            cur = queue.pop(0)
            for a in atts:
                ch = a.get("child")
                if a.get("parent") == cur and ch in ids and ch not in reached:
                    reached[ch] = (cur, reached[cur][1] + 1, a)
                    queue.append(ch)
    raw = {c.get("id"): c for c in (design.raw or design.data).get("components", [])}
    local = set(overlay.design_overlay_parts(design))
    parts = []
    for c in comps:
        parent, depth, a = reached.get(c["id"], (None, 0, None))
        g = c.get("geometry") or {}
        parts.append({
            "id": c["id"], "type": c.get("type"), "parent": parent,
            "attachment": att_label(a) if a else None, "depth": depth,
            "articulated": bool(a and a.get("articulation")),
            "position_mm": [float(v) for v in (c.get("position") or [0, 0, 0])],
            "position_expr": any(isinstance(v, str) for v in (raw.get(c["id"], {}).get("position") or [])),
            "has_cavities": bool(c.get("cavities")),
            "visual_only": bool(c.get("visual_only", False)),
            "local_only": g.get("generator") == "library_part" and (g.get("params") or {}).get("part") in local,
        })
    return {"design": str(design.data.get("id", design.base_dir.name)), "root": root, "parts": parts,
            "attachments": [{"label": att_label(a), "parent": a["parent"], "child": a["child"]} for a in atts]}


def mechanism_sweeps(design) -> dict | None:
    """Per-step part transforms for every mechanism (the T6 sweep, 1 degree steps) for the viewer's Physics mode.
    Designs with articulations but no `mechanisms` block get one pseudo-mechanism per articulated joint."""
    mechs = design.data.get("mechanisms") or []
    all_arts = articulated_attachments(design)
    arts = [a for a in all_arts if a["articulation"].get("type") != "continuous"]
    spins = [a for a in all_arts if a["articulation"].get("type") == "continuous"]
    if not mechs and not all_arts:
        return None
    if not mechs:
        mechs = [{"id": "sweep-" + att_label(a), "driver": att_label(a), "driven": [att_label(a)],
                  "input_range_deg": a["articulation"]["range_deg"], "expect": []} for a in arts]
    atts = _atts(design)
    skip = {c["id"] for c in design.components if is_point_mass(c)}
    out = []
    for mech in mechs:
        steps = []
        for st in simulate_mechanism(design, mech)["steps"]:
            drv = _clamp(st["input_deg"], atts[mech["driver"]]["articulation"]["range_deg"])
            ov = link_overrides(design, mech, st["input_deg"], next(iter(st["followers"].values()))) if mech.get("kinematics") == "four_bar" else None
            tf = pose_transforms(design, {mech["driver"]: drv, **st["followers"]}, ov)
            steps.append({"input_deg": st["input_deg"], "followers": st["followers"],
                          "transforms": {cid: np.round(t, 12 if ov else 6).ravel().tolist() for cid, t in tf.items()
                                         if cid not in skip and not np.allclose(t, np.eye(4))}})
        out.append({"id": mech["id"], "driver": mech["driver"], "driven": list(mech["driven"]),
                    "input_range_deg": list(_input_range(design, mech)), "steps": steps})
    used = {mech["driver"] for mech in mechs} | {a for mech in mechs for a in mech["driven"]} \
        | {e["attachment"] for mech in mechs for e in mech.get("expect", [])}
    for a in spins:
        label = att_label(a)
        if label in used:
            continue
        steps = []
        for k in range(361):
            tf = pose_transforms(design, {label: float(k)})
            steps.append({"input_deg": float(k), "followers": {},
                          "transforms": {cid: np.round(t, 6).ravel().tolist() for cid, t in tf.items()
                                         if cid not in skip and not np.allclose(t, np.eye(4))}})
        out.append({"id": "spin-" + label, "driver": label, "driven": [label], "input_range_deg": [0, 360],
                    "steps": steps})
    return {"design": str(design.data.get("id", design.base_dir.name)), "mechanisms": out}


def fea_rows(design) -> dict | None:
    """Stress results per printed part, read from designs/<id>/fea/<part>.json (nothing is recomputed)."""
    parts = fea.eligible_parts(design)
    if not parts:
        return None
    rows, allow, uf = [], None, None
    for pid in parts:
        row = {"part": pid, "description": design.component(pid).get("description", ""), "status": None,
               "up_to_date": None, "worst": None, "error": None}
        path = fea.result_path(design, pid)
        if path.exists():
            rec = json.loads(path.read_text(encoding="utf-8"))
            allow = rec.get("allowable_mpa") if allow is None else allow
            uf = rec.get("ultimate_factor") if uf is None else uf
            cases = [c for c in rec.get("cases", []) if c.get("safety_factor_at_ultimate") is not None]
            w = min(cases, key=lambda c: c["safety_factor_at_ultimate"], default=None)
            row.update(status=rec["status"], up_to_date=rec.get("hash") == fea.part_hash(design, pid),
                       error=rec.get("error"),
                       worst=w and {"name": w["name"], "stress_mpa": w.get("max_von_mises_away_mpa"),
                                    "safety_factor": w["safety_factor_at_ultimate"]})
        rows.append(row)
    return {"allowable_mpa": allow, "ultimate_factor": uf, "parts": rows}


def _summary(text: str) -> str:
    return text.split("\n")[0].split(".")[0][:100]


def index_extras(entries: list[dict], root: Path, public: bool = False) -> dict:
    """index.json v2 keys shared by `plane build-index` and Plane Studio. public=True cuts the ledger to the
    fields that may be published on the (public) Pages site."""
    from .ledger import Ledger
    from .ops.update import _read_entries
    ledger = []
    for it in Ledger(Path(root) / "ledger" / "items.yaml").items:
        d = asdict(it)
        ledger.append({"id": d["id"], "kind": d["kind"], "status": d["status"], "owner": d["owner"],
                       "summary": _summary(d["text"]), "due": d["due"], "decided_in": d["decided_in"]} if public else d)
    updates = []
    for f in sorted((Path(root) / "updates").glob("*/updates.yaml"), reverse=True):
        try:
            rows = _read_entries(f)
        except yaml.YAMLError:
            continue
        updates.append({"week": f.parent.name, "entries": [{k: r.get(k) for k in ("person", "link", "changed")} for r in rows]})
    return {"version": 2, "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "scorecards": {e["id"]: e["scorecard"] for e in entries if e.get("scorecard")},
            "mechanisms": {e["id"]: e["mechanisms"] for e in entries if e.get("mechanisms")},
            "ledger": ledger, "updates": updates}


def design_entry(design, out_dir: Path, file_id: str | None = None) -> dict:
    """Write <file_id>.glb, .scorecard.json and .mass.json into out_dir and return the index entry.

    file_id defaults to the design id; the studio passes a content-hashed name so browsers never
    show a stale model after an edit.
    """
    meta = design.data
    did = str(meta.get("id", design.base_dir.name))
    fid = file_id or did
    out_dir.mkdir(parents=True, exist_ok=True)
    export_glb(design, out_dir / f"{fid}.glb")
    card = validate(design)
    card_dict = card.to_dict()
    (out_dir / f"{fid}.scorecard.json").write_text(dumps(card_dict) + "\n")
    mp = mass_properties(design)
    (out_dir / f"{fid}.mass.json").write_text(dumps(mp) + "\n")
    (out_dir / f"{fid}.parts.json").write_text(dumps(parts_json(design)) + "\n")
    extra = {}
    for key, fn in (("mechanisms", mechanism_sweeps), ("fea", fea_rows)):
        extra[key] = None
        try:
            data = fn(design)
        except Exception:  # noqa: BLE001  (a bad mechanism is reported by gate T6)
            data = None
        if data is not None:
            (out_dir / f"{fid}.{key}.json").write_text(dumps(data) + "\n")
            extra[key] = f"{fid}.{key}.json"
    entry = {
        "id": did,
        "name": str(meta.get("name", "")),
        "status": str(meta.get("status", "")),
        "morphology": meta.get("morphology") or {},
        "accepted": bool(card.accepted),
        "mass_g": mp["mass_g"],
        "cg_mm": mp["cg_mm"],
        "glb": f"{fid}.glb",
        "scorecard": f"{fid}.scorecard.json",
        "mass": f"{fid}.mass.json",
        "parts": f"{fid}.parts.json",
        "tiers": {str(t["tier"]): t["status"] for t in card_dict["tiers"]},
        "error": None,
        **extra,
    }
    from .geom import overlay
    local_only = overlay.design_overlay_parts(design)
    if local_only:
        entry["local_only"] = local_only
    return entry


def error_entry(did: str, message: str, meta: dict | None = None) -> dict:
    meta = meta or {}
    return {
        "id": did,
        "name": str(meta.get("name", "")),
        "status": str(meta.get("status", "")),
        "morphology": meta.get("morphology") or {},
        "accepted": False,
        "mass_g": None,
        "cg_mm": None,
        "glb": None,
        "scorecard": None,
        "mass": None,
        "parts": None,
        "tiers": {},
        "mechanisms": None,
        "fea": None,
        "error": message,
    }
