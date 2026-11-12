"""Parser for TOML configuration files."""

import sys
from typing import Any

from smartenv.exceptions import ParseError


def parse_toml_file(filepath: str) -> dict[str, Any]:
    """Parse a TOML file and return a flattened dictionary with dot notation keys."""
    try:
        if sys.version_info >= (3, 11):
            import tomllib
        else:
            # For Python < 3.11, try to import tomli
            try:
                import tomli as tomllib
            except ImportError:
                raise ParseError(
                    "TOML support requires Python 3.11+ or the 'tomli' package",
                    source=filepath,
                ) from None

        with open(filepath, "rb") as f:
            data = tomllib.load(f)

        return _flatten_dict(data)

    except FileNotFoundError:
        raise
    except ParseError:
        raise
    except Exception as e:
        raise ParseError(f"Failed to parse TOML file: {e}", source=filepath) from e


def parse_toml_string(content: str, *, source: str = "<string>") -> dict[str, Any]:
    """Parse a TOML string and return a flattened dictionary with dot notation keys."""
    try:
        if sys.version_info >= (3, 11):
            import tomllib
        else:
            try:
                import tomli as tomllib
            except ImportError:
                raise ParseError(
                    "TOML support requires Python 3.11+ or the 'tomli' package",
                    source=source,
                ) from None

        data = tomllib.loads(content)
        return _flatten_dict(data)

    except ParseError:
        raise
    except Exception as e:
        raise ParseError(f"Failed to parse TOML string: {e}", source=source) from e


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
