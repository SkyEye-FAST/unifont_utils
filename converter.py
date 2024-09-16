# -*- encoding: utf-8 -*-
"""Unifont辅助转换程序"""

from functools import reduce
from pathlib import Path
from platform import system
from typing import List, Tuple, Optional
from PIL import Image as Img


class BaseConverter:
    """基础转换器类。"""

    def __init__(
        self,
        data: List[int],
        hex_str: str,
        size: Tuple[int, int],
        black_and_white: bool,
    ) -> None:
        """
        初始化基础转换器类。

        Args:
            data (List[int]): 字形数据。
            hex_str (str): Unifont Hex字符串。
            size (Tuple[int, int]): 字形尺寸，格式为(width, height)。
            black_and_white (bool): 是否为黑白格式图片。
                若为True，则0为白色，1为黑色；若为False，则0为透明，1为白色。
        """

        self.data = data
        self.hex_str = hex_str
        self.size = size
        self.width, self.height = size
        self.black_and_white = black_and_white

    def save_img(
        self,
        save_path: Path,
        black_and_white: Optional[bool] = None,
    ) -> None:
        """
        将Unifont字形保存为图片。

        Args:
            save_path (Path): 保存路径
            black_and_white (bool, optional): 是否为黑白格式图片，默认为使用初始化时的设置。
                若为True，则0为白色，1为黑色；若为False，则0为透明，1为白色。
        """

        if len(self.data) != self.width * self.height:
            raise ValueError("无效的字形数据或尺寸。")

        img = Img.new("RGBA", self.size)
        black_and_white = (
            black_and_white if black_and_white is not None else self.black_and_white
        )
        if black_and_white:
            rgba_data = [
                (0, 0, 0, 255) if pixel else (255, 255, 255, 255) for pixel in self.data
            ]
        else:
            rgba_data = [
                (255, 255, 255, 255) if pixel else (0, 0, 0, 0) for pixel in self.data
            ]
        img.putdata(rgba_data)
        img.save(save_path, "PNG")

    def print_glyph(
        self,
        *,
        black_and_white: Optional[bool] = None,
        display_hex: bool = False,
        display_bin: bool = False,
    ) -> None:
        """
        在控制台打印Unifont字形。

        Args:
            black_and_white (bool, optional): 是否为黑白格式图片，默认使用初始化时的设置。
                若为True，则0为白色，1为黑色；若为False，则0为透明，1为白色。
            display_hex (bool, optional): 是否显示每行对应的Hex字符串。
            display_bin (bool, optional): 是否显示每行对应的Bin字符串。
        """

        if len(self.data) != self.width * self.height:
            raise ValueError("无效的字形数据或尺寸。")

        white_block, black_block, new_line = (
            ("▇", "  ", "\n")
            if system() == "Windows"
            else ("\033[0;37;47m  ", "\033[0;37;40m  ", "\033[0m")
        )

        black_and_white = (
            black_and_white if black_and_white is not None else self.black_and_white
        )
        if black_and_white:
            white_block, black_block = black_block, white_block

        for i in range(self.height):
            row = "".join(
                white_block if self.data[i * self.width + j] else black_block
                for j in range(self.width)
            )
            if display_hex:
                length = self.width // 4
                hex_slice = self.hex_str[i * length : (i + 1) * length]
                if display_bin:
                    bin_slice = "".join(
                        str(self.data[i])
                        for i in range(i * self.width, (i + 1) * self.width)
                    )
                    row = f"{bin_slice}\t{row}"
                row = f"{hex_slice}\t{row}"
            print(row + new_line)


class ImgConverter(BaseConverter):
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

        self.img = Img.open(img_path).convert("1")
        self.data = (
            [0 if pixel == 255 else 1 for pixel in self.img.getdata()]
            if black_and_white
            else [1 if pixel == 255 else 0 for pixel in self.img.getdata()]
        )
        super().__init__(self.data, self.to_hex(), self.img.size, black_and_white)

    def to_hex(self) -> str:
        """将图片数据转换为Unifont Hex字符串。"""
        if not self.data:
            raise ValueError("无法转换为Hex字符串，图片数据为空。")

        n = reduce(lambda acc, pixel: (acc << 1) | (1 if pixel else 0), self.data, 0)
        return hex(n)[2:].upper().zfill(32 if len(self.data) == 128 else 64)


class HexConverter(BaseConverter):
    """Hex字符串转换器类。"""

    def __init__(self, hex_str: str, black_and_white: bool = True) -> None:
        if not hex_str or len(hex_str) not in {32, 64}:
            raise ValueError("无效的Hex字符串。")

        self.hex_str = hex_str.upper()
        self.width, self.height = (16, 16) if len(hex_str) == 64 else (8, 16)
        super().__init__(
            self.to_img_data(), self.hex_str, (self.width, self.height), black_and_white
        )

    def to_img_data(self) -> List[int]:
        """将Unifont Hex字符串转换为图片数据。"""

        if not all(c in "0123456789ABCDEF" for c in self.hex_str):
            raise ValueError("无效的Hex字符串。")

        n = int(self.hex_str, 16)
        return [(n >> i) & 1 for i in range(self.width * self.height - 1, -1, -1)]
