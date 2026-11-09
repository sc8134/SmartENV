"""Custom exceptions for SmartEnv."""

from typing import Any


class ConfigError(Exception):
    """Base exception for all configuration errors."""

    def __init__(self, message: str, *, key: str | None = None, source: str | None = None) -> None:
        self.key = key
        self.source = source
        super().__init__(message)


class MissingKeyError(ConfigError):
    """Raised when a required configuration key is missing."""

    def __init__(
        self,
        key: str,
        *,
        source: str | None = None,
        available_keys: list[str] | None = None,
    ) -> None:
        self.key = key
        self.source = source
        self.available_keys = available_keys or []

        message = f"Required configuration key '{key}' is missing"
        if source:
            message += f" (from {source})"
        if self.available_keys:
            message += f". Available keys: {', '.join(sorted(self.available_keys))}"
        message += "."

        super().__init__(message, key=key, source=source)


class CastingError(ConfigError):
    """Raised when type casting fails."""

    def __init__(
        self,
        key: str,
        target_type: type,
        value: Any,
        *,
        source: str | None = None,
        reason: str | None = None,
    ) -> None:
        self.key = key
        self.target_type = target_type
        self.value = value
        self.source = source

        type_name = getattr(target_type, "__name__", str(target_type))
        message = f"Failed to cast key '{key}' to {type_name}"
        if source:
            message += f" (from {source})"
        message += f": got {repr(value)}"
        if reason:
            message += f" ({reason})"
        message += "."

        super().__init__(message, key=key, source=source)


class ParseError(ConfigError):
    """Raised when parsing a configuration file fails."""

    def __init__(
        self,
        message: str,
        *,
        source: str | None = None,
        line: int | None = None,
    ) -> None:
        self.source = source
        self.line = line

        full_message = message
        if source:
            full_message += f" (in {source})"
        if line is not None:
            full_message += f" at line {line}"

        super().__init__(full_message, source=source)