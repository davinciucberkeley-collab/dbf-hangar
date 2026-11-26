"""U16.1 S7: kinematic MJCF export (hinges, servo actuators, closed pushrod loop) against the S1 hand values."""
import copy
import math

import numpy as np
import pytest
from pathlib import Path

mujoco = pytest.importorskip("mujoco")

from click.testing import CliRunner  # noqa: E402

from hangar.cli import cli  # noqa: E402
from hangar.design import Design, load_design  # noqa: E402
from hangar.sim import build_kinematic_mjcf, build_mjcf  # noqa: E402

FIX = Path(__file__).parent / "fixtures" / "four-bar"
ROOT = Path(__file__).parent.parent


def model(design=None):
    d = design or load_design(FIX)
    return mujoco.MjModel.from_xml_string(build_kinematic_mjcf(d))


def drive(m, deg, seconds=1.0):
    data = mujoco.MjData(m)
    data.ctrl[0] = math.radians(deg)
    for _ in range(int(seconds / m.opt.timestep)):
        mujoco.mj_step(m, data)
    return data


def ang(m, data, name):
    j = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, name)
    return math.degrees(data.qpos[m.jnt_qposadr[j]])


def jid(m, name):
    return mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, name)


def test_structure():
    text = build_kinematic_mjcf(load_design(FIX))
    m = mujoco.MjModel.from_xml_string(text)
    assert (m.nbody, m.njnt, m.nu, m.neq, m.ngeom) == (5, 3, 1, 1, 7)
    assert m.jnt_type[jid(m, "servo-arm")] == mujoco.mjtJoint.mjJNT_HINGE
    assert m.jnt_type[jid(m, "stab-elev")] == mujoco.mjtJoint.mjJNT_HINGE
    assert m.jnt_type[jid(m, "arm-rod")] == mujoco.mjtJoint.mjJNT_BALL
    assert mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_EQUALITY, 0) == "elevator-drive-link"
    assert mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_ACTUATOR, 0) == "elevator-drive"
    assert "<weld" not in text and "<freejoint" not in text
    assert not np.any(m.opt.gravity)


def test_servo_drives_the_surface_like_the_s1_solve():
    m = model()
    for deg, want in ((-20, 8.1215), (-10, 4.0154), (10, -3.8240), (20, -7.3789)):
        data = drive(m, deg)
        assert ang(m, data, "servo-arm") == pytest.approx(deg, abs=0.05)
        assert ang(m, data, "stab-elev") == pytest.approx(want, abs=0.02)


def test_no_nan_no_warnings_at_the_ends():
    m = model()
    for deg in (20, -20):
        data = drive(m, deg)
        assert np.all(np.isfinite(data.qpos))
        assert sum(int(w.number) for w in data.warning) == 0


def test_loop_closes_in_the_simulation():
    m = model()
    data = drive(m, 20)
    r = np.nonzero(data.efc_type[:data.nefc] == mujoco.mjtConstraint.mjCNSTR_EQUALITY)[0]
    assert len(r) == 3
    assert np.abs(data.efc_pos[r]).max() < 1e-4


def test_plain_mjcf_is_untouched():
    t = build_mjcf(load_design(FIX))
    assert "<freejoint" in t and "<weld" in t
    for s in ("<connect", "<position", "<joint name="):
        assert s not in t


def test_wheel_is_a_ground_colliding_continuous_joint():
    data = copy.deepcopy(load_design(FIX).data)
    data["components"].append({"id": "wheel", "type": "other", "geometry": {"generator": "tube", "params": {"axis": "y", "length": 6, "outer_d": 20}},
                               "position": [100, 0, -30], "mass_g": 2, "manufacturing": {"method": "purchased"}})
    data["attachments"].append({"id": "stab-wheel", "parent": "stab", "child": "wheel", "method": "bolted", "location": [100, 0, -30],
                                "embed_ok": True, "rated_load_n": 10,
                                "articulation": {"type": "continuous", "pivot": [100, 0, -30], "axis": [0, 1, 0]}})
    m = model(Design(data=data, path=FIX / "plane.yaml"))
    assert m.njnt == 4
    j = jid(m, "stab-wheel")
    assert m.jnt_type[j] == mujoco.mjtJoint.mjJNT_HINGE and m.jnt_limited[j] == 0
    g = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, "ground")
    assert g >= 0
    assert m.geom_pos[g][2] == pytest.approx(-0.040, abs=0.0005)
    assert m.geom_contype[g] == 1
    wheel_body = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "wheel")
    others = [i for i in range(m.ngeom) if i != g and m.geom_contype[i] == 2]
    assert others and all(m.geom_bodyid[i] == wheel_body for i in others)
    assert sum(1 for i in range(m.ngeom) if m.geom_bodyid[i] == wheel_body) == len(others)


def test_export_op_and_cli(tmp_path):
    out = tmp_path / "k.xml"
    res = CliRunner().invoke(cli, ["export", str(FIX), "--format", "mjcf-kinematic", "--out", str(out)])
    assert res.exit_code == 0, res.output
    assert out.read_text() == build_kinematic_mjcf(load_design(FIX))
    h = CliRunner().invoke(cli, ["export", "--help"])
    assert "mjcf-kinematic" in h.output
    # the overlay-guard assertion is skipped: it needs the overlay test fixtures (test_cad_overlay_guard)


def test_docs_in_sync():
    rd = lambda p: (ROOT / p).read_text(encoding="utf-8")  # noqa: E731
    assert "mjcf-kinematic" in rd("docs/cli.md")
    assert "Kinematic MJCF export" in rd("docs/mechanisms.md")
    assert "mjcf-kinematic" in rd("docs/mcp.md")
