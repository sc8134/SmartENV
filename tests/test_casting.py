"""Tests for the type casting system."""

import pytest

from smartenv.casting import (
    cast_bool,
    cast_int,
    cast_float,
    cast_list,
    cast_json,
    cast_value,
    get_caster,
    register_caster,
)
from smartenv.exceptions import CastingError


class TestCastBool:
    """Tests for boolean casting."""

    @pytest.mark.parametrize("value", ["true", "True", "TRUE", "1", "yes", "Yes", "YES", "on", "On", "ON", "y", "Y", "t", "T"])
    def test_truthy_values(self, value):
        assert cast_bool(value) is True

    @pytest.mark.parametrize("value", ["false", "False", "FALSE", "0", "no", "No", "NO", "off", "Off", "OFF", "n", "N", "f", "F"])
    def test_falsy_values(self, value):
        assert cast_bool(value) is False

    def test_boolean_passthrough(self):
        assert cast_bool(True) is True
        assert cast_bool(False) is False

    def test_integer_passthrough(self):
        assert cast_bool(1) is True
        assert cast_bool(0) is False

    def test_invalid_string_raises(self):
        with pytest.raises(CastingError) as exc_info:
            cast_bool("invalid")
        assert "unrecognized boolean value" in str(exc_info.value)

    def test_invalid_type_raises(self):
        with pytest.raises(CastingError) as exc_info:
            cast_bool([])
        assert "unsupported type" in str(exc_info.value)


class TestCastInt:
    """Tests for integer casting."""

    @pytest.mark.parametrize("value,expected", [
        ("42", 42),
        ("0", 0),
        ("-10", -10),
        ("  42  ", 42),
        ("0xFF", 255),
        ("0XFF", 255),
        ("0o77", 63),
        ("0O77", 63),
        ("0b1010", 10),
        ("0B1010", 10),
    ])
    def test_valid_integers(self, value, expected):
        assert cast_int(value) == expected

    def test_integer_passthrough(self):
        assert cast_int(42) == 42
        assert cast_int(0) == 0

    def test_float_whole_number(self):
        assert cast_int(3.0) == 3

    def test_float_not_whole_raises(self):
        with pytest.raises(CastingError) as exc_info:
            cast_int(3.14)
        assert "not a whole number" in str(exc_info.value)

    def test_empty_string_raises(self):
        with pytest.raises(CastingError) as exc_info:
            cast_int("")
        assert "empty string" in str(exc_info.value)

    def test_invalid_string_raises(self):
        with pytest.raises(CastingError) as exc_info:
            cast_int("not a number")
        assert "invalid literal" in str(exc_info.value).lower()

    def test_bool_rejected(self):
        with pytest.raises(CastingError):
            cast_int(True)


class TestCastFloat:
    """Tests for float casting."""

    @pytest.mark.parametrize("value,expected", [
        ("3.14", 3.14),
        ("0", 0.0),
        ("-2.5", -2.5),
        ("  3.14  ", 3.14),
        ("1e10", 1e10),
        ("1E-5", 1e-5),
    ])
    def test_valid_floats(self, value, expected):
        assert cast_float(value) == expected

    def test_integer_passthrough(self):
        assert cast_float(42) == 42.0

    def test_float_passthrough(self):
        assert cast_float(3.14) == 3.14

    def test_empty_string_raises(self):
        with pytest.raises(CastingError) as exc_info:
            cast_float("")
        assert "empty string" in str(exc_info.value)

    def test_invalid_string_raises(self):
        with pytest.raises(CastingError) as exc_info:
            cast_float("not a number")


class TestCastList:
    """Tests for list casting."""

    def test_comma_separated(self):
        result = cast_list("a,b,c")
        assert result == ["a", "b", "c"]

    def test_comma_separated_with_spaces(self):
        result = cast_list("a, b, c")
        assert result == ["a", "b", "c"]

    def test_custom_separator(self):
        result = cast_list("a;b;c", separator=";")
        assert result == ["a", "b", "c"]

    def test_json_array(self):
        result = cast_list('["a", "b", "c"]')
        assert result == ["a", "b", "c"]

    def test_json_array_with_spaces(self):
        result = cast_list('[ "a", "b", "c" ]')
        assert result == ["a", "b", "c"]

    def test_empty_string(self):
        result = cast_list("")
        assert result == []

    def test_whitespace_only(self):
        result = cast_list("   ")
        assert result == []

    def test_list_passthrough(self):
        result = cast_list(["a", "b", "c"])
        assert result == ["a", "b", "c"]

    def test_filters_empty_items(self):
        result = cast_list("a,,b,,c")
        assert result == ["a", "b", "c"]


