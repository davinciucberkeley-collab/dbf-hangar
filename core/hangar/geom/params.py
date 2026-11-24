"""Design-level `parameters`, "$name" references and small arithmetic expressions over them (PDL 1.2)."""
from __future__ import annotations

import copy
import math
import re

_REF_PAT = r"\$([a-z][a-z0-9_]*)"
REF_PATHS = ("geometry.params", "planform", "position", "rotation_deg")   # under components[*]
ATT_REF_PATHS = ("location", "articulation.pivot")                        # under attachments[*]
MAX_EXPR_LEN = 200
_NUM_PAT = r"(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
_NAME_PAT = r"[a-z][a-z0-9_]*"


def _ref(s):
    """Parameter name when `s` is exactly "$name", else None."""
    m = re.fullmatch(_REF_PAT, s) if isinstance(s, str) else None
    return m.group(1) if m else None


class ExprError(ValueError):
    def __init__(self, kind: str, message: str):
        super().__init__(message)
        self.kind = kind


def _is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def is_expression(s) -> bool:
    return isinstance(s, str) and "$" in s


def _tokens(expr: str) -> list[tuple[str, object]]:
    if len(expr) > MAX_EXPR_LEN:
        raise ExprError("syntax", f"longer than {MAX_EXPR_LEN} characters")
    out, i = [], 0
    while i < len(expr):
        ch = expr[i]
        if ch in " \t":
            i += 1
        elif ch in "+-*/()":
            out.append((ch, ch))
            i += 1
        elif ch == "$":
            m = re.match(_NAME_PAT, expr[i + 1:])
            if not m:
                raise ExprError("syntax", f"'$' must be followed by a parameter name (at {i})")
            out.append(("name", m.group(0)))
            i += 1 + m.end()
        else:
            m = re.match(_NUM_PAT, expr[i:])
            if not m:
                raise ExprError("syntax", f"unexpected {ch!r} at {i}")
            out.append(("num", float(m.group(0))))
            i += m.end()
    return out


class _Parser:
    """expr := term (("+"|"-") term)*; term := unary (("*"|"/") unary)*; unary := "-" unary | atom."""

    def __init__(self, expr: str, params: dict | None):
        self.t, self.i, self.params, self.names = _tokens(expr), 0, params, []

    def peek(self):
        return self.t[self.i][0] if self.i < len(self.t) else None

    def run(self):
        v = self.expr()
        if self.i != len(self.t):
            raise ExprError("syntax", f"unexpected {self.t[self.i][1]!r}")
        return v

    def expr(self):
        v = self.term()
        while self.peek() in ("+", "-"):
            op = self.t[self.i][0]
            self.i += 1
            r = self.term()
            v = v + r if op == "+" else v - r
        return v

    def term(self):
        v = self.unary()
        while self.peek() in ("*", "/"):
            op = self.t[self.i][0]
            self.i += 1
            r = self.unary()
            if op == "*":
                v = v * r
            elif self.params is None:
                v = 0.0                      # parse only
            elif r == 0:
                raise ExprError("zero", "division by zero")
            else:
                v = v / r
        return v

    def unary(self):
        if self.peek() == "-":
            self.i += 1
            return -self.unary()
        return self.atom()

    def atom(self):
        k = self.peek()
        if k is None:
            raise ExprError("syntax", "unexpected end of expression")
        val = self.t[self.i][1]
        self.i += 1
        if k == "num":
            return val
        if k == "name":
            if val not in self.names:
                self.names.append(val)
            if self.params is None:
                return 0.0
            p = self.params.get(val)
            if not _is_num(p):
                raise ExprError("name", f"${val} is not a number parameter")
            return float(p)
        if k == "(":
            v = self.expr()
            if self.peek() != ")":
                raise ExprError("syntax", "missing ')'")
            self.i += 1
            return v
        raise ExprError("syntax", f"unexpected {val!r}")


def expr_names(expr: str) -> list[str]:
    """Distinct parameter names in order of first appearance. Parse only. Raises ExprError('syntax')."""
    p = _Parser(expr, None)
    p.run()
    return p.names


