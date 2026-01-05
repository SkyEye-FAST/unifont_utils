# @Author: SkyEye_FAST <skyeyefast@foxmail.com>
# @Copyright: Copyright (C) 2024-2026 SkyEye_FAST
"""Unifont Utils - Converter"""

from collections.abc import Iterable


class Converter:
    """Class for converters."""

    @staticmethod
    def to_hex(data: Iterable[int]) -> str:
        """Convert glyph pixel data to a Unifont `.hex` string.

        Args:
            data (Iterable[int]): Glyph pixels stored as `0` or `1`.

        Returns:
            str: The `.hex` string representing the glyph.

        Raises:
            ValueError: If the input is empty or contains values other than `0` or `1`.
        """
        bits = [int(bit) for bit in data]
        if not bits:
            raise ValueError("Unable to convert to .hex string. The glyph data is empty.")
        if any(bit not in (0, 1) for bit in bits):
            raise ValueError("Glyph data must contain only 0 or 1 values.")

        return f"{int(''.join(str(bit) for bit in bits), 2):0{((len(bits) + 3) // 4)}X}"

    @staticmethod
    def to_img_data(hex_str: str, width: int = 16, height: int = 16) -> list[int]:
        """Convert a Unifont `.hex` string to glyph pixel data.

        Args:
            hex_str (str): The `.hex` string to decode.
            width (int): Glyph width in pixels.
            height (int): Glyph height in pixels.

        Returns:
            list[int]: Glyph pixels as `0` and `1` values ordered row-major from top-left.

        Raises:
            ValueError: If the hex string is invalid or exceeds the expected size.
        """
        stripped = hex_str.strip()
        if not stripped:
            return []

        bit_length = width * height
        if len(stripped) > (bit_length + 3) // 4:
            raise ValueError("Hex string is longer than the expected glyph size.")

        try:
            value = int(stripped, 16)
        except ValueError as exc:
            raise ValueError("Invalid hex string for glyph data.") from exc

        return [(value >> i) & 1 for i in range(bit_length - 1, -1, -1)]
