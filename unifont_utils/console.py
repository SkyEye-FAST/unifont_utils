# @Author: SkyEye_FAST <skyeyefast@foxmail.com>
# @Copyright: Copyright (C) 2024-2025 SkyEye_FAST
"""Unifont Utils - Console"""

import io
from contextlib import redirect_stdout

import click

from .base import Validator
from .downloader import UnifontDownloader
from .editor import GlyphEditor
from .glyphs import Glyph, GlyphSet
from .page_converter import image_to_hex_page, save_page_image


def output_path(font_path: str) -> str:
    """Return the default output path for an edited font file.

    Args:
        font_path (str): Original .hex font file path.

    Returns:
        str: Suggested output path with "_edited" suffix.
    """
    return font_path.replace(".hex", "_edited.hex")


@click.group()
def cli():
    """Unipie - Unifont Pixel Interactive Editor"""


@cli.group()
def edit():
    """Edit the Unifont .hex glyphs."""


@edit.command(name="file")
@click.option(
    "--font_path",
    "--path",
    "-p",
    required=True,
    type=click.Path(exists=True),
    help="The path to the Unifont .hex file.",
)
@click.option("--code_point", "--cp", "-c", required=True, type=str, help="The code point to edit.")
@click.option(
    "--output",
    "-o",
    default=None,
    help="Output file path for the edited font. If provided, --overwrite is ignored.",
)
@click.option(
    "--overwrite/--no-overwrite",
    default=False,
    show_default=True,
    help="Overwrite the original .hex file when no --output is given.",
)
def hex_file(font_path, code_point, output, overwrite):
    """Edit a code point in the Unifont .hex file."""
    click.echo(f"Editing Unifont .hex file: {font_path}")
    display_cp = Validator.code_point_display(code_point)
    click.echo(f"Editing code point: {display_cp}\n")
    output = output if output else (font_path if overwrite else output_path(font_path))

    glyphs = GlyphSet.load_hex_file(font_path)
    GlyphEditor(glyphs[code_point]).run()
    glyphs.save_hex_file(output)

    click.echo(f"\nOutput saved to: {output}")


@edit.command(name="str")
@click.option("--code_point", "--cp", required=True, type=str, help="The code point to edit.")
@click.option(
    "--str",
    "--hex_str",
    "--hex",
    "-s",
    required=True,
    type=str,
    help="The .hex format string to edit.",
)
def hex_str(code_point, hex_string):
    """Edit a single Unifont .hex format string."""
    display_cp = Validator.code_point_display(code_point)
    click.echo(f"Editing code point: {display_cp}")

    click.echo(f"Editing .hex format string: {hex_string}")
    glyph = Glyph.init_from_hex(code_point, hex_string)
    GlyphEditor(glyph).run()

    click.echo(f"\nResult: {glyph.hex_str}\n")


@edit.command()
@click.option("--code_point", "--cp", required=True, type=str, help="The code point to edit.")
@click.option("--width", "-w", default=16, type=int, help="The width of the glyph.")
def empty(code_point, width):
    """Create an empty Unifont glyph for editing."""
    display_cp = Validator.code_point_display(code_point)
    click.echo(f"Editing code point: {display_cp}")
    click.echo(f"Glyph width: {width}")

    glyph = Glyph.init_from_hex(code_point, "0" * (width * 4))
    GlyphEditor(glyph).run()

    click.echo(f"\nResult: {glyph.hex_str}\n")
    glyph.print_glyph(display_hex=True, display_bin=True)


@cli.group(name="hex")
def hex_group():
    """Directly modify .hex files using raw strings."""


def _resolve_output(font_path: str, output: str | None, overwrite: bool) -> str:
    """Resolve the final output path based on parameters.

    Args:
        font_path (str): Source font path.
        output (str | None): Explicit output path or ``None``.
        overwrite (bool): Whether to overwrite the original file when no
            explicit output is provided.

    Returns:
        str: Resolved output file path.
    """
    return output if output else (font_path if overwrite else output_path(font_path))


