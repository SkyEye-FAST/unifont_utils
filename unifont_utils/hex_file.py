# -*- encoding: utf-8 -*-
"""Unifont Utils - .hex File"""

import time
from typing import Union
from pathlib import Path

from .glyphs import GlyphSet


def load_hex_file(file_path: Union[str, Path]) -> GlyphSet:
    """Parse and load a .hex file.

    Args:
        file_path (Union[str, Path]): The path to the `.hex` file.

        If a string is provided, it will be converted to a Path object.

    Returns:
        GlyphSet: Obtained glyphs.
    """

    start_time = time.time()

    if isinstance(file_path, str):
        file_path = Path(file_path)

    glyphs = GlyphSet()

    with file_path.open("r", encoding="utf-8") as f:
        for line in f:
            code_point, hex_str = line.strip().split(":")
            glyphs.add_glyph((code_point, hex_str))

    elapsed_time = time.time() - start_time
    print(
        f'Loaded {len(glyphs)} glyphs from "{file_path.name}". Time elapsed: {elapsed_time:.2f} s.'
    )
    return glyphs


def save_hex_file(glyphs: GlyphSet, file_path: Union[str, Path]) -> None:
    """Save a .hex file.

    Args:
        glyphs (GlyphSet): The glyphs to save.
        file_path (Union[str, Path]): The path to the `.hex` file.

        If a string is provided, it will be converted to a Path object.
    """

    start_time = time.time()

    if isinstance(file_path, str):
        file_path = Path(file_path)

    with file_path.open("w", encoding="utf-8") as f:
        for code_point, glyph in sorted(glyphs.glyphs.items()):
            f.write(f"{code_point}:{glyph.hex_str}\n")

    elapsed_time = time.time() - start_time
    print(
        f'Saved {len(glyphs)} glyphs to "{file_path.name}". Time elapsed: {elapsed_time:.2f} s.'
    )
