"""Real-parts library (knowledge/parts/<id>/part.yaml) and the `library_part` generator."""
from __future__ import annotations

import re
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
    errs += _frames_errors(data)
    errs += _ports_errors(data)
    return errs


def _ports_errors(data: dict) -> list[str]:
    """U16.1 S8: optional `ports` (name -> point, direction) and `ports_source`, required together with ports."""
    if "ports" not in data:
        return []
    errs = []
    if not (isinstance(data.get("ports_source"), str) and data["ports_source"].strip()):
        errs.append("ports_source is required with ports")
    ports = data["ports"]
    if not isinstance(ports, dict):
        return errs + ["ports must be a mapping of port name to point and direction"]
    for name, p in ports.items():
        if not (isinstance(name, str) and re.fullmatch(r"[a-z0-9][a-z0-9_]*", name)):
            errs.append(f"ports: port name {name} is not a slug")
        p = p if isinstance(p, dict) else {}
        if not _vec3(p.get("point")):
            errs.append(f"ports.{name}.point must be 3 numbers")
        if not (_vec3(p.get("direction")) and any(x != 0 for x in p["direction"])):
            errs.append(f"ports.{name}.direction must be 3 numbers, not all zero")
    return errs


def _vec3(v) -> bool:
    return isinstance(v, (list, tuple)) and len(v) == 3 and all(_num(x) for x in v)


def _axis_aligned(v) -> bool:
    return _vec3(v) and sum(1 for x in v if x != 0) == 1


def _frames_errors(data: dict) -> list[str]:
    """U16.1 S3: optional `frames` (output, mount_face) and `frames_source`, servos only, required together."""
    errs = []
    has_f, has_s = "frames" in data, "frames_source" in data
    if has_f and data.get("category") != "servo":
        errs.append("frames is allowed only for category: servo")
    if has_f and not has_s:
        errs.append("frames needs frames_source (where the numbers come from; \"estimate\" is allowed)")
    if has_s and not has_f:
        errs.append("frames_source needs frames")
    if has_s and not (isinstance(data["frames_source"], str) and data["frames_source"].strip()):
        errs.append("frames_source must be a non-empty string")
    if has_f:
        f = data["frames"]
        if not isinstance(f, dict):
            return errs + ["frames must be a mapping with output and mount_face"]
        for name, direction in (("output", "axis"), ("mount_face", "normal")):
            fr = f.get(name)
            if not isinstance(fr, dict):
                errs.append(f"frames.{name} is missing")
                continue
            if not _vec3(fr.get("point")):
                errs.append(f"frames.{name}.point must be 3 numbers")
            if not _axis_aligned(fr.get(direction)):
                errs.append(f"frames.{name}.{direction} must be 3 numbers with exactly one non-zero component")
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
