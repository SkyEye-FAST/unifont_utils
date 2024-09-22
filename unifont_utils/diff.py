# -*- encoding: utf-8 -*-
"""Unifont Utils - Diff"""

from typing import List, Union

from .converter import HexConverter
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

    if not isinstance(glyph, (str, Glyph)):
        raise TypeError("The glyph must be either a .hex string or a Glyph object.")

    return HexConverter(glyph).data if isinstance(glyph, str) else glyph.data


def diff_glyphs(glyph_a: Union[str, Glyph], glyph_b: Union[str, Glyph]) -> List[int]:
    """Compares two glyphs and returns a list of differences.

    Args:
        glyph_a (Union[str, Glyph]): The first glyph to compare.
        glyph_b (Union[str, Glyph]): The second glyph to compare.

    Returns:
        List[int]: A list of differences between the two glyphs.

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

    white_block, black_block, add_block, remove_block, new_line = (
        "\033[48;5;7m  ",  # White
        "\033[48;5;0m  ",  # Black
        "\033[48;5;2m  ",  # Green
        "\033[48;5;1m  ",  # Red
        "\033[0m",
    )

    if black_and_white:
        white_block, black_block = black_block, white_block

    width = len(a) // 16

    def get_row(i: int, data: List[str]) -> str:
        row_data = data[i * width : (i + 1) * width]
        return "".join(white_block if pixel else black_block for pixel in row_data)

    def get_row_diff(i: int) -> str:
        row_diff = {
            "+": add_block,
            "-": remove_block,
            "1": white_block,
            "0": black_block,
        }
        return "".join(
            row_diff[element] for element in diff_list[i * width : (i + 1) * width]
        )

    for i in range(16):
        print(f"{get_row(i, a)}\t{get_row_diff(i)}\t{get_row(i, b)}{new_line}")


def replace_pattern(img_data, pattern_a, pattern_b, pattern_width) -> List[int]:
    """Replaces a pattern in an image with another pattern.

    Args:
        img_data (List[int]): The image data to be modified.
        pattern_a (List[int]): The pattern to be replaced.
        pattern_b (List[int]): The new pattern to replace the old one.
        pattern_width (int): The width of the patterns.

    Returns:
        List[int]: The modified image data.

    Raises:
        ValueError: If the two patterns have different sizes.
    """

    if len(pattern_a) != len(pattern_b):
        raise ValueError("The two patterns must have the same size.")
    image_width = len(img_data) // 16
    pattern_height = len(pattern_a) // pattern_width

    def match_pattern(img_data, pattern_a, i, j):
        for y in range(pattern_height):
            for x in range(pattern_width):
                if (
                    pattern_a[y * pattern_width + x] == 1
                    and img_data[(i + y) * image_width + (j + x)] != 1
                ):
                    return False
        return True

    def apply_new_pattern(img_data, pattern_a, pattern_b, i, j):
        for y in range(pattern_height):
            for x in range(pattern_width):
                if pattern_b[y * pattern_width + x] == 1:
                    img_data[(i + y) * image_width + (j + x)] = 1
                elif (
                    pattern_b[y * pattern_width + x] == 0
                    and pattern_a[y * pattern_width + x] == 1
                ):
                    continue

    for i in range(16 - pattern_height + 1):
        for j in range(image_width - pattern_width + 1):
            if match_pattern(img_data, pattern_a, i, j):
                apply_new_pattern(img_data, pattern_a, pattern_b, i, j)

    return img_data