class TestCastJson:
    """Tests for JSON casting."""

    def test_json_object(self):
        result = cast_json('{"key": "value", "num": 42}')
        assert result == {"key": "value", "num": 42}

    def test_json_array(self):
        result = cast_json('[1, 2, 3]')
        assert result == [1, 2, 3]

    def test_json_string(self):
        result = cast_json('"hello"')
        assert result == "hello"

    def test_json_number(self):
        result = cast_json("42")
        assert result == 42

    def test_json_bool(self):
        result = cast_json("true")
        assert result is True

    def test_json_null(self):
        result = cast_json("null")
        assert result is None

    def test_passthrough_dict(self):
        result = cast_json({"key": "value"})
        assert result == {"key": "value"}

    def test_passthrough_list(self):
        result = cast_json([1, 2, 3])
        assert result == [1, 2, 3]

    def test_invalid_json_raises(self):
        with pytest.raises(CastingError) as exc_info:
            cast_json("{invalid}")
        assert "Expecting" in str(exc_info.value) or "invalid" in str(exc_info.value).lower()


class TestCastValue:
    """Tests for the main cast_value function."""

    def test_no_cast_returns_value(self):
        assert cast_value("hello", None) == "hello"
        assert cast_value(42, None) == 42
        assert cast_value({"a": 1}, None) == {"a": 1}

    def test_cast_with_type(self):
        assert cast_value("42", int) == 42
        assert cast_value("true", bool) is True
        assert cast_value("3.14", float) == 3.14

    def test_cast_with_string_name(self):
        assert cast_value("42", "int") == 42
        assert cast_value("true", "bool") is True
        assert cast_value('["a","b"]', "json") == ["a", "b"]

    def test_cast_with_callable(self):
        assert cast_value("hello", str.upper) == "HELLO"
        assert cast_value("42", lambda x: int(x) * 2) == 84

    def test_cast_error_includes_key_and_source(self):
        with pytest.raises(CastingError) as exc_info:
            cast_value("invalid", int, key="PORT", source=".env")
        assert "PORT" in str(exc_info.value)
        assert ".env" in str(exc_info.value)
        assert "int" in str(exc_info.value)


class TestGetCaster:
    """Tests for get_caster function."""

    def test_get_builtin_by_type(self):
        assert get_caster(int) is cast_int
        assert get_caster(bool) is cast_bool
        assert get_caster(float) is cast_float
        assert get_caster(list) is cast_list

    def test_get_builtin_by_name(self):
        assert get_caster("int") is cast_int
        assert get_caster("bool") is cast_bool
        assert get_caster("float") is cast_float
        assert get_caster("list") is cast_list
        assert get_caster("json") is cast_json

    def test_get_custom_callable(self):
        custom = lambda x: x * 2
        assert get_caster(custom) is custom

    def test_unknown_name_raises(self):
        with pytest.raises(ValueError) as exc_info:
            get_caster("unknown")
        assert "Unknown caster name" in str(exc_info.value)


class TestRegisterCaster:
    """Tests for register_caster function."""

    def test_register_custom_caster(self):
        def custom_caster(value):
            return f"custom:{value}"

        register_caster("custom", custom_caster)
        assert get_caster("custom") is custom_caster

        # Cleanup
        from smartenv.casting import _BUILTIN_CASTERS
        del _BUILTIN_CASTERS["custom"]

    def test_register_by_type(self):
        def custom_caster(value):
            return f"typed:{value}"

        register_caster(int, custom_caster)
        assert get_caster(int) is custom_caster

        # Cleanup
        from smartenv.casting import _BUILTIN_CASTERS
        del _BUILTIN_CASTERS[int]