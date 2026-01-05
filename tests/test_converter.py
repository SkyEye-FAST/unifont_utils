"""Tests for glyph data conversions in converter module."""

import pytest

from unifont_utils.converter import Converter


def test_to_hex_round_trip_for_8x16():
    """Round-trip 8x16 glyph data to hex and back."""
    data = [0, 1] * 64

    hex_str = Converter.to_hex(data)
    assert len(hex_str) == 32
    assert Converter.to_img_data(hex_str, 8, 16) == data


def test_to_hex_round_trip_for_16x16():
    """Round-trip 16x16 glyph data to hex and back."""
    data = [1 if i % 3 == 0 else 0 for i in range(256)]

    hex_str = Converter.to_hex(data)
    assert len(hex_str) == 64
    assert Converter.to_img_data(hex_str, 16, 16) == data


def test_to_hex_empty_raises():
    """Reject converting empty glyph data."""
    with pytest.raises(ValueError):
        Converter.to_hex([])


def test_to_img_data_empty_returns_empty():
    """Return empty list when hex string is empty."""
    assert Converter.to_img_data("") == []


def test_to_hex_rejects_non_binary_values():
    """Non-binary glyph data should raise."""
    with pytest.raises(ValueError):
        Converter.to_hex([0, 2, 1])


def test_to_hex_accepts_iterable_and_preserves_bits():
    """Iterables (not just lists) convert correctly and preserve order."""
    data = (1 if i % 2 == 0 else 0 for i in range(8))  # 10101010 -> 0xAA
    assert Converter.to_hex(data) == "AA"


def test_to_img_data_rejects_invalid_hex_characters():
    """Invalid hex input should raise."""
    with pytest.raises(ValueError):
        Converter.to_img_data("ZZ")


def test_to_img_data_rejects_oversized_hex():
    """Hex longer than glyph capacity should raise."""
    with pytest.raises(ValueError):
        Converter.to_img_data("FFFFFF", width=8, height=2)


def test_to_img_data_trims_whitespace_and_decodes():
    """Whitespace is ignored and bits decoded in row-major order."""
    bits = Converter.to_img_data(" 0A ", width=4, height=2)
    assert bits == [0, 0, 0, 0, 1, 0, 1, 0]
