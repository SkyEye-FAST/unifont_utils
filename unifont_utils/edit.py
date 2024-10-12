# -*- encoding: utf-8 -*-
"""Unifont Utils - Edit"""

from rich.text import Text
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.reactive import reactive

from .glyphs import Glyph


class GlyphWidget(Static, can_focus=True):
    """Widget to display and edit a Glyph."""

    cursor_x = reactive(0)
    cursor_y = reactive(0)
    glyph: Glyph

    BINDINGS = [
        ("w", "move_up", "Move Up"),
        ("s", "move_down", "Move Down"),
        ("a", "move_left", "Move Left"),
        ("d", "move_right", "Move Right"),
        ("space", "toggle_glyph", "Toggle Glyph"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, glyph: Glyph) -> None:
        super().__init__()
        self.glyph = glyph

    def on_mount(self) -> None:
        """Actions that are executed when the widget is mounted."""
        self.render_glyph()
        self.focus()

    def watch_cursor_x(self) -> None:
        """Watch for changes to the cursor_x attribute."""
        self.render_glyph()

    def watch_cursor_y(self) -> None:
        """Watch for changes to the cursor_y attribute."""
        self.render_glyph()

    def render_glyph(self):
        """Render the glyph with the current cursor position."""
        text = Text()
        width = self.glyph.width
        for i in range(16):
            for j in range(width):
                x = j % width
                if self.cursor_x == x and self.cursor_y == i:
                    char = "⬥ "
                    block_style = (
                        "blue on white"
                        if self.glyph.data[i * width + j]
                        else "blue on black"
                    )
                else:
                    char = "  "
                    block_style = (
                        "white on white"
                        if self.glyph.data[i * width + j]
                        else "black on black"
                    )
                text.append(char, style=block_style)
            text.append("\n")
        text.append(f"{self.cursor_x}, {self.cursor_y}\n")
        self.update(text)

    def action_move_up(self) -> None:
        """Move the cursor up."""
        self.cursor_y = max(0, self.cursor_y - 1)

    def action_move_down(self) -> None:
        """Move the cursor down."""
        self.cursor_y = min(15, self.cursor_y + 1)

    def action_move_left(self) -> None:
        """Move the cursor left."""
        self.cursor_x = max(0, self.cursor_x - 1)

    def action_move_right(self) -> None:
        """Move the cursor right."""
        self.cursor_x = min(self.glyph.width - 1, self.cursor_x + 1)

    def action_toggle_glyph(self) -> None:
        """Toggle the glyph's visibility."""
        index = self.cursor_y * self.glyph.width + self.cursor_x
        self.glyph.data[index] = int(not self.glyph.data[index])
        self.render_glyph()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()


class GlyphEditor(App):
    """Main application for editing a glyph."""

    glyph: Glyph
    CSS_PATH = "editor.tcss"

    BINDINGS = [
        ("w", "move_up", "Move Up"),
        ("s", "move_down", "Move Down"),
        ("a", "move_left", "Move Left"),
        ("d", "move_right", "Move Right"),
        ("space", "toggle_glyph", "Toggle Glyph"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, glyph: Glyph) -> None:
        super().__init__()
        self.glyph = glyph

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        yield GlyphWidget(self.glyph)
