"""Tests for glyph data conversions in converter module."""

from __future__ import annotations

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
