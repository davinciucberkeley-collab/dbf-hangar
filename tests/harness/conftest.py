import json, os, subprocess, sys
from pathlib import Path
import pytest

REPO = Path(__file__).resolve().parents[2]

@pytest.fixture
def root(tmp_path):
    (tmp_path / "plans").mkdir()
    (tmp_path / "plans" / "2026-11-20-x.md").write_text(
        "# P\n## 7. Units\n### Unit U9.1: Done thing\n- [x] a\n### Unit U9.2: Open thing\n- [ ] b\n## 8. End\n", encoding="utf-8")
    return tmp_path

def run_hook(name, event, root, **env):
    e = dict(os.environ, CLAUDE_PROJECT_DIR=str(root), **env)
    return subprocess.run([sys.executable, str(REPO / "harness" / "hooks" / f"{name}.py")],
                          input=json.dumps(event), capture_output=True, text=True, env=e)
