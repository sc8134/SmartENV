"""Regression tests for issues found during review."""

import copy
import pickle
import typing
from pathlib import Path

import pytest

import smartenv
from smartenv import load
from smartenv.core import Config
from smartenv.exceptions import MissingKeyError
from smartenv.parsers.env import parse_env_string


class TestImportCompatibility:
    """Annotations must resolve on every supported Python version."""

    def test_config_get_annotations_resolve(self):
        # `type | str | callable` raised TypeError at import time on <3.14
        hints = typing.get_type_hints(Config.get)
        assert "cast" in hints

    def test_convenience_getter_annotations_resolve(self):
        assert typing.get_type_hints(Config.get_list)
        assert typing.get_type_hints(Config.get_json)

    def test_py_typed_marker_exists(self):
        package_dir = Path(smartenv.__file__).parent
        assert (package_dir / "py.typed").is_file()


class TestCopyAndPickle:
    """Config must survive copy, deepcopy, and pickling."""

    @pytest.fixture
    def config(self):
        return Config({"A": "1", "db.host": "localhost"}, source_files=["a.env"])

    def test_copy_roundtrip(self, config):
        restored = copy.copy(config)
        assert restored.to_dict() == {"A": "1", "db.host": "localhost"}

    def test_deepcopy_roundtrip(self, config):
        restored = copy.deepcopy(config)
        assert restored.to_dict() == {"A": "1", "db.host": "localhost"}

    def test_pickle_roundtrip(self, config):
        restored = pickle.loads(pickle.dumps(config))
        assert restored.get("A") == "1"
        assert restored.db.host == "localhost"


class TestFilePrecedence:
    """File precedence follows format (.env > TOML > JSON), not argument order."""

    def test_env_file_overrides_toml_in_either_order(self, tmp_path):
        env_path = tmp_path / "a.env"
        env_path.write_text("SMARTENV_PREC=from_env\n", encoding="utf-8")
        toml_path = tmp_path / "a.toml"
        toml_path.write_text('SMARTENV_PREC = "from_toml"\n', encoding="utf-8")

        assert load(env_path, toml_path).get("SMARTENV_PREC") == "from_env"
        assert load(toml_path, env_path).get("SMARTENV_PREC") == "from_env"

    def test_toml_overrides_json_in_either_order(self, tmp_path):
        toml_path = tmp_path / "a.toml"
        toml_path.write_text('SMARTENV_PREC = "from_toml"\n', encoding="utf-8")
        json_path = tmp_path / "a.json"
        json_path.write_text('{"SMARTENV_PREC": "from_json"}', encoding="utf-8")

        assert load(toml_path, json_path).get("SMARTENV_PREC") == "from_toml"
        assert load(json_path, toml_path).get("SMARTENV_PREC") == "from_toml"

    def test_same_format_later_argument_wins(self, tmp_path):
        first = tmp_path / "first.env"
        first.write_text("SMARTENV_PREC=first\n", encoding="utf-8")
        second = tmp_path / "second.env"
        second.write_text("SMARTENV_PREC=second\n", encoding="utf-8")

        assert load(first, second).get("SMARTENV_PREC") == "second"


class TestNullValues:
    """A stored null is present, not missing."""

    def test_json_null_is_a_present_value(self, tmp_path):
        path = tmp_path / "settings.json"
        path.write_text('{"NULL_KEY": null}', encoding="utf-8")

        config = load(path)

        assert "NULL_KEY" in config
        assert config["NULL_KEY"] is None
        assert config.get("NULL_KEY") is None
        assert config.get("NULL_KEY", default="fallback") is None
        config.require("NULL_KEY")

    def test_missing_key_still_uses_default(self):
        config = Config({})

        assert config.get("MISSING", default="fallback") == "fallback"
        with pytest.raises(KeyError):
            _ = config["MISSING"]
        with pytest.raises(MissingKeyError):
            config.require("MISSING")


class TestEnvParserBom:
    """UTF-8 BOM (common on Windows) must not break parsing."""

    def test_bom_prefixed_key_in_string(self):
        assert parse_env_string("\ufeffKEY=value") == {"KEY": "value"}

    def test_bom_prefixed_comment_in_string(self):
        assert parse_env_string("\ufeff# comment\nKEY=value") == {"KEY": "value"}

    def test_bom_in_file(self, tmp_path):
        path = tmp_path / "bom.env"
        path.write_bytes("\ufeffSMARTENV_BOM=value\n".encode("utf-8"))

        assert load(path).get("SMARTENV_BOM") == "value"


class TestQuotedBackslashes:
    """Trailing backslashes before a closing quote are handled by parity."""

    def test_double_quoted_value_ending_in_backslash(self):
        # file content: KEY="abc\\"
        assert parse_env_string('KEY="abc\\\\"')["KEY"] == "abc\\"

    def test_single_quoted_value_ending_in_backslash(self):
        # file content: KEY='abc\\'
        assert parse_env_string("KEY='abc\\\\'")["KEY"] == "abc\\"

    def test_escaped_closing_quote_stays_literal(self):
        # file content: KEY="abc\"
        assert parse_env_string('KEY="abc\\"')["KEY"] == 'abc"'


class TestRequireMessages:
    """require() reports every missing key, not just the first."""

    def test_multiple_missing_keys_are_all_reported(self):
        config = Config({"PRESENT": "1"})

        with pytest.raises(MissingKeyError) as exc_info:
            config.require("MISSING_A", "MISSING_B")

        message = str(exc_info.value)
        assert "MISSING_A" in message
        assert "MISSING_B" in message
