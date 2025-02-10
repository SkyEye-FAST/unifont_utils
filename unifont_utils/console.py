# @Author: SkyEye_FAST <skyeyefast@foxmail.com>
# @Copyright: Copyright (C) 2024-2025 SkyEye_FAST
"""Unifont Utils - Console"""

import click

from .base import Validator
from .editor import GlyphEditor
from .glyphs import Glyph, GlyphSet


def output_path(font_path: str) -> str:
    """Return the default output path for the edited font."""
    return font_path.replace(".hex", "_edited.hex")


@click.group()
def cli():
    """Unipie - Unifont Pixel Interactive Editor"""


@cli.group()
def edit():
    """Edit the Unifont .hex glyphs."""


@edit.command()
@click.option(
    "--font_path",
    "--path",
    "-p",
    required=True,
    type=click.Path(exists=True),
    help="The path to the Unifont .hex file.",
)
@click.option("--code_point", "--cp", required=True, type=str, help="The code point to edit.")
@click.option("--output", "-o", default=None, help="Output file path for the edited font.")
def hexfile(font_path, code_point, output):
    """Edit a code point in the Unifont .hex file."""
    click.echo(f"Editing Unifont .hex file: {font_path}")
    click.echo(f"Editing code point: {Validator.code_point(code_point)}\n")
    output = output if output else output_path(font_path)

    glyphs = GlyphSet.load_hex_file(font_path)
    GlyphEditor(glyphs[code_point]).run()
    glyphs.save_hex_file(output)

    click.echo(f"\nOutput saved to: {output}")


@edit.command()
@click.option("--code_point", "--cp", required=True, type=str, help="The code point to edit.")
@click.option(
    "--hex_str",
    "--hex",
    required=True,
    type=str,
    help="The .hex format string to edit.",
)
def hexstr(code_point, hex_str):
    """Edit a single Unifont .hex format string."""
    click.echo(f"Editing code point: {Validator.code_point(code_point)}")

    click.echo(f"Editing .hex format string: {hex_str}")
    glyph = Glyph.init_from_hex(code_point, hex_str)
    GlyphEditor(glyph).run()

    click.echo(f"\nResult: {glyph.hex_str}\n")


@edit.command()
@click.option("--code_point", "--cp", required=True, type=str, help="The code point to edit.")
@click.option("--width", "-w", default=16, type=int, help="The width of the glyph.")
def empty(code_point, width):
    """Create an empty Unifont glyph for editing."""
    click.echo(f"Editing code point: {Validator.code_point(code_point)}")
    click.echo(f"Glyph width: {width}")

    glyph = Glyph.init_from_hex(code_point, "0" * (width * 4))
    GlyphEditor(glyph).run()

    click.echo(f"\nResult: {glyph.hex_str}\n")
    glyph.print_glyph(display_hex=True, display_bin=True)


@cli.group()
def convert():
    """Convert between Unifont formats."""


@convert.command()
@click.option(
    "--hex_str",
    "--hex",
    required=True,
    type=str,
    help="The .hex format string to convert.",
)
@click.option(
    "--output",
    "-o",
    required=True,
    type=click.Path(),
    help="The output image path.",
)
@click.option(
    "--img_format",
    "--format",
    "-f",
    default="PNG",
    type=str,
    help="The output image format.",
)
@click.option(
    "--color_scheme",
    default="black_and_white",
    type=str,
    help="The color scheme for the output image.",
)
def hex2img(hex_str, output, img_format, color_scheme):
    """Convert a .hex format string to a image."""
    Glyph.init_from_hex(0, hex_str).save_img(
        output, img_format=img_format, color_scheme=color_scheme
    )
    click.echo(f"Output saved to: {output}")


@convert.command()
@click.option(
    "--img_path",
    "--path",
    "-p",
    required=True,
    type=click.Path(exists=True),
    help="The path to the input image.",
)
@click.option(
    "--auto_detect",
    is_flag=True,
    default=False,
    type=bool,
    help="Whether to automatically detect the color scheme from the image.",
)
@click.option(
    "--color_scheme",
    type=str,
    help="The color scheme for the output image.",
)
def img2hex(img_path, auto_detect, color_scheme):
    """Convert a image to a .hex format string."""
    click.echo(f"Loading image: {img_path}\n")
    glyph = Glyph.init_from_img(
        0, img_path, color_auto_detect=auto_detect, color_scheme=color_scheme
    )
    click.echo(f"Result: {glyph.hex_str}")


@cli.command()
def info():
    """Show information about Unipie."""
    click.echo("Unipie - Unifont Pixel Interactive Editor\n")
    click.echo("Unipie v0.2.0")
    click.echo("Written by SkyEye_FAST")


if __name__ == "__main__":
    cli()
