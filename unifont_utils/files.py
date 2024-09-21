# -*- encoding: utf-8 -*-
"""Unifont Utils - Files"""

import time

from PIL import Image as Img

from .base import CodePoint, FilePath, validate_file_path
from .converter import HexConverter
from .glyphs import GlyphSet


def load_hex_file(file_path: FilePath) -> GlyphSet:
    """Parse and load a .hex file.

    Args:
        file_path (FilePath): The path to the `.hex` file.

    Returns:
        GlyphSet: Obtained glyphs.
    """

    start_time = time.time()

    file_path = validate_file_path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    glyphs = GlyphSet()

    with file_path.open("r", encoding="utf-8") as f:
        for line in f:
            if ":" not in line:
                raise ValueError(f"Invalid line in file: {line}")
            code_point, hex_str = line.strip().split(":")
            glyphs.add_glyph((code_point, hex_str))

    elapsed_time = time.time() - start_time
    print(
        f'Loaded {len(glyphs)} glyphs from "{file_path.name}".'
        f"Time elapsed: {elapsed_time:.2f} s."
    )
    return glyphs


def save_hex_file(glyphs: GlyphSet, file_path: FilePath) -> None:
    """Save a .hex file.

    Args:
        glyphs (GlyphSet): The glyphs to save.
        file_path (FilePath): The path to the `.hex` file.
    """

    start_time = time.time()

    file_path = validate_file_path(file_path)
    with file_path.open("w", encoding="utf-8") as f:
        for code_point, glyph in sorted(glyphs.glyphs.items()):
            f.write(f"{code_point}:{glyph.hex_str}\n")

    elapsed_time = time.time() - start_time
    print(
        f'Saved {len(glyphs)} glyphs to "{file_path.name}".'
        f"Time elapsed: {elapsed_time:.2f} s."
    )


def save_unicode_page(
    glyphs: GlyphSet, file_path: FilePath, start: CodePoint = "4E00"
) -> None:
    """Save a Unicode page image for Minecraft.

    This function saves a 256px image with each Unicode code point represented by a 16px
    pixel glyph. The image contains 256 characters at most, starting from the specified
    Unicode code point.

    Args:
        glyphs (GlyphSet): The glyphs to save.
        file_path (FilePath): The path to the Unicode page file.
        start (CodePoint, optional): The starting Unicode code point. Defaults to "4E00".
    """

    start_time = time.time()

    glyphs.sort_glyphs()
    file_path = validate_file_path(file_path)
    start = int(start, 16) if isinstance(start, str) else start

    img = Img.new("RGBA", (256, 256))
    position = 0
    for code_point, glyph in glyphs.glyphs.items():
        if int(code_point, 16) < start:
            continue

        if glyph.hex_str:
            converter = HexConverter(glyph.hex_str)
            glyph_img = Img.new("RGBA", (16, 16))
            rgba_data = [
                (255, 255, 255, 255) if pixel else (0, 0, 0, 0)
                for pixel in converter.data
            ]
            glyph_img.putdata(rgba_data)

            x = (position % 16) * 16
            y = (position // 16) * 16
            img.paste(glyph_img, (x, y))

        position += 1
        if position >= 256:
            break

    img.save(file_path)

    elapsed_time = time.time() - start_time
    print(
        f'Saved {position} glyphs to "{file_path.name}".'
        f" Time elapsed: {elapsed_time:.2f} s."
    )
