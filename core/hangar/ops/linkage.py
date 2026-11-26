"""U16.1 S4: `design add-linkage` writes arm, rod, horn, pin, their attachments and the four_bar mechanism.

Construction (D117 amendment): the arm sits on its own plane above the servo's highest point, the horn is rooted on the
surface skin aft of the hinge, the pin sits beside the horn in the arm plane, the rod stops short of the pin.
All constants are layout defaults for a 1:10 RC model, not thresholds.
"""
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

T = 1.5                    # diameter of arm, rod, horn and pin, mm
ARM_GAP = 0.6              # clear gap between the servo's highest point and the arm underside, mm
ROOT_EMBED = 1.0           # horn start below the skin, mm
HORN_EXT = 1.0             # horn end beyond the pin hole, mm
ROD_SHORT = 2.0            # rod stops this far short of the pin, mm
PIN_LEN = 1.2              # pin length, mm
MIN_SKIN_TO_PIN = 2.5      # skin point to pin hole along the horn, mm
MAX_SKIN_TO_PIN = 40.0
DEFAULT_SKIN_TO_PIN = 8.0
DEFLECTION_TOL_MM = 1e-9     # fixed-point tolerance on the arm length, mm
DEFLECTION_MAX_ITER = 50


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


def _elements(prefix, servo_id, hinge_id, surface, Op, a_o, tip0, pin0, K, n, q, H, *, servo_range, input_range, ratio):
    rh = _unit(pin0 - tip0)
    rod_end = pin0 - ROD_SHORT * rh

    def strut(cid, a, b, mass, mfg, chord=None):
        params = {"start": _vecs(a), "end": _vecs(b), "diameter": T}
        if chord:
            params["chord"] = chord
        return {"id": cid, "type": "other", "geometry": {"generator": "strut", "params": params},
                "position": [0, 0, 0], "mass_g": mass, "manufacturing": dict(mfg)}

    laser = {"method": "laser-cut", "machine": "jacobs-laser"}
    bought = {"method": "purchased"}
    comps = [strut(f"{prefix}-arm", Op, tip0, 1, laser, 4),
             strut(f"{prefix}-rod", tip0, rod_end, 1, bought),
             strut(f"{prefix}-horn", K - ROOT_EMBED * n, H + HORN_EXT * n, 1, laser, 4),
             strut(f"{prefix}-pin", pin0 - (PIN_LEN / 2) * q, pin0 + (PIN_LEN / 2) * q, 0.2, bought)]

    def att(aid, parent, child, method, loc, **extra):
        return {"id": aid, "parent": parent, "child": child, "method": method, "location": _vecs(loc),
                "embed_ok": True, "rated_load_n": 10, "rating_basis": "placeholder", **extra}

    atts = [att(f"{prefix}-servo-arm", servo_id, f"{prefix}-arm", "bolted", Op,
                articulation={"type": "revolute", "pivot": _vecs(Op), "axis": _vecs(a_o),
                              "range_deg": [-_clean(servo_range), _clean(servo_range)]}),
            att(f"{prefix}-arm-rod", f"{prefix}-arm", f"{prefix}-rod", "hinge", tip0, kinematic_link=True),
            att(f"{prefix}-horn-mount", surface, f"{prefix}-horn", "glued", K),
            att(f"{prefix}-horn-pin", f"{prefix}-horn", f"{prefix}-pin", "bolted", pin0)]
    mech = {"id": f"{prefix}-drive", "driver": f"{prefix}-servo-arm", "kinematics": "four_bar", "driven": [hinge_id],
            "input_range_deg": [-_clean(input_range), _clean(input_range)],
            "expect": [{"attachment": hinge_id, "ratio": ratio}],
            "link": {"driver_end": f"{prefix}-arm-rod", "follower_end": f"{prefix}-horn-pin"}}
    return comps, atts, mech


def _tip(pin, Op, a_o, arm_length: float, side: float):
    """Arm tip in the arm plane so that arm and rod are at 90 degrees at neutral; and the plane distance W."""
    v = pin - Op
    w = v - (v @ a_o) * a_o
    W = float(np.linalg.norm(w))
    if W <= arm_length:
        raise OpInputError(f"arm length must be shorter than the distance from the servo shaft to the horn pin "
                           f"({W:.4f} mm)")
    wu = w / W
    phi = float(np.arccos(arm_length / W))
    return Op + arm_length * (np.cos(phi) * wu + side * np.sin(phi) * np.cross(a_o, wu))


