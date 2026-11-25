"""Motor thrust helpers: `propulsion.max_thrust_n` is a number > 0 or the text `pending` (unknown, never 0 or 1)."""
from __future__ import annotations

PENDING = "pending"


def thrust_n(motor: dict) -> float | None:
    """Peak static thrust in N, or None when it is pending."""
    v = motor["propulsion"]["max_thrust_n"]
    return None if v == PENDING else float(v)


def pending_motors(design, roles: tuple[str, ...] | None = None) -> list[str]:
    """Ids of motor components whose thrust is pending; with `roles`, only those whose propulsion.role (default both) is in it."""
    return [c["id"] for c in design.components
            if c["type"] == "motor" and c.get("propulsion", {}).get("max_thrust_n") == PENDING
            and (roles is None or c["propulsion"].get("role", "both") in roles)]
