# Claude Desktop + dbf-hangar MCP: facts for the team guide (W19-X, 2026-11-23)

Only pages opened are cited. "UNVERIFIED" marks things not confirmed from a page.

## 1. Connecting a local stdio MCP server

- Manual route still documented: Settings (Claude menu > Settings, not in-window) > Developer > Edit Config opens/creates the config. Source: https://modelcontextprotocol.io/docs/2026-07-28/develop/connect-local-servers.md
- Config file: macOS `~/Library/Application Support/Claude/claude_desktop_config.json`; Windows `%APPDATA%\Claude\claude_desktop_config.json`. Same source.
- Shape: `{"mcpServers": {"<name>": {"command": "...", "args": [...], "env": {...}}}}`. Windows paths in JSON need doubled backslashes. Same source; env example at https://modelcontextprotocol.io/docs/2026-07-28/tools/debugging.md
- Restart: fully quit and reopen Desktop (closing the window is not enough) after config or server code changes. debugging.md ("Testing changes").
- Absolute paths: "use absolute paths"; cwd for config-launched servers "may be undefined" (like `/` on macOS); "try using an absolute path for `command`". There is no documented `cwd` key in these pages (UNVERIFIED whether Desktop honors one). debugging.md ("Working directory", "Server startup").
- Env: stdio servers inherit only a limited, platform-dependent subset of env vars; set others in `env`. debugging.md.
- Full-path example for this repo (derived; `.venv\Scripts\plane-mcp.exe` exists on this machine):
  `{"mcpServers":{"dbf-hangar":{"command":"C:\\Users\\<you>\\dbf-hangar\\.venv\\Scripts\\plane-mcp.exe"}}}`
  macOS: `/Users/<you>/dbf-hangar/.venv/bin/plane-mcp`. Not tested in Desktop.
