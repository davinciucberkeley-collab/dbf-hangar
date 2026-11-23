"""The one pattern for a bare id (a design, template, agent or task name). Always test it with `fullmatch`:
`match` on a `$`-anchored pattern accepts a trailing newline."""
from __future__ import annotations

import re

ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
