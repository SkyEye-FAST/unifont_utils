# -*- encoding: utf-8 -*-
"""Unifont Utils - Console"""

import click

from .base import Validator as V
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
@click.option(
    "--code_point", "--cp", required=True, type=str, help="The code point to edit."
)
@click.option("--output", default=None, help="Output file path for the edited font.")
def hexfile(font_path, code_point, output):
    """Edit a code point in the Unifont .hex file."""

    click.echo(f"Editing Unifont .hex file: {font_path}")
    click.echo(f"Editing code point: {V.code_point(code_point)}\n")
    output = output if output else output_path(font_path)

    glyphs = GlyphSet.load_hex_file(font_path)
    GlyphEditor(glyphs[code_point]).run()
    glyphs.save_hex_file(output)

    click.echo(f"\nOutput saved to: {output}")


@edit.command()
@click.option(
    "--code_point", "--cp", required=True, type=str, help="The code point to edit."
)
@click.option(
    "--hex_str",
    "--hex",
    required=True,
    type=str,
    help="The .hex format string to edit.",
)
def hexstr(code_point, hex_str):
    """Edit a single Unifont .hex format string."""

    click.echo(f"Editing code point: {V.code_point(code_point)}")

    click.echo(f"Editing .hex format string: {hex_str}")
    glyph = Glyph.init_from_hex(code_point, hex_str)
    GlyphEditor(glyph).run()

    click.echo(f"\nResult: {glyph.hex_str}\n")


@edit.command()
@click.option(
    "--code_point", "--cp", required=True, type=str, help="The code point to edit."
)
@click.option("--width", "-w", default=16, type=int, help="The width of the glyph.")
def empty(code_point, width):
    """Create an empty Unifont glyph for editing."""

    click.echo(f"Editing code point: {V.code_point(code_point)}")
    click.echo(f"Glyph width: {width}")

    glyph = Glyph.init_from_hex(code_point, "0" * (width * 4))
    GlyphEditor(glyph).run()

    click.echo(f"\nResult: {glyph.hex_str}\n")
    glyph.print_glyph(display_hex=True, display_bin=True)


@cli.command()
def info():
    """Show information about Unipie."""

    click.echo("Unipie v0.1.0")
    click.echo("Written by SkyEye_FAST")


if __name__ == "__main__":
    cli()
