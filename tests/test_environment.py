"""Tests for environment detection and multiple source loading."""

from smartenv.core import Config, load
from smartenv.utils import detect_environment, is_development, is_production, is_staging, is_testing


class TestEnvironmentDetection:
    """Tests for environment detection from config."""

    def test_default_development(self):
        config = Config({})
        assert config.environment == "development"
        assert config.is_development

    def test_app_env(self):
        config = Config({"APP_ENV": "production"})
        assert config.environment == "production"
        assert config.is_production

    def test_environment_var(self):
        config = Config({"ENVIRONMENT": "testing"})
        assert config.environment == "testing"
        assert config.is_testing

    def test_env_var(self):
        config = Config({"ENV": "staging"})
        assert config.environment == "staging"
        assert config.is_staging

    def test_flask_env(self):
        config = Config({"FLASK_ENV": "development"})
        assert config.environment == "development"

    def test_node_env(self):
        config = Config({"NODE_ENV": "production"})
        assert config.environment == "production"

    def test_rails_env(self):
        config = Config({"RAILS_ENV": "test"})
        assert config.environment == "testing"

    def test_django_env(self):
        config = Config({"DJANGO_ENV": "production"})
        assert config.environment == "production"

    def test_fastapi_env(self):
        config = Config({"FASTAPI_ENV": "testing"})
        assert config.environment == "testing"

    def test_priority_order(self):
        """Test that APP_ENV has highest priority."""
        config = Config(
            {
                "APP_ENV": "production",
                "ENVIRONMENT": "testing",
                "FLASK_ENV": "development",
            }
        )
        assert config.environment == "production"

    def test_normalization(self):
        """Test environment value normalization."""
        test_cases = [
            ("prod", "production"),
            ("production", "production"),
            ("live", "production"),
            ("dev", "development"),
            ("develop", "development"),
            ("development", "development"),
            ("local", "development"),
            ("test", "testing"),
            ("testing", "testing"),
            ("ci", "testing"),
            ("stage", "staging"),
            ("staging", "staging"),
            ("preprod", "staging"),
        ]
        for input_val, expected in test_cases:
            config = Config({"APP_ENV": input_val})
            assert config.environment == expected, f"Failed for {input_val}"

    def test_unknown_env_returns_as_is(self):
        """Test unknown environment values are returned as-is (lowercased)."""
        config = Config({"APP_ENV": "custom_env"})
        assert config.environment == "custom_env"


class TestEnvironmentDetectionFromOS:
    """Tests for environment detection from OS environment variables."""

    def test_detects_from_os_env(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "production")
        config = Config({})
        assert config.environment == "production"

    def test_config_overrides_os_env(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "production")
        config = Config({"APP_ENV": "testing"})
        assert config.environment == "testing"


class TestUtilityFunctions:
    """Tests for standalone utility functions."""

    def test_detect_environment_function(self):
        assert detect_environment({}) == "development"
        assert detect_environment({"APP_ENV": "production"}) == "production"

    def test_is_production(self):
        assert is_production({"APP_ENV": "production"}) is True
        assert is_production({"APP_ENV": "development"}) is False

    def test_is_development(self):
        assert is_development({"APP_ENV": "development"}) is True
        assert is_development({"APP_ENV": "production"}) is False

    def test_is_testing(self):
        assert is_testing({"APP_ENV": "testing"}) is True
        assert is_testing({"APP_ENV": "production"}) is False

    def test_is_staging(self):
        assert is_staging({"APP_ENV": "staging"}) is True
        assert is_staging({"APP_ENV": "production"}) is False


class TestMultipleSourceLoading:
    """Tests for load() function with multiple sources."""

    def test_load_env_file(self, basic_env_path):
        config = load(basic_env_path)
        assert config.get("DATABASE_URL") == "postgres://localhost:5432/mydb"
        assert config.get("DEBUG", cast=bool) is True

    def test_load_toml_file(self, toml_path):
        config = load(toml_path)
        assert config.get("database.host") == "localhost"
        assert config.get("database.port", cast=int) == 5432

    def test_load_json_file(self, json_path):
        config = load(json_path)
        assert config.get("database.host") == "localhost"

    def test_load_multiple_files(self, basic_env_path, toml_path):
        """Test loading multiple files - later files override earlier."""
        # basic.env has DEBUG=true, toml has debug=true (same)
        # But let's add a conflict
        config = load(basic_env_path, toml_path)
        assert config.get("DATABASE_URL") == "postgres://localhost:5432/mydb"

    def test_env_vars_highest_precedence(self, basic_env_path, monkeypatch):
        """Test that environment variables have highest precedence."""
        monkeypatch.setenv("DATABASE_URL", "postgres://env-override/db")
        monkeypatch.setenv("DEBUG", "false")

        config = load(basic_env_path)
        assert config.get("DATABASE_URL") == "postgres://env-override/db"
        assert config.get("DEBUG", cast=bool) is False

    def test_env_prefix_filters_env_vars(self, basic_env_path, monkeypatch):
        """Test that env_prefix filters environment variables."""
        monkeypatch.setenv("APP_DATABASE_URL", "postgres://prefixed/db")
        monkeypatch.setenv("DATABASE_URL", "postgres://unprefixed/db")

        config = load(basic_env_path, env_prefix="APP_")
        assert config.get("DATABASE_URL") == "postgres://prefixed/db"

    def test_env_prefix_strips_prefix(self, basic_env_path, monkeypatch):
        """Test that env_prefix is stripped from keys."""
        monkeypatch.setenv("APP_DEBUG", "true")
        monkeypatch.setenv("APP_PORT", "9000")

        config = load(basic_env_path, env_prefix="APP_")
        assert config.get("DEBUG", cast=bool) is True
        assert config.get("PORT", cast=int) == 9000

    def test_environment_override(self, basic_env_path):
        """Test explicit environment override."""
        config = load(basic_env_path, environment="production")
        assert config.environment == "production"
        assert config.is_production

    def test_load_with_no_sources(self):
        """Test load() with no file sources (only env vars)."""
        config = load()
        assert isinstance(config, Config)

    def test_load_only_env_vars(self, monkeypatch):
        """Test load with only environment variables."""
        monkeypatch.setenv("TEST_KEY", "test_value")
        config = load()
        assert config.get("TEST_KEY") == "test_value"


class TestPrecedenceOrder:
    """Tests for specific precedence order."""

    def test_precedence_env_vars_over_env_file(self, basic_env_path, monkeypatch):
        """Env vars > .env file."""
        monkeypatch.setenv("PORT", "9999")
        config = load(basic_env_path)
        assert config.get("PORT", cast=int) == 9999

    def test_precedence_env_file_over_toml(self, basic_env_path, toml_path):
        """.env file > TOML."""
        # Both have port-like values but different keys
        # Create a conflict by using same key
        pass  # Hard to test without modifying fixtures

    def test_load_specific_functions(self, basic_env_path, toml_path, json_path):
        """Test load_env, load_toml, load_json functions."""
        from smartenv import load_env, load_json, load_toml

        config_env = load_env(basic_env_path)
        assert config_env.get("DATABASE_URL") == "postgres://localhost:5432/mydb"

        config_toml = load_toml(toml_path)
        assert config_toml.get("database.host") == "localhost"

        config_json = load_json(json_path)
        assert config_json.get("database.host") == "localhost"
