"""Shared test fixtures and configuration."""

import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from smartenv.core import Config


@pytest.fixture
def basic_env_path() -> Path:
    """Path to basic .env fixture."""
    return Path(__file__).parent / "fixtures" / "basic.env"


@pytest.fixture
def edge_cases_env_path() -> Path:
    """Path to edge cases .env fixture."""
    return Path(__file__).parent / "fixtures" / "edge_cases.env"


@pytest.fixture
def toml_path() -> Path:
    """Path to TOML fixture."""
    return Path(__file__).parent / "fixtures" / "config.toml"


@pytest.fixture
def json_path() -> Path:
    """Path to JSON fixture."""
    return Path(__file__).parent / "fixtures" / "settings.json"


@pytest.fixture
def temp_env_file() -> Generator[Path, None, None]:
    """Create a temporary .env file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("TEMP_KEY=temp_value\n")
        temp_path = Path(f.name)
    yield temp_path
    temp_path.unlink(missing_ok=True)


@pytest.fixture
def sample_env_content() -> str:
    """Sample .env content for testing."""
    return """DATABASE_URL=postgres://localhost/mydb
DEBUG=true
PORT=8000
SECRET_KEY=test-secret
EMPTY=
QUOTED="hello world"
SINGLE='single quoted'
WITH_SPACES = value with spaces
EXPORT_VAR=exported
# Comment
ANOTHER=value"""


@pytest.fixture
def sample_config_dict() -> dict:
    """Sample configuration dictionary."""
    return {
        "DATABASE_URL": "postgres://localhost/mydb",
        "DEBUG": "true",
        "PORT": "8000",
        "SECRET_KEY": "test-secret",
        "db.host": "localhost",
        "db.port": "5432",
        "redis.url": "redis://localhost:6379",
    }


@pytest.fixture
def config(sample_config_dict) -> Config:
    """Create a Config instance with sample data."""
    return Config(sample_config_dict)


@pytest.fixture(autouse=True)
def clean_env() -> Generator[None, None, None]:
    """Clean environment variables before and after each test."""
    # Store original env
    original_env = dict(os.environ)
    # Clear test-related env vars
    test_keys = [k for k in os.environ if k.startswith(("TEST_", "APP_", "SMARTENV_"))]
    for key in test_keys:
        os.environ.pop(key, None)
    yield
    # Restore
    os.environ.clear()
    os.environ.update(original_env)
