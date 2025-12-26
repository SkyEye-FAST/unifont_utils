# @Author: SkyEye_FAST <skyeyefast@foxmail.com>
# @Copyright: Copyright (C) 2024-2025 SkyEye_FAST
"""Unifont Utils - Diff"""

from rich.console import Console
from rich.table import Table
from rich.text import Text

from .base import Validator as Validator
from .converter import Converter
from .glyphs import Glyph


def get_img_data(glyph: str | Glyph) -> list[int]:
    """Input a `.hex` string or a Glyph object and output its image data.

    Args:
        glyph (str | Glyph): The glyph to be converted.

    Returns:
        list[int]: The converted image data.

    Raises:
        TypeError: If the glyph is not a valid type.
    """
    if isinstance(glyph, str):
        glyph = Validator.hex_str(glyph)
        width = 16 if len(glyph) == 64 else 8
        return Converter.to_img_data(glyph, width)
    if isinstance(glyph, Glyph):
        return glyph.data
    raise TypeError("The glyph must be either a .hex string or a Glyph object.")


def diff_glyphs(glyph_a: str | Glyph, glyph_b: str | Glyph) -> list[str]:
    """Compares two glyphs and returns a list of differences.

    Args:
        glyph_a (str | Glyph): The first glyph to compare.
        glyph_b (str | Glyph): The second glyph to compare.

    Returns:
        list[str]: A list of differences between the two glyphs.

    Raises:
        ValueError: If the two glyphs have different sizes.
    """
    a, b = map(get_img_data, (glyph_a, glyph_b))
    if len(a) != len(b):
        raise ValueError("The two glyphs must have the same size.")

    return [
        "+" if not i and j else "-" if i and not j else "1" if i and j else "0"
        for i, j in zip(a, b)
    ]


def print_diff(
    glyph_a: str | Glyph,
    glyph_b: str | Glyph,
    *,
    black_and_white: bool = True,
) -> None:
    """Print the differences between two glyphs to the console.

    Args:
        glyph_a (str | Glyph): The first glyph to compare.
        glyph_b (str | Glyph): The second glyph to compare.
        black_and_white (bool, optional): Whether the images are black-and-white.
            Defaults to ``True``. If ``True``, ``0`` is white and ``1`` is black.
            If ``False``, ``0`` is transparent and ``1`` is white.

    Returns:
        None
    """
    diff_list = diff_glyphs(glyph_a, glyph_b)
    a, b = get_img_data(glyph_a), get_img_data(glyph_b)
    console = Console()

    white_block = "white on white"
    black_block = "black on black"

    if black_and_white:
        white_block, black_block = black_block, white_block

    width = len(a) // 16

    def get_row(row_index: int, data: list[int]) -> Text:
        row_text = Text()
        row_data = data[row_index * width : (row_index + 1) * width]
        for pixel in row_data:
            block_style = white_block if pixel else black_block
            row_text.append("  ", style=block_style)
        return row_text

    def get_row_diff(row_index: int) -> Text:
        row_text = Text()
        row_diff = {
            "+": "green on green",
            "-": "red on red",
            "1": white_block,
            "0": black_block,
        }
        for element in diff_list[row_index * width : (row_index + 1) * width]:
            block_style = row_diff.get(str(element), black_block)
            row_text.append("  ", style=block_style)
        return row_text

    table = Table(show_lines=False, expand=False)
    table.add_column("Input")
    table.add_column("Diff")
    table.add_column("Output")

    for i in range(16):
        table.add_row(get_row(i, a), get_row_diff(i), get_row(i, b))

    console.print(table)
