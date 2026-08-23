"""Representation and bitmap operations for a single Unifont glyph."""

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, cast
from unicodedata import name

from PIL import Image as Img
from rich.console import Console
from rich.text import Text

from unifont_utils.base import CodePoint, FilePath, Validator
from unifont_utils.colors import (
    COLOR_MAP,
    COLOR_VALUE_MAP,
    RGBA,
    ColorScheme,
    resolve_color_scheme,
)
from unifont_utils.converter import Converter
from unifont_utils.patterns import ReplacePattern, SearchPattern

if TYPE_CHECKING:
    from unifont_utils.glyph_set import GlyphSet


def _pattern_matches(
    pattern_data: list[int],
    height: int,
    width: int,
    image_data: list[int],
    image_width: int,
    row: int,
    col: int,
) -> bool:
    """Return whether every set pixel in a pattern exists at ``(row, col)``."""
    return all(
        pattern_data[y * width + x] != 1 or image_data[(row + y) * image_width + (col + x)] == 1
        for y in range(height)
        for x in range(width)
    )


def _apply_pattern_to_data(
    pattern_data: list[int],
    height: int,
    width: int,
    image_data: list[int],
    image_width: int,
    row: int,
    col: int,
) -> None:
    """Apply a replacement pattern to mutable glyph data at ``(row, col)``."""
    for y in range(height):
        for x in range(width):
            pixel = pattern_data[y * width + x]
            if pixel in {0, 1}:
                image_data[(row + y) * image_width + (col + x)] = pixel


