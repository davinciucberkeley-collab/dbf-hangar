"""Fast YAML loading for hangar (U11.2, D81)."""
import yaml

_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


def safe_load(stream):
    """yaml.safe_load using libyaml's C loader when PyYAML has it, else the pure-Python SafeLoader. Same data for valid input; libyaml accepts some inputs the pure loader rejects (e.g. a trailing tab) and loses the error caret."""
    return yaml.load(stream, Loader=_LOADER)
