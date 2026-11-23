"""Byte-preserving edits of a design's plane.yaml (U1.4). Nothing here re-emits the document."""
from __future__ import annotations

import copy
import difflib
import json
import math
import re
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from ruamel.yaml import YAML

from . import yamlio
from .design import SCHEMA_PATH
from .ops import OpInputError

_SEG = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*)((?:\[[^\[\]]+\])*)$")
_SEL = re.compile(r"\[([^\[\]]+)\]")
# the text of one scalar value: a "..." string, a '...' string, or a plain scalar up to , ] } # or end of line
_TOKEN = re.compile(r"\"(?:[^\"\\\r\n]|\\.)*\"|'(?:[^'\r\n]|'')*'|[^\s,\[\]{}#\"'][^,\[\]{}#\r\n]*?(?=[ \t]*(?:[,\]}\r\n]|#|$))")


# in a block mapping or list a plain scalar runs to the end of the line (before " #"); commas and brackets are text there
_PLAIN_EOL = re.compile(r"[^\s,\[\]{}#\"'|>&*!%@`][^\r\n]*?(?=[ \t]+#|[ \t]*(?:\r|\n|\Z))")
_BLOCK_HEAD = re.compile(r"[|>][+-]?[0-9]?[ \t]*(?:#[^\r\n]*)?(?=\r|\n|\Z)")
_SPACES = re.compile(" *")


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


def parse_set_value(raw: str):
    """Value for design.set --kind modify/subtract: a plain text containing ': ' (or ending in ':') is the string itself, not a YAML mapping (T58); everything else as parse_scalar."""
    s = raw.strip()
    if (": " in s or s.endswith(":")) and s[:1] not in ("[", "{", '"', "'"):
        return s
    return parse_scalar(raw)


def _no_empty(v, raw: str) -> None:
    if isinstance(v, (list, dict)):
        if not v:
            raise OpInputError(f"value {raw!r}: empty list or mapping not allowed")
        for x in (v.values() if isinstance(v, dict) else v):
            _no_empty(x, raw)


def parse_value(raw: str):
    """Scalar as parse_scalar does; or, when raw.strip() starts with '[' and ends with ']' (or '{' ... '}'), the parsed list or mapping."""
    s = raw.strip()
    if (s.startswith("[") and s.endswith("]")) or (s.startswith("{") and s.endswith("}")):
        try:
            v = yaml.safe_load(s)
        except yaml.YAMLError as e:
            raise OpInputError(f"cannot read value {raw!r}: {e}") from e
        if not isinstance(v, (list, dict)):
            raise OpInputError(f"cannot read value {raw!r}: not a list or mapping")
        _no_empty(v, raw)
        return v
    return parse_scalar(raw)


_KEY = re.compile(r"[A-Za-z_][A-Za-z0-9_-]*")


def render_flow(v) -> str:
    """One-line YAML flow text for a scalar, list or mapping; scalars via render_scalar."""
    if isinstance(v, list):
        return "[" + ", ".join(render_flow(x) for x in v) + "]"
    if isinstance(v, dict):
        parts = []
        for k, x in v.items():
            if not isinstance(k, str) or not _KEY.fullmatch(k):
                raise OpInputError(f"unsupported mapping key {k!r}")
            parts.append(f"{k}: {render_flow(x)}")
        return "{" + ", ".join(parts) + "}"
    return render_scalar(v)


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
    in_flow = bool(getattr(parent, "fa", None) and parent.fa.flow_style())
    if not in_flow and _BLOCK_HEAD.match(text, pos):
        end = _block_scalar_end(text, starts, line)      # a | or > text block: header and body lines become one quoted line
    else:
        m = _TOKEN.match(text, pos)
        if m and not in_flow and m.group()[0] not in "\"'":
            m = _PLAIN_EOL.match(text, pos)              # block context: the plain scalar runs to the end of the line
        if not m:
            raise OpInputError(f"{key}: cannot find the value's text in the file")
        end = m.end()
    patched = text[:pos] + render_scalar(new) + text[end:]
    expected = copy.deepcopy(yaml.safe_load(text))
    assign(expected, key, new)
    try:
        same = yaml.safe_load(patched) == expected
    except yaml.YAMLError:
        same = False
    if not same:
        raise OpInputError(f"{key}: cannot change this value without rewriting other text; edit the file by hand")
    return patched


def _block_scalar_end(text: str, starts: list[int], line: int) -> int:
    """Offset of the end (before its newline) of the last body line of the | or > text block whose header is on `line`."""
    indent = _SPACES.match(text, starts[line]).end() - starts[line]
    last = line
    for i in range(line + 1, len(starts)):
        s = starts[i]
        e = starts[i + 1] if i + 1 < len(starts) else len(text)
        if not text[s:e].strip():
            continue                                    # a blank line belongs to the block only if a body line follows
        if _SPACES.match(text, s).end() - s <= indent:
            break
        last = i
    end = starts[last + 1] if last + 1 < len(starts) else len(text)
    while end > 0 and text[end - 1] in "\r\n":
        end -= 1
    return end


