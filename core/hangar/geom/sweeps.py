"""Swept poses of the cut meshes of a generated part: where the neighbours that move are, at every pose T1 and T6 sample."""
from __future__ import annotations

import posixpath
from pathlib import Path

import numpy as np

MERGE_MM = 0.05   # poses whose transforms move no vertex of the cutter by more than this are one pocket


def swept_cut_poses(data: dict, cut_files: list[str], base_dir: Path, wing_id: str | None = None) -> list[dict]:
    """[{"file", "matrices"}] sorted by file: for each cut file whose component moves, the non-identity body-frame
    wing-frame transforms inv(wing) @ pose @ cutter placement (3 top rows of the 4x4, row-major, round 9) over the T1 configurations and the T6 mechanism poses.
    `data` is the resolved-reference design dict. A cutter that never moves yields no entry. When `wing_id` itself
    moves in some configuration the pockets would not be static: returns []."""
    from hangar.checks import _configurations
    from hangar.design import Design, load_standards
    from hangar.gates import load_gate_thresholds
    from hangar.gates.mechanisms import mechanism_pose_angles
    from hangar.geometry import pose_transforms

    by_file: dict[str, list[str]] = {}
    for c in data.get("components") or []:
        f = ((c.get("geometry") or {}).get("mesh") or {}).get("file") if isinstance(c, dict) else None
        if f:
            by_file.setdefault(posixpath.normpath(f), []).append(c["id"])
    wanted = {f: by_file[posixpath.normpath(f)] for f in cut_files if posixpath.normpath(f) in by_file}
    if not wanted:
        return []
    design = Design(data, Path(base_dir) / "plane.yaml")
    step = load_standards()["geometry"]["articulation_sweep_step_deg"]["value"]
    configs = [ang for _, ang in _configurations(design, step)]
    configs += mechanism_pose_angles(design, load_gate_thresholds()["mechanism_contact_step_deg"]["value"])
    from hangar.geometry import _transform
    eye = np.eye(4)
    comp = {c["id"]: c for c in data.get("components") or [] if isinstance(c, dict) and "id" in c}
    w_inv = np.linalg.inv(_transform(comp[wing_id])) if wing_id in comp else eye
    found: dict[str, dict[tuple, list[float]]] = {f: {} for f in wanted}
    for ang in configs:
        tf = pose_transforms(design, ang)
        if wing_id is not None and wing_id in tf and not np.allclose(tf[wing_id], eye, atol=1e-9):
            return []
        for f, cids in wanted.items():
            for cid in cids:
                t = tf[cid]
                if np.allclose(t, eye, atol=1e-9):
                    continue
                row = [round(float(x), 9) + 0.0 for x in (w_inv @ t @ _transform(comp[cid]))[:3].ravel()]
                found[f].setdefault(tuple(row), row)
    return [{"file": f, "matrices": merge_poses(list(found[f].values()), _vertices(Path(base_dir) / f))}
            for f in sorted(found) if found[f]]


def _vertices(path: Path) -> np.ndarray:
    import trimesh
    return np.asarray(trimesh.load(path, force="mesh").vertices, dtype=float)


def merge_poses(rows: list[list[float]], verts: np.ndarray, tol: float = MERGE_MM) -> list[list[float]]:
    """Drop every pose within `tol` mm (at the farthest vertex of the cutter) of one already kept. Poses are taken
    from the largest excursion down, so the extreme angles of each range are always kept."""
    def pos(r):
        t = np.array(r, dtype=float).reshape(3, 4)
        return verts @ t[:, :3].T + t[:, 3]
    pts = [pos(r) for r in rows]
    order = sorted(range(len(rows)), key=lambda i: -float(np.abs(pts[i] - verts).max()))
    kept: list[int] = []
    for i in order:
        if all(float(np.abs(pts[i] - pts[j]).max()) > tol for j in kept):
            kept.append(i)
    return [rows[i] for i in sorted(kept)]
