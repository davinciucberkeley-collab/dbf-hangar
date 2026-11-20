"""UserPromptSubmit hook: log the prompt to the ledger and tell its id. Never raises."""
import json
import sys
from pathlib import Path


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import ledger

    event = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    prompt = event.get("prompt") or ""
    if not prompt.strip():
        return 0
    root = ledger.project_root(event)
    item_id = ledger.add_prompt(root, event.get("session_id") or "", prompt)
    ledger_py = Path(root).resolve() / "harness" / "ledger.py"
    print(f'Logged as {item_id}. When done: python "{ledger_py}" addressed {item_id} --evidence "<what answered it>"')
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except Exception as e:
        print(f"log_prompt: {e!r}", file=sys.stderr)
        code = 0
    sys.exit(code)
