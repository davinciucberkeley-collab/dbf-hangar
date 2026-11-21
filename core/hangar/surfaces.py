"""Public parameter names for the MCP and Studio surfaces (same rule as the CLI: drop one trailing underscore)."""
from __future__ import annotations


def public_name(param) -> str:
    return param.name[:-1] if param.name.endswith("_") else param.name


def map_params(spec, raw: dict) -> dict:
    """Public-name keys -> ParamSpec.name keys. Unknown keys pass through so call() reports them."""
    back = {public_name(p): p.name for p in spec.params}
    return {back.get(k, k): v for k, v in raw.items()}
