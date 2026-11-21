"""Built-in calculation functions for claims. A claim's calculation names one of these, or one added with register_calcs()."""


def sum_values(**terms):
    return {"total": sum(terms.values())}


CALCS = {"sum_values": sum_values}
