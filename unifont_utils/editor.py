# -*- encoding: utf-8 -*-
"""Unifont Utils - Editor"""

from rich.text import Text
from rich.panel import Panel
from rich.console import Group
from textual import events
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
        ("w,up", "move_up", "Move Up"),
        ("s,down", "move_down", "Move Down"),
        ("a,left", "move_left", "Move Left"),
        ("d,right", "move_right", "Move Right"),
        ("space", "toggle_glyph", "Toggle Visibility"),
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
        """Watch for changes to the cursor_x or cursor_y attribute."""
        self.render_glyph()

    watch_cursor_y = watch_cursor_x

    def render_glyph(self) -> None:
        """Render the glyph with the current cursor position."""

        def get_color(i: int) -> str:
            """Get color based on index."""
            return "white" if i % 2 == 0 else ("green" if i > 9 else "red")

        def get_block_style(is_cursor: bool, data_value: int) -> str:
            """Get style for the glyph block."""
            if is_cursor:
                return "red on white" if data_value else "red on black"
            return "white on white" if data_value else "black on black"

        def get_nums(i: int) -> str:
            """Get the hexadecimal representation of index."""
            return hex(i)[2:].rjust(2).upper()

        width = self.glyph.width
        glyph = Text("\n  ")
        # Columns
        for i in range(width):
            glyph.append(get_nums(i), style=f"{get_color(i)} bold")
        glyph.append("\n")

        for i in range(16):
            # Rows
            glyph.append(f"{get_nums(i)} ", style=f"{get_color(i)} bold")
            # Glyph pixel blocks
            for j in range(width):
                is_cursor = self.cursor_x == j % width and self.cursor_y == i
                block_style = get_block_style(is_cursor, self.glyph.data[i * width + j])
                char = "⬥ " if is_cursor else "  "
                glyph.append(char, style=block_style)
            glyph.append("\n")

        position = Text(
            f"Position: ({self.cursor_x}, {self.cursor_y})",
            justify="center",
            style="bold",
        )
        panel = Panel(
            glyph,
            title=f"U+{self.glyph.code_point} ({self.glyph.character})",
            subtitle=position,
        )

        self.update(
            Group(Text(self.glyph.unicode_name, justify="center", style="bold"), panel)
        )

    def move_cursor(self, dx: int, dy: int) -> None:
        """Move cursor by the given offsets."""
        self.cursor_x = min(max(0, self.cursor_x + dx), self.glyph.width - 1)
        self.cursor_y = min(max(0, self.cursor_y + dy), 15)

    def action_move_up(self) -> None:
        """Move the cursor up."""
        self.move_cursor(0, -1)

    def action_move_down(self) -> None:
        """Move the cursor down."""
        self.move_cursor(0, 1)

    def action_move_left(self) -> None:
        """Move the cursor left."""
        self.move_cursor(-1, 0)

    def action_move_right(self) -> None:
        """Move the cursor right."""
        self.move_cursor(1, 0)

    def action_toggle_glyph(self) -> None:
        """Toggle the glyph's visibility."""
        index = self.cursor_y * self.glyph.width + self.cursor_x
        self.glyph.data[index] = int(not self.glyph.data[index])
        self.render_glyph()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

    def on_mouse_down(self, event: events.MouseDown) -> None:
        """Handle mouse click events."""

        x, y = event.x, event.y
        grid_x = (x - 5) // 2
        grid_y = y - 4

        if 0 <= grid_x < self.glyph.width and 0 <= grid_y < 16:
            self.cursor_x = grid_x
            self.cursor_y = grid_y

        self.render_glyph()


class GlyphEditor(App):
    """Main application for editing a glyph."""

    glyph: Glyph
    CSS_PATH = "editor.tcss"

    def __init__(self, glyph: Glyph) -> None:
        super().__init__()
        self.glyph = glyph

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        yield GlyphWidget(self.glyph)
