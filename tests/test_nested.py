"""Tests for nested configuration access."""

import pytest

from smartenv.core import Config
from smartenv.parsers import parse_toml_string, parse_json_string


class TestNestedAccess:
    """Tests for nested key access patterns."""

    def test_simple_nested_dict(self):
        """Test nested access with flat dict using dot notation."""
        data = {
            "database.host": "localhost",
            "database.port": 5432,
            "database.name": "myapp",
            "redis.url": "redis://localhost",
        }
        config = Config(data)

        assert config.get("database.host") == "localhost"
        assert config.get("database.port") == 5432
        assert config["database.name"] == "myapp"

    def test_nested_namespace_attribute_access(self):
        """Test attribute access for nested namespaces."""
        data = {
            "database.host": "localhost",
            "database.port": 5432,
            "redis.url": "redis://localhost",
        }
        config = Config(data)

        db = config.database
        assert isinstance(db, Config)
        assert db.get("host") == "localhost"
        assert db.get("port") == 5432

        redis = config.redis
        assert redis.get("url") == "redis://localhost"

    def test_deeply_nested(self):
        """Test deeply nested keys."""
        data = {
            "app.database.primary.host": "primary.db",
            "app.database.primary.port": 5432,
            "app.database.replica.host": "replica.db",
            "app.cache.redis.url": "redis://cache",
        }
        config = Config(data)

        # Direct access
        assert config.get("app.database.primary.host") == "primary.db"

        # Namespace access
        primary = config.app.database.primary
        assert primary.get("host") == "primary.db"
        assert primary.get("port") == 5432

    def test_nested_with_cast(self):
        """Test casting with nested keys."""
        data = {
            "database.port": "5432",
            "database.ssl": "true",
            "database.pool_size": "10",
        }
        config = Config(data)

        assert config.get("database.port", cast=int) == 5432
        assert config.get("database.ssl", cast=bool) is True
        assert config.get("database.pool_size", cast=int) == 10

    def test_nested_namespace_with_cast(self):
        """Test casting through nested namespace."""
        data = {
            "database.port": "5432",
            "database.ssl": "true",
        }
        config = Config(data)

        db = config.database
        assert db.get("port", cast=int) == 5432
        assert db.get("ssl", cast=bool) is True

    def test_mixed_flat_and_nested(self):
        """Test config with both flat and nested keys."""
        data = {
            "APP_NAME": "MyApp",
            "DEBUG": "true",
            "database.host": "localhost",
            "database.port": "5432",
        }
        config = Config(data)

        assert config.get("APP_NAME") == "MyApp"
        assert config.get("DEBUG", cast=bool) is True
        assert config.get("database.host") == "localhost"

    def test_nested_require(self):
        """Test require with nested keys."""
        data = {
            "database.host": "localhost",
            "database.port": "5432",
            "redis.url": "redis://localhost",
        }
        config = Config(data)

        config.require("database.host", "redis.url")  # Should not raise

        with pytest.raises(Exception):  # MissingKeyError
            config.require("database.host", "database.missing")


class TestTOMLNestedParsing:
    """Tests for TOML nested structure parsing."""

    def test_toml_parsing_creates_nested_keys(self, toml_path):
        from smartenv.parsers import parse_toml_file
        data = parse_toml_file(toml_path)

        assert "database.host" in data
        assert data["database.host"] == "localhost"
        assert data["database.port"] == 5432
        assert data["database.name"] == "myapp"
        assert data["database.ssl"] is True
        assert "redis.url" in data
        assert data["redis.url"] == "redis://localhost:6379"

    def test_toml_string_parsing(self):
        toml_content = """
        [database]
        host = "localhost"
        port = 5432
        
        [server]
        host = "0.0.0.0"
        port = 8000
        """
        data = parse_toml_string(toml_content)
        assert data["database.host"] == "localhost"
        assert data["database.port"] == 5432
        assert data["server.host"] == "0.0.0.0"
        assert data["server.port"] == 8000


class TestJSONNestedParsing:
    """Tests for JSON nested structure parsing."""

    def test_json_parsing_creates_nested_keys(self, json_path):
        from smartenv.parsers import parse_json_file
        data = parse_json_file(json_path)

        assert "database.host" in data
        assert data["database.host"] == "localhost"
        assert data["database.port"] == 5432

    def test_json_string_parsing(self):
        json_content = '{"database": {"host": "localhost", "port": 5432}, "server": {"host": "0.0.0.0"}}'
        data = parse_json_string(json_content)
        assert data["database.host"] == "localhost"
        assert data["database.port"] == 5432
        assert data["server.host"] == "0.0.0.0"


class TestLoadWithNestedFiles:
    """Tests for load() function with nested file formats."""

    def test_load_toml_creates_nested_config(self, toml_path):
        from smartenv import load
        config = load(toml_path)

        assert config.get("database.host") == "localhost"
        assert config.database.host == "localhost"
        assert config.database.port == 5432

    def test_load_json_creates_nested_config(self, json_path):
        from smartenv import load
        config = load(json_path)

        assert config.get("database.host") == "localhost"
        assert config.database.host == "localhost"

    def test_load_multiple_sources_merges_nested(self, toml_path, json_path):
        from smartenv import load
        # Both have database.host - JSON should override (lower precedence)
        # Actually load order: env vars > .env > toml > json
        # So TOML should win over JSON
        config = load(toml_path, json_path)

        # Both have same values, so either works
        assert config.get("database.host") == "localhost"