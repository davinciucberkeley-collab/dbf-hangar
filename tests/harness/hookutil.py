import json, os, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

def run_hook(name, event, root, **env):
    e = dict(os.environ, CLAUDE_PROJECT_DIR=str(root), **env)
    # Bytes in, explicit UTF-8 out: the child writes UTF-8, but the locale codec
    # (cp1252 on Windows) must not be used to decode it in the parent.
    r = subprocess.run([sys.executable, str(REPO / "harness" / "hooks" / f"{name}.py")],
                       input=json.dumps(event).encode("utf-8"), capture_output=True, env=e)
    return subprocess.CompletedProcess(r.args, r.returncode,
                                       r.stdout.decode("utf-8", errors="replace"),
                                       r.stderr.decode("utf-8", errors="replace"))