- Repo-path caveat (code): server resolves designs via `DESIGNS_DIR`/`REPO_ROOT` imported from `hangar.design` (mcp_server.py:21). Whether these derive from the package location (works from any cwd with an editable install) or from cwd was not checked; verify before telling teammates cwd does not matter. UNVERIFIED.
- Desktop Extensions (.mcpb; renamed from .dxt Sept 2025): install via Settings > Extensions, drag the .mcpb file, Install. Described as the streamlined option ("Instead of manually configuring JSON files and managing dependencies"); the support page does not say "recommended" and the Extensions page says orgs can disable them. Sources: https://claude.com/docs/connectors/custom/desktop-extensions and https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop . Python servers supported (support article). For a repo-editable install, JSON config is simpler than packaging a bundle (our judgement).
- Layout drift: support article says current layout is Settings > Desktop app > Extensions > Manage; older layout Settings > Developer. The MCP docs still describe Developer > Edit Config. Expect the button to be in either place.
- Logs: macOS `~/Library/Logs/Claude`; Windows `%APPDATA%\Claude\logs`. `mcp.log` = connection events; `mcp-server-<NAME>.log` = server stderr. Source: connect-local-servers.md. Never write to stdout in a stdio server (debugging.md).
- Check it connected: "+" in the chat box > Connectors, hover to see servers and tools (debugging.md "Checking server status"). Connectors can be toggled per conversation via "+" (https://claude.com/docs/connectors/getting-started.md).

## 2. Projects as a carrier for repo rules

- Projects hold custom instructions plus uploaded project knowledge (docs, text, code); Claude uses them as context in that project's chats. Free: max 5 projects. Paid plans get RAG mode that expands knowledge capacity up to 10x when near context limits. Source: https://support.claude.com/en/articles/9517075-what-are-projects
- Page gives NO numeric limits for instructions length, file size or file count, and does not say whether MCP connectors work inside projects. Treat as UNVERIFIED; test once (tool toggle in "+" menu in a project chat). Third-party figures (200K context, short instructions) seen in search results were not opened; not cited.
- Practical fit: put a condensed CLAUDE.md plus design-engineer role in Project instructions; upload `standards/*.yaml` summary and docs/mcp.md as knowledge. Knowledge is static copies (our inference); the server's `get_standards` and `get_schema` tools return the live versions.
- Team/Enterprise: editors can change instructions and knowledge; members chat only (search summary of support article; the page I opened did not state this, UNVERIFIED).

## 3. What Desktop chat lacks vs Claude Code

- CLAUDE.md auto-load: Claude Code feature, loaded "every session" from project/user/org scope. https://code.claude.com/docs/en/memory . Chat has no equivalent; use Project instructions.
- Subagents in `.claude/agents/` (markdown + YAML frontmatter) and hooks (also in subagent frontmatter) are Claude Code features. https://code.claude.com/docs/en/sub-agents . Chat does not read them (no source says it does; absence inferred).
- Shell, git, pytest: Chat with a local MCP server can only call the server's tools (https://modelcontextprotocol.io/docs/2026-07-28/develop/connect-local-servers.md). The academy page does not mention shell or terminal for Chat. https://academy.claude.com/tutorials/navigating-the-claude-desktop-app . So no pytest/git/shell from Chat unless a separate MCP server provides it (inference).
- Desktop app DOES now include a Claude Code mode: the desktop app "adds Claude Code, described as a visual coding workbench" (academy page above). Code tab environments: Local (runs on your machine with direct file access), Cloud, SSH, WSL on Windows; permission modes Manual / Accept edits / Plan / Auto / Bypass; Git worktree option; background tasks pane lists subagents and shell commands. Source: https://code.claude.com/docs/en/desktop (first 100k of 230k chars read). Not seen in the read part: explicit CLAUDE.md/hooks statements for the Code tab (assume same as CLI per memory/sub-agents pages; UNVERIFIED), and whether the Code tab reads `claude_desktop_config.json` (not stated; UNVERIFIED). Windows Git requirement not confirmed.
- Also: Cowork mode works on folders you grant (academy page), not a shell.

## 4. Tool permission prompts in Desktop

- Claude can ask approval before using a connector tool: "Allow once" or "Always allow" (skip prompt for that tool from now on). Change later under connector page > Tool permissions: Always allow / Needs approval / Blocked, per tool or group. Source: https://claude.com/docs/connectors/getting-started.md . Applied to connectors; for config-file local servers the same menu is presumed (UNVERIFIED).
- Advice from docs: only click Always allow for trusted servers; block tools you don't need (https://claude.com/docs/connectors/custom/desktop-extensions). Suggest: leave write tools (design_set, save_design, design_propose) on "Needs approval".
- MCP quickstart: all actions need explicit approval (connect-local-servers.md "How Approval Works").

## 5. This repo's server

- Entry point: `plane-mcp = "hangar.mcp_server:main"` (pyproject.toml:19); CLI `plane = "hangar.cli:main"` (:18). Install: `pip install -e ".[mcp]"` (docs/mcp.md:29). Existing docs/mcp.md:37-47 shows Desktop config with bare `command: "plane-mcp"` (works only if on PATH Desktop sees; prefer full path). Transport stdio (mcp_server.py:138-139). Server name "dbf-hangar" (:25).
- Tools: one per registry op, name = op with `.` -> `_` (mcp_server.py:66-69, 62), description gets " Writes files." when op mutates (:69); plus hand-written `save_design` (:72, writes designs/<id>/plane.yaml after tier-0 check, :97-98), `get_schema` (:103), `get_standards` (:112), `list_structural_parts` (:123, read-only; reads fea results).
- Registry ops now (from `registry()` on this machine). Writers (W): assembly_animate, bench_run, bom_verify, claim_import-dbf, design_copy, design_export, design_migrate, design_new, design_propose, design_set, docs_cli, fea_run, fea_setup, idea_add, ledger_add, ledger_import-dbf, ledger_ingest, ledger_seed, ledger_set, morph_add-option, research_new, schema_docs, update_add, update_new, update_publish. Readers (R): bench_list, bench_report, bom_cost, bom_list, claim_check/explain/list, design_diff/get/list/mass/sweep/validate, fea_plan, gate_explain/list, ledger_check/report, morph_coverage/list, ops_list, research_check, sim_drop, sim_mechanism, standards_*, tools_doctor. (Op names with `-` become tool names containing `-`; whether Desktop accepts them: UNVERIFIED, so check the tool list after connecting.)
- Note: ~57 tools is a lot of surface; Always-allow only on readers.
