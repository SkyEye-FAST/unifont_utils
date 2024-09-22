# -*- encoding: utf-8 -*-
"""Unifont Utils - Glyphs"""

from typing import Dict, Tuple, Optional, Union
from unicodedata import name
from dataclasses import dataclass

from .base import (
    validate_code_point,
    validate_code_points,
    validate_hex_str,
    CodePoint,
    CodePoints,
)
from .converter import HexConverter


@dataclass
class Glyph:
    """A class representing a single glyph in Unifont."""

    code_point: CodePoint
    hex_str: Optional[str] = None

    def __post_init__(self) -> None:
        self.code_point = validate_code_point(self.code_point)
        self.hex_str = validate_hex_str(self.hex_str)
        self.__converter = HexConverter(self.hex_str)
        self.data = self.__converter.data
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

    def __getitem__(self, code_point: CodePoint) -> Glyph:
        return self.get_glyph(code_point)

    def __setitem__(self, code_point: CodePoint, hex_str: str) -> None:
        self.add_glyph((code_point, hex_str))

    def __delitem__(self, code_point: CodePoint) -> None:
        self.remove_glyph(code_point)

    def __add__(self, other: Union["GlyphSet", Glyph]) -> "GlyphSet":
        result = GlyphSet()
        result.glyphs = self.glyphs.copy()
        if isinstance(other, Glyph):
            result.add_glyph(other)
        elif isinstance(other, GlyphSet):
            result.glyphs.update(other.glyphs)
        else:
            raise TypeError("Invalid type for addition to GlyphSet.")
        return result

    def __iadd__(self, other: Union["GlyphSet", Glyph]) -> "GlyphSet":
        if isinstance(other, Glyph):
            self.add_glyph(other)
        elif isinstance(other, GlyphSet):
            self.glyphs.update(other.glyphs)
        else:
            raise TypeError("Invalid type for in-place addition to GlyphSet.")
        return self

    def __len__(self) -> int:
        return len(self.glyphs)

    def __iter__(self) -> iter:
        return iter(self.glyphs.values())

    def __contains__(self, glyph: Union[Glyph, str]) -> bool:
        code_point = validate_code_point(
            glyph if isinstance(glyph, str) else glyph.code_point
        )
        return code_point in self.glyphs

    def initialize_glyphs(self, code_points: CodePoints) -> None:
        """Initialize a set of glyphs.

        Args:
            code_points (CodePoints): The code points to initialize.

                If a string is provided, it should be a comma-separated list of code points.

                If a tuple is provided, it should be in the format of `(begin, end)`.

                The code points specified should be hexadecimal number strings or integers.
        """

        code_points = validate_code_points(code_points)
        for code_point in code_points:
            self.add_glyph((code_point, ""))

    def get_glyph(self, code_point: CodePoint) -> Glyph:
        """Get a glyph by its code point.

        Args:
            code_point (CodePoint): The code point of the glyph to get.

        Returns:
            Glyph: The obtained glyph.
        """

        code_point = validate_code_point(code_point)
        try:
            return self.glyphs[code_point]
        except KeyError as exc:
            raise KeyError(f"Glyph with code point U+{code_point} not found.") from exc

    def get_glyphs(
        self, code_points: CodePoints, *, skip_empty: bool = True
    ) -> "GlyphSet":
        """Get a set of glyphs by their code points.

        Args:
            code_points (CodePoints): The code points of the glyphs to get.

                If a string is provided, it should be a comma-separated list of code points.

                If a tuple is provided, it should be in the format of `(begin, end)`.

                The code points specified should be hexadecimal number strings.
            skip_empty (bool, optional): Whether to skip empty glyphs. Defaults to `True`.

                If `True`, empty glyphs will be skipped.

                If `False`, empty glyphs will be included with empty .hex strings.

        Returns:
            GlyphSet: The obtained set of glyphs.
        """

        result = GlyphSet()
        code_points = validate_code_points(code_points)
        for code_point in code_points:
            if code_point in self.glyphs:
                result.add_glyph(self.glyphs[code_point])
            elif not skip_empty:
                result.add_glyph((code_point, ""))
        return result

    def add_glyph(self, glyph: Union[Glyph, Tuple[CodePoint, str]]) -> None:
        """Add a glyph to the set.

        Args:
            glyph (Union[Glyph, Tuple[CodePoint, str]]): The glyph to add.

                If a tuple is provided, it should be in the format of `(code_point, hex_str)`.
        """

        glyph_obj = self._validate_and_create_glyph(glyph)
        if glyph_obj.code_point in self.glyphs:
            raise ValueError(
                f"Glyph with code point U+{glyph_obj.code_point} already exists."
            )
        self.glyphs[glyph_obj.code_point] = glyph_obj

    def remove_glyph(self, code_point: CodePoint) -> None:
        """Remove a glyph from the set.

        Args:
            code_point (CodePoint): The code point of the glyph to remove.
        """

        code_point = validate_code_point(code_point)
        if code_point not in self.glyphs:
            raise KeyError(f"Glyph with code point U+{code_point} not found.")
        del self.glyphs[code_point]

    def update_glyph(self, glyph: Union[Glyph, Tuple[CodePoint, str]]) -> None:
        """Update a glyph in the set.

        Args:
            glyph (Union[Glyph, Tuple[CodePoint, str]]): The new glyph to update.

                If a tuple is provided, it should be in the format of `(code_point, hex_str)`.
        """

        glyph_obj = self._validate_and_create_glyph(glyph)
        if glyph_obj.code_point not in self.glyphs:
            raise KeyError(f"Glyph with code point U+{glyph_obj.code_point} not found.")
        self.glyphs[glyph_obj.code_point].hex_str = glyph_obj.hex_str

    def sort_glyphs(self) -> None:
        """Sort the glyphs in the set by their code points."""

        if not self.glyphs:
            raise ValueError("Cannot sort an empty glyph set.")
        self.glyphs = dict(sorted(self.glyphs.items(), key=lambda x: int(x[0], 16)))

    def _validate_and_create_glyph(
        self, glyph: Union[Glyph, Tuple[CodePoint, str]]
    ) -> Glyph:
        """Helper function to validate and create a Glyph object."""
        if isinstance(glyph, Glyph):
            return glyph
        if isinstance(glyph, tuple):
            code_point, hex_str = glyph
            code_point = validate_code_point(code_point)
            hex_str = validate_hex_str(hex_str)
            return Glyph(code_point, hex_str)
        raise TypeError(
            "Invalid glyph type. Must be a Glyph or a tuple (code_point, hex_str)."
        )
