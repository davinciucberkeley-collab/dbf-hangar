"""Install the hangar harness (agents, quiet output style, hooks, harness code) into a target project."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

HANGAR = Path(__file__).resolve().parents[1]
GITIGNORE_LINES = ["ledger/prompts.jsonl", "ledger/events.jsonl", "ledger/.stop_blocks.json"]


def _is_old_python_hook(cmd: str) -> bool:
    return "harness/hooks/" in cmd and cmd.endswith('.py"')


def _merge_settings(target_settings: Path, source_settings: Path, written: list):
    if target_settings.exists():
        data = json.loads(target_settings.read_text(encoding="utf-8"))
    else:
        data = {}
    src = json.loads(source_settings.read_text(encoding="utf-8"))
    if "outputStyle" not in data and "outputStyle" in src:
        data["outputStyle"] = src["outputStyle"]
    hooks = data.setdefault("hooks", {})
    # Drop old direct `python ".../harness/hooks/x.py"` entries; other tools' hooks are kept.
    for event, entries in list(hooks.items()):
        kept = []
        for e in entries:
            cmds = e.get("hooks", [])
            live = [h for h in cmds if not _is_old_python_hook(h.get("command") or "")]
            if cmds and not live:
                continue
            if len(live) != len(cmds):
                e = dict(e, hooks=live)
            kept.append(e)
        hooks[event] = kept
    for event, entries in src.get("hooks", {}).items():
        existing = hooks.setdefault(event, [])
        present = {h.get("command") for e in existing for h in e.get("hooks", [])}
        for entry in entries:
            cmds = [h.get("command") for h in entry.get("hooks", [])]
            if cmds and all(c in present for c in cmds):
                for e in existing:  # same hook already installed: take over a changed matcher
                    if "matcher" in entry and [h.get("command") for h in e.get("hooks", [])] == cmds:
                        e["matcher"] = entry["matcher"]
                continue
            existing.append(entry)
            present.update(cmds)
    target_settings.parent.mkdir(parents=True, exist_ok=True)
    target_settings.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    written.append(target_settings.resolve())


def _copy(src: Path, dst: Path, written: list):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix == ".sh":
        # Shell scripts keep LF endings and are executable, whatever the checkout did.
        dst.write_bytes(src.read_bytes().replace(b"\r\n", b"\n"))
        dst.chmod(0o755)
    else:
        shutil.copyfile(src, dst)
    written.append(dst.resolve())


def _ensure_gitignore(target: Path, written: list):
    path = target / ".gitignore"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    present = {line.strip() for line in text.splitlines()}
    missing = [line for line in GITIGNORE_LINES if line not in present]
    if not missing:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    text += "".join(line + "\n" for line in missing)
    path.write_text(text, encoding="utf-8")
    written.append(path.resolve())


def _ensure_gitattributes(target: Path, written: list):
    line = "*.sh text eol=lf"
    path = target / ".gitattributes"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if line in {l.strip() for l in text.splitlines()}:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    path.write_text(text + line + "\n", encoding="utf-8")
    written.append(path.resolve())


def install(target: Path, source: Path | None = None) -> list[Path]:
    source = Path(source) if source is not None else HANGAR
    target = Path(target)
    if target.resolve() == Path.home().resolve():
        raise ValueError("install into a project folder, not your home folder")
    written: list[Path] = []

    for agent in sorted((source / ".claude" / "agents").glob("*.md")):
        _copy(agent, target / ".claude" / "agents" / agent.name, written)

    _copy(source / ".claude" / "output-styles" / "quiet.md",
          target / ".claude" / "output-styles" / "quiet.md", written)

    harness_src = source / "harness"
    for f in sorted(harness_src.rglob("*")):
        if not f.is_file() or "__pycache__" in f.relative_to(harness_src).parts:
            continue
        _copy(f, target / "harness" / f.relative_to(harness_src), written)

    _merge_settings(target / ".claude" / "settings.json", source / ".claude" / "settings.json", written)
    _ensure_gitignore(target, written)
    _ensure_gitattributes(target, written)
    return written


def main(argv=None):
    parser = argparse.ArgumentParser(description="Install the hangar harness into a project.")
    parser.add_argument("--target", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        files = install(args.target)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"Installed hangar harness into {args.target} ({len(files)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
