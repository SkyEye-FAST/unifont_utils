# -*- encoding: utf-8 -*-
"""Unifont Utils - Glyphs"""

from typing import Dict, Tuple, Optional, Union
from unicodedata import name
from dataclasses import dataclass

from .converter import HexConverter


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


@dataclass
class Glyph:
    """A class representing a single glyph in Unifont."""

    code_point: str
    hex_str: Optional[str] = None

    def __post_init__(self) -> None:
        self.code_point = validate_code_point(self.code_point)
        self.hex_str = validate_hex_str(self.hex_str)
        self.__converter = HexConverter(self.hex_str)
        self.img_data = self.__converter.to_img_data()
        try:
            self.unicode_name = name(chr(int(self.code_point, 16)))
        except ValueError:
            self.unicode_name = ""

    def __str__(self) -> str:
        code_point = self.code_point
        if len(self.code_point) == 6 and self.code_point.startswith("0"):
            code_point = code_point[1:]
        return f"Unifont Glyph (U+{code_point})"

    def print_glyph(
        self,
        *,
        black_and_white: Optional[bool] = None,
        display_hex: bool = False,
        display_bin: bool = False,
    ) -> None:
        """Print a Unifont glyph to the console.

        Args:
            black_and_white (bool, optional): Whether it is a black and white image.

                Defaults to the one specified during class initialization.

                If `True`, `0` is white and `1` is black.

                If `False`, `0` is transparent and `1` is white.
            display_hex (bool, optional): Whether to display the hexadecimal strings.

                Defaults to `False`.

                If `True`, the hexadecimal string of each line will be displayed on the left.

            display_bin (bool, optional): Whether to display the binary strings.

                Defaults to `False`.

                If `True`, the binary string of each line will be displayed on the left.
        """

        self.__converter.print_glyph(
            black_and_white=black_and_white,
            display_hex=display_hex,
            display_bin=display_bin,
        )


class GlyphSet:
    """A class representing a set of glyphs in Unifont."""

    def __init__(self) -> None:
        self.glyphs: Dict[str, Glyph] = {}

    def __str__(self) -> str:
        return f"Unifont Glyph Set ({len(self.glyphs)} glyphs)"

    def __getitem__(self, code_point: str) -> Glyph:
        return self.get_glyph(code_point)

    def __setitem__(self, code_point: str, hex_str: str) -> None:
        self.add_glyph((code_point, hex_str))

    def __delitem__(self, code_point: str) -> None:
        self.remove_glyph(code_point)

    def __add__(self, other: "GlyphSet") -> "GlyphSet":
        result = GlyphSet()
        result.glyphs = {**self.glyphs, **other.glyphs}
        return result

    def __iadd__(self, other: "GlyphSet") -> "GlyphSet":
        self.glyphs = {**self.glyphs, **other.glyphs}
        return self

    def __len__(self) -> int:
        return len(self.glyphs)

    def __iter__(self) -> "GlyphSet":
        return iter(self.glyphs.values())

    def __contains__(self, code_point: str) -> bool:
        return validate_code_point(code_point) in self.glyphs

    def initialize_glyphs(self, code_points: Union[str, Tuple[str, str]]) -> None:
        """Initialize a set of glyphs.

        Args:
            code_points (Union[str, Tuple[str, str]]): The code points to initialize.
                If a string is provided, it should be a comma-separated list of code points.
                If a tuple is provided, it should be in the format of `(begin, end)`.
        """

        if not isinstance(code_points, (str, tuple)):
            raise TypeError(
                "Invalid type for code_points. "
                "The argument must be either a string or a tuple of two strings."
            )
        if isinstance(code_points, str):
            code_points = (
                code_points.split(",") if "," in code_points else [code_points]
            )
        if isinstance(code_points, tuple):
            if len(code_points) != 2:
                raise ValueError(
                    "The tuple must contain exactly two elements (begin, end)."
                )
            begin_code_point, end_code_point = code_points
            code_points = range(int(begin_code_point, 16), int(end_code_point, 16) + 1)

        for code_point in code_points:
            code_point = validate_code_point(code_point)
            self.add_glyph((code_point, ""))

    def get_glyph(self, code_point: str) -> Glyph:
        """Get a glyph by its code point.

        Args:
            code_point (str): The code point of the glyph to get.

        Returns:
            Glyph: The obtained glyph.
        """

        code_point = validate_code_point(code_point)
        if code_point not in self.glyphs:
            raise KeyError(f"Glyph with code point U+{code_point} not found.")

        return self.glyphs[code_point]

    def add_glyph(self, glyph: Union[Glyph, Tuple[str, str]]) -> None:
        """Add a glyph to the set.

        Args:
            glyph (Union[Glyph, Tuple[str, str]]): The glyph to add.

                If a tuple is provided, it should be in the format of `(code_point, hex_str)`.
        """

        if not isinstance(glyph, (Glyph, tuple)):
            raise TypeError(
                "Invalid type for glyph. "
                "The argument must be either a Glyph object or a tuple of two strings."
            )
        if isinstance(glyph, tuple):
            code_point, hex_str = glyph
        else:
            code_point, hex_str = glyph.code_point, glyph.hex_str

        code_point = validate_code_point(code_point)
        hex_str = validate_hex_str(hex_str)

        if code_point in self.glyphs:
            raise ValueError(
                f"Glyph with code point U+{code_point} already exists. "
                "Use update_glyph method instead."
            )

        self.glyphs[code_point] = Glyph(code_point, hex_str)

    def remove_glyph(self, code_point: str) -> None:
        """Remove a glyph from the set.

        Args:
            code_point (str): The code point of the glyph to remove.
        """

        code_point = validate_code_point(code_point)
        if code_point not in self.glyphs:
            raise KeyError(f"Glyph with code point U+{code_point} not found.")

        del self.glyphs[code_point]

    def update_glyph(self, glyph: Union[Glyph, Tuple[str, str]]) -> None:
        """Update a glyph in the set.

        Args:
            glyph (Union[Glyph, Tuple[str, str]]): The new glyph to update.

                If a tuple is provided, it should be in the format of `(code_point, hex_str)`.
        """

        if not isinstance(glyph, (Glyph, tuple)):
            raise TypeError(
                "Invalid type for glyph. "
                "The argument must be either a Glyph object or a tuple of two strings."
            )
        if isinstance(glyph, tuple):
            code_point, hex_str = glyph
            glyph = Glyph(code_point, hex_str)
        else:
            code_point, hex_str = glyph.code_point, glyph.hex_str

        code_point = validate_code_point(code_point)
        hex_str = validate_hex_str(hex_str)

        if not validate_code_point(code_point):
            raise ValueError("Invalid code point.")

        if code_point not in self.glyphs:
            raise KeyError(f"Glyph with code point U+{code_point} not found.")

        self.glyphs[code_point].hex_str = hex_str
