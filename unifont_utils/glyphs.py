# -*- encoding: utf-8 -*-
"""Unifont Utils - Glyphs"""

from dataclasses import dataclass, field
import time
from unicodedata import name
from typing import Dict, List, Tuple, Iterator, Optional, Union

from PIL import Image as Img
from rich.console import Console
from rich.text import Text

from .base import (
    Validator as V,
    CodePoint,
    CodePoints,
    FilePath,
)
from .converter import Converter as C


@dataclass
class Pattern:
    """A class to represent a pattern.

    Attributes:
        data (List[int]): The pattern data.
        width (int): The width of the pattern.
        height (Optional[int]): The height of the pattern.

    Raises:
        ValueError: If the size of the pattern is invalid.
    """

    data: List[int]
    """The pattern data."""
    _width: int
    """The width of the pattern."""
    _height: Optional[int] = None
    """The height of the pattern.
    If it is `None`, the height is set to the length of `data` divided by `width`.
    """

    def __post_init__(self) -> None:
        if self._width <= 2:
            raise ValueError("The width must be greater than 2 pixels.")
        if self._width > 16:
            raise ValueError("The width must be less than 16 pixels.")
        if self._height is None:
            self._height = len(self.data) // self._width
            if len(self.data) % self._width != 0:
                raise ValueError("The length of the data must be divisible by width.")
            if self._height <= 2:
                raise ValueError("The height must be greater than 2 pixels.")
            if self._height > 16:
                raise ValueError("The height must be less than 16 pixels.")

    def __str__(self) -> str:
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
    def init_from_hex(cls, hex_str: str, width: int) -> "Pattern":
        """Create a new Pattern object from a `.hex` format string.

        Args:
            hex_str (str): The `.hex` format string of the glyph.
            width (int): The width of the pattern.

        Returns:
            Pattern: The created Pattern object.
        """

        hex_str = V.hex_str(hex_str)
        data = C.to_img_data(hex_str, width)

        return cls(data, width)

    @classmethod
    def init_from_img(cls, img_path: FilePath) -> "Pattern":
        """Create a new Pattern object from an image file.

        Args:
            img_path (FilePath): The path to the image file.

        Returns:
            Pattern: The created Pattern object.
        """

        img_path = V.file_path(img_path)
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
        if not all(i in {0, 1} for i in self.data):
            raise ValueError("The pattern data must be a list of integers 0 and 1.")

    @classmethod
    def init_from_hex(cls, hex_str: str, width: int) -> "SearchPattern":
        p = super().init_from_hex(hex_str, width)
        return cls(p.data, p.width, p.height)

    @classmethod
    def init_from_img(cls, img_path: FilePath) -> "SearchPattern":
        p = super().init_from_img(img_path)
        return cls(p.data, p.width, p.height)


@dataclass
class ReplacePattern(Pattern):
    """A class to represent a pattern for replacing."""

    def __post_init__(self) -> None:
        if not all(i in {0, 1, -1} for i in self.data):
            raise ValueError(
                "The pattern data must be a list of integers 0, 1, and -1."
            )

    @classmethod
    def init_from_hex(cls, hex_str: str, width: int) -> "ReplacePattern":
        p = super().init_from_hex(hex_str, width)
        return cls(p.data, p.width, p.height)

    @classmethod
    def init_from_img(cls, img_path: FilePath) -> "ReplacePattern":
        p = super().init_from_img(img_path)
        return cls(p.data, p.width, p.height)


