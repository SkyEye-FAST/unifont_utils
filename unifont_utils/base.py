# -*- encoding: utf-8 -*-
"""Unifont Utils - Base Module"""

from pathlib import Path
from typing import List, Tuple, Optional, Union, TypeAlias

# Type aliases
FilePath: TypeAlias = Union[str, Path]
CodePoint: TypeAlias = Union[str, int]
CodePoints: TypeAlias = Union[str, Tuple[CodePoint, CodePoint]]


def validate_code_point(code_point: Union[str, int]) -> str:
    """Validate a code point string and return its normalized form.

    Args:
        code_point (str): The code point string to validate.

    Returns:
        str: The normalized code point if valid.

    Raises:
        ValueError: If the code point is invalid.
    """

    if not isinstance(code_point, (str, int)):
        raise ValueError("Invalid code point type. Must be a string or integer.")
    if isinstance(code_point, int):
        code_point = hex(code_point)[2:].upper()
    if not code_point.isalnum() or len(code_point) >= 7:
        raise ValueError("Invalid code point.")

    code_point = code_point.upper()

    if not all(c in "0123456789ABCDEF" for c in code_point):
        raise ValueError("Invalid character in code point.")

    if len(code_point) >= 5:
        return code_point.zfill(6)
    return code_point.zfill(4)


def validate_code_points(code_points: CodePoints) -> List[str]:
    """Validate a code point string or tuple and return its normalized form.

    Args:
        code_points (CodePoints): The code point string or tuple to validate.

    Returns:
        List[int]: The normalized code point tuple if valid.

    Raises:
        TypeError: If the code points are not a string or a tuple.
        ValueError: If the code points are invalid.
    """

    if not isinstance(code_points, (str, tuple)):
        raise TypeError(
            "Invalid type for the specified code points. "
            "The argument must be either a string or a tuple."
        )

    if isinstance(code_points, str):
        code_points_list = code_points.split(",")
    else:
        if len(code_points) != 2:
            raise ValueError("The tuple must contain exactly two elements (begin, end).")
        begin, end = code_points
        if not isinstance(begin, (str, int)) or not isinstance(end, (str, int)):
            raise TypeError("The begin and end code points must be strings or integers.")
        begin, end = validate_code_point(begin), validate_code_point(end)
        code_points_list = range(int(begin, 16), int(end, 16) + 1)
        code_points_list = [hex(i)[2:].zfill(4) for i in code_points_list]

    return [validate_code_point(code_point) for code_point in code_points_list]


def validate_hex_str(hex_str: Optional[str]) -> Optional[str]:
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

    if not all(c in "0123456789ABCDEF" for c in hex_str):
        raise ValueError("Invalid character in .hex string.")

    return hex_str.upper() if hex_str else ""


def validate_file_path(file_path: FilePath) -> Path:
    """Validate a file path and return its normalized form.

    Args:
        file_path (FilePath): The file path to validate.

    Returns:
        Path: The normalized file path if valid.

    Raises:
        TypeError: If the file path is not a string or a Path object.
    """

    if not isinstance(file_path, (str, Path)):
        raise TypeError("The file path must be a string or a Path object.")

    if isinstance(file_path, str):
        return Path(file_path)
    return file_path
