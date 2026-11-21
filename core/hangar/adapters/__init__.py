"""Tool adapters: one contract for external tools (U2.3). A missing tool is a SKIP with its fix command, never a PASS."""
from __future__ import annotations
import importlib
from typing import Protocol, runtime_checkable
from ..ops import OpResult

ADAPTER_NAMES = ("opencae", "mujoco", "aerosandbox", "blender", "sitl", "davinci")
_MODULES = {"opencae": ("opencae", "OpenCAE"), "mujoco": ("mujoco", "MuJoCo"), "aerosandbox": ("aerosandbox", "AeroSandbox"),
            "blender": ("blender", "Blender"), "sitl": ("sitl", "Sitl"), "davinci": ("davinci", "DaVinci")}


@runtime_checkable
class Adapter(Protocol):
    name: str
    planned: bool
    def available(self) -> tuple[bool, str]: ...   # (True, what was found) | (False, reason + "; run: <fix command>")
    def run(self, design, **params) -> OpResult: ...


def skip_result(adapter: str, detail: str, what: str = "") -> OpResult:
    """The one way an adapter reports a tool it cannot use: ok, but skipped, with the reason and fix command first."""
    return OpResult(ok=True, data={"status": "SKIP", "adapter": adapter, "what": what}, messages=[detail], skipped=[what or adapter])


def get_adapter(name: str) -> Adapter:
    if name not in _MODULES:
        raise KeyError(f"unknown adapter {name!r}; known: {', '.join(ADAPTER_NAMES)}")
    mod, cls = _MODULES[name]
    return getattr(importlib.import_module(f"{__name__}.{mod}"), cls)()
