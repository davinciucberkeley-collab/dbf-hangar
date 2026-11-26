# MCP server

`plane-mcp` exposes the aircraft platform to Claude as MCP tools over stdio. Claude can list,
read, validate, measure, export and save designs as YAML without hand-editing HTML or files.
Logic lives in `core/hangar/`; the server is `core/hangar/mcp_server.py`.

## Tools

Every registry op is a tool; name = op name with `.` replaced by `_`; each returns the `OpResult` JSON as a dict; run `ops_list` to see all of them and their parameters.

- `design_list()` - every design under designs/: id, name, status and morphology.
- `design_get(path)` - the plane.yaml text, in `data.text`.
- `design_validate(path, tier)` - scorecard across the validation tiers (`tier` is `"0"` to `"9"`, which runs tiers 0 to N, or `"all"`, the default, which runs 0 to 9).
- `design_mass(path)` - total mass, CG, inertia and per-component mass.
- `design_export(path, format, out)` - write glb, stl, json, mjcf or mjcf-kinematic (joints, servo actuators, closed pushrod loop; gravity 0) to `out`; returns the written files. This is a breaking change from `export_design`: `out` is now required, and the old tool wrote to `build/` itself.
- `design_new(new_id, template)` - create a design from a template.
- `ops_list()` - every op and its parameters.

### Hand-written (until their op exists)

- `save_design(design_id, yaml_text, overwrite=False)` - schema-check then write designs/<id>/plane.yaml.
- `list_structural_parts(design_id)` - printed structural parts and whether their stored stress result is current.
- `get_schema()` - the plane.yaml JSON schema.
- `get_standards()` - design standards plus the agent standard.

## Setup

Install the MCP extra inside the repo, then register the server with Claude Code:

```
pip install -e ".[mcp]"
claude mcp add dbf-hangar -- plane-mcp
```

Run the `claude mcp add` command from the repo root.

For Claude Desktop, add this to `claude_desktop_config.json` under `mcpServers`:

```json
{
  "mcpServers": {
    "dbf-hangar": {
      "command": "C:\\Users\\<you>\\dbf-hangar\\.venv\\Scripts\\plane-mcp.exe"
    }
  }
}
```

Use the full path to plane-mcp.exe in your venv: Claude Desktop does not see your venv on PATH. Fully quit and reopen Desktop after editing. See the team guide (team-guide.md) for the Project instructions and permissions.