@hex_group.command(name="add")
@click.option(
    "--font_path",
    "--path",
    "-p",
    required=True,
    type=click.Path(exists=True),
    help="The path to the Unifont .hex file to modify.",
)
@click.option("--code_point", "--cp", "-c", required=True, type=str, help="The code point to add.")
@click.option(
    "--hex_str",
    "--hex",
    "-s",
    required=True,
    type=str,
    help="The .hex format string to write.",
)
@click.option(
    "--output",
    "-o",
    default=None,
    help="Output file path. If provided, --overwrite is ignored.",
)
@click.option(
    "--overwrite/--no-overwrite",
    default=False,
    show_default=True,
    help="Overwrite the original .hex file when no --output is given.",
)
def hex_add(font_path, code_point, hex_string, output, overwrite):
    """Add a new code point entry to a .hex file."""
    target = _resolve_output(font_path, output, overwrite)
    glyphs = GlyphSet.load_hex_file(font_path)
    try:
        glyphs.add_glyph((code_point, hex_string))
    except Exception as exc:  # pragma: no cover - delegated to Click for UX
        raise click.ClickException(str(exc)) from exc

    glyphs.save_hex_file(target)
    display_cp = Validator.code_point_display(code_point)
    click.echo(f"Added U+{display_cp} and saved to: {target}")


@hex_group.command(name="replace")
@click.option(
    "--font_path",
    "--path",
    "-p",
    required=True,
    type=click.Path(exists=True),
    help="The path to the Unifont .hex file to modify.",
)
@click.option(
    "--code_point",
    "--cp",
    "-c",
    required=True,
    type=str,
    help="The code point to replace.",
)
@click.option(
    "--hex_str",
    "--hex",
    "-s",
    required=True,
    type=str,
    help="The new .hex format string.",
)
@click.option(
    "--output",
    "-o",
    default=None,
    help="Output file path. If provided, --overwrite is ignored.",
)
@click.option(
    "--overwrite/--no-overwrite",
    default=False,
    show_default=True,
    help="Overwrite the original .hex file when no --output is given.",
)
def hex_replace(font_path, code_point, hex_string, output, overwrite):
    """Replace an existing code point entry in a .hex file."""
    target = _resolve_output(font_path, output, overwrite)
    glyphs = GlyphSet.load_hex_file(font_path)
    try:
        glyphs.update_glyph((code_point, hex_string))
    except Exception as exc:  # pragma: no cover - delegated to Click for UX
        raise click.ClickException(str(exc)) from exc

    glyphs.save_hex_file(target)
    display_cp = Validator.code_point_display(code_point)
    click.echo(f"Replaced U+{display_cp} and saved to: {target}")


@hex_group.command(name="delete")
@click.option(
    "--font_path",
    "--path",
    "-p",
    required=True,
    type=click.Path(exists=True),
    help="The path to the Unifont .hex file to modify.",
)
@click.option(
    "--code_point", "--cp", "-c", required=True, type=str, help="The code point to delete."
)
@click.option(
    "--output",
    "-o",
    default=None,
    help="Output file path. If provided, --overwrite is ignored.",
)
@click.option(
    "--overwrite/--no-overwrite",
    default=False,
    show_default=True,
    help="Overwrite the original .hex file when no --output is given.",
)
def hex_delete(font_path, code_point, output, overwrite):
    """Delete a code point entry from a .hex file."""
    target = _resolve_output(font_path, output, overwrite)
    glyphs = GlyphSet.load_hex_file(font_path)
    try:
        glyphs.remove_glyph(code_point)
    except Exception as exc:  # pragma: no cover - delegated to Click for UX
        raise click.ClickException(str(exc)) from exc

    glyphs.save_hex_file(target)
    display_cp = Validator.code_point_display(code_point)
    click.echo(f"Deleted U+{display_cp} and saved to: {target}")


