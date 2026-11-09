"""Utility functions for SmartEnv."""

import os
from typing import Any


# Environment variable names that indicate the environment
ENV_DETECTION_KEYS = [
    "APP_ENV",
    "ENVIRONMENT",
    "ENV",
    "FLASK_ENV",
    "NODE_ENV",
    "RAILS_ENV",
    "DJANGO_ENV",
    "FASTAPI_ENV",
]


# Known environment values and their normalized forms
ENV_NORMALIZATION = {
    # Production
    "prod": "production",
    "production": "production",
    "live": "production",
    # Development
    "dev": "development",
    "develop": "development",
    "development": "development",
    "local": "development",
    # Testing
    "test": "testing",
    "testing": "testing",
    "ci": "testing",
    # Staging
    "stage": "staging",
    "staging": "staging",
    "preprod": "staging",
}


def detect_environment(config: dict[str, Any] | None = None) -> str:
    """Detect the current environment from configuration or environment variables.
    
    Checks in order:
    1. Provided config dictionary
    2. Environment variables (ENV_DETECTION_KEYS)
    3. Defaults to 'development'
    
    Returns normalized environment name: 'development', 'production', 'testing', or 'staging'
    """
    # First check provided config
    if config:
        for key in ENV_DETECTION_KEYS:
            if key in config and config[key]:
                return _normalize_env(config[key])

    # Then check environment variables
    for key in ENV_DETECTION_KEYS:
        value = os.environ.get(key)
        if value:
            return _normalize_env(value)

    # Default
    return "development"


def _normalize_env(value: str) -> str:
    """Normalize an environment value to standard form."""
    lower = value.strip().lower()
    return ENV_NORMALIZATION.get(lower, lower)


def is_production(config: dict[str, Any] | None = None) -> bool:
    """Check if running in production environment."""
    return detect_environment(config) == "production"


def is_development(config: dict[str, Any] | None = None) -> bool:
    """Check if running in development environment."""
    return detect_environment(config) == "development"


def is_testing(config: dict[str, Any] | None = None) -> bool:
    """Check if running in testing environment."""
    return detect_environment(config) == "testing"


def is_staging(config: dict[str, Any] | None = None) -> bool:
    """Check if running in staging environment."""
    return detect_environment(config) == "staging"


def get_env_prefix(prefix: str | None) -> str:
    """Normalize environment variable prefix."""
    if not prefix:
        return ""
    prefix = prefix.strip().upper()
    if not prefix.endswith("_"):
        prefix += "_"
    return prefix


def filter_by_prefix(data: dict[str, Any], prefix: str) -> dict[str, Any]:
    """Filter dictionary keys by prefix, removing the prefix from keys."""
    if not prefix:
        return data

    result = {}
    prefix_len = len(prefix)
    for key, value in data.items():
        if key.startswith(prefix):
            new_key = key[prefix_len:]
            if new_key:  # Skip if key is exactly the prefix
                result[new_key] = value
    return result


def merge_configs(*configs: dict[str, Any]) -> dict[str, Any]:
    """Merge multiple configuration dictionaries.
    
    Later configs override earlier ones (higher precedence).
    """
    result: dict[str, Any] = {}
    for config in configs:
        if config:
            result.update(config)
    return result


def parse_env_vars(prefix: str | None = None) -> dict[str, str]:
    """Parse environment variables, optionally filtered by prefix."""
    prefix = get_env_prefix(prefix)
    result = {}

    for key, value in os.environ.items():
        if key.startswith(prefix):
            new_key = key[len(prefix):]
            if new_key:
                result[new_key] = value

    return result