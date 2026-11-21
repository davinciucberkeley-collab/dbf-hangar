from __future__ import annotations
import json, shutil, struct
from pathlib import Path
import pytest, trimesh
from hangar.export import export_glb
from hangar.design import load_design
from hangar.ops import call

REPO = Path(__file__).resolve().parents[1]
ASSEMBLY = ("\nassembly:\n  sequence:\n    - {step: 2, add: [wing, motor_l]}\n    - {step: 1, add: [center_body]}\n")


def _doc(path):
    glb = Path(path).read_bytes()
    jlen = struct.unpack("<I4s", glb[12:20])[0]
    return json.loads(glb[20:20 + jlen]), glb


@pytest.fixture
def design(tmp_path):
    shutil.copytree(REPO / "designs" / "example-tailsitter-wing", tmp_path / "ex")
    return tmp_path / "ex"


@pytest.fixture
def with_assembly(design):
    p = design / "plane.yaml"
    p.write_bytes(p.read_bytes() + ASSEMBLY.encode("utf-8"))
    return design


def test_animate_one_animation_per_step_in_order(with_assembly, tmp_path):
    out = tmp_path / "a.glb"
    r = call("assembly.animate", path=str(with_assembly), out=str(out))
    assert r.ok, r.messages
    assert r.data["animations"] == ["step-1", "step-2"]
    doc, glb = _doc(out)
    assert [a["name"] for a in doc["animations"]] == ["step-1", "step-2"]
    names = [[doc["nodes"][c["target"]["node"]]["name"] for c in a["channels"]] for a in doc["animations"]]
    assert names == [["center_body"], ["wing", "motor_l"]]
    for a in doc["animations"]:
        for c in a["channels"]:
            assert c["target"]["path"] == "translation"
    for acc in doc["accessors"]:
        assert 0 <= acc["bufferView"] < len(doc["bufferViews"])
    for bv in doc["bufferViews"]:
        assert bv["byteOffset"] + bv["byteLength"] <= doc["buffers"][0]["byteLength"]
    assert struct.unpack("<4sII", glb[:12])[2] == len(glb)


def test_animate_output_loads_and_keeps_geometry(with_assembly, tmp_path):
    out = tmp_path / "a.glb"
    r = call("assembly.animate", path=str(with_assembly), out=str(out))
    assert r.ok, r.messages
    plain = tmp_path / "plain.glb"
    export_glb(load_design(with_assembly), plain)
    animated = trimesh.load(out, file_type="glb")
    reference = trimesh.load(plain, file_type="glb")
    assert len(animated.geometry) == len(reference.geometry)


def test_animate_without_assembly_exit2(design, tmp_path):
    r = call("assembly.animate", path=str(design), out=str(tmp_path / "a.glb"))
    assert r.exit_code == 2
    assert any("no assembly.sequence" in m for m in r.messages)


def test_animate_unknown_component_exit2(design, tmp_path):
    p = design / "plane.yaml"
    p.write_bytes(p.read_bytes() + "\nassembly:\n  sequence:\n    - {step: 1, add: [nope]}\n".encode("utf-8"))
    r = call("assembly.animate", path=str(design), out=str(tmp_path / "a.glb"))
    assert r.exit_code == 2
    assert any("unknown component nope" in m for m in r.messages)


def test_animate_bad_design_path_exit2(tmp_path):
    r = call("assembly.animate", path=str(tmp_path / "missing"), out=str(tmp_path / "a.glb"))
    assert r.exit_code == 2