@dataclass
class Glyph:
    """A class representing a single glyph in Unifont."""

    _code_point: str
    """The code point of the character represented by the glyph."""
    _width: int = 16
    """The width of the glyph."""
    _hex_str: str = field(default_factory=str)
    """The `.hex` format string of the glyph."""
    _data: List[int] = field(default_factory=list)
    """The pixel data of the glyph."""
    _black_and_white: bool = True
    """Whether the glyph is loaded from a black and white image."""

    def __post_init__(self) -> None:
        self._code_point = V.code_point(self._code_point)

    def __str__(self) -> str:
        code_point = self._code_point
        if len(self._code_point) == 6 and self._code_point.startswith("0"):
            code_point = code_point[1:]
        return f"Unifont Glyph (U+{code_point})"

    def __add__(self, other: "Glyph") -> "GlyphSet":
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
        return self._width

    @property
    def hex_str(self) -> str:
        """The `.hex` format string of the glyph."""
        return self._hex_str

    @hex_str.setter
    def hex_str(self, hex_str: str) -> None:
        """Set the `.hex` format string of the glyph."""
        self.load_hex(hex_str)

    @property
    def data(self) -> List[int]:
        """The pixel data of the glyph."""
        return self._data[:]

    @data.setter
    def data(self, data: List[int]) -> None:
        """Set the pixel data of the glyph."""
        self._data = data
        self._hex_str = C.to_hex(data)

    def update_data_at_index(self, index: int, value: int) -> None:
        """Update the pixel data at a specific index."""
        self._data[index] = value
        self._hex_str = C.to_hex(self._data)

    @property
    def black_and_white(self) -> bool:
        """Whether the glyph is loaded from a black and white image."""
        return self._black_and_white

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

        hex_str = V.hex_str(hex_str)
        width = 16 if len(hex_str) == 64 else 8
        self._hex_str = hex_str
        self._width = width
        self._data = C.to_img_data(hex_str, width)

    def load_img(self, img_path: FilePath, black_and_white: bool = True) -> None:
        """Load an image file.
        Args:
            img_path (FilePath): The path to the image file.
            black_and_white (bool, optional): Whether it is a black and white image.

                If `True`, `0` is white and `1` is black.

                If `False`, `0` is transparent and `1` is white.
        """

        img_path = V.file_path(img_path)
        if not img_path.is_file():
            raise FileNotFoundError(f"File not found: {img_path}")

        img = Img.open(img_path).convert("1")
        self._width = img.size[0]
        data = (
            [0 if pixel == 255 else 1 for pixel in img.getdata()]  # type: ignore
            if black_and_white
            else [1 if pixel == 255 else 0 for pixel in img.getdata()]  # type: ignore
        )
        self._hex_str = C.to_hex(data)
        self._black_and_white = black_and_white

    @classmethod
    def init_from_hex(cls, code_point: CodePoint, hex_str: str) -> "Glyph":
        """Create a new Glyph object from a code point and a `.hex` format string.

        Args:
            code_point (CodePoint): The code point of the character represented by the glyph.
            hex_str (str): The `.hex` format string of the glyph.

        Returns:
            Glyph: The created glyph object.
        """

        code_point = V.code_point(code_point)
        hex_str = V.hex_str(hex_str)
        width = 16 if len(hex_str) == 64 else 8
        data = C.to_img_data(hex_str, width)

        return cls(code_point, _hex_str=hex_str, _width=width, _data=data)

    @classmethod
    def init_from_img(
        cls, code_point: CodePoint, img_path: FilePath, black_and_white: bool = True
    ) -> "Glyph":
        """Create a new Glyph object from a code point and an image file.

        Args:
            code_point (CodePoint): The code point of the character represented by the glyph.
            img_path (FilePath): The path to the image file.
            black_and_white (bool, optional): Whether it is a black and white image.

                If `True`, `0` is white and `1` is black.

                If `False`, `0` is transparent and `1` is white.

        Returns:
            Glyph: The created glyph object.
        """

        code_point = V.code_point(code_point)
        img_path = V.file_path(img_path)
        if not img_path.is_file():
            raise FileNotFoundError(f"File not found: {img_path}")

        img = Img.open(img_path).convert("1")
        data = (
            [0 if pixel == 255 else 1 for pixel in img.getdata()]  # type: ignore
            if black_and_white
            else [1 if pixel == 255 else 0 for pixel in img.getdata()]  # type: ignore
        )

        return cls(
            code_point,
            _hex_str=C.to_hex(data),
            _data=data,
            _width=img.size[0],
            _black_and_white=black_and_white,
        )

    def save_img(
        self,
        save_path: FilePath,
        img_format: str = "PNG",
        black_and_white: Optional[bool] = None,
    ) -> None:
        """Save Unifont glyphs as PNG images.

        Args:
            save_path (FilePath): The path to save the image.
            format (str, optional): The format of the image. Defaults to `PNG`.
            black_and_white (bool, optional): Whether it is a black and white image.

                Defaults to the one specified during class initialization.

                If `True`, `0` is white and `1` is black.

                If `False`, `0` is transparent and `1` is white.

        Raises:
            ValueError: If the image format is not supported.
            ValueError: If the glyph data or size is invalid.
        """

        save_path = V.file_path(save_path)
        img_format = img_format.upper()
        if img_format not in {"PNG", "BMP"}:
            raise ValueError(
                "Invalid image format. The image format must be PNG or BMP."
            )
        if len(self._data) != self._width * 16:
            raise ValueError("Invalid glyph data or size.")

        img = Img.new("RGBA", (self._width, 16))
        black_and_white = (
            black_and_white if black_and_white is not None else self._black_and_white
        )
        if img_format == "BMP":
            black_and_white = True
            print(
                "Warning: BMP format does not support transparency. "
                "The image will be saved as a black and white image."
            )
        data = (
            [(0, 0, 0, 255) if pixel else (255, 255, 255, 255) for pixel in self._data]
            if black_and_white
            else [
                (255, 255, 255, 255) if pixel else (0, 0, 0, 0) for pixel in self._data
            ]
        )
        img.putdata(data)
        img.save(save_path, img_format)

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

        console = Console()

        if len(self._data) != self._width * 16:
            raise ValueError("Invalid glyph data or size.")

        white_block = "white on white"
        black_block = "black on black"

        black_and_white = (
            black_and_white if black_and_white is not None else self._black_and_white
        )
        if black_and_white:
            white_block, black_block = black_block, white_block

        hex_length = self._width // 4 if display_hex else 0

        for i in range(16):
            row_text = Text()

            for j in range(self._width):
                block_style = (
                    white_block if self._data[i * self._width + j] else black_block
                )
                row_text.append("  ", style=block_style)

            if display_hex or display_bin:
                prefix = []
                if display_hex:
                    hex_slice = self._hex_str[i * hex_length : (i + 1) * hex_length]
                    prefix.append(hex_slice)
                if display_bin:
                    bin_slice = "".join(
                        str(self._data[i * self._width + j]) for j in range(16)
                    )
                    prefix.append(bin_slice)

                row_text = Text("\t".join(prefix) + "\t") + row_text

            console.print(row_text)

    def replace(
        self, search_pattern: SearchPattern, replace_pattern: ReplacePattern
    ) -> None:
        """Replaces a pattern in an image with another pattern.

        Args:
            search_pattern (SearchPattern): The pattern to be searched.
            replace_pattern (ReplacePattern): The pattern to be replaced.

        Raises:
            ValueError: If the two patterns have different size.
        """

        img_data = self._data.copy()
        pattern_a, pattern_b = search_pattern.data, replace_pattern.data

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
                    if pattern_b[y * width + x] == 1:
                        img_data[(i + y) * image_width + (j + x)] = 1
                    elif pattern_b[y * width + x] == 0:
                        img_data[(i + y) * image_width + (j + x)] = 0

        for i in range(16 - height + 1):
            for j in range(image_width - width + 1):
                if match_pattern(i, j):
                    apply_pattern(i, j)

        self._data = img_data


