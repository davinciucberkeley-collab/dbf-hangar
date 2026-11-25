"""Every generator parameter has a doc, and every numeric doc names its unit (U13.2)."""
import re

import hangar.geom  # noqa: F401  (registers the generators)
from hangar.geom import registry

UNIT_RE = re.compile(r"\b(mm|deg|g|fraction|ratio|count)\b")
NUMERIC = ("number", "int", "vec2", "vec3")

# Params whose value is a pure index or flag (neither a length, angle, mass,
# fraction, ratio nor count). Add one only with a reason from its code.
NO_UNIT: set[str] = set()


def _params():
    for n in registry.names():
        for k, spec in registry.get(n).params.items():
            yield n, k, spec


def test_every_param_has_a_doc():
    failures = [f"{n}.{k}" for n, k, spec in _params() if spec.doc.strip() == ""]
    assert failures == []


def test_numeric_docs_name_a_unit():
    failures = [
        f"{n}.{k}"
        for n, k, spec in _params()
        if spec.kind in NUMERIC and f"{n}.{k}" not in NO_UNIT and not UNIT_RE.search(spec.doc)
    ]
    assert failures == []


def test_wing_span_doc_is_unchanged():
    assert registry.get("wing_panel").params["span"].doc == "tip to tip, mm"
