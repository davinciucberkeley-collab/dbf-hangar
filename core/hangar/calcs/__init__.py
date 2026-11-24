"""Built-in calculation functions for claims. A claim's calculation names one of these, or one added with register_calcs()."""


def sum_values(**terms):
    return {"total": sum(terms.values())}


def read_value(v):
    """Echo: a stored result read from its source (sitl/cad_mass.json and the like), not recomputed. The claim compares the value, as given, with its limit."""
    return {"v": v}


read_value.stored_result = True   # T103: claims over this function are reported as read, not recomputed

CALCS = {"sum_values": sum_values, "read_value": read_value}
from .concept_a import CALCS as _CONCEPT_A  # noqa: E402

CALCS.update(_CONCEPT_A)