@dataclass
class GlyphSet:
    """A class representing a set of glyphs in Unifont."""

    _glyphs: Dict[str, Glyph] = field(default_factory=dict)
    """A dictionary of glyphs in the set."""

    @property
    def glyphs(self) -> Dict[str, Glyph]:
        """A dictionary of glyphs in the set."""
        self.sort_glyphs()
        return self._glyphs

    @property
    def code_points(self) -> List[CodePoint]:
        """A list of code points of the glyphs in the set."""
        self.sort_glyphs()
        return list(self._glyphs.keys())

    def __str__(self) -> str:
        if not self._glyphs:
            return "Unifont Glyph Set (0 glyphs)"

        return f"Unifont Glyph Set ({len(self._glyphs)} glyphs)"

    def __getitem__(self, code_point: CodePoint) -> Glyph:
        return self.get_glyph(code_point)

    def __setitem__(self, code_point: CodePoint, hex_str: str) -> None:
        self.add_glyph((code_point, hex_str))

    def __delitem__(self, code_point: CodePoint) -> None:
        self.remove_glyph(code_point)

    def __add__(self, other: Union["GlyphSet", Glyph]) -> "GlyphSet":
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
        if isinstance(other, Glyph):
            self.add_glyph(other)
        elif isinstance(other, GlyphSet):
            self._glyphs.update(other.glyphs)
        else:
            raise TypeError("Invalid type for in-place addition to GlyphSet.")
        return self

    def __len__(self) -> int:
        return len(self._glyphs)

    def __iter__(self) -> Iterator[Glyph]:
        return iter(self._glyphs.values())

    def __contains__(self, glyph: Union[Glyph, str]) -> bool:
        code_point = V.code_point(glyph if isinstance(glyph, str) else glyph.code_point)
        return code_point in self._glyphs

    @classmethod
    def init_glyphs(cls, code_points: CodePoints) -> "GlyphSet":
        """Initialize a set of glyphs.
        All the code points will be initialized with empty data.

        Args:
            code_points (CodePoints): The code points to initialize.

                The code points specified should be hexadecimal number strings or integers.
        """

        code_points_list = V.code_points(code_points)
        glyphs = {cp: Glyph.init_from_hex(cp, "") for cp in code_points_list}
        return cls(_glyphs=glyphs)

    def get_glyph(self, code_point: CodePoint) -> Glyph:
        """Get a glyph by its code point.

        Args:
            code_point (CodePoint): The code point of the glyph to get.

        Returns:
            Glyph: The obtained glyph.
        """

        code_point = V.code_point(code_point)
        try:
            return self._glyphs[code_point]
        except KeyError as exc:
            raise KeyError(f"Glyph with code point U+{code_point} not found.") from exc

    def get_glyphs(
        self, code_points: CodePoints, *, skip_empty: bool = True
    ) -> "GlyphSet":
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
        code_points_list = V.code_points(code_points)
        for code_point in code_points_list:
            if code_point in self._glyphs:
                result.add_glyph(self._glyphs[code_point])
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
        if glyph_obj.code_point in self._glyphs:
            raise ValueError(
                f"Glyph with code point U+{glyph_obj.code_point} already exists."
            )
        self._glyphs[glyph_obj.code_point] = glyph_obj

    def remove_glyph(self, code_point: CodePoint) -> None:
        """Remove a glyph from the set.

        Args:
            code_point (CodePoint): The code point of the glyph to remove.
        """

        code_point = V.code_point(code_point)
        if code_point not in self._glyphs:
            raise KeyError(f"Glyph with code point U+{code_point} not found.")
        del self._glyphs[code_point]

    def update_glyph(self, glyph: Union[Glyph, Tuple[CodePoint, str]]) -> None:
        """Update a glyph in the set.

        Args:
            glyph (Union[Glyph, Tuple[CodePoint, str]]): The new glyph to update.

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

    def _validate_and_create_glyph(
        self, glyph: Union[Glyph, Tuple[CodePoint, str]]
    ) -> Glyph:
        """Helper function to validate and create a Glyph object."""
        if isinstance(glyph, Glyph):
            return glyph
        if isinstance(glyph, tuple):
            code_point, hex_str = glyph
            code_point = V.code_point(code_point)
            hex_str = V.hex_str(hex_str)
            return Glyph.init_from_hex(code_point, hex_str)
        raise TypeError(
            "Invalid glyph type. Must be a Glyph or a tuple (code_point, hex_str)."
        )

    @classmethod
    def load_hex_file(cls, file_path: FilePath) -> "GlyphSet":
        """Parse and load a `.hex` file.

        Args:
            file_path (FilePath): The path to the `.hex` file.
        """

        print(f"Start loading glyphs from {file_path}...")
        start_time = time.time()

        file_path = V.file_path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        glyphs = GlyphSet()

        with file_path.open("r", encoding="utf-8") as f:
            for line in f:
                if l := line.strip():
                    if ":" not in line:
                        raise ValueError(f"Invalid line in file: {l}")
                    code_point, hex_str = l.split(":", 1)
                    glyphs.add_glyph((code_point, hex_str))

        elapsed_time = time.time() - start_time
        print(
            f'Loaded {len(glyphs)} glyphs from "{file_path.name}".'
            f"Time elapsed: {elapsed_time:.2f} s."
        )

        return glyphs

    def save_hex_file(self, file_path: FilePath) -> None:
        """Save the glyphs as a `.hex` file.

        Args:
            file_path (FilePath): The path to the `.hex` file.
        """

        start_time = time.time()

        file_path = V.file_path(file_path)
        with file_path.open("w", encoding="utf-8") as f:
            for code_point, glyph in sorted(self._glyphs.items()):
                f.write(f"{code_point}:{glyph.hex_str}\n")

        elapsed_time = time.time() - start_time
        print(
            f'Saved {len(self._glyphs)} glyphs to "{file_path.name}".'
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
        file_path = V.file_path(file_path)
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
                    for pixel in C.to_img_data(glyph.hex_str)
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
        print(
            f'Saved {position} glyphs to "{file_path.name}".'
            f" Time elapsed: {elapsed_time:.2f} s."
        )
