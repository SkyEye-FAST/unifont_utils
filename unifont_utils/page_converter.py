# @Author: SkyEye_FAST <skyeyefast@foxmail.com>
# @Copyright: Copyright (C) 2024-2025 SkyEye_FAST
"""Utilities for converting an entire 256-code-point page between .hex and images."""

from collections.abc import Iterable
from pathlib import Path
from typing import cast

from PIL import Image as Img

from .base import FilePath, Validator
from .glyphs import COLOR_MAP, ColorScheme, Glyph, GlyphSet

HEX_DIGIT_STRINGS: list[str] = [
    "0030:00000000182442424242424224180000",
    "0031:000000000818280808080808083E0000",
    "0032:000000003C4242020C102040407E0000",
    "0033:000000003C4242021C020242423C0000",
    "0034:00000000040C142444447E0404040000",
    "0035:000000007E4040407C020202423C0000",
    "0036:000000001C2040407C424242423C0000",
    "0037:000000007E0202040404080808080000",
    "0038:000000003C4242423C424242423C0000",
    "0039:000000003C4242423E02020204380000",
    "0041:0000000018242442427E424242420000",
    "0042:000000007C4242427C424242427C0000",
    "0043:000000003C42424040404042423C0000",
    "0044:00000000784442424242424244780000",
    "0045:000000007E4040407C404040407E0000",
    "0046:000000007E4040407C40404040400000",
    "0055:000000004242424242424242423C0000",
    "002B:0000000000000808087F080808000000",
]

UNIHEX_WIDTH = 18 * 32  # 576
UNIHEX_HEIGHT = 17 * 32  # 544


def _normalize_page(page: int | str) -> int:
    """Normalize a page identifier to an integer block index."""
    page_int = int(page, 16) if isinstance(page, str) else int(page)
    if page_int < 0 or page_int > (0x10FFFF >> 8):
        raise ValueError("The page value must be between 0x0 and 0x10FF.")
    return page_int


def _resolve_image_format(output_path: Path, img_format: str | None) -> str:
    """Resolve the Pillow image format from explicit input or file suffix."""
    if img_format:
        return img_format.upper()
    if suffix := output_path.suffix:
        return suffix.lstrip(".").upper()
    return "PNG"


def _background_rgba(scheme: ColorScheme) -> tuple[int, int, int, int]:
    """Get the RGBA value used for background pixels in a color scheme."""
    for name, value in scheme.color_map.items():
        if value == 0:
            return COLOR_MAP[name]
    raise ValueError("Color scheme must map background to value 0.")


def _foreground_rgba(scheme: ColorScheme) -> tuple[int, int, int, int]:
    """Get the RGBA value used for foreground pixels in a color scheme."""
    for name, value in scheme.color_map.items():
        if value == 1:
            return COLOR_MAP[name]
    raise ValueError("Color scheme must map foreground to value 1.")


def _hex2bit_bytes(instring: str) -> list[list[int]]:
    """Convert the portion of a hex string after ':' into a 32x4 byte bitmap."""
    character = [[0, 0, 0, 0] for _ in range(32)]
    data = instring.strip()
    width = 0
    if len(data) <= 34:
        width = 0
    elif len(data) <= 66:
        width = 1
    elif len(data) <= 98:
        width = 3
    else:
        width = 4

    k = 0 if width > 1 else 1
    j = 0
    for i in range(8, 24):
        character[i][k] = int(data[j : j + 2], 16)
        j += 2
        if width > 0:
            character[i][k + 1] = int(data[j : j + 2], 16)
            j += 2
            if width > 1:
                character[i][k + 2] = int(data[j : j + 2], 16)
                j += 2
                if width > 2:
                    character[i][k + 3] = int(data[j : j + 2], 16)
                    j += 2
    return character


def _build_hex_digit_bitmaps() -> list[list[int]]:
    """Return inverted byte rows for the 18 hex digit glyphs used in headers."""
    hexbits: list[list[int]] = [[0] * 32 for _ in range(18)]
    for idx, entry in enumerate(HEX_DIGIT_STRINGS):
        _, hex_part = entry.split(":", 1)
        charbits = _hex2bit_bytes(hex_part)
        for row in range(32):
            hexbits[idx][row] = (~charbits[row][1]) & 0xFF
    return hexbits


