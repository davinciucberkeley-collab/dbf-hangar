"""Blender adapter: planned stub."""
from __future__ import annotations

from ..ops import OpResult
from . import skip_result

_TEXT = "planned, not implemented in v1.0 (optional collision/transport check, will use Blender 4.5); nothing to run yet"


class Blender:
    name = "blender"
    planned = True

    def available(self) -> tuple[bool, str]:
        return False, _TEXT

    def run(self, design, **params) -> OpResult:
        return skip_result("blender", _TEXT, "run")
