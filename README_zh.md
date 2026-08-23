# Unifont Utils

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

[![CI](https://github.com/SkyEye-FAST/unifont_utils/actions/workflows/ci.yml/badge.svg)](https://github.com/SkyEye-FAST/unifont_utils/actions/workflows/ci.yml)
![PyPI - Version](https://img.shields.io/pypi/v/unifont_utils) ![GitHub Release](https://img.shields.io/github/v/release/SkyEye-FAST/unifont_utils)

- **[English](README.md) | [中文](README_zh.md)**

此项目提供一系列用于处理GNU Unifont字体的工具。

**更多信息请见[Read the Docs上的文档](https://unifont-utils.readthedocs.io/)。**

## 安装

请使用下面的命令从PyPI安装Unifont Utils：

``` shell
pip install unifont-utils
```

## 快速开始

通过统一的 Python 公共 API 读取并查询 GNU Unifont `.hex` 文件：

```python
from unifont_utils import GlyphSet

glyphs = GlyphSet.load_hex_file("unifont.hex")
glyph = glyphs["0041"]
print(glyph.hex_str)
```

命令行工具支持编辑、转换、下载和直接操作 `.hex` 文件：

```shell
unifont-utils --help
unifont-utils hex query --path unifont.hex --code_point 0041 --pure
```

## 开发

项目使用 [uv](https://docs.astral.sh/uv/) 管理锁定环境，并使用 Ruff 检查与格式化代码：

```shell
uv sync --locked
uv run --locked pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
```

## 协议

本项目在[GPL v3协议](LICENSE)下发布。

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

## 反馈

遇到的问题和功能建议等可以提出议题（Issue）。

欢迎创建拉取请求（Pull request）。
