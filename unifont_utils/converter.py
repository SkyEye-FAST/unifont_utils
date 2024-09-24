# -*- encoding: utf-8 -*-
"""Unifont Utils - Converter"""

from functools import reduce
from typing import List


class Converter:
    """Class for converters."""

    @staticmethod
    def to_hex(data: List[int]) -> str:
        """Convert glyph pixel data to Unifont `.hex` format string.

        Args:
            data (List[int]): Glyph pixel data in the image, stored as `0` and `1`.

        Returns:
            str: The Unifont `.hex` format string.

        Raises:
            ValueError: If the glyph data is empty.
        """

        if not data:
            raise ValueError(
                "Unable to convert to .hex string. The glyph data is empty."
            )

        n = reduce(lambda acc, pixel: (acc << 1) | (1 if pixel else 0), data, 0)
        return hex(n)[2:].upper().zfill(32 if len(data) == 128 else 64)

    @staticmethod
    def to_img_data(hex_str: str, width: int = 16, height: int = 16) -> List[int]:
        """Convert Unifont `.hex` format string to glyph pixel data.

        Args:
            hex_str (str): The Unifont `.hex` format string.
            width (int, optional): The width of the glyph in pixels. Defaults to `16`.
            height (int, optional): The height of the glyph in pixels. Defaults to `16`.

        Returns:
            List[int]: The glyph pixel data in the image, stored as `0` and `1`.
        """

        if not hex_str:
            return []

        return [(int(hex_str, 16) >> i) & 1 for i in range(width * height - 1, -1, -1)]
