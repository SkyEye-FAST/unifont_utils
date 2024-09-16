# -*- encoding: utf-8 -*-
"""Unifont辅助转换程序"""

from functools import reduce
from pathlib import Path
from platform import system
from typing import List, Tuple, Optional

from PIL import Image as Img


def print_glyph(
    data: List[int], size: Tuple[int, int], black_and_white: bool = True
) -> None:
    """
    在控制台打印Unifont字形。

    Args:
        data (List[int]): 字形数据
        size (Tuple[int, int]): 字形尺寸，格式为(width, height)。
        black_and_white (bool, optional): 是否为黑白格式图片，默认为True。
            若为True，则0为白色，1为黑色；若为False，则0为透明，1为白色。
    """

    width, height = size
    if not data or len(data) != width * height:
        raise ValueError("无效的字形数据或尺寸。")

    white_block, black_block, new_line = (
        ("▇", "  ", "\n")
        if system() == "Windows"
        else ("\033[0;37;47m  ", "\033[0;37;40m  ", "\033[0m")
    )

    if not black_and_white:
        white_block, black_block = black_block, white_block

    for i in range(0, height, 16):
        for k in range(i, min(i + 16, height)):
            row = "".join(
                white_block if data[k * width + l] else black_block
                for l in range(min(width, 16))
            )
            print(row + new_line)


def save_img(
    data: List[int],
    size: Tuple[int, int],
    save_path: Path,
    black_and_white: bool = True,
    img_format: str = "PNG",
) -> None:
    """
    将Unifont字形保存为图片。

    Args:
        data (List[int]): 字形数据。
        size (Tuple[int, int]): 字形尺寸，格式为(width, height)。
        save_path (Path): 保存路径。
        black_and_white (bool, optional): 是否为黑白格式图片，默认为True。
            若为True，则0为白色，1为黑色；若为False，则0为透明，1为白色。
        img_format (str, optional): 图片格式，默认为PNG。
    """

    if not data or len(data) != size[0] * size[1]:
        raise ValueError("无效的字形数据或尺寸。")

    img = Img.new("RGBA", size)
    if black_and_white:
        rgba_data = [
            (255, 255, 255, 255) if pixel else (0, 0, 0, 255) for pixel in data
        ]
    else:
        rgba_data = [(0, 0, 0, 0) if pixel else (255, 255, 255, 255) for pixel in data]
    img.putdata(rgba_data)
    img.save(save_path, img_format)


class ImgConverter:
    """字形图片转换器类。"""

    def __init__(self, img_path: Path, black_and_white: bool = True) -> None:
        """
        初始化字形图片转换器。

        Args:
            img_path (Path): 图片路径
            black_and_white (bool, optional): 是否为黑白格式图片，默认为True。
                若为True，则0为白色，1为黑色；若为False，则0为透明，1为白色。
        """

        if not img_path.is_file():
            raise FileNotFoundError(f"文件不存在: {img_path}")

        self.path = img_path
        self.img = Img.open(img_path).convert("1")
        self.width, self.height = self.img.size
        self.data = list(self.img.getdata())
        self.black_and_white = black_and_white

        self.data = (
            [1 if pixel else 0 for pixel in self.data]
            if black_and_white
            else [0 if pixel else 1 for pixel in self.data]
        )

    def to_hex(self) -> str:
        """转换为Unifont Hex字符串"""

        if not self.data:
            raise ValueError("无法转换，图片数据为空。")

        n = reduce(
            lambda acc, pixel: (acc << 1) | (1 if pixel == 0 else 0), self.data, 0
        )
        return hex(n)[2:].upper()

    def save_img(
        self,
        save_path: Path,
        black_and_white: Optional[bool] = None,
        img_format: str = "PNG",
    ) -> None:
        """
        保存为图片。

        Args:
            save_path (Path): 保存路径
            black_and_white (bool, optional): 是否为黑白格式图片，默认为使用初始化时的设置。
                若为True，则0为白色，1为黑色；若为False，则0为透明，1为白色。
            img_format (str, optional): 图片格式，默认为PNG。
        """

        if not self.data:
            raise ValueError("无法保存图片，图片数据为空。")

        black_and_white = (
            black_and_white if black_and_white is not None else self.black_and_white
        )

        save_img(self.data, self.img.size, save_path, black_and_white, img_format)

    def print_glyph(self, black_and_white: Optional[bool] = None) -> None:
        """
        在控制台打印Unifont字形。

        Args:
            black_and_white (bool, optional): 是否为黑白格式图片，默认使用初始化时的设置。
                若为True，则0为白色，1为黑色；若为False，则0为透明，1为白色。
        """

        if not self.data:
            raise ValueError("无法打印字形，图片数据为空。")

        black_and_white = (
            black_and_white if black_and_white is not None else self.black_and_white
        )

        print_glyph(self.data, self.img.size, black_and_white)


class HexConverter:
    """Hex字符串转换器类。"""

    def __init__(self, hex_str: str, black_and_white: bool = True) -> None:
        """
        初始化Unifont Hex字符串转换器。

        Args:
            hex_str (str): Hex字符串
            black_and_white (bool, optional): 是否为黑白格式图片，默认为True。
                若为True，则0为白色，1为黑色；若为False，则0为透明，1为白色。
        """

        if not hex_str:
            raise ValueError("Hex字符串不能为空。")

        self.hex_str = hex_str.upper()
        hex_length = len(self.hex_str)

        if hex_length not in {32, 64}:
            raise ValueError("无效的Hex字符串长度。")

        self.width, self.height = (16, 16) if hex_length == 64 else (8, 16)
        self.size = (self.width, self.height)
        self.black_and_white = black_and_white

    def to_img_data(self) -> list:
        """将Unifont Hex字符串转换为图片数据"""

        if not self.hex_str:
            raise ValueError("无法转换，输入的Hex字符串为空。")

        if not all(c in "0123456789ABCDEF" for c in self.hex_str):
            raise ValueError("无效的Hex字符串。")

        n = int(self.hex_str, 16)
        data_length = (len(self.hex_str) + 1) // 2
        return [(0 if (n >> i) & 1 else 1) for i in range(data_length * 8 - 1, -1, -1)]

    def save_img(
        self,
        save_path: Path,
        black_and_white: Optional[bool] = None,
        img_format: str = "PNG",
    ) -> None:
        """
        将Unifont字形保存为图片。

        Args:
            save_path (Path): 保存路径
            black_and_white (bool, optional): 是否为黑白格式图片，默认使用初始化时的设置。
                若为True，则0为白色，1为黑色；若为False，则0为透明，1为白色。
            img_format (str, optional): 图片格式，默认为PNG。
        """

        data = self.to_img_data()
        if not data:
            raise ValueError("无法保存图片，提供的数据为空。")

        save_img(data, self.size, save_path, black_and_white, img_format)

    def print_glyph(self, black_and_white: Optional[bool] = None) -> None:
        """
        在控制台打印Unifont字形。

        Args:
            black_and_white (bool, optional): 是否为黑白格式图片，默认使用初始化时的设置。
                若为True，则0为白色，1为黑色；若为False，则0为透明，1为白色。
        """

        data = self.to_img_data()
        if not data:
            raise ValueError("无法打印字形，提供的数据为空。")

        black_and_white = (
            black_and_white if black_and_white is not None else self.black_and_white
        )

        print_glyph(data, self.size, black_and_white)
