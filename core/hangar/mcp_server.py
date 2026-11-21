"""MCP server: one tool per registry op (name = op name with '.' -> '_'), plus a few hand-written tools whose ops do not exist yet (see docs/mcp.md).

Run over stdio with the `plane-mcp` entry point. Thin wrapper: all logic lives in the ops registry
(hangar.ops) and the modules it calls.
"""
from __future__ import annotations

import inspect
import json
import re
from pathlib import Path
from typing import Callable, Literal

import yaml
try:  # mcp >= 2
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP

from .checks import validate
from .design import Design, DESIGNS_DIR, REPO_ROOT, SCHEMA_PATH, STANDARDS_PATH, load_design
from .ops import registry, _call_spec
from .surfaces import map_params, public_name

mcp = FastMCP("dbf-hangar")

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def _design_path(design_id: str, must_exist: bool = True) -> Path:
    if not isinstance(design_id, str) or not _ID_RE.match(design_id):
        raise ValueError(f"invalid design id {design_id!r}: use lowercase letters, digits, '-' and '_' "
                         "and start with a letter or digit")
    path = DESIGNS_DIR / design_id / "plane.yaml"
    if must_exist and not path.is_file():
        raise ValueError(f"no design '{design_id}': {path} does not exist (see list_designs)")
    return path


_PY_TYPES = {"str": str, "path": str, "bool": bool, "int": int, "float": float}
GENERATED: dict[str, Callable] = {}


def _annotation(p):
    if p.type_name == "choice":
        return Literal[p.choices]
    if p.type_name == "list[str]":
        return list[str]
    return _PY_TYPES[p.type_name]


def _make_tool(spec):
    """One MCP tool for one op: same params, same OpResult dict as hangar.ops.call()."""
    def tool(**kwargs) -> dict:
        given = {k: v for k, v in kwargs.items() if v is not None}
        return json.loads(_call_spec(spec, **map_params(spec, given)).to_json())

    params = [inspect.Parameter(
        public_name(p), inspect.Parameter.KEYWORD_ONLY, annotation=_annotation(p),
        default=inspect.Parameter.empty if p.required else (str(p.default) if isinstance(p.default, Path) else p.default))
        for p in spec.params]
    tool.__signature__ = inspect.Signature(params, return_annotation=dict)
    tool.__annotations__ = {**{public_name(p): _annotation(p) for p in spec.params}, "return": dict}
    tool.__name__ = spec.name.replace(".", "_")
    return tool


for _spec in registry().values():
    _tool = _make_tool(_spec)
    GENERATED[_tool.__name__] = _tool
    mcp.add_tool(_tool, name=_tool.__name__, description=_spec.summary + (" Writes files." if _spec.mutates else ""))


@mcp.tool()
def save_design(design_id: str, yaml_text: str, overwrite: bool = False) -> dict:
    """Validate new plane.yaml text and save it as designs/<id>/plane.yaml.

    Use this to create or update a design from YAML you have written. The YAML's 'id' must equal
    design_id. The schema check (tier 0) runs before anything is written; if it fails, nothing is
    saved and the scorecard explains why. Set overwrite=true to replace an existing design.
    Returns {"saved": bool, "path": ..., "scorecard": ...}.
    """
    path = _design_path(design_id, must_exist=False)
    try:
        data = yaml.safe_load(yaml_text)
    except yaml.YAMLError as e:
        raise ValueError(f"yaml_text is not valid YAML: {e}") from e
    if not isinstance(data, dict):
        raise ValueError("yaml_text: top level must be a mapping")
    if data.get("id") != design_id:
        raise ValueError(f"yaml 'id' is {data.get('id')!r} but design_id is {design_id!r}")

    precheck = validate(Design(data=data, path=path), max_tier=0)
    if not precheck.clean:
        return {"saved": False, "scorecard": precheck.to_dict()}
    if path.exists() and not overwrite:
        raise ValueError(f"design '{design_id}' already exists; pass overwrite=true to replace it")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml_text)
    return {"saved": True, "path": str(path),
            "scorecard": validate(load_design(path)).to_dict()}


@mcp.tool()
def get_schema() -> dict:
    """Return the JSON schema that every plane.yaml must match.

    Use this before writing a new design from scratch so the YAML passes tier 0.
    """
    return json.loads(SCHEMA_PATH.read_text())


@mcp.tool()
def get_standards() -> str:
    """Return the design standards (standards/design-standards.yaml) followed by the agent
    standard (standards/agents.md), separated by a line '---'.

    Use this to learn the numeric limits and the rules the validators enforce.
    """
    agents = (REPO_ROOT / "standards" / "agents.md").read_text()
    return STANDARDS_PATH.read_text() + "\n---\n" + agents


@mcp.tool()
def structural_check(design_id: str, part_id: str = "", all_printed: bool = False) -> dict:
    """Run a finite-element stress check of printed parts in OpenCAE Studio (CalculiX) and return the verdicts.

    part_id: one component id (see list_structural_parts); or all_printed=True for every printed structural part.
    The load cases come from the design itself (joint forces and moments from the tier-2 drop test, and from hover
    at full thrust held at the root), times the ultimate factor; supports are the joints leading toward the root. A part passes when its peak
    von Mises stress away from the clamps is within structure.fea_allowable_printed_petg_mpa.
    Results are saved in designs/<id>/fea/<part>.json and appear in validate_design (tier 2, T2.fea_strength).
    Slow: seconds to a few minutes per part. Needs OpenCAE set up once (plane fea --setup).
    """
    from . import fea
    design = load_design(_design_path(design_id))
    parts = fea.eligible_parts(design) if all_printed else [part_id]
    if not parts or not parts[0]:
        raise ValueError("give part_id, or all_printed=True")
    oc = fea.find_opencae()
    if not oc["found"]:
        raise RuntimeError("OpenCAE is not set up on this computer: run `plane fea --setup --opencae-python <python> "
                           "--opencae-root <OpenCAE folder>` once")
    drop = fea.joint_loads(design)
    out = []
    for pid in parts:
        try:
            r = fea.run(design, pid, oc, drop=drop, log=lambda m: None)
            out.append({"part": pid, "status": r["status"], "error": r["error"], "notes": r["notes"],
                        "cases": [{k: c.get(k) for k in ("name", "status", "max_von_mises_away_mpa", "max_von_mises_mpa",
                                                         "safety_factor_at_ultimate", "max_displacement_mm", "message")}
                                  for c in r["cases"]]})
        except Exception as e:  # noqa: BLE001 - one bad part must not hide the others
            out.append({"part": pid, "status": "ERROR", "error": f"{type(e).__name__}: {e}"})
    return {"design": design_id, "allowable_mpa_key": "structure.fea_allowable_printed_petg_mpa", "results": out}


@mcp.tool()
def list_structural_parts(design_id: str) -> list[dict]:
    """Printed structural parts that structural_check can analyse, with their stored result (if any)."""
    from . import fea
    design = load_design(_design_path(design_id))
    rows = []
    for pid in fea.eligible_parts(design):
        f = fea.result_path(design, pid)
        rec = json.loads(f.read_text()) if f.exists() else None
        rows.append({"part": pid, "description": design.component(pid).get("description", ""),
                     "result": None if rec is None else rec.get("status"),
                     "up_to_date": bool(rec) and rec.get("hash") == fea.part_hash(design, pid)})
    return rows


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
