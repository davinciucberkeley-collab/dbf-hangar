from __future__ import annotations
import shutil
from datetime import date
from pathlib import Path
import pytest, yaml
from hangar.ops import call, registry

REPO = Path(__file__).resolve().parents[1]
BOM = ("\nbom:\n  items:\n    - id: motor-a\n      qty: 2\n      unit_cost_usd: 12.5\n      url: https://example.com/m\n"
       "    - id: servo-b\n      qty: 1\n    - {id: prop-c, qty: 4, unit_cost_usd: 1.25}\n")
FILLED = ('---\nid: my-paper\ntitle: "A paper"\nauthors: "A. Author"\nyear: 2020\nurl: https://example.com/p\ntype: paper\n'
          'retrieved: 2026-11-24\nverified: true\n---\n\n## Summary\nShort summary.\n\n## Usable rules / numbers\nnone\n\n'
          '## How we could use it\n- tier 2\n')


@pytest.fixture
def root(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    shutil.copytree(REPO / "knowledge", tmp_path / "knowledge", ignore=shutil.ignore_patterns("diy-projects", "concepts"))
    shutil.copytree(REPO / "designs" / "example-tailsitter-wing", tmp_path / "designs" / "ex")
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def bom_design(root):
    p = root / "designs" / "ex" / "plane.yaml"
    p.write_bytes(p.read_bytes() + BOM.encode("utf-8"))
    return "designs/ex"


def test_b_ops_registered():
    assert {"research.new", "research.check", "morph.add-option", "morph.coverage", "bom.verify", "bom.cost"} <= set(registry())


def test_research_new_source_copies_template(root):
    r = call("research.new", kind="source", slug="my-paper")
    assert r.ok
    assert r.data["path"] == "knowledge/sources/my-paper.md"
    text = (root / "knowledge" / "sources" / "my-paper.md").read_text(encoding="utf-8")
    assert text.startswith("---\nid: my-paper\n")
    assert "## Usable rules / numbers" in text


def test_research_new_diy(root):
    r = call("research.new", kind="diy", slug="my-build")
    assert r.ok
    assert r.data["path"] == "knowledge/diy-projects/my-build.md"
    text = (root / "knowledge" / "diy-projects" / "my-build.md").read_text(encoding="utf-8")
    assert text.startswith("---\nid: my-build\n")


def test_research_new_rejects_bad_slug_and_existing(root):
    assert call("research.new", kind="source", slug="Bad Slug").exit_code == 2
    assert call("research.new", kind="source", slug="my-paper").ok
    assert call("research.new", kind="source", slug="my-paper").exit_code == 2


def test_research_check_template_is_incomplete(root):
    call("research.new", kind="source", slug="my-paper")
    r = call("research.check", path="knowledge/sources/my-paper.md")
    assert r.exit_code == 1
    assert r.data["kind"] == "source"
    missing = r.data["missing_fields"]
    assert "title" in missing and "url" in missing and "section:Summary" in missing
    assert "id" not in missing

    call("research.new", kind="diy", slug="my-build")
    r = call("research.check", path="knowledge/diy-projects/my-build.md")
    assert r.data["kind"] == "diy"
    assert "source_url" in r.data["missing_fields"]
    assert "section:Lessons for us" in r.data["missing_fields"]


def test_research_check_filled_source_passes(root):
    folder = root / "knowledge" / "sources"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "my-paper.md").write_text(FILLED, encoding="utf-8")
    r = call("research.check", path="knowledge/sources/my-paper.md")
    assert r.ok
    assert r.data["missing_fields"] == []

    (folder / "my-paper.md").write_text(FILLED.replace("verified: true", "verified: true | false"), encoding="utf-8")
    r = call("research.check", path="knowledge/sources/my-paper.md")
    assert r.exit_code == 1
    assert "verified" in r.data["missing_fields"]


def test_research_check_bad_path(root):
    assert call("research.check", path="knowledge/sources/nope.md").exit_code == 2
    (root / "knowledge" / "sources").mkdir(parents=True, exist_ok=True)
    (root / "knowledge" / "sources" / "plain.md").write_text("just text\n", encoding="utf-8")
    assert call("research.check", path="knowledge/sources/plain.md").exit_code == 2


def test_morph_add_option_inserts_one_line(root):
    chart = root / "knowledge" / "morphological-chart.yaml"
    before = chart.read_text(encoding="utf-8").splitlines()
    r = call("morph.add-option", dimension="tail", id="tandem", name="Tandem", source="morph-uaav-hybrid-2022")
    assert r.ok
    after = chart.read_text(encoding="utf-8").splitlines()
    assert len(after) == len(before) + 1
    new = [line for line in after if line not in before]
    assert new == ["      - {id: tandem, name: \"Tandem\", source: morph-uaav-hybrid-2022}"]
    remaining = list(after)
    remaining.remove(new[0])
    assert remaining == before
    dim = next(d for d in yaml.safe_load(chart.read_text(encoding="utf-8"))["dimensions"] if d["id"] == "tail")
    assert "tandem" in [o["id"] for o in dim["options"]]


def test_morph_add_option_errors(root):
    assert call("morph.add-option", dimension="nope", id="x-opt", name="X", source="morph-uaav-hybrid-2022").exit_code == 2
    assert call("morph.add-option", dimension="tail", id="v-tail", name="V", source="morph-uaav-hybrid-2022").exit_code == 2
    assert call("morph.add-option", dimension="tail", id="x-opt", name="X", source="no-such-source").exit_code == 2
    assert call("morph.add-option", dimension="tail", id="Bad Id", name="X", source="morph-uaav-hybrid-2022").exit_code == 2


