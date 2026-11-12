"""Core Config class and load function for SmartEnv."""

import os
from collections.abc import Callable, Mapping
from typing import Any, overload

from .casting import cast_list, cast_value
from .exceptions import MissingKeyError
from .parsers import parse_env_file, parse_json_file, parse_toml_file
from .utils import detect_environment, filter_by_prefix, merge_configs, parse_env_vars


class Config(Mapping):
    """Smart configuration container with nested access, casting, and validation."""

    def __init__(
        self,
        data: dict[str, Any],
        *,
        env_prefix: str | None = None,
        source_files: list[str] | None = None,
    ) -> None:
        self._data = data
        self._env_prefix = env_prefix
        self._source_files = source_files or []
        self._environment = detect_environment(data)
        self._nested_cache: dict[str, Config] = {}

    @property
    def environment(self) -> str:
        """Current environment name (development, production, testing, staging)."""
        return self._environment

    @property
    def is_production(self) -> bool:
        """True if running in production environment."""
        return self._environment == "production"

    @property
    def is_development(self) -> bool:
        """True if running in development environment."""
        return self._environment == "development"

    @property
    def is_testing(self) -> bool:
        """True if running in testing environment."""
        return self._environment == "testing"

    @property
    def is_staging(self) -> bool:
        """True if running in staging environment."""
        return self._environment == "staging"

    def __getitem__(self, key: str) -> Any:
        if key not in self._data:
            raise KeyError(key)
        return self._data[key]

    def __iter__(self) -> Any:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __contains__(self, key: object) -> bool:
        return key in self._data

    def __repr__(self) -> str:
        sources = f", sources={self._source_files!r}" if self._source_files else ""
        return f"Config({len(self._data)} keys{sources})"

    # Attribute access for nested keys
    def __getattr__(self, name: str) -> Any:
        data = self.__dict__.get("_data")
        if data is None:
            # Reached before __init__ runs or while copy/pickle builds the instance
            raise AttributeError(name)

        # Check if it's a nested config namespace
        if "." not in name:
            prefix = f"{name}."
            has_nested = any(k.startswith(prefix) for k in data)
            if has_nested:
                return self._get_nested(name)

        # Otherwise check if it's a direct key
        if name in data:
            return data[name]

        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def _get_nested(self, prefix: str) -> "Config":
        """Get a nested Config for a key prefix."""
        if prefix in self._nested_cache:
            return self._nested_cache[prefix]

        nested_prefix = f"{prefix}."
        nested_data = {
            k[len(nested_prefix) :]: v for k, v in self._data.items() if k.startswith(nested_prefix)
        }

        nested = Config(nested_data, env_prefix=self._env_prefix)
        self._nested_cache[prefix] = nested
        return nested

    # Main get method with casting and defaults
    @overload
    def get(self, key: str, default: Any = None, cast: None = None) -> Any: ...
    @overload
    def get(self, key: str, default: Any, cast: type | str | Callable[[Any], Any]) -> Any: ...
    @overload
    def get(
        self,
        key: str,
        default: None = None,
        cast: type | str | Callable[[Any], Any] | None = None,
    ) -> Any: ...

    def get(
        self,
        key: str,
        default: Any = None,
        cast: type | str | Callable[[Any], Any] | None = None,
    ) -> Any:
        """Get a configuration value with optional casting and default.

        Args:
            key: Configuration key (supports dot notation for nested access)
            default: Default value if key is not found
            cast: Type or caster function to convert the value

        Returns:
            The configuration value, cast if requested, or default if not found.
            Keys present with a value of ``None`` are returned as ``None``.

        Raises:
            CastingError: If casting fails
        """
        if key not in self._data:
            return default

        return cast_value(self._data[key], cast, key=key, source=self._source_name)

    @property
    def _source_name(self) -> str | None:
        if self._source_files:
            return ", ".join(self._source_files)
        return None

    # Required keys validation
    def require(self, *keys: str) -> "Config":
        """Ensure required keys are present.

        Args:
            *keys: One or more required configuration keys

        Returns:
            Self for chaining

        Raises:
            MissingKeyError: If any required key is missing
        """
        missing = [key for key in keys if key not in self._data]
        available = list(self._data.keys())

        if missing:
            raise MissingKeyError(
                missing[0],
                source=self._source_name,
                available_keys=available,
                missing_keys=missing,
            )

        return self

    def require_all(self, keys: list[str]) -> "Config":
        """Ensure all keys in a list are present."""
        return self.require(*keys)

    # Convenience methods for common types
    def get_bool(self, key: str, default: bool | None = None) -> bool | None:
        """Get a boolean value."""
        result: bool | None = self.get(key, default=default, cast=bool)
        return result

    def get_int(self, key: str, default: int | None = None) -> int | None:
        """Get an integer value."""
        result: int | None = self.get(key, default=default, cast=int)
        return result

    def get_float(self, key: str, default: float | None = None) -> float | None:
        """Get a float value."""
        result: float | None = self.get(key, default=default, cast=float)
        return result

    def get_list(
        self, key: str, default: list[str] | None = None, separator: str = ","
    ) -> list[str] | None:
        """Get a list value."""
        result: list[str] | None = self.get(
            key, default=default, cast=lambda v: cast_list(v, separator)
        )
        return result

    def get_json(self, key: str, default: Any = None) -> Any:
        """Get a JSON-parsed value."""
        return self.get(key, default=default, cast="json")

    def get_str(self, key: str, default: str | None = None) -> str | None:
        """Get a string value."""
        result: str | None = self.get(key, default=default, cast=str)
        return result

    # Dictionary-like methods
    def keys(self) -> Any:
        return self._data.keys()

    def values(self) -> Any:
        return self._data.values()

    def items(self) -> Any:
        return self._data.items()

    def to_dict(self) -> dict[str, Any]:
        """Return a plain dictionary copy of the configuration."""
        return dict(self._data)

    def update(self, other: dict[str, Any]) -> "Config":
        """Update configuration with another dictionary (returns new Config)."""
        new_data = merge_configs(self._data, other)
        return Config(new_data, env_prefix=self._env_prefix, source_files=self._source_files)

    def with_prefix(self, prefix: str) -> "Config":
        """Return a new Config with keys filtered by prefix (prefix removed)."""
        filtered = filter_by_prefix(self._data, prefix)
        return Config(filtered, env_prefix=prefix, source_files=self._source_files)


