"""Fast YAML loading for hangar (U4.35, D81)."""
import yaml

_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


def safe_load(stream):
    """yaml.safe_load using libyaml's C loader when PyYAML has it, else the pure-Python SafeLoader. Same data either way."""
    return yaml.load(stream, Loader=_LOADER)
