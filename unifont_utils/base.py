# -*- encoding: utf-8 -*-
"""Unifont Utils - Base Module"""

from pathlib import Path
from typing import List, Tuple, Optional, Union, TypeAlias

# Type aliases
FilePath: TypeAlias = Union[str, Path]
CodePoint: TypeAlias = Union[str, int]
CodePoints: TypeAlias = Union[str, Tuple[CodePoint, CodePoint]]


class Validator:
    """Class for validators."""

    @staticmethod
    def code_point(code_point: CodePoint) -> str:
        """Validate a code point string and return its normalized form.

        Args:
            code_point (CodePoint): The code point string to validate.

        Returns:
            str: The normalized code point if valid.

        Raises:
            ValueError: If the code point is invalid.
        """

        if isinstance(code_point, int):
            code_point = hex(code_point)[2:]
        elif isinstance(code_point, str):
            pass
        else:
            raise ValueError("Invalid code point type. Must be a string or integer.")

        if not code_point.isalnum() or len(code_point) >= 7:
            raise ValueError(f"Invalid code point: {code_point}.")

        code_point = code_point.upper()

        for c in code_point:
            if c not in "0123456789ABCDEF":
                raise ValueError(f"Invalid character in code point: {c}.")

        return code_point.zfill(6 if len(code_point) > 4 else 4)

    @staticmethod
    def code_points(code_points: CodePoints) -> List[str]:
        """Validate a code point string or tuple and return its normalized form.

        Args:
            code_points (CodePoints): The code point string or tuple to validate.

        Returns:
            List[int]: The normalized code point tuple if valid.

        Raises:
            TypeError: If the code points are not a string or a tuple.
            ValueError: If the code points are invalid.
        """

        if isinstance(code_points, str):
            code_points_list = code_points.split(",")
        elif isinstance(code_points, tuple):
            if len(code_points) != 2:
                raise ValueError(
                    "The tuple must contain exactly two elements (begin, end)."
                )
            begin, end = code_points
            if not isinstance(begin, (str, int)) or not isinstance(end, (str, int)):
                raise TypeError(
                    "The begin and end code points must be strings or integers."
                )
            begin, end = Validator.code_point(begin), Validator.code_point(end)
            code_points_list = range(int(begin, 16), int(end, 16) + 1)
            code_points_list = [hex(i)[2:].zfill(4) for i in code_points_list]
        else:
            raise TypeError(
                "Invalid type for the specified code points. "
                "The argument must be either a string or a tuple."
            )

        return [Validator.code_point(code_point) for code_point in code_points_list]

    @staticmethod
    def hex_str(hex_str: Optional[str]) -> Optional[str]:
        """Validate a hexadecimal string and return its normalized form.

        Args:
            hex_str (str, optional): The hexadecimal string to validate.

        Returns:
            str, optional: The normalized hexadecimal string if valid.

        Raises:
            ValueError: If the hexadecimal string is invalid.
        """

        if not hex_str:
            return ""

        if len(hex_str) not in {32, 64}:
            raise ValueError(
                f"Invalid .hex string length: {hex_str} (length: {len(hex_str)})."
            )

        for c in hex_str:
            if c not in "0123456789ABCDEF":
                raise ValueError(f"Invalid character in .hex string: {c}.")

        return hex_str.upper()

    @staticmethod
    def file_path(file_path: FilePath) -> Path:
        """Validate a file path and return its normalized form.

        Args:
            file_path (FilePath): The file path to validate.

        Returns:
            Path: The normalized file path if valid.

        Raises:
            TypeError: If the file path is not a string or a Path object.
        """

        if isinstance(file_path, str):
            return Path(file_path)
        if isinstance(file_path, Path):
            return file_path
        raise TypeError("The file path must be a string or a Path object.")
