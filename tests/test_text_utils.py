"""Tests for text utilities."""

from altomatic.utils.text import extract_json_from_string

def test_extract_json_with_nested_braces():
    """Verify that JSON with nested braces is extracted correctly."""
    test_string = 'Some text {invalid} real JSON: {"key": {"nested_key": "value"}}'
    expected_json = {"key": {"nested_key": "value"}}
    assert extract_json_from_string(test_string) == expected_json