def test_morph_coverage(root):
    cells = call("morph.coverage").data["cells"]
    assert {"dimension": "lift", "option": "flying-wing", "designs": ["example-tailsitter-wing"]} in cells
    assert {"dimension": "lift", "option": "fixed-wing", "designs": []} in cells
    chart = yaml.safe_load((root / "knowledge" / "morphological-chart.yaml").read_text(encoding="utf-8"))
    assert len(cells) == sum(len(d["options"]) for d in chart["dimensions"])


def test_bom_cost(bom_design):
    r = call("bom.cost", path=bom_design)
    assert r.data["total_usd"] == 30.0
    assert r.data["costed"] == 2
    assert r.data["missing_cost"] == ["servo-b"]
    assert r.data["unverified"] == ["motor-a", "servo-b", "prop-c"]


def test_bom_verify_inserts_block_stamp(root, bom_design):
    p = root / "designs" / "ex" / "plane.yaml"
    before = p.read_text(encoding="utf-8").splitlines()
    r = call("bom.verify", path=bom_design, item="motor-a", method="browser", evidence="https://example.com/m", by="ana")
    assert r.ok
    after = p.read_text(encoding="utf-8").splitlines()
    assert len(after) == len(before) + 1
    new_index = next(i for i, line in enumerate(after) if line not in before)
    assert after[new_index - 1].strip() == "url: https://example.com/m"
    remaining = after[:new_index] + after[new_index + 1:]
    assert remaining == before
    item = yaml.safe_load(p.read_text(encoding="utf-8"))["bom"]["items"][0]
    assert item["verified"] == {"by": "ana", "date": date.today().isoformat(), "method": "browser",
                                "evidence": "https://example.com/m"}
    assert call("bom.cost", path=bom_design).data["unverified"] == ["servo-b", "prop-c"]


def test_bom_verify_errors(bom_design):
    assert call("bom.verify", path=bom_design, item="motor-a", method="browser", evidence="https://example.com/m", by="ana").ok
    assert call("bom.verify", path=bom_design, item="motor-a", method="browser", evidence="e", by="ana").exit_code == 2
    assert call("bom.verify", path=bom_design, item="prop-c", method="browser", evidence="e", by="ana").exit_code == 2
    assert call("bom.verify", path=bom_design, item="zzz", method="browser", evidence="e", by="ana").exit_code == 2
    assert call("bom.verify", path=bom_design, item="servo-b", method="guess", evidence="e", by="ana").exit_code == 2
    assert call("bom.verify", path=bom_design, item="servo-b", method="browser", evidence="", by="ana").exit_code == 2
    assert call("bom.cost", path="designs/missing").exit_code == 2


def test_bom_cost_missing_qty_exit2(root):  # T17
    p = root / "designs" / "ex" / "plane.yaml"
    p.write_bytes(p.read_bytes() + b"\nbom:\n  items:\n    - {id: motor-a, unit_cost_usd: 12.5}\n")
    r = call("bom.cost", path="designs/ex")
    assert r.exit_code == 2 and any("motor-a" in m and "qty" in m for m in r.messages)


def test_bom_verify_non_mapping_verified_exit2(root):  # T17
    p = root / "designs" / "ex" / "plane.yaml"
    p.write_bytes(p.read_bytes() + b"\nbom:\n  items:\n    - id: motor-a\n      qty: 1\n      verified: yes\n")
    before = p.read_bytes()
    r = call("bom.verify", path="designs/ex", item="motor-a", method="browser", evidence="e", by="ana")
    assert r.exit_code == 2 and any("verified must be a mapping" in m for m in r.messages)
    assert p.read_bytes() == before


def test_templates_frontmatter_parses():
    for template in sorted((REPO / "knowledge").glob("TEMPLATE-*.md")):
        lines = template.read_text(encoding="utf-8").splitlines()
        assert lines[0] == "---", template.name
        close = lines.index("---", 1)
        assert isinstance(yaml.safe_load("\n".join(lines[1:close])), dict), template.name


def test_ingest_dedupes_within_one_file(root):
    p = root / "ledger" / "inbox" / "2026-11-24.yaml"
    p.parent.mkdir(parents=True, exist_ok=True)
    items = [{"kind": "task", "text": "Order foam", "source": "s"},
             {"kind": "task", "text": " order FOAM ", "source": "s"},
             {"kind": "idea", "text": "Try coroplast", "source": "s"}]
    p.write_text(yaml.safe_dump({"items": items}), encoding="utf-8")
    r = call("ledger.ingest", path=str(p))
    assert r.ok
    assert len(r.data["added"]) == 2
    assert len(r.skipped) == 1
    assert "order FOAM" in r.skipped[0]


def test_bom_cost_non_numeric_unit_cost_is_an_input_error(root, bom_design):  # T85
    p = root / "designs" / "ex" / "plane.yaml"
    p.write_text(p.read_text(encoding="utf-8").replace("unit_cost_usd: 12.5", "unit_cost_usd: free"), encoding="utf-8")
    r = call("bom.cost", path=bom_design)
    assert r.exit_code == 2 and "motor-a" in " ".join(r.messages) and "unit_cost_usd" in " ".join(r.messages)
