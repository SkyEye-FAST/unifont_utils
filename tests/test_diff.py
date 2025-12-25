"""Tests for diff helpers operating on glyphs and hex strings."""

from __future__ import annotations

import pytest

from unifont_utils.converter import Converter
from unifont_utils.diff import diff_glyphs, get_img_data
from unifont_utils.glyphs import Glyph


def test_get_img_data_accepts_hex_and_glyph():
    """Support both hex strings and Glyph objects; reject invalid types."""
    data = [0] * 127 + [1]
    hex_str = Converter.to_hex(data)
    glyph = Glyph.init_from_hex("0041", hex_str)

    assert get_img_data(hex_str) == data
    assert get_img_data(glyph) == data

    with pytest.raises(TypeError):
        get_img_data(123)  # type: ignore[arg-type]


def test_diff_glyphs_reports_pixel_changes():
    """Mark added pixel with '+' and keep unchanged as '0'."""
    data_a = [0] * 128
    data_b = data_a.copy()
    data_b[0] = 1

    hex_a = Converter.to_hex(data_a)
    hex_b = Converter.to_hex(data_b)

    diff = diff_glyphs(hex_a, hex_b)
    assert diff[0] == "+"
    assert all(entry == "0" for entry in diff[1:])


def test_diff_glyphs_size_mismatch_raises():
    """Reject diffing glyphs with different dimensions."""
    hex_a = Converter.to_hex([0] * 128)
    hex_b = Converter.to_hex([0] * 256)

    with pytest.raises(ValueError):
        diff_glyphs(hex_a, hex_b)