def exists(data, key: str) -> bool:
    """True when every step of `key` resolves in `data` (uses walk; False on OpInputError)."""
    try:
        walk(data, key)
    except OpInputError:
        return False
    return True


def _create(root, key: str, new, mk_map, mk_list):
    """Walk `key` from `root`, creating what is missing; return the mapping that received the final key."""
    steps = parse_key(key)
    node = root
    for i, step in enumerate(steps):
        kind, v = step
        last = i == len(steps) - 1
        nxt = None if last else steps[i + 1]
        if kind == "key":
            if not isinstance(node, dict):
                raise OpInputError(f"{key}: {v!r} needs a mapping")
            if v in node:
                if last:
                    raise OpInputError(f"{key}: already set; use --kind modify")
            elif last:
                node[v] = new
                return node
            elif nxt[0] == "id":
                node[v] = mk_list()
            elif nxt[0] == "key":
                node[v] = mk_map()
            else:
                raise OpInputError(f"{key}: no key {v!r}; cannot add a list element by index")
            node = node[v]
        elif kind == "index" or any(isinstance(x, dict) and str(x.get("id")) == v for x in (node if isinstance(node, list) else [])):
            child = _child(node, step, key)[0]      # an out-of-range index raises here
            if last:
                raise OpInputError(f"{key}: already set; use --kind modify")
            node = child
        else:
            if not isinstance(node, list):
                raise OpInputError(f"{key}: [{v}] needs a list")
            if last:
                raise OpInputError(f"{key}: name a scalar value, not a list element")
            item = mk_map()
            item["id"] = v
            node.append(item)
            node = item
    raise OpInputError(f"{key}: nothing to add")


def _locate(root, key: str):
    """Deepest existing node on `key`'s path and the steps still to create (key already passed _create)."""
    steps = parse_key(key)
    node = root
    for i, step in enumerate(steps):
        kind, v = step
        if kind == "key":
            if v not in node:
                return node, steps[i:]
        elif kind == "index":
            pass
        elif not any(isinstance(x, dict) and str(x.get("id")) == v for x in node):
            return node, steps[i:]
        node = _child(node, step, key)[0]
    raise OpInputError(f"{key}: nothing to add")


def _emit(rest, indent: int, new, key: str) -> list[str]:
    """Block-YAML lines that create the chain `rest` (key / id steps) at `indent`, in the repo's layout."""
    sp = " " * indent
    kind, v = rest[0]
    if kind != "key":
        raise OpInputError(f"{key}: cannot add this value without rewriting other text; edit the file by hand")
    if len(rest) == 1:
        return [f"{sp}{v}: {render_flow(new)}"]
    if rest[1][0] == "key":
        return [f"{sp}{v}:"] + _emit(rest[1:], indent + 2, new, key)
    if rest[1][0] == "id" and len(rest) > 2 and rest[2][0] == "key":
        out = _emit(rest[2:], indent + 4, new, key)
        return [f"{sp}{v}:", f"{sp}  - id: {render_scalar(rest[1][1])}"] + out
    raise OpInputError(f"{key}: cannot add this value without rewriting other text; edit the file by hand")


def _nest(rest, new):
    if any(kind != "key" for kind, _ in rest):
        raise OpInputError("cannot add this value without rewriting other text; edit the file by hand")
    return new if not rest else {rest[0][1]: _nest(rest[1:], new)}


def _block_end(lines: list[str], start: int, ind: int, same_indent_dash: bool) -> int:
    """Index of the last content line of the block whose last entry starts at `start`."""
    end = start
    for j in range(start + 1, len(lines)):
        line = lines[j]
        body = line.lstrip()
        if not body or body.startswith("#"):
            continue
        n = len(line) - len(body)
        if n > ind or (same_indent_dash and n == ind and body.startswith("- ")):
            end = j
        else:
            break
    return end