def _solve_arm(pin0, Op, a_o, side, P, ax, ratio, W) -> float:
    """Arm length whose small-angle gate ratio L / lever(L) equals `ratio` (fixed point of L = ratio * lever(L)).
    Raises OpInputError; `.arm` is the offending length when it reached W, None when it did not converge."""
    def lever(L):
        tip = _tip(pin0, Op, a_o, L, side)
        u = _unit(pin0 - tip)
        return float(abs(u @ np.cross(ax, pin0 - P)))

    def fail(msg, arm):
        e = OpInputError(msg)
        e.arm = arm
        return e

    L = 6.0
    for _ in range(DEFLECTION_MAX_ITER):
        Ln = ratio * lever(L)
        if abs(Ln - L) < DEFLECTION_TOL_MM:
            return Ln
        L = Ln
        if L >= W:
            raise fail("the arm length reached the horn pin distance", L)
    raise fail("the arm length did not converge", None)


def _geometry(design: Design, servo: str, hinge: str, station: float, arm_length: float, side: float,
              horn_height, horn_offset: float, horn_toward: np.ndarray):
    """The linkage points (unrounded) from the resolved design and the servo and surface meshes."""
    from ..geom.library import load_part
    from ..geometry import component_parts
    data = design.data_without_mass()
    comps = {c.get("id"): c for c in data["components"]}
    comp = comps.get(servo)
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
    surf = att["child"]
    rot = rotation_matrix(comp.get("rotation_deg") or [0, 0, 0])
    pos = np.array(comp.get("position") or [0, 0, 0], float)
    O = rot @ np.array(frames["output"]["point"], float) + pos
    a_o = _unit(rot @ np.array(frames["output"]["axis"], float))
    ax = _unit(art["axis"])
    P = np.array(art["pivot"], float) + station * ax
    # 1. the arm plane, above the highest point of the servo
    parts_s = component_parts(comp, design.base_dir)
    sv = np.vstack([m.vertices for m in parts_s])
    h_top = max(0.0, float(((sv - O) @ a_o).max()))
    Op = O + (h_top + T / 2 + ARM_GAP) * a_o
    # 2. the horn direction
    d = (O - P) - ((O - P) @ ax) * ax
    if np.linalg.norm(d) < 1e-9:
        raise OpInputError("the servo shaft lies on the hinge line; move the servo or give another --station")
    n = _unit(np.cross(ax, d))
    if n @ horn_toward < 0:
        n = -n
    if abs(n @ horn_toward) < 0.3:
        raise OpInputError(f"the horn direction is ambiguous (normal to hinge and shaft is {n.round(3).tolist()}); "
                           f"give --horn-toward along the side the horn should stand")
    # 3. the horn root on the skin, aft of the hinge
    parts_f = component_parts(comps[surf], design.base_dir)
    cen = np.mean(np.vstack([m.vertices for m in parts_f]), axis=0)
    u = _unit(np.cross(n, ax))
    if u @ (cen - P) < 0:
        u = -u
    Ph = P + horn_offset * u
    best = None
    for m in parts_f:
        locs, _rays, tris = m.ray.intersects_location([Ph], [n], multiple_hits=True)
        for loc, tri in zip(locs, tris):
            s_ = float((loc - Ph) @ n)
            if s_ > 1e-6 and m.face_normals[tri] @ n > 0 and (best is None or s_ < best):
                best = s_
    if best is None:
        raise OpInputError(f"horn root point {[round(float(v), 2) for v in Ph]} is not inside {surf}; "
                           f"lower --horn-offset or move --station")
    K = Ph + best * n
    # 4. the pin beside the horn
    c0 = np.array([1.0, 0, 0]) - n[0] * n
    if np.linalg.norm(c0) < 1e-6:
        c0 = np.array([0.0, 1.0, 0]) - n[1] * n
    c0 = _unit(c0)
    q = _unit(np.cross(n, c0))
    plane_formula = horn_height is None and abs(n @ a_o) >= 0.3

    def solve(sg):
        off = sg * T * q
        if horn_height is not None:
            s = float(horn_height)
        elif plane_formula:
            s = float(((Op - K - off) @ a_o) / (n @ a_o))
        else:
            s = DEFAULT_SKIN_TO_PIN
        H = K + s * n
        return s, H, H + off

    _, H_A, _ = solve(0.0)
    tip_A = _tip(H_A, Op, a_o, arm_length, side)
    sg = 1.0 if (tip_A - H_A) @ q >= 0 else -1.0
    s, H, pin0 = solve(sg)
    if plane_formula and not MIN_SKIN_TO_PIN <= s <= MAX_SKIN_TO_PIN:
        raise OpInputError(f"the servo arm plane is {s:.2f} mm from the horn skin point along the horn (needs "
                           f"{MIN_SKIN_TO_PIN:g} to {MAX_SKIN_TO_PIN:g} mm): move the servo, turn it (rotation_deg) so "
                           f"its shaft points to the horn side, or give --horn-height")
    tip0 = _tip(pin0, Op, a_o, arm_length, side)
    v = pin0 - Op
    W = float(np.linalg.norm(v - (v @ a_o) * a_o))
    return dict(Op=Op, a_o=a_o, K=K, n=n, q=q, H=H, s=s, pin0=pin0, tip0=tip0, surface=surf, P=P, ax=ax, W=W)


