# @Author: SkyEye_FAST <skyeyefast@foxmail.com>
# @Copyright: Copyright (C) 2024-2025 SkyEye_FAST
"""Unifont Utils - Downloader"""

import gzip
import os
import re
import shutil
import tempfile
from collections.abc import Callable, Iterable
from pathlib import Path

import requests

from .base import FilePath, Validator


class UnifontDownloader:
    """Helper for downloading and extracting Unifont releases."""

    BASE_URL = "https://unifoundry.com/pub/unifont/"
    MIN_MAJOR = 7
    DEFAULT_VARIANT = "unifont_all"
    ALLOWED_VARIANTS = (
        "unifont",
        "unifont_all",
        "unifont_jp",
        "unifont_jp_sample",
        "unifont_sample",
        "unifont_upper",
        "unifont_upper_sample",
    )

    def __init__(self, timeout: int = 30) -> None:
        """Initialize the downloader.

        Args:
            timeout: HTTP request timeout in seconds.
        """
        self.timeout = timeout

    @classmethod
    def normalize_version(cls, version: str | int) -> str:
        """Normalize and validate a Unifont version string.

        Accepts versions like ``17.0.03`` or ``v17.0.03`` and enforces a
        minimum major version of ``7``.

        Args:
            version: Version string or integer (with optional leading ``v``).

        Returns:
            Canonical version string in ``<major>.<minor>.<patch>`` form.

        Raises:
            ValueError: If the format is invalid or the major version is too
                low.
        """
        version_str = str(version).strip()
        if version_str.startswith(("v", "V")):
            version_str = version_str[1:]

        if not re.fullmatch(r"\d+\.\d+\.\d+", version_str):
            raise ValueError("Invalid version format. Expected <major>.<minor>.<patch>.")

        if cls._version_key(version_str)[0] < cls.MIN_MAJOR:
            raise ValueError(f"Unifont version must be >= {cls.MIN_MAJOR}.0.0.")

        return version_str

    @classmethod
    def normalize_variant(cls, variant: str | None) -> str:
        """Validate and normalize the requested font build variant.

        Args:
            variant: Variant name; defaults to ``unifont_all`` when ``None``.

        Returns:
            Lowercase variant name.

        Raises:
            ValueError: If the variant is not allowed.
        """
        normalized = (variant or cls.DEFAULT_VARIANT).strip().lower()
        if normalized not in cls.ALLOWED_VARIANTS:
            allowed = ", ".join(cls.ALLOWED_VARIANTS)
            raise ValueError(f"Invalid variant '{normalized}'. Allowed: {allowed}.")
        return normalized

    @staticmethod
    def _version_key(version: str) -> tuple[int, int, int]:
        """Return a sortable tuple for a version string.

        Args:
            version: Version string in ``<major>.<minor>.<patch>`` form.

        Returns:
            Tuple of integers ``(major, minor, patch)``.

        Raises:
            ValueError: If the string cannot be parsed.
        """
        try:
            major, minor, patch = (int(part) for part in version.split("."))
        except ValueError as exc:  # pragma: no cover - defensive guard
            raise ValueError(f"Invalid version string: {version}") from exc
        return major, minor, patch

    @classmethod
    def parse_versions(cls, content: str) -> list[str]:
        """Parse available versions from an index page.

        Args:
            content: HTML/text content of the index page.

        Returns:
            Sorted list of version strings meeting the minimum major version.
        """
        versions: set[str] = set()
        for match in re.findall(r"unifont-((?:\d+\.){2}\d+)/", content):
            parts = match.split(".")
            if len(parts) != 3 or not all(part.isdigit() for part in parts):
                continue
            if int(parts[0]) >= cls.MIN_MAJOR:
                versions.add(match)
        return sorted(versions, key=cls._version_key)

    def latest_version(self) -> str:
        """Return the latest available Unifont version (>=7.x).

        Returns:
            Latest version string.

        Raises:
            RuntimeError: If the index page cannot be parsed or yields no
                versions.
        """
        content = self._fetch_text(self.BASE_URL)
        versions = self.parse_versions(content)
        if not versions:
            raise RuntimeError("Unable to determine latest Unifont version (>=7.x).")
        return versions[-1]

    def build_download_url(self, version: str, *, variant: str | None = None) -> str:
        """Build the download URL for the given version and variant.

        Args:
            version: Unifont version string.
            variant: Optional build variant name.

        Returns:
            URL to the ``.hex.gz`` archive.
        """
        normalized_version = self.normalize_version(version)
        normalized_variant = self.normalize_variant(variant)
        filename = f"{normalized_variant}-{normalized_version}.hex.gz"
        return f"{self.BASE_URL}unifont-{normalized_version}/font-builds/{filename}"

    def download_hex(
        self,
        version: str | int | None = None,
        output: FilePath | None = None,
        *,
        force: bool = False,
        variant: str | None = None,
        progress_callback: Callable[[int, int | None], None] | None = None,
    ) -> tuple[Path, str]:
        """Download and extract a Unifont ``.hex`` file.

        Args:
            version: Requested version; defaults to the latest when ``None``.
            output: Destination file path; defaults to ``<variant>-<version>.hex``.
            force: Whether to overwrite an existing destination file.
            variant: Unifont build variant.
            progress_callback: Optional callback receiving ``downloaded`` bytes
                and total size (or ``None`` when unknown).

        Returns:
            Tuple of ``(output_path, resolved_version)``.

        Raises:
            FileExistsError: If the destination exists and ``force`` is ``False``.
            RuntimeError: On download or extraction failures.
            ValueError: On invalid version or variant input.
        """
        target_version = self.normalize_version(version) if version else self.latest_version()
        target_variant = self.normalize_variant(variant)
        output_path = (
            Validator.file_path(output)
            if output
            else Path.cwd() / f"{target_variant}-{target_version}.hex"
        )

        if output_path.exists() and not force:
            raise FileExistsError(f"Destination already exists: {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        archive_url = self.build_download_url(target_version, variant=target_variant)

        tmp_fd, tmp_name = tempfile.mkstemp(suffix=".gz")
        os.close(tmp_fd)
        tmp_path = Path(tmp_name)
        try:
            self._download_file(archive_url, tmp_path, progress_callback=progress_callback)
            self._extract_gzip(tmp_path, output_path)
        finally:
            tmp_path.unlink(missing_ok=True)

        return output_path, target_version

    def _download_file(
        self,
        url: str,
        destination: Path,
        *,
        progress_callback: Callable[[int, int | None], None] | None = None,
    ) -> None:
        """Download a file to the destination path.

        Args:
            url: Source URL.
            destination: Local path to write.
            progress_callback: Optional callback for progress updates.

        Raises:
            RuntimeError: If the request fails.
        """
        headers = {
            "User-Agent": "unifont-utils/0.6 (+https://github.com/SkyEye-FAST/unifont_utils)",
        }

        try:
            with requests.get(url, headers=headers, timeout=self.timeout, stream=True) as response:
                response.raise_for_status()

                total = int(response.headers.get("Content-Length", 0)) or None
                downloaded = 0
                chunk_size = 1024 * 64

                if progress_callback:
                    progress_callback(downloaded, total)

                with destination.open("wb") as file:
                    for chunk in self._iter_chunks(response.iter_content(chunk_size)):
                        file.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(downloaded, total)
        except requests.RequestException as exc:
            raise RuntimeError(f"Failed to download Unifont archive from {url}: {exc}") from exc

    @staticmethod
    def _iter_chunks(chunks: Iterable[bytes]) -> Iterable[bytes]:
        """Yield non-empty chunks from a streaming response.

        Args:
            chunks: Iterable of raw byte chunks.

        Returns:
            Iterator over non-empty chunks.
        """
        for chunk in chunks:
            if chunk:
                yield chunk

    def _extract_gzip(self, source: Path, destination: Path) -> None:
        """Extract a gzip file to the destination path.

        Args:
            source: Path to the ``.gz`` archive.
            destination: Output path for extracted content.

        Raises:
            RuntimeError: If extraction fails.
        """
        try:
            with gzip.open(source, "rb") as gz_file, destination.open("wb") as out_file:
                shutil.copyfileobj(gz_file, out_file)
        except OSError as exc:
            raise RuntimeError(f"Failed to extract archive {source}: {exc}") from exc

    def _fetch_text(self, url: str) -> str:
        """Fetch text content from a URL.

        Args:
            url: Target URL.

        Returns:
            Response body as text.

        Raises:
            RuntimeError: If the request fails.
        """
        try:
            response = requests.get(
                url,
                headers={
                    "User-Agent": "unifont-utils/0.6 (+https://github.com/SkyEye-FAST/unifont_utils)",
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException as exc:
            raise RuntimeError(f"Failed to fetch {url}: {exc}") from exc
