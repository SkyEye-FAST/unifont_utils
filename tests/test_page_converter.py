"""Tests for page-level conversions between .hex and images."""

from pathlib import Path

import pytest
from PIL import Image as Img

from unifont_utils.converter import Converter
from unifont_utils.glyphs import Glyph, GlyphSet
from unifont_utils.page_converter import image_to_hex_page, save_page_image


def _glyph_set_with_samples() -> GlyphSet:
    """Create a GlyphSet containing a diagonal 16x16 glyph and a narrow 8x16 glyph."""
    glyphs = GlyphSet()
    diag_data = [1 if i % 17 == 0 else 0 for i in range(256)]
    narrow_data = [1 if i % 8 == 0 else 0 for i in range(128)]

    glyphs.add_glyph(Glyph.init_from_hex("0000", Converter.to_hex(diag_data)))
    glyphs.add_glyph(Glyph.init_from_hex("0001", Converter.to_hex(narrow_data)))
    return glyphs


def test_page_hex_img_round_trip(tmp_path: Path):
    """Round-trip a page image through save_page_image and image_to_hex_page."""
    glyphs = _glyph_set_with_samples()
    output = tmp_path / "page.png"

    save_page_image(glyphs, 0x00, output)
    restored = image_to_hex_page(output, 0x00)

    assert set(restored.code_points) == {"0000", "0001"}
    assert restored.get_glyph("0000").hex_str == glyphs.get_glyph("0000").hex_str
    assert restored.get_glyph("0001").hex_str == glyphs.get_glyph("0001").hex_str


def test_page_round_trip_with_color_scheme(tmp_path: Path):
    """Round-trip using a non-default color scheme and auto-detect on read."""
    glyphs = _glyph_set_with_samples()
    output = tmp_path / "page_transparent.png"

    save_page_image(glyphs, 0x00, output, color_scheme="transparent_and_white")
    restored = image_to_hex_page(output, 0x00, color_auto_detect=True)

    assert set(restored.code_points) == {"0000", "0001"}
    assert restored.get_glyph("0000").hex_str == glyphs.get_glyph("0000").hex_str
    assert restored.get_glyph("0001").hex_str == glyphs.get_glyph("0001").hex_str


def test_image_to_hex_page_requires_valid_dimensions(tmp_path: Path):
    """Reject images whose dimensions are not the fixed unihex2bmp page size."""
    bad_output = tmp_path / "bad.png"
    Img.new("RGBA", (10, 10), (255, 255, 255, 255)).save(bad_output)

    with pytest.raises(ValueError):
        image_to_hex_page(bad_output, 0x00)
