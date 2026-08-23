"""Focused tests for editor presentation helpers."""

from unifont_utils.editor import _hex_index


def test_hex_index_is_zero_padded() -> None:
    """Grid headers use stable two-character hexadecimal labels."""
    assert _hex_index(0) == "00"
    assert _hex_index(15) == "0F"
