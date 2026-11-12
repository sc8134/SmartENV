"""Tests for the Config class."""

import pytest

from smartenv.core import Config
from smartenv.exceptions import CastingError, MissingKeyError


class TestConfigBasicAccess:
    """Tests for basic dictionary-like access."""

    def test_get_item(self, config):
        assert config["DATABASE_URL"] == "postgres://localhost/mydb"
        assert config["DEBUG"] == "true"

    def test_get_missing_key_raises(self, config):
        with pytest.raises(KeyError):
            _ = config["NONEXISTENT"]

    def test_contains(self, config):
        assert "DATABASE_URL" in config
        assert "NONEXISTENT" not in config

    def test_iter(self, config):
        keys = list(config)
        assert "DATABASE_URL" in keys
        assert "DEBUG" in keys

    def test_len(self, config):
        assert len(config) == 7

    def test_get_method(self, config):
        assert config.get("DATABASE_URL") == "postgres://localhost/mydb"
        assert config.get("NONEXISTENT") is None
        assert config.get("NONEXISTENT", "default") == "default"

    def test_get_with_cast(self, config):
        assert config.get("PORT", cast=int) == 8000
        assert config.get("DEBUG", cast=bool) is True

    def test_get_with_default_and_cast(self, config):
        assert config.get("MISSING", default=999, cast=int) == 999
        assert config.get("MISSING", default=False, cast=bool) is False


class TestConfigNestedAccess:
    """Tests for nested key access."""

    def test_dot_notation_get(self, config):
        assert config.get("db.host") == "localhost"
        assert config.get("db.port") == "5432"
        assert config.get("redis.url") == "redis://localhost:6379"

    def test_dot_notation_bracket_access(self, config):
        assert config["db.host"] == "localhost"
        assert config["db.port"] == "5432"

    def test_nested_missing_returns_none(self, config):
        assert config.get("db.nonexistent") is None
        assert config.get("nonexistent.key") is None

    def test_attribute_access_namespace(self, config):
        # Access nested namespace via attribute
        db = config.db
        assert isinstance(db, Config)
        assert db.get("host") == "localhost"
        assert db.get("port") == "5432"

    def test_attribute_access_deep_namespace(self, config):
        # This should work if we have deeper nesting
        redis = config.redis
        assert isinstance(redis, Config)
        assert redis.get("url") == "redis://localhost:6379"

    def test_attribute_access_direct_key(self, config):
        # Direct keys should also work as attributes
        assert config.DATABASE_URL == "postgres://localhost/mydb"
        assert config.DEBUG == "true"

    def test_attribute_access_missing_raises(self, config):
        with pytest.raises(AttributeError):
            _ = config.NONEXISTENT


class TestConfigCasting:
    """Tests for type casting in Config.get."""

    def test_cast_int(self, config):
        assert config.get("PORT", cast=int) == 8000

    def test_cast_bool(self, config):
        assert config.get("DEBUG", cast=bool) is True

    def test_cast_float(self, config):
        # Add a float value
        config_with_float = Config({**config.to_dict(), "RATE": "3.14"})
        assert config_with_float.get("RATE", cast=float) == 3.14

    def test_cast_list(self, config):
        config_with_list = Config({**config.to_dict(), "HOSTS": "a,b,c"})
        assert config_with_list.get("HOSTS", cast=list) == ["a", "b", "c"]

    def test_cast_json(self, config):
        config_with_json = Config({**config.to_dict(), "SETTINGS": '{"key": "value"}'})
        assert config_with_json.get("SETTINGS", cast="json") == {"key": "value"}

    def test_cast_custom_callable(self, config):
        result = config.get("DATABASE_URL", cast=str.upper)
        assert result == "POSTGRES://LOCALHOST/MYDB"

    def test_cast_error_raises_casting_error(self, config):
        with pytest.raises(CastingError):
            config.get("DEBUG", cast=int)  # "true" can't be cast to int

    def test_convenience_methods(self, config):
        assert config.get_int("PORT") == 8000
        assert config.get_bool("DEBUG") is True
        assert config.get_str("DATABASE_URL") == "postgres://localhost/mydb"


