#!/usr/bin/env python
"""Basic usage examples for SmartEnv."""

from smartenv import load, Config


def main():
    print("=== SmartEnv Basic Usage Examples ===\n")

    # Example 1: Load from .env file
    print("1. Loading from .env file:")
    # Create a sample .env for demo
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("""DATABASE_URL=postgres://localhost:5432/myapp
DEBUG=true
PORT=8000
SECRET_KEY=dev-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
RATE_LIMIT=100.5
FEATURE_FLAGS={"new_ui": true, "beta": false}
""")
        env_path = f.name

    try:
        config = load(env_path)

        print(f"   DATABASE_URL: {config.get('DATABASE_URL')}")
        print(f"   DEBUG: {config.get('DEBUG', cast=bool)}")
        print(f"   PORT: {config.get('PORT', default=3000, cast=int)}")
        print(f"   SECRET_KEY: {config.get('SECRET_KEY')}")
        print(f"   ALLOWED_HOSTS: {config.get('ALLOWED_HOSTS', cast=list)}")
        print(f"   RATE_LIMIT: {config.get('RATE_LIMIT', cast=float)}")
        print(f"   FEATURE_FLAGS: {config.get('FEATURE_FLAGS', cast='json')}")
    finally:
        os.unlink(env_path)

    # Example 2: Nested configuration from TOML
    print("\n2. Nested configuration from TOML:")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write("""
[database]
host = "localhost"
port = 5432
name = "myapp"
ssl = true

[redis]
url = "redis://localhost:6379"
pool_size = 10

[app]
name = "MyApp"
version = "1.0.0"
debug = true
""")
        toml_path = f.name

    try:
        config = load(toml_path)

        # Dot notation access
        print(f"   config['database.host']: {config['database.host']}")
        print(f"   config.get('database.port'): {config.get('database.port')}")

        # Attribute access (namespace)
        print(f"   config.database.host: {config.database.host}")
        print(f"   config.database.port: {config.database.port}")
        print(f"   config.redis.url: {config.redis.url}")

        # Casting through namespace
        print(f"   config.database.port (cast=int): {config.database.get('port', cast=int)}")
        print(f"   config.database.ssl (cast=bool): {config.database.get('ssl', cast=bool)}")
    finally:
        os.unlink(toml_path)

    # Example 3: Multiple sources with precedence
    print("\n3. Multiple sources with precedence:")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("APP_NAME=from-env-file\nDEBUG=false\n")
        env_path2 = f.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write("APP_NAME = \"from-toml\"\nDEBUG = true\n")
        toml_path2 = f.name

    try:
        # Set environment variable (highest precedence)
        os.environ["APP_NAME"] = "from-env-var"
        os.environ["DEBUG"] = "true"

        config = load(env_path2, toml_path2)

        print(f"   APP_NAME (env var wins): {config.get('APP_NAME')}")
        print(f"   DEBUG (env var wins): {config.get('DEBUG', cast=bool)}")
    finally:
        os.unlink(env_path2)
        os.unlink(toml_path2)
        os.environ.pop("APP_NAME", None)
        os.environ.pop("DEBUG", None)

    # Example 4: Environment detection
    print("\n4. Environment detection:")
    config = Config({"APP_ENV": "production"})
    print(f"   Environment: {config.environment}")
    print(f"   Is production: {config.is_production}")
    print(f"   Is development: {config.is_development}")

    config = Config({"FLASK_ENV": "testing"})
    print(f"   Environment (from FLASK_ENV): {config.environment}")
    print(f"   Is testing: {config.is_testing}")

    # Example 5: Validation
    print("\n5. Required key validation:")
    config = Config({"SECRET_KEY": "secret", "DATABASE_URL": "postgres://..."})
    try:
        config.require("SECRET_KEY", "DATABASE_URL")
        print("   All required keys present!")
    except Exception as e:
        print(f"   Error: {e}")

    try:
        config.require("MISSING_KEY")
    except Exception as e:
        print(f"   Missing key error: {e}")

    # Example 6: Environment variable prefix
    print("\n6. Environment variable prefix:")
    os.environ["MYAPP_DATABASE_URL"] = "postgres://prefixed/db"
    os.environ["MYAPP_DEBUG"] = "true"
    os.environ["OTHER_VAR"] = "ignored"

    config = load(env_prefix="MYAPP_")
    print(f"   DATABASE_URL (prefixed): {config.get('DATABASE_URL')}")
    print(f"   DEBUG (prefixed): {config.get('DEBUG', cast=bool)}")
    print(f"   OTHER_VAR (not prefixed): {config.get('OTHER_VAR')}")

    os.environ.pop("MYAPP_DATABASE_URL", None)
    os.environ.pop("MYAPP_DEBUG", None)
    os.environ.pop("OTHER_VAR", None)

    # Example 7: Convenience methods
    print("\n7. Convenience methods:")
    config = Config({"PORT": "8000", "DEBUG": "true", "RATE": "3.14", "HOSTS": "a,b,c"})
    print(f"   get_int('PORT'): {config.get_int('PORT')}")
    print(f"   get_bool('DEBUG'): {config.get_bool('DEBUG')}")
    print(f"   get_float('RATE'): {config.get_float('RATE')}")
    print(f"   get_list('HOSTS'): {config.get_list('HOSTS')}")
    print(f"   get_str('PORT'): {config.get_str('PORT')}")

    print("\n=== All examples completed ===")


if __name__ == "__main__":
    main()