@dataclass
class Glyph:
    """A single 8x16 or 16x16 GNU Unifont glyph."""

    _code_point: str
    _width: int = field(default_factory=int)
    _hex_str: str = field(default_factory=str)
    _data: list[int] = field(default_factory=list)
    _color_scheme: ColorScheme = field(default_factory=ColorScheme)

    def __post_init__(self) -> None:
        """Normalize the glyph code point."""
        self._code_point = Validator.code_point(self._code_point)

    def __str__(self) -> str:
        """Return a readable representation of this glyph."""
        display_code_point = Validator.code_point_display(self._code_point)
        return f"Unifont Glyph (U+{display_code_point})"

    def __add__(self, other: "Glyph") -> "GlyphSet":
        """Create a glyph set containing this glyph and another glyph."""
        from unifont_utils.glyph_set import GlyphSet

        glyphs = GlyphSet()
        glyphs += self
        glyphs += other
        return glyphs

    @property
    def code_point(self) -> str:
        """Normalized code point represented by the glyph."""
        return self._code_point

    @property
    def width(self) -> int:
        """Glyph width in pixels."""
        if not self._width and self.hex_str:
            self._width = 16 if len(self.hex_str) == 64 else 8
        return self._width

    @property
    def hex_str(self) -> str:
        """Glyph data in GNU Unifont ``.hex`` format."""
        if not self._hex_str and self._data:
            self._hex_str = Converter.to_hex(self._data)
        return self._hex_str

    @hex_str.setter
    def hex_str(self, hex_str: str) -> None:
        self.load_hex(hex_str)

    @property
    def data(self) -> list[int]:
        """Copy of the row-major binary pixel data."""
        if not self._data and self.hex_str:
            self._data = Converter.to_img_data(self.hex_str, self.width)
        return self._data.copy()

    @data.setter
    def data(self, data: list[int]) -> None:
        if len(data) not in {8 * 16, 16 * 16}:
            raise ValueError("Glyph data must contain exactly 128 or 256 pixels.")
        hex_str = Converter.to_hex(data)
        self._data = data.copy()
        self._hex_str = hex_str
        self._width = len(data) // 16

    def update_data_at_index(self, index: int, value: int) -> None:
        """Set one glyph pixel to ``0`` or ``1``.

        Raises:
            IndexError: If the index is outside the glyph bitmap.
            ValueError: If the new value is not ``0`` or ``1``.
        """
        if isinstance(value, bool) or not isinstance(value, int) or value not in {0, 1}:
            raise ValueError("Glyph pixel value must be 0 or 1.")

        data = self.data
        if not 0 <= index < len(data):
            raise IndexError(f"Glyph pixel index out of range: {index}")
        data[index] = value
        self.data = data

    @property
    def color_scheme(self) -> ColorScheme:
        """Color scheme used to render this glyph."""
        return self._color_scheme

    @color_scheme.setter
    def color_scheme(self, scheme: str | ColorScheme) -> None:
        self._color_scheme = resolve_color_scheme(scheme)

    @staticmethod
    def auto_detect_color_scheme(width: int, rgba_values: list[RGBA]) -> str:
        """Detect a supported two-color scheme from row-major RGBA pixels."""
        if isinstance(width, bool) or not isinstance(width, int) or width <= 0:
            raise ValueError("Image width must be a positive integer.")
        if not rgba_values:
            raise ValueError("Cannot detect a color scheme from an empty image.")
        if any(pixel not in COLOR_VALUE_MAP for pixel in rgba_values):
            raise ValueError("Invalid pixel RGBA values.")

        colors = set(rgba_values)
        if len(colors) > 2:
            raise ValueError("A glyph image must contain at most two supported colors.")

        if len(colors) == 1:
            only_color = COLOR_VALUE_MAP[next(iter(colors))]
            return {
                "white": "black_and_white",
                "black": "inverted_black_and_white",
                "transparent": "transparent_and_white",
            }[only_color]

        transparent = (0, 0, 0, 0)
        if transparent in colors:
            background_value = transparent
        else:
            background_value = rgba_values[min(width - 1, len(rgba_values) - 1)]
        foreground_value = next(iter(colors - {background_value}))
        background = COLOR_VALUE_MAP[background_value]
        foreground = COLOR_VALUE_MAP[foreground_value]

        schemes = {
            ("black", "white"): "inverted_black_and_white",
            ("white", "black"): "black_and_white",
            ("transparent", "white"): "transparent_and_white",
            ("transparent", "black"): "transparent_and_black",
        }
        try:
            return schemes[(background, foreground)]
        except KeyError as exc:
            raise ValueError("Invalid foreground and background color combination.") from exc

    @property
    def character(self) -> str:
        """Unicode character represented by the glyph."""
        return chr(int(self._code_point, 16))

    @property
    def unicode_name(self) -> str:
        """Unicode name of the glyph, or an empty string when unnamed."""
        try:
            return name(self.character)
        except ValueError:
            return ""

    def load_hex(self, hex_str: str) -> None:
        """Replace glyph data from a GNU Unifont ``.hex`` payload."""
        normalized = Validator.hex_str(hex_str)
        width = 16 if len(normalized) == 64 else 8
        self._hex_str = normalized
        self._width = width
        self._data = Converter.to_img_data(normalized, width)

    def load_img(
        self,
        img_path: FilePath,
        *,
        color_auto_detect: bool = True,
        color_scheme: str | ColorScheme | None = None,
    ) -> None:
        """Replace glyph data from an 8x16 or 16x16 image."""
        if color_scheme is None and not color_auto_detect:
            raise ValueError("Specify a color scheme when automatic detection is disabled.")

        resolved_scheme = resolve_color_scheme(color_scheme) if color_scheme is not None else None
        resolved_path = Validator.file_path(img_path)
        if not resolved_path.is_file():
            raise FileNotFoundError(f"File not found: {resolved_path}")

        with Img.open(resolved_path) as source, source.convert("RGBA") as image:
            if image.size not in {(8, 16), (16, 16)}:
                raise ValueError("Glyph image dimensions must be 8x16 or 16x16 pixels.")
            rgba_values = list(cast(Iterable[RGBA], cast(object, image.getdata())))
            if color_auto_detect and color_scheme is None:
                resolved_scheme = ColorScheme(
                    self.auto_detect_color_scheme(image.size[0], rgba_values)
                )
            width = image.size[0]

        if resolved_scheme is None:  # pragma: no cover - guarded by input validation
            raise ValueError("Failed to determine color scheme.")

        try:
            data = [resolved_scheme.color_map[COLOR_VALUE_MAP[pixel]] for pixel in rgba_values]
        except KeyError as exc:
            raise ValueError(
                f"Pixel color is not part of the selected scheme: {exc.args[0]}"
            ) from exc

        self._color_scheme = resolved_scheme
        self._width = width
        self._data = data
        self._hex_str = Converter.to_hex(data)

    @classmethod
    def init_from_hex(cls, code_point: CodePoint, hex_str: str) -> "Glyph":
        """Create a glyph from a code point and ``.hex`` payload."""
        normalized_hex = Validator.hex_str(hex_str)
        width = 16 if len(normalized_hex) == 64 else 8
        return cls(
            Validator.code_point(code_point),
            _width=width,
            _hex_str=normalized_hex,
        )

    @classmethod
    def init_from_img(
        cls,
        code_point: CodePoint,
        img_path: FilePath,
        *,
        color_auto_detect: bool = True,
        color_scheme: str | ColorScheme | None = None,
    ) -> "Glyph":
        """Create a glyph from a code point and image file."""
        glyph = cls(Validator.code_point(code_point))
        glyph.load_img(
            img_path,
            color_auto_detect=color_auto_detect,
            color_scheme=color_scheme,
        )
        return glyph

    def save_img(
        self,
        save_path: FilePath,
        img_format: str = "PNG",
        color_scheme: str | ColorScheme | None = None,
    ) -> None:
        """Save the glyph as a PNG or BMP image."""
        resolved_path = Validator.file_path(save_path)
        resolved_format = img_format.upper()
        if resolved_format not in {"PNG", "BMP"}:
            raise ValueError("Invalid image format. The image format must be PNG or BMP.")

        data = self.data
        if len(data) != self.width * 16:
            raise ValueError("Invalid glyph data or size.")

        scheme = (
            resolve_color_scheme(color_scheme) if color_scheme is not None else self.color_scheme
        )
        if resolved_format == "BMP":
            if scheme.name == "transparent_and_black":
                scheme = ColorScheme("black_and_white")
            elif scheme.name == "transparent_and_white":
                scheme = ColorScheme("inverted_black_and_white")

        color_names = {value: color_name for color_name, value in scheme.color_map.items()}
        rgba_data = [COLOR_MAP[color_names[pixel]] for pixel in data]
        with Img.new("RGBA", (self.width, 16)) as image:
            image.putdata(rgba_data)
            image.save(resolved_path, resolved_format)

    def print_glyph(
        self,
        *,
        color_scheme: str | ColorScheme | None = None,
        display_hex: bool = False,
        display_bin: bool = False,
    ) -> None:
        """Print this glyph to the console using Rich."""
        console = Console()
        white_block = "white on white"
        black_block = "black on black"
        scheme = (
            resolve_color_scheme(color_scheme) if color_scheme is not None else self.color_scheme
        )
        if scheme.name in {"inverted_black_and_white", "transparent_and_black"}:
            white_block, black_block = black_block, white_block

        data = self.data
        hex_length = self.width // 4 if display_hex else 0
        for row in range(16):
            row_text = Text()
            for col in range(self.width):
                style = white_block if data[row * self.width + col] else black_block
                row_text.append("  ", style=style)

            if display_hex or display_bin:
                prefix: list[str] = []
                if display_hex:
                    prefix.append(self.hex_str[row * hex_length : (row + 1) * hex_length])
                if display_bin:
                    prefix.append(
                        "".join(str(data[row * self.width + col]) for col in range(self.width))
                    )
                prefix_text = "\t".join(prefix)
                row_text = Text(f"{prefix_text}\t").append_text(row_text)
            console.print(row_text)

    def replace(self, search_pattern: SearchPattern, replace_pattern: ReplacePattern) -> None:
        """Replace every match of one pattern with another pattern."""
        if search_pattern.width > self.width or replace_pattern.width > self.width:
            raise ValueError("The pattern is wider than the glyph.")
        if (search_pattern.width, search_pattern.height) != (
            replace_pattern.width,
            replace_pattern.height,
        ):
            raise ValueError("The two patterns must have the same dimensions.")

        image_data = self.data
        for row, col in self.find_matches(search_pattern):
            _apply_pattern_to_data(
                replace_pattern.data,
                replace_pattern.height,
                replace_pattern.width,
                image_data,
                self.width,
                row,
                col,
            )
        self.data = image_data

    def find_matches(self, search_pattern: SearchPattern) -> list[tuple[int, int]]:
        """Return coordinates where a search pattern matches this glyph."""
        if search_pattern.width > self.width:
            raise ValueError("The pattern is wider than the glyph.")

        data = self.data
        return [
            (row, col)
            for row in range(16 - search_pattern.height + 1)
            for col in range(self.width - search_pattern.width + 1)
            if _pattern_matches(
                search_pattern.data,
                search_pattern.height,
                search_pattern.width,
                data,
                self.width,
                row,
                col,
            )
        ]

    def apply_pattern(self, row: int, col: int, replace_pattern: ReplacePattern) -> None:
        """Apply a replacement pattern at the specified coordinates."""
        if row < 0 or row + replace_pattern.height > 16:
            raise ValueError("The pattern is out of bounds.")
        if col < 0 or col + replace_pattern.width > self.width:
            raise ValueError("The pattern is out of bounds.")

        data = self.data
        _apply_pattern_to_data(
            replace_pattern.data,
            replace_pattern.height,
            replace_pattern.width,
            data,
            self.width,
            row,
            col,
        )
        self.data = data


__all__ = ["Glyph"]
