"""Tests for the .env parser."""

import pytest

from smartenv.parsers.env import EnvParser, parse_env_file, parse_env_string
from smartenv.exceptions import ParseError


class TestEnvParser:
    """Tests for EnvParser class."""

    def test_basic_parsing(self, sample_env_content):
        """Test basic .env parsing."""
        parser = EnvParser(sample_env_content)
        result = parser.parse()

        assert result["DATABASE_URL"] == "postgres://localhost/mydb"
        assert result["DEBUG"] == "true"
        assert result["PORT"] == "8000"
        assert result["SECRET_KEY"] == "test-secret"

    def test_empty_value(self, sample_env_content):
        """Test empty value parsing."""
        parser = EnvParser(sample_env_content)
        result = parser.parse()
        assert result["EMPTY"] == ""

    def test_quoted_values(self, sample_env_content):
        """Test quoted value parsing."""
        parser = EnvParser(sample_env_content)
        result = parser.parse()

        assert result["QUOTED"] == "hello world"
        assert result["SINGLE"] == "single quoted"

    def test_spaces_around_equals(self, sample_env_content):
        """Test spaces around equals sign."""
        parser = EnvParser(sample_env_content)
        result = parser.parse()
        assert result["WITH_SPACES"] == "value with spaces"

    def test_export_prefix(self, sample_env_content):
        """Test export prefix handling."""
        parser = EnvParser(sample_env_content)
        result = parser.parse()
        assert result["EXPORT_VAR"] == "exported"

    def test_comments_ignored(self, sample_env_content):
        """Test that comments are ignored."""
        parser = EnvParser(sample_env_content)
        result = parser.parse()
        assert "Comment" not in result

    def test_inline_comments(self):
        """Test inline comments are stripped."""
        content = 'KEY=value # this is a comment'
        parser = EnvParser(content)
        result = parser.parse()
        assert result["KEY"] == "value"

    def test_quoted_values_preserve_hash(self):
        """Test that # inside quotes is preserved."""
        content = 'KEY="value # not a comment"'
        parser = EnvParser(content)
        result = parser.parse()
        assert result["KEY"] == "value # not a comment"

    def test_multiline_not_supported(self):
        """Test that multiline values are not supported (single line only)."""
        content = 'KEY="line1\nline2"'
        parser = EnvParser(content)
        result = parser.parse()
        # The parser handles \n as literal characters in quotes
        assert result["KEY"] == "line1\nline2"

    def test_equals_in_value(self):
        """Test equals sign in value."""
        content = "KEY=value=with=equals"
        parser = EnvParser(content)
        result = parser.parse()
        assert result["KEY"] == "value=with=equals"

    def test_escape_sequences_double_quotes(self):
        """Test escape sequences in double-quoted strings."""
        content = r'KEY="line1\nline2\ttabbed\"quoted\"'
        parser = EnvParser(content)
        result = parser.parse()
        assert result["KEY"] == 'line1\nline2\ttabbed"quoted"'

    def test_escape_sequences_single_quotes(self):
        """Test escape sequences in single-quoted strings (literal)."""
        content = r"KEY='line1\nline2\ttabbed\'quoted\'"
        parser = EnvParser(content)
        result = parser.parse()
        # Single quotes: only \' and \\ are processed
        assert result["KEY"] == r"line1\nline2\ttabbed'quoted'"

    def test_unicode_escapes(self):
        """Test unicode escape sequences."""
        content = r'KEY="\u0041\u0042"'
        parser = EnvParser(content)
        result = parser.parse()
        assert result["KEY"] == "AB"

    def test_invalid_line_raises_error(self):
        """Test that invalid lines raise ParseError."""
        content = "INVALID LINE NO EQUALS"
        parser = EnvParser(content, source="test.env")
        with pytest.raises(ParseError) as exc_info:
            parser.parse()
        assert "Invalid line format" in str(exc_info.value)
        assert exc_info.value.line == 1

    def test_empty_lines_skipped(self):
        """Test that empty lines are skipped."""
        content = "\n\nKEY=value\n\n"
        parser = EnvParser(content)
        result = parser.parse()
        assert result["KEY"] == "value"
        assert len(result) == 1

    def test_comment_lines_skipped(self):
        """Test that comment lines are skipped."""
        content = "# Comment\nKEY=value\n# Another comment"
        parser = EnvParser(content)
        result = parser.parse()
        assert result["KEY"] == "value"
        assert len(result) == 1


class TestParseEnvFile:
    """Tests for parse_env_file function."""

    def test_parse_file(self, basic_env_path):
        """Test parsing a .env file."""
        result = parse_env_file(basic_env_path)
        assert result["DATABASE_URL"] == "postgres://localhost:5432/mydb"
        assert result["DEBUG"] == "true"
        assert result["PORT"] == "8000"

    def test_parse_nonexistent_file(self):
        """Test parsing nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            parse_env_file("/nonexistent/path/.env")


class TestParseEnvString:
    """Tests for parse_env_string function."""

    def test_parse_string(self, sample_env_content):
        """Test parsing .env string."""
        result = parse_env_string(sample_env_content, source="test.env")
        assert result["DATABASE_URL"] == "postgres://localhost/mydb"

    def test_empty_string(self):
        """Test parsing empty string."""
        result = parse_env_string("")
        assert result == {}

    def test_only_comments(self):
        """Test parsing only comments."""
        result = parse_env_string("# Comment\n# Another")
        assert result == {}


class TestEdgeCases:
    """Tests for edge cases from fixture."""

    def test_key_with_equals(self, edge_cases_env_path):
        result = parse_env_file(edge_cases_env_path)
        assert result["KEY_WITH_EQUALS"] == "value=with=equals"

    def test_key_with_hash(self, edge_cases_env_path):
        result = parse_env_file(edge_cases_env_path)
        assert result["KEY_WITH_HASH"] == "value#notacomment"

    def test_key_with_quotes(self, edge_cases_env_path):
        result = parse_env_file(edge_cases_env_path)
        assert result["KEY_WITH_QUOTES"] == 'quoted "value"'

    def test_key_with_escapes(self, edge_cases_env_path):
        result = parse_env_file(edge_cases_env_path)
        assert result["KEY_WITH_ESCAPES"] == "line1\nline2\ttabbed"

    def test_bool_values(self, edge_cases_env_path):
        result = parse_env_file(edge_cases_env_path)
        assert result["BOOL_TRUE"] == "true"
        assert result["BOOL_FALSE"] == "false"
        assert result["BOOL_YES"] == "yes"
        assert result["BOOL_NO"] == "no"
        assert result["BOOL_ON"] == "on"
        assert result["BOOL_OFF"] == "off"
        assert result["BOOL_1"] == "1"
        assert result["BOOL_0"] == "0"

    def test_int_value(self, edge_cases_env_path):
        result = parse_env_file(edge_cases_env_path)
        assert result["INT_VAL"] == "42"

    def test_float_value(self, edge_cases_env_path):
        result = parse_env_file(edge_cases_env_path)
        assert result["FLOAT_VAL"] == "3.14"

    def test_list_value(self, edge_cases_env_path):
        result = parse_env_file(edge_cases_env_path)
        assert result["LIST_VAL"] == "a,b,c"
        assert result["LIST_WITH_SPACES"] == "a, b, c"