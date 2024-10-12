# -*- encoding: utf-8 -*-
"""Unifont Utils - Edit"""

from rich.console import Console
from rich.text import Text
from rich.live import Live

from .glyphs import Glyph

console = Console()


def render_glyph(glyph: Glyph, cursor_x=None, cursor_y=None):
    """Render a glyph with cursor."""

    text = Text()
    width = glyph.width
    for i in range(16):
        for j in range(width):
            x = j % width
            if cursor_x == x and cursor_y == i:
                char = "⬥ "
                block_style = (
                    "blue on white" if glyph.data[i * width + j] else "blue on black"
                )
            else:
                char = "  "
                block_style = (
                    "white on white" if glyph.data[i * width + j] else "black on black"
                )
            text.append(char, style=block_style)
        text.append("\n")
    return text


def edit_glyph(glyph: Glyph):
    """Edit a glyph."""

    cursor_x, cursor_y = 0, 0
    with Live(render_glyph(glyph, cursor_x, cursor_y), refresh_per_second=10) as live:
        while True:
            key = (
                console.input(
                    "[bold]Press arrow keys to move, 'space' to toggle, 'q' to quit: [/bold]"
                )
                .strip()
                .lower()
            )

            if key == "w":  # UP
                cursor_y = max(0, cursor_y - 1)
            elif key == "s":  # DOWN
                cursor_y = min(15, cursor_y + 1)
            elif key == "a":  # LEFT
                cursor_x = max(0, cursor_x - 1)
            elif key == "d":  # RIGHT
                cursor_x = min(7, cursor_x + 1)
            elif key == " ":  # TOGGLE PIXEL
                glyph.data[cursor_y * 8 + cursor_x] = not glyph.data[cursor_y * 8 + cursor_x]
            elif key == "q":  # QUIT
                break

            live.update(render_glyph(glyph, cursor_x, cursor_y))
