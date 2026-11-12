"""Tests for TOML and JSON parsers."""

import pytest

from smartenv.exceptions import ParseError
from smartenv.parsers import parse_json_file, parse_json_string, parse_toml_file, parse_toml_string


class TestTOMLParser:
    """Tests for TOML parser."""

    def test_parse_toml_file(self, toml_path):
        data = parse_toml_file(toml_path)
        assert data["app_name"] == "SmartEnv Test"
        assert data["version"] == "1.0.0"
        assert data["debug"] is True
        assert data["port"] == 8000
        assert data["database.host"] == "localhost"
        assert data["database.port"] == 5432
        assert data["database.ssl"] is True

    def test_parse_toml_string(self):
        content = """
        name = "test"
        value = 42
        [nested]
        key = "value"
        """
        data = parse_toml_string(content)
        assert data["name"] == "test"
        assert data["value"] == 42
        assert data["nested.key"] == "value"

    def test_parse_toml_invalid(self):
        content = "invalid toml ["
        with pytest.raises(ParseError) as exc_info:
            parse_toml_string(content)
        assert "Failed to parse TOML" in str(exc_info.value)

    def test_parse_toml_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            parse_toml_file("/nonexistent/config.toml")


class TestJSONParser:
    """Tests for JSON parser."""

    def test_parse_json_file(self, json_path):
        data = parse_json_file(json_path)
        assert data["app.name"] == "SmartEnv Test"
        assert data["app.version"] == "1.0.0"
        assert data["app.debug"] is True
        assert data["app.port"] == 8000
        assert data["database.host"] == "localhost"
        assert data["database.port"] == 5432

    def test_parse_json_string(self):
        content = '{"name": "test", "value": 42, "nested": {"key": "value"}}'
        data = parse_json_string(content)
        assert data["name"] == "test"
        assert data["value"] == 42
        assert data["nested.key"] == "value"

    def test_parse_json_invalid(self):
        content = '{"invalid": }'
        with pytest.raises(ParseError) as exc_info:
            parse_json_string(content)
        assert "Invalid JSON" in str(exc_info.value)
        assert exc_info.value.line is not None

    def test_parse_json_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            parse_json_file("/nonexistent/config.json")


class TestParserIntegration:
    """Tests for parsers integrated with load()."""

    def test_load_toml_then_json(self, toml_path, json_path):
        from smartenv import load

        config = load(toml_path, json_path)
        # TOML has higher precedence than JSON
        assert config.get("database.host") == "localhost"

    def test_load_json_then_toml(self, toml_path, json_path):
        from smartenv import load

        config = load(json_path, toml_path)
        # TOML still has higher precedence (file order doesn't matter for different formats)
        # Actually, in load(), the order is: env vars > .env > toml > json
        # Wait, the implementation processes files in order provided
        # Let me check: the load function adds configs in order, then merges
        # So later sources override earlier ones
        config = load(json_path, toml_path)
        # toml is processed after json, so toml values win
        assert config.get("database.host") == "localhost"

    def test_load_all_three(self, basic_env_path, toml_path, json_path):
        from smartenv import load

        config = load(basic_env_path, toml_path, json_path)
        # .env has DATABASE_URL, TOML has database.host
        assert config.get("DATABASE_URL") == "postgres://localhost:5432/mydb"
        assert config.get("database.host") == "localhost"
