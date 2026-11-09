"""
SmartEnv - Simple, powerful, zero-dependency configuration loader.

A modern Python configuration library that loads from .env files, TOML, JSON,
and environment variables with nested access, type casting, and validation.

Example:
    from smartenv import load

    config = load(".env", "config.toml", env_prefix="APP_")
    
    # Access styles
    config.get("DATABASE_URL")
    config["db.host"]
    config.db.host
    
    # Casting + defaults
    config.get("PORT", default=8000, cast=int)
    config.get("DEBUG", cast=bool)
    
    # Validation
    config.require("SECRET_KEY", "DATABASE_URL")
    
    # Environment helpers
    config.environment
    config.is_production
"""

from .core import Config, load, load_env, load_json, load_toml
from .exceptions import CastingError, ConfigError, MissingKeyError, ParseError
from .utils import detect_environment

__version__ = "1.0.0"

__all__ = [
    # Main API
    "load",
    "load_env",
    "load_toml",
    "load_json",
    "Config",
    # Exceptions
    "ConfigError",
    "MissingKeyError",
    "CastingError",
    "ParseError",
    # Utilities
    "detect_environment",
]