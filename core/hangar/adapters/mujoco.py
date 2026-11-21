"""MuJoCo adapter. This module is named like the library; it imports it with an absolute `import mujoco`."""
from __future__ import annotations

from .. import fea
from ..ops import OpResult
from . import skip_result


class MuJoCo:
    name = "mujoco"
    planned = False

    def available(self) -> tuple[bool, str]:
        try:
            import mujoco
            return True, f"mujoco {mujoco.__version__}"
        except Exception as e:  # noqa: BLE001 - ImportError or a broken native library
            return False, f"mujoco import failed ({type(e).__name__}: {e}); run: python -m pip install 'mujoco>=3'"

    def run(self, design, **params) -> OpResult:
        ok, detail = self.available()
        if not ok:
            return skip_result("mujoco", detail, "joint_loads")
        return OpResult(True, {"joint_loads": fea.joint_loads(design)}, ["mujoco: joint load cases"])
