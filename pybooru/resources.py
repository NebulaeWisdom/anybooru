"""Explicit project configuration and Rails parameter encoding."""

import json


def load_config(path):
    """Read a JSON parameter file; paths are relative to the working directory."""
    with open(path, encoding="utf-8") as config_file:
        return json.load(config_file)


def encode_params(params):
    """Encode nested mappings and sequences as Rails form/query parameters."""
    def items(key, value):
        if isinstance(value, dict):
            for child, item in value.items():
                yield from items("{}[{}]".format(key, child), item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                yield from items(key + "[]", item)
        elif value is not None:
            yield key, str(value).lower() if isinstance(value, bool) else value

    if params is None:
        return None
    return [pair for key, value in params.items() for pair in items(key, value)]
