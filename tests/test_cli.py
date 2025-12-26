"""Tests for Unipie."""

from pathlib import Path

from click.testing import CliRunner
from PIL import Image as Img

from unifont_utils.console import cli
from unifont_utils.converter import Converter
from unifont_utils.glyphs import Glyph, GlyphSet
from unifont_utils.page_converter import save_page_image


def _glyph_set_with_samples() -> GlyphSet:
    glyphs = GlyphSet()
    diag_data = [1 if i % 17 == 0 else 0 for i in range(256)]
    narrow_data = [1 if i % 8 == 0 else 0 for i in range(128)]

    glyphs.add_glyph(Glyph.init_from_hex("0000", Converter.to_hex(diag_data)))
    glyphs.add_glyph(Glyph.init_from_hex("0001", Converter.to_hex(narrow_data)))
    return glyphs


def test_convert_page_hex2img_cli(tmp_path: Path):
    """Round-trip: convert a hex page (file) to an image via CLI."""
    runner = CliRunner()

    glyphs = _glyph_set_with_samples()
    font_file = tmp_path / "test_font.hex"
    glyphs.save_hex_file(font_file)

    output_image = tmp_path / "out_page.png"
    result = runner.invoke(
        cli,
        [
            "convert",
            "page",
            "hex2img",
            "-p",
            str(font_file),
            "-g",
            "00",
            "-o",
            str(output_image),
            "-c",
            "transparent_and_white",
        ],
    )

    assert result.exit_code == 0, result.output
    assert output_image.exists()


def test_convert_page_img2hex_cli(tmp_path: Path):
    """Convert a page image to a .hex file using the CLI img2hex command."""
    runner = CliRunner()

    glyphs = _glyph_set_with_samples()
    page_image = tmp_path / "page.png"
    save_page_image(glyphs, "00", page_image, color_scheme="transparent_and_white")

    out_hex = tmp_path / "extracted.hex"
    result = runner.invoke(
        cli,
        [
            "convert",
            "page",
            "img2hex",
            "-p",
            str(page_image),
            "-g",
            "00",
            "-o",
            str(out_hex),
            "--no-auto_detect",
            "-c",
            "transparent_and_white",
        ],
    )

    assert result.exit_code == 0, result.output
    assert out_hex.exists()
    content = out_hex.read_text(encoding="utf-8")
    assert "0000" in content


def test_edit_commands(tmp_path: Path, monkeypatch):
    """Smoke-test interactive `edit` subcommands; stub editor run method."""
    from unifont_utils.editor import GlyphEditor

    runner = CliRunner()

    monkeypatch.setattr(GlyphEditor, "run", lambda self: None)

    glyphs = _glyph_set_with_samples()
    font_file = tmp_path / "font_cli.hex"
    glyphs.save_hex_file(font_file)

    # edit file
    res = runner.invoke(cli, ["edit", "file", "-p", str(font_file), "--cp", "0000", "--overwrite"])
    assert res.exit_code == 0, res.output

    # edit str
    res = runner.invoke(cli, ["edit", "str", "--cp", "0002", "-s", "0" * 32])
    assert res.exit_code == 0, res.output

    # edit empty
    res = runner.invoke(cli, ["edit", "empty", "--cp", "0003", "-w", "8"])
    assert res.exit_code == 0, res.output


def test_hex_commands(tmp_path: Path):
    """Exercise the `hex` subcommands: add, replace, view, and query via CLI."""
    runner = CliRunner()

    glyphs = _glyph_set_with_samples()
    font_file = tmp_path / "font_cli.hex"
    glyphs.save_hex_file(font_file)

    # hex add
    out_hex_add = tmp_path / "added.hex"
    res = runner.invoke(
        cli,
        [
            "hex",
            "add",
            "-p",
            str(font_file),
            "-c",
            "00AA",
            "-s",
            "0" * 32,
            "-o",
            str(out_hex_add),
        ],
    )
    assert res.exit_code == 0, res.output
    assert out_hex_add.exists()

    # hex replace
    res = runner.invoke(
        cli,
        [
            "hex",
            "replace",
            "-p",
            str(out_hex_add),
            "-c",
            "00AA",
            "-s",
            "0" * 32,
            "-o",
            str(out_hex_add),
        ],
    )
    assert res.exit_code == 0, res.output

    # hex view
    res = runner.invoke(cli, ["hex", "view", "-p", str(out_hex_add), "-c", "00AA"])
    assert res.exit_code == 0, res.output

    # hex query (pure)
    res = runner.invoke(cli, ["hex", "query", "-p", str(out_hex_add), "-c", "00AA", "--pure"])
    assert res.exit_code == 0, res.output


def test_single_convert_commands(tmp_path: Path, monkeypatch):
    """Test `convert single` commands (hex2img and img2hex) through the CLI."""
    runner = CliRunner()

    def fake_save_img(self, output, img_format="PNG", color_scheme=None):
        outp = Path(output)
        outp.write_bytes(b"PNG")
        return outp

    from unifont_utils.glyphs import Glyph

    monkeypatch.setattr(Glyph, "save_img", fake_save_img)

    # single hex2img (uses fake_save_img)
    out_img = tmp_path / "single.png"
    res = runner.invoke(cli, ["convert", "single", "hex2img", "-s", "0" * 32, "-o", str(out_img)])
    assert res.exit_code == 0, res.output
    assert out_img.exists()

    # single img2hex: create a tiny image and run
    tiny = tmp_path / "tiny.png"
    Img.new("RGBA", (16, 16), (0, 0, 0, 0)).save(tiny)
    res = runner.invoke(
        cli, ["convert", "single", "img2hex", "-p", str(tiny), "-c", "transparent_and_white"]
    )
    assert res.exit_code == 0, res.output


def test_misc_commands(tmp_path: Path, monkeypatch):
    """Verify miscellaneous commands: `info` and `download` (download is stubbed)."""
    runner = CliRunner()

    res = runner.invoke(cli, ["info"])
    assert res.exit_code == 0 and "Unipie" in res.output

    from unifont_utils.downloader import UnifontDownloader

    def fake_download_hex(self, *args, **kwargs):
        out = tmp_path / "downloaded.hex"
        out.write_text("0000:00000000")
        return str(out), "17.0.03"

    monkeypatch.setattr(UnifontDownloader, "download_hex", fake_download_hex)

    res = runner.invoke(
        cli, ["download", "-v", "17.0.03", "-t", "unifont_all", "-o", str(tmp_path / "dl.hex")]
    )
    assert res.exit_code == 0, res.output