def _render_unihex2bmp_page(glyphs: GlyphSet, page: int | str, *, flip: bool = True) -> Img.Image:
    """Render a page image matching unihex2bmp.c output (576x544 monochrome)."""
    unipage = _normalize_page(page)
    bitmap: list[list[int]] = [[0xFF for _ in range(72)] for _ in range(UNIHEX_HEIGHT)]
    hexbits = _build_hex_digit_bitmaps()

    # Display the page number as a 4-nybble value (e.g., 0x0084).
    pnybble3 = (unipage >> 12) & 0xF
    pnybble2 = (unipage >> 8) & 0xF
    pnybble1 = (unipage >> 4) & 0xF
    pnybble0 = unipage & 0xF
    for i in range(32):
        bitmap[i][1] = hexbits[16][i]
        bitmap[i][2] = hexbits[17][i]
        bitmap[i][3] = hexbits[pnybble3][i]
        bitmap[i][4] = hexbits[pnybble2][i]
        bitmap[i][5] = hexbits[pnybble1][i]
        bitmap[i][6] = hexbits[pnybble0][i]

    pnybble3 = (unipage >> 4) & 0xF
    pnybble2 = unipage & 0xF
    for i in range(16):
        for j in range(32):
            if flip:
                bitmap[j][((i + 2) << 2) | 0] = (hexbits[pnybble3][j] >> 4) | 0xF0
                bitmap[j][((i + 2) << 2) | 1] = (hexbits[pnybble3][j] << 4) | (
                    hexbits[pnybble2][j] >> 4
                )
                bitmap[j][((i + 2) << 2) | 2] = (hexbits[pnybble2][j] << 4) | (hexbits[i][j] >> 4)
                bitmap[j][((i + 2) << 2) | 3] = (hexbits[i][j] << 4) | 0x0F
            else:
                bitmap[j][((i + 2) << 2) | 1] = (hexbits[i][j] >> 4) | 0xF0
                bitmap[j][((i + 2) << 2) | 2] = (hexbits[i][j] << 4) | 0x0F

    for i in range(16):
        toppixelrow = 32 * (i + 1) - 1
        for j in range(32):
            if not flip:
                bitmap[toppixelrow + j][4] = hexbits[pnybble3][j]
                bitmap[toppixelrow + j][5] = hexbits[pnybble2][j]
            bitmap[toppixelrow + j][6] = hexbits[i][j]

    for i in range(1 * 32, 17 * 32):
        if (i & 0x1F) == 7:
            i += 1
        elif (i & 0x1F) == 14:
            i += 2
        elif (i & 0x1F) == 22:
            i += 1
        for j in range(1, 18):
            bitmap[i][(j << 2) | 3] &= 0xFE

    for i in range(1 * 32 - 1, 18 * 32 - 1, 32):
        for j in range(2, 18):
            bitmap[i][(j << 2) | 0] = 0x00
            bitmap[i][(j << 2) | 1] = 0x81
            bitmap[i][(j << 2) | 2] = 0x81
            bitmap[i][(j << 2) | 3] = 0x00

    bitmap[31][7] = 0xFE

    glyph_dict = getattr(glyphs, "_glyphs", {})
    for offset in range(256):
        code_point_value = (unipage << 8) + offset
        code_point_str = Validator.code_point(code_point_value)
        glyph = glyph_dict.get(code_point_str)
        if glyph is None or not glyph.hex_str:
            continue

        thischarbyte = offset & 0xFF
        thiscol = (thischarbyte & 0xF) + 2
        thischarrow = thischarbyte >> 4
        if flip:
            thiscol, thischarrow = thischarrow, thiscol
            thiscol += 2
            thischarrow -= 2
        toppixelrow = 32 * (thischarrow + 1) - 1

        charbits = _hex2bit_bytes(glyph.hex_str)
        for i in range(8, 24):
            for b in range(4):
                value = (~charbits[i][b]) & 0xFF
                if b == 3:
                    value &= 0xFE
                bitmap[toppixelrow + i][(thiscol << 2) | b] = value
        bitmap[toppixelrow + 8][(thiscol << 2) | 3] |= 1
        bitmap[toppixelrow + 14][(thiscol << 2) | 3] |= 1
        bitmap[toppixelrow + 15][(thiscol << 2) | 3] |= 1
        bitmap[toppixelrow + 23][(thiscol << 2) | 3] |= 1

    pixels: list[int] = []
    for row in bitmap:
        for byte in row:
            pixels.extend(255 if byte & (1 << bit) else 0 for bit in range(7, -1, -1))

    img = Img.new("L", (UNIHEX_WIDTH, UNIHEX_HEIGHT))
    img.putdata(pixels)
    return img


def hex_page_to_image(
    glyphs: GlyphSet,
    page: int | str,
    *,
    color_scheme: str | ColorScheme = "black_and_white",
) -> Img.Image:
    """Render a 256-code-point page."""
    scheme = color_scheme if isinstance(color_scheme, ColorScheme) else ColorScheme(color_scheme)
    mask = _render_unihex2bmp_page(glyphs, page, flip=True)

    # The unihex2bmp layout is monochrome; map foreground/background to the requested scheme.
    if scheme.name == "black_and_white":
        return mask

    background_rgba = _background_rgba(scheme)
    foreground_rgba = _foreground_rgba(scheme)
    pixels = [foreground_rgba if value < 128 else background_rgba for value in mask.getdata()]
    colored = Img.new("RGBA", mask.size)
    colored.putdata(pixels)
    return colored


