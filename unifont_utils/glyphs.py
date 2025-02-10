# @Author: SkyEye_FAST <skyeyefast@foxmail.com>
# @Copyright: Copyright (C) 2024-2025 SkyEye_FAST
"""Unifont Utils - Glyphs"""

import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Optional, Union
from unicodedata import name

from PIL import Image as Img
from rich.console import Console
from rich.text import Text

from .base import (
    CodePoint,
    CodePoints,
    FilePath,
)
from .base import (
    Validator as Validator,
)
from .converter import Converter as Converter

COLOR_MAP = {
    "white": (255, 255, 255, 255),
    "black": (0, 0, 0, 255),
    "transparent": (0, 0, 0, 0),
}
COLOR_VALUE_MAP = {
    (255, 255, 255, 255): "white",
    (0, 0, 0, 255): "black",
    (0, 0, 0, 0): "transparent",
}


@dataclass
class Pattern:
    """A class to represent a pattern.

    Attributes:
        data (list[int]): The pattern data.
        width (int): The width of the pattern.
        height (Optional[int]): The height of the pattern.

    Raises:
        ValueError: If the size of the pattern is invalid.
    """

    data: list[int]
    """The pattern data."""
    _width: int
    """The width of the pattern."""
    _height: Optional[int] = None
    """The height of the pattern.
    If it is `None`, the height is set to the length of `data` divided by `width`.
    """

    def __post_init__(self) -> None:
        """Post-initialization method to validate the pattern."""
        if self._width <= 2:
            raise ValueError("The width must be greater than 2 pixels.")
        if self._width > 16:
            raise ValueError("The width must be less than 16 pixels.")
        if self._height is None:
            self._height = len(self.data) // self._width
            if len(self.data) % self._width != 0:
                raise ValueError("The length of the data must be divisible by width.")
        if self._height * self._width != len(self.data):
            raise ValueError("The length of the data must be equal to width * height.")
        if self._height <= 2:
            raise ValueError("The height must be greater than 2 pixels.")
        if self._height > 16:
            raise ValueError("The height must be less than 16 pixels.")

    def __str__(self) -> str:
        """Return the string representation of the pattern.

        Returns:
            str: The string representation of the pattern.
        """
        return f"Unifont Pattern ({self._width}x{self._height})"

    @property
    def width(self) -> int:
        """The width of the pattern."""
        return self._width

    @property
    def height(self) -> int:
        """The height of the pattern."""
        if self._height is None:
            self._height = len(self.data) // self._width
        return self._height

    @classmethod
    def init_from_img(cls, img_path: FilePath) -> "Pattern":
        """Create a new Pattern object from an image file.

        Args:
            img_path (FilePath): The path to the image file.

        Returns:
            Pattern: The created Pattern object.
        """
        img_path = Validator.file_path(img_path)
        if not img_path.is_file():
            raise FileNotFoundError(f"File not found: {img_path}")

        img = Img.open(img_path).convert("RGBA")
        data = []
        for pixel in img.getdata():  # type: ignore
            if pixel == (255, 255, 255, 255):
                data.append(0)
            elif pixel == (0, 0, 0, 255):
                data.append(1)
            elif pixel == (0, 0, 0, 0):
                data.append(-1)
            else:
                raise ValueError(f"Invalid pixel RGBA value: {pixel}")

        return cls(data, img.size[0], img.size[1])


@dataclass
class SearchPattern(Pattern):
    """A class to represent a pattern for searching."""

    def __post_init__(self) -> None:
        """Post-initialization method to validate the pattern.

        Raises:
            ValueError: If the pattern data is invalid.
        """
        if not all(i in {0, 1} for i in self.data):
            raise ValueError("The pattern data must be a list of integers 0 and 1.")

    @classmethod
    def init_from_img(cls, img_path: FilePath) -> "SearchPattern":
        """Create a new SearchPattern object from an image file.

        Args:
            img_path (FilePath): The path to the image file.

        Returns:
            SearchPattern: The created SearchPattern object.
        """
        p = super().init_from_img(img_path)
        return cls(p.data, p.width, p.height)


