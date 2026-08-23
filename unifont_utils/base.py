# @Author: SkyEye_FAST <skyeyefast@foxmail.com>
# @Copyright: Copyright (C) 2024-2026 SkyEye_FAST
"""Unifont Utils - Base Module"""

from collections.abc import Iterable
from pathlib import Path
from typing import TypeAlias

# Type aliases
FilePath: TypeAlias = str | Path
CodePoint: TypeAlias = str | int
CodePoints: TypeAlias = Iterable[CodePoint]


class Validator:
    """Helpers for validating common Unifont values."""

    HEX_CHARS = frozenset("0123456789ABCDEF")

    @staticmethod
    def code_point(code_point: CodePoint) -> str:
        """Validate a code point string and return its normalized form.

        Args:
            code_point (CodePoint): Code point as an integer or hexadecimal string.

        Returns:
            str: Normalized uppercase code point.

        Raises:
            TypeError: If the code point is not a string or an integer.
            ValueError: If the code point is invalid.
        """
        if isinstance(code_point, bool):
            raise TypeError("Invalid code point type. Must be a string or integer.")
        if isinstance(code_point, int):
            if code_point < 0:
                raise ValueError(f"Invalid code point: {code_point}.")
            code_point = f"{code_point:X}"
        elif not isinstance(code_point, str):
            raise TypeError("Invalid code point type. Must be a string or integer.")

        normalized = code_point.upper()
        if not normalized or any(character not in Validator.HEX_CHARS for character in normalized):
            raise ValueError(f"Invalid code point: {code_point}.")
        if int(normalized, 16) > 0x10FFFF:
            raise ValueError(f"Invalid code point: {code_point}.")

        return normalized.zfill(6 if len(normalized) > 4 else 4)

    @staticmethod
    def code_point_display(code_point: CodePoint) -> str:
        """Return a formatted code point string for display.

        Pads to 4 digits when shorter, preserves 5-digit width (does not
        zero-pad to 6), and keeps 6-digit values as-is. Always uppercase.

        Args:
            code_point (CodePoint): Input code point string or integer.

        Returns:
            str: Display-ready code point string.
        """
        normalized = Validator.code_point(code_point)
        if len(normalized) == 6 and normalized.startswith("0") and normalized[1] != "0":
            return normalized[1:]
        return normalized

    @staticmethod
    def code_points(code_points: CodePoints) -> list[str]:
        """Validate a sequence of code points and return normalized list.

        Args:
            code_points (CodePoints): Sequence or set of code points to validate.

        Returns:
            list[str]: Normalized list of code point strings.

        Raises:
            TypeError: If the code points are not a sequence or set.
            ValueError: If the code points are invalid.
        """
        if isinstance(code_points, (str, bytes)) or not isinstance(code_points, Iterable):
            raise TypeError("Code points must be an iterable of strings or integers.")

        normalized = [Validator.code_point(code_point) for code_point in code_points]
        return list(dict.fromkeys(normalized))

    @staticmethod
    def hex_str(hex_str: str | None) -> str:
        """Validate a hexadecimal string and return its normalized form.

        Args:
            hex_str (str | None): The hexadecimal string to validate.

        Returns:
            str: Normalized hexadecimal string.

        Raises:
            ValueError: If the hexadecimal string is invalid.
        """
        if hex_str is None or hex_str == "":
            return ""
        if not isinstance(hex_str, str):
            raise TypeError("The .hex value must be a string or None.")

        hex_str = hex_str.upper()

        if len(hex_str) not in {32, 64}:
            raise ValueError(f"Invalid .hex string length: {hex_str} (length: {len(hex_str)}).")

        for c in hex_str:
            if c not in Validator.HEX_CHARS:
                raise ValueError(f"Invalid character in .hex string: {c}.")

        return hex_str

    @staticmethod
    def file_path(file_path: FilePath) -> Path:
        """Validate a file path and return its normalized form.

        Args:
            file_path (FilePath): The file path to validate.

        Returns:
            Path: Normalized file path.

        Raises:
            TypeError: If the file path is not a string or a Path object.
        """
        if isinstance(file_path, str):
            return Path(file_path)
        if isinstance(file_path, Path):
            return file_path
        raise TypeError("The file path must be a string or a Path object.")
