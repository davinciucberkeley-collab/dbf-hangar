"""AeroSandbox adapter: probe only in v1.0."""
from __future__ import annotations

import importlib.util

from ..ops import OpResult
from . import skip_result


class AeroSandbox:
    name = "aerosandbox"
    planned = False

    def available(self) -> tuple[bool, str]:
        if importlib.util.find_spec("aerosandbox"):
            return True, "aerosandbox installed"
        return False, "aerosandbox not installed; run: python -m pip install aerosandbox"

    def run(self, design, **params) -> OpResult:
        ok, detail = self.available()
        if not ok:  # the missing tool and its fix command come first (same as every other adapter)
            return skip_result("aerosandbox", detail, "run")
        return skip_result("aerosandbox", "aerosandbox adapter has no run operation in v1.0 (probe only)", "run")
