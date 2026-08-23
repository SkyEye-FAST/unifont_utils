# Unifont Utils

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

[![CI](https://github.com/SkyEye-FAST/unifont_utils/actions/workflows/ci.yml/badge.svg)](https://github.com/SkyEye-FAST/unifont_utils/actions/workflows/ci.yml)
![PyPI - Version](https://img.shields.io/pypi/v/unifont_utils) ![GitHub Release](https://img.shields.io/github/v/release/SkyEye-FAST/unifont_utils)

- **[English](README.md) | [中文](README_zh.md)**

This project provides a set of tools for working with the GNU Unifont.

**See the documentation at [Read the Docs](https://unifont-utils.readthedocs.io/)
for more information.**

## Installation

Install the package from PyPI using the following command:

``` shell
pip install unifont-utils
```

## Quick start

Use the public Python API to load and inspect a GNU Unifont `.hex` file:

```python
from unifont_utils import GlyphSet

glyphs = GlyphSet.load_hex_file("unifont.hex")
glyph = glyphs["0041"]
print(glyph.hex_str)
```

The command-line interface exposes editing, conversion, download, and direct `.hex` operations:

```shell
unifont-utils --help
unifont-utils hex query --path unifont.hex --code_point 0041 --pure
```

## Development

The repository uses [uv](https://docs.astral.sh/uv/) for locked environments and Ruff for linting
and formatting:

```shell
uv sync --locked
uv run --locked pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
```

## License

The project is released under the [GPL v3 License](LICENSE).

``` text
    Unifont Utils
    Copyright (C) 2024-2026 SkyEye_FAST

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
```

## Feedback

Please feel free to raise issues for any problems encountered or feature suggestions.

Pull requests are welcome.
