"""U16.1 S4: `design add-linkage` writes arm, rod, horn, pin, their attachments and the four_bar mechanism."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Literal

import numpy as np

from . import op, OpResult, OpInputError
from .bay import _clean, _vec
from .edit import _plane, _text, _write_with_log
from .. import pdledit, yamlfast
from ..design import Design, load_design
from ..geometry import rotation_matrix


def _unit(v) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    return v / np.linalg.norm(v)


def _norm(x):
    """Numbers rounded to 4 decimals (whole numbers as int), so a re-run compares equal to what it wrote."""
    if isinstance(x, dict):
        return {k: _norm(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_norm(v) for v in x]
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        return _clean(x)
    return x


def _vecs(v) -> list:
    return [_clean(t) for t in v]


def _elements(prefix, servo_id, hinge_id, surface, O, a_o, tip0, pin0, P, n, *, servo_range, input_range, ratio):
    t = _unit(np.cross(_unit(pin0 - tip0), n))
    rod_end = pin0 - 2.0 * _unit(pin0 - tip0)

    def strut(cid, a, b, mass, mfg, chord=None):
        params = {"start": _vecs(a), "end": _vecs(b), "diameter": 1.5}
        if chord:
            params["chord"] = chord
        return {"id": cid, "type": "other", "geometry": {"generator": "strut", "params": params},
                "position": [0, 0, 0], "mass_g": mass, "manufacturing": dict(mfg)}

    laser = {"method": "laser-cut", "machine": "jacobs-laser"}
    bought = {"method": "purchased"}
    comps = [strut(f"{prefix}-arm", O, tip0, 1, laser, 4),
             strut(f"{prefix}-rod", tip0, rod_end, 1, bought),
             strut(f"{prefix}-horn", P, pin0, 1, laser, 4),
             strut(f"{prefix}-pin", pin0 - 0.6 * t, pin0 + 0.6 * t, 0.2, bought)]

    def att(aid, parent, child, method, loc, **extra):
        return {"id": aid, "parent": parent, "child": child, "method": method, "location": _vecs(loc),
                "embed_ok": True, "rated_load_n": 10, **extra}

    atts = [att(f"{prefix}-servo-arm", servo_id, f"{prefix}-arm", "bolted", O,
                articulation={"type": "revolute", "pivot": _vecs(O), "axis": _vecs(a_o),
                              "range_deg": [-_clean(servo_range), _clean(servo_range)]}),
            att(f"{prefix}-arm-rod", f"{prefix}-arm", f"{prefix}-rod", "hinge", tip0, kinematic_link=True),
            att(f"{prefix}-horn-mount", surface, f"{prefix}-horn", "glued", P),
            att(f"{prefix}-horn-pin", f"{prefix}-horn", f"{prefix}-pin", "bolted", pin0)]
    mech = {"id": f"{prefix}-drive", "driver": f"{prefix}-servo-arm", "kinematics": "four_bar", "driven": [hinge_id],
            "input_range_deg": [-_clean(input_range), _clean(input_range)],
            "expect": [{"attachment": hinge_id, "ratio": ratio}],
            "link": {"driver_end": f"{prefix}-arm-rod", "follower_end": f"{prefix}-horn-pin"}}
    return comps, atts, mech


def _geometry(design: Design, servo: str, hinge: str, station: float, arm_length: float, horn_height: float,
              horn_dir: np.ndarray):
    """O, a_o, P, n, ax, surface id, hinge id, tip0, pin0 (unrounded) from the resolved design."""
    from ..geom.library import load_part
    data = design.data_without_mass()
    comp = next((c for c in data["components"] if c.get("id") == servo), None)
    if comp is None:
        raise OpInputError(f"no component {servo!r} (--servo)")
    g = comp.get("geometry") or {}
    pid = (g.get("params") or {}).get("part") if g.get("generator") == "library_part" else None
    if not pid:
        raise OpInputError(f"{servo}: must be a library_part component (a servo with part frames)")
    frames = load_part(pid).get("frames") or {}
    if "output" not in frames:
        raise OpInputError(f"{servo}: library part {pid!r} has no frames.output in its part.yaml")
    att = next((a for a in data["attachments"] if a.get("id") == hinge), None)
    if att is None:
        raise OpInputError(f"no attachment {hinge!r} (--hinge)")
    art = att.get("articulation")
    if not art:
        raise OpInputError(f"{hinge}: has no articulation; --hinge must be a hinge attachment")
    rot = rotation_matrix(comp.get("rotation_deg") or [0, 0, 0])
    pos = np.array(comp.get("position") or [0, 0, 0], float)
    O = rot @ np.array(frames["output"]["point"], float) + pos
    a_o = _unit(rot @ np.array(frames["output"]["axis"], float))
    ax = _unit(art["axis"])
    P = np.array(art["pivot"], float) + station * ax
    d = (O - P) - ((O - P) @ ax) * ax
    if np.linalg.norm(d) < 1e-9:
        raise OpInputError("the servo shaft lies on the hinge line; move the servo or give another --station")
    n = _unit(np.cross(ax, d))
    if n @ horn_dir < 0:
        n = -n
    if abs(n @ horn_dir) < 0.3:
        raise OpInputError(f"the horn direction is ambiguous (normal to hinge and shaft is {n.round(3).tolist()}); "
                           f"give --horn-dir along the side the horn should stand")
    pin0 = P + horn_height * n
    v = pin0 - O
    w = v - (v @ a_o) * a_o
    W = float(np.linalg.norm(w))
    if W <= arm_length:
        raise OpInputError(f"arm length must be shorter than the distance from the servo shaft to the horn pin "
                           f"({W:.4f} mm)")
    return dict(O=O, a_o=a_o, P=P, n=n, W=W, w=w, pin0=pin0, surface=att["child"])


@op(name="design.add-linkage", summary="Generate a servo linkage: arm, rod, horn and pin components, their four attachments and a four_bar mechanism '<prefix>-drive', from a library servo with part frames and a hinge attachment (read from the resolved design, so a derived hinge is followed). Defaults are layout defaults for a 1:10 RC model, not thresholds. Idempotent: an identical re-run writes nothing; changed elements are replaced in place. One logged write; reports the ratio, tip, pin, rod length and the T0 FAIL, T1 FAIL (naming the new parts) and T6 rows.",
    mutates=True, render=lambda r: "\n".join(r.messages))
def add_linkage_op(path: str, *, servo: str, hinge: str, station: float, prefix: str = None, arm_length: float = 6.0,
                   horn_height: float = 13.0, arm_side: Literal["+", "-"] = "+", horn_dir: str = "0,0,-1",
                   input_range: float = 20.0, servo_range: float = 30.0, why: str) -> OpResult:
    from ..checks import validate
    from ..gates.mechanisms import link_ratios, simulate_mechanism
    from ..geom.params import expression_errors
    plane = _plane(path)
    text = _text(plane)
    if not why.strip():
        raise OpInputError("why must not be empty")
    hd = np.array(_vec(horn_dir, 3, "--horn-dir"), float)
    if np.linalg.norm(hd) < 1e-9:
        raise OpInputError("--horn-dir must not be zero")
    hd = _unit(hd)
    if arm_length <= 0 or horn_height <= 0:
        raise OpInputError("--arm-length and --horn-height must be positive")
    prefix = prefix or hinge
    design = load_design(plane)
    g = _geometry(design, servo, hinge, station, arm_length, horn_height, hd)
    O, a_o, P, n, W, w, pin0 = (g[k] for k in ("O", "a_o", "P", "n", "W", "w", "pin0"))
    wu = w / W
    phi = float(np.arccos(arm_length / W))
    side = 1.0 if arm_side == "+" else -1.0
    e = np.cos(phi) * wu + side * np.sin(phi) * np.cross(a_o, wu)
    tip0 = O + arm_length * e
    r4 = lambda v: np.array([_clean(t) for t in v], float)
    O, a_o, P, n, tip0, pin0 = (r4(v) for v in (O, a_o, P, n, tip0, pin0))
    rod_length = float(np.linalg.norm(pin0 - tip0))
    raw_hinge_id = hinge
    comps, atts, mech = _elements(prefix, servo, raw_hinge_id, g["surface"], O, a_o, tip0, pin0, P, n,
                                  servo_range=servo_range, input_range=input_range, ratio=0.0)
    # the ratio is what the gate itself computes from these points, rounded to 2 decimals
    mem = copy.deepcopy(design.data_without_mass())
    mem["components"] = [c for c in mem["components"] if c.get("id") not in {x["id"] for x in comps}] + copy.deepcopy(comps)
    mem["attachments"] = [a for a in mem["attachments"] if a.get("id") not in {x["id"] for x in atts}] + copy.deepcopy(atts)
    mem["mechanisms"] = [m for m in mem.get("mechanisms", []) if m.get("id") != mech["id"]] + [copy.deepcopy(mech)]
    ratio = round(link_ratios(Design(data=mem, path=design.path), mech)[raw_hinge_id], 2)
    ratio = ratio + 0.0
    mech["expect"][0]["ratio"] = ratio

    before = yamlfast.safe_load(text)
    working, entries = text, []
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def patch(old, new, key):
        nonlocal working
        if isinstance(new, dict):
            if not isinstance(old, dict) or set(old) - set(new):
                raise OpInputError(f"{key}: cannot be replaced in place (other keys present); edit the file by hand")
            for k, v in new.items():
                if k in old:
                    patch(old[k], v, f"{key}.{k}")
                else:
                    working = pdledit.add_value(working, f"{key}.{k}", v)
        elif isinstance(new, list):
            if not isinstance(old, list) or len(old) != len(new):
                raise OpInputError(f"{key}: cannot be replaced in place (list length changed); edit the file by hand")
            for i, v in enumerate(new):
                patch(old[i], v, f"{key}[{i}]")
        elif old != new:
            working = pdledit.patch_text(working, key, new)

    def put(listkey: str, element: dict):
        nonlocal working
        data = yamlfast.safe_load(working)
        lst = data.get(listkey)
        key = f"{listkey}[{element['id']}]"
        old = next((x for x in lst or [] if isinstance(x, dict) and x.get("id") == element["id"]), None)
        if old is None:
            if lst is None:
                working = pdledit.add_value(working, listkey, [element])
            else:
                working, _, _ = pdledit.append_element(working, listkey, element)
            entries.append({"date": stamp, "key": key, "old": None, "new": element, "why": why, "kind": "add"})
            return
        if _norm(old) == _norm(element):
            return
        patch(old, element, key)
        entries.append({"date": stamp, "key": key, "old": old, "new": element, "why": why, "kind": "modify"})

    for c in comps:
        put("components", c)
    for a in atts:
        put("attachments", a)
    put("mechanisms", mech)

    changed = bool(entries)
    if changed:
        after = yamlfast.safe_load(working)
        fresh = [x for x in expression_errors(after) if x not in set(expression_errors(before))]
        if fresh:
            raise OpInputError("; ".join(f"{o}: {p}: {m}" for o, p, m in fresh))
        pdledit.check_schema(before, after, "linkage")
        log = _write_with_log(plane, text, working, entries)

    card = validate(load_design(plane), max_tier=6)
    rows = []
    for t in card.tiers:
        for x in t.results:
            names_new = any(i in x.message for i in (*(c["id"] for c in comps), *(a["id"] for a in atts)))
            if ((t.tier == 0 and x.status == "FAIL") or (t.tier == 1 and x.status == "FAIL" and names_new)
                    or (x.check_id.startswith("T6.") and x.check_id.endswith(f".{mech['id']}"))):
                rows.append([x.check_id, x.status, x.message])
    final = load_design(plane)
    fm = next(m for m in final.data["mechanisms"] if m["id"] == mech["id"])
    try:
        sim = simulate_mechanism(final, fm)
        mu = [s["transmission_deg"] for s in sim["steps"] if "transmission_deg" in s]
        min_mu = round(min(mu), 3) if mu else None
    except RuntimeError:
        min_mu = None
    ids_c, ids_a = [c["id"] for c in comps], [a["id"] for a in atts]
    data_out = {"components": ids_c, "attachments": ids_a, "mechanism": mech["id"], "ratio": ratio,
                "tip0": [round(float(v), 4) + 0.0 for v in tip0], "pin0": [round(float(v), 4) + 0.0 for v in pin0],
                "rod_length": round(rod_length, 4), "min_transmission_deg": min_mu, "rows": rows, "changed": changed}
    msgs = [f"{prefix}: ratio {ratio:g}, rod {rod_length:.2f} mm, tip {data_out['tip0']}, pin {data_out['pin0']}"
            + ("" if changed else "; unchanged")]
    msgs += [f"{r[0]} {r[1]}: {r[2]}" for r in rows if r[1] != "PASS"]
    return OpResult(True, data_out, msgs, changed_files=[str(plane), str(log)] if changed else [])
