"""Search and replacement patterns for Unifont glyph bitmaps."""

from dataclasses import dataclass

from PIL import Image as Img

from unifont_utils.base import FilePath, Validator


@dataclass
class Pattern:
    """Rectangular bitmap pattern with dimensions between 3 and 16 pixels."""

    data: list[int]
    _width: int
    _height: int | None = None

    def __post_init__(self) -> None:
        """Validate and normalize the pattern dimensions."""
        if isinstance(self._width, bool) or not isinstance(self._width, int):
            raise TypeError("The pattern width must be an integer.")
        if not 3 <= self._width <= 16:
            raise ValueError("The width must be between 3 and 16 pixels.")
        if self._height is None:
            height, remainder = divmod(len(self.data), self._width)
            if remainder:
                raise ValueError("The length of the data must be divisible by width.")
            self._height = height
        if isinstance(self._height, bool) or not isinstance(self._height, int):
            raise TypeError("The pattern height must be an integer or None.")
        if self._height * self._width != len(self.data):
            raise ValueError("The length of the data must be equal to width * height.")
        if not 3 <= self._height <= 16:
            raise ValueError("The height must be between 3 and 16 pixels.")

    def __str__(self) -> str:
        """Return a readable representation of this pattern."""
        return f"Unifont Pattern ({self._width}x{self._height})"

    @property
    def width(self) -> int:
        """Width of the pattern."""
        return self._width

    @property
    def height(self) -> int:
        """Height of the pattern."""
        assert self._height is not None
        return self._height

    @classmethod
    def init_from_img(cls, img_path: FilePath) -> "Pattern":
        """Create a pattern from a black, white, and transparent image."""
        resolved_path = Validator.file_path(img_path)
        if not resolved_path.is_file():
            raise FileNotFoundError(f"File not found: {resolved_path}")

        with Img.open(resolved_path) as source, source.convert("RGBA") as image:
            data: list[int] = []
            for pixel in image.getdata():
                if pixel == (255, 255, 255, 255):
                    data.append(0)
                elif pixel == (0, 0, 0, 255):
                    data.append(1)
                elif pixel == (0, 0, 0, 0):
                    data.append(-1)
                else:
                    raise ValueError(f"Invalid pixel RGBA value: {pixel}")
            size = image.size

        return cls(data, *size)


@dataclass
class SearchPattern(Pattern):
    """Binary bitmap pattern used to find pixels in a glyph."""

    def __post_init__(self) -> None:
        """Validate dimensions and binary pattern values."""
        super().__post_init__()
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value not in {0, 1}
            for value in self.data
        ):
            raise ValueError("The pattern data must contain only integer 0 and 1 values.")

    @classmethod
    def init_from_img(cls, img_path: FilePath) -> "SearchPattern":
        """Create a search pattern from an image."""
        pattern = super().init_from_img(img_path)
        return cls(pattern.data, pattern.width, pattern.height)


@dataclass
class ReplacePattern(Pattern):
    """Bitmap pattern used to replace pixels, with ``-1`` meaning unchanged."""

    def __post_init__(self) -> None:
        """Validate dimensions and replacement pattern values."""
        super().__post_init__()
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value not in {-1, 0, 1}
            for value in self.data
        ):
            raise ValueError("The pattern data must contain only integer -1, 0, and 1 values.")

    @classmethod
    def init_from_img(cls, img_path: FilePath) -> "ReplacePattern":
        """Create a replacement pattern from an image."""
        pattern = super().init_from_img(img_path)
        return cls(pattern.data, pattern.width, pattern.height)


__all__ = ["Pattern", "ReplacePattern", "SearchPattern"]
