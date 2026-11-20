import json, os, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

def run_hook(name, event, root, **env):
    e = dict(os.environ, CLAUDE_PROJECT_DIR=str(root), **env)
    return subprocess.run([sys.executable, str(REPO / "harness" / "hooks" / f"{name}.py")],
                          input=json.dumps(event), capture_output=True, text=True, env=e)
