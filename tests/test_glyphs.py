"""Tests for glyph data structures and I/O helpers."""

from pathlib import Path

import pytest
from PIL import Image

from unifont_utils.converter import Converter
from unifont_utils.glyphs import Glyph, GlyphSet, ReplacePattern, SearchPattern


def test_search_pattern_requires_binary_data():
    """SearchPattern only allows 0/1 values."""
    with pytest.raises(ValueError):
        SearchPattern([0, -1, 1, 0, 1, 0, 1, 1, 0], 3, 3)


def test_replace_pattern_rejects_invalid_values():
    """ReplacePattern only allows 0/1/-1 values."""
    with pytest.raises(ValueError):
        ReplacePattern([2, 0, 1, 0, 1, 0, 1, 1, 0], 3, 3)


def test_glyph_hex_and_data_stay_in_sync():
    """Hex string and data stay synchronized after mutation."""
    data = [1 if i % 5 == 0 else 0 for i in range(256)]
    hex_str = Converter.to_hex(data)
    glyph = Glyph.init_from_hex("0041", hex_str)

    assert glyph.width == 16
    assert glyph.data == data

    glyph.update_data_at_index(0, 0)
    expected_data = data.copy()
    expected_data[0] = 0
    assert glyph.data[0] == 0
    assert glyph.hex_str == Converter.to_hex(expected_data)


def test_glyph_data_property_returns_copy():
    """Data property returns a copy, not a live view."""
    data = [0] * 128
    hex_str = Converter.to_hex(data)
    glyph = Glyph.init_from_hex("0042", hex_str)

    data_view = glyph.data
    data_view[0] = 1

    assert glyph.data[0] == 0


def test_find_matches_and_replace_pattern():
    """Find a 3x3 block of ones then replace it with zeros."""
    data = [0] * 128
    for y in range(3):
        for x in range(3):
            data[y * 8 + x] = 1

    glyph = Glyph.init_from_hex("0043", Converter.to_hex(data))
    search_pattern = SearchPattern([1] * 9, 3, 3)
    replace_pattern = ReplacePattern([0] * 9, 3, 3)

    matches = glyph.find_matches(search_pattern)
    assert matches == [(0, 0)]

    glyph.replace(search_pattern, replace_pattern)
    assert all(glyph.data[y * 8 + x] == 0 for y in range(3) for x in range(3))


def test_apply_pattern_bounds_checks():
    """apply_pattern enforces bounds for start coordinates."""
    glyph = Glyph.init_from_hex("0044", Converter.to_hex([0] * 128))
    replace_pattern = ReplacePattern([1] * 9, 3, 3)

    with pytest.raises(ValueError):
        glyph.apply_pattern(-1, 0, replace_pattern)
    with pytest.raises(ValueError):
        glyph.apply_pattern(15, 0, replace_pattern)
    with pytest.raises(ValueError):
        glyph.apply_pattern(0, 6, replace_pattern)


def test_replace_with_mismatched_pattern_sizes_raises():
    """Reject replacement when search/replace pattern sizes differ."""
    glyph = Glyph.init_from_hex("0045", Converter.to_hex([0] * 128))
    search_pattern = SearchPattern([1] * 9, 3, 3)
    replace_pattern = ReplacePattern([0] * 12, 3, 4)

    with pytest.raises(ValueError):
        glyph.replace(search_pattern, replace_pattern)


def test_load_img_auto_detects_color_scheme(tmp_path):
    """Auto-detect color scheme from image and decode pixels."""
    img_path = tmp_path / "glyph.png"
    img = Image.new("RGBA", (16, 16), (255, 255, 255, 255))
    img.putpixel((0, 0), (0, 0, 0, 255))
    img.save(img_path)

    glyph = Glyph.init_from_img("0046", img_path)

    assert glyph.color_scheme.name == "black_and_white"
    assert glyph.width == 16
    assert glyph.data[0] == 1
    assert glyph.data[1] == 0


def test_save_img_rejects_invalid_format(tmp_path):
    """Reject saving glyph image with unsupported format."""
    glyph = Glyph.init_from_hex("0047", Converter.to_hex([0] * 256))

    with pytest.raises(ValueError):
        glyph.save_img(tmp_path / "out.jpg", img_format="JPG")


def test_glyphset_add_update_remove_and_errors():
    """Add, update, remove glyphs and validate error paths."""
    glyph_set = GlyphSet()
    glyph_a = Glyph.init_from_hex("0048", Converter.to_hex([0] * 128))
    glyph_b = Glyph.init_from_hex("0049", Converter.to_hex([1] * 128))

    glyph_set.add_glyph(glyph_a)
    assert glyph_set.get_glyph("0048").hex_str == glyph_a.hex_str

    with pytest.raises(ValueError):
        glyph_set.add_glyph(glyph_a)

    glyph_set.add_glyph(glyph_b)
    glyph_set.update_glyph(("0049", Converter.to_hex([0] * 128)))
    assert glyph_set.get_glyph("0049").data == [0] * 128

    glyph_set.remove_glyph("0048")
    with pytest.raises(KeyError):
        glyph_set.remove_glyph("0048")
    with pytest.raises(KeyError):
        glyph_set.get_glyph("FFFF")


def test_glyphset_sort_empty_raises():
    """Sorting an empty GlyphSet raises an error."""
    glyph_set = GlyphSet()
    with pytest.raises(ValueError):
        glyph_set.sort_glyphs()


def test_save_and_load_hex_file_sorted_and_round_trips(tmp_path):
    """Save glyphs to hex file, ensure sorted order on reload."""
    glyph_set = GlyphSet()
    glyph_set.add_glyph(Glyph.init_from_hex("004A", Converter.to_hex([0] * 128)))
    glyph_set.add_glyph(Glyph.init_from_hex("0041", Converter.to_hex([1] * 128)))

    file_path = tmp_path / "font.hex"
    glyph_set.save_hex_file(file_path)

    loaded = GlyphSet.load_hex_file(file_path)
    assert list(loaded.glyphs.keys()) == ["0041", "004A"]
    assert loaded.get_glyph("0041").hex_str == glyph_set.get_glyph("0041").hex_str


def test_load_hex_file_invalid_line_raises(tmp_path):
    """Invalid lines in hex files raise a ValueError."""
    file_path = tmp_path / "bad.hex"
    file_path.write_text("not_a_valid_line\n", encoding="utf-8")

    with pytest.raises(ValueError):
        GlyphSet.load_hex_file(file_path)
