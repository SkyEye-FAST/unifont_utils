# @Author: SkyEye_FAST <skyeyefast@foxmail.com>
# @Copyright: Copyright (C) 2024-2025 SkyEye_FAST
"""Unifont Utils - Converter"""


class Converter:
    """Class for converters."""

    @staticmethod
    def to_hex(data: list[int]) -> str:
        """Convert glyph pixel data to Unifont `.hex` format string.

        Args:
            data (list[int]): Glyph pixel data in the image, stored as `0` and `1`.

        Returns:
            str: The Unifont `.hex` format string.

        Raises:
            ValueError: If the glyph data is empty.
        """
        if not data:
            raise ValueError("Unable to convert to .hex string. The glyph data is empty.")

        n = sum((pixel & 1) << i for i, pixel in enumerate(reversed(data)))
        return f"{n:X}".zfill(32 if len(data) == 128 else 64)

    @staticmethod
    def to_img_data(hex_str: str, width: int = 16, height: int = 16) -> list[int]:
        """Convert Unifont `.hex` format string to glyph pixel data.

        Args:
            hex_str (str): The Unifont `.hex` format string.
            width (int, optional): The width of the glyph in pixels. Defaults to `16`.
            height (int, optional): The height of the glyph in pixels. Defaults to `16`.

        Returns:
            list[int]: The glyph pixel data in the image, stored as `0` and `1`.
        """
        if not hex_str:
            return []

        return [(int(hex_str, 16) >> i) & 1 for i in range(width * height - 1, -1, -1)]