def _close_brace(line: str, col: int) -> int:
    depth, i, q = 0, col, None
    while i < len(line):
        c = line[i]
        if q:
            if q == '"' and c == "\\":
                i += 1
            elif c == q:
                q = None
        elif c in "\"'":
            q = c
        elif c in "{[":
            depth += 1
        elif c in "}]":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def add_value(text: str, key: str, new) -> str:
    """Return the patched text: create what `key` needs and set the last step to the scalar `new`.

    The new lines are spliced into the original text (comments and layout stay); the file is never re-emitted.
    """
    crlf = "\r\n" in text
    t = text.replace("\r\n", "\n")
    expected = copy.deepcopy(yaml.safe_load(t))
    _create(expected, key, new, dict, list)      # raises the input errors; also the reference result
    node, rest = _locate(yamlio.load(t), key)
    lines = t.split("\n")
    hand = f"{key}: cannot add this value without rewriting other text; edit the file by hand"
    flow_line = None
    if isinstance(node, dict) and node.fa.flow_style():
        line_no, col = node.lc.line, node.lc.col
        end = _close_brace(lines[line_no], col) if lines[line_no][col:col + 1] == "{" else -1
        if end < 0 or any(kind != "key" for kind, _ in rest):
            raise OpInputError(hand)
        value_text = render_flow(_nest(rest[1:], new))
        head = lines[line_no][:end].rstrip()
        sep = "" if head.endswith("{") else ","
        lines[line_no] = f"{head}{sep} {rest[0][1]}: {value_text}{lines[line_no][end:]}"
        flow_line = line_no
    elif isinstance(node, dict):
        first = next(iter(node), None)
        if first is None:
            raise OpInputError(hand)
        ind = node.lc.key(first)[1]
        last_key = list(node)[-1]
        at = _block_end(lines, node.lc.key(last_key)[0], ind, True)
        lines[at + 1:at + 1] = _emit(rest, ind, new, key)
    else:
        if not node or node.fa.flow_style() or len(rest) < 2 or rest[0][0] != "id" or rest[1][0] != "key":
            raise OpInputError(hand)
        start = node.lc.item(len(node) - 1)[0]
        dash = len(lines[start]) - len(lines[start].lstrip())
        if not lines[start].lstrip().startswith("- "):
            raise OpInputError(hand)
        at = _block_end(lines, start, dash, False)
        body = _emit(rest[1:], dash + 2, new, key)
        body[0] = " " * dash + "- id: " + render_scalar(rest[0][1]) + "\n" + body[0]
        lines[at + 1:at + 1] = "\n".join(body).split("\n")
    out = "\n".join(lines)
    if yaml.safe_load(out) != expected:
        raise OpInputError(hand)
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, t.splitlines(), out.splitlines(), autojunk=False).get_opcodes():
        if tag in ("equal", "insert"):
            continue
        if tag == "replace" and i2 - i1 == 1 and j2 - j1 == 1 and i1 == flow_line:
            continue
        raise OpInputError(f"{key}: adding would rewrite other lines; edit the file by hand")
    return out.replace("\n", "\r\n") if crlf else out


def remove_element(text: str, key: str) -> tuple[str, object]:
    """Return (patched text, removed element): `key` is `name[id]`; exactly that element's lines are deleted.

    Deleted: the element's own lines (one line for a one-line flow entry `- {...}`; for a block entry its dash line
    through its last more-indented line) and the directly preceding comment lines that belong to it. Nothing is re-emitted.
    """
    crlf = "\r\n" in text
    t = text.replace("\r\n", "\n")
    hand = f"{key}: cannot remove this element without rewriting other text; edit the file by hand"
    steps = parse_key(key)
    if steps[-1][0] == "index":
        raise OpInputError(f"{key}: remove by index is not supported; address the element by id, like name[id]")
    if len(steps) > 2:
        raise OpInputError(f"{key}: remove takes a top-level list element name[id]; a nested path (one field, or a list below an element) is not supported")
    if len(steps) != 2 or steps[1][0] != "id":
        raise OpInputError(f"{key}: remove needs a list element like name[id]; this is not one")
    data = yaml.safe_load(t)
    element = walk(data, key)[0]                 # raises the "no key", "needs a list" and "no element with id" errors
    expected = copy.deepcopy(data)
    _, exp_list, _, exp_i = walk(expected, key)
    del exp_list[exp_i]                          # the reference result for Verify 1
    _, seq, _, i = walk(yamlio.load(t), key)
    if seq.fa.flow_style():
        raise OpInputError(hand)
    lines = t.split("\n")
    start, col = seq.lc.item(i)
    body = lines[start].lstrip()
    if not body.startswith("- "):
        raise OpInputError(hand)
    if seq[i].fa.flow_style():
        close = _close_brace(lines[start], col) if lines[start][col:col + 1] == "{" else -1
        rest = lines[start][close + 1:].strip() if close >= 0 else "?"
        if rest and not rest.startswith("#"):
            raise OpInputError(hand)             # a multi-line flow entry, or text after the closing brace
        last = start
    else:
        last = _block_end(lines, start, len(lines[start]) - len(body), False)
    first = start
    mine = re.compile(r"#\s*" + re.escape(str(steps[1][1])) + r"(?![A-Za-z0-9_-])")
    j = start - 1
    while j >= 0 and lines[j].lstrip().startswith("#"):
        if mine.match(lines[j].lstrip()):
            first = j                            # the topmost comment line that begins with the id
        j -= 1
    out = "\n".join(lines[:first] + lines[last + 1:])
    if yaml.safe_load(out) != expected:
        raise OpInputError(hand)
    for tag, *_ in difflib.SequenceMatcher(None, t.splitlines(), out.splitlines(), autojunk=False).get_opcodes():
        if tag not in ("equal", "delete"):
            raise OpInputError(f"{key}: removing would rewrite other lines; edit the file by hand")
    return (out.replace("\n", "\r\n") if crlf else out), element


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