def save_page_image(
    glyphs: GlyphSet,
    page: int | str,
    output: FilePath,
    *,
    color_scheme: str | ColorScheme = "black_and_white",
    img_format: str | None = None,
) -> Path:
    """Render and save a glyph page image."""
    output_path = Validator.file_path(output)
    img = hex_page_to_image(glyphs, page, color_scheme=color_scheme)
    resolved_format = _resolve_image_format(output_path, img_format)
    try:
        img.save(output_path, format=resolved_format)
    except Exception as exc:  # pragma: no cover - delegated to Pillow
        raise ValueError(f"Failed to save image in format {resolved_format}: {exc}") from exc
    return output_path


def image_to_hex_page(
    img_path: FilePath,
    page: int | str,
    *,
    color_auto_detect: bool = True,
    color_scheme: str | ColorScheme | None = None,
    skip_blank: bool = True,
) -> GlyphSet:
    """Convert a page image into a GlyphSet representing 256 code points."""
    page_int = _normalize_page(page)
    resolved_path = Validator.file_path(img_path)
    if not resolved_path.exists():
        raise FileNotFoundError(f"File not found: {resolved_path}")

    if color_scheme is None and not color_auto_detect:
        raise ValueError("Specify a color scheme when auto detection is disabled.")

    image = Img.open(resolved_path).convert("RGBA")
    if image.size != (UNIHEX_WIDTH, UNIHEX_HEIGHT):
        raise ValueError("Image dimensions must be 576x544 to match unihex2bmp output.")

    rgba_values = list(cast(Iterable[tuple[int, int, int, int]], image.getdata()))
    if color_auto_detect:
        detected_name = Glyph._auto_detect_color_scheme(image.size[0], rgba_values)
        scheme = ColorScheme(detected_name)
    else:
        scheme = (
            color_scheme
            if isinstance(color_scheme, ColorScheme)
            else ColorScheme(color_scheme or "black_and_white")
        )

    bits = _rgba_to_bits(rgba_values, scheme)
    background_value = 0

    # Reconstruct stored bitmap bytes from bits (background -> 1, foreground -> 0).
    bitmap: list[list[int]] = [[0 for _ in range(72)] for _ in range(UNIHEX_HEIGHT)]
    for y in range(UNIHEX_HEIGHT):
        row_base = y * UNIHEX_WIDTH
        for byte_idx in range(72):
            value = 0
            for bit in range(8):
                bit_val = bits[row_base + byte_idx * 8 + (7 - bit)]
                if bit_val == background_value:
                    value |= 1 << bit
            bitmap[y][byte_idx] = value

    glyphs = GlyphSet()

    for offset in range(256):
        thischarbyte = offset & 0xFF
        thiscol = (thischarbyte & 0xF) + 2
        thischarrow = thischarbyte >> 4
        thiscol, thischarrow = thischarrow, thiscol
        thiscol += 2
        thischarrow -= 2
        toppixelrow = 32 * (thischarrow + 1) - 1

        charbytes = [[0, 0, 0, 0] for _ in range(32)]
        for i in range(8, 24):
            for b in range(4):
                stored = bitmap[toppixelrow + i][(thiscol << 2) + b]
                charbytes[i][b] = (~stored) & 0xFF
            charbytes[i][3] &= 0xFE

        has_b0 = any(charbytes[i][0] for i in range(8, 24))
        has_b2 = any(charbytes[i][2] for i in range(8, 24))
        has_b3 = any(charbytes[i][3] & 0xFE for i in range(8, 24))

        if not (has_b0 or has_b2 or has_b3):
            use_bytes = [1]
        elif has_b3 or has_b0:
            use_bytes = [0, 1, 2, 3]
        else:
            use_bytes = [1, 2]

        hex_parts: list[str] = []
        for i in range(8, 24):
            hex_parts.extend(f"{charbytes[i][b]:02X}" for b in use_bytes)

        if skip_blank and all(part == "00" for part in hex_parts):
            continue

        hex_str = "".join(hex_parts)
        code_point_value = (page_int << 8) + offset
        code_point_str = Validator.code_point(code_point_value)
        glyphs.add_glyph((code_point_str, hex_str))

    return glyphs


def _rgba_to_bits(
    rgba_values: Iterable[tuple[int, int, int, int]], scheme: ColorScheme
) -> list[int]:
    """Convert RGBA pixels to binary glyph data according to a color scheme."""
    rgba_map = {COLOR_MAP[name]: value for name, value in scheme.color_map.items()}
    bits: list[int] = []
    for pixel in rgba_values:
        if pixel not in rgba_map:
            raise ValueError(f"Invalid pixel RGBA value: {pixel}")
        bits.append(rgba_map[pixel])
    return bits
