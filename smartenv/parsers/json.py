"""Parser for JSON configuration files."""

import json
from typing import Any

from smartenv.exceptions import ParseError


def parse_json_file(filepath: str) -> dict[str, Any]:
    """Parse a JSON file and return a flattened dictionary with dot notation keys."""
    try:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        return _flatten_dict(data)

    except FileNotFoundError:
        raise
    except json.JSONDecodeError as e:
        raise ParseError(
            f"Invalid JSON: {e.msg}",
            source=filepath,
            line=e.lineno,
        )
    except Exception as e:
        raise ParseError(f"Failed to parse JSON file: {e}", source=filepath)


def parse_json_string(content: str, *, source: str = "<string>") -> dict[str, Any]:
    """Parse a JSON string and return a flattened dictionary with dot notation keys."""
    try:
        data = json.loads(content)
        return _flatten_dict(data)

    except json.JSONDecodeError as e:
        raise ParseError(
            f"Invalid JSON: {e.msg}",
            source=source,
            line=e.lineno,
        )
    except Exception as e:
        raise ParseError(f"Failed to parse JSON string: {e}", source=source)


def _flatten_dict(data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Flatten a nested dictionary using dot notation for keys."""
    result: dict[str, Any] = {}

    for key, value in data.items():
        new_key = f"{prefix}.{key}" if prefix else key

        if isinstance(value, dict):
            # Recursively flatten nested dictionaries
            result.update(_flatten_dict(value, new_key))
        else:
            result[new_key] = value

    return result