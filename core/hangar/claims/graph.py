"""Claims graph: load claims.yaml, validate, recompute every claim against the PDL, explain, import proofs/1.

Adapted from DBF-Combined redesign/proofs (build_graph.py, proofkit.py); see PROVENANCE.md.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml
from jsonschema import Draft202012Validator

from ..design import Design
from .calc import close, is_number, load_claims_standards, margin, margin_text, resolve_calc

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schema" / "claims.schema.json"
_SEG = re.compile(r"^([^\[\]]+)(?:\[([^\]]*)\])?$")


class ClaimGraphError(ValueError):
    pass


@dataclass
class ClaimResult:
    id: str
    value: object          # the number the status was judged on (recomputed when possible, else the stored one), or None
    limit: dict | None     # resolved {"op": ">=", "value": 1.6} or None
    margin: float | None
    margin_abs: bool
    status: Literal["PASS", "FAIL", "PROPOSED", "STALE"]
    message: str = ""


def _split_path(path: str) -> list[str]:
    segs, cur, depth = [], "", 0
    for ch in path:
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        if ch == "." and depth == 0:
            segs.append(cur)
            cur = ""
        else:
            cur += ch
    segs.append(cur)
    return segs


def pdl_lookup(data, path: str):
    """Resolve a PDL path ('components[battery].mass_g'). Returns (found, value); a leaf must exist and not be None."""
    cur = data
    for seg in _split_path(path):
        m = _SEG.match(seg)
        if not m:
            return False, None
        name, sel = m.group(1), m.group(2)
        if not isinstance(cur, dict) or name not in cur:
            return False, None
        cur = cur[name]
        if sel is not None:
            if not isinstance(cur, list):
                return False, None
            hit = [x for x in cur if isinstance(x, dict) and str(x.get("id")) == sel]
            if hit:
                cur = hit[0]
            elif sel.isdigit() and int(sel) < len(cur):
                cur = cur[int(sel)]
            else:
                return False, None
    return (cur is not None), cur


def claims_path(design: Design) -> Path | None:
    if design.path is None:
        return None
    p = design.path.parent / "claims.yaml"
    return p if p.is_file() else None


def _ids(v) -> list[str]:
    if v is None:
        return []
    return [v] if isinstance(v, str) else [x for x in v if isinstance(x, str)]


class ClaimGraph:
    def __init__(self, nodes, design: Design | None = None):
        self.design = design
        self.warnings: list[str] = []
        self.nodes: dict[str, dict] = {}
        for n in nodes:
            if n["id"] in self.nodes:
                raise ClaimGraphError(f"{n['id']}: duplicate id")
            self.nodes[n["id"]] = n
        self._check()

    # ---------------------------------------------------------------- load-time checks
    def _pdl(self, ref: str):
        if self.design is None or not ref.startswith("P:"):
            return False, None
        return pdl_lookup(self.design.data, ref[2:])

    def _check_ref(self, who: str, ref):
        if not isinstance(ref, str) or ref in self.nodes:
            return
        if ref.startswith("P:"):
            if self.design is None or self._pdl(ref)[0]:
                return
        raise ClaimGraphError(f"{who}: unknown reference {ref}")

    def _check(self):
        for nid, n in self.nodes.items():
            t = n["type"]
            if t == "claim":
                if "calc" in n:
                    if n["calc"] not in self.nodes or self.nodes[n["calc"]]["type"] != "calculation":
                        raise ClaimGraphError(f"{nid}: unknown reference {n['calc']}")
                if "limit" in n and "ref" in n["limit"]:
                    self._check_ref(nid, n["limit"]["ref"])
            if t == "calculation":
                for ref in n["inputs"].values():
                    self._check_ref(nid, ref)
            if t in ("claim", "calculation"):
                for ref in n.get("assumes", []):
                    self._check_ref(nid, ref)
            for ref in n.get("cites", []):
                self._check_ref(nid, ref)
            if t in ("claim", "test"):
                for ref in n.get("verifies", []):
                    self._check_ref(nid, ref)
            if t == "parameter":
                for ref in _ids(n.get("source")):
                    if ref.startswith("SRC-"):
                        self._check_ref(nid, ref)
        for nid, n in self.nodes.items():
            if n["type"] == "claim" and "calc" not in n and "value" not in n:
                raise ClaimGraphError(f"{nid}: a claim without calc needs a value")
        if self.design is not None:
            for nid, n in self.nodes.items():
                if n["type"] == "parameter" and "value" in n and self._pdl(nid)[0]:
                    raise ClaimGraphError(f"{nid}: constant shadows a PDL value")
        for nid, n in self.nodes.items():
            if n["type"] != "calculation":
                continue
            for arg, u1 in n.get("units", {}).items():
                ref = n["inputs"].get(arg)
                u2 = self.nodes.get(ref, {}).get("unit") if isinstance(ref, str) else None
                if u1 and u2 and u1 != u2:
                    raise ClaimGraphError(f"{nid}: input {arg} expects {u1} but {ref} is in {u2}")
        self._check_cycles()
        for nid, n in self.nodes.items():
            if n["type"] == "claim" and self.design is not None:
                have = {c.get("id") for c in self.design.components}
                for part in n.get("parts", []):
                    if part not in have:
                        self.warnings.append(f"{nid}: part {part} is not a component of the design")
            if n["type"] == "source" and not n.get("url"):
                self.warnings.append(f"{nid}: source has no url")

    def _check_cycles(self):
        state: dict[str, int] = {}

        def visit(cid, stack):
            if state.get(cid) == 2:
                return
            if state.get(cid) == 1:
                i = stack.index(cid)
                raise ClaimGraphError("calculation cycle: " + " -> ".join(stack[i:] + [cid]))
            state[cid] = 1
            calc = self.nodes[cid].get("calc")
            if calc:
                for ref in self.nodes[calc]["inputs"].values():
                    if isinstance(ref, str) and self.nodes.get(ref, {}).get("type") == "claim":
                        visit(ref, stack + [cid, calc])
            state[cid] = 2

        for nid, n in self.nodes.items():
            if n["type"] == "claim":
                visit(nid, [])

    # ---------------------------------------------------------------- recompute
    def recompute(self, rel_tol: float | None = None) -> list[ClaimResult]:
        if rel_tol is None:
            rel_tol = load_claims_standards()["recompute_rel_tol"]["value"]
        memo: dict[str, tuple[ClaimResult, str | None]] = {}

        def lookup(ref):
            """Return (confirmed, value) for an input or limit reference."""
            n = self.nodes.get(ref)
            if n is None:
                if self.design is None:
                    return False, None
                found, v = self._pdl(ref)
                return found, v
            t = n["type"]
            if t == "parameter":
                if "value" in n:
                    return n["value"] is not None, n["value"]
                if self.design is None:
                    return False, None
                return self._pdl(ref)
            if t == "claim":
                res, unconf = evaluate(ref)
                # confirmed only if recomputed in this run from its own calc (not stored-only, not PROPOSED)
                recomputed = "calc" in n and unconf is None and res.status in ("PASS", "FAIL", "STALE")
                return (res.value is not None and recomputed), res.value
            if t == "assumption":
                return n.get("value") is not None, n.get("value")
            return False, None

        def evaluate(cid) -> tuple[ClaimResult, str | None]:
            if cid in memo:
                return memo[cid]
            memo[cid] = (ClaimResult(cid, None, None, None, False, "PROPOSED"), "cycle")   # guard, never read
            memo[cid] = self._evaluate(cid, rel_tol, lookup)
            return memo[cid]

        return [evaluate(nid)[0] for nid, n in self.nodes.items() if n["type"] == "claim"]

    def _evaluate(self, cid, rel_tol, lookup) -> tuple[ClaimResult, str | None]:
        c = self.nodes[cid]
        unit = c.get("unit", "")
        calc = self.nodes[c["calc"]] if "calc" in c else None
        tol = rel_tol
        failed = unconfirmed = None
        if calc is None:
            now = c.get("value")
        else:
            tol = calc.get("tol", rel_tol)
            now = c.get("value")
            fn = resolve_calc(calc["function"])
            kwargs = {}
            for arg, ref in calc["inputs"].items():       # inputs first: a missing input is the more useful reason
                ok, v = lookup(ref)
                if not ok:
                    unconfirmed = f"input {ref} has no confirmed value"
                    break
                kwargs[arg] = v
            if unconfirmed is None and fn is None:
                unconfirmed = f"calc function {calc['function']!r} is not registered"
            if unconfirmed is None:
                try:
                    out = fn(**kwargs)
                    out = out if isinstance(out, dict) else {c["output"]: out}
                    if c["output"] not in out:
                        failed = f"calculation {calc['id']} has no output {c['output']!r}"
                        now = None
                    else:
                        now = out[c["output"]]
                except Exception as e:  # noqa: BLE001
                    failed = f"calculation {calc['id']} raised {type(e).__name__}: {e}"
                    now = None
        limit = None
        m = None
        mabs = False
        lim = c.get("limit")
        if lim is not None and is_number(now):
            lv = lim["value"] if "value" in lim else (lookup(lim["ref"])[1] if "ref" in lim else None)
            if is_number(lv):
                limit = {"op": lim["op"], "value": lv}
                m = margin(now, lv, lim["op"])
                mabs = lv == 0
                plain_fail = not (now >= lv if lim["op"] == ">=" else now <= lv)
                if (m < 0) != plain_fail:
                    raise ClaimGraphError(f"SELF-CHECK {cid}: margin and plain comparison disagree")
        if m is not None and m < 0:
            status, msg = "FAIL", f"margin {margin_text(m, limit['value'], unit, 1)}: {now} against {limit['op']} {limit['value']}"
        elif failed:
            status, msg = "FAIL", failed
        elif unconfirmed:
            status, msg = "PROPOSED", unconfirmed
        else:
            stored = c.get("value")
            if stored is None and calc is not None:
                stored = calc.get("outputs", {}).get(c["output"])
            if calc is not None and stored is not None and not close(stored, now, tol):
                status, msg = "STALE", f"stored {stored}, recomputes to {now}"
            elif calc is None or c.get("status") == "PROPOSED":
                status, msg = "PROPOSED", "no calculation: proposed, not verified"
            else:
                status = "PASS"
                msg = f"margin {margin_text(m, limit['value'], unit, 1)}" if m is not None else "computed, no limit"
        return ClaimResult(cid, now, limit, m, mabs, status, msg), (unconfirmed if calc is not None else None)

    # ---------------------------------------------------------------- explain
    def explain(self, claim_id: str) -> list[dict]:
        if claim_id not in self.nodes or self.nodes[claim_id]["type"] != "claim":
            raise KeyError(claim_id)
        res = {r.id: r for r in self.recompute()}
        out: list[dict] = []
        seen: set[str] = set()

        def pdl_value(ref):
            if self.design is None:
                return None
            return self._pdl(ref)[1]

        def walk(nid, depth, edge):
            n = self.nodes.get(nid)
            if n is None:
                out.append({"id": nid, "type": "parameter", "title": nid, "depth": depth, "edge": edge,
                            "value": pdl_value(nid)})
                return
            item = {"id": nid, "type": n["type"], "title": n.get("title", ""), "depth": depth, "edge": edge}
            if n["type"] == "claim":
                item["value"], item["unit"], item["status"] = res[nid].value, n.get("unit", ""), res[nid].status
            if n["type"] == "parameter":
                item["value"] = n["value"] if "value" in n else pdl_value(nid)
                item["unit"] = n.get("unit", "")
            if not out:
                item["verifies"] = list(n.get("verifies", []))
            if nid in seen:
                item["repeat"] = True
                out.append(item)
                return
            seen.add(nid)
            out.append(item)
            t = n["type"]
            if t == "claim":
                if "calc" in n:
                    walk(n["calc"], depth + 1, "derives-from")
                for a in n.get("assumes", []):
                    walk(a, depth + 1, "assumes")
                for s in n.get("cites", []):
                    walk(s, depth + 1, "cites")
            elif t == "calculation":
                for ref in n["inputs"].values():
                    walk(ref, depth + 1, "uses")
                for a in n.get("assumes", []):
                    walk(a, depth + 1, "assumes")
                for s in n.get("cites", []):
                    walk(s, depth + 1, "cites")
            elif t == "parameter":
                for s in _ids(n.get("source")):
                    if s in self.nodes:
                        walk(s, depth + 1, "cites")
            elif t in ("assumption", "requirement"):
                for s in n.get("cites", []):
                    walk(s, depth + 1, "cites")

        walk(claim_id, 0, None)
        return out

    def to_dict(self) -> dict:
        return {"schema": "claims/1", "nodes": list(self.nodes.values())}


def _schema_errors(doc) -> str:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errs = sorted(Draft202012Validator(schema).iter_errors(doc), key=lambda e: list(map(str, e.absolute_path)))[:5]
    return "; ".join(f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}" for e in errs)


def load_claims(design: Design) -> ClaimGraph:
    p = claims_path(design)
    if p is None:
        raise ClaimGraphError("no claims.yaml next to the design")
    try:
        doc = yaml.safe_load(p.read_bytes().decode("utf-8"))
    except (yaml.YAMLError, UnicodeDecodeError) as e:
        raise ClaimGraphError(f"claims.yaml does not parse: {e}") from e
    if not isinstance(doc, dict):
        raise ClaimGraphError("claims.yaml must be a mapping")
    err = _schema_errors(doc)
    if err:
        raise ClaimGraphError(err)
    return ClaimGraph(doc["nodes"], design)


def import_proofs1(paths) -> ClaimGraph:
    nodes: list[dict] = []
    for p in paths:
        p = Path(p)
        doc = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(doc, dict) or doc.get("schema") != "proofs/1":
            raise ClaimGraphError(f"{p.name}: not a proofs/1 file")
        for n in doc["nodes"]:
            n = dict(n)
            if n.get("type") == "calculation" and "script" in n:
                n["imported_from"] = {"script": n.pop("script")}
            n["defined_in"] = p.name
            nodes.append(n)
    return ClaimGraph(nodes, design=None)
