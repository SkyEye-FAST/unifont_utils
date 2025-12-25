"""Tests for UnifontDownloader helpers."""

from __future__ import annotations

import gzip
from pathlib import Path

import pytest

from unifont_utils.downloader import UnifontDownloader


def test_normalize_version_enforces_format_and_minimum():
    """Normalize versions and reject invalid entries."""
    assert UnifontDownloader.normalize_version("17.0.03") == "17.0.03"
    assert UnifontDownloader.normalize_version("v7.0.01") == "7.0.01"

    with pytest.raises(ValueError):
        UnifontDownloader.normalize_version("6.0.0")
    with pytest.raises(ValueError):
        UnifontDownloader.normalize_version("17.0")


def test_parse_versions_filters_and_sorts():
    """Only keep >=7.x versions and sort them."""
    html = """
    <a href="unifont-6.0.01/">unifont-6.0.01/</a>
    <a href="unifont-7.0.01/">unifont-7.0.01/</a>
    <a href="unifont-17.0.03/">unifont-17.0.03/</a>
    """

    assert UnifontDownloader.parse_versions(html) == ["7.0.01", "17.0.03"]


def test_build_download_url_uses_template():
    """Build the correct download URL."""
    downloader = UnifontDownloader()
    assert (
        downloader.build_download_url("17.0.03")
        == "https://unifoundry.com/pub/unifont/unifont-17.0.03/font-builds/unifont_all-17.0.03.hex.gz"
    )


def test_download_hex_uses_latest_and_writes_file(tmp_path, monkeypatch):
    """Download helper fetches latest version and writes decompressed hex content."""
    downloader = UnifontDownloader(timeout=1)
    monkeypatch.setattr(downloader, "latest_version", lambda: "17.0.03")

    def fake_download(url: str, destination: Path, *, progress_callback=None) -> None:
        with gzip.open(destination, "wb") as gz_file:
            gz_file.write(b"0041:0000\n")

    monkeypatch.setattr(downloader, "_download_file", fake_download)

    output = tmp_path / "output.hex"
    path, version = downloader.download_hex(output=output, force=True)

    assert version == "17.0.03"
    assert path == output
    assert path.read_text(encoding="utf-8") == "0041:0000\n"
