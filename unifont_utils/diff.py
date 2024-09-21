# -*- encoding: utf-8 -*-
"""Unifont Utils - Diff"""

from platform import system
from typing import List, Union

from .converter import HexConverter
from .glyphs import Glyph


def get_img_data(glyph: Union[str, Glyph]) -> List[str]:
    """Input a `.hex` string or a Glyph object and output its image data.

    Args:
        glyph (Union[str, Glyph]): The glyph to be converted.

    Returns:
        List[str]: The converted image data.

    Raises:
        TypeError: If the glyph is not a valid type.
    """

    if not isinstance(glyph, (str, Glyph)):
        raise TypeError("The glyph must be either a .hex string or a Glyph object.")

    return HexConverter(glyph).data if isinstance(glyph, str) else glyph.data


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
):
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

    white_block, black_block, add_block, remove_block, new_line = (
        ("▇", "  ", "+", "-", "\n")
        if system() == "Windows"
        else (
            "\033[48;5;7m  ",  # White
            "\033[48;5;0m  ",  # Black
            "\033[48;5;2m  ",  # Green
            "\033[48;5;1m  ",  # Red
            "\033[0m",
        )
    )

    if black_and_white:
        white_block, black_block = black_block, white_block

    width = len(a) // 16

    def get_row(i: int, data: List[str]) -> str:
        return "".join(
            white_block if data[i * width + j] else black_block for j in range(width)
        )

    def get_row_diff(i: int, data: List[str]) -> str:
        row_diff = ""
        for j in range(width):
            element = data[i * width + j]
            if element == "+":
                row_diff += add_block
            elif element == "-":
                row_diff += remove_block
            elif element == "1":
                row_diff += white_block
            else:
                row_diff += black_block
        return row_diff

    for i in range(16):
        print(f"{get_row(i,a)}\t{get_row_diff(i,diff_list)}\t{get_row(i,b)}{new_line}")
