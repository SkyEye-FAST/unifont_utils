"""Granular CLI tests for Unifont Utils."""

from pathlib import Path

import pytest
from click.testing import CliRunner
from PIL import Image as Img

from unifont_utils import Glyph, GlyphSet, __version__
from unifont_utils.console import cli, output_path
from unifont_utils.converter import Converter
from unifont_utils.page_converter import save_page_image


@pytest.fixture()
def runner() -> CliRunner:
    """Provide a reusable Click test runner."""
    return CliRunner()


@pytest.fixture()
def sample_glyphs() -> GlyphSet:
    """Construct a small glyph set used across CLI scenarios."""
    glyphs = GlyphSet()
    diag_data = [1 if i % 17 == 0 else 0 for i in range(256)]
    narrow_data = [1 if i % 8 == 0 else 0 for i in range(128)]

    glyphs.add_glyph(Glyph.init_from_hex("0000", Converter.to_hex(diag_data)))
    glyphs.add_glyph(Glyph.init_from_hex("0001", Converter.to_hex(narrow_data)))
    return glyphs


@pytest.fixture()
def font_file(tmp_path: Path, sample_glyphs: GlyphSet) -> Path:
    """Persist sample glyphs to disk and return the font path."""
    path = tmp_path / "font.hex"
    sample_glyphs.save_hex_file(path)
    return path


@pytest.fixture()
def font_with_extra(tmp_path: Path, sample_glyphs: GlyphSet) -> Path:
    """Create a font file with an extra glyph for hex operations."""
    glyphs = GlyphSet()
    glyphs += sample_glyphs["0000"]
    glyphs += sample_glyphs["0001"]
    glyphs.add_glyph(("00AA", "0" * 32))
    path = tmp_path / "font_extra.hex"
    glyphs.save_hex_file(path)
    return path


def test_info(runner: CliRunner) -> None:
    """CLI info command prints metadata."""
    res = runner.invoke(cli, ["info"])
    assert res.exit_code == 0
    assert "Unifont Utils" in res.output
    assert f"Version {__version__}" in res.output


def test_output_path_only_changes_the_filename_suffix(tmp_path: Path) -> None:
    """Default edited paths do not replace '.hex' text in parent directories."""
    source = tmp_path / "contains.hex" / "font.hex"
    assert output_path(str(source)) == str(source.with_name("font_edited.hex"))


def test_download_stubbed(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Download command succeeds when downloader is stubbed."""
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


def test_edit_file_overwrite(
    runner: CliRunner, font_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Editing a file overwrites in-place when flagged."""
    from unifont_utils.editor import GlyphEditor

    monkeypatch.setattr(GlyphEditor, "run", lambda self: None)

    res = runner.invoke(cli, ["edit", "file", "-p", str(font_file), "--cp", "0000", "--overwrite"])
    assert res.exit_code == 0, res.output
    assert font_file.exists()


def test_edit_str_command(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """Editing a raw hex string yields output."""
    from unifont_utils.editor import GlyphEditor

    monkeypatch.setattr(GlyphEditor, "run", lambda self: None)

    res = runner.invoke(cli, ["edit", "str", "--cp", "0002", "-s", "0" * 32])
    assert res.exit_code == 0, res.output
    assert "Result" in res.output


def test_edit_empty_command(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """Editing an empty glyph reports width and succeeds."""
    from unifont_utils.editor import GlyphEditor

    monkeypatch.setattr(GlyphEditor, "run", lambda self: None)

    res = runner.invoke(cli, ["edit", "empty", "--cp", "0003", "-w", "8"])
    assert res.exit_code == 0, res.output
    assert "Glyph width" in res.output


def test_hex_add_creates_new_file(runner: CliRunner, font_file: Path, tmp_path: Path) -> None:
    """Adding a glyph writes a new file with the entry."""
    target = tmp_path / "added.hex"
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
            str(target),
        ],
    )
    assert res.exit_code == 0, res.output
    assert target.exists()
    assert "00AA" in target.read_text(encoding="utf-8")


def test_hex_replace_overwrites_existing(runner: CliRunner, font_with_extra: Path) -> None:
    """Replacing a glyph updates its hex string."""
    updated = "F" * 32
    res = runner.invoke(
        cli,
        [
            "hex",
            "replace",
            "-p",
            str(font_with_extra),
            "-c",
            "00AA",
            "-s",
            updated,
            "-o",
            str(font_with_extra),
        ],
    )
    assert res.exit_code == 0, res.output
    assert updated in font_with_extra.read_text(encoding="utf-8")


def test_hex_view_displays_glyph(runner: CliRunner, font_with_extra: Path) -> None:
    """Viewing prints glyph details to the console."""
    res = runner.invoke(cli, ["hex", "view", "-p", str(font_with_extra), "-c", "00AA"])
    assert res.exit_code == 0, res.output
    assert "Viewing" in res.output


def test_hex_query_pure(runner: CliRunner, font_with_extra: Path) -> None:
    """Pure query outputs only the hex string."""
    res = runner.invoke(cli, ["hex", "query", "-p", str(font_with_extra), "-c", "00AA", "--pure"])
    assert res.exit_code == 0, res.output
    assert res.output.strip() == "0" * 32 or res.output.strip() == "F" * 32


def test_hex_query_verbose(runner: CliRunner, font_with_extra: Path) -> None:
    """Verbose query includes code point label."""
    res = runner.invoke(cli, ["hex", "query", "-p", str(font_with_extra), "-c", "00AA"])
    assert res.exit_code == 0, res.output
    assert "U+00AA" in res.output


def test_convert_page_hex2img(runner: CliRunner, font_file: Path, tmp_path: Path) -> None:
    """Page hex to image conversion writes an image file."""
    output_image = tmp_path / "out_page.png"
    res = runner.invoke(
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
    assert res.exit_code == 0, res.output
    assert output_image.exists()


def test_convert_page_img2hex(runner: CliRunner, sample_glyphs: GlyphSet, tmp_path: Path) -> None:
    """Page image back to hex regenerates glyph entries."""
    page_image = tmp_path / "page.png"
    save_page_image(sample_glyphs, "00", page_image, color_scheme="transparent_and_white")

    out_hex = tmp_path / "extracted.hex"
    res = runner.invoke(
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
    assert res.exit_code == 0, res.output
    assert out_hex.exists()
    assert "0000" in out_hex.read_text(encoding="utf-8")


def test_convert_single_hex2img(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Single hex string can be rendered to an image."""

    def fake_save_img(self, output, img_format="PNG", color_scheme=None):
        outp = Path(output)
        outp.write_bytes(b"PNG")
        return outp

    monkeypatch.setattr(Glyph, "save_img", fake_save_img)

    out_img = tmp_path / "single.png"
    res = runner.invoke(cli, ["convert", "single", "hex2img", "-s", "0" * 32, "-o", str(out_img)])
    assert res.exit_code == 0, res.output
    assert out_img.exists()


def test_convert_single_img2hex(runner: CliRunner, tmp_path: Path) -> None:
    """Single image can be converted to hex string."""
    tiny = tmp_path / "tiny.png"
    Img.new("RGBA", (16, 16), (0, 0, 0, 0)).save(tiny)

    res = runner.invoke(
        cli, ["convert", "single", "img2hex", "-p", str(tiny), "-c", "transparent_and_white"]
    )
    assert res.exit_code == 0, res.output
