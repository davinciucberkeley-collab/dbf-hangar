import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "harness"))
import install as installer  # harness/install.py


def test_installer_converts_crlf_sh_to_lf(tmp_path):
    src = tmp_path / "src"
    shutil.copytree(REPO / ".claude", src / ".claude")
    shutil.copytree(REPO / "harness", src / "harness", ignore=shutil.ignore_patterns("__pycache__"))
    run_sh = src / "harness" / "hooks" / "run.sh"
    crlf = run_sh.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    run_sh.write_bytes(crlf)
    assert b"\r\n" in run_sh.read_bytes()  # the fixture really is CRLF
    dst = tmp_path / "dst"
    dst.mkdir()
    installer.install(dst, source=src)
    out = (dst / "harness" / "hooks" / "run.sh").read_bytes()
    assert b"\r" not in out
    assert out == crlf.replace(b"\r\n", b"\n")
