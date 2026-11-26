"""Lazy module proxy: `from hangar._lazy import trimesh` imports trimesh on first attribute access (start-up cost, T124)."""
from __future__ import annotations

import importlib


# Note: tests that monkeypatch trimesh must patch the real module (import trimesh; monkeypatch.setattr(trimesh, ...)),
# not this proxy: setattr on the proxy would not reach the real module.
class LazyModule:
    def __init__(self, name: str):
        self.__dict__["_name"] = name
        self.__dict__["_mod"] = None

    def _load(self):
        mod = self.__dict__["_mod"]
        if mod is None:
            mod = importlib.import_module(self.__dict__["_name"])
            self.__dict__["_mod"] = mod
        return mod

    def __getattr__(self, attr):
        return getattr(self._load(), attr)

    def __dir__(self):
        return dir(self._load())


trimesh = LazyModule("trimesh")
