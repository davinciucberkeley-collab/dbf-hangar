"""Byte-preserving edits of a design's plane.yaml (U1.4). Nothing here re-emits the document."""
from __future__ import annotations

import copy
import json
import math
import re
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from ruamel.yaml import YAML

from .design import SCHEMA_PATH
from .ops import OpInputError

_SEG = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*)((?:\[[^\[\]]+\])*)$")
_SEL = re.compile(r"\[([^\[\]]+)\]")
# the text of one scalar value: a "..." string, a '...' string, or a plain scalar up to , ] } # or end of line
_TOKEN = re.compile(r"\"(?:[^\"\\\r\n]|\\.)*\"|'(?:[^'\r\n]|'')*'|[^\s,\[\]{}#\"'][^,\[\]{}#\r\n]*?(?=[ \t]*(?:[,\]}\r\n]|#|$))")


def resolve_design_path(path) -> Path:
    """The one place a design path is normalised: backslashes become slashes; a folder means its plane.yaml."""
    p = Path(str(path).replace("\\", "/"))
    return p / "plane.yaml" if p.is_dir() else p


def parse_key(key: str) -> list[tuple[str, object]]:
    steps: list[tuple[str, object]] = []
    for seg in re.split(r"\.(?![^\[]*\])", key):
        m = _SEG.match(seg)
        if not m:
            raise OpInputError(f"bad key {key!r}: segment {seg!r} must look like name, name[id] or name[0]")
        steps.append(("key", m.group(1)))
        for sel in _SEL.findall(m.group(2)):
            steps.append(("index", int(sel)) if sel.isdigit() else ("id", sel))
    return steps


def _child(node, step, key):
    kind, v = step
    if kind == "key":
        if not isinstance(node, dict) or v not in node:
            have = sorted(map(str, node)) if isinstance(node, dict) else type(node).__name__
            raise OpInputError(f"{key}: no key {v!r} (have: {have})")
        return node[v], "value", v
    if not isinstance(node, list):
        raise OpInputError(f"{key}: [{v}] needs a list")
    if kind == "index":
        if v >= len(node):
            raise OpInputError(f"{key}: index {v} out of range (length {len(node)})")
        return node[v], "item", v
    for i, item in enumerate(node):
        if isinstance(item, dict) and str(item.get("id")) == v:
            return item, "item", i
    ids = [str(x.get("id")) for x in node if isinstance(x, dict) and "id" in x]
    raise OpInputError(f"{key}: no element with id {v!r} (have: {ids})")


def walk(root, key: str):
    """Return (value, parent, how, ref) for the last step of `key`; raise OpInputError if any step is missing."""
    node, parent, how, ref = root, None, None, None
    for step in parse_key(key):
        parent = node
        node, how, ref = _child(node, step, key)
    return node, parent, how, ref


def get_value(data, key: str):
    return walk(data, key)[0]


def assign(data, key: str, new) -> None:
    _, parent, _how, ref = walk(data, key)
    parent[ref] = new


def parse_scalar(raw: str):
    try:
        v = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        raise OpInputError(f"cannot read value {raw!r}: {e}") from e
    if isinstance(v, (dict, list)):
        raise OpInputError(f"value {raw!r} is a mapping or list; give one scalar (number, text, true/false, null)")
    return v


def render_scalar(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if not math.isfinite(v):
            raise OpInputError("value must be finite")
        return repr(v)
    if isinstance(v, str):
        if re.fullmatch(r"[A-Za-z0-9_./-]+", v) and yaml.safe_load(v) == v:
            return v
        return json.dumps(v, ensure_ascii=False)
    raise OpInputError(f"unsupported value type {type(v).__name__}")


def patch_text(text: str, key: str, new) -> str:
    """Return `text` with only the one scalar at `key` replaced. Raises OpInputError rather than rewrite anything else."""
    root = YAML().load(text)          # used only to locate the value; never dumped
    old, parent, how, ref = walk(root, key)
    if isinstance(old, (dict, list)):
        raise OpInputError(f"{key}: points at a mapping or list; name one scalar value")
    line, col = parent.lc.value(ref) if how == "value" else parent.lc.item(ref)
    starts = [0] + [m.end() for m in re.finditer("\n", text)]
    pos = starts[line] + col
    m = _TOKEN.match(text, pos)
    if not m:
        raise OpInputError(f"{key}: cannot find the value's text in the file")
    patched = text[:pos] + render_scalar(new) + text[m.end():]
    expected = copy.deepcopy(yaml.safe_load(text))
    assign(expected, key, new)
    if yaml.safe_load(patched) != expected:
        raise OpInputError(f"{key}: cannot change this value without rewriting other text; edit the file by hand")
    return patched


def _errors(data) -> dict:
    v = Draft202012Validator(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
    return {(tuple(map(str, e.absolute_path)), e.message): e for e in v.iter_errors(data)}


def check_schema(before, after, key: str) -> None:
    """Raise OpInputError for schema errors that `after` has and `before` did not."""
    old = _errors(before)
    fresh = [e for k, e in _errors(after).items() if k not in old]
    if not fresh:
        return
    parts = []
    for e in fresh:
        s = f"{key}: {e.message} (data path {'/'.join(map(str, e.absolute_path))}; schema path {'/'.join(map(str, e.absolute_schema_path))}"
        if e.validator == "type":
            s += f"; allowed type {e.validator_value}"
        parts.append(s + ")")
    raise OpInputError("; ".join(parts))


def flatten(node, prefix: str = "") -> dict:
    """Leaf values keyed like design.set keys: components[battery].mass_g, components[x].position[0]."""
    out: dict = {}
    if isinstance(node, dict):
        for k, v in node.items():
            out.update(flatten(v, f"{prefix}.{k}" if prefix else str(k)))
        if not node and prefix:
            out[prefix] = {}
    elif isinstance(node, list):
        for i, v in enumerate(node):
            sel = str(v["id"]) if isinstance(v, dict) and "id" in v else str(i)
            out.update(flatten(v, f"{prefix}[{sel}]"))
        if not node and prefix:
            out[prefix] = []
    else:
        out[prefix] = node
    return out