@dataclass
class ReplacePattern(Pattern):
    """A class to represent a pattern for replacing."""

    def __post_init__(self) -> None:
        """Post-initialization method to validate the pattern.

        Raises:
            ValueError: If the pattern data is invalid.
        """
        if not all(i in {0, 1, -1} for i in self.data):
            raise ValueError("The pattern data must be a list of integers 0, 1, and -1.")

    @classmethod
    def init_from_img(cls, img_path: FilePath) -> "ReplacePattern":
        """Create a new ReplacePattern object from an image file.

        Args:
            img_path (FilePath): The path to the image file.

        Returns:
            ReplacePattern: The created ReplacePattern object.
        """
        p = super().init_from_img(img_path)
        return cls(p.data, p.width, p.height)


class ColorScheme:
    """A class to represent a color scheme."""

    _scheme_name: str
    """The name of the color scheme."""
    _color_map: dict[int, str]
    """The color map of the color scheme."""
    _available_schemes = {
        "black_and_white": {"white": 0, "black": 1},
        "inverted_black_and_white": {"black": 0, "white": 1},
        "transparent_and_black": {"transparent": 0, "black": 1},
        "transparent_and_white": {"transparent": 0, "white": 1},
    }

    def __init__(self, scheme_name: str = "black_and_white") -> None:
        """Initialize a new ColorScheme object.

        Args:
            scheme_name (str, optional): The name of the color scheme.
                Defaults to "black_and_white".

        Raises:
            ValueError: If the color scheme is invalid.
        """
        if scheme_name not in self._available_schemes:
            raise ValueError(f"Invalid color scheme: {scheme_name}")
        self._scheme_name = scheme_name
        self._color_map = self._available_schemes[scheme_name]

    def __str__(self) -> str:
        """Return the string representation of the color scheme.

        Returns:
            str: The string representation of the color scheme.
        """
        return f"Unifont Color Scheme ({self._color_map})"

    @property
    def name(self) -> str:
        """The name of the color scheme."""
        return self._scheme_name

    @property
    def color_map(self) -> dict[int, str]:
        """The color map of the color scheme."""
        return self._color_map


