"""Aircraft design platform core: one library behind the CLI, the MCP server and the viewer."""
from __future__ import annotations

import importlib

__all__ = ["Design", "Scorecard", "load_design", "list_designs", "validate", "mass_properties"]
__version__ = "1.0.0.dev0"

# PEP 562 lazy exports: `import hangar.<x>` must not pay for checks/mass (trimesh, scipy; T124).
_EXPORTS = {
    "Design": ".design", "Scorecard": ".design", "load_design": ".design", "list_designs": ".design",
    "validate": ".checks", "mass_properties": ".mass",
}


def __getattr__(name):
    mod = _EXPORTS.get(name)
    if mod is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(importlib.import_module(mod, __name__), name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))
