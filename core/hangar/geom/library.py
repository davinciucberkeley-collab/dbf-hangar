"""Real-parts library (knowledge/parts/<id>/part.yaml) and the `library_part` generator."""
from __future__ import annotations

from pathlib import Path

import yaml

from hangar.design import REPO_ROOT
from hangar.geom import registry
from hangar.geom.kernel import GeometryError
from hangar.geom.registry import Generator, ParamSpec, register

PARTS_DIR = REPO_ROOT / "knowledge" / "parts"
REQUIRED = ("id", "name", "category", "vendor", "part_number", "url", "mass_g", "dimensions_mm", "cad_status",
            "cad_source", "verified", "geometry")
CATEGORIES = ("motor", "propeller", "esc", "battery", "servo", "flight-controller", "receiver", "gps", "sensor",
              "connector", "fastener", "structure", "other")
CAD_STATUS = ("vendor-cad", "representative-envelope")


def _num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def part_errors(data: dict, folder_name: str) -> list[str]:
    errs = [f"missing key {k!r}" for k in REQUIRED if k not in data]
    if "id" in data and data["id"] != folder_name:
        errs.append(f"id {data['id']!r} must equal the folder name {folder_name!r}")
    if "category" in data and data["category"] not in CATEGORIES:
        errs.append(f"category {data['category']!r} must be one of {', '.join(CATEGORIES)}")
    if "cad_status" in data and data["cad_status"] not in CAD_STATUS:
        errs.append(f"cad_status {data['cad_status']!r} must be one of {', '.join(CAD_STATUS)}")
    if "mass_g" in data and not (_num(data["mass_g"]) and data["mass_g"] > 0):
        errs.append("mass_g must be a number > 0")
    if "dimensions_mm" in data:
        d = data["dimensions_mm"]
        if not (isinstance(d, (list, tuple)) and len(d) == 3 and all(_num(x) and x > 0 for x in d)):
            errs.append("dimensions_mm must be 3 positive numbers")
    if "url" in data and not str(data["url"]).startswith("http"):
        errs.append("url must start with http")
    if "verified" in data:
        v = data["verified"]
        for k in ("by", "date", "method"):
            if not isinstance(v, dict) or k not in v:
                errs.append(f"verified.{k} is missing")
    if "geometry" in data and not (isinstance(data["geometry"], dict) and "generator" in data["geometry"]):
        errs.append("geometry.generator is missing")
    return errs


def list_parts() -> list[str]:
    root = Path(PARTS_DIR)
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if (p / "part.yaml").is_file())


def load_part(part_id: str) -> dict:
    if part_id not in list_parts():
        raise KeyError(f"unknown library part {part_id!r}; known: {', '.join(list_parts())}")
    folder = Path(PARTS_DIR) / part_id
    data = yaml.safe_load((folder / "part.yaml").read_text(encoding="utf-8")) or {}
    errs = part_errors(data, part_id) if isinstance(data, dict) else ["part.yaml is not a mapping"]
    if errs:
        raise GeometryError(f"library part {part_id!r} is invalid: " + "; ".join(errs))
    return {**data, "_dir": folder}


def _build(p: dict, base_dir) -> list:
    from . import overlay
    part = load_part(p["part"])
    m = overlay.mesh(part["id"])
    if m is not None:
        return [m.copy()]
    return registry.build_component({"id": part["id"], "geometry": part["geometry"]}, part["_dir"])


def _files(p: dict) -> list[str]:
    from . import overlay
    return overlay.cache_files(p["part"])


def _check(p: dict) -> list[str]:
    if p["part"] not in list_parts():
        return [f"part: unknown library part {p['part']!r}; known: {', '.join(list_parts())}"]
    return []


register(Generator("library_part",
                   {"part": ParamSpec("string", required=True, doc="id of a knowledge/parts/ entry")},
                   _build, files=_files, check=_check))