@dataclass
class Glyph:
    """A class representing a single glyph in Unifont."""

    _code_point: str
    """The code point of the character represented by the glyph."""
    _width: int = field(default_factory=int)
    """The width of the glyph."""
    _hex_str: str = field(default_factory=str)
    """The `.hex` format string of the glyph."""
    _data: list[int] = field(default_factory=list)
    """The pixel data of the glyph."""
    _color_scheme: ColorScheme = ColorScheme()
    """The color scheme of the glyph."""

    def __post_init__(self) -> None:
        """Post-initialization method to validate the glyph."""
        self._code_point = Validator.code_point(self._code_point)

    def __str__(self) -> str:
        """Return the string representation of the glyph.

        Returns:
            str: The string representation of the glyph.
        """
        code_point = self._code_point
        if len(self._code_point) == 6 and self._code_point.startswith("0"):
            code_point = code_point[1:]
        return f"Unifont Glyph (U+{code_point})"

    def __add__(self, other: "Glyph") -> "GlyphSet":
        """Add two glyphs together.

        Args:
            other (Glyph): The other glyph to add.

        Returns:
            GlyphSet: The combined glyph set.
        """
        glyphs = GlyphSet()
        glyphs += self
        glyphs += other
        return glyphs

    @property
    def code_point(self) -> str:
        """The code point of the character represented by the glyph."""
        return self._code_point

    @property
    def width(self) -> int:
        """The width of the glyph."""
        if not self._width and self.hex_str:
            self._width = 16 if len(self.hex_str) == 64 else 8
        return self._width

    @property
    def hex_str(self) -> str:
        """The `.hex` format string of the glyph."""
        if not self._hex_str and self.data:
            self._hex_str = Converter.to_hex(self.data)
        return self._hex_str

    @hex_str.setter
    def hex_str(self, hex_str: str) -> None:
        """Set the `.hex` format string of the glyph."""
        self.load_hex(hex_str)

    @property
    def data(self) -> list[int]:
        """The pixel data of the glyph."""
        if not self._data and self.hex_str:
            self._data = Converter.to_img_data(self.hex_str, self.width)
        return self._data[:]

    @data.setter
    def data(self, data: list[int]) -> None:
        """Set the pixel data of the glyph."""
        self._data = data
        self._hex_str = Converter.to_hex(data)
        self._width = 16 if len(self._hex_str) == 64 else 8

    def update_data_at_index(self, index: int, value: int) -> None:
        """Update the pixel data at a specific index."""
        self._data[index] = value
        self._hex_str = Converter.to_hex(self._data)

    @property
    def color_scheme(self) -> ColorScheme:
        """The color scheme of the glyph."""
        return self._color_scheme

    @color_scheme.setter
    def color_scheme(self, scheme: Union[str, ColorScheme]) -> None:
        """Set the color scheme of the glyph."""
        self._color_scheme = self._validate_and_create_color_scheme(scheme)

    def _validate_and_create_color_scheme(
        self, color_scheme: Union[str, ColorScheme]
    ) -> ColorScheme:
        """Helper function to validate and create a ColorScheme object."""
        if isinstance(color_scheme, str):
            return ColorScheme(color_scheme)
        if isinstance(color_scheme, ColorScheme):
            return color_scheme
        raise TypeError("Invalid color scheme type. Must be a string or a ColorScheme.")

    @staticmethod
    def _auto_detect_color_scheme(width: int, rgba_values: list[tuple[int, int, int, int]]) -> str:
        """Helper function to automatically detect the color scheme of the glyph."""
        valid_rgba_values = {(0, 0, 0, 255), (255, 255, 255, 255), (0, 0, 0, 0)}

        if not all(pixel in valid_rgba_values for pixel in rgba_values):
            raise ValueError("Invalid pixel RGBA values.")

        existed_colors = set(rgba_values)
        if len(existed_colors) == 3:
            raise ValueError("Invalid pixel RGBA values.")

        background_color_value = rgba_values[width - 1]
        background_color = COLOR_VALUE_MAP[background_color_value]
        existed_colors.remove(background_color_value)
        foreground_color = COLOR_VALUE_MAP[existed_colors.pop()]

        if background_color == "black" and foreground_color == "white":
            return "inverted_black_and_white"
        if background_color == "white" and foreground_color == "black":
            return "black_and_white"
        if background_color == "transparent" and foreground_color == "white":
            return "transparent_and_white"
        if background_color == "transparent" and foreground_color == "black":
            return "transparent_and_black"
        raise ValueError("Invalid pixel RGBA values.")

    @property
    def character(self) -> str:
        """The character represented by the glyph."""
        return chr(int(self._code_point, 16))

    @property
    def unicode_name(self) -> str:
        """The Unicode name of the glyph."""
        try:
            return name(chr(int(self._code_point, 16)))
        except ValueError:
            return ""

    def load_hex(self, hex_str: str) -> None:
        """Load a `.hex` format string.

        Args:
            hex_str (str): The `.hex` format string of the glyph.
        """
        hex_str = Validator.hex_str(hex_str)
        width = 16 if len(hex_str) == 64 else 8
        self._hex_str = hex_str
        self._width = width
        self._data = Converter.to_img_data(hex_str, width)

    def load_img(
        self,
        img_path: FilePath,
        *,
        color_auto_detect: bool = True,
        color_scheme: Optional[Union[str, ColorScheme]] = None,
    ) -> None:
        """Load an image file.

        Args:
            img_path (FilePath): The path to the image file.
            color_auto_detect (bool, optional): Whether to automatically detect the color scheme.

                Defaults to `True`.
            color_scheme (Union[str, ColorScheme], optional): The color scheme of the glyph.

        Raises:
            ValueError: If the color scheme is invalid.
            FileNotFoundError: If the image file is not found.
        """
        if color_scheme is None and not color_auto_detect:
            raise ValueError("You must specify a color scheme if automatic detection is disabled.")
        if color_scheme is not None:
            color_auto_detect = False
            color_scheme = self._validate_and_create_color_scheme(color_scheme)
        img_path = Validator.file_path(img_path)
        if not img_path.is_file():
            raise FileNotFoundError(f"File not found: {img_path}")

        img = Img.open(img_path).convert("RGBA")
        rgba_values = list(img.getdata())
        if color_auto_detect:
            try:
                color_scheme = self._auto_detect_color_scheme(img.size[0], rgba_values)
                color_scheme = self._validate_and_create_color_scheme(color_scheme)
            except ValueError as e:
                print(f"Warning: {e}. The glyph will not be changed.")
                return
        self.color_scheme = color_scheme
        self._width = img.size[0]
        data = [color_scheme.color_map[COLOR_VALUE_MAP[pixel]] for pixel in rgba_values]
        self._hex_str = Converter.to_hex(data)

    @classmethod
    def init_from_hex(cls, code_point: CodePoint, hex_str: str) -> "Glyph":
        """Create a new Glyph object from a code point and a `.hex` format string.

        Args:
            code_point (CodePoint): The code point of the character represented by the glyph.
            hex_str (str): The `.hex` format string of the glyph.

        Returns:
            Glyph: The created glyph object.
        """
        code_point = Validator.code_point(code_point)
        hex_str = Validator.hex_str(hex_str)

        return cls(code_point, _hex_str=hex_str)

    @classmethod
    def init_from_img(
        cls,
        code_point: CodePoint,
        img_path: FilePath,
        *,
        color_auto_detect: bool = True,
        color_scheme: Optional[Union[str, ColorScheme]] = None,
    ) -> "Glyph":
        """Create a new Glyph object from a code point and an image file.

        Args:
            code_point (CodePoint): The code point of the character represented by the glyph.
            img_path (FilePath): The path to the image file.
            color_auto_detect (bool, optional): Whether to automatically detect the color scheme.

                Defaults to `True`.
            color_scheme (Union[str, ColorScheme], optional): The color scheme of the glyph.

        Returns:
            Glyph: The created glyph object.
        """
        g = cls(code_point)
        g.load_img(img_path, color_auto_detect=color_auto_detect, color_scheme=color_scheme)
        return g

    def save_img(
        self,
        save_path: FilePath,
        img_format: str = "PNG",
        color_scheme: Optional[Union[str, ColorScheme]] = None,
    ) -> None:
        """Save Unifont glyphs as PNG images.

        Args:
            save_path (FilePath): The path to save the image.
            img_format (str, optional): The format of the image. Defaults to `PNG`.
            color_scheme (Union[str, ColorScheme], optional): The color scheme of the   glyph.

        Raises:
            ValueError: If the image format is not supported.
            ValueError: If the glyph data or size is invalid.
        """
        save_path = Validator.file_path(save_path)
        img_format = img_format.upper()
        if img_format not in {"PNG", "BMP"}:
            raise ValueError("Invalid image format. The image format must be PNG or BMP.")
        if len(self.data) != self.width * 16:
            raise ValueError("Invalid glyph data or size.")

        img = Img.new("RGBA", (self.width, 16))
        color_scheme = (
            self._validate_and_create_color_scheme(color_scheme)
            if color_scheme is not None
            else self.color_scheme
        )
        if img_format == "BMP":
            if color_scheme.name == "transparent_and_black":
                color_scheme = ColorScheme("black_and_white")
            elif color_scheme.name == "transparent_and_white":
                color_scheme = ColorScheme("inverted_black_and_white")
            print(
                "Warning: BMP format does not support transparency. "
                "The image will be saved as a black and white image."
            )
        color_dict = {v: k for k, v in color_scheme.color_map.items()}
        data = [COLOR_MAP[color_dict[pixel]] for pixel in self.data]
        img.putdata(data)
        img.save(save_path, img_format)

    def print_glyph(
        self,
        *,
        color_scheme: Optional[Union[str, ColorScheme]] = None,
        display_hex: bool = False,
        display_bin: bool = False,
    ) -> None:
        """Print a Unifont glyph to the console.

        Args:
            color_scheme (Union[str, ColorScheme], optional): The color scheme of the glyph.
            display_hex (bool, optional): Whether to display the hexadecimal strings.

                Defaults to `False`.

                If `True`, the hexadecimal string of each line will be displayed on the left.
            display_bin (bool, optional): Whether to display the binary strings.

                Defaults to `False`.

                If `True`, the binary string of each line will be displayed on the left.
        """
        console = Console()

        white_block = "white on white"
        black_block = "black on black"

        color_scheme = (
            self._validate_and_create_color_scheme(color_scheme)
            if color_scheme is not None
            else self.color_scheme
        )
        if color_scheme.name in {"inverted_black_and_white", "transparent_and_black"}:
            white_block, black_block = black_block, white_block

        hex_length = self.width // 4 if display_hex else 0

        for i in range(16):
            row_text = Text()

            for j in range(self.width):
                row_text.append(
                    "  ",
                    style=(white_block if self.data[i * self.width + j] else black_block),
                )

            if display_hex or display_bin:
                prefix = []
                if display_hex:
                    hex_slice = self.hex_str[i * hex_length : (i + 1) * hex_length]
                    prefix.append(hex_slice)
                if display_bin:
                    bin_slice = "".join(
                        str(self.data[i * self.width + j]) for j in range(self.width)
                    )
                    prefix.append(bin_slice)

                prefix_text = "\t".join(prefix)
                row_text = Text(f"{prefix_text}\t").append_text(row_text)

            console.print(row_text)

    def replace(self, search_pattern: SearchPattern, replace_pattern: ReplacePattern) -> None:
        """Replaces a pattern in an image with another pattern.

        Args:
            search_pattern (SearchPattern): The pattern to be searched.
            replace_pattern (ReplacePattern): The pattern to be replaced.

        Raises:
            ValueError: If the two patterns have different size.
        """
        img_data = self.data
        pattern_a, pattern_b = search_pattern.data, replace_pattern.data
        if search_pattern.width > self.width:
            raise ValueError("The pattern to be searched is larger than the glyph.")
        if replace_pattern.width > self.width:
            raise ValueError("The pattern to be replaced is larger than the glyph.")

        if len(pattern_a) != len(pattern_b):
            raise ValueError("The two patterns must have the same size.")

        height = search_pattern.height
        width = search_pattern.width
        image_width = len(img_data) // 16

        def match_pattern(i: int, j: int) -> bool:
            for y in range(height):
                for x in range(width):
                    if (
                        pattern_a[y * width + x] == 1
                        and img_data[(i + y) * image_width + (j + x)] != 1
                    ):
                        return False
            return True

        def apply_pattern(i: int, j: int) -> None:
            for y in range(height):
                for x in range(width):
                    pixel = pattern_b[y * width + x]
                    index = (i + y) * image_width + (j + x)
                    if pixel == 1:
                        img_data[index] = 1
                    elif pixel == 0:
                        img_data[index] = 0

        for i in range(16 - height + 1):
            for j in range(image_width - width + 1):
                if match_pattern(i, j):
                    apply_pattern(i, j)

        self.data = img_data

    def find_matches(self, search_pattern: SearchPattern) -> list[tuple[int, int]]:
        """Finds all matches of a pattern in the image.

        Args:
            search_pattern (SearchPattern): The pattern to be searched.

        Returns:
            list[tuple[int, int]]: list of coordinates where the pattern is found.
        """
        if search_pattern.width > self.width:
            raise ValueError("The pattern to be searched is larger than the glyph.")
        pattern_a = search_pattern.data

        height = search_pattern.height
        width = search_pattern.width
        image_width = len(self.data) // 16
        matches = []

        def match_pattern(i: int, j: int) -> bool:
            for y in range(height):
                for x in range(width):
                    if (
                        pattern_a[y * width + x] == 1
                        and self.data[(i + y) * image_width + (j + x)] != 1
                    ):
                        return False
            return True

        for i in range(16 - height + 1):
            for j in range(image_width - width + 1):
                if match_pattern(i, j):
                    matches.extend([(i, j)])

        return matches

    def apply_pattern(self, i: int, j: int, replace_pattern: ReplacePattern) -> None:
        """Apply the replacement pattern at the specified coordinates.

        Args:
            i (int): The row coordinate where the pattern starts.
            j (int): The column coordinate where the pattern starts.
            replace_pattern (ReplacePattern): The pattern to replace with.
        """
        if replace_pattern.width > self.width:
            raise ValueError("The pattern to be replaced is larger than the glyph.")
        if i < 0 or i + replace_pattern.height > 16:
            raise ValueError("The pattern is out of bounds.")
        if j < 0 or j + replace_pattern.width > self.width:
            raise ValueError("The pattern is out of bounds.")
        img_data = self.data.copy()
        pattern_b = replace_pattern.data

        height = replace_pattern.height
        width = replace_pattern.width
        image_width = len(img_data) // 16

        for y in range(height):
            for x in range(width):
                pixel = pattern_b[y * width + x]
                index = (i + y) * image_width + (j + x)
                if pixel == 1:
                    img_data[index] = 1
                elif pixel == 0:
                    img_data[index] = 0

        self.data = img_data