def _add_linkage(path: str, *, servo: str, hinge: str, station: float, prefix: str = None, arm_length: float = None,
                   deflection: float = 15.0, horn_height: float = None, horn_offset: float = 6.0,
                   arm_side: Literal["+", "-"] = "+", horn_toward: str = "0,0,-1", input_range: float = 20.0,
                   servo_range: float = 30.0, why: str) -> OpResult:
    from ..checks import validate
    from ..gates.mechanisms import link_ratios, simulate_mechanism
    from ..geom.params import expression_errors
    plane = _plane(path)
    text = _text(plane)
    if not why.strip():
        raise OpInputError("why must not be empty")
    hd = np.array(_vec(horn_toward, 3, "--horn-toward"), float)
    if np.linalg.norm(hd) < 1e-9:
        raise OpInputError("--horn-toward must not be zero")
    hd = _unit(hd)
    if (arm_length is not None and arm_length <= 0) or (horn_height is not None and horn_height <= 0) or horn_offset < 0:
        raise OpInputError("--arm-length and --horn-height must be positive and --horn-offset not negative")
    prefix = prefix or hinge
    design = load_design(plane)
    side = 1.0 if arm_side == "+" else -1.0
    if arm_length is None:
        if deflection <= 0:
            raise OpInputError("--deflection must be positive")
        if input_range <= 0:
            raise OpInputError("--input-range must be positive")
        g0 = _geometry(design, servo, hinge, station, 6.0, side, horn_height, float(horn_offset), hd)
        try:
            arm_length = _solve_arm(g0["pin0"], g0["Op"], g0["a_o"], side, g0["P"], g0["ax"],
                                    deflection / input_range, g0["W"])
        except OpInputError as e:
            if getattr(e, "arm", None) is None:
                raise OpInputError(f"deflection {deflection:g} deg: the arm length did not converge; "
                                   f"give --arm-length")
            raise OpInputError(f"deflection {deflection:g} deg needs an arm of {e.arm:.2f} mm, longer than the "
                               f"distance from the servo shaft to the horn pin ({g0['W']:.2f} mm); lower --deflection, "
                               f"raise --input-range, or give --arm-length")
    g = _geometry(design, servo, hinge, station, arm_length, side, horn_height, float(horn_offset), hd)
    Op, a_o, K, n, q, H, pin0, tip0 = (g[k] for k in ("Op", "a_o", "K", "n", "q", "H", "pin0", "tip0"))
    skin_to_pin = g["s"]
    rod_length = float(np.linalg.norm(pin0 - tip0))
    raw_hinge_id = hinge
    comps, atts, mech = _elements(prefix, servo, raw_hinge_id, g["surface"], Op, a_o, tip0, pin0, K, n, q, H,
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

    def patch(old, new, key, keep_extra=False):
        nonlocal working
        if isinstance(new, dict):
            if not isinstance(old, dict) or (set(old) - set(new) and not keep_extra):
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
        if _norm({k: old.get(k) for k in element}) == _norm(element):
            return
        patch(old, element, key, keep_extra=True)
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
    follower = deflection_deg = None
    try:
        sim = simulate_mechanism(final, fm)
        mu = [s["transmission_deg"] for s in sim["steps"] if "transmission_deg" in s]
        min_mu = round(min(mu), 3) if mu else None
        at = {}
        for s_ in sim["steps"]:
            for key, want in (("plus", float(input_range)), ("minus", -float(input_range))):
                if abs(float(s_["input_deg"]) - want) < 1e-9 and raw_hinge_id in (s_.get("followers") or {}):
                    at[key] = float(s_["followers"][raw_hinge_id])
        if len(at) == 2:
            follower = {k: round(at[k], 3) + 0.0 for k in ("plus", "minus")}
            deflection_deg = round((abs(at["plus"]) + abs(at["minus"])) / 2, 2)
    except RuntimeError:
        min_mu = None
    r4 = lambda v: [round(float(t), 4) + 0.0 for t in v]
    ids_c, ids_a = [c["id"] for c in comps], [a["id"] for a in atts]
    data_out = {"components": ids_c, "attachments": ids_a, "mechanism": mech["id"], "ratio": ratio,
                "tip0": r4(tip0), "pin0": r4(pin0), "arm_pivot": r4(Op), "horn_root": r4(K), "skin_to_pin": round(skin_to_pin, 4) + 0.0,
                "rod_length": round(rod_length, 4), "arm_length": round(float(arm_length), 4) if follower else None,
                "follower_deg": follower, "deflection_deg": deflection_deg, "min_transmission_deg": min_mu,
                "rows": rows, "changed": changed}
    msgs = [f"{prefix}: ratio {ratio:g}, rod {rod_length:.2f} mm, tip {data_out['tip0']}, pin {data_out['pin0']}"
            + ("" if deflection_deg is None else f", deflection {deflection_deg:g} deg")
            + ("" if changed else "; unchanged")]
    msgs += [f"{r[0]} {r[1]}: {r[2]}" for r in rows if r[1] != "PASS"]
    return OpResult(True, data_out, msgs, changed_files=[str(plane), str(log)] if changed else [])


@op(name="design.add-linkage", summary="Generate a servo linkage: arm, rod, horn and pin components built clear of the servo (arm plane above its highest point), the horn rooted on the surface skin aft of the hinge and the pin beside the horn, their four attachments and a four_bar mechanism '<prefix>-drive', from a library servo with part frames and a hinge attachment (read from the resolved design, so a derived hinge is followed). The arm length is solved from `--deflection` (default 15 deg per side at the input range) unless `--arm-length` is given; reports the achieved deflection. Defaults are layout defaults for a 1:10 RC model, not thresholds. Idempotent: an identical re-run writes nothing; changed elements are replaced in place. One logged write; reports the ratio, arm pivot, tip, horn root, pin, rod length and the T0 FAIL, T1 FAIL (naming the new parts) and T6 rows.",
    mutates=True, render=lambda r: "\n".join(r.messages))
def add_linkage_op(path: str, *, servo: str, hinge: str, station: float, prefix: str = None, arm_length: float = None,
                   deflection: float = 15.0, horn_height: float = None, horn_offset: float = 6.0,
                   arm_side: Literal["+", "-"] = "+", horn_toward: str = "0,0,-1", input_range: float = 20.0,
                   servo_range: float = 30.0, why: str) -> OpResult:
    from ..geom import overlay
    with overlay.forced_off():       # the CAD overlay never changes what is written: same plane.yaml on every machine
        return _add_linkage(path, servo=servo, hinge=hinge, station=station, prefix=prefix, arm_length=arm_length,
                            deflection=deflection, horn_height=horn_height, horn_offset=horn_offset, arm_side=arm_side, horn_toward=horn_toward,
                            input_range=input_range, servo_range=servo_range, why=why)
