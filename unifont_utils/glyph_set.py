"""Collections and file I/O for GNU Unifont glyphs."""

import tempfile
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType

from PIL import Image as Img

from unifont_utils.base import CodePoint, CodePoints, FilePath, Validator
from unifont_utils.glyph import Glyph


def _coerce_glyph(glyph: Glyph | tuple[CodePoint, str]) -> Glyph:
    """Return a validated glyph instance from a glyph or tuple."""
    if isinstance(glyph, Glyph):
        return glyph
    if isinstance(glyph, tuple) and len(glyph) == 2:
        code_point, hex_str = glyph
        return Glyph.init_from_hex(code_point, hex_str)
    raise TypeError("Invalid glyph type. Must be a Glyph or a (code_point, hex_str) tuple.")


@dataclass
class GlyphSet:
    """An ordered collection of glyphs keyed by normalized code point."""

    _glyphs: dict[str, Glyph] = field(default_factory=dict)

    @property
    def glyphs(self) -> Mapping[str, Glyph]:
        """Read-only mapping of code points to glyphs, sorted numerically."""
        self.sort_glyphs()
        return MappingProxyType(self._glyphs)

    @property
    def code_points(self) -> list[str]:
        """Normalized code points in numeric order."""
        self.sort_glyphs()
        return list(self._glyphs)

    def __str__(self) -> str:
        """Return a readable representation of the set."""
        return f"Unifont Glyph Set ({len(self)} glyphs)"

    def __getitem__(self, code_point: CodePoint) -> Glyph:
        """Return a glyph by code point."""
        return self.get_glyph(code_point)

    def __setitem__(self, code_point: CodePoint, hex_str: str) -> None:
        """Add a glyph from a code point and ``.hex`` payload."""
        self.add_glyph((code_point, hex_str))

    def __delitem__(self, code_point: CodePoint) -> None:
        """Remove a glyph by code point."""
        self.remove_glyph(code_point)

    def __add__(self, other: "GlyphSet | Glyph") -> "GlyphSet":
        """Return a new collection containing glyphs from both operands."""
        result = GlyphSet(self._glyphs.copy())
        result += other
        return result

    def __iadd__(self, other: "GlyphSet | Glyph") -> "GlyphSet":
        """Add a glyph or glyph set to this collection."""
        if isinstance(other, Glyph):
            self.add_glyph(other)
        elif isinstance(other, GlyphSet):
            self._glyphs.update(other._glyphs)
        else:
            raise TypeError("Invalid type for in-place addition to GlyphSet.")
        return self

    def __len__(self) -> int:
        """Return the number of glyphs."""
        return len(self._glyphs)

    def __iter__(self) -> Iterator[Glyph]:
        """Iterate over glyphs in numeric code-point order."""
        self.sort_glyphs()
        return iter(self._glyphs.values())

    def __contains__(self, glyph: Glyph | CodePoint) -> bool:
        """Return whether a glyph or code point exists in the collection."""
        code_point = glyph.code_point if isinstance(glyph, Glyph) else glyph
        return Validator.code_point(code_point) in self._glyphs

    @classmethod
    def init_glyphs(cls, code_points: CodePoints) -> "GlyphSet":
        """Create empty glyphs for each requested code point."""
        return cls(
            {
                code_point: Glyph.init_from_hex(code_point, "")
                for code_point in Validator.code_points(code_points)
            }
        )

    def get_glyph(self, code_point: CodePoint) -> Glyph:
        """Return a glyph by code point."""
        normalized = Validator.code_point(code_point)
        try:
            return self._glyphs[normalized]
        except KeyError as exc:
            display_code_point = Validator.code_point_display(normalized)
            raise KeyError(f"Glyph with code point U+{display_code_point} not found.") from exc

    def get_glyphs(self, code_points: CodePoints, *, skip_empty: bool = True) -> "GlyphSet":
        """Return a new set containing requested code points."""
        result = GlyphSet()
        for code_point in Validator.code_points(code_points):
            if code_point in self._glyphs:
                result.add_glyph(self._glyphs[code_point])
            elif not skip_empty:
                result.add_glyph((code_point, ""))
        return result

    def add_glyph(self, glyph: Glyph | tuple[CodePoint, str]) -> None:
        """Add one glyph, rejecting duplicate code points."""
        glyph_object = _coerce_glyph(glyph)
        if glyph_object.code_point in self._glyphs:
            display_code_point = Validator.code_point_display(glyph_object.code_point)
            raise ValueError(f"Glyph with code point U+{display_code_point} already exists.")
        self._glyphs[glyph_object.code_point] = glyph_object

    def remove_glyph(self, code_point: CodePoint) -> None:
        """Remove one glyph by code point."""
        normalized = Validator.code_point(code_point)
        try:
            del self._glyphs[normalized]
        except KeyError as exc:
            display_code_point = Validator.code_point_display(normalized)
            raise KeyError(f"Glyph with code point U+{display_code_point} not found.") from exc

    def update_glyph(self, glyph: Glyph | tuple[CodePoint, str]) -> None:
        """Replace the bitmap of an existing glyph."""
        glyph_object = _coerce_glyph(glyph)
        try:
            existing = self._glyphs[glyph_object.code_point]
        except KeyError as exc:
            display_code_point = Validator.code_point_display(glyph_object.code_point)
            raise KeyError(f"Glyph with code point U+{display_code_point} not found.") from exc
        existing.hex_str = glyph_object.hex_str

    def sort_glyphs(self) -> None:
        """Sort glyphs numerically by code point; empty sets are already sorted."""
        self._glyphs = dict(sorted(self._glyphs.items(), key=lambda item: int(item[0], 16)))

    @classmethod
    def load_hex_file(cls, file_path: FilePath) -> "GlyphSet":
        """Load glyphs from a UTF-8 GNU Unifont ``.hex`` file."""
        resolved_path = Validator.file_path(file_path)
        if not resolved_path.is_file():
            raise FileNotFoundError(f"File not found: {resolved_path}")

        glyphs = cls()
        with resolved_path.open("r", encoding="utf-8") as font_file:
            for line_number, line in enumerate(font_file, start=1):
                current_line = line.strip()
                if not current_line:
                    continue
                if ":" not in current_line:
                    raise ValueError(f"Invalid line {line_number}: {current_line}")
                code_point, hex_str = current_line.split(":", 1)
                try:
                    glyphs.add_glyph((code_point, hex_str))
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"Invalid line {line_number}: {current_line}") from exc
        return glyphs

    def save_hex_file(self, file_path: FilePath) -> None:
        """Atomically save glyphs to a UTF-8 GNU Unifont ``.hex`` file."""
        resolved_path = Validator.file_path(file_path)
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                newline="\n",
                dir=resolved_path.parent,
                prefix=f".{resolved_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                for code_point, glyph in sorted(
                    self._glyphs.items(), key=lambda item: int(item[0], 16)
                ):
                    temporary_file.write(f"{code_point}:{glyph.hex_str}\n")
            temporary_path.replace(resolved_path)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    def save_unicode_page(self, file_path: FilePath, start: CodePoint = "4E00") -> None:
        """Save up to 256 glyphs as a 16x16-cell Unicode page image."""
        resolved_path = Validator.file_path(file_path)
        start_value = int(Validator.code_point(start), 16)
        self.sort_glyphs()

        with Img.new("RGBA", (256, 256)) as image:
            position = 0
            for code_point, glyph in self._glyphs.items():
                if int(code_point, 16) < start_value:
                    continue
                if glyph.hex_str:
                    source_data = glyph.data
                    cell_data = [
                        pixel
                        for row in range(16)
                        for pixel in (
                            source_data[row * glyph.width : (row + 1) * glyph.width]
                            + [0] * (16 - glyph.width)
                        )
                    ]
                    rgba_data = [
                        (255, 255, 255, 255) if pixel else (0, 0, 0, 0) for pixel in cell_data
                    ]
                    with Img.new("RGBA", (16, 16)) as glyph_image:
                        glyph_image.putdata(rgba_data)
                        x = (position % 16) * 16
                        y = (position // 16) * 16
                        image.paste(glyph_image, (x, y))

                position += 1
                if position == 256:
                    break
            image.save(resolved_path)


__all__ = ["GlyphSet"]