class TestConfigValidation:
    """Tests for required key validation."""

    def test_require_single_key(self, config):
        config.require("SECRET_KEY")  # Should not raise
        assert True

    def test_require_multiple_keys(self, config):
        config.require("SECRET_KEY", "DATABASE_URL")  # Should not raise

    def test_require_missing_key_raises(self, config):
        with pytest.raises(MissingKeyError) as exc_info:
            config.require("NONEXISTENT")
        assert "NONEXISTENT" in str(exc_info.value)
        assert "Available keys" in str(exc_info.value)

    def test_require_multiple_missing_raises_first(self, config):
        with pytest.raises(MissingKeyError) as exc_info:
            config.require("MISSING1", "MISSING2")
        assert "MISSING1" in str(exc_info.value)

    def test_require_all_from_list(self, config):
        config.require_all(["SECRET_KEY", "DATABASE_URL"])

    def test_require_all_missing_raises(self, config):
        with pytest.raises(MissingKeyError):
            config.require_all(["MISSING1", "MISSING2"])


class TestConfigEnvironment:
    """Tests for environment detection."""

    def test_default_environment(self):
        config = Config({"FOO": "bar"})
        assert config.environment == "development"
        assert config.is_development
        assert not config.is_production
        assert not config.is_testing

    def test_production_environment(self):
        config = Config({"APP_ENV": "production"})
        assert config.environment == "production"
        assert config.is_production
        assert not config.is_development

    def test_testing_environment(self):
        config = Config({"ENVIRONMENT": "testing"})
        assert config.environment == "testing"
        assert config.is_testing

    def test_staging_environment(self):
        config = Config({"FLASK_ENV": "staging"})
        assert config.environment == "staging"
        assert config.is_staging

    def test_environment_normalization(self):
        config = Config({"APP_ENV": "prod"})
        assert config.environment == "production"

        config = Config({"APP_ENV": "dev"})
        assert config.environment == "development"

    def test_env_override(self):
        config = Config({"APP_ENV": "production"})
        config2 = config.update({"APP_ENV": "testing"})
        assert config2.environment == "testing"


class TestConfigUtilities:
    """Tests for utility methods."""

    def test_to_dict(self, config):
        d = config.to_dict()
        assert isinstance(d, dict)
        assert d["DATABASE_URL"] == "postgres://localhost/mydb"
        # Modifying dict shouldn't affect config
        d["NEW"] = "value"
        assert "NEW" not in config

    def test_update(self, config):
        new_config = config.update({"NEW_KEY": "new_value", "DEBUG": "false"})
        assert new_config.get("NEW_KEY") == "new_value"
        assert new_config.get("DEBUG") == "false"
        # Original unchanged
        assert config.get("DEBUG") == "true"

    def test_with_prefix(self):
        config = Config(
            {
                "APP_DATABASE_URL": "postgres://...",
                "APP_DEBUG": "true",
                "OTHER_KEY": "value",
            }
        )
        prefixed = config.with_prefix("APP_")
        assert prefixed.get("DATABASE_URL") == "postgres://..."
        assert prefixed.get("DEBUG") == "true"
        assert "OTHER_KEY" not in prefixed

    def test_repr(self, config):
        repr_str = repr(config)
        assert "Config" in repr_str
        assert "7 keys" in repr_str


class TestConfigEdgeCases:
    """Tests for edge cases."""

    def test_empty_config(self):
        config = Config({})
        assert len(config) == 0
        assert config.get("ANY") is None

    def test_none_values(self):
        config = Config({"KEY": None})
        assert config.get("KEY") is None
        assert config["KEY"] is None
        assert "KEY" in config
        # An explicitly stored None is a present value, not a missing key
        assert config.get("KEY", default="default") is None
        config.require("KEY")

    def test_numeric_keys(self):
        config = Config({"123": "value"})
        assert config.get("123") == "value"

    def test_keys_with_special_chars(self):
        config = Config({"key-with-dashes": "value", "key.with.dots": "value"})
        assert config.get("key-with-dashes") == "value"
        assert config.get("key.with.dots") == "value"
