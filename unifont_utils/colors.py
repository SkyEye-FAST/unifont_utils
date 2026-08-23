"""Color schemes used to render and decode Unifont glyphs."""

from collections.abc import Mapping
from types import MappingProxyType

RGBA = tuple[int, int, int, int]

COLOR_MAP: Mapping[str, RGBA] = MappingProxyType(
    {
        "white": (255, 255, 255, 255),
        "black": (0, 0, 0, 255),
        "transparent": (0, 0, 0, 0),
    }
)
COLOR_VALUE_MAP: Mapping[RGBA, str] = MappingProxyType(
    {value: name for name, value in COLOR_MAP.items()}
)


class ColorScheme:
    """Map logical background and foreground colors to binary pixel values."""

    _available_schemes: Mapping[str, Mapping[str, int]] = MappingProxyType(
        {
            "black_and_white": MappingProxyType({"white": 0, "black": 1}),
            "inverted_black_and_white": MappingProxyType({"black": 0, "white": 1}),
            "transparent_and_black": MappingProxyType({"transparent": 0, "black": 1}),
            "transparent_and_white": MappingProxyType({"transparent": 0, "white": 1}),
        }
    )

    def __init__(self, scheme_name: str = "black_and_white") -> None:
        """Create a named color scheme.

        Args:
            scheme_name: Name of an available color scheme.

        Raises:
            ValueError: If the color scheme is unknown.
        """
        try:
            color_map = self._available_schemes[scheme_name]
        except KeyError as exc:
            raise ValueError(f"Invalid color scheme: {scheme_name}") from exc

        self._scheme_name = scheme_name
        self._color_map = color_map

    def __str__(self) -> str:
        """Return a readable representation of this color scheme."""
        return f"Unifont Color Scheme ({dict(self._color_map)})"

    @property
    def name(self) -> str:
        """Name of the color scheme."""
        return self._scheme_name

    @property
    def color_map(self) -> Mapping[str, int]:
        """Read-only mapping from color names to binary pixel values."""
        return self._color_map


def resolve_color_scheme(color_scheme: str | ColorScheme) -> ColorScheme:
    """Return a validated color scheme instance."""
    if isinstance(color_scheme, str):
        return ColorScheme(color_scheme)
    if isinstance(color_scheme, ColorScheme):
        return color_scheme
    raise TypeError("Invalid color scheme type. Must be a string or a ColorScheme.")


__all__ = ["COLOR_MAP", "COLOR_VALUE_MAP", "ColorScheme", "RGBA"]
