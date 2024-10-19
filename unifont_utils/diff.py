# -*- encoding: utf-8 -*-
"""Unifont Utils - Diff"""

from typing import List, Union

from rich.console import Console
from rich.text import Text
from rich.table import Table

from .base import Validator as V
from .converter import Converter as C
from .glyphs import Glyph


def get_img_data(glyph: Union[str, Glyph]) -> List[int]:
    """Input a `.hex` string or a Glyph object and output its image data.

    Args:
        glyph (Union[str, Glyph]): The glyph to be converted.

    Returns:
        List[int]: The converted image data.

    Raises:
        TypeError: If the glyph is not a valid type.
    """

    if isinstance(glyph, str):
        glyph = V.hex_str(glyph)
        width = 16 if len(glyph) == 64 else 8
        return C.to_img_data(glyph, width)
    if isinstance(glyph, Glyph):
        return glyph.data
    raise TypeError("The glyph must be either a .hex string or a Glyph object.")


def diff_glyphs(glyph_a: Union[str, Glyph], glyph_b: Union[str, Glyph]) -> List[str]:
    """Compares two glyphs and returns a list of differences.

    Args:
        glyph_a (Union[str, Glyph]): The first glyph to compare.
        glyph_b (Union[str, Glyph]): The second glyph to compare.

    Returns:
        List[str]: A list of differences between the two glyphs.

    Raises:
        ValueError: If the two glyphs have different sizes.
    """

    a, b = get_img_data(glyph_a), get_img_data(glyph_b)
    if len(a) != len(b):
        raise ValueError("The two glyphs must have the same size.")

    diff_list = []
    for i, j in zip(a, b):
        if i and not j:
            diff_list.append("-")
        elif not i and j:
            diff_list.append("+")
        elif i and j:
            diff_list.append("1")
        else:
            diff_list.append("0")

    return diff_list


def print_diff(
    glyph_a: Union[str, Glyph],
    glyph_b: Union[str, Glyph],
    *,
    black_and_white: bool = True,
) -> None:
    """Prints the differences between two glyphs.

    Args:
        glyph_a (Union[str, Glyph]): The first glyph to compare.
        glyph_b (Union[str, Glyph]): The second glyph to compare.
        black_and_white (bool, optional): Whether it is a black and white image.

            Defaults to `True`.

            If `True`, `0` is white and `1` is black.

            If `False`, `0` is transparent and `1` is white.
    """

    diff_list = diff_glyphs(glyph_a, glyph_b)
    a, b = get_img_data(glyph_a), get_img_data(glyph_b)
    console = Console()

    white_block = "white on white"
    black_block = "black on black"

    if black_and_white:
        white_block, black_block = black_block, white_block

    width = len(a) // 16

    def get_row(i: int, data: List[int]) -> Text:
        row_text = Text()
        row_data = data[i * width : (i + 1) * width]
        for pixel in row_data:
            block_style = white_block if pixel else black_block
            row_text.append("  ", style=block_style)
        return row_text

    def get_row_diff(i: int) -> Text:
        row_text = Text()
        row_diff = {
            "+": "green on green",
            "-": "red on red",
            "1": white_block,
            "0": black_block,
        }
        for element in diff_list[i * width : (i + 1) * width]:
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