def load(
    *sources: str | os.PathLike[str],
    env_prefix: str | None = None,
    environment: str | None = None,
) -> Config:
    """Load configuration from multiple sources with precedence.

    Precedence (highest to lowest):
    1. Real environment variables (with optional prefix)
    2. .env files
    3. TOML files
    4. JSON files

    Args:
        *sources: Paths to configuration files (.env, .toml, .json)
        env_prefix: Prefix for environment variables (e.g., "APP_")
        environment: Override environment detection

    Returns:
        Config object with merged configuration
    """
    # Files are merged in ascending priority: JSON, then TOML, then .env, so that
    # .env > TOML > JSON regardless of argument order. Within one format, later
    # arguments override earlier ones.
    parsed: list[tuple[int, int, dict[str, Any]]] = []

    for index, source in enumerate(sources):
        source_path = os.fspath(source)
        ext = os.path.splitext(source_path)[1].lower()

        if ext in (".toml", ".tml"):
            priority = 1
            data = parse_toml_file(source_path)
        elif ext == ".json":
            priority = 0
            data = parse_json_file(source_path)
        else:
            # .env files, plus unknown extensions treated as .env
            priority = 2
            data = parse_env_file(source_path)

        parsed.append((priority, index, data))

    parsed.sort(key=lambda item: (item[0], item[1]))
    configs = [data for _, _, data in parsed]

    # 1. Environment variables (highest precedence - added last)
    env_vars = parse_env_vars(env_prefix)
    if env_vars:
        configs.append(env_vars)

    # Merge all configs (later sources override earlier)
    merged = merge_configs(*configs)

    # Override environment if explicitly provided
    if environment:
        merged["ENVIRONMENT"] = environment
        merged["APP_ENV"] = environment

    return Config(merged, env_prefix=env_prefix, source_files=[os.fspath(s) for s in sources])


def load_env(
    filepath: str | os.PathLike[str],
    *,
    env_prefix: str | None = None,
) -> Config:
    """Load configuration from a single .env file."""
    return load(filepath, env_prefix=env_prefix)


def load_toml(
    filepath: str | os.PathLike[str],
    *,
    env_prefix: str | None = None,
) -> Config:
    """Load configuration from a single TOML file."""
    return load(filepath, env_prefix=env_prefix)


def load_json(
    filepath: str | os.PathLike[str],
    *,
    env_prefix: str | None = None,
) -> Config:
    """Load configuration from a single JSON file."""
    return load(filepath, env_prefix=env_prefix)
