"""hangar.geom: geometry kernel and generator registry (PDL 1.2)."""
from hangar.geom import generators  # noqa: F401  (registers the built-in generators)
from hangar.geom import wing, parts, powerplant, airframe, tails  # noqa: F401
from hangar.geom.registry import build_component, get, names, register  # noqa: F401