@hex_group.command(name="view")
@click.option(
    "--font_path",
    "--path",
    "-p",
    required=True,
    type=click.Path(exists=True),
    help="The path to the Unifont .hex file to read.",
)
@click.option(
    "--code_point",
    "--cp",
    "-c",
    required=True,
    type=str,
    help="The code point to view.",
)
def hex_view(font_path, code_point):
    """Render a glyph from a .hex file in the console."""
    glyphs = GlyphSet.load_hex_file(font_path)
    try:
        glyph = glyphs.get_glyph(code_point)
    except Exception as exc:  # pragma: no cover - delegated to Click for UX
        raise click.ClickException(str(exc)) from exc

    display_cp = Validator.code_point_display(code_point)
    click.echo(f"Viewing U+{display_cp} from {font_path}\n")
    glyph.print_glyph(display_hex=True, display_bin=True)


@hex_group.command(name="query")
@click.option(
    "--font_path",
    "--path",
    "-p",
    required=True,
    type=click.Path(exists=True),
    help="The path to the Unifont .hex file to read.",
)
@click.option(
    "--code_point",
    "--cp",
    "-c",
    required=True,
    type=str,
    help="The code point to query.",
)
@click.option(
    "--pure/--verbose",
    default=False,
    show_default=True,
    help="Only output the glyph .hex string, suppressing load logs.",
)
def hex_query(font_path, code_point, pure):
    """Print the .hex string for a glyph in a .hex file."""
    if pure:
        with redirect_stdout(io.StringIO()):
            glyphs = GlyphSet.load_hex_file(font_path)
    else:
        glyphs = GlyphSet.load_hex_file(font_path)
    try:
        glyph = glyphs.get_glyph(code_point)
    except Exception as exc:  # pragma: no cover - delegated to Click for UX
        raise click.ClickException(str(exc)) from exc

    display_cp = Validator.code_point_display(code_point)
    click.echo(f"U+{display_cp}: {glyph.hex_str}")


@cli.group()
def convert():
    """Convert between Unifont formats."""


@convert.group()
def single():
    """Convert a single glyph between .hex and image."""


@single.command(name="hex2img")
@click.option(
    "--str",
    "--hex_str",
    "--hex",
    "-s",
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
    "-c",
    "--color_scheme",
    default="black_and_white",
    type=str,
    help="The color scheme for the output image.",
)
def single_hex2img(hex_string, output, img_format, color_scheme):
    """Convert a .hex format string to an image."""
    Glyph.init_from_hex(0, hex_string).save_img(
        output, img_format=img_format, color_scheme=color_scheme
    )
    click.echo(f"Output saved to: {output}")


@single.command(name="img2hex")
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
    "--auto",
    "-a",
    is_flag=True,
    default=False,
    type=bool,
    help="Whether to automatically detect the color scheme from the image.",
)
@click.option(
    "--color_scheme",
    "-c",
    type=str,
    help="The color scheme for the output image.",
)
def single_img2hex(img_path, auto_detect, color_scheme):
    """Convert an image to a .hex format string."""
    click.echo(f"Loading image: {img_path}\n")
    glyph = Glyph.init_from_img(
        0, img_path, color_auto_detect=auto_detect, color_scheme=color_scheme
    )
    click.echo(f"Result: {glyph.hex_str}")


@convert.group()
def page():
    """Convert an entire 256-code-point page between .hex and image."""


@page.command(name="hex2img")
@click.option(
    "--font_path",
    "--path",
    "-p",
    required=True,
    type=click.Path(exists=True),
    help="The path to the Unifont .hex file containing the page.",
)
@click.option(
    "--page",
    "-g",
    required=True,
    type=str,
    help="The hex page value (e.g., 00, 83).",
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
    default=None,
    type=str,
    help="The output image format. Defaults to deriving from file suffix.",
)
@click.option(
    "-c",
    "--color_scheme",
    default="black_and_white",
    type=str,
    help="The color scheme for the output image.",
)
def page_hex2img(font_path, glyph_page, output, img_format, color_scheme):
    """Convert a .hex file page to an image."""
    glyphs = GlyphSet.load_hex_file(font_path)
    try:
        save_page_image(
            glyphs,
            glyph_page,
            output,
            color_scheme=color_scheme,
            img_format=img_format,
        )
    except Exception as exc:  # pragma: no cover - delegated to Click for UX
        raise click.ClickException(str(exc)) from exc

    page_display = (
        f"0x{int(glyph_page, 16):X}" if isinstance(glyph_page, str) else f"0x{int(glyph_page):X}"
    )
    click.echo(f"Saved page {page_display} to: {output}")