def evaluate(expr: str, params: dict):
    """Value of `expr` over `params`: int when whole, else float rounded to 9 places. Raises ExprError."""
    p = _Parser(expr, params if isinstance(params, dict) else {})
    v = p.run()
    if not math.isfinite(v):
        raise ExprError("range", "result is not finite")
    v = round(float(v), 9)
    return int(v) if v.is_integer() else v


def _walk(node, path: str):
    """Yield (path, parameter name): a whole-string "$name", or one entry per distinct name of an expression."""
    if isinstance(node, str):
        if _ref(node):
            yield path, _ref(node)
        elif is_expression(node):
            try:
                names = expr_names(node)
            except ExprError:
                return
            for n in names:
                yield path, n
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from _walk(v, f"{path}.{k}")
    elif isinstance(node, (list, tuple)):
        for i, v in enumerate(node):
            yield from _walk(v, f"{path}[{i}]")


def _walk_exprs(node, path: str):
    """Yield (path, string) for every string with '$' that is not a whole-string "$name"."""
    if isinstance(node, str):
        if is_expression(node) and _ref(node) is None:
            yield path, node
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from _walk_exprs(v, f"{path}.{k}")
    elif isinstance(node, (list, tuple)):
        for i, v in enumerate(node):
            yield from _walk_exprs(v, f"{path}[{i}]")


def _at(component: dict, dotted: str):
    node = component
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return None, False
        node = node[part]
    return node, True


def _owners(data):
    """(owner, dict, paths) for components, then attachments."""
    if not isinstance(data, dict):
        return
    for c in (data.get("components") or []):
        if isinstance(c, dict):
            yield str(c.get("id")), c, REF_PATHS
    for a in (data.get("attachments") or []):
        if isinstance(a, dict):
            yield f"attachments[{a.get('id')}]", a, ATT_REF_PATHS


def find_references(data: dict) -> list[tuple[str, str, str]]:
    """[(owner, dotted path, parameter name)]: owner is a component id or 'attachments[<id>]'."""
    out = []
    for owner, d, paths in _owners(data):
        for rp in paths:
            node, ok = _at(d, rp)
            if ok:
                out.extend((owner, p, n) for p, n in _walk(node, rp))
    return out


def expression_errors(data: dict) -> list[tuple[str, str, str]]:
    """(owner, path, message) for expressions with a syntax, zero-division or range error (unknown names are T0.parameters rows)."""
    out = []
    params = data.get("parameters") if isinstance(data, dict) and isinstance(data.get("parameters"), dict) else {}
    for owner, d, paths in _owners(data):
        for rp in paths:
            node, ok = _at(d, rp)
            if not ok:
                continue
            for p, s in _walk_exprs(node, rp):
                try:
                    evaluate(s, params)
                except ExprError as e:
                    if e.kind != "name":
                        out.append((owner, p, f"expression {s!r}: {e}"))
    return out


def _sub(node, params: dict):
    if isinstance(node, str):
        name = _ref(node)
        if name:
            return params[name] if _is_num(params.get(name)) else node
        if is_expression(node):
            try:
                return evaluate(node, params)
            except ExprError:
                return node
        return node
    if isinstance(node, dict):
        return {k: _sub(v, params) for k, v in node.items()}
    if isinstance(node, list):
        return [_sub(v, params) for v in node]
    return node


def resolve_references(data: dict) -> dict:
    """Deep copy of `data` with each "$name" / expression under REF_PATHS and ATT_REF_PATHS replaced by its number; `data` is not mutated."""
    out = copy.deepcopy(data)
    params = out.get("parameters") if isinstance(out.get("parameters"), dict) else {}
    for _owner, d, paths in _owners(out):
        for rp in paths:
            parent: dict = d
            parts = rp.split(".")
            for part in parts[:-1]:
                parent = parent.get(part) if isinstance(parent, dict) else None
                if not isinstance(parent, dict):
                    break
            else:
                if parts[-1] in parent:
                    parent[parts[-1]] = _sub(parent[parts[-1]], params)
    return out
