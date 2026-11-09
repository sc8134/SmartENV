"""Parser for .env files."""

import os
import re
from typing import Any

from smartenv.exceptions import ParseError


class EnvParser:
    """Parses .env file content into a dictionary."""

    # Simple regex to match KEY=VALUE lines with optional export prefix
    _LINE_PATTERN = re.compile(
        r'^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$'
    )

    def __init__(self, content: str, *, source: str = "<string>") -> None:
        self.content = content
        self.source = source
        self._lines = content.splitlines()

    def parse(self) -> dict[str, str]:
        """Parse the .env content and return a dictionary of key-value pairs."""
        result: dict[str, str] = {}

        i = 0
        while i < len(self._lines):
            line_num = i + 1
            line = self._lines[i]

            parsed = self._parse_line(line, line_num)
            if parsed:
                key, raw_value = parsed
                
                # Check for multiline quoted string
                if (raw_value.startswith('"') and not self._ends_with_unescaped_quote(raw_value, '"')) or \
                   (raw_value.startswith("'") and not self._ends_with_unescaped_quote(raw_value, "'")):
                    # Consume subsequent lines
                    raw_value, consumed = self._consume_multiline_raw(raw_value, i + 1)
                    i += consumed
                
                # Strip trailing comment (but not inside quotes)
                raw_value = self._strip_inline_comment(raw_value)

                # Process the value: unquote and handle escapes
                value = self._process_value(raw_value, line_num)
                result[key] = value

            i += 1

        return result

    def _parse_line(self, line: str, line_num: int) -> tuple[str, str] | None:
        """Parse a single line. Returns (key, raw_value) or None for empty/comment lines."""
        stripped = line.strip()

        # Skip empty lines and comments
        if not stripped or stripped.startswith("#"):
            return None

        match = self._LINE_PATTERN.match(line)
        if not match:
            raise ParseError(
                f"Invalid line format",
                source=self.source,
                line=line_num,
            )

        key = match.group(1)
        raw_value = match.group(2)

        return key, raw_value

    def _consume_multiline_raw(self, raw_value: str, start_line: int) -> tuple[str, int]:
        """Consume subsequent lines for a multiline quoted value."""
        quote_char = raw_value[0]
        lines = [raw_value]
        i = start_line  # start_line is 1-based, _lines is 0-based
        
        while i < len(self._lines):
            next_line = self._lines[i]
            lines.append(next_line)
            # Check if this line ends with the matching quote (not escaped)
            if self._ends_with_unescaped_quote(next_line, quote_char):
                break
            i += 1
        
        # Join with newlines
        combined = "\n".join(lines)
        consumed = i - start_line + 1
        return combined, consumed

    def _ends_with_unescaped_quote(self, line: str, quote_char: str) -> bool:
        """Check if line ends with an unescaped quote."""
        if not line.endswith(quote_char):
            return False
        # Count backslashes before the quote
        count = 0
        i = len(line) - 2
        while i >= 0 and line[i] == "\\":
            count += 1
            i -= 1
        # If odd number of backslashes, the quote is escaped
        return count % 2 == 0

    def _strip_inline_comment(self, value: str) -> str:
        """Strip trailing comment starting with # preceded by whitespace, but not inside quotes."""
        in_double = False
        in_single = False
        escape_next = False
        comment_pos = -1

        for i, ch in enumerate(value):
            if escape_next:
                escape_next = False
                continue

            if ch == "\\":
                escape_next = True
                continue

            if ch == '"' and not in_single:
                in_double = not in_double
            elif ch == "'" and not in_double:
                in_single = not in_single
            elif ch == "#" and not in_double and not in_single:
                # Check if preceded by whitespace
                if i > 0 and value[i - 1].isspace():
                    comment_pos = i
                    break

        if comment_pos > 0:
            return value[:comment_pos].rstrip()

        return value.rstrip()

    def _process_value(self, raw_value: str, line_num: int) -> str:
        """Process a raw value string: remove quotes, handle escapes."""
        if not raw_value:
            return ""

        # Check if quoted
        if (raw_value.startswith('"') and raw_value.endswith('"')) or (
            raw_value.startswith("'") and raw_value.endswith("'")
        ):
            # Remove surrounding quotes
            quote_char = raw_value[0]
            inner = raw_value[1:-1]

            # Handle edge case: if the closing quote is escaped (preceded by odd number of backslashes),
            # then the string is not properly terminated. Treat the last quote as literal.
            if inner and inner[-1] == "\\":
                # The closing quote was escaped, so it's part of the content
                # Put the last quote back and process as unquoted
                inner = raw_value[1:]  # Keep everything after first quote
                # Process escapes in the whole thing
                if quote_char == '"':
                    return self._unescape(inner, line_num)
                else:
                    return inner.replace("\\'", "'").replace("\\\\", "\\")

            # Handle escape sequences
            if quote_char == '"':
                # Double quotes: process escape sequences
                return self._unescape(inner, line_num)
            else:
                # Single quotes: literal, no escape processing (except \' and \\)
                return inner.replace("\\'", "'").replace("\\\\", "\\")

        # Unquoted value: strip trailing whitespace but preserve internal spaces
        return raw_value.rstrip()

    def _unescape(self, value: str, line_num: int) -> str:
        """Process escape sequences in double-quoted strings."""
        # Common escape sequences
        escape_map = {
            "n": "\n",
            "r": "\r",
            "t": "\t",
            "\\": "\\",
            '"': '"',
            "'": "'",
        }

        result = []
        i = 0
        while i < len(value):
            char = value[i]
            if char == "\\" and i + 1 < len(value):
                next_char = value[i + 1]
                if next_char in escape_map:
                    result.append(escape_map[next_char])
                    i += 2
                elif next_char == "u" and i + 5 < len(value):
                    # Unicode escape \uXXXX
                    hex_digits = value[i + 2 : i + 6]
                    try:
                        result.append(chr(int(hex_digits, 16)))
                        i += 6
                    except ValueError:
                        raise ParseError(
                            f"Invalid unicode escape \\u{hex_digits}",
                            source=self.source,
                            line=line_num,
                        )
                elif next_char == "U" and i + 9 < len(value):
                    # Unicode escape \UXXXXXXXX
                    hex_digits = value[i + 2 : i + 10]
                    try:
                        result.append(chr(int(hex_digits, 16)))
                        i += 10
                    except ValueError:
                        raise ParseError(
                            f"Invalid unicode escape \\U{hex_digits}",
                            source=self.source,
                            line=line_num,
                        )
                else:
                    # Unknown escape - keep as literal (just the next char)
                    result.append(next_char)
                    i += 2
            else:
                result.append(char)
                i += 1

        return "".join(result)


def parse_env_file(filepath: str | os.PathLike[str]) -> dict[str, str]:
    """Parse a .env file and return a dictionary of key-value pairs."""
    path = os.fspath(filepath)
    with open(path, encoding="utf-8") as f:
        content = f.read()
    return EnvParser(content, source=path).parse()


def parse_env_string(content: str, *, source: str = "<string>") -> dict[str, str]:
    """Parse a .env string and return a dictionary of key-value pairs."""
    return EnvParser(content, source=source).parse()