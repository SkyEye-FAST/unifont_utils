# -*- encoding: utf-8 -*-
"""Unifont Utils - Converter"""

from functools import reduce
from pathlib import Path
from platform import system
from typing import List, Tuple, Optional

from PIL import Image as Img

from .base import validate_hex_str


class BaseConverter:
    """The base converter class for use by other converter classes."""

    def __init__(
        self,
        data: List[int],
        hex_str: str,
        size: Tuple[int, int],
        black_and_white: bool,
    ) -> None:
        """Initialize the base converter class (`BaseConverter`).

        Args:
            data (List[int]): Glyph pixel data in the image, stored as `0` and `1`.
            hex_str (str): Glyph data in the Unifont `.hex` format.
            size (Tuple[int, int]): Glyph size in pixels, as a tuple of `(width, height)`.
            black_and_white (bool): Whether it is a black and white image.

                If `True`, `0` is white and `1` is black.

                If `False`, `0` is transparent and `1` is white.
        """

        self.data = data
        self.hex_str = hex_str
        self.size = size
        self.width, self.height = size
        self.black_and_white = black_and_white

    def _get_rgba_data(self, black_and_white: bool) -> List[Tuple[int, int, int, int]]:
        """Get RGBA data based on black and white mode.

        Args:
            black_and_white (bool): Whether it is a black and white image.

            If `True`, `0` is white and `1` is black.

            If `False`, `0` is transparent and `1` is white.
        """

        if black_and_white:
            return [
                (0, 0, 0, 255) if pixel else (255, 255, 255, 255) for pixel in self.data
            ]
        return [(255, 255, 255, 255) if pixel else (0, 0, 0, 0) for pixel in self.data]

    def save_img(
        self,
        save_path: Path,
        black_and_white: Optional[bool] = None,
    ) -> None:
        """Save Unifont glyphs as PNG images.

        Args:
            save_path (Path): The path to save the image.
            black_and_white (bool, optional): Whether it is a black and white image.

                Defaults to the one specified during class initialization.

                If `True`, `0` is white and `1` is black.

                If `False`, `0` is transparent and `1` is white.
        """

        if len(self.data) != self.width * self.height:
            raise ValueError("Invalid glyph data or size.")

        img = Img.new("RGBA", self.size)
        black_and_white = black_and_white or self.black_and_white
        img.putdata(self._get_rgba_data(black_and_white))
        img.save(save_path, "PNG")

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

        if len(self.data) != self.width * self.height:
            raise ValueError("Invalid glyph data or size.")

        white_block, black_block, new_line = (
            ("▇", "  ", "\n")
            if system() == "Windows"
            else ("\033[48;5;7m  ", "\033[48;5;0m  ", "\033[0m")
        )

        black_and_white = (
            black_and_white if black_and_white is not None else self.black_and_white
        )
        if black_and_white:
            white_block, black_block = black_block, white_block

        hex_length = self.width // 4 if display_hex else None

        for i in range(self.height):
            row = "".join(
                white_block if self.data[i * self.width + j] else black_block
                for j in range(self.width)
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

                row = "\t".join(prefix) + "\t" + row

            print(row + new_line)


class ImgConverter(BaseConverter):
    """Glyph image converter class."""

    def __init__(self, img_path: Path, black_and_white: bool = True) -> None:
        """Initialize the glyph image converter class (`ImgConverter`).

        Args:
            img_path (Path): The path to the image file.
            black_and_white (bool, optional): Whether it is a black and white image.

                If `True`, `0` is white and `1` is black.

                If `False`, `0` is transparent and `1` is white.
        """

        if not img_path.is_file():
            raise FileNotFoundError(f"File not found: {img_path}")

        self.img = Img.open(img_path).convert("1")
        self.data = (
            [0 if pixel == 255 else 1 for pixel in self.img.getdata()]
            if black_and_white
            else [1 if pixel == 255 else 0 for pixel in self.img.getdata()]
        )
        super().__init__(self.data, self._to_hex(), self.img.size, black_and_white)

    def _to_hex(self) -> str:
        """Convert glyph pixel data to Unifont `.hex` format string."""
        if not self.data:
            raise ValueError(
                "Unable to convert to .hex string. The glyph data is empty."
            )

        n = reduce(lambda acc, pixel: (acc << 1) | (1 if pixel else 0), self.data, 0)
        return hex(n)[2:].upper().zfill(32 if len(self.data) == 128 else 64)


class HexConverter(BaseConverter):
    """Unifont `.hex` format string converter class."""

    def __init__(self, hex_str: str, black_and_white: bool = True) -> None:
        """Initialize the Unifont `.hex` format string converter class (`HexConverter`).

        Args:
            hex_str (str): The Unifont `.hex` format string.
            black_and_white (bool, optional): Whether it is a black and white image.

                If `True`, `0` is white and `1` is black.

                If `False`, `0` is transparent and `1` is white.
        """

        self.hex_str = validate_hex_str(hex_str)
        self.width, self.height = (16, 16) if len(hex_str) == 64 else (8, 16)
        super().__init__(
            self._to_img_data(),
            self.hex_str,
            (self.width, self.height),
            black_and_white,
        )

    def _to_img_data(self) -> List[int]:
        """Convert Unifont `.hex` format string to glyph pixel data."""

        if not self.hex_str:
            return []

        n = int(self.hex_str, 16)
        return [(n >> i) & 1 for i in range(self.width * self.height - 1, -1, -1)]
