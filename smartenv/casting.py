"""Type casting system for configuration values."""

import json
from collections.abc import Callable
from typing import Any

from .exceptions import CastingError

# Type alias for caster functions
Caster = Callable[[Any], Any]


# Built-in casters
def cast_bool(value: Any) -> bool:
    """Cast a value to boolean.
    
    True values (case-insensitive): true, 1, yes, on, y, t
    False values (case-insensitive): false, 0, no, off, n, f
    """
    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return bool(value)

    if not isinstance(value, str):
        raise CastingError("bool", bool, value, reason="unsupported type")

    lower = value.strip().lower()

    if lower in ("true", "1", "yes", "on", "y", "t"):
        return True
    if lower in ("false", "0", "no", "off", "n", "f"):
        return False

    raise CastingError("bool", bool, value, reason=f"unrecognized boolean value: {value!r}")


def cast_int(value: Any) -> int:
    """Cast a value to integer."""
    if isinstance(value, int) and not isinstance(value, bool):
        return value

    if isinstance(value, float):
        if value.is_integer():
            return int(value)
        raise CastingError("int", int, value, reason="float value is not a whole number")

    if not isinstance(value, str):
        raise CastingError("int", int, value, reason="unsupported type")

    stripped = value.strip()
    if not stripped:
        raise CastingError("int", int, value, reason="empty string")

    # Handle hex, octal, binary prefixes
    try:
        if stripped.startswith(("0x", "0X")):
            return int(stripped, 16)
        if stripped.startswith(("0o", "0O")):
            return int(stripped, 8)
        if stripped.startswith(("0b", "0B")):
            return int(stripped, 2)
        return int(stripped)
    except ValueError as e:
        raise CastingError("int", int, value, reason=str(e))


def cast_float(value: Any) -> float:
    """Cast a value to float."""
    if isinstance(value, float):
        return value

    if isinstance(value, int) and not isinstance(value, bool):
        return float(value)

    if not isinstance(value, str):
        raise CastingError("float", float, value, reason="unsupported type")

    stripped = value.strip()
    if not stripped:
        raise CastingError("float", float, value, reason="empty string")

    try:
        return float(stripped)
    except ValueError as e:
        raise CastingError("float", float, value, reason=str(e))


def cast_list(value: Any, separator: str = ",") -> list[str]:
    """Cast a value to list of strings.
    
    By default splits on comma. Also supports JSON-style arrays.
    """
    if isinstance(value, list):
        return [str(item) for item in value]

    if not isinstance(value, str):
        raise CastingError("list", list, value, reason="unsupported type")

    stripped = value.strip()
    if not stripped:
        return []

    # Try JSON array first
    if stripped.startswith("[") and stripped.endswith("]"):
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except json.JSONDecodeError:
            pass

    # Split by separator
    return [item.strip() for item in stripped.split(separator) if item.strip()]


def cast_json(value: Any) -> Any:
    """Cast a value by parsing as JSON."""
    if isinstance(value, (dict, list, int, float, bool)) or value is None:
        return value

    if not isinstance(value, str):
        raise CastingError("json", object, value, reason="unsupported type")

    stripped = value.strip()
    if not stripped:
        raise CastingError("json", object, value, reason="empty string")

    try:
        return json.loads(stripped)
    except json.JSONDecodeError as e:
        raise CastingError("json", object, value, reason=str(e))


# Registry of built-in casters
_BUILTIN_CASTERS: dict[type | str, Caster] = {
    bool: cast_bool,
    "bool": cast_bool,
    "boolean": cast_bool,
    int: cast_int,
    "int": cast_int,
    "integer": cast_int,
    float: cast_float,
    "float": cast_float,
    "double": cast_float,
    list: cast_list,
    "list": cast_list,
    "array": cast_list,
    "json": cast_json,
    str: lambda v: str(v) if v is not None else "",
    "str": lambda v: str(v) if v is not None else "",
    "string": lambda v: str(v) if v is not None else "",
}


def get_caster(cast: type | str | Callable[[Any], Any] | None) -> Caster | None:
    """Get a caster function from a type, string name, or callable."""
    if cast is None:
        return None

    if callable(cast) and not isinstance(cast, type):
        # Custom callable
        return cast

    if isinstance(cast, str):
        # String name lookup
        if cast in _BUILTIN_CASTERS:
            return _BUILTIN_CASTERS[cast]
        raise ValueError(f"Unknown caster name: {cast!r}. Available: {list(_BUILTIN_CASTERS.keys())}")

    # Type lookup
    if cast in _BUILTIN_CASTERS:
        return _BUILTIN_CASTERS[cast]

    # For other types, try to use the type constructor
    return cast  # type: ignore[return-value]


def register_caster(name: str | type, caster: Caster) -> None:
    """Register a custom caster."""
    _BUILTIN_CASTERS[name] = caster


def cast_value(value: Any, cast: type | str | Callable[[Any], Any] | None, *, key: str = "value", source: str | None = None) -> Any:
    """Cast a value using the specified caster."""
    if cast is None:
        return value

    caster = get_caster(cast)
    if caster is None:
        return value

    try:
        return caster(value)
    except CastingError as e:
        # Re-raise with the correct key and source
        raise CastingError(key, e.target_type, value, source=source, reason=str(e))
    except Exception as e:
        # Determine the target type for error message
        if isinstance(cast, type):
            target_type = cast
        elif isinstance(cast, str):
            # Map string names to types for error message
            type_map = {"int": int, "bool": bool, "float": float, "list": list, "json": object, "str": str, "string": str}
            target_type = type_map.get(cast, object)
        else:
            target_type = type(cast)
        raise CastingError(key, target_type, value, source=source, reason=str(e))