@page.command(name="img2hex")
@click.option(
    "--img_path",
    "--path",
    "-p",
    required=True,
    type=click.Path(exists=True),
    help="The path to the input page image.",
)
@click.option(
    "--page",
    "-g",
    required=True,
    type=str,
    help="The hex page value the image represents (e.g., 00, 83).",
)
@click.option(
    "--output",
    "-o",
    required=True,
    type=click.Path(),
    help="The output .hex file path.",
)
@click.option(
    "--auto_detect/--no-auto_detect",
    default=True,
    show_default=True,
    help="Automatically detect the color scheme from each glyph cell.",
)
@click.option(
    "--color_scheme",
    "-c",
    type=str,
    help="Manually specify the color scheme when auto detection is disabled.",
)
def page_img2hex(img_path, glyph_page, output, auto_detect, color_scheme):
    """Convert a page image to a .hex file containing 256 code points."""
    if not auto_detect and color_scheme is None:
        raise click.ClickException("Specify --color_scheme when --no-auto_detect is used.")

    try:
        glyphs = image_to_hex_page(
            img_path,
            glyph_page,
            color_auto_detect=auto_detect,
            color_scheme=color_scheme,
        )
    except Exception as exc:  # pragma: no cover - delegated to Click for UX
        raise click.ClickException(str(exc)) from exc

    glyphs.save_hex_file(output)
    click.echo(f"Extracted {len(glyphs)} glyphs from {img_path} to: {output}")


@cli.command()
@click.option(
    "--version",
    "-v",
    help="Unifont version (>=7.x). If omitted, the latest available version is used.",
)
@click.option(
    "--variant",
    "-t",
    type=click.Choice(UnifontDownloader.ALLOWED_VARIANTS, case_sensitive=False),
    default=UnifontDownloader.DEFAULT_VARIANT,
    show_default=True,
    help=(
        "Unifont font-build variant to download. Supported: "
        "unifont, unifont_all, unifont_jp, unifont_jp_sample, "
        "unifont_sample, unifont_upper, unifont_upper_sample."
    ),
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Destination .hex file path. Defaults to ./<variant>-<version>.hex.",
)
@click.option("--force", "-f", is_flag=True, help="Overwrite the output file if it exists.")
@click.option(
    "--timeout",
    default=30,
    show_default=True,
    type=int,
    help="Network timeout in seconds for downloading.",
)
def download(version, variant, output, force, timeout):
    """Download and extract Unifont .hex releases."""
    downloader = UnifontDownloader(timeout=timeout)

    try:
        initial_length = 0
        with click.progressbar(length=initial_length, label="Downloading", show_eta=False) as bar:

            def progress(downloaded: int, total: int | None) -> None:
                if total and bar.length != total:
                    bar.length = total
                    bar.show_eta = True
                bar.update(downloaded - bar.pos)

            downloaded_file_path, resolved_version = downloader.download_hex(
                version=version,
                variant=variant,
                output=output,
                force=force,
                progress_callback=progress,
            )
    except Exception as exc:  # pragma: no cover - delegated to Click for UX
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Downloaded Unifont {resolved_version} to: {downloaded_file_path}")


@cli.command()
def info():
    """Show information about Unipie."""
    click.echo("Unipie - Unifont Pixel Interactive Editor\n")
    click.echo("Unipie v0.3.1")
    click.echo("Written by SkyEye_FAST")


if __name__ == "__main__":
    cli()
