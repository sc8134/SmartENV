# SmartEnv

[![Python Version](https://img.shields.io/pypi/pyversions/smartenv.svg)](https://pypi.org/project/smartenv/)
[![License](https://img.shields.io/pypi/l/smartenv.svg)](https://github.com/smartenv/smartenv/blob/main/LICENSE)
[![PyPI Version](https://img.shields.io/pypi/v/smartenv.svg)](https://pypi.org/project/smartenv/)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)](https://github.com/smartenv/smartenv)

> **Simple + Powerful + Zero Dependencies + Modern API**

SmartEnv is a pure standard-library Python configuration loader that combines the simplicity of `python-dotenv` with the power of `pydantic-settings` — but with zero dependencies and a delightful developer experience.

## Why SmartEnv?

| Feature | python-dotenv | pydantic-settings | **SmartEnv** |
|---------|--------------|-------------------|--------------|
| Nested access (`config.db.host`) | ❌ Manual | ✅ | ✅ **Native** |
| Type casting (`cast=int`, `cast=bool`) | ❌ Manual | ✅ | ✅ **Built-in** |
| Defaults + casting | Basic | ✅ | ✅ **First-class** |
| Required keys validation | ❌ Manual | ✅ | ✅ `config.require()` |
| Environment detection | ❌ | Limited | ✅ `config.is_production` |
| Multiple sources (.env, TOML, JSON) | Limited | ✅ | ✅ **Native** |
| Zero dependencies | ✅ | ❌ | ✅ **Yes** |
| Modern Python API (3.10+) | ❌ | ✅ | ✅ **Yes** |

## Quick Start

```bash
pip install smartenv
```

```python
from smartenv import load

# Load from .env file
config = load(".env")

# Access values
config.get("DATABASE_URL")
config["db.host"]           # Dot notation for nested keys
config.db.host              # Attribute access!

# Type casting with defaults
port = config.get("PORT", default=8000, cast=int)
debug = config.get("DEBUG", cast=bool)
allowed = config.get("ALLOWED_HOSTS", cast=list)

# Validation
config.require("SECRET_KEY", "DATABASE_URL")

# Environment detection
if config.is_production:
    print("Running in production!")
```

## Installation

```bash
pip install smartenv
```

Requires Python 3.10+. Zero dependencies — only the standard library.

## Features

- **🔧 Multiple Sources**: Load from `.env`, `.toml`, `.json`, and environment variables with clear precedence
- **🌳 Nested Access**: `config.db.host`, `config["db.host"]`, `config.get("db.host")` — all work
- **🎯 Type Casting**: Built-in `bool`, `int`, `float`, `list`, `json` with custom caster support
- **🛡️ Validation**: `config.require("KEY")` with helpful error messages listing available keys
- **🌍 Environment Detection**: Automatic detection from `APP_ENV`, `ENVIRONMENT`, `FLASK_ENV`, etc.
- **💬 Clear Errors**: Exception messages tell you exactly what's wrong and where
- **📦 Zero Dependencies**: Pure standard library (uses `tomllib` in Python 3.11+)
- **🏷️ Full Typing**: Complete type hints with `py.typed` for IDE support

## Usage Examples

### Basic .env Loading

```python
from smartenv import load

# .env file:
# DATABASE_URL=postgres://localhost/mydb
# DEBUG=true
# PORT=8000

config = load(".env")
config.get("DATABASE_URL")  # "postgres://localhost/mydb"
config.get("DEBUG", cast=bool)  # True
config.get("PORT", cast=int)    # 8000
```

### Multiple Sources with Precedence

```python
# Precedence (highest to lowest):
# 1. Environment variables
# 2. .env files
# 3. TOML/JSON files

config = load(".env", "config.toml", "settings.json", env_prefix="APP_")
```

### Nested Configuration

```python
# config.toml:
# [database]
# host = "localhost"
# port = 5432
# [redis]
# url = "redis://localhost"

config = load("config.toml")
config["database.host"]     # "localhost"
config.database.host        # "localhost" (attribute access!)
config.database.port        # 5432
config.get("redis.url")     # "redis://localhost"
```

### Type Casting

```python
config.get("PORT", default=8000, cast=int)
config.get("DEBUG", cast=bool)
config.get("RATE", cast=float)
config.get("ALLOWED_HOSTS", cast=list)          # Splits on comma
config.get("ALLOWED_HOSTS", cast=list, separator=";")  # Custom separator
config.get("CONFIG_JSON", cast="json")          # Parse JSON string
config.get("CUSTOM", cast=lambda v: v.upper())  # Custom callable
```

### Convenience Methods

```python
config.get_bool("DEBUG")
config.get_int("PORT", default=8000)
config.get_float("RATE")
config.get_list("HOSTS")
config.get_json("SETTINGS")
config.get_str("NAME")
```

### Environment Detection

```python
config.environment        # "development" | "production" | "testing" | "staging"
config.is_production      # True/False
config.is_development     # True/False
config.is_testing         # True/False
config.is_staging         # True/False
```

### Validation

```python
# Single key
config.require("SECRET_KEY")

# Multiple keys
config.require("SECRET_KEY", "DATABASE_URL", "API_KEY")

# From list
config.require_all(["KEY1", "KEY2", "KEY3"])
```

### Environment Variable Prefix

```python
# Load only APP_* env vars, strip prefix
config = load(".env", env_prefix="APP_")

# APP_DATABASE_URL=postgres://... -> config["DATABASE_URL"]
# APP_DEBUG=true -> config["DEBUG"]
```

## Migration from python-dotenv

```python
# Before (python-dotenv)
from dotenv import load_dotenv
import os

load_dotenv()
database_url = os.getenv("DATABASE_URL")
port = int(os.getenv("PORT", "8000"))
debug = os.getenv("DEBUG", "false").lower() == "true"

# After (SmartEnv)
from smartenv import load

config = load(".env")
database_url = config.get("DATABASE_URL")
port = config.get("PORT", default=8000, cast=int)
debug = config.get("DEBUG", cast=bool)
```

## API Reference

### `load(*sources, env_prefix=None, environment=None)`

Main entry point. Loads configuration from multiple sources.

**Parameters:**
- `*sources`: Paths to `.env`, `.toml`, `.json` files
- `env_prefix`: Prefix for environment variables (e.g., `"APP_"`)
- `environment`: Override environment detection

**Returns:** `Config` object

### `Config` Class

#### Access Methods
- `config[key]` — Dictionary access (supports dot notation)
- `config.key` — Attribute access for nested namespaces
- `config.get(key, default=None, cast=None)` — Get with default and casting

#### Type-Specific Getters
- `get_bool(key, default=None)`
- `get_int(key, default=None)`
- `get_float(key, default=None)`
- `get_list(key, default=None, separator=",")`
- `get_json(key, default=None)`
- `get_str(key, default=None)`

#### Validation
- `require(*keys)` — Raise `MissingKeyError` if any key missing
- `require_all(keys)` — Same, from a list

#### Environment
- `environment` — Current environment name
- `is_production` / `is_development` / `is_testing` / `is_staging`

#### Utilities
- `to_dict()` — Plain dictionary copy
- `update(other)` — Merge with another dict (returns new Config)
- `with_prefix(prefix)` — Filter keys by prefix

### Exceptions
- `ConfigError` — Base exception
- `MissingKeyError` — Required key not found (lists available keys)
- `CastingError` — Type casting failed (shows value and expected type)
- `ParseError` — File parsing failed (shows file and line number)

## Project Structure

```
your-project/
├── .env              # Environment variables
├── config.toml       # Structured configuration
├── settings.json     # JSON configuration
└── main.py
```

## Contributing

Contributions welcome! Please read our contributing guidelines first.

```bash
git clone https://github.com/smartenv/smartenv
cd smartenv
pip install -e ".[dev]"
pytest
```

## License

MIT License — see [LICENSE](LICENSE) for details.

---

**Built with care** — SmartEnv aims to be the config loader you wish already existed.