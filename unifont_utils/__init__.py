"""Public API for Unifont Utils."""

from unifont_utils._version import __version__
from unifont_utils.colors import ColorScheme
from unifont_utils.converter import Converter
from unifont_utils.diff import diff_glyphs, print_diff
from unifont_utils.downloader import UnifontDownloader
from unifont_utils.editor import GlyphEditor, GlyphReplacer
from unifont_utils.glyph import Glyph
from unifont_utils.glyph_set import GlyphSet
from unifont_utils.page_converter import hex_page_to_image, image_to_hex_page, save_page_image
from unifont_utils.patterns import Pattern, ReplacePattern, SearchPattern

__author__ = "SkyEye_FAST"
__copyright__ = "Copyright (C) 2024-2026 SkyEye_FAST"
__license__ = "GPL-3.0-or-later"
__maintainer__ = "SkyEye_FAST"
__email__ = "skyeyefast@foxmail.com"

__all__ = [
    "ColorScheme",
    "Converter",
    "Glyph",
    "GlyphEditor",
    "GlyphReplacer",
    "GlyphSet",
    "Pattern",
    "ReplacePattern",
    "SearchPattern",
    "UnifontDownloader",
    "__version__",
    "diff_glyphs",
    "hex_page_to_image",
    "image_to_hex_page",
    "print_diff",
    "save_page_image",
]
