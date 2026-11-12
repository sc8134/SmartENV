"""Edge-case tests that exercise error paths and defensive branches."""

import pytest

from smartenv import load
from smartenv.casting import cast_float, cast_json, cast_list, cast_value, get_caster
from smartenv.core import Config
from smartenv.exceptions import CastingError, MissingKeyError, ParseError
from smartenv.parsers import (
    parse_json_file,
    parse_json_string,
    parse_toml_file,
    parse_toml_string,
)
from smartenv.parsers.env import parse_env_string
from smartenv.utils import (
    filter_by_prefix,
    get_env_prefix,
    is_development,
    is_production,
    is_staging,
    is_testing,
    merge_configs,
    parse_env_vars,
)


class TestCastingErrorPaths:
    """Unsupported types and failing custom casters surface as CastingError."""

    def test_float_rejects_unsupported_type(self):
        with pytest.raises(CastingError):
            cast_float([1])

    def test_list_rejects_unsupported_type(self):
        with pytest.raises(CastingError):
            cast_list(123)

    def test_list_handles_unclosed_json_array(self):
        assert cast_list("[a, b") == ["[a", "b"]

    def test_list_handles_invalid_json_array(self):
        assert cast_list("[not json]") == ["[not json]"]

    def test_json_rejects_unsupported_type(self):
        with pytest.raises(CastingError):
            cast_json(object())

    def test_json_rejects_empty_string(self):
        with pytest.raises(CastingError):
            cast_json("")

    def test_get_caster_none(self):
        assert get_caster(None) is None

    def test_get_caster_falls_back_to_type_constructor(self):
        assert get_caster(complex) is complex

    def test_custom_caster_failure_is_wrapped(self):
        def boom(value):
            raise RuntimeError("boom")

        with pytest.raises(CastingError) as exc_info:
            cast_value("x", boom, key="KEY", source="test.env")

        assert exc_info.value.target_type is type(boom)
        assert "boom" in str(exc_info.value)

    def test_named_caster_failure_is_wrapped(self):
        def boom(value):
            raise RuntimeError("boom")

        from smartenv.casting import register_caster

        register_caster("boom_caster", boom)

        with pytest.raises(CastingError) as exc_info:
            Config({"KEY": "x"}).get("KEY", cast="boom_caster")

        assert exc_info.value.target_type is object

    def test_type_constructor_failure_is_wrapped(self):
        with pytest.raises(CastingError) as exc_info:
            Config({"KEY": "not-complex"}).get("KEY", cast=complex)

        assert exc_info.value.target_type is complex


class TestConfigExtras:
    """Less common Config access patterns."""

    def test_convenience_getters_and_mapping_views(self):
        config = Config({"RATE": "3.14", "HOSTS": "a;b", "DATA": '{"a": 1}'})

        assert config.get_float("RATE") == 3.14
        assert config.get_list("HOSTS", separator=";") == ["a", "b"]
        assert config.get_json("DATA") == {"a": 1}
        assert list(config.keys()) == ["RATE", "HOSTS", "DATA"]
        assert "3.14" in config.values()
        assert ("RATE", "3.14") in config.items()

    def test_attribute_access_flat_dotted_key(self):
        config = Config({"a.b": 1})

        assert getattr(config, "a.b") == 1

    def test_load_when_no_env_vars_match_prefix(self, tmp_path, monkeypatch):
        env_path = tmp_path / "test.env"
        env_path.write_text("KEY=value\n", encoding="utf-8")
        monkeypatch.setenv("SMARTENV_UNRELATED", "1")

        config = load(env_path, env_prefix="NO_SUCH_PREFIX_")

        assert config.get("KEY") == "value"


class TestUtils:
    """Utility helpers and their boundary conditions."""

    def test_get_env_prefix(self):
        assert get_env_prefix(None) == ""
        assert get_env_prefix("app") == "APP_"
        assert get_env_prefix(" APP_ ") == "APP_"

    def test_filter_by_prefix_returns_input_for_empty_prefix(self):
        data = {"A": "1"}
        assert filter_by_prefix(data, "") is data

    def test_filter_by_prefix_skips_exact_prefix_key(self):
        data = {"APP_": "ignored", "APP_A": "1", "OTHER": "2"}
        assert filter_by_prefix(data, "APP_") == {"A": "1"}

    def test_merge_configs_skips_falsy_configs(self):
        assert merge_configs({}, {"A": "1"}, {}) == {"A": "1"}

    def test_parse_env_vars_skips_exact_prefix(self, monkeypatch):
        monkeypatch.setenv("SMARTENV_TEST_X", "1")
        monkeypatch.setenv("SMARTENV_TEST_", "exact")

        assert parse_env_vars("SMARTENV_TEST_") == {"X": "1"}

    def test_environment_helpers(self):
        assert is_production({"APP_ENV": "prod"})
        assert is_development({"APP_ENV": "dev"})
        assert is_testing({"APP_ENV": "test"})
        assert is_staging({"APP_ENV": "stage"})


class TestExceptionMessages:
    """Exception messages cover all optional fields."""

    def test_missing_key_error_with_multiple_keys_and_source(self):
        error = MissingKeyError(
            "A",
            source="app.env",
            available_keys=["A"],
            missing_keys=["A", "B"],
        )
        message = str(error)

        assert "A" in message
        assert "B" in message
        assert "from app.env" in message
        assert "Available keys" in message
        assert error.missing_keys == ["A", "B"]

    def test_casting_error_without_reason(self):
        assert "got 'x'" in str(CastingError("KEY", int, "x"))

    def test_parse_error_without_source_or_line(self):
        assert str(ParseError("bad input")) == "bad input"

    def test_parse_error_with_line(self):
        assert "at line 3" in str(ParseError("bad input", source="f.toml", line=3))


class TestParserErrorPaths:
    """Invalid input raises ParseError with useful context."""

    def test_invalid_json_file(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{bad", encoding="utf-8")

        with pytest.raises(ParseError) as exc_info:
            parse_json_file(str(path))

        assert exc_info.value.line == 1

    def test_json_root_is_not_an_object(self, tmp_path):
        path = tmp_path / "list.json"
        path.write_text("[1, 2]", encoding="utf-8")

        with pytest.raises(ParseError):
            parse_json_file(str(path))

    def test_invalid_json_string(self):
        with pytest.raises(ParseError):
            parse_json_string("{bad")

    def test_json_string_with_wrong_input_type(self):
        with pytest.raises(ParseError):
            parse_json_string(123)  # type: ignore[arg-type]

    def test_invalid_toml_file(self, tmp_path):
        path = tmp_path / "bad.toml"
        path.write_text("key = ", encoding="utf-8")

        with pytest.raises(ParseError):
            parse_toml_file(str(path))

    def test_invalid_toml_string(self):
        with pytest.raises(ParseError):
            parse_toml_string("key = ")


class TestEnvEscapePaths:
    """Escape and multiline edge cases in the .env parser."""

    def test_unterminated_quote_at_end_of_input(self):
        assert parse_env_string('KEY="abc')["KEY"] == '"abc'

    def test_wide_unicode_escape(self):
        assert parse_env_string(r'KEY="\U00000041"')["KEY"] == "A"

    def test_invalid_unicode_escape(self):
        with pytest.raises(ParseError):
            parse_env_string(r'KEY="\uZZZZ"')

    def test_invalid_wide_unicode_escape(self):
        with pytest.raises(ParseError):
            parse_env_string(r'KEY="\UZZZZZZZZ"')

    def test_unknown_escape_keeps_literal_character(self):
        assert parse_env_string(r'KEY="\q"')["KEY"] == "q"