@dataclass
class GlyphSet:
    """A class representing a set of glyphs in Unifont."""

    _glyphs: dict[str, Glyph] = field(default_factory=dict)
    """A dictionary of glyphs in the set."""

    @property
    def glyphs(self) -> dict[str, Glyph]:
        """A dictionary of glyphs in the set."""
        self.sort_glyphs()
        return self._glyphs

    @property
    def code_points(self) -> list[CodePoint]:
        """A list of code points of the glyphs in the set."""
        self.sort_glyphs()
        return list(self._glyphs.keys())

    def __str__(self) -> str:
        """Return the string representation of the glyph set.

        Returns:
            str: The string representation of the glyph set.
        """
        if not self._glyphs:
            return "Unifont Glyph Set (0 glyphs)"

        return f"Unifont Glyph Set ({len(self._glyphs)} glyphs)"

    def __getitem__(self, code_point: CodePoint) -> Glyph:
        """Get a glyph by its code point.

        Args:
            code_point (CodePoint): The code point of the glyph to get.

        Returns:
            Glyph: The obtained glyph.
        """
        return self.get_glyph(code_point)

    def __setitem__(self, code_point: CodePoint, hex_str: str) -> None:
        """Set the hexadecimal string of a glyph.

        Args:
            code_point (CodePoint): The code point of the glyph to set.
            hex_str (str): The hexadecimal string to set.
        """
        self.add_glyph((code_point, hex_str))

    def __delitem__(self, code_point: CodePoint) -> None:
        """Remove a glyph from the set.

        Args:
            code_point (CodePoint): The code point of the glyph to remove.
        """
        self.remove_glyph(code_point)

    def __add__(self, other: Union["GlyphSet", Glyph]) -> "GlyphSet":
        """Add two glyph sets together.

        Args:
            other (Union["GlyphSet", Glyph]): The other glyph set to add.

        Raises:
            TypeError: If the type of the other object is invalid.

        Returns:
            GlyphSet: The combined glyph set.
        """
        result = GlyphSet()
        result._glyphs = self._glyphs.copy()
        if isinstance(other, Glyph):
            result.add_glyph(other)
        elif isinstance(other, GlyphSet):
            result.glyphs.update(other.glyphs)
        else:
            raise TypeError("Invalid type for addition to GlyphSet.")
        return result

    def __iadd__(self, other: Union["GlyphSet", Glyph]) -> "GlyphSet":
        """Add another glyph set or glyph to the set in-place.

        Args:
            other (Union["GlyphSet", Glyph]): The other glyph set or glyph to add.

        Raises:
            TypeError: If the type of the other object is invalid.

        Returns:
            GlyphSet: The updated glyph set.
        """
        if isinstance(other, Glyph):
            self.add_glyph(other)
        elif isinstance(other, GlyphSet):
            self._glyphs.update(other.glyphs)
        else:
            raise TypeError("Invalid type for in-place addition to GlyphSet.")
        return self

    def __len__(self) -> int:
        """Return the number of glyphs in the set.

        Returns:
            int: The number of glyphs in the set.
        """
        return len(self._glyphs)

    def __iter__(self) -> Iterator[Glyph]:
        """Iterate through the glyphs in the set."""
        return iter(self._glyphs.values())

    def __contains__(self, glyph: Union[Glyph, str]) -> bool:
        """Check if a glyph is in the set.

        Args:
            glyph (Union[Glyph, str]): The glyph to check.

        Returns:
            bool: Whether the glyph is in the set.
        """
        code_point = Validator.code_point(glyph if isinstance(glyph, str) else glyph.code_point)
        return code_point in self._glyphs

    @classmethod
    def init_glyphs(cls, code_points: CodePoints) -> "GlyphSet":
        """Initialize a set of glyphs. All the code points will be initialized with empty data.

        Args:
            code_points (CodePoints): The code points to initialize.

                The code points specified should be hexadecimal number strings or integers.
        """
        code_points_list = Validator.code_points(code_points)
        glyphs = {cp: Glyph.init_from_hex(cp, "") for cp in code_points_list}
        return cls(_glyphs=glyphs)

    def get_glyph(self, code_point: CodePoint) -> Glyph:
        """Get a glyph by its code point.

        Args:
            code_point (CodePoint): The code point of the glyph to get.

        Returns:
            Glyph: The obtained glyph.
        """
        code_point = Validator.code_point(code_point)
        try:
            return self._glyphs[code_point]
        except KeyError as exc:
            raise KeyError(f"Glyph with code point U+{code_point} not found.") from exc

    def get_glyphs(self, code_points: CodePoints, *, skip_empty: bool = True) -> "GlyphSet":
        """Get a set of glyphs by their code points.

        Args:
            code_points (CodePoints): The code points of the glyphs to get.

                The code points specified should be hexadecimal number strings.
            skip_empty (bool, optional): Whether to skip empty glyphs. Defaults to `True`.

                If `True`, empty glyphs will be skipped.

                If `False`, empty glyphs will be included with empty `.hex` strings.

        Returns:
            GlyphSet: The obtained set of glyphs.
        """
        result = GlyphSet()
        code_points_list = Validator.code_points(code_points)
        for code_point in code_points_list:
            if code_point in self._glyphs:
                result.add_glyph(self._glyphs[code_point])
            elif not skip_empty:
                result.add_glyph((code_point, ""))
        return result

    def add_glyph(self, glyph: Union[Glyph, tuple[CodePoint, str]]) -> None:
        """Add a glyph to the set.

        Args:
            glyph (Union[Glyph, tuple[CodePoint, str]]): The glyph to add.

                If a tuple is provided, it should be in the format of `(code_point, hex_str)`.
        """
        glyph_obj = self._validate_and_create_glyph(glyph)
        if glyph_obj.code_point in self._glyphs:
            raise ValueError(f"Glyph with code point U+{glyph_obj.code_point} already exists.")
        self._glyphs[glyph_obj.code_point] = glyph_obj

    def remove_glyph(self, code_point: CodePoint) -> None:
        """Remove a glyph from the set.

        Args:
            code_point (CodePoint): The code point of the glyph to remove.
        """
        code_point = Validator.code_point(code_point)
        if code_point not in self._glyphs:
            raise KeyError(f"Glyph with code point U+{code_point} not found.")
        del self._glyphs[code_point]

    def update_glyph(self, glyph: Union[Glyph, tuple[CodePoint, str]]) -> None:
        """Update a glyph in the set.

        Args:
            glyph (Union[Glyph, tuple[CodePoint, str]]): The new glyph to update.

                If a tuple is provided, it should be in the format of `(code_point, hex_str)`.
        """
        glyph_obj = self._validate_and_create_glyph(glyph)
        if glyph_obj.code_point not in self._glyphs:
            raise KeyError(f"Glyph with code point U+{glyph_obj.code_point} not found.")
        self._glyphs[glyph_obj.code_point].hex_str = glyph_obj.hex_str

    def sort_glyphs(self) -> None:
        """Sort the glyphs in the set by their code points."""
        if not self._glyphs:
            raise ValueError("Cannot sort an empty glyph set.")
        self._glyphs = dict(sorted(self._glyphs.items(), key=lambda x: int(x[0], 16)))

    def _validate_and_create_glyph(self, glyph: Union[Glyph, tuple[CodePoint, str]]) -> Glyph:
        """Helper function to validate and create a Glyph object."""
        if isinstance(glyph, Glyph):
            return glyph
        if isinstance(glyph, tuple):
            code_point, hex_str = glyph
            code_point = Validator.code_point(code_point)
            hex_str = Validator.hex_str(hex_str)
            return Glyph.init_from_hex(code_point, hex_str)
        raise TypeError("Invalid glyph type. Must be a Glyph or a tuple (code_point, hex_str).")

    @classmethod
    def load_hex_file(cls, file_path: FilePath) -> "GlyphSet":
        """Parse and load a `.hex` file.

        Args:
            file_path (FilePath): The path to the `.hex` file.
        """
        print(f"Start loading glyphs from {file_path}...")
        start_time = time.time()

        file_path = Validator.file_path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        glyphs = GlyphSet()
        with file_path.open("r", encoding="utf-8") as f:
            for line in f:
                if current_line := line.strip():
                    if ":" not in line:
                        raise ValueError(f"Invalid line in file: {current_line}")
                    code_point, hex_str = current_line.split(":", 1)
                    glyphs.add_glyph((code_point, hex_str))

        elapsed_time = time.time() - start_time
        print(
            f'Loaded {len(glyphs)} glyphs from "{file_path.name}". '
            f"Time elapsed: {elapsed_time:.2f} s."
        )

        return glyphs

    def save_hex_file(self, file_path: FilePath) -> None:
        """Save the glyphs as a `.hex` file.

        Args:
            file_path (FilePath): The path to the `.hex` file.
        """
        start_time = time.time()

        file_path = Validator.file_path(file_path)
        with file_path.open("w", encoding="utf-8") as f:
            for code_point, glyph in sorted(self._glyphs.items()):
                f.write(f"{code_point}:{glyph.hex_str}\n")

        elapsed_time = time.time() - start_time
        print(
            f'Saved {len(self._glyphs)} glyphs to "{file_path.name}". '
            f"Time elapsed: {elapsed_time:.2f} s."
        )

    def save_unicode_page(self, file_path: FilePath, start: CodePoint = "4E00") -> None:
        """Save a Unicode page image for Minecraft.

        This function saves a 256px image with each Unicode code point represented by a 16px
        pixel glyph. The image contains 256 characters at most, starting from the specified
        Unicode code point.

        Args:
            file_path (FilePath): The path to the Unicode page file.
            start (CodePoint, optional): The starting Unicode code point. Defaults to "4E00".
        """
        start_time = time.time()

        self.sort_glyphs()
        file_path = Validator.file_path(file_path)
        start = int(start, 16) if isinstance(start, str) else start

        img = Img.new("RGBA", (256, 256))
        position = 0
        for code_point, glyph in self._glyphs.items():
            if int(code_point, 16) < start:
                continue

            if glyph.hex_str:
                glyph_img = Img.new("RGBA", (16, 16))
                rgba_data = [
                    (255, 255, 255, 255) if pixel else (0, 0, 0, 0)
                    for pixel in Converter.to_img_data(glyph.hex_str)
                ]
                glyph_img.putdata(rgba_data)

                x = (position % 16) * 16
                y = (position // 16) * 16
                img.paste(glyph_img, (x, y))

            position += 1
            if position >= 256:
                break

        img.save(file_path)

        elapsed_time = time.time() - start_time
        print(f'Saved {position} glyphs to "{file_path.name}". Time elapsed: {elapsed_time:.2f} s.')
