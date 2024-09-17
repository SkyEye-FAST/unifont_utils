# -*- encoding: utf-8 -*-
"""Unifont Utils - Base Module"""

from typing import Optional


def validate_code_point(code_point: str) -> str:
    """Validate a code point string and return its normalized form.

    Args:
        code_point (str): The code point string to validate.

    Returns:
        str: The normalized code point if valid.

    Raises:
        ValueError: If the code point is invalid.
    """

    if not code_point.isalnum() or len(code_point) >= 7:
        raise ValueError("Invalid code point.")

    code_point = code_point.upper()

    if not all(c in "0123456789ABCDEF" for c in code_point):
        raise ValueError("Invalid character in code point.")

    if len(code_point) >= 5:
        return code_point.zfill(6)
    return code_point.zfill(4)


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
