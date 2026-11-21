"""Built-in calculation functions for claims. A claim's calculation names one of these, or one added with register_calcs()."""


def sum_values(**terms):
    return {"total": sum(terms.values())}


CALCS = {"sum_values": sum_values}
from .concept_a import CALCS as _CONCEPT_A  # noqa: E402

CALCS.update(_CONCEPT_A)
