import pytest
from hookutil import REPO  # noqa: F401  (helpers live in hookutil so test modules never import a 'conftest')

@pytest.fixture
def root(tmp_path):
    (tmp_path / "plans").mkdir()
    (tmp_path / "plans" / "2026-11-20-x.md").write_text(
        "# P\n## 7. Units\n### Unit U9.1: Done thing\n- [x] a\n### Unit U9.2: Open thing\n- [ ] b\n## 8. End\n", encoding="utf-8")
    return tmp_